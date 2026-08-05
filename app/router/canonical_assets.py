import csv
import io
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.core.dependencies import CurrentUserDep
from app.models.enums import ASSET_CATEGORIES, ASSET_CATEGORY_SLUGS, CATEGORY_LABELS
from app.services import asset_cache

router = APIRouter(prefix="/api/canonical-assets", tags=["canonical-assets"])


class CanonicalAssetRead(BaseModel):
    id: int
    provider: str
    provider_resource_id: str
    canonical_type: str
    display_name: str | None
    account_id: str | None
    region: str | None
    owner: str | None
    tags: dict | None
    status: str | None
    environment: str | None = None
    data_classification: str | None = None
    source_connection_id: str | None = None
    details: dict | None
    discovered_at: datetime | None = None
    last_seen_at: datetime | None = None
    deleted_at: datetime | None = None


class CategoryCount(BaseModel):
    slug: str
    label: str
    count: int


@router.get("/categories")
async def list_categories(
    current_user: CurrentUserDep,
) -> list[CategoryCount]:
    assets = asset_cache.get_assets(current_user.organization_id)

    type_counts: dict[str, int] = {}
    for a in assets:
        ct = a.get("canonical_type", "Other")
        type_counts[ct] = type_counts.get(ct, 0) + 1

    cat_counts: dict[str, int] = {}
    for canonical_type, count in type_counts.items():
        slug = ASSET_CATEGORIES.get(canonical_type, "other")
        cat_counts[slug] = cat_counts.get(slug, 0) + count

    merged: list[CategoryCount] = []
    seen = set()
    for slug in ASSET_CATEGORY_SLUGS:
        merged.append(
            CategoryCount(
                slug=slug,
                label=CATEGORY_LABELS.get(slug, slug),
                count=cat_counts.get(slug, 0),
            )
        )
        seen.add(slug)

    for slug in sorted(cat_counts):
        if slug not in seen:
            merged.append(
                CategoryCount(
                    slug=slug,
                    label=CATEGORY_LABELS.get(slug, slug),
                    count=cat_counts.get(slug, 0),
                )
            )
            seen.add(slug)

    return merged


@router.get("")
async def list_assets(
    current_user: CurrentUserDep,
    category: str | None = Query(None),
    type: str | None = Query(None, alias="type"),
    provider: str | None = Query(None),
) -> list[CanonicalAssetRead]:
    assets = asset_cache.get_assets(current_user.organization_id)

    if type:
        assets = [a for a in assets if a.get("canonical_type") == type]
    elif category:
        types_in_category = {
            ct for ct, cat in ASSET_CATEGORIES.items() if cat == category
        }
        if types_in_category:
            assets = [a for a in assets if a.get("canonical_type") in types_in_category]

    if provider:
        assets = [a for a in assets if a.get("provider") == provider]

    assets.sort(key=lambda a: (a.get("canonical_type", ""), a.get("display_name", "") or ""))

    return [CanonicalAssetRead.model_validate(a) for a in assets]


@router.get("/export-csv")
async def export_csv(
    current_user: CurrentUserDep,
):
    assets = asset_cache.get_assets(current_user.organization_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "provider", "provider_resource_id", "canonical_type", "display_name",
                      "account_id", "region", "owner", "status", "environment",
                      "data_classification", "discovered_at", "last_seen_at"])

    for a in assets:
        writer.writerow([
            a.get("id"), a.get("provider"), a.get("provider_resource_id"),
            a.get("canonical_type"), a.get("display_name"),
            a.get("account_id"), a.get("region"), a.get("owner"),
            a.get("status"), a.get("environment"), a.get("data_classification"),
            a.get("discovered_at", "") or "",
            a.get("last_seen_at", "") or "",
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=canonical_assets.csv"},
    )


@router.delete("/clear")
async def clear_assets(current_user: CurrentUserDep):
    asset_cache.clear(current_user.organization_id)
    return {"status": "ok", "message": f"Cleared cached assets for organization {current_user.organization_id}"}


@router.get("/{asset_id}", response_model=CanonicalAssetRead)
async def get_asset(
    asset_id: int,
    current_user: CurrentUserDep,
) -> CanonicalAssetRead:
    assets = asset_cache.get_assets(current_user.organization_id)
    for a in assets:
        if a.get("id") == asset_id:
            return CanonicalAssetRead.model_validate(a)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
