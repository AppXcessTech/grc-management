"""
Dynamic Steampipe-based Azure resource discovery.
Uses Azure Steampipe table names and maps them to CanonicalTypes.
Azure authentication uses Service Principal (subscription_id, tenant_id, client_id, client_secret).

Performance design:
  - Queries use `SELECT * FROM <table>` (one subprocess per table)
  - Table queries run in parallel via ThreadPoolExecutor (max 5 concurrent)
  - Per-query timeout (120s) + overall timeout (600s) prevent hanging
"""
import json
import re
import tempfile
import subprocess
import logging
import concurrent.futures
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from app.mappers.canonical_map import AZURE_STEAMPIPE_TABLE_TO_TYPE
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
# 1. Helper: resolve a stable resource_id from a row (Azure-specific)
# ===================================================================
def resolve_resource_id(row: dict) -> str:
    """Pick the best identifier from an Azure Steampipe row.

    Priority: id (full Azure resource ID) -> name -> common fields -> first value.
    """
    for key in (
        "id",
        "name",
        "resource_id",
        "vm_id",
        "aks_id",
        "storage_account_id",
        "sql_server_id",
        "database_id",
        "cluster_id",
        "server_id",
        "account_id",
        "load_balancer_id",
        "gateway_id",
        "registry_id",
        "function_app_id",
        "vnet_id",
        "subnet_id",
        "nsg_id",
        "route_table_id",
        "role_id",
        "role_assignment_id",
        "subscription_id",
        "workspace_id",
        "queue_id",
        "container_group_id",
        "scale_set_id",
        "managed_instance_id",
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
    """Normalise tags to {'Key': ..., 'Value': ...} list or dict."""
    raw = row.get("tags") or row.get("Tags") or row.get("TagSet")
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            if "Key" in raw[0] or "key" in raw[0]:
                return raw
            return [{"Key": t.get("key", t.get("Key", "")), "Value": t.get("value", t.get("Value", ""))} for t in raw]
    if isinstance(raw, dict):
        return raw
    return None


# Azure-specific pattern to extract operation/resource from error lines
_AZURE_ACTION_RE = re.compile(r"(Microsoft\.[A-Za-z0-9.]+/[A-Za-z0-9]+)")


def _parse_permission_error(line: str, table_name: str = "") -> dict | None:
    """Parse an Azure permission error line into structured components."""
    lower = line.lower()
    has_perm = any(kw in lower for kw in [
        "accessdenied", "access denied", "not authorized", "unauthorized",
        "insufficient privileges", "permission denied", "authorizationerror",
    ])
    if not has_perm:
        return None

    service: str | None = None
    action: str | None = None

    # Extract Azure action (e.g., "Microsoft.Compute/virtualMachines/write")
    action_match = _AZURE_ACTION_RE.search(line)
    if action_match:
        action = action_match.group(1)
        # Derive service from the action namespace
        parts = action.split("/")
        if len(parts) >= 2:
            svc_ns = parts[0].replace("Microsoft.", "")
            service = svc_ns

    # Derive service from table name if action parsing failed
    if not service and table_name:
        parts = table_name.split("_")
        if len(parts) >= 2 and parts[0] == "azure":
            svc_name = parts[1].capitalize()
            service = {
                "compute": "Compute",
                "storage": "Storage",
                "sql": "SQL",
                "mysql": "MySQL",
                "postgresql": "PostgreSQL",
                "mariadb": "MariaDB",
                "mssql": "MSSQL",
                "cosmosdb": "CosmosDB",
                "kubernetes": "AKS",
                "container": "Container",
                "network": "Network",
                "lb": "Load Balancer",
                "app_service": "App Service",
                "monitor": "Monitor",
                "security": "Security Center",
                "role": "IAM",
                "subscription": "Subscription",
            }.get(svc_name.lower(), svc_name)

    msg = line[:300].strip()
    return {
        "service": service or "Azure",
        "action": action or "Permission Denied",
        "resource": "",
        "table": table_name,
        "message": msg,
    }


def _extract_permission_warnings(stderr: str, table_name: str = "") -> list[dict]:
    """Extract structured permission warnings from Azure stderr output."""
    if not stderr:
        return []
    seen = set()
    warnings = []
    for line in stderr.split("\n"):
        line = line.strip()
        if not line:
            continue
        parsed = _parse_permission_error(line, table_name)
        if parsed:
            dedup_key = f"{parsed['service']}:{parsed['action']}"
            if dedup_key not in seen:
                seen.add(dedup_key)
                warnings.append(parsed)
    return warnings


# ===================================================================
# 3. Run a single Steampipe query
# ===================================================================
def run_query(sql: str, install_dir: str, timeout_sec: int = PER_QUERY_TIMEOUT_SEC) -> list[dict]:
    """Execute a Steampipe SQL query and return parsed rows."""
    cmd = ["steampipe", "query", sql, "--install-dir", install_dir, "--output", "json"]
    for attempt in range(MAX_QUERY_ATTEMPTS):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
            if res.returncode != 0:
                if handle_query_failure(res.stderr or ""):
                    logger.warning(
                        "Network recovered — retrying query (attempt %d)", attempt + 1,
                    )
                    continue
                logger.warning("Steampipe query returned %d: %s", res.returncode, res.stderr[:500])
                return []
            if res.stderr and res.stderr.strip():
                logger.warning("Steampipe query stderr (table may have partial results): %s", res.stderr[:500])
            data = json.loads(res.stdout)
            rows = data.get("rows", [])
            logger.debug("  Query returned %d rows", len(rows))
            return rows
        except subprocess.TimeoutExpired:
            if handle_query_failure("", timed_out=True):
                logger.warning(
                    "Network recovered — retrying timed-out query (attempt %d)", attempt + 1,
                )
                continue
            logger.warning("Steampipe query timed out after %ds: %.80s...", timeout_sec, sql)
            return []
        except json.JSONDecodeError as e:
            logger.warning("Steampipe JSON parse error: %s", e)
            return []
        except NetworkUnavailableError:
            raise
        except Exception as e:
            logger.warning("Steampipe query failed: %s", e)
            return []
    return []


# ===================================================================
# 4. Query a single Azure table
# ===================================================================
def _query_table(
    table_name: str,
    canonical_type: str,
    install_dir: str,
    default_region: str,
    default_subscription_id: str,
) -> tuple[list[dict], list[dict]]:
    """Query a single Azure Steampipe table and produce resource entries.

    Returns:
        (entries, structured_permission_warnings)
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

            # Check stderr for permission warnings on this table
            if res.stderr and res.stderr.strip():
                perm_warnings = _extract_permission_warnings(res.stderr, table_name)
                if perm_warnings:
                    warnings.extend(perm_warnings)
                    logger.warning("Permission warnings for table %s: %s", table_name, [w["message"] for w in perm_warnings])

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
                "service": "Timeout",
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
        row_region = row.get("region") or default_region
        tags = extract_tags(row)

        # Build display name
        name = (
            row.get("name")
            or row.get("Name")
            or rid
        )

        entry = {
            "resource_type": table_name,
            "resource_id": rid,
            "canonical_type": canonical_type,
            "region": row_region,
            "subscription_id": row.get("subscription_id") or default_subscription_id,
            "account_id": row.get("subscription_id") or default_subscription_id,
            "provider": "Azure",
            "name": name,
            "display_name": name,
            "tags": tags,
            "details": row,
        }

        # Extract common Azure relationship references
        relationships = {}
        for ref_key in (
            "vnet_id", "VNetId", "virtual_network_id",
            "subnet_id", "SubnetId",
            "nsg_id", "NsgId", "network_security_group_id",
            "resource_group_name", "ResourceGroupName",
            "cluster_name", "ClusterName",
            "managed_by", "ManagedBy",
            "load_balancer_id", "LoadBalancerId",
        ):
            if ref_key in row:
                rel_name = ref_key.replace("_id", "").replace("Id", "").lower()
                relationships[rel_name] = row[ref_key]
        if relationships:
            entry["relationships"] = relationships

        entries.append(entry)

    return entries, warnings


# ===================================================================
# 5. Main import function
# ===================================================================
async def import_azure_resources_via_steampipe(
    subscription_id: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    account_name: Optional[str] = None,
    db=None,
    progress_callback: Optional[callable] = None,
) -> dict:
    """
    Discover Azure resources via Steampipe using Service Principal auth.

    Flow:
      1. Create a temporary Steampipe config directory with Azure credentials
      2. Read AZURE_STEAMPIPE_TABLE_TO_TYPE to know which tables to query
      3. For each table, run ``SELECT * FROM <table>`` **in parallel**
         (up to MAX_CONCURRENT_QUERIES at a time, each with a timeout)
      4. Map each result to the appropriate canonical type
      5. Return structured data ready for ingestion
    """
    # Detect default region from Azure metadata if possible
    default_region = "eastus"

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

        # Write azure.spc with Service Principal credentials
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        spc = f"""
connection "azure" {{
  plugin = "azure"
  subscriptions = ["{subscription_id}"]
  tenant_id = "{tenant_id}"
  client_id = "{client_id}"
  client_secret = "{client_secret}"
}}
"""
        (config_dir / "azure.spc").write_text(spc)

        # Point the network gate at the Microsoft login endpoint so a
        # connectivity probe checks the same network path the Azure plugin
        # uses for token acquisition.
        set_network_probe_url("https://login.microsoftonline.com")

        # ---------------------------------------------------------------
        # 2. Load table-to-type mapping
        # ---------------------------------------------------------------
        if not AZURE_STEAMPIPE_TABLE_TO_TYPE:
            logger.error("AZURE_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
            return {
                "subscription_id": subscription_id,
                "resources_discovered": 0,
                "resources_detail": [],
            }

        # Build the list of table-query tasks
        tasks = []
        for table_name, canonical_type in AZURE_STEAMPIPE_TABLE_TO_TYPE.items():
            tasks.append((table_name, canonical_type, temp_dir, default_region, subscription_id))

        all_resources: list[dict] = []
        all_warnings: list[dict] = []

        logger.info(
            "Starting parallel discovery of %d Azure tables (max %d concurrent, %ds per-query timeout)",
            len(tasks), MAX_CONCURRENT_QUERIES, PER_QUERY_TIMEOUT_SEC,
        )

        # Notify initial progress
        if progress_callback:
            progress_callback({
                "total_tables": len(tasks),
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": f"Starting discovery of {len(tasks)} Azure resource types...",
                "warnings": [],
            })

        completed = 0

        # Run table queries in the thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_QUERIES) as pool:
            future_map = {
                pool.submit(_query_table, t, ct, td, r, sid): t
                for t, ct, td, r, sid in tasks
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
                            "service": "Timeout",
                            "action": "Query",
                            "resource": "",
                            "table": table,
                            "message": f"Query for {table} was cancelled due to overall timeout",
                        })
                    except (ImportCancelledError, NetworkUnavailableError):
                        raise
                    except Exception as e:
                        logger.warning("  %s -> error: %s", table, e)
                        all_warnings.append({
                            "service": "Error",
                            "action": "Unknown",
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
                    "service": "Timeout",
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
                "Discovery complete: %d total resources from %d tables",
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
            "provider": "Azure",
            "account_id": subscription_id,
            "region": r.get("region"),
            "service": r["resource_type"],
            "resource_type": r["resource_type"],
            "provider_resource_id": r["resource_id"],
            "api_call": "steampipe_query",
            "api_response": r["details"],
        })

    if db and raw_api_records:
        from app.models.raw_api_response import RawApiResponse
        db.add_all([RawApiResponse(**rec) for rec in raw_api_records])
        # NOT committing here — caller is responsible for the full transaction
        # lifecycle so that a network failure mid-import rolls back everything.

    asset_results = [{**r, "action": "discovered"} for r in all_resources]

    return {
        "subscription_id": subscription_id,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate Azure connection
# ===================================================================
def validate_azure_connection(
    subscription_id: str,
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> dict:
    """
    Validate an Azure Service Principal connection by running a simple query.
    """
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
            spc = f"""
connection "azure" {{
  plugin = "azure"
  subscriptions = ["{subscription_id}"]
  tenant_id = "{tenant_id}"
  client_id = "{client_id}"
  client_secret = "{client_secret}"
}}
"""
            (config_dir / "azure.spc").write_text(spc)

            # Run a simple query to validate connectivity
            cmd = [
                "steampipe", "query",
                "select subscription_id, tenant_id from azure_subscription limit 1;",
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
            if rows:
                return {
                    "success": True,
                    "subscription_id": rows[0].get("subscription_id", subscription_id),
                    "tenant_id": rows[0].get("tenant_id", tenant_id),
                }
            return {
                "success": True,
                "subscription_id": subscription_id,
                "tenant_id": tenant_id,
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Connection timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
