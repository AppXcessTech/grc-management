"""
Dynamic Steampipe-based Okta resource discovery.
Uses Okta Steampipe table names and maps them to CanonicalTypes.

With this service, Okta resources land as Canonical Assets:
  - okta_user        →  Identity
  - okta_group       →  Group
  - okta_application →  Application
  - okta_factor      →  Policy
  - okta_device      →  Device
  - etc. (19 tables total)

This mode is scoped to **asset inventory**: each table is queried for its
identifier column only (``id`` by default) so the inventory knows *what
exists* (id + provider + canonical type) without hydrating every column.

Performance design:
  - Inventory queries select only the id column (no hydrate columns → faster,
    fewer permission warnings)
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

from app.mappers.canonical_map import OKTA_STEAMPIPE_TABLE_TO_TYPE
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

# ---------------------------------------------------------------------------
# Inventory-mode identifier column per table
# ---------------------------------------------------------------------------
# Asset inventory only needs a stable identifier per resource — the Okta ``id``.
# Querying just the id column instead of ``select *`` skips every hydrate
# column and makes imports much faster.
#
# Nearly every Okta Steampipe table exposes ``id``. The handful that don't use
# ``id`` as the YAML rule's canonical id are mapped to the column the rule
# resolves instead (mirrors the AWS ``arn`` inventory pattern).
TABLE_ID_COLUMN: dict[str, str] = {
    # One row per group-owner assignment; the rule's canonical id is the
    # group id (there is no per-assignment ``id`` column used as identity).
    "okta_group_owner": "group_id",
}


def _table_select_sql(table_name: str) -> str:
    """Build the inventory SELECT for a table — just its identifier column.

    Defaults to ``id``; tables whose canonical id isn't ``id`` are looked up
    in ``TABLE_ID_COLUMN``.
    """
    id_col = TABLE_ID_COLUMN.get(table_name, "id")
    return f"select {id_col} from {table_name};"


# ===================================================================
# 1. Helper: resolve a stable resource_id from a row (Okta-specific)
# ===================================================================
def resolve_resource_id(row: dict) -> str:
    """Pick the best identifier from an Okta Steampipe row.

    Okta resources use 'id' as the primary identifier.
    """
    for key in (
        "id",
        "name",
        "resource_id",
        "user_id",
        "group_id",
        "app_id",
        "application_id",
        "policy_id",
        "device_id",
        "authenticator_id",
        "auth_server_id",
        "network_zone_id",
        "trusted_origin_id",
        "factor_id",
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
# 2. Extract tags from a row (Okta resources typically don't have tags)
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags if present (most Okta resources don't have tags)."""
    raw = row.get("tags") or row.get("Tags")
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
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
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
        logger.warning("Steampipe query timed out after %ds: %.80s...", timeout_sec, sql)
        return []
    except json.JSONDecodeError as e:
        logger.warning("Steampipe JSON parse error: %s", e)
        return []
    except Exception as e:
        logger.warning("Steampipe query failed: %s", e)
        return []


# ===================================================================
# 4. Query a single Okta table
# ===================================================================
def _query_table(
    table_name: str,
    canonical_type: str,
    install_dir: str,
) -> tuple[list[dict], list[dict]]:
    """Query a single Okta Steampipe table via a minimal id-column SELECT.

    Asset-inventory mode: each row carries only the identifier column, so
    every resource resolves to ``id`` (or the table's fallback id). Rows
    with no resolvable id are skipped to avoid ``unknown`` collisions on the
    (organization, provider, provider_resource_id) unique constraint.

    Returns:
        (entries, structured_warnings)
    """
    sql = _table_select_sql(table_name)
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
                "service": "Okta",
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
        rid = resolve_resource_id(row)
        # Skip rows with no identifier — they'd collide on the
        # (organization, provider, provider_resource_id) unique constraint.
        if not rid or rid == "unknown":
            logger.debug("Skipping row from %s with no resolvable id", table_name)
            continue
        tags = extract_tags(row)

        # The id (via `rid`) is the single identifier for Okta resources — the
        # YAML rules resolve display_name from $.id during ingestion, so no
        # name-based display fields are computed here.
        entry = {
            "resource_type": table_name,
            "resource_id": rid,
            "canonical_type": canonical_type,
            "region": "global",
            "provider": "Okta",
            "tags": tags,
            "details": row,
        }

        entries.append(entry)

    return entries, warnings


