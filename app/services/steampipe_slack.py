"""
Dynamic Steampipe-based Slack resource discovery.
Uses Slack Steampipe table names and maps them to CanonicalTypes.

With this service, Slack resources land as Canonical Assets:
  - slack_user                 →  Identity
  - slack_conversation         →  Group
  - slack_group                →  Group
  - slack_conversation_member  →  Group
  - slack_access_log           →  Logging
  - slack_connection           →  Organization

Authentication uses a Slack Bot User OAuth Token (``xoxb-...``).

The Slack plugin has provider-specific quirks that this module handles:

  * ``slack_conversation_member`` REQUIRES a ``conversation_id = '...'``
    qualifier — it cannot be queried with a bare SELECT. Phase 1 gathers the
    conversation ids from ``slack_conversation``; Phase 2 queries the member
    table once per conversation (capped to keep imports bounded).
  * Several tables depend on the token's scopes (``channels:read``,
    ``groups:read``, ``usergroups:read``, ``team:read``) or on a user token
    (``slack_access_log`` needs ``xoxp-`` + ``team.access_logs:read``).
    Tables that fail with ``missing_scope`` / ``not_allowed_token_type`` are
    skipped gracefully and surfaced as warnings in the UI.

This mode is scoped to **asset inventory**: each table is queried for its
identifier column(s) only so the inventory knows *what exists* (id + provider
+ canonical type) without hydrating every column.

Performance design:
  - Inventory queries select only the identifier column(s) (no hydrate
    columns → faster, fewer permission-gated API calls)
  - Table queries run in parallel via ThreadPoolExecutor (max 5 concurrent)
  - Per-query timeout (120s) + overall timeout (600s) prevent hanging
"""
import json
import tempfile
import subprocess
import logging
import concurrent.futures
from uuid import uuid4
from pathlib import Path
from typing import Optional

import httpx

from app.mappers.canonical_map import SLACK_STEAMPIPE_TABLE_TO_TYPE
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
MEMBER_QUERY_CAP = 300           # Max conversations to expand for conversation_member

# Table whose List call requires a `conversation_id = '...'` qualifier.
_MEMBER_TABLE = "slack_conversation_member"

# ---------------------------------------------------------------------------
# Inventory-mode identifier columns per table
# ---------------------------------------------------------------------------
# Asset inventory only needs a stable identifier per resource. Querying just
# the identifier column(s) instead of ``select *`` skips every hydrate column
# and makes imports much faster.
#
# Composite identifiers (two columns) are joined with ``:`` when building the
# resource id, e.g. conversation membership is unique per
# (conversation_id, member_id). The access log is namespaced per user because
# there is one row per login event.
TABLE_ID_COLUMN: dict[str, list[str]] = {
    # --- Identity ---
    "slack_user": ["id"],
    # --- Groups / channels ---
    "slack_conversation": ["id"],
    "slack_group": ["id"],
    # Queried with a conversation_id qualifier (Phase 2) — the row returns
    # both halves of the composite identity. NOTE: this table's List call
    # REQUIRES a conversation_id qualifier, so it must never be added to the
    # direct Phase 1 batch (a bare SELECT fails in the plugin).
    "slack_conversation_member": ["conversation_id", "member_id"],
    # --- Logging ---
    "slack_access_log": ["user_id", "date_first"],
    # --- Organization (workspace connection) ---
    "slack_connection": ["team_id"],
}

# Extra columns selected alongside the identifier for display/dedup only.
# These are NOT part of the resource id — they just ride along so assets get
# a recognisable name and the workspace (account_id) is preserved.
TABLE_EXTRA_COLUMNS: dict[str, list[str]] = {
    "slack_user": ["email"],
    "slack_conversation": ["name"],
    "slack_group": ["name"],
    "slack_access_log": ["user_name"],
    "slack_connection": ["team", "workspace_domain"],
}


def _table_select_columns(table_name: str) -> list[str]:
    """Return all columns to SELECT for a table (identifier + extras)."""
    return TABLE_ID_COLUMN.get(table_name, ["id"]) + TABLE_EXTRA_COLUMNS.get(table_name, [])


