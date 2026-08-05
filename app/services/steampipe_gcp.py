"""
Dynamic Steampipe-based GCP resource discovery.
Uses GCP_STEAMPIPE_TABLE_TO_TYPE from mappers/canonical_map.py to determine
which tables to query and how to map each discovered resource to a
CanonicalType.

GCP resources are discovered via the Steampipe GCP plugin, which uses
a service account JSON key for authentication. All discovered resources
are mapped to canonical types like Compute, Storage, Database, etc.

Performance design:
  - Queries use `SELECT * FROM <table>` (one subprocess per table)
  - Table queries run in parallel via ThreadPoolExecutor (max 5 concurrent)
  - Per-query timeout (120s) + overall timeout (600s) prevent hanging
"""
import json
import tempfile
import subprocess
import logging
import concurrent.futures
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.mappers.canonical_map import GCP_STEAMPIPE_TABLE_TO_TYPE
from app.services.steampipe_process import (
    ImportCancelledError,
    NetworkUnavailableError,
    MAX_QUERY_ATTEMPTS,
    handle_query_failure,
    kill_all,
    register,
    set_network_probe_url,
    unregister,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuning knobs
# ---------------------------------------------------------------------------
MAX_CONCURRENT_QUERIES = 5       # Steampipe processes to run in parallel
PER_QUERY_TIMEOUT_SEC = 120      # Seconds before a single table query is abandoned
OVERALL_TIMEOUT_SEC = 600        # Seconds before the entire import is abandoned


# ===================================================================
# 1. Helper: resolve a stable resource_id from a row (GCP-specific)
# ===================================================================
def resolve_resource_id(row: dict) -> str:
    """Pick the best identifier from a GCP Steampipe row.

    GCP resources use 'id', 'name', or 'self_link' as primary identifiers.
    """
    for key in (
        "id",
        "name",
        "self_link",
        "resource_id",
        "instance_id",
        "instance_name",
        "cluster_name",
        "cluster_id",
        "certificate_id",
        "key_ring_name",
        "key_name",
        "secret_id",
        "bucket",
        "bucket_name",
        "dataset_id",
        "database_id",
        "instance",
        "display_name",
        "project",
    ):
        val = row.get(key)
        if val and isinstance(val, str):
            return val
    # Last resort - first non-null value
    for v in row.values():
        if v and isinstance(v, str):
            return v
    return "unknown"


# ===================================================================
# 2. Extract labels from a row (GCP uses 'labels' instead of 'tags')
# ===================================================================
def extract_labels(row: dict) -> list[dict] | dict | None:
    """Normalise GCP labels to a standard tags format.

    GCP resources store metadata as 'labels' dicts (key-value pairs).
    """
    raw = row.get("labels") or row.get("Labels")
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            if "Key" in raw[0] or "key" in raw[0]:
                return raw
            return [{"Key": t.get("key", t.get("Key", "")), "Value": t.get("value", t.get("Value", ""))} for t in raw]
    if isinstance(raw, dict):
        return raw
    return None


# ===================================================================
# 3. Run a single Steampipe query
# ===================================================================
def run_query(sql: str, install_dir: str, timeout_sec: int = PER_QUERY_TIMEOUT_SEC) -> list[dict]:
    """Execute a Steampipe SQL query and return parsed rows."""
    cmd = ["steampipe", "query", sql, "--install-dir", install_dir, "--output", "json"]
    proc = None
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        register(proc)
        stdout, stderr = proc.communicate(timeout=timeout_sec)
        res = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
        if res.returncode != 0:
            logger.warning("Steampipe query returned %d: %s", res.returncode, res.stderr[:500])
            return []
        if res.stderr and res.stderr.strip():
            logger.warning("Steampipe query stderr: %s", res.stderr[:500])
        data = json.loads(res.stdout)
        rows = data.get("rows", [])
        logger.debug("  Query returned %d rows", len(rows))
        return rows
    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
        logger.warning("Steampipe query timed out after %ds: %.80s...", timeout_sec, sql)
        return []
    except json.JSONDecodeError as e:
        logger.warning("Steampipe JSON parse error: %s", e)
        return []
    except Exception as e:
        logger.warning("Steampipe query failed: %s", e)
        return []
    finally:
        if proc:
            unregister(proc)


# ===================================================================
# 4. Derive status from common GCP status fields
# ===================================================================
def _derive_status(row: dict) -> str | None:
    """Extract a status string from common GCP row fields."""
    for key in ("status", "state", "lifecycle_state", "lifecycle"):
        val = row.get(key)
        if val and isinstance(val, str):
            return val
    return None


# ===================================================================
# 5. Query a single GCP table
# ===================================================================
def _query_table(
    table_name: str,
    canonical_type: str,
    install_dir: str,
) -> tuple[list[dict], list[dict]]:
    """Query a single GCP Steampipe table and produce resource entries.

    Returns:
        (entries, structured_warnings)
    """
    sql = f"select * from {table_name};"
    cmd = ["steampipe", "query", sql, "--install-dir", install_dir, "--output", "json"]
    warnings: list[dict] = []
    rows: list[dict] = []

    for attempt in range(MAX_QUERY_ATTEMPTS):
        proc = None
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            register(proc)
            stdout, stderr = proc.communicate(timeout=PER_QUERY_TIMEOUT_SEC)
            res = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)

            if res.stderr and res.stderr.strip():
                logger.warning("Steampipe query stderr for %s: %s", table_name, res.stderr[:500])

            if res.returncode != 0:
                if handle_query_failure(res.stderr or ""):
                    logger.warning(
                        "Network recovered — retrying %s (attempt %d)", table_name, attempt + 1,
                    )
                    continue
                logger.warning("Steampipe query returned %d for %s: %s", res.returncode, table_name, res.stderr[:500])
                return [], warnings

            data = json.loads(res.stdout)
            rows = data.get("rows", [])
            logger.debug("  %s -> %d rows", table_name, len(rows))
            break
        except subprocess.TimeoutExpired:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            if handle_query_failure("", timed_out=True):
                logger.warning(
                    "Network recovered — retrying timed-out query for %s (attempt %d)", table_name, attempt + 1,
                )
                continue
            logger.warning("Steampipe query timed out for %s", table_name)
            return [], warnings + [{
                "service": "GCP",
                "action": "Query",
                "resource": "",
                "table": table_name,
                "message": f"Query for {table_name} timed out after {PER_QUERY_TIMEOUT_SEC}s",
            }]
        except json.JSONDecodeError as e:
            logger.warning("Steampipe JSON parse error for %s: %s", table_name, e)
            return [], warnings
        except NetworkUnavailableError:
            raise
        except Exception as e:
            logger.warning("Steampipe query failed for %s: %s", table_name, e)
            return [], warnings
        finally:
            if proc:
                unregister(proc)
    else:
        # Loop exhausted after repeated network flaps — give up on this table
        return [], warnings

    if not rows:
        return [], warnings

    entries = []
    for row in rows:
        # GCP IAM role filtering: skip predefined (GCP-managed) roles —
        # only import custom roles that are actually in use
        if table_name == "gcp_iam_role" and row.get("is_gcp_managed", True):
            continue

        rid = resolve_resource_id(row)
        labels = extract_labels(row)
        status = _derive_status(row)

        # Build display name
        name = (
            row.get("name")
            or row.get("Name")
            or row.get("display_name")
            or row.get("instance_name")
            or row.get("cluster_name")
            or row.get("bucket")
            or row.get("key_ring_name")
            or row.get("key_name")
            or rid
        )

        entry = {
            "resource_type": table_name,
            "resource_id": rid,
            "canonical_type": canonical_type,
            "region": row.get("region", "global"),
            "provider": "GCP",
            "name": name,
            "display_name": name,
            "tags": labels,
            "status": status,
            "details": row,
        }

        # Extract common relationship references
        relationships = {}
        for ref_key in (
            "network", "subnetwork", "vpc_id", "project",
            "cluster_name", "zone", "region",
        ):
            if ref_key in row:
                relationships[ref_key] = row[ref_key]
        if relationships:
            entry["relationships"] = relationships

        entries.append(entry)

    return entries, warnings


