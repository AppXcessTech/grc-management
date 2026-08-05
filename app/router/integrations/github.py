import asyncio
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.database import SQLALCHEMY_DATABASE_URL
from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.audit_log import AuditLog
from app.services.steampipe_github import import_github_resources_via_steampipe, validate_github_connection
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/integrations/github", tags=["integrations"])

CONFIG_DIR = Path("data/github_config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# In-memory job tracking for async imports
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
            "message": "Starting import...",
            "total_tables": 0,
            "completed_tables": 0,
            "current_table": "",
            "resources_found": 0,
            "resources_discovered": 0,
            "assets_stored": 0,
            "relationships_created": 0,
            "error": None,
            "warnings": [],
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


def _cleanup_old_jobs():
    """Remove jobs older than 1 hour."""
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
# Pydantic models
# ---------------------------------------------------------------------------
class GitHubConfigRequest(BaseModel):
    github_token: str
    classic_token: str | None = None
    account_name: str = ""


class GitHubConfigResponse(BaseModel):
    account_name: str
    configured: bool
    has_classic_token: bool = False


class TestResult(BaseModel):
    success: bool
    users_found: int = 0
    error: str = ""


class ImportStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    phase: str
    message: str
    total_tables: int
    completed_tables: int
    current_table: str
    resources_found: int
    resources_discovered: int
    assets_stored: int
    relationships_created: int
    error: Optional[str] = None
    warnings: list[dict] = []
    started_at: str
    completed_at: Optional[str] = None
    last_activity_at: Optional[str] = None


class SyncStartResponse(BaseModel):
    job_id: str
    status: str
    message: str


class SyncResult(BaseModel):
    status: str
    message: str
    resources_discovered: int
    assets_stored: int
    relationships_created: int


# ---------------------------------------------------------------------------
# Config file helpers
# ---------------------------------------------------------------------------
def _config_path(org_id: int) -> Path:
    return CONFIG_DIR / f"org_{org_id}.json"


def _load_config(org_id: int) -> dict:
    path = _config_path(org_id)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_config(org_id: int, data: dict):
    _config_path(org_id).write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Background import runner
# ---------------------------------------------------------------------------
def _run_import_in_background(
    job_id: str,
    org_id: int,
    github_token: str,
    classic_token: str | None = None,
):
    """Run the import in a background thread, updating job progress.

    Uses synchronous SQLAlchemy because the async engine is attached
    to the main thread's event loop.
    """
    import asyncio
    import json as json_module
    from sqlalchemy import create_engine, text

    # Clear the in-memory asset cache so this import starts fresh
    from app.services import asset_cache
    asset_cache.clear(org_id)

    sync_db_url = SQLALCHEMY_DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _store_and_ingest(result: dict) -> dict:
        """Store raw API responses and run ingestion synchronously."""
        resources_detail = result.get("resources_detail", [])

        with sync_engine.begin() as conn:
            if resources_detail:
                discovery_run_id = str(uuid4())
                for r in resources_detail:
                    conn.execute(
                        text("""
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
                            "region": "global",
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json_module.dumps(r["details"]),
                        },
                    )

        # Run ingestion
        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            "github",
        ))
        return ingest_result

    try:
        _update_job(job_id, status="running", phase="discovering", message="Discovering GitHub resources...")

        def progress_callback(data: dict):
            _update_job(
                job_id,
                total_tables=data.get("total_tables", 0),
                completed_tables=data.get("completed_tables", 0),
                current_table=data.get("current_table", ""),
                resources_found=data.get("resources_found", 0),
                phase="discovering",
                status="running",
                message=data.get("message", "Discovering resources..."),
                progress=int(data.get("completed_tables", 0) / max(data.get("total_tables", 1), 1) * 80),
                warnings=data.get("warnings", []),
                last_activity_at=datetime.now(timezone.utc).isoformat(),
            )

        # Run the Steampipe discovery with both tokens
        result = asyncio.run(import_github_resources_via_steampipe(
            github_token,
            classic_token=classic_token,
            db=None,
            progress_callback=progress_callback,
        ))

        all_warnings = result.get("warnings", [])

        _update_job(
            job_id,
            phase="ingesting",
            message="Storing discovered assets...",
            progress=85,
            resources_discovered=result.get("resources_discovered", 0),
            warnings=all_warnings,
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

        # Store and ingest using synchronous DB
        ingest_result = _store_and_ingest(result)

        _update_job(
            job_id,
            status="completed",
            phase="complete",
            message="Import complete!",
            progress=100,
            resources_discovered=result.get("resources_discovered", 0),
            assets_stored=ingest_result.get("assets_stored", 0),
            relationships_created=ingest_result.get("relationships_created", 0),
            warnings=all_warnings,
            completed_at=datetime.now(timezone.utc).isoformat(),
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        _update_job(
            job_id,
            status="error",
            phase="error",
            message=str(e),
            error=str(e),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@router.post("/setup")
async def setup_github(body: GitHubConfigRequest, current_user: CurrentUserDep, db: DBSessionDep):
    existing = _load_config(current_user.organization_id)

    # Build merged config preserving existing secrets when incoming is empty
    incoming = body.model_dump(exclude_unset=True)
    merged = {}

    # Fine-grained token: keep existing if incoming is empty
    if incoming.get("github_token"):
        merged["github_token"] = incoming["github_token"]
    elif existing.get("github_token"):
        merged["github_token"] = existing["github_token"]
    else:
        merged["github_token"] = ""

    # Classic token: keep existing if incoming is empty
    if incoming.get("classic_token"):
        merged["classic_token"] = incoming["classic_token"]
    elif existing.get("classic_token"):
        merged["classic_token"] = existing["classic_token"]
    # else: don't set classic_token at all (not configured)

    # Account name: always use incoming if provided, else keep existing
    merged["account_name"] = incoming.get("account_name", existing.get("account_name", ""))

    _save_config(current_user.organization_id, merged)

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="github_setup",
        resource_type="integration",
        new_values={"github_configured": True},
    ))
    await db.commit()

    token_types = []
    if merged.get("github_token"):
        token_types.append("fine-grained")
    if merged.get("classic_token"):
        token_types.append("classic")
    return {
        "success": True,
        "message": "GitHub configuration saved. "
                   f"Tokens configured: {', '.join(token_types) or 'none'}.",
    }


@router.get("/config", response_model=GitHubConfigResponse)
async def get_config(current_user: CurrentUserDep):
    cfg = _load_config(current_user.organization_id)
    return GitHubConfigResponse(
        account_name=cfg.get("account_name", ""),
        configured=bool(cfg.get("github_token")),
        has_classic_token=bool(cfg.get("classic_token")),
    )


@router.post("/test", response_model=TestResult)
async def test_github(current_user: CurrentUserDep):
    cfg = _load_config(current_user.organization_id)
    github_token = cfg.get("github_token", "")

    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured. Save configuration first.")

    conn = validate_github_connection(github_token)
    if not conn["success"]:
        return TestResult(success=False, error=conn.get("error", "Unknown error"))
    return TestResult(success=True, users_found=conn.get("users_found", 0))


@router.post("/sync", response_model=SyncStartResponse)
async def sync_github(current_user: CurrentUserDep):
    """Start an async GitHub import and return immediately with a job_id."""
    cfg = _load_config(current_user.organization_id)
    github_token = cfg.get("github_token", "")
    classic_token = cfg.get("classic_token") or None

    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub not configured.")

    conn = validate_github_connection(github_token)
    if not conn["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub connection failed: {conn.get('error', 'Unknown error')}",
        )

    # Create a job and run import in background
    job_id = _create_job(current_user.organization_id)
    _cleanup_old_jobs()

    token_msg = "(fine-grained + classic)" if classic_token else "(fine-grained only)"

    thread = threading.Thread(
        target=_run_import_in_background,
        args=(job_id, current_user.organization_id, github_token, classic_token),
        daemon=True,
    )
    thread.start()

    return SyncStartResponse(
        job_id=job_id,
        status="started",
        message=f"Import started {token_msg}. Poll /api/integrations/github/sync-status/{{job_id}} for progress.",
    )


@router.get("/sync-status/{job_id}", response_model=ImportStatusResponse)
async def sync_status(job_id: str):
    """Get the current status of an async import job."""
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ImportStatusResponse(**job)