def _table_select_sql(table_name: str) -> str:
    """Build the inventory SELECT for a table — its identifier column(s) plus
    any display extras."""
    cols = ", ".join(_table_select_columns(table_name))
    return f"select {cols} from {table_name};"


# ===================================================================
# 1. Helper: resolve a stable resource_id from a row (Slack-specific)
# ===================================================================
def resolve_resource_id(row: dict, table_name: str = "") -> str:
    """Pick the best identifier from a Slack Steampipe row.

    In inventory mode the row carries the identifier column(s) declared in
    ``TABLE_ID_COLUMN`` — those are returned directly (composite columns
    joined with ``:``). If a declared column is missing (e.g. a row that
    didn't come from a minimal select), fall back to the legacy priority list.
    """
    if table_name:
        cols = TABLE_ID_COLUMN.get(table_name, ["id"])
        parts = []
        for c in cols:
            v = row.get(c)
            if v is None or (isinstance(v, str) and not v.strip()):
                break
            parts.append(str(v))
        if len(parts) == len(cols):
            return ":".join(parts)

    # Legacy fallback — Slack resources use 'id' as the primary identifier.
    for key in ("id", "team_id", "user_id", "conversation_id", "member_id",
                "email", "name", "handle", "workspace_domain"):
        val = row.get(key)
        if val and isinstance(val, str):
            return val
    # Last resort - first non-null value
    for v in row.values():
        if v and isinstance(v, str):
            return v
    return "unknown"


