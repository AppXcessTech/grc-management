"""
Bulk import router — runs all configured integrations (AWS, Azure, Okta, GitHub,
GitLab, Microsoft 365, GCP) **sequentially** in a single background thread to
minimise peak RAM usage.

Each integration is discovered and ingested one at a time:
  1. AWS   (Steampipe-based cloud resource discovery)
  2. Azure (Steampipe-based cloud resource discovery)
  3. Okta  (Steampipe-based identity resource discovery)
  4. GitHub (Steampipe-based version-control resource discovery)
  5. GitLab (Steampipe-based version-control resource discovery)

Memory design rationale:
  - Each Steampipe import holds ALL discovered resources in a Python list
    before writing to the DB.  Running multiple imports in parallel would
    multiply that memory overhead, risking OOM on small VPS instances.
  - Sequential execution keeps peak memory at ~the largest single-provider
    import, letting Python GC / temp-directory cleanup free memory between
    phases.
"""
import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from app.core.database import SQLALCHEMY_DATABASE_URL
from app.core.dependencies import CurrentUserDep

from app.services.steampipe_aws import import_aws_resources_via_steampipe, _derive_service
from app.services.steampipe_azure import import_azure_resources_via_steampipe
from app.services.steampipe_okta import import_okta_resources_via_steampipe
from app.services.steampipe_github import import_github_resources_via_steampipe
from app.services.steampipe_gitlab import import_gitlab_resources_via_steampipe
from app.services.steampipe_microsoft365 import import_microsoft365_resources_via_steampipe
from app.services.steampipe_gcp import import_gcp_resources_via_steampipe
from app.services.steampipe_bitbucket import import_bitbucket_resources_via_steampipe
from app.services.ingestion import IngestionService
from app.utils.crypto import decrypt_value
from app.services.steampipe_process import (
    ImportCancelledError,
    NetworkUnavailableError,
    kill_all as kill_steampipe_processes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations/bulk", tags=["integrations"])

# ---------------------------------------------------------------------------
# Config directories (same paths used by individual integration routers)
# ---------------------------------------------------------------------------
CONFIG_DIRS = {
    "aws": Path("data/aws_config"),
    "azure": Path("data/azure_config"),
    "okta": Path("data/okta_config"),
    "github": Path("data/github_config"),
    "gitlab": Path("data/gitlab_config"),
    "microsoft365": Path("data/microsoft365_config"),
    "gcp": Path("data/gcp_config"),
    "bitbucket": Path("data/bitbucket_config"),
}

# ---------------------------------------------------------------------------
# In-memory job tracking
# ---------------------------------------------------------------------------
_import_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _create_job(org_id: int) -> str:
    now = datetime.now(timezone.utc).isoformat()
    job_id = str(uuid4())
    with _jobs_lock:
        _import_jobs[job_id] = {
            "job_id": job_id,
            "organization_id": org_id,
            "status": "pending",
            "progress": 0,
            "phase": "starting",
            "message": "Starting bulk import...",
            "integrations_to_run": [],
            "current_integration": "",
            "current_phase": "",
            "current_message": "",
            "current_progress": 0,
            "results": {},
            "error": None,
            "warnings": [],
            "cancelled": False,
            "started_at": now,
            "completed_at": None,
            "last_activity_at": now,
        }
    return job_id


def _update_job(job_id: str, **kwargs):
    with _jobs_lock:
        if job_id in _import_jobs:
            _import_jobs[job_id].update(kwargs)


def _get_job(job_id: str) -> Optional[dict]:
    with _jobs_lock:
        return _import_jobs.get(job_id)


def _is_cancelled(job_id: str) -> bool:
    """Check whether a cancellation has been requested for this job."""
    with _jobs_lock:
        job = _import_jobs.get(job_id)
        if job is None:
            return False
        return job.get("cancelled", False)


def _raise_if_cancelled(job_id: str):
    """Raise ImportCancelledError if the job has been cancelled.

    Used by the ingestion path (which has no progress callback of its own)
    so that a cancellation request is honoured while resources are being
    written to the database / mapped to canonical assets — not just while
    Steampipe queries are running.
    """
    if _is_cancelled(job_id):
        raise ImportCancelledError("Import cancelled by user")


def _cleanup_old_jobs():
    now = datetime.now(timezone.utc)
    with _jobs_lock:
        stale = [
            jid for jid, job in _import_jobs.items()
            if job.get("completed_at") and (
                now - datetime.fromisoformat(job["completed_at"])
            ).total_seconds() > 3600
        ]
        for jid in stale:
            del _import_jobs[jid]


# ---------------------------------------------------------------------------
# Config loaders
# ---------------------------------------------------------------------------
def _is_aws_configured(org_id: int) -> dict:
    path = CONFIG_DIRS["aws"] / f"org_{org_id}.json"
    if path.exists():
        cfg = json.loads(path.read_text())
        if cfg.get("role_arn"):
            return cfg
    return {}


def _is_azure_configured(org_id: int) -> dict:
    path = CONFIG_DIRS["azure"] / f"org_{org_id}.json"
    if path.exists():
        cfg = json.loads(path.read_text())
        if cfg.get("subscription_id") and cfg.get("tenant_id") and cfg.get("client_id"):
            # Decrypt the client_secret if encrypted
            if cfg.get("client_secret"):
                try:
                    cfg["client_secret"] = decrypt_value(cfg["client_secret"])
                except Exception:
                    pass
            return cfg
    return {}


def _is_okta_configured(org_id: int) -> dict:
    path = CONFIG_DIRS["okta"] / f"org_{org_id}.json"
    if path.exists():
        cfg = json.loads(path.read_text())
        if cfg.get("okta_domain") and cfg.get("okta_token"):
            return cfg
    return {}


def _is_github_configured(org_id: int) -> dict:
    path = CONFIG_DIRS["github"] / f"org_{org_id}.json"
    if path.exists():
        cfg = json.loads(path.read_text())
        if cfg.get("github_token"):
            return cfg
    return {}


def _is_gitlab_configured(org_id: int) -> dict:
    """Check if GitLab is configured.

    Prefers the dedicated ``data/gitlab_config`` dir (synced by the generic
    config router), falling back to the generic ``data/integrations/gitlab``
    location for configs saved before the dedicated sync existed.
    """
    for path in (
        CONFIG_DIRS["gitlab"] / f"org_{org_id}.json",
        Path("data/integrations/gitlab") / f"org_{org_id}.json",
    ):
        if path.exists():
            cfg = json.loads(path.read_text())
            baseurl = (cfg.get("baseurl") or cfg.get("base_url") or cfg.get("gitlab_url") or "").strip()
            token = (cfg.get("token") or cfg.get("gitlab_token") or "").strip()
            if baseurl and token:
                return {"baseurl": baseurl, "token": token}
    return {}


def _is_gcp_configured(org_id: int) -> dict:
    """Check if GCP is configured and return decrypted credentials."""
    path = CONFIG_DIRS["gcp"] / f"org_{org_id}.json"
    if path.exists():
        cfg = json.loads(path.read_text())
        if cfg.get("project_id") and cfg.get("credentials_json"):
            # Decrypt the credentials for Steampipe
            if cfg.get("credentials_json"):
                try:
                    cfg["credentials_json"] = decrypt_value(cfg["credentials_json"])
                except Exception:
                    pass
            if cfg.get("private_key"):
                try:
                    cfg["private_key"] = decrypt_value(cfg["private_key"])
                except Exception:
                    pass
            return cfg
    return {}


def _is_microsoft365_configured(org_id: int) -> dict:
    path = CONFIG_DIRS["microsoft365"] / f"org_{org_id}.json"
    if path.exists():
        cfg = json.loads(path.read_text())
        if cfg.get("tenant_id") and cfg.get("client_id") and cfg.get("client_secret"):
            return cfg
    return {}


def _is_bitbucket_configured(org_id: int) -> dict:
    """Check if Bitbucket is configured.

    Prefers the dedicated ``data/bitbucket_config`` dir (synced by the generic
    config router), falling back to the generic ``data/integrations/bitbucket``
    location for configs saved before the dedicated sync existed.
    """
    for path in (
        CONFIG_DIRS["bitbucket"] / f"org_{org_id}.json",
        Path("data/integrations/bitbucket") / f"org_{org_id}.json",
    ):
        if path.exists():
            cfg = json.loads(path.read_text())
            username = (cfg.get("username") or "").strip()
            password = (cfg.get("password") or cfg.get("app_password") or "").strip()
            if username and password:
                return {
                    "base_url": cfg.get("base_url") or "https://api.bitbucket.org/2.0",
                    "username": username,
                    "password": password,
                    "workspace_slug": (cfg.get("workspace_slug") or "").strip(),
                }
    return {}


# ---------------------------------------------------------------------------
# Phase helpers – each returns a result dict
# ---------------------------------------------------------------------------
def _import_aws_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run AWS import (Steampipe discovery + ingestion)."""
    engine = create_engine(sync_db_url, pool_pre_ping=True)

    # Build progress callback that updates the job
    def _aws_progress_cb(info: dict):
        if not job_id:
            return
        # Check if cancellation was requested
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"AWS: {msg}" if msg else "AWS: Querying...",
            current_phase=f"aws_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict, region: str) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for r in resources_detail:
                    service = _derive_service(r["resource_type"])
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "AWS",
                            "account_id": result.get("account_id"),
                            "region": r.get("region"),
                            "service": service,
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            region,
            result.get("account_id"),
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    try:
        result = asyncio.run(import_aws_resources_via_steampipe(
            role_arn=cfg["role_arn"],
            account_name=cfg.get("account_name", ""),
            external_id=cfg.get("external_id", ""),
            region=cfg.get("region", "us-east-1"),
            db=None,
            progress_callback=_aws_progress_cb,
        ))

        ingest_result = _store_and_ingest(result, cfg.get("region", "us-east-1"))

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("AWS bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during AWS bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("AWS bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("AWS bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_azure_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run Azure import (Steampipe discovery + ingestion)."""
    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _azure_progress_cb(info: dict):
        if not job_id:
            return
        # Check if cancellation was requested
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        table = info.get("current_table", "")
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"Azure: {msg}" if msg else "Azure: Querying...",
            current_phase=f"azure_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict, subscription_id: str) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "Azure",
                            "account_id": subscription_id,
                            "region": r.get("region"),
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            subscription_id,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    subscription_id = cfg.get("subscription_id", "")
    try:
        result = asyncio.run(import_azure_resources_via_steampipe(
            subscription_id=subscription_id,
            tenant_id=cfg["tenant_id"],
            client_id=cfg["client_id"],
            client_secret=cfg.get("client_secret", ""),
            account_name=cfg.get("account_name", ""),
            db=None,
            progress_callback=_azure_progress_cb,
        ))

        ingest_result = _store_and_ingest(result, subscription_id)

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("Azure bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during Azure bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("Azure bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("Azure bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_github_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run GitHub import (Steampipe discovery + ingestion)."""
    github_token = cfg.get("github_token", "").strip()
    classic_token = cfg.get("classic_token", "").strip() or None

    if not github_token:
        return {"status": "error", "error": "GitHub not fully configured", "warnings": []}

    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _github_progress_cb(info: dict):
        if not job_id:
            return
        # Check if cancellation was requested
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        table = info.get("current_table", "")
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"GitHub: {msg}" if msg else "GitHub: Querying...",
            current_phase=f"github_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "GitHub",
                            "account_id": "github",
                            "region": r.get("region", "global"),
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            "github",
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    has_classic = bool(classic_token and classic_token.strip())
    token_label = "(fine-grained + classic)" if has_classic else "(fine-grained only)"

    try:
        result = asyncio.run(import_github_resources_via_steampipe(
            github_token=github_token,
            classic_token=classic_token,
            db=None,
            progress_callback=_github_progress_cb,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))

        ingest_result = _store_and_ingest(result)

        logger.info(
            "GitHub bulk import complete %s: %d resources, %d warnings",
            token_label,
            result.get("resources_discovered", 0),
            len(result.get("warnings", [])),
        )

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("GitHub bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during GitHub bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("GitHub bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("GitHub bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_gitlab_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run GitLab import (Steampipe discovery + ingestion)."""
    baseurl = (cfg.get("baseurl", "") or cfg.get("base_url", "") or cfg.get("gitlab_url", "")).strip()
    gitlab_token = (cfg.get("token", "") or cfg.get("gitlab_token", "")).strip()

    if not baseurl or not gitlab_token:
        return {"status": "error", "error": "GitLab not fully configured", "warnings": []}

    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _gitlab_progress_cb(info: dict):
        if not job_id:
            return
        # Check if cancellation was requested
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        table = info.get("current_table", "")
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"GitLab: {msg}" if msg else "GitLab: Querying...",
            current_phase=f"gitlab_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "GitLab",
                            "account_id": baseurl,
                            "region": "global",
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            baseurl,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    try:
        result = asyncio.run(import_gitlab_resources_via_steampipe(
            baseurl=baseurl,
            token=gitlab_token,
            db=None,
            progress_callback=_gitlab_progress_cb,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))

        ingest_result = _store_and_ingest(result)

        logger.info(
            "GitLab bulk import complete: %d resources, %d warnings",
            result.get("resources_discovered", 0),
            len(result.get("warnings", [])),
        )

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("GitLab bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during GitLab bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("GitLab bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("GitLab bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_okta_steampipe_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run Okta Steampipe discovery + ingestion.

    This uses the Okta Steampipe plugin to discover ALL Okta resources
    (users, groups, applications, auth policies, devices, etc.) and maps
    them to canonical categories like Identity, Group, Application, etc.

    Previously Okta only synced users as People Assets — this replaces
    that with full Steampipe-based discovery into Canonical Assets.
    """
    okta_domain = cfg.get("okta_domain", "").strip()
    okta_token = cfg.get("okta_token", "").strip()

    if not okta_domain or not okta_token:
        return {"status": "error", "error": "Okta not fully configured", "warnings": []}

    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _okta_progress_cb(info: dict):
        if not job_id:
            return
        # Check if cancellation was requested
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        table = info.get("current_table", "")
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"Okta: {msg}" if msg else "Okta: Querying...",
            current_phase=f"okta_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "Okta",
                            "account_id": okta_domain,
                            "region": r.get("region"),
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            okta_domain,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    try:
        result = asyncio.run(import_okta_resources_via_steampipe(
            okta_domain=okta_domain,
            okta_token=okta_token,
            db=None,
            progress_callback=_okta_progress_cb,
        ))

        ingest_result = _store_and_ingest(result)

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("Okta Steampipe import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during Okta bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("Okta import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("Okta Steampipe import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_gcp_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run GCP import (Steampipe discovery + ingestion)."""
    credentials_json = cfg.get("credentials_json", "")
    project_id = cfg.get("project_id", "")
    region = cfg.get("region", "us-central1")

    if not credentials_json or not project_id:
        return {"status": "error", "error": "GCP not fully configured", "warnings": []}

    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _gcp_progress_cb(info: dict):
        if not job_id:
            return
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        table = info.get("current_table", "")
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"GCP: {msg}" if msg else "GCP: Querying...",
            current_phase=f"gcp_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "GCP",
                            "account_id": project_id,
                            "region": r.get("region"),
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            region,
            project_id,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    try:
        result = asyncio.run(import_gcp_resources_via_steampipe(
            credentials_json=credentials_json,
            project_id=project_id,
            db=None,
            progress_callback=_gcp_progress_cb,
        ))

        ingest_result = _store_and_ingest(result)

        logger.info(
            "GCP bulk import complete: %d resources",
            result.get("resources_discovered", 0),
        )

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("GCP bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during GCP bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("GCP bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("GCP bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_bitbucket_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run Bitbucket import (Steampipe discovery + ingestion)."""
    base_url = cfg.get("base_url", "https://api.bitbucket.org/2.0").strip()
    username = cfg.get("username", "").strip()
    app_password = cfg.get("password", "").strip()
    workspace_slug = (cfg.get("workspace_slug") or "").strip()

    if not username or not app_password:
        return {"status": "error", "error": "Bitbucket not fully configured", "warnings": []}
    if not workspace_slug:
        return {
            "status": "error",
            "error": (
                "Bitbucket requires a workspace slug. Bitbucket deprecated the "
                "workspace-listing endpoints (the bitbucket_my_* tables return "
                "410 Gone), so add a workspace slug to the Bitbucket integration "
                "configuration."
            ),
            "warnings": [],
        }

    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _bitbucket_progress_cb(info: dict):
        if not job_id:
            return
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"Bitbucket: {msg}" if msg else "Bitbucket: Querying...",
            current_phase=f"bitbucket_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "Bitbucket",
                            "account_id": base_url,
                            "region": "global",
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            base_url,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    try:
        result = asyncio.run(import_bitbucket_resources_via_steampipe(
            base_url=base_url,
            username=username,
            app_password=app_password,
            db=None,
            progress_callback=_bitbucket_progress_cb,
            cancel_check=lambda: _raise_if_cancelled(job_id),
            workspace_slug=workspace_slug,
        ))

        ingest_result = _store_and_ingest(result)

        logger.info(
            "Bitbucket bulk import complete: %d resources, %d warnings",
            result.get("resources_discovered", 0),
            len(result.get("warnings", [])),
        )

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("Bitbucket bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during Bitbucket bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("Bitbucket bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("Bitbucket bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


def _import_microsoft365_phase(
    org_id: int,
    cfg: dict,
    sync_db_url: str,
    job_id: str = "",
    step_progress_base: int = 5,
    step_progress_range: int = 30,
) -> dict:
    """Run Microsoft 365 import (Steampipe discovery + ingestion)."""
    tenant_id = cfg.get("tenant_id", "").strip()
    client_id = cfg.get("client_id", "").strip()
    client_secret = cfg.get("client_secret", "").strip()

    if not tenant_id or not client_id or not client_secret:
        return {"status": "error", "error": "Microsoft 365 not fully configured", "warnings": []}

    engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _m365_progress_cb(info: dict):
        if not job_id:
            return
        if _is_cancelled(job_id):
            raise ImportCancelledError("Import cancelled by user")
        total = info.get("total_tables", 1)
        completed = info.get("completed_tables", 0)
        table = info.get("current_table", "")
        resources = info.get("resources_found", 0)
        msg = info.get("message", "")
        frac = (completed / total) if total > 0 else 0
        phase_pct = int(frac * 100)
        overall = step_progress_base + int(frac * step_progress_range)
        _update_job(
            job_id,
            current_progress=phase_pct,
            current_message=f"Microsoft 365: {msg}" if msg else "Microsoft 365: Querying...",
            current_phase=f"m365_discovery ({completed}/{total})",
            progress=overall,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    def _store_and_ingest(result: dict, tenant_id: str) -> dict:
        resources_detail = result.get("resources_detail", [])

        with engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for idx, r in enumerate(resources_detail):
                    if idx % 100 == 0:
                        _raise_if_cancelled(job_id)
                    conn.execute(
                        text("""\
                            INSERT INTO raw_api_responses
                                (discovery_run_id, provider, account_id, region, service,
                                 resource_type, provider_resource_id, api_call, api_response)
                            VALUES
                                (:discovery_run_id, :provider, :account_id, :region, :service,
                                 :resource_type, :provider_resource_id, :api_call, :api_response)
                        """),
                        {
                            "discovery_run_id": discovery_run_id,
                            "provider": "Microsoft 365",
                            "account_id": tenant_id,
                            "region": r.get("region", "global"),
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            tenant_id,
            cancel_check=lambda: _raise_if_cancelled(job_id),
        ))
        return ingest_result

    try:
        result = asyncio.run(import_microsoft365_resources_via_steampipe(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            db=None,
            progress_callback=_m365_progress_cb,
        ))

        ingest_result = _store_and_ingest(result, tenant_id)

        logger.info(
            "Microsoft 365 bulk import complete: %d resources",
            result.get("resources_discovered", 0),
        )

        return {
            "status": "completed",
            "resources_discovered": result.get("resources_discovered", 0),
            "assets_stored": ingest_result.get("assets_stored", 0),
            "relationships_created": ingest_result.get("relationships_created", 0),
            "warnings": result.get("warnings", []),
        }
    except ImportCancelledError:
        logger.warning("Microsoft 365 bulk import cancelled by user")
        return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
    except NetworkUnavailableError as e:
        logger.error("Network unavailable during Microsoft 365 bulk import: %s", e)
        return {"status": "network_error", "error": str(e), "warnings": []}
    except Exception as e:
        if _is_cancelled(job_id):
            logger.warning("Microsoft 365 bulk import interrupted by cancellation")
            return {"status": "cancelled", "message": "Cancelled by user", "warnings": []}
        logger.exception("Microsoft 365 bulk import failed")
        return {"status": "error", "error": str(e), "warnings": []}


# ---------------------------------------------------------------------------
# Background runner — sequential execution of configured integrations
# ---------------------------------------------------------------------------
def _run_bulk_import_in_background(
    job_id: str,
    org_id: int,
    current_user_id: int,
    integrations_to_run: Optional[list[str]] = None,
):
    """Run each integration one at a time in a background thread.

    Args:
        integrations_to_run: List of integration names to import.
            If None, all configured integrations are discovered and run.
    """
    sync_db_url = SQLALCHEMY_DATABASE_URL.replace("+asyncpg", "")

    # Clear the in-memory asset cache so this import starts fresh
    # (asset_cache.store() appends, so without this, each import run
    # would duplicate the previous run's data).
    from app.services import asset_cache
    asset_cache.clear(org_id)

    try:
        # ---------------------------------------------------------------
        # 1. Discover which integrations are configured
        # ---------------------------------------------------------------
        aws_cfg = _is_aws_configured(org_id)
        azure_cfg = _is_azure_configured(org_id)
        okta_cfg = _is_okta_configured(org_id)
        github_cfg = _is_github_configured(org_id)
        gitlab_cfg = _is_gitlab_configured(org_id)
        microsoft365_cfg = _is_microsoft365_configured(org_id)
        gcp_cfg = _is_gcp_configured(org_id)
        bitbucket_cfg = _is_bitbucket_configured(org_id)

        if integrations_to_run is None:
            integrations_to_run = []
            if aws_cfg:
                integrations_to_run.append("aws")
            if azure_cfg:
                integrations_to_run.append("azure")
            if okta_cfg:
                integrations_to_run.append("okta")
            if github_cfg:
                integrations_to_run.append("github")
            if gitlab_cfg:
                integrations_to_run.append("gitlab")
            if microsoft365_cfg:
                integrations_to_run.append("microsoft365")
            if gcp_cfg:
                integrations_to_run.append("gcp")
            if bitbucket_cfg:
                integrations_to_run.append("bitbucket")

        if not integrations_to_run:
            _update_job(
                job_id,
                status="completed",
                phase="complete",
                message="No integrations are configured. Configure AWS, Azure, Okta, GitHub, GitLab, or Microsoft 365 first.",
                progress=100,
                integrations_to_run=[],
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            return

        _update_job(job_id, status="running", phase="initializing",
                     message=f"Preparing to import from {len(integrations_to_run)} integration(s)...",
                     integrations_to_run=integrations_to_run,
                     progress=5)

        results = {}
        total_steps = len(integrations_to_run)
        warnings_acc = []

        # ---------------------------------------------------------------
        # 2. Run each integration sequentially
        # ---------------------------------------------------------------
        for step_idx, integration_name in enumerate(integrations_to_run):
            # Check if cancellation was requested before starting the next phase
            if _is_cancelled(job_id):
                logger.warning("Bulk import cancelled by user after %s", integration_name)
                results[integration_name] = {"status": "cancelled", "message": "Cancelled by user"}
                _update_job(
                    job_id,
                    status="cancelled",
                    phase="cancelled",
                    message=f"Import cancelled — stopped after {integration_name.upper()}",
                    progress=100,
                    results=results,
                    warnings=warnings_acc,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    last_activity_at=datetime.now(timezone.utc).isoformat(),
                )
                return

            step_progress_base = 5 + int((step_idx / total_steps) * 90)
            step_progress_range = int(90 / total_steps) if total_steps > 0 else 90

            _update_job(
                job_id,
                current_integration=integration_name,
                current_phase="discovering",
                current_message=f"Discovering {integration_name.upper()} resources...",
                current_progress=0,
                phase=f"importing_{integration_name}",
                message=f"Importing {integration_name.upper()} resources...",
                progress=step_progress_base,
            )

            if integration_name == "aws":
                _update_job(job_id, current_message="Querying AWS Steampipe tables...")
                result = _import_aws_phase(
                    org_id, aws_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["aws"] = result

            elif integration_name == "azure":
                _update_job(job_id, current_message="Querying Azure Steampipe tables...")
                result = _import_azure_phase(
                    org_id, azure_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["azure"] = result

            elif integration_name == "okta":
                _update_job(job_id, current_message="Discovering Okta resources via Steampipe...")
                result = _import_okta_steampipe_phase(
                    org_id, okta_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["okta"] = result

            elif integration_name == "github":
                _update_job(job_id, current_message="Discovering GitHub resources via Steampipe...")
                result = _import_github_phase(
                    org_id, github_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["github"] = result

            elif integration_name == "gitlab":
                _update_job(job_id, current_message="Discovering GitLab resources via Steampipe...")
                result = _import_gitlab_phase(
                    org_id, gitlab_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["gitlab"] = result

            elif integration_name == "gcp":
                _update_job(job_id, current_message="Discovering GCP resources via Steampipe...")
                result = _import_gcp_phase(
                    org_id, gcp_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["gcp"] = result

            elif integration_name == "microsoft365":
                _update_job(job_id, current_message="Discovering Microsoft 365 Teams resources via Steampipe...")
                result = _import_microsoft365_phase(
                    org_id, microsoft365_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["microsoft365"] = result

            elif integration_name == "bitbucket":
                _update_job(job_id, current_message="Discovering Bitbucket resources via Steampipe...")
                result = _import_bitbucket_phase(
                    org_id, bitbucket_cfg, sync_db_url,
                    job_id=job_id,
                    step_progress_base=step_progress_base,
                    step_progress_range=step_progress_range,
                )
                results["bitbucket"] = result

            # Collect warnings
            if result.get("warnings"):
                warnings_acc.extend(result["warnings"])

            # Check if phase was cancelled
            if result.get("status") == "cancelled":
                logger.warning("Bulk import cancelled during %s", integration_name)
                _update_job(
                    job_id,
                    status="cancelled",
                    phase="cancelled",
                    message=f"Import cancelled during {integration_name.upper()}",
                    progress=100,
                    results=results,
                    warnings=warnings_acc,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    last_activity_at=datetime.now(timezone.utc).isoformat(),
                )
                return

            # Network outage — stop the WHOLE import rather than skipping
            # the failing provider and "completing" with zero assets.
            if result.get("status") == "network_error":
                logger.error(
                    "Bulk import stopped — network connection lost during %s",
                    integration_name,
                )
                _update_job(
                    job_id,
                    status="error",
                    phase="error",
                    message=f"Import failed — network connection lost during {integration_name.upper()}. "
                            "Check the connection and click Retry Now.",
                    error=result.get("error") or "Network connection lost",
                    progress=100,
                    results=results,
                    warnings=warnings_acc,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    last_activity_at=datetime.now(timezone.utc).isoformat(),
                )
                return

            # Check for fatal error
            if result.get("status") == "error":
                # If a cancellation was requested while this phase was running,
                # treat the failure as a cancellation and stop right away rather
                # than continuing to the next integration.
                if _is_cancelled(job_id):
                    logger.warning(
                        "Bulk import cancelled — %s phase interrupted by cancellation",
                        integration_name,
                    )
                    _update_job(
                        job_id,
                        status="cancelled",
                        phase="cancelled",
                        message=f"Import cancelled during {integration_name.upper()}",
                        progress=100,
                        results=results,
                        warnings=warnings_acc,
                        completed_at=datetime.now(timezone.utc).isoformat(),
                        last_activity_at=datetime.now(timezone.utc).isoformat(),
                    )
                    return
                logger.warning(
                    "%s bulk import phase failed: %s",
                    integration_name, result.get("error", "Unknown error"),
                )
                # Continue to the next integration rather than aborting

        # ---------------------------------------------------------------
        # 3. Finalise
        # ---------------------------------------------------------------
        if _is_cancelled(job_id):
            logger.warning("Bulk import cancelled before finalise")
            _update_job(
                job_id,
                status="cancelled",
                phase="cancelled",
                message="Import cancelled",
                progress=100,
                results=results,
                warnings=warnings_acc,
                completed_at=datetime.now(timezone.utc).isoformat(),
                last_activity_at=datetime.now(timezone.utc).isoformat(),
            )
            return

        _update_job(
            job_id,
            status="completed",
            phase="complete",
            message="Bulk import complete!",
            progress=100,
            results=results,
            warnings=warnings_acc,
            completed_at=datetime.now(timezone.utc).isoformat(),
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Bulk import failed with unexpected error")
        _update_job(
            job_id,
            status="error",
            phase="error",
            message=str(e),
            error=str(e),
            completed_at=datetime.now(timezone.utc).isoformat(),
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


class BulkConfigResponse(BaseModel):
    aws_configured: bool = False
    azure_configured: bool = False
    okta_configured: bool = False
    github_configured: bool = False
    gitlab_configured: bool = False
    microsoft365_configured: bool = False
    gcp_configured: bool = False
    bitbucket_configured: bool = False
    integrations_to_run: list[str] = []


class BulkSyncRequest(BaseModel):
    integrations: list[str] = []


class BulkSyncStartResponse(BaseModel):
    job_id: str
    status: str
    message: str


class BulkStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    phase: str
    message: str
    integrations_to_run: list[str] = []
    current_integration: str = ""
    current_phase: str = ""
    current_message: str = ""
    current_progress: int = 0
    results: dict = {}
    error: Optional[str] = None
    warnings: list = []
    cancelled: bool = False
    started_at: str
    completed_at: Optional[str] = None
    last_activity_at: Optional[str] = None


@router.get("/config", response_model=BulkConfigResponse)
async def get_bulk_config(current_user: CurrentUserDep):
    """Check which integrations are configured and ready to import."""
    org_id = current_user.organization_id
    aws_cfg = _is_aws_configured(org_id)
    azure_cfg = _is_azure_configured(org_id)
    okta_cfg = _is_okta_configured(org_id)
    github_cfg = _is_github_configured(org_id)
    gitlab_cfg = _is_gitlab_configured(org_id)
    microsoft365_cfg = _is_microsoft365_configured(org_id)
    gcp_cfg = _is_gcp_configured(org_id)
    bitbucket_cfg = _is_bitbucket_configured(org_id)

    integrations = []
    if aws_cfg:
        integrations.append("aws")
    if azure_cfg:
        integrations.append("azure")
    if okta_cfg:
        integrations.append("okta")
    if github_cfg:
        integrations.append("github")
    if gitlab_cfg:
        integrations.append("gitlab")
    if microsoft365_cfg:
        integrations.append("microsoft365")
    if gcp_cfg:
        integrations.append("gcp")
    if bitbucket_cfg:
        integrations.append("bitbucket")

    return BulkConfigResponse(
        aws_configured=bool(aws_cfg),
        azure_configured=bool(azure_cfg),
        okta_configured=bool(okta_cfg),
        github_configured=bool(github_cfg),
        gitlab_configured=bool(gitlab_cfg),
        microsoft365_configured=bool(microsoft365_cfg),
        gcp_configured=bool(gcp_cfg),
        bitbucket_configured=bool(bitbucket_cfg),
        integrations_to_run=integrations,
    )


@router.post("/sync", response_model=BulkSyncStartResponse)
async def start_bulk_sync(
    body: BulkSyncRequest,
    current_user: CurrentUserDep,
):
    """Start a sequential bulk import of selected integrations.

    If ``integrations`` is empty, imports all configured integrations.
    Otherwise only imports the requested ones (e.g. ["aws", "okta"]).
    """
    org_id = current_user.organization_id

    # Check which integrations are configured
    aws_cfg = _is_aws_configured(org_id)
    azure_cfg = _is_azure_configured(org_id)
    okta_cfg = _is_okta_configured(org_id)
    github_cfg = _is_github_configured(org_id)
    gitlab_cfg = _is_gitlab_configured(org_id)
    microsoft365_cfg = _is_microsoft365_configured(org_id)
    gcp_cfg = _is_gcp_configured(org_id)
    bitbucket_cfg = _is_bitbucket_configured(org_id)

    # Build the requested list
    requested = body.integrations or []
    configured_map = {
        "aws": aws_cfg, "azure": azure_cfg,
        "okta": okta_cfg, "github": github_cfg,
        "gitlab": gitlab_cfg,
        "microsoft365": microsoft365_cfg,
        "gcp": gcp_cfg,
        "bitbucket": bitbucket_cfg,
    }

    integrations_to_run = []
    if not requested:
        # Import all configured
        for name in ["aws", "azure", "okta", "github", "gitlab", "microsoft365", "gcp", "bitbucket"]:
            if configured_map[name]:
                integrations_to_run.append(name)
    else:
        # Only import requested ones that are actually configured
        for name in requested:
            if name in configured_map and configured_map[name]:
                integrations_to_run.append(name)

    if not integrations_to_run:
        raise HTTPException(
            status_code=400,
            detail="No integrations are configured for the selected options. "
                    "Configure AWS, Azure, Okta, GitHub, GitLab, or Microsoft 365 first.",
        )

    # Pass the specific list to the background runner
    job_id = _create_job(org_id)
    _cleanup_old_jobs()

    thread = threading.Thread(
        target=_run_bulk_import_in_background,
        args=(job_id, org_id, current_user.id, integrations_to_run),
        daemon=True,
    )
    thread.start()

    configured_labels = {"aws": "AWS", "azure": "Azure", "okta": "Okta", "github": "GitHub", "gitlab": "GitLab", "microsoft365": "Microsoft 365", "gcp": "GCP", "bitbucket": "Bitbucket"}
    labels = [configured_labels[n] for n in integrations_to_run]

    return BulkSyncStartResponse(
        job_id=job_id,
        status="started",
        message=f"Sequential import started for: {', '.join(labels)}",
    )


@router.get("/sync-status/{job_id}", response_model=BulkStatusResponse)
async def bulk_sync_status(job_id: str):
    """Get the current status of a bulk import job."""
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return BulkStatusResponse(**job)


@router.post("/cancel/{job_id}")
async def cancel_bulk_import(job_id: str):
    """Request cancellation of a running bulk import job."""
    with _jobs_lock:
        job = _import_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        current_status = job.get("status")
        if current_status in ("completed", "cancelled", "error"):
            return {"job_id": job_id, "status": current_status, "message": "Job is already finished."}
        
        # Set the cancellation flag — the background thread checks this
        job["cancelled"] = True
        job["message"] = "Cancellation requested..."
        job["phase"] = "cancelling"
        job["last_activity_at"] = datetime.now(timezone.utc).isoformat()

    # Kill any running Steampipe subprocesses immediately
    killed = kill_steampipe_processes()

    logger.info(
        "Cancellation requested for bulk import job %s (killed %d processes)",
        job_id, killed,
    )
    return {
        "job_id": job_id,
        "status": "cancelling",
        "message": f"Cancellation requested. Killed {killed} running query(s). The import will stop shortly.",
    }
