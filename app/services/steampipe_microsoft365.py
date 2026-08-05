"""
Dynamic Steampipe-based Microsoft 365 resource discovery.
Uses Microsoft 365 Steampipe table names and maps them to CanonicalTypes.

Authentication uses an Entra ID (Azure AD) app registration with Microsoft
Graph API permissions (tenant_id, client_id, client_secret).

Currently discovers:
  - microsoft365_team         → Group
  - microsoft365_team_member  → Identity

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

import httpx

from app.mappers.canonical_map import M365_STEAMPIPE_TABLE_TO_TYPE
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
# 1. Helper: resolve a stable resource_id from a row (M365-specific)
# ===================================================================
def resolve_resource_id(row: dict) -> str:
    """Pick the best identifier from a Microsoft 365 Steampipe row.

    M365 resources use 'id' as the primary identifier.
    """
    for key in (
        "id",
        "team_id",
        "member_id",
        "name",
        "display_name",
        "user_id",
        "group_id",
        "resource_id",
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
# 2. Extract tags from a row
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags if present."""
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
# 4. Query a single Microsoft 365 table
# ===================================================================
def _query_table(
    table_name: str,
    canonical_type: str,
    install_dir: str,
) -> tuple[list[dict], list[dict]]:
    """Query a single Microsoft 365 Steampipe table and produce resource entries.

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
                "service": "Microsoft 365",
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
        tags = extract_tags(row)

        # Build display name
        name = (
            row.get("display_name")
            or row.get("displayName")
            or row.get("name")
            or row.get("Name")
            or row.get("team_name")
            or rid
        )

        entry = {
            "resource_type": table_name,
            "resource_id": rid,
            "canonical_type": canonical_type,
            "region": "global",
            "provider": "Microsoft 365",
            "name": name,
            "display_name": name,
            "tags": tags,
            "details": row,
        }

        entries.append(entry)

    return entries, warnings


# ===================================================================
# 5. Main import function
# ===================================================================
async def import_microsoft365_resources_via_steampipe(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    db=None,
    progress_callback: Optional[callable] = None,
) -> dict:
    """
    Discover Microsoft 365 resources via Steampipe using Entra ID app credentials.

    Flow:
      1. Create a temporary Steampipe config directory with M365 credentials
      2. Read M365_STEAMPIPE_TABLE_TO_TYPE to know which tables to query
      3. For each table, run ``SELECT * FROM <table>`` **in parallel**
         (up to MAX_CONCURRENT_QUERIES at a time, each with a timeout)
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

        # Write microsoft365.spc with app registration credentials
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        spc = f'''
connection "microsoft365" {{
  plugin = "microsoft365"
  tenant_id = "{tenant_id}"
  client_id = "{client_id}"
  client_secret = "{client_secret}"
}}
'''
        (config_dir / "microsoft365.spc").write_text(spc)

        # Point the network gate at the Microsoft login endpoint so a
        # connectivity probe checks the same network path the M365 plugin
        # uses for token acquisition.
        set_network_probe_url("https://login.microsoftonline.com")

        # ---------------------------------------------------------------
        # 2. Load table-to-type mapping
        # ---------------------------------------------------------------
        if not M365_STEAMPIPE_TABLE_TO_TYPE:
            logger.error("M365_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
            return {
                "tenant_id": tenant_id,
                "resources_discovered": 0,
                "resources_detail": [],
            }

        # Build the list of table-query tasks
        tasks = []
        for table_name, canonical_type in M365_STEAMPIPE_TABLE_TO_TYPE.items():
            tasks.append((table_name, canonical_type, temp_dir))

        all_resources: list[dict] = []
        all_warnings: list[dict] = []

        logger.info(
            "Starting parallel discovery of %d Microsoft 365 tables (max %d concurrent, %ds per-query timeout)",
            len(tasks), MAX_CONCURRENT_QUERIES, PER_QUERY_TIMEOUT_SEC,
        )

        # Notify initial progress
        if progress_callback:
            progress_callback({
                "total_tables": len(tasks),
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": f"Starting discovery of {len(tasks)} Microsoft 365 resource types...",
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
                            "service": "Microsoft 365",
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
                            "service": "Microsoft 365",
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
                    "service": "Microsoft 365",
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
                "Discovery complete: %d total Microsoft 365 resources from %d tables",
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
            "provider": "Microsoft 365",
            "account_id": tenant_id,
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
        "tenant_id": tenant_id,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Get Microsoft Graph API access token
# ===================================================================
def _get_graph_token(tenant_id: str, client_id: str, client_secret: str) -> dict:
    """Obtain an OAuth2 access token for the Microsoft Graph API.

    Uses the client credentials flow (app-only auth). Returns a dict with
    ``{"success": True, "token": "..."}`` or ``{"success": False, "error": "..."}``.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, data=data)

        if resp.status_code == 200:
            token_data = resp.json()
            token = token_data.get("access_token", "")
            if not token:
                return {"success": False, "error": "Azure AD returned 200 but no access_token was provided. The response may be malformed."}
            return {"success": True, "token": token}
        elif resp.status_code == 400:
            body = resp.text[:300]
            if "AADSTS700016" in body:
                return {"success": False, "error": "Application not found in tenant. Check that the client_id and tenant_id are correct and the app registration exists."}
            elif "AADSTS70002" in body or "AADSTS7000215" in body:
                return {"success": False, "error": "Invalid client_secret. Check that the secret is correct and has not expired."}
            return {"success": False, "error": f"Azure AD auth error: {body}"}
        elif resp.status_code == 401:
            return {"success": False, "error": "Unauthorized. Check your tenant_id, client_id, and client_secret."}
        else:
            return {"success": False, "error": f"Azure AD returned HTTP {resp.status_code}: {resp.text[:300]}"}
    except httpx.ConnectError:
        return {"success": False, "error": "Could not connect to login.microsoftonline.com. Check network connectivity."}
    except httpx.TimeoutException:
        return {"success": False, "error": "Connection to login.microsoftonline.com timed out."}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===================================================================
# Helper: Validate Microsoft 365 connection via Microsoft Graph API
# ===================================================================
def validate_microsoft365_connection(
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> dict:
    """Validate a Microsoft 365 connection by:

    1. Getting an OAuth2 token from Azure AD (validates credentials)
    2. Calling Microsoft Graph API to list Teams (validates permissions)

    This validates credentials directly against the Microsoft Graph API
    rather than going through Steampipe, so it works even when the
    Steampipe database is unavailable.
    """
    # ---------------------------------------------------------------
    # 1. Get access token
    # ---------------------------------------------------------------
    token_result = _get_graph_token(tenant_id, client_id, client_secret)
    if not token_result["success"]:
        return {"success": False, "error": token_result["error"]}

    access_token = token_result["token"]

    # ---------------------------------------------------------------
    # 2. Call Microsoft Graph API to validate Teams access
    # ---------------------------------------------------------------
    # Teams are represented as groups with resourceProvisioningOptions containing "Team"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                "https://graph.microsoft.com/v1.0/groups",
                headers=headers,
                params={
                    "$filter": "resourceProvisioningOptions/Any(x:x eq 'Team')",
                    "$top": 1,
                    "$select": "id,displayName,visibility",
                },
            )

        if resp.status_code == 200:
            data = resp.json()
            teams = data.get("value", [])
            team_count = len(teams)

            # Check if we got partial results or a nextLink (more teams exist)
            has_more = "@odata.nextLink" in data
            count_suffix = f" (showing first {team_count})" if has_more and team_count > 0 else ""

            return {
                "success": True,
                "tenant_id": tenant_id,
                "teams_found": team_count,
                "message": f"Connected to Microsoft 365! Found {team_count} team(s) via Graph API{count_suffix}.",
            }
        elif resp.status_code == 401:
            body = resp.text[:300]
            return {
                "success": False,
                "error": f"Graph API authentication failed (401). The app may lack required permissions. {body}",
            }
        elif resp.status_code == 403:
            body = resp.text[:300]
            return {
                "success": False,
                "error": f"Graph API access denied (403). Ensure the app has 'Group.Read.All' permission (and 'Team.ReadBasic.All' for Teams). {body}",
            }
        else:
            return {
                "success": False,
                "error": f"Graph API returned HTTP {resp.status_code}: {resp.text[:300]}",
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Could not connect to graph.microsoft.com. Check network connectivity."}
    except httpx.TimeoutException:
        return {"success": False, "error": "Connection to graph.microsoft.com timed out."}
    except Exception as e:
        return {"success": False, "error": str(e)}