# ===================================================================
# 2. Extract tags from a row (Slack resources typically don't have tags)
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags if present (most Slack resources don't have tags)."""
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
def run_query(sql: str, install_dir: str, timeout_sec: int = PER_QUERY_TIMEOUT_SEC) -> tuple[list[dict], str]:
    """Execute a Steampipe SQL query and return (rows, error).

    ``error`` is the plugin's error message (e.g. ``missing_scope``) when the
    query fails, or an empty string on success. Callers surface it as a
    warning so the UI explains why a table produced no resources.
    """
    cmd = ["steampipe", "query", sql, "--install-dir", install_dir, "--output", "json"]
    for attempt in range(MAX_QUERY_ATTEMPTS):
        proc = None
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            register(proc)
            stdout, stderr = proc.communicate(timeout=timeout_sec)
            res = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
            if res.returncode != 0:
                if handle_query_failure(res.stderr or ""):
                    logger.warning(
                        "Network recovered — retrying query (attempt %d)", attempt + 1,
                    )
                    continue
                err = (res.stderr or "").strip()
                logger.warning("Steampipe query returned %d: %.500s", res.returncode, err)
                return [], err
            if res.stderr and res.stderr.strip():
                logger.warning("Steampipe query stderr: %s", res.stderr[:500])
            data = json.loads(res.stdout)
            rows = data.get("rows", [])
            logger.debug("  Query returned %d rows", len(rows))
            return rows, ""
        except subprocess.TimeoutExpired:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            if handle_query_failure("", timed_out=True):
                logger.warning(
                    "Network recovered — retrying timed-out query (attempt %d)", attempt + 1,
                )
                continue
            logger.warning("Steampipe query timed out after %ds: %.80s...", timeout_sec, sql)
            return [], "timed out"
        except json.JSONDecodeError as e:
            logger.warning("Steampipe JSON parse error: %s", e)
            return [], str(e)
        except NetworkUnavailableError:
            raise
        except Exception as e:
            logger.warning("Steampipe query failed: %s", e)
            return [], str(e)
        finally:
            if proc:
                unregister(proc)
    return [], "query failed after retries"


# ===================================================================
# 4. Convert a raw Steampipe row into a resource entry
# ===================================================================
def _row_to_entry(row: dict, table_name: str, canonical_type: str, workspace: str = "") -> dict:
    """Convert a single Steampipe row into a standardised resource entry dict."""
    rid = resolve_resource_id(row, table_name)
    # Skip rows with no identifier — they'd collide on the
    # (organization, provider, provider_resource_id) unique constraint.
    if not rid or rid == "unknown":
        return None
    tags = extract_tags(row)

    # Attach the workspace (from the configured profile) so the YAML rules can
    # map account_id without an extra round-trip per row. The plugin also
    # exposes workspace_domain natively — prefer the row's own value.
    if workspace and not row.get("workspace_domain"):
        row = {**row, "workspace_domain": workspace}

    # Build display name
    name = (
        row.get("name")
        or row.get("display_name")
        or row.get("real_name")
        or row.get("email")
        or row.get("handle")
        or row.get("team")
        or row.get("user_name")
        or rid
    )

    entry = {
        "resource_type": table_name,
        "resource_id": rid,
        "canonical_type": canonical_type,
        "region": "global",
        "provider": "Slack",
        "name": name,
        "display_name": name,
        "tags": tags,
        "details": row,
    }

    # Extract common relationship references
    relationships = {}
    for ref_key in (
        "team_id", "TeamId",
        "user_id", "UserId",
        "conversation_id", "ConversationId",
        "member_id", "MemberId",
    ):
        if ref_key in row:
            rel_name = ref_key.replace("_", "").lower()
            relationships[rel_name] = row[ref_key]
    if relationships:
        entry["relationships"] = relationships

    return entry


# ===================================================================
# 5. Query a single Slack table
# ===================================================================
def _query_table(table_name: str, canonical_type: str, install_dir: str, workspace: str = "") -> tuple[list[dict], list[dict]]:
    """Query a single Slack table via a minimal identifier-column SELECT.

    Returns (entries, warnings).
    """
    warnings: list[dict] = []
    all_entries: list[dict] = []
    sql = _table_select_sql(table_name)
    rows, err = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
    if rows:
        for row in rows:
            entry = _row_to_entry(row, table_name, canonical_type, workspace)
            if entry:
                all_entries.append(entry)
        logger.debug("  %s -> %d rows", table_name, len(rows))
    else:
        logger.debug("  %s -> 0 rows", table_name)
        if err:
            warnings.append({
                "service": "Slack",
                "action": "Query",
                "resource": "",
                "table": table_name,
                "message": f"Query for {table_name} failed: {err[:200]}",
            })
    return all_entries, warnings


# ===================================================================
# 6. Phase 2: query slack_conversation_member per conversation
# ===================================================================
def _query_conversation_members(
    install_dir: str,
    workspace: str,
    conversation_ids: list[str],
    progress_callback: Optional[callable] = None,
    total_tables: int = 0,
    completed: int = 0,
    resources_so_far: int = 0,
    cancel_check: Optional[callable] = None,
) -> tuple[list[dict], list[dict], int]:
    """Query slack_conversation_member once per conversation id.

    The Slack plugin's List call for this table REQUIRES a
    ``conversation_id = '...'`` qualifier, so there is no bare-SELECT path.

    Returns (entries, warnings, completed_count).
    """
    entries: list[dict] = []
    warnings: list[dict] = []

    if not conversation_ids:
        warnings.append({
            "service": "Slack",
            "action": "Query",
            "resource": "",
            "table": _MEMBER_TABLE,
            "message": (
                "slack_conversation_member needs conversation ids, but no "
                "conversations were discovered (check the channels:read scope)."
            ),
        })
        return entries, warnings, completed

    capped = conversation_ids[:MEMBER_QUERY_CAP]
    if len(conversation_ids) > MEMBER_QUERY_CAP:
        warnings.append({
            "service": "Slack",
            "action": "Import",
            "resource": "",
            "table": _MEMBER_TABLE,
            "message": (
                f"Only {MEMBER_QUERY_CAP} of {len(conversation_ids)} conversations "
                "were expanded for conversation_member (cap)."
            ),
        })

    for cid in capped:
        if cancel_check:
            cancel_check()
        if not cid:
            continue
        sql = (
            f"select conversation_id, member_id from {_MEMBER_TABLE} "
            f"where conversation_id = '{cid}';"
        )
        rows, err = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
        completed += 1
        if rows:
            for row in rows:
                entry = _row_to_entry(row, _MEMBER_TABLE, "Group", workspace)
                if entry:
                    entries.append(entry)
            logger.debug("  %s (WHERE conversation_id='%s') -> %d rows", _MEMBER_TABLE, cid, len(rows))
        elif err:
            warnings.append({
                "service": "Slack",
                "action": "Query",
                "resource": "",
                "table": _MEMBER_TABLE,
                "message": f"Query for {_MEMBER_TABLE} (conversation {cid}) failed: {err[:200]}",
            })

        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": completed,
                "current_table": _MEMBER_TABLE,
                "resources_found": resources_so_far + len(entries),
                "message": f"Queried {_MEMBER_TABLE} for conversation {cid} ({completed}/{total_tables})",
                "warnings": [],
            })

    return entries, warnings, completed