# ===================================================================
# 6. Main import function
# ===================================================================
async def import_gcp_resources_via_steampipe(
    credentials_json: str,
    project_id: Optional[str] = None,
    db=None,
    progress_callback: Optional[callable] = None,
) -> dict:
    """
    Discover GCP resources via Steampipe using service account credentials.

    Flow:
      1. Write the service account JSON to a temp file
      2. Create a temporary Steampipe config directory with GCP credentials
      3. Read GCP_STEAMPIPE_TABLE_TO_TYPE to know which tables to query
      4. For each table, run ``SELECT * FROM <table>`` **in parallel**
         (up to MAX_CONCURRENT_QUERIES at a time, each with a timeout)
      5. Map each result to the appropriate canonical type
      6. Return structured data ready for ingestion
    """
    # ---------------------------------------------------------------
    # 1. Write credentials to a temp file
    # ---------------------------------------------------------------
    with tempfile.TemporaryDirectory() as temp_dir:
        # Symlink Steampipe installation folders
        steampipe_home = Path.home() / ".steampipe"
        for folder in ["plugins", "db", "internal"]:
            src = steampipe_home / folder
            dst = Path(temp_dir) / folder
            if src.exists() and not dst.exists():
                dst.symlink_to(src, target_is_directory=True)

        # Write the service account key file
        key_path = Path(temp_dir) / "gcp_credentials.json"
        key_path.write_text(credentials_json)

        # Write gcp.spc with service account credentials
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        creds_file_path = str(key_path)
        spc_lines = [
            'connection "gcp" {',
            '  plugin = "gcp"',
            f'  credential_file = "{creds_file_path}"',
        ]
        if project_id:
            spc_lines.append(f'  project = "{project_id}"')
        spc_lines.append("}")
        spc = "\n".join(spc_lines) + "\n"

        (config_dir / "gcp.spc").write_text(spc)

        # Point the network gate at the GCP OAuth endpoint so a connectivity
        # probe checks the same network path the Steampipe plugin uses.
        set_network_probe_url("https://oauth2.googleapis.com")

        # ---------------------------------------------------------------
        # 2. Load table-to-type mapping
        # ---------------------------------------------------------------
        if not GCP_STEAMPIPE_TABLE_TO_TYPE:
            logger.error("GCP_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
            return {
                "project_id": project_id or "unknown",
                "resources_discovered": 0,
                "resources_detail": [],
            }

        # Build the list of table-query tasks
        tasks = []
        for table_name, canonical_type in GCP_STEAMPIPE_TABLE_TO_TYPE.items():
            tasks.append((table_name, canonical_type, temp_dir))

        all_resources: list[dict] = []
        all_warnings: list[dict] = []

        logger.info(
            "Starting parallel discovery of %d GCP tables (max %d concurrent, %ds per-query timeout)",
            len(tasks), MAX_CONCURRENT_QUERIES, PER_QUERY_TIMEOUT_SEC,
        )

        # Notify initial progress
        if progress_callback:
            progress_callback({
                "total_tables": len(tasks),
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": f"Starting discovery of {len(tasks)} GCP resource types...",
                "warnings": [],
            })

        completed = 0

        # Run table queries in the thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_QUERIES) as pool:
            future_map = {
                pool.submit(_query_table, t, ct, td): t
                for t, ct, td in tasks
            }

            try:
                for future in concurrent.futures.as_completed(future_map, timeout=OVERALL_TIMEOUT_SEC):
                    table = future_map[future]
                    completed += 1
                    try:
                        entries, table_warnings = future.result()
                        if entries:
                            logger.info("  %s -> %d resources", table, len(entries))
                            all_resources.extend(entries)
                        else:
                            logger.debug("  %s -> 0 resources", table)
                        if table_warnings:
                            all_warnings.extend(table_warnings)
                    except concurrent.futures.CancelledError:
                        logger.warning("  %s -> cancelled (timeout)", table)
                        all_warnings.append({
                            "service": "GCP",
                            "action": "Timeout",
                            "resource": "",
                            "table": table,
                            "message": f"Query for {table} was cancelled due to overall timeout",
                        })
                    except (ImportCancelledError, NetworkUnavailableError):
                        raise
                    except Exception as e:
                        logger.warning("  %s -> error: %s", table, e)
                        all_warnings.append({
                            "service": "GCP",
                            "action": "Error",
                            "resource": "",
                            "table": table,
                            "message": f"{table}: {str(e)[:200]}",
                        })

                    if progress_callback:
                        progress_callback({
                            "total_tables": len(tasks),
                            "completed_tables": completed,
                            "current_table": table,
                            "resources_found": len(all_resources),
                            "message": f"Queried {table} ({completed}/{len(tasks)})",
                            "warnings": all_warnings[-20:],
                        })
            except concurrent.futures.TimeoutError:
                logger.warning("Overall import timeout reached after %ds — processing partial results", OVERALL_TIMEOUT_SEC)
                all_warnings.append({
                    "service": "GCP",
                    "action": "Import",
                    "resource": "",
                    "table": "",
                    "message": f"Import timed out after {OVERALL_TIMEOUT_SEC}s — only partial results available",
                })
            except (ImportCancelledError, NetworkUnavailableError):
                # Cancellation requested or network outage — cancel queued
                # table tasks so the executor's shutdown(wait=True) below does
                # NOT drain the whole queue before the outcome is honoured.
                # Re-kill any newly spawned Steampipe subprocesses (workers may
                # have dequeued the next task and registered a fresh process
                # after the cancel endpoint's initial kill) so shutdown returns
                # immediately.
                for future, table in future_map.items():
                    if not future.done():
                        future.cancel()
                        logger.debug("Cancelled pending future for table %s", table)
                kill_all()
                raise

            for future, table in future_map.items():
                if not future.done():
                    future.cancel()
                    logger.debug("Cancelled pending future for table %s", table)

            tables_with_data = {r["resource_type"] for r in all_resources}
            logger.info(
                "Discovery complete: %d total GCP resources from %d tables",
                len(all_resources), len(tables_with_data),
            )

    # ---------------------------------------------------------------
    # 3. Determine the GCP project ID from results or input
    # ---------------------------------------------------------------
    effective_project_id = project_id or "unknown"
    if not effective_project_id or effective_project_id == "unknown":
        for r in all_resources:
            p = r.get("details", {}).get("project")
            if p:
                effective_project_id = p
                break

    # ---------------------------------------------------------------
    # 4. Build final result
    # ---------------------------------------------------------------
    discovery_run_id = str(uuid4())
    raw_api_records = []
    for r in all_resources:
        raw_api_records.append({
            "discovery_run_id": discovery_run_id,
            "provider": "GCP",
            "account_id": effective_project_id,
            "region": r.get("region", "global"),
            "service": r["resource_type"],
            "resource_type": r["resource_type"],
            "provider_resource_id": r["resource_id"],
            "api_call": "steampipe_query",
            "api_response": r["details"],
        })

    if db and raw_api_records:
        from app.models.raw_api_response import RawApiResponse
        db.add_all([RawApiResponse(**rec) for rec in raw_api_records])

    asset_results = [{**r, "action": "discovered"} for r in all_resources]

    return {
        "project_id": effective_project_id,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate GCP connection via Steampipe
# ===================================================================
def validate_gcp_connection(
    credentials_json: str,
    project_id: Optional[str] = None,
) -> dict:
    """Validate a GCP connection by running a simple Steampipe query."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            steampipe_home = Path.home() / ".steampipe"
            for folder in ["plugins", "db", "internal"]:
                src = steampipe_home / folder
                dst = Path(temp_dir) / folder
                if src.exists() and not dst.exists():
                    dst.symlink_to(src, target_is_directory=True)

            # Write the service account key file
            key_path = Path(temp_dir) / "gcp_credentials.json"
            key_path.write_text(credentials_json)

            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            creds_file_path = str(key_path)
            spc_lines = [
                'connection "gcp" {',
                '  plugin = "gcp"',
                f'  credential_file = "{creds_file_path}"',
            ]
            if project_id:
                spc_lines.append(f'  project = "{project_id}"')
            spc_lines.append("}")
            spc = "\n".join(spc_lines) + "\n"

            (config_dir / "gcp.spc").write_text(spc)

            # Run a simple query to validate connectivity
            # Steampipe GCP plugin uses 'project_id' (not 'project') as the column name
            cmd = [
                "steampipe", "query",
                "select name, project_id from gcp_project limit 1;",
                "--install-dir", temp_dir,
                "--output", "json",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if res.returncode != 0:
                return {
                    "success": False,
                    "error": res.stderr[:500] or "Steampipe query failed",
                }

            data = json.loads(res.stdout)
            rows = data.get("rows", [])
            project_count = len(rows)
            detected_project = rows[0].get("project_id", project_id or "unknown") if rows else project_id or "unknown"
            return {
                "success": True,
                "project_id": detected_project,
                "projects_found": project_count,
                "message": f"Connected to GCP Steampipe! Found {project_count} project(s).",
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Connection timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
