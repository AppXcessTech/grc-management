"""
GCP integration router with file-upload support for service account credentials.

Instead of typing a file path, users upload their GCP service account JSON key file
directly from the frontend. The backend parses the JSON, extracts the necessary fields
(project_id, client_email, private_key, etc.), encrypts the private key at rest, and
stores the full credentials for use by the Steampipe GCP plugin during resource discovery.
"""
import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel

from app.core.database import SQLALCHEMY_DATABASE_URL
from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.audit_log import AuditLog
from app.services.steampipe_gcp import (
    import_gcp_resources_via_steampipe,
    validate_gcp_connection,
)
from app.services.ingestion import IngestionService
from app.utils.crypto import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations/gcp", tags=["integrations"])

CONFIG_DIR = Path("data/gcp_config")
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


GCP_REGIONS = [
    "us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
    "northamerica-northeast1", "northamerica-northeast2",
    "southamerica-east1", "southamerica-west1",
    "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6",
    "europe-west8", "europe-west9", "europe-north1", "europe-central2",
    "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
    "asia-southeast1", "asia-southeast2", "asia-south1", "asia-south2",
    "australia-southeast1", "australia-southeast2",
    "me-central1", "me-west1",
    "africa-south1",
]


class GCPConfigResponse(BaseModel):
    project_id: str
    client_email: str
    region: str
    configured: bool


class TestResult(BaseModel):
    success: bool
    project_id: str = ""
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


def _config_path(org_id: int) -> Path:
    return CONFIG_DIR / f"org_{org_id}.json"


def _load_config(org_id: int) -> dict:
    path = _config_path(org_id)
    if path.exists():
        cfg = json.loads(path.read_text())
        # Decrypt the private_key if it was encrypted
        if cfg.get("private_key"):
            try:
                cfg["private_key"] = decrypt_value(cfg["private_key"])
            except Exception:
                pass  # might not be encrypted (legacy)
        return cfg
    return {}


def _save_config(org_id: int, data: dict):
    existing = {}
    path = _config_path(org_id)
    if path.exists():
        existing = json.loads(path.read_text())

    # Preserve existing private_key if a new one is not provided
    if not data.get("private_key", "").strip():
        if existing.get("private_key"):
            data["private_key"] = existing["private_key"]

    # Encrypt the private_key before storing
    if data.get("private_key", "").strip():
        data["private_key"] = encrypt_value(data["private_key"])

    # Also store the full credentials JSON for Steampipe
    if data.get("credentials_json", "").strip():
        data["credentials_json"] = encrypt_value(data["credentials_json"])
    else:
        # Preserve existing encrypted credentials_json
        if existing.get("credentials_json"):
            data["credentials_json"] = existing["credentials_json"]

    _config_path(org_id).write_text(json.dumps(data, indent=2))


def _decrypt_credentials_for_steampipe(cfg: dict) -> tuple[str, str]:
    """Get decrypted credentials_json and private_key for Steampipe use."""
    credentials_json = cfg.get("credentials_json", "")
    if credentials_json:
        try:
            credentials_json = decrypt_value(credentials_json)
        except Exception:
            pass  # might not be encrypted

    private_key = cfg.get("private_key", "")
    if private_key:
        try:
            private_key = decrypt_value(private_key)
        except Exception:
            pass

    return credentials_json, private_key