# ===================================================================
# 5. Main import function
# ===================================================================
async def import_okta_resources_via_steampipe(
    okta_domain: str,
    okta_token: str,
    db=None,
    progress_callback: Optional[callable] = None,
) -> dict:
    """
    Discover Okta resources via Steampipe using API token auth.

    Flow:
      1. Create a temporary Steampipe config directory with Okta credentials
      2. Read OKTA_STEAMPIPE_TABLE_TO_TYPE to know which tables to query
      3. For each table, run a minimal id-column SELECT (``id`` by default)
         **in parallel** (up to MAX_CONCURRENT_QUERIES at a time, each with a
         timeout)
      4. Map each result to the appropriate canonical type
      5. Return structured data ready for ingestion
    """
    # ---------------------------------------------------------------
    # 1. Create temp config and run queries in parallel
    # ---------------------------------------------------------------
    with tempfile.TemporaryDirectory() as temp_dir:
        # Symlink Steampipe installation folders
        steampipe_home = Path.home() / ".steampipe"
        for folder in ["plugins", "db", "internal"]:
            src = steampipe_home / folder
            dst = Path(temp_dir) / folder
            if src.exists() and not dst.exists():
                dst.symlink_to(src, target_is_directory=True)

        # Write okta.spc with API token credentials
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Normalise domain (remove protocol prefix)
        clean_domain = (
            okta_domain.removeprefix("https://")
            .removeprefix("http://")
            .split("/")[0]
        )

        spc = f'''
connection "okta" {{
  plugin = "okta"
  domain = "{clean_domain}"
  token  = "{okta_token}"
}}
'''
        (config_dir / "okta.spc").write_text(spc)

        # Point the network gate at the Okta tenant so a connectivity probe
        # checks the same network path the Steampipe plugin uses.
        set_network_probe_url(f"https://{clean_domain}")

        # ---------------------------------------------------------------
        # 2. Load table-to-type mapping
        # ---------------------------------------------------------------
        if not OKTA_STEAMPIPE_TABLE_TO_TYPE:
            logger.error("OKTA_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
            return {
                "okta_domain": clean_domain,
                "resources_discovered": 0,
                "resources_detail": [],
            }

        # Build the list of table-query tasks
        tasks = []
        for table_name, canonical_type in OKTA_STEAMPIPE_TABLE_TO_TYPE.items():
            tasks.append((table_name, canonical_type, temp_dir))

        all_resources: list[dict] = []
        all_warnings: list[dict] = []

        logger.info(
            "Starting parallel discovery of %d Okta tables (max %d concurrent, %ds per-query timeout)",
            len(tasks), MAX_CONCURRENT_QUERIES, PER_QUERY_TIMEOUT_SEC,
        )

        # Notify initial progress
        if progress_callback:
            progress_callback({
                "total_tables": len(tasks),
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": f"Starting discovery of {len(tasks)} Okta resource types...",
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
                            "service": "Okta",
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
                            "service": "Okta",
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
                    "service": "Okta",
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
                "Discovery complete: %d total Okta resources from %d tables",
                len(all_resources), len(tables_with_data),
            )

    # ---------------------------------------------------------------
    # 3. Build final result
    # ---------------------------------------------------------------
    discovery_run_id = str(uuid4())
    raw_api_records = []
    for r in all_resources:
        raw_api_records.append({
            "discovery_run_id": discovery_run_id,
            "provider": "Okta",
            "account_id": clean_domain,
            "region": "global",
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
        "okta_domain": clean_domain,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate Okta connection via Steampipe
# ===================================================================
def validate_okta_connection(
    okta_domain: str,
    okta_token: str,
) -> dict:
    """Validate an Okta connection by running a simple Steampipe query."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            steampipe_home = Path.home() / ".steampipe"
            for folder in ["plugins", "db", "internal"]:
                src = steampipe_home / folder
                dst = Path(temp_dir) / folder
                if src.exists() and not dst.exists():
                    dst.symlink_to(src, target_is_directory=True)

            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir(parents=True, exist_ok=True)

            clean_domain = (
                okta_domain.removeprefix("https://")
                .removeprefix("http://")
                .split("/")[0]
            )

            spc = f'''
connection "okta" {{
  plugin = "okta"
  domain = "{clean_domain}"
  token  = "{okta_token}"
}}
'''
            (config_dir / "okta.spc").write_text(spc)

            # Run a simple query to validate connectivity
            cmd = [
                "steampipe", "query",
                "select id, status from okta_user limit 1;",
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
            user_count = len(rows)
            return {
                "success": True,
                "domain": clean_domain,
                "users_found": user_count,
                "message": f"Connected to Okta Steampipe! Found {user_count} Okta users.",
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Connection timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
