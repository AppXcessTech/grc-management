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
from app.services.steampipe_azure import import_azure_resources_via_steampipe, validate_azure_connection
from app.services.ingestion import IngestionService
from app.utils.crypto import encrypt_value, decrypt_value

router = APIRouter(prefix="/api/integrations/azure", tags=["integrations"])

CONFIG_DIR = Path("data/azure_config")
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


AZURE_REGIONS = [
    "eastus", "eastus2", "westus", "westus2", "westus3",
    "centralus", "northcentralus", "southcentralus",
    "northeurope", "westeurope",
    "eastasia", "southeastasia",
    "japaneast", "japanwest",
    "australiaeast", "australiasoutheast",
    "brazilsouth",
    "canadacentral", "canadaeast",
    "uksouth", "ukwest",
    "francecentral",
    "germanywestcentral",
    "norwayeast",
    "koreacentral", "koreasouth",
    "indiawest", "indiacentral", "indiasouth",
    "switzerlandnorth",
    "uaenorth",
    "southafricanorth",
    "swedencentral",
]


class AzureConfigRequest(BaseModel):
    subscription_id: str
    tenant_id: str
    client_id: str
    client_secret: str = ""
    account_name: str = ""
    region: str = "eastus"


class AzureConfigResponse(BaseModel):
    subscription_id: str
    tenant_id: str
    client_id: str
    account_name: str
    region: str
    configured: bool


class TestResult(BaseModel):
    success: bool
    subscription_id: str = ""
    tenant_id: str = ""
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


def _config_path(org_id: int) -> Path:
    return CONFIG_DIR / f"org_{org_id}.json"


def _load_config(org_id: int) -> dict:
    path = _config_path(org_id)
    if path.exists():
        cfg = json.loads(path.read_text())
        # Decrypt the client_secret if it was encrypted
        if cfg.get("client_secret"):
            try:
                cfg["client_secret"] = decrypt_value(cfg["client_secret"])
            except Exception:
                pass  # might not be encrypted (legacy)
        return cfg
    return {}


def _save_config(org_id: int, data: dict):
    existing = {}
    path = _config_path(org_id)
    if path.exists():
        existing = json.loads(path.read_text())

    # Preserve existing client_secret if a new one is not provided
    if not data.get("client_secret", "").strip():
        if existing.get("client_secret"):
            data["client_secret"] = existing["client_secret"]

    # Encrypt the client_secret before storing
    if data.get("client_secret", "").strip():
        data["client_secret"] = encrypt_value(data["client_secret"])

    # Only store encrypted form — never store raw secret in the file
    to_store = dict(data)
    to_store["client_secret"] = data["client_secret"] if data.get("client_secret") else ""
    _config_path(org_id).write_text(json.dumps(to_store, indent=2))


def _run_import_in_background(
    job_id: str,
    org_id: int,
    subscription_id: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    account_name: str,
):
    """Run the import in a background thread, updating job progress."""
    import asyncio
    import json as json_module
    from sqlalchemy import create_engine, text
    from uuid import uuid4

    # Clear the in-memory asset cache so this import starts fresh
    from app.services import asset_cache
    asset_cache.clear(org_id)

    sync_db_url = SQLALCHEMY_DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_db_url, pool_pre_ping=True)

    def _store_and_ingest(result: dict) -> dict:
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
                            "provider": "Azure",
                            "account_id": subscription_id,
                            "region": r.get("region"),
                            "service": r["resource_type"],
                            "resource_type": r["resource_type"],
                            "provider_resource_id": r["resource_id"],
                            "api_call": "steampipe_query",
                            "api_response": json_module.dumps(r["details"]),
                        },
                    )

        svc = IngestionService()
        ingest_result = asyncio.run(svc.ingest_from_result(
            org_id,
            result,
            "global",
            subscription_id,
        ))
        return ingest_result

    try:
        _update_job(job_id, status="running", phase="discovering", message="Discovering Azure resources...")

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

        result = asyncio.run(import_azure_resources_via_steampipe(
            subscription_id, tenant_id, client_id, client_secret,
            account_name=account_name, db=None,
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


@router.post("/setup")
async def setup_azure(body: AzureConfigRequest, current_user: CurrentUserDep, db: DBSessionDep):
    _save_config(current_user.organization_id, body.model_dump())

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="azure_setup",
        resource_type="integration",
        new_values={"azure_configured": True},
    ))
    await db.commit()

    return {"success": True, "message": "Azure configuration saved."}


@router.get("/config", response_model=AzureConfigResponse)
async def get_config(current_user: CurrentUserDep):
    cfg = _load_config(current_user.organization_id)
    return AzureConfigResponse(
        subscription_id=cfg.get("subscription_id", ""),
        tenant_id=cfg.get("tenant_id", ""),
        client_id=cfg.get("client_id", ""),
        account_name=cfg.get("account_name", ""),
        region=cfg.get("region", "eastus"),
        configured=bool(cfg.get("subscription_id") and cfg.get("tenant_id") and cfg.get("client_id")),
    )


@router.post("/test", response_model=TestResult)
async def test_azure(current_user: CurrentUserDep):
    cfg = _load_config(current_user.organization_id)
    subscription_id = cfg.get("subscription_id", "")
    tenant_id = cfg.get("tenant_id", "")
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")

    if not all([subscription_id, tenant_id, client_id, client_secret]):
        raise HTTPException(status_code=400, detail="Azure not configured. Save configuration first.")

    conn = validate_azure_connection(subscription_id, tenant_id, client_id, client_secret)
    if not conn["success"]:
        return TestResult(success=False, error=conn.get("error", "Unknown error"))
    return TestResult(
        success=True,
        subscription_id=conn.get("subscription_id", subscription_id),
        tenant_id=conn.get("tenant_id", tenant_id),
    )


@router.post("/sync", response_model=SyncStartResponse)
async def sync_azure(current_user: CurrentUserDep):
    """Start an async Azure import and return immediately with a job_id."""
    cfg = _load_config(current_user.organization_id)
    subscription_id = cfg.get("subscription_id", "")
    tenant_id = cfg.get("tenant_id", "")
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    account_name = cfg.get("account_name", "")

    if not all([subscription_id, tenant_id, client_id, client_secret]):
        raise HTTPException(status_code=400, detail="Azure not configured.")

    conn = validate_azure_connection(subscription_id, tenant_id, client_id, client_secret)
    if not conn["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Azure connection failed: {conn.get('error', 'Unknown error')}",
        )

    job_id = _create_job(current_user.organization_id)
    _cleanup_old_jobs()

    thread = threading.Thread(
        target=_run_import_in_background,
        args=(job_id, current_user.organization_id, subscription_id, tenant_id, client_id, client_secret, account_name),
        daemon=True,
    )
    thread.start()

    return SyncStartResponse(
        job_id=job_id,
        status="started",
        message="Import started. Poll /api/integrations/azure/sync-status/{job_id} for progress.",
    )


@router.get("/sync-status/{job_id}", response_model=ImportStatusResponse)
async def sync_status(job_id: str):
    """Get the current status of an async import job."""
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ImportStatusResponse(**job)