def _run_import_in_background(
    job_id: str,
    org_id: int,
    project_id: str,
    region: str,
):
    """Run the import in a background thread, updating job progress."""
    # Load config to get credentials
    cfg = _load_config(org_id)
    credentials_json, _ = _decrypt_credentials_for_steampipe(cfg)

    if not credentials_json:
        _update_job(
            job_id,
            status="error",
            phase="error",
            message="No GCP credentials found. Please re-configure.",
            error="Missing credentials",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        return

    import asyncio
    import json as json_module
    from sqlalchemy import create_engine, text

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
                            "provider": "GCP",
                            "account_id": project_id,
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
            region,
            project_id,
        ))
        return ingest_result

    try:
        _update_job(job_id, status="running", phase="discovering", message="Discovering GCP resources...")

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

        result = asyncio.run(import_gcp_resources_via_steampipe(
            credentials_json=credentials_json,
            project_id=project_id,
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
async def setup_gcp(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    file: UploadFile = File(None),
    project_id: str = Form(""),
    region: str = Form("us-central1"),
    client_email: str = Form(""),
):
    """Configure GCP integration.

    Accepts an uploaded GCP service account JSON key file plus optional form fields.
    If a file is provided, the backend parses the JSON and extracts:
      - project_id
      - client_email
      - private_key
      - client_id
      - private_key_id

    The full credentials JSON is encrypted and stored for Steampipe.
    Individual fields are stored for display purposes.
    """
    data = {}

    # Load existing config to check for previously stored values
    existing = _load_config(current_user.organization_id)

    if file and file.filename:
        try:
            content = await file.read()
            creds = json.loads(content)

            # Validate required fields
            if "project_id" not in creds:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid GCP service account JSON: missing 'project_id' field.",
                )
            if "private_key" not in creds:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid GCP service account JSON: missing 'private_key' field.",
                )
            if "client_email" not in creds:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid GCP service account JSON: missing 'client_email' field.",
                )

            # Store the full raw credentials JSON for Steampipe
            data["credentials_json"] = json.dumps(creds)

            # Extract individual fields
            data["project_id"] = creds.get("project_id", project_id)
            data["client_email"] = creds.get("client_email", client_email)
            data["private_key"] = creds.get("private_key", "")
            data["client_id"] = creds.get("client_id", "")
            data["private_key_id"] = creds.get("private_key_id", "")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON file. Please upload a valid GCP service account key JSON file.",
            )
    else:
        # No file uploaded — use form fields and preserve existing secrets
        data["project_id"] = project_id
        data["client_email"] = client_email
        data["region"] = region

        # If updating without uploading a new file, preserve existing credentials
        if existing.get("credentials_json"):
            data["credentials_json"] = existing["credentials_json"]
        if existing.get("private_key"):
            data["private_key"] = existing["private_key"]

    # Always apply the region field
    data["region"] = region

    # Save (encrypts sensitive fields)
    _save_config(current_user.organization_id, data)

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="gcp_setup",
        resource_type="integration",
        new_values={"gcp_configured": True},
    ))
    await db.commit()

    return {
        "success": True,
        "message": "GCP configuration saved.",
        "project_id": data.get("project_id", ""),
        "client_email": data.get("client_email", ""),
    }


@router.get("/config", response_model=GCPConfigResponse)
async def get_config(current_user: CurrentUserDep):
    cfg = _load_config(current_user.organization_id)
    return GCPConfigResponse(
        project_id=cfg.get("project_id", ""),
        client_email=cfg.get("client_email", ""),
        region=cfg.get("region", "us-central1"),
        configured=bool(cfg.get("project_id") and cfg.get("credentials_json")),
    )


@router.post("/test", response_model=TestResult)
async def test_gcp(current_user: CurrentUserDep):
    cfg = _load_config(current_user.organization_id)
    project_id = cfg.get("project_id", "")
    credentials_json, _ = _decrypt_credentials_for_steampipe(cfg)

    if not credentials_json or not project_id:
        raise HTTPException(status_code=400, detail="GCP not configured. Save configuration first.")

    conn = validate_gcp_connection(credentials_json, project_id=project_id)
    if not conn.get("success"):
        return TestResult(success=False, error=conn.get("error", "Unknown error"))
    return TestResult(
        success=True,
        project_id=conn.get("project_id", project_id),
    )


@router.post("/sync", response_model=SyncStartResponse)
async def sync_gcp(current_user: CurrentUserDep):
    """Start an async GCP import and return immediately with a job_id."""
    cfg = _load_config(current_user.organization_id)
    project_id = cfg.get("project_id", "")
    region = cfg.get("region", "us-central1")
    credentials_json, _ = _decrypt_credentials_for_steampipe(cfg)

    if not credentials_json or not project_id:
        raise HTTPException(status_code=400, detail="GCP not configured.")

    conn = validate_gcp_connection(credentials_json, project_id=project_id)
    if not conn.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GCP connection failed: {conn.get('error', 'Unknown error')}",
        )

    job_id = _create_job(current_user.organization_id)
    _cleanup_old_jobs()

    thread = threading.Thread(
        target=_run_import_in_background,
        args=(job_id, current_user.organization_id, project_id, region),
        daemon=True,
    )
    thread.start()

    return SyncStartResponse(
        job_id=job_id,
        status="started",
        message="Import started. Poll /api/integrations/gcp/sync-status/{job_id} for progress.",
    )


@router.get("/sync-status/{job_id}", response_model=ImportStatusResponse)
async def sync_status(job_id: str):
    """Get the current status of an async import job."""
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ImportStatusResponse(**job)