# ===================================================================
# 7. Main import function
# ===================================================================
def _write_slack_spc(config_dir: Path, token: str) -> Path:
    """Write a slack.spc connection config with the given bot token."""
    spc = f'''
connection "slack" {{
  plugin = "slack"
  token  = "{token}"
}}
'''
    path = config_dir / "slack.spc"
    path.write_text(spc)
    return path


async def import_slack_resources_via_steampipe(
    slack_token: str,
    workspace: str = "",
    db=None,
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
) -> dict:
    """
    Discover Slack resources via Steampipe using a Bot User OAuth token.

    Flow:
      1. Create a temporary Steampipe config directory with Slack credentials
      2. Read SLACK_STEAMPIPE_TABLE_TO_TYPE to know which tables to query
      3. Phase 1: query the direct tables in parallel (minimal identifier
         SELECTs)
      4. Phase 2: expand slack_conversation_member once per discovered
         conversation (the plugin requires a conversation_id qualifier)
      5. Map each result to the appropriate canonical type
      6. Return structured data ready for ingestion
    """
    account_id = workspace.strip() or "slack"

    with tempfile.TemporaryDirectory() as temp_dir:
        # ---------------------------------------------------------------
        # Symlink Steampipe installation folders
        # ---------------------------------------------------------------
        steampipe_home = Path.home() / ".steampipe"
        for folder in ["plugins", "db", "internal"]:
            src = steampipe_home / folder
            dst = Path(temp_dir) / folder
            if src.exists() and not dst.exists():
                dst.symlink_to(src, target_is_directory=True)

        # Write slack.spc with the bot token credentials
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        _write_slack_spc(config_dir, slack_token)

        # Point the network gate at the Slack API so a connectivity probe
        # checks the same network path the Steampipe plugin uses.
        set_network_probe_url("https://slack.com")

        # ---------------------------------------------------------------
        # Load table-to-type mapping
        # ---------------------------------------------------------------
        if not SLACK_STEAMPIPE_TABLE_TO_TYPE:
            logger.error("SLACK_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
            return {
                "account_id": account_id,
                "resources_discovered": 0,
                "resources_detail": [],
            }

        # Build the list of direct table-query tasks (conversation_member is
        # handled in Phase 2 because it needs a conversation_id qualifier).
        direct_tables = [t for t in SLACK_STEAMPIPE_TABLE_TO_TYPE if t != _MEMBER_TABLE]
        tasks = [(t, SLACK_STEAMPIPE_TABLE_TO_TYPE[t], temp_dir, workspace) for t in direct_tables]

        all_resources: list[dict] = []
        all_warnings: list[dict] = []
        member_total = 1  # placeholder until conversation ids are known

        logger.info(
            "Starting parallel discovery of %d Slack tables (max %d concurrent, %ds per-query timeout)",
            len(tasks), MAX_CONCURRENT_QUERIES, PER_QUERY_TIMEOUT_SEC,
        )

        # Notify initial progress
        if progress_callback:
            progress_callback({
                "total_tables": len(tasks) + member_total,
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": f"Starting discovery of {len(tasks)} Slack resource types...",
                "warnings": [],
            })

        completed = 0

        # ---------------------------------------------------------------
        # Phase 1: run direct table queries in the thread pool
        # ---------------------------------------------------------------
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_QUERIES) as pool:
            future_map = {
                pool.submit(_query_table, t, ct, td, ws): t
                for t, ct, td, ws in tasks
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
                            "service": "Slack",
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
                            "service": "Slack",
                            "action": "Error",
                            "resource": "",
                            "table": table,
                            "message": f"{table}: {str(e)[:200]}",
                        })

                    if progress_callback:
                        progress_callback({
                            "total_tables": len(tasks) + member_total,
                            "completed_tables": completed,
                            "current_table": table,
                            "resources_found": len(all_resources),
                            "message": f"Queried {table} ({completed}/{len(tasks)})",
                            "warnings": all_warnings[-20:],
                        })
            except concurrent.futures.TimeoutError:
                logger.warning("Overall import timeout reached after %ds — processing partial results", OVERALL_TIMEOUT_SEC)
                all_warnings.append({
                    "service": "Slack",
                    "action": "Import",
                    "resource": "",
                    "table": "",
                    "message": f"Import timed out after {OVERALL_TIMEOUT_SEC}s — only partial results available",
                })
            except (ImportCancelledError, NetworkUnavailableError):
                # Cancellation requested or network outage — cancel queued table
                # tasks so the executor's shutdown(wait=True) below does NOT drain
                # the whole queue before the outcome is honoured.
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

        # ---------------------------------------------------------------
        # Phase 2: expand conversation members per conversation id
        # ---------------------------------------------------------------
        conversation_ids: list[str] = []
        for r in all_resources:
            if r.get("resource_type") != "slack_conversation":
                continue
            details = r.get("details", {}) or {}
            cid = details.get("id")
            if cid and cid not in conversation_ids:
                conversation_ids.append(str(cid))

        member_total = min(len(conversation_ids), MEMBER_QUERY_CAP)
        member_entries, member_warnings, completed = _query_conversation_members(
            temp_dir,
            workspace,
            conversation_ids,
            progress_callback=progress_callback,
            total_tables=len(tasks) + member_total,
            completed=completed,
            resources_so_far=len(all_resources),
            cancel_check=cancel_check,
        )
        all_resources.extend(member_entries)
        all_warnings.extend(member_warnings)

        # ---------------------------------------------------------------
        # Deduplicate by resource_id (mirrors the GitHub service)
        # ---------------------------------------------------------------
        # Composite ids (access log per login, conversation membership) could
        # otherwise collide on the (organization, provider, provider_resource_id)
        # unique constraint in canonical_assets.
        seen_ids: set[str] = set()
        deduped: list[dict] = []
        for r in all_resources:
            key = r.get("resource_id", "")
            if not key or key == "unknown":
                deduped.append(r)
            elif key not in seen_ids:
                seen_ids.add(key)
                deduped.append(r)
        duplicates_removed = len(all_resources) - len(deduped)
        if duplicates_removed:
            logger.warning(
                "Removed %d duplicate Slack resource entries (dedup by resource_id)",
                duplicates_removed,
            )
        all_resources = deduped

        tables_with_data = {r["resource_type"] for r in all_resources}
        logger.info(
            "Import complete: %d total Slack resources from %d tables (%d warnings)",
            len(all_resources), len(tables_with_data), len(all_warnings),
        )

    # ---------------------------------------------------------------
    # Build final result
    # ---------------------------------------------------------------
    discovery_run_id = str(uuid4())
    raw_api_records = []
    for r in all_resources:
        raw_api_records.append({
            "discovery_run_id": discovery_run_id,
            "provider": "Slack",
            "account_id": account_id,
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
        "account_id": account_id,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate Slack connection via the Slack API
# ===================================================================
def validate_slack_connection(slack_token: str) -> dict:
    """Validate a Slack Bot token by calling the Slack auth.test endpoint.

    Uses the Slack Web API directly (rather than Steampipe) so validation
    works even when the Steampipe database is unavailable.
    """
    if not slack_token.strip():
        return {"success": False, "error": "Slack Bot Token is required."}

    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post("https://slack.com/api/auth.test", headers=headers)

        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"Slack API returned HTTP {resp.status_code}: {resp.text[:200]}",
            }

        data = resp.json()
        if data.get("ok"):
            team = data.get("team", "unknown")
            team_id = data.get("team_id", "")
            user = data.get("user", "")
            return {
                "success": True,
                "team": team,
                "team_id": team_id,
                "user": user,
                "message": f"Connected to Slack workspace '{team}' ({team_id}) as {user}.",
            }
        else:
            error = data.get("error", "unknown_error")
            return {
                "success": False,
                "error": f"Slack authentication failed: {error}",
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Could not connect to slack.com. Check network connectivity."}
    except httpx.TimeoutException:
        return {"success": False, "error": "Connection to slack.com timed out."}
    except Exception as e:
        return {"success": False, "error": str(e)}
