import logging
from datetime import datetime, timezone
from typing import Any

from app.mappers import CanonicalAssetData, RelationshipData
from app.mappers.canonical_map import get_rule
from app.mappers.rules_engine import apply_rule
from app.services import asset_cache

logger = logging.getLogger(__name__)


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _asset_data_to_dict(ad: CanonicalAssetData) -> dict:
    return {
        "provider": ad.provider,
        "provider_resource_id": ad.provider_resource_id,
        "canonical_type": ad.canonical_type,
        "display_name": ad.display_name,
        "account_id": ad.account_id,
        "region": ad.region,
        "owner": ad.owner,
        "tags": ad.tags,
        "status": ad.status,
        "environment": ad.environment,
        "data_classification": ad.data_classification,
        "source_connection_id": ad.source_connection_id,
        "details": ad.details,
        "discovered_at": ad.discovered_at.isoformat() if ad.discovered_at else None,
        "last_seen_at": ad.last_seen_at.isoformat() if ad.last_seen_at else None,
        "deleted_at": ad.deleted_at.isoformat() if ad.deleted_at else None,
    }


RELATIONSHIP_TYPE_MAP: dict[str, str] = {
    "VPC": "belongs_to",
    "Subnet": "belongs_to",
    "Volume": "attached_to",
    "SecurityGroup": "associated_with",
    "EC2": "attached_to",
    "Cluster": "belongs_to",
}


def _resolve_status(details: dict) -> str | None:
    """Fallback: resolve status from common AWS/Azure status fields.

    This is a safety net until all YAML rules are enriched with explicit
    ``status`` mappings.  Once that's done, this function can be removed.
    """
    for key in ("State", "state", "KeyState", "InstanceState",
                "DBInstanceStatus", "LifecycleState", "Status", "status"):
        raw = details.get(key)
        if raw is None:
            continue
        if isinstance(raw, dict):
            raw = raw.get("Name") or raw.get("name") or str(raw)
        if not isinstance(raw, str):
            raw = str(raw)
        if not raw:
            continue
        s = raw.lower()
        if s in ("running", "available", "active", "in-use", "attached", "enabled"):
            return "Active"
        if s in ("stopped", "terminated", "deleted", "detached", "disabled"):
            return "Stopped"
        if s in ("pending", "creating"):
            return "Pending"
        return raw
    return None


def _build_from_rule(
    organization_id: int,
    resource: dict,
    now: datetime,
) -> tuple[CanonicalAssetData | None, list[RelationshipData]]:
    """Build CanonicalAssetData by applying the YAML rule for this resource type.

    Flow:
      1. Look up the rule by ``resource["resource_type"]`` (the Steampipe table name)
      2. Get the raw source data from ``resource["details"]``
      3. Call ``apply_rule(rule, source_data)`` → canonical dict
      4. Map that dict to a ``CanonicalAssetData``
    """
    resource_type = resource.get("resource_type")
    if not resource_type:
        return None, []

    # Look up the YAML rule for this resource type
    try:
        rule = get_rule(resource_type)
    except KeyError:
        logger.warning("No YAML rule found for resource type '%s' — skipping", resource_type)
        return None, []

    # The raw Steampipe row is in details
    source_data = resource.get("details", {})

    # Apply the rule to produce a canonical dict
    try:
        canonical = apply_rule(rule, source_data)
    except ValueError:
        logger.warning(
            "Skipping resource type '%s': rule produced invalid canonical_category",
            resource_type,
        )
        return None, []

    # Normalise tags from various source formats
    tags = resource.get("tags") or source_data.get("Tags")
    if isinstance(tags, list):
        tags = {t.get("Key", ""): t.get("Value", "") for t in tags if isinstance(t, dict)}

    # Fallback: resolve status from common status fields
    # (until all YAML rules are enriched with explicit status mappings)
    status = canonical.get("status")
    if not status:
        status = _resolve_status(source_data)

    # Build CanonicalAssetData from the rule output
    asset = CanonicalAssetData(
        organization_id=organization_id,
        provider=canonical.get("provider", "AWS"),
        provider_resource_id=canonical.get("provider_resource_id", ""),
        canonical_type=canonical.get("canonical_type", "Other"),
        display_name=canonical.get("display_name"),
        account_id=canonical.get("account_id"),
        region=canonical.get("region"),
        owner=canonical.get("owner"),
        tags=tags,
        status=status,
        details=_json_safe(source_data),
        discovered_at=now,
    )

    # Build relationships from the embedded relationships map
    # (relationships are not YAML-driven yet — extracted from steampipe entry)
    relationships: list[RelationshipData] = []
    rel_map = resource.get("relationships", {})
    if isinstance(rel_map, dict):
        source_id = canonical.get("provider_resource_id") or resource.get("resource_id", "")
        for rel_key, rel_value in rel_map.items():
            target_ids: list[str] = []
            if isinstance(rel_value, str):
                target_ids = [rel_value]
            elif isinstance(rel_value, list):
                target_ids = [str(v) for v in rel_value if v]
            rel_type = RELATIONSHIP_TYPE_MAP.get(rel_key, "associated_with")
            for tid in target_ids:
                if not tid:
                    continue
                relationships.append(RelationshipData(
                    organization_id=organization_id,
                    source_provider_resource_id=source_id,
                    target_provider_resource_id=str(tid),
                    relationship_type=rel_type,
                    extras={"source_type": resource_type, "target_type": rel_key},
                ))

    return asset, relationships


class IngestionService:
    async def ingest_from_result(
        self,
        organization_id: int,
        import_result: dict,
        region: str,
        account_id: str | None = None,
        cancel_check=None,
    ) -> dict:
        resources_detail = import_result.get("resources_detail", [])

        now = datetime.now(timezone.utc)
        asset_data_list: list[dict] = []
        relationship_data_list: list[dict] = []

        for idx, r in enumerate(resources_detail):
            # Honour bulk-import cancellation while mapping resources (this
            # step has no Steampipe subprocess running, so the cancel flag
            # must be polled explicitly).
            if cancel_check is not None and idx % 50 == 0:
                cancel_check()
            asset_data, rel_data = _build_from_rule(organization_id, r, now)
            if asset_data:
                asset_data_list.append(_asset_data_to_dict(asset_data))
            for rd in rel_data:
                relationship_data_list.append({
                    "source_provider_resource_id": rd.source_provider_resource_id,
                    "target_provider_resource_id": rd.target_provider_resource_id,
                    "relationship_type": rd.relationship_type,
                    "extras": rd.extras,
                })

        asset_cache.store(organization_id, asset_data_list, relationship_data_list)

        return {
            "resources_collected": len(resources_detail),
            "assets_stored": len(asset_data_list),
            "relationships_created": len(relationship_data_list),
        }
