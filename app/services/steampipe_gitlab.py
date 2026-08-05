"""
Dynamic Steampipe-based GitLab resource discovery.
Uses GitLab Steampipe table names and maps them to CanonicalTypes.

Authentication uses a GitLab Personal Access Token (PAT) plus the GitLab
API base URL (e.g. https://gitlab.com/api/v4 or https://gitlab.company.com/api/v4).

The GitLab Steampipe plugin (theapsgroup/gitlab) requires many tables to be
queried with specific qualifiers (WHERE clauses). This module uses a
multi-phase approach:

  Phase 1 — Context gathering: Query context tables (gitlab_my_project,
             gitlab_group) to discover project ids and group ids.

  Phase 2 — Qualifier queries: For each group-scoped table, query with
            ``where group_id = <id>``; for each project-scoped table, query
            with ``where project_id = <id>``. Tables that need no qualifier
            (instance-wide, admin-only tables) are queried with SELECT *.

  Phase 3 — Identity resolution: Collect user ids from the rows gathered in
            Phase 2 (members, deployments, etc.) and query ``gitlab_user``
            with ``where id = <user_id>``.

Note on GitLab.com: the plugin refuses unqualified SELECT * on
``gitlab_project`` / ``gitlab_user`` when pointed at the hosted SaaS. We
always qualify these tables with ``=`` predicates derived from context,
which works for both GitLab.com and self-hosted instances.

This mode is scoped to **asset inventory**: each table is queried for its
identifier column(s) only (``TABLE_ID_COLUMN``) so the inventory knows *what
exists* (id + provider + canonical type) without hydrating every column.
Composite identifiers (e.g. variables are ``group_id`` + ``key`` +
``environment_scope``) are joined with ``:``.

Performance design:
  - Inventory queries select only the identifier column(s) (+ a few extras
    needed for dedup / Phase 3) — no hydrate columns → faster, fewer
    token-scope errors
  - Context queries run first (sequential, fast)
  - Qualifier queries run in parallel via ThreadPoolExecutor (max 5 concurrent)
  - Per-query timeout (120s) + overall timeout (600s) prevent hanging
"""
import json
import logging
import subprocess
import tempfile
import time
import concurrent.futures
from pathlib import Path
from typing import Optional
from uuid import uuid4

import httpx

from app.mappers.canonical_map import GITLAB_STEAMPIPE_TABLE_TO_TYPE
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
CONTEXT_QUERY_TIMEOUT_SEC = 60   # Timeout for context-gathering queries
MAX_PIPELINE_DETAIL_QUERIES = 25 # Cap on per-pipeline detail queries
MAX_USER_QUERIES = 200           # Cap on per-user identity queries

# ---------------------------------------------------------------------------
# Qualifier map — defines what WHERE clause each table needs and where the
# qualifier value comes from.
#   group-scoped tables  -> group_id (ids come from gitlab_group)
#   project-scoped tables -> project_id (ids come from gitlab_my_project)
# ---------------------------------------------------------------------------
GROUP_QUALIFIER_TABLES = {
    "gitlab_group_member",
    "gitlab_group_variable",
    "gitlab_group_push_rule",
    "gitlab_group_hook",
    "gitlab_group_access_request",
    "gitlab_group_project",
}

# gitlab_group_subgroup uses parent_id (which is the group id)
PARENT_QUALIFIER_TABLES = {
    "gitlab_group_subgroup",
}

PROJECT_QUALIFIER_TABLES = {
    "gitlab_project_member",
    "gitlab_project_variable",
    "gitlab_project_container_registry",
    "gitlab_project_pipeline",
    "gitlab_project_job",
    "gitlab_project_deployment",
    "gitlab_project_protected_branch",
    "gitlab_project_access_request",
}

# Tables that must always carry an `=` qualifier on GitLab.com (the plugin
# refuses unqualified SELECT * against the hosted SaaS). We always qualify
# them — safe for self-hosted instances too.
ID_QUALIFIER_TABLES = {
    "gitlab_project",  # qualifier: id (project id)
    "gitlab_user",     # qualifier: id (user id)
}

# Requires both project_id and id (pipeline id) — handled in Phase 3.
PIPELINE_DETAIL_TABLE = "gitlab_project_pipeline_detail"

# Context tables — handled in Phase 1, excluded from the batch loop
CONTEXT_TABLES = {"gitlab_my_project", "gitlab_group"}


# ---------------------------------------------------------------------------
# Inventory-mode identifier columns per table
# ---------------------------------------------------------------------------
# Asset inventory only needs a stable identifier per resource. Querying just
# the identifier column(s) instead of ``select *`` skips every hydrate column
# (which can call extra GitLab APIs the token isn't authorised for) and makes
# imports much faster.
#
# Composite identifiers (multiple columns) are joined with ``:`` when building
# the resource id — GitLab variables reuse the same ``key`` across scopes, so
# ``gitlab_group_variable`` / ``gitlab_project_variable`` are unique per
# (scope id, key, environment_scope) and ``gitlab_instance_variable`` per
# (key, environment_scope).
TABLE_ID_COLUMN: dict[str, list[str]] = {
    # --- Application ---
    "gitlab_application": ["application_id"],
    # --- Configuration (CI/CD variables) ---
    "gitlab_group_variable": ["group_id", "key", "environment_scope"],
    "gitlab_project_variable": ["project_id", "key", "environment_scope"],
    "gitlab_instance_variable": ["key", "environment_scope"],
    # --- Container registry / deployment ---
    "gitlab_project_container_registry": ["id"],
    "gitlab_project_deployment": ["id"],
    # --- Groups ---
    "gitlab_group": ["id"],
    "gitlab_group_subgroup": ["id"],
    "gitlab_group_project": ["id"],
    "gitlab_group_member": ["id"],
    "gitlab_project_member": ["id"],
    "gitlab_group_access_request": ["id"],
    "gitlab_project_access_request": ["id"],
    # --- Identity ---
    "gitlab_user": ["id"],
    # --- Pipelines ---
    "gitlab_project_pipeline": ["id"],
    "gitlab_project_pipeline_detail": ["id"],
    "gitlab_project_job": ["id"],
    # --- Repositories ---
    "gitlab_project": ["id"],
    "gitlab_my_project": ["id"],
    "gitlab_project_protected_branch": ["id"],
    "gitlab_group_push_rule": ["id"],
    # --- Webhooks ---
    "gitlab_group_hook": ["id"],
}

# Extra columns to select for tables where the identifier alone is not enough
# to drive the pipeline correctly. These are NOT part of the resource id —
# they ride along so dedup + display_name + Phase 3 keep working in inventory
# mode.
TABLE_EXTRA_COLUMNS: dict[str, list[str]] = {
    # Phase 3 resolves pipeline-detail pairs from gitlab_project_pipeline rows
    # (needs project_id + id) and users from member rows; keeping user_id on
    # pipeline rows also lets Phase 3 resolve pipeline authors.
    "gitlab_project_pipeline": ["project_id", "user_id"],
    # Identity assets are deduped by username/email — keep username on user
    # rows so the same person is not imported multiple times.
    "gitlab_user": ["username"],
}

# Tables that must be queried with ``select *`` — their identifier is not a
# real column. gitlab_setting is a singleton instance-level settings object
# with no ``id`` column; it is resolved to a constant ``instance`` id.
FULL_SELECT_TABLES: set[str] = {"gitlab_setting"}


def _table_id_columns(table_name: str) -> list[str]:
    """Return the identifier column(s) to select for a table (default ``id``)."""
    return TABLE_ID_COLUMN.get(table_name, ["id"])


def _table_select_columns(table_name: str) -> list[str]:
    """Return all columns to SELECT for a table (identifier + extras)."""
    return _table_id_columns(table_name) + TABLE_EXTRA_COLUMNS.get(table_name, [])


def _table_select_sql(table_name: str, where: Optional[str] = None) -> str:
    """Build the inventory SELECT for a table — identifier column(s) plus any
    dedup/display extras, optionally with a WHERE clause.

    Tables in ``FULL_SELECT_TABLES`` keep ``select *``.
    """
    if table_name in FULL_SELECT_TABLES:
        body = f"select * from {table_name}"
    else:
        cols = ", ".join(_table_select_columns(table_name))
        body = f"select {cols} from {table_name}"
    if where:
        return f"{body} where {where};"
    return body + ";"


# ===================================================================
# 1. Helper: resolve a stable resource_id from a row (GitLab-specific)
# ===================================================================
def resolve_resource_id(row: dict, table_name: str = "") -> str:
    """Pick the best identifier from a GitLab Steampipe row.

    In inventory mode the row carries only the identifier column(s) declared
    in ``TABLE_ID_COLUMN`` — those are returned directly (composite columns
    joined with ``:``). If the declared columns are missing (e.g. a row that
    didn't come from a minimal select), fall back to the legacy priority list
    (readable fields first, then numeric id).
    """
    # Singleton instance-level settings — no ``id`` column in the plugin table.
    if table_name == "gitlab_setting":
        return "instance"

    if table_name:
        cols = _table_id_columns(table_name)
        parts = []
        for c in cols:
            v = row.get(c)
            if v is None or (isinstance(v, str) and not v.strip()):
                break
            parts.append(str(v))
        if len(parts) == len(cols):
            return ":".join(parts)

    # Legacy fallback — GitLab resources use numeric 'id' as the primary
    # identifier, but for readability we prefer unique string fields
    # (full_path / web_url) when available.
    for key in (
        "web_url",
        "full_path",
        "path",
        "name",
        "username",
        "slug",
        "email",
        "key",
        "url",
    ):
        val = row.get(key)
        if val and isinstance(val, str):
            return val
    # Numeric id fallback
    for key in ("id", "user_id", "project_id", "group_id", "parent_id"):
        val = row.get(key)
        if val is not None:
            return str(val)
    # Last resort - first non-null value
    for v in row.values():
        if v and isinstance(v, str):
            return v
    return "unknown"


# ===================================================================
# 2. Extract tags from a row (GitLab resources typically don't have tags)
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags if present (most GitLab resources don't have tags)."""
    raw = row.get("tags") or row.get("Topics") or row.get("topics")
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            if "Key" in raw[0] or "key" in raw[0]:
                return raw
            return [
                {"Key": t.get("key", t.get("Key", "")), "Value": t.get("value", t.get("Value", ""))}
                for t in raw
            ]
        if raw and isinstance(raw[0], str):
            return [{"Key": t, "Value": t} for t in raw]
    if isinstance(raw, dict):
        return raw
    return None


# ===================================================================
# 3. Run a single Steampipe query
# ===================================================================
def _is_transient_service_error(stderr: str) -> bool:
    """True if the error looks like a transient local-service startup race."""
    if not stderr:
        return False
    return (
        "unknown state" in stderr
        or "service is running" in stderr
        or "invalid memory address" in stderr
        or "nil pointer dereference" in stderr
    )


def run_query(sql: str, install_dir: str, timeout_sec: int = PER_QUERY_TIMEOUT_SEC) -> list[dict]:
    """Execute a Steampipe SQL query and return parsed rows.

    On a cold start, parallel subprocesses can race to bring up the local
    Steampipe service, producing transient "service is running in an unknown
    state" errors. We retry those briefly before giving up.
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
                if _is_transient_service_error(res.stderr or ""):
                    logger.warning(
                        "Steampipe query transient error (attempt %d): %.200s",
                        attempt + 1, (res.stderr or "")[:200],
                    )
                    time.sleep(2 + attempt * 2)
                    continue
                if handle_query_failure(res.stderr or ""):
                    logger.warning(
                        "Network recovered — retrying query (attempt %d)", attempt + 1,
                    )
                    continue
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
            return []
        except json.JSONDecodeError as e:
            logger.warning("Steampipe JSON parse error: %s", e)
            return []
        except NetworkUnavailableError:
            raise
        except Exception as e:
            logger.warning("Steampipe query failed: %s", e)
            return []
        finally:
            if proc:
                unregister(proc)
    return []


# ===================================================================
# 4. Convert a raw Steampipe row into a resource entry
# ===================================================================
def _row_to_entry(row: dict, table_name: str, canonical_type: str) -> dict:
    """Convert a single Steampipe row into a standardised resource entry dict."""
    rid = resolve_resource_id(row, table_name)
    tags = extract_tags(row)

    # Build display name
    name = (
        row.get("name")
        or row.get("full_path")
        or row.get("path")
        or row.get("username")
        or row.get("web_url")
        or row.get("url")
        or row.get("key")
        or rid
    )

    entry = {
        "resource_type": table_name,
        "resource_id": rid,
        "canonical_type": canonical_type,
        "region": "global",
        "provider": "GitLab",
        "name": name,
        "display_name": name,
        "tags": tags,
        "details": row,
    }

    # Extract common relationship references
    relationships = {}
    for ref_key in (
        "project_id", "ProjectID",
        "group_id", "GroupID",
        "namespace_id", "NamespaceID",
        "user_id", "UserID",
        "author_id", "AuthorID",
        "creator_id", "CreatorID",
    ):
        if ref_key in row and row[ref_key] is not None:
            rel_name = ref_key.replace("_", "").lower()
            relationships[rel_name] = row[ref_key]
    if relationships:
        entry["relationships"] = relationships

    return entry


# ===================================================================
# 5. Phase 1: Gather context (projects, groups)
# ===================================================================
def _gather_context(install_dir: str, cancel_check: Optional[callable] = None) -> dict:
    """Gather context information needed for qualifier queries.

    ``cancel_check`` is invoked between the sequential context queries so a
    bulk-import cancellation interrupts context gathering between queries.

    Returns a dict with:
      - project_ids: set of project ids (from gitlab_my_project)
      - group_ids: set of group ids (from gitlab_group)
      - projects: list of raw project rows
      - groups: list of raw group rows
      - warnings: any warnings encountered
    """
    context: dict = {
        "project_ids": set(),
        "group_ids": set(),
        "projects": [],
        "groups": [],
        "warnings": [],
    }

    # --- Query gitlab_my_project (projects the user is a member of) ---
    my_projects = run_query(
        "SELECT * FROM gitlab_my_project;",
        install_dir, CONTEXT_QUERY_TIMEOUT_SEC,
    )
    if my_projects:
        logger.info("Context: gitlab_my_project returned %d projects", len(my_projects))
        context["projects"] = my_projects
        for r in my_projects:
            pid = r.get("id")
            if pid is not None:
                context["project_ids"].add(pid)
    else:
        logger.warning("Context: gitlab_my_project returned 0 projects")
        context["warnings"].append({
            "service": "GitLab", "action": "Context",
            "resource": "", "table": "gitlab_my_project",
            "message": (
                "No projects found. Check the personal access token scope: "
                "fine-grained tokens need 'Project: Read' (and 'Group: Read') "
                "user permissions; classic tokens need the 'read_api' scope."
            ),
        })

    # --- Query gitlab_group (groups where the user is a member) ---
    if cancel_check:
        cancel_check()
    groups = run_query(
        "SELECT * FROM gitlab_group;",
        install_dir, CONTEXT_QUERY_TIMEOUT_SEC,
    )
    if groups:
        logger.info("Context: gitlab_group returned %d groups", len(groups))
        context["groups"] = groups
        for r in groups:
            gid = r.get("id")
            if gid is not None:
                context["group_ids"].add(gid)
    else:
        logger.debug("Context: gitlab_group returned 0 groups")

    logger.info(
        "Context gathered: %d projects, %d groups",
        len(context["project_ids"]), len(context["group_ids"]),
    )
    return context


# ===================================================================
# 6. Query a single table with an optional WHERE clause
# ===================================================================
def _query_where(
    table_name: str,
    canonical_type: str,
    install_dir: str,
    where: Optional[str] = None,
) -> list[dict]:
    """Query a table (optionally with a WHERE clause) and convert rows.

    Asset-inventory mode: selects only the identifier column(s) declared in
    ``TABLE_ID_COLUMN`` (plus ``TABLE_EXTRA_COLUMNS``), so each row carries
    just the id — skipping every hydrate column that can trigger
    permission-gated API calls. Rows with no resolvable id fall back to the
    legacy ``resolve_resource_id`` priority list.
    """
    sql = _table_select_sql(table_name, where)
    rows = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
    if rows:
        logger.debug("  %s %s -> %d rows", table_name, f"({where})" if where else "", len(rows))
        return [_row_to_entry(r, table_name, canonical_type) for r in rows]
    return []


# ===================================================================
# 7. Process a single table task (for parallel execution)
# ===================================================================
def _process_table(
    table_name: str,
    canonical_type: str,
    install_dir: str,
    context: dict,
    cancel_check: Optional[callable] = None,
) -> tuple[str, list[dict], list[dict]]:
    """Process a single table, returning (table_name, entries, warnings).

    This is the worker function for Phase 2 parallel execution.
    ``cancel_check`` is invoked before each qualifier query so that a
    bulk-import cancellation interrupts a long table task between queries
    (instead of running every remaining qualifier first).
    """
    warnings: list[dict] = []
    entries: list[dict] = []

    if table_name in GROUP_QUALIFIER_TABLES:
        for gid in sorted(context.get("group_ids", set())):
            if cancel_check:
                cancel_check()
            entries.extend(_query_where(table_name, canonical_type, install_dir,
                                        where=f"group_id = {gid}"))
    elif table_name in PARENT_QUALIFIER_TABLES:
        for gid in sorted(context.get("group_ids", set())):
            if cancel_check:
                cancel_check()
            entries.extend(_query_where(table_name, canonical_type, install_dir,
                                        where=f"parent_id = {gid}"))
    elif table_name in PROJECT_QUALIFIER_TABLES:
        for pid in sorted(context.get("project_ids", set())):
            if cancel_check:
                cancel_check()
            entries.extend(_query_where(table_name, canonical_type, install_dir,
                                        where=f"project_id = {pid}"))
    elif table_name in ID_QUALIFIER_TABLES:
        # gitlab_project — qualify by project id (required on GitLab.com)
        if table_name == "gitlab_project":
            for pid in sorted(context.get("project_ids", set())):
                if cancel_check:
                    cancel_check()
                entries.extend(_query_where(table_name, canonical_type, install_dir,
                                            where=f"id = {pid}"))
        # gitlab_user is handled in Phase 3 (needs user ids from members)
        else:
            logger.debug("  %s deferred to Phase 3 (user identity)", table_name)
    else:
        # No qualifier needed — SELECT *
        entries = _query_where(table_name, canonical_type, install_dir)

    return table_name, entries, warnings


# ===================================================================
# 8. Main import function
# ===================================================================
def _write_gitlab_spc(config_dir: Path, baseurl: str, token: str) -> Path:
    """Write a gitlab.spc connection config with the given credentials."""
    spc = f'''
connection "gitlab" {{
  plugin = "theapsgroup/gitlab"
  baseurl = "{baseurl}"
  token  = "{token}"
}}
'''
    path = config_dir / "gitlab.spc"
    path.write_text(spc)
    return path


def _query_table_batch(
    tables: list[tuple[str, str]],
    temp_dir: str,
    context: dict,
    completed: int,
    total_tables: int,
    all_resources: list[dict],
    all_warnings: list[dict],
    progress_callback: Optional[callable],
    cancel_check: Optional[callable] = None,
) -> int:
    """Query a batch of tables in parallel (Phase 2)."""
    if not tables:
        return completed

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_QUERIES) as pool:
        future_map = {
            pool.submit(_process_table, t, ct, temp_dir, context, cancel_check): t
            for t, ct in tables
        }

        try:
            for future in concurrent.futures.as_completed(future_map, timeout=OVERALL_TIMEOUT_SEC):
                table = future_map[future]
                completed += 1
                try:
                    _table, entries, table_warnings = future.result()
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
                        "service": "GitLab", "action": "Timeout",
                        "resource": "", "table": table,
                        "message": f"Query for {table} was cancelled due to overall timeout",
                    })
                except (ImportCancelledError, NetworkUnavailableError):
                    raise
                except Exception as e:
                    logger.warning("  %s -> error: %s", table, e)
                    all_warnings.append({
                        "service": "GitLab", "action": "Error",
                        "resource": "", "table": table,
                        "message": f"{table}: {str(e)[:200]}",
                    })

                if progress_callback:
                    progress_callback({
                        "total_tables": total_tables,
                        "completed_tables": completed,
                        "current_table": table,
                        "resources_found": len(all_resources),
                        "message": f"Queried {table} ({completed}/{total_tables})",
                        "warnings": all_warnings[-20:],
                    })
        except concurrent.futures.TimeoutError:
            logger.warning("Overall import timeout reached after %ds — processing partial results", OVERALL_TIMEOUT_SEC)
            all_warnings.append({
                "service": "GitLab", "action": "Import",
                "resource": "", "table": "",
                "message": f"Import timed out after {OVERALL_TIMEOUT_SEC}s — only partial results available",
            })
        except (ImportCancelledError, NetworkUnavailableError):
            # Cancellation requested or network outage — cancel queued table
            # tasks so the executor's shutdown(wait=True) below does NOT drain
            # the whole queue before the outcome is honoured. Re-kill any
            # newly spawned Steampipe subprocesses (workers may have dequeued
            # the next task and registered a fresh process after the cancel
            # endpoint's initial kill) so shutdown returns immediately.
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

    return completed


def _run_phase3_queries(
    temp_dir: str,
    all_resources: list[dict],
    all_warnings: list[dict],
    context: dict,
    progress_callback: Optional[callable] = None,
    total_tables: int = 0,
    completed_base: int = 0,
) -> None:
    """Phase 3: resolve users and pipeline details using Phase 2 results.

    ``progress_callback`` is invoked before each query so that a bulk-import
    cancellation (which raises inside the callback) can interrupt this phase
    between queries instead of letting it run every remaining query first.
    """
    # --- Collect user ids from member/deployment rows ---
    user_ids: set = set()
    pipeline_pairs: list[tuple] = []

    for r in all_resources:
        details = r.get("details", {}) or {}
        # Member tables expose the user's id via the row's `id` field
        if r.get("resource_type") in ("gitlab_group_member", "gitlab_project_member"):
            mid = details.get("id")
            if mid is not None:
                user_ids.add(mid)
        # Common user-id columns across GitLab tables
        for key in ("user_id", "author_id", "creator_id", "owner_id", "merged_by_id", "updated_by_id"):
            uid = details.get(key)
            if uid is not None:
                user_ids.add(uid)
        if r.get("resource_type") == "gitlab_project_pipeline":
            pid = details.get("project_id")
            pipe_id = details.get("id")
            if pid is not None and pipe_id is not None:
                pipeline_pairs.append((pid, pipe_id))

    completed = completed_base

    # --- gitlab_user (needs id qualifier on GitLab.com) ---
    if "gitlab_user" in GITLAB_STEAMPIPE_TABLE_TO_TYPE and user_ids:
        canonical_type = GITLAB_STEAMPIPE_TABLE_TO_TYPE["gitlab_user"]
        count = 0
        for uid in sorted(user_ids):
            if count >= MAX_USER_QUERIES:
                all_warnings.append({
                    "service": "GitLab", "action": "Skipped",
                    "resource": "", "table": "gitlab_user",
                    "message": f"Stopped after {MAX_USER_QUERIES} user identity queries (cap reached).",
                })
                break
            if progress_callback:
                completed += 1
                progress_callback({
                    "total_tables": total_tables,
                    "completed_tables": completed,
                    "current_table": "gitlab_user",
                    "resources_found": len(all_resources),
                    "message": f"Phase 3: resolving user {count + 1} (id {uid})...",
                    "warnings": all_warnings[-20:],
                })
            entries = _query_where("gitlab_user", canonical_type, temp_dir, where=f"id = {uid}")
            if entries:
                all_resources.extend(entries)
            count += 1
        if count:
            logger.info("Phase 3: queried gitlab_user for %d users", count)

    # --- gitlab_project_pipeline_detail (needs project_id + id) ---
    if PIPELINE_DETAIL_TABLE in GITLAB_STEAMPIPE_TABLE_TO_TYPE and pipeline_pairs:
        canonical_type = GITLAB_STEAMPIPE_TABLE_TO_TYPE[PIPELINE_DETAIL_TABLE]
        count = 0
        for pid, pipe_id in pipeline_pairs:
            if count >= MAX_PIPELINE_DETAIL_QUERIES:
                all_warnings.append({
                    "service": "GitLab", "action": "Skipped",
                    "resource": "", "table": PIPELINE_DETAIL_TABLE,
                    "message": f"Stopped after {MAX_PIPELINE_DETAIL_QUERIES} pipeline detail queries (cap reached).",
                })
                break
            if progress_callback:
                completed += 1
                progress_callback({
                    "total_tables": total_tables,
                    "completed_tables": completed,
                    "current_table": PIPELINE_DETAIL_TABLE,
                    "resources_found": len(all_resources),
                    "message": f"Phase 3: resolving pipeline {count + 1}...",
                    "warnings": all_warnings[-20:],
                })
            entries = _query_where(PIPELINE_DETAIL_TABLE, canonical_type, temp_dir,
                                   where=f"project_id = {pid} and id = {pipe_id}")
            if entries:
                all_resources.extend(entries)
            count += 1
        if count:
            logger.info("Phase 3: queried %s for %d pipelines", PIPELINE_DETAIL_TABLE, count)


async def import_gitlab_resources_via_steampipe(
    baseurl: str,
    token: str,
    db=None,
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
) -> dict:
    """
    Discover GitLab resources via Steampipe using a Personal Access Token.

    Flow:
      1. Create a temporary Steampipe config directory with credentials
      2. Phase 1: Gather context (projects, groups)
      3. Phase 2: Query group/project/no-qualifier tables in parallel
      4. Phase 3: Resolve users + pipeline details from Phase 2 results
      5. Map each result to the appropriate canonical type
      6. Return structured data ready for ingestion
    """
    baseurl = (baseurl or "").strip().rstrip("/")
    token = (token or "").strip()

    if not baseurl or not token:
        return {"resources_discovered": 0, "resources_detail": [], "warnings": [
            {"service": "GitLab", "action": "Config", "resource": "", "table": "",
             "message": "GitLab base URL and personal access token are required."},
        ]}

    # Point the network gate at the GitLab instance so a connectivity probe
    # checks the same network path the Steampipe plugin uses.
    set_network_probe_url(baseurl)

    # ---------------------------------------------------------------
    # Validate table-to-type mapping
    # ---------------------------------------------------------------
    if not GITLAB_STEAMPIPE_TABLE_TO_TYPE:
        logger.error("GITLAB_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
        return {"resources_discovered": 0, "resources_detail": []}

    # Build the batch table list.
    #   - gitlab_project stays in the batch: it needs an `id` qualifier on
    #     GitLab.com, which _process_table applies via ID_QUALIFIER_TABLES.
    #   - gitlab_user and pipeline_detail are deferred to Phase 3.
    #   - Context tables (gitlab_my_project, gitlab_group) run in Phase 1 and
    #     their rows are re-added to the resource list afterwards.
    batch_tables = [
        (t, ct) for t, ct in GITLAB_STEAMPIPE_TABLE_TO_TYPE.items()
        if t not in CONTEXT_TABLES
        and t != "gitlab_user"
        and t != PIPELINE_DETAIL_TABLE
    ]

    total_tables = len(batch_tables) + len(CONTEXT_TABLES) + 1  # +1 for gitlab_user (phase 3)

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

        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Write gitlab.spc with token + base URL
        _write_gitlab_spc(config_dir, baseurl, token)

        # ---------------------------------------------------------------
        # Phase 1: Gather context
        # ---------------------------------------------------------------
        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": "Phase 1: Gathering context (projects, groups)...",
                "warnings": [],
            })

        logger.info("Phase 1: Gathering context...")
        context = _gather_context(temp_dir, cancel_check)
        all_warnings = list(context.get("warnings", []))
        all_resources: list[dict] = []

        # Context rows become assets too:
        #   - gitlab_my_project -> Repository (gitlab_project also captures
        #     these; the dedupe step removes the overlap)
        #   - gitlab_group -> Group (context-only table, no other query
        #     captures groups)
        for r in context.get("projects", []):
            all_resources.append(_row_to_entry(
                r, "gitlab_my_project",
                GITLAB_STEAMPIPE_TABLE_TO_TYPE.get("gitlab_my_project", "Repository"),
            ))
        for r in context.get("groups", []):
            all_resources.append(_row_to_entry(
                r, "gitlab_group",
                GITLAB_STEAMPIPE_TABLE_TO_TYPE.get("gitlab_group", "Group"),
            ))

        context_table_count = len(CONTEXT_TABLES)

        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": context_table_count,
                "current_table": "gitlab_my_project",
                "resources_found": 0,
                "message": f"Context gathered: {len(context.get('project_ids', set()))} projects, "
                          f"{len(context.get('group_ids', set()))} groups",
                "warnings": all_warnings[-20:],
            })

        # ---------------------------------------------------------------
        # Phase 2: Query tables in parallel
        # ---------------------------------------------------------------
        completed = context_table_count
        if batch_tables:
            logger.info(
                "Phase 2: Querying %d tables (max %d concurrent)",
                len(batch_tables), MAX_CONCURRENT_QUERIES,
            )
            completed = _query_table_batch(
                batch_tables, temp_dir, context,
                completed, total_tables,
                all_resources, all_warnings, progress_callback,
                cancel_check,
            )

        # ---------------------------------------------------------------
        # Phase 3: Users + pipeline details
        # ---------------------------------------------------------------
        completed += 1  # account for gitlab_user query in progress accounting
        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": completed,
                "current_table": "gitlab_user",
                "resources_found": len(all_resources),
                "message": "Phase 3: Resolving users and pipeline details...",
                "warnings": all_warnings[-20:],
            })
        _run_phase3_queries(
            temp_dir, all_resources, all_warnings, context,
            progress_callback=progress_callback,
            total_tables=total_tables,
            completed_base=completed,
        )

        # ---------------------------------------------------------------
        # Deduplicate by resource_id (or username for Identity types)
        # ---------------------------------------------------------------
        seen_ids: set[str] = set()
        deduped: list[dict] = []
        for r in all_resources:
            if r.get("canonical_type") == "Identity":
                details = r.get("details", {}) or {}
                dedup_key = details.get("username") or details.get("email") or r.get("display_name", "") or r.get("resource_id", "")
            else:
                dedup_key = r.get("resource_id", "")
            if not dedup_key or dedup_key == "unknown":
                deduped.append(r)
            elif dedup_key not in seen_ids:
                seen_ids.add(dedup_key)
                deduped.append(r)
        duplicates_removed = len(all_resources) - len(deduped)
        if duplicates_removed:
            logger.warning("Removed %d duplicate resource entries", duplicates_removed)
        all_resources = deduped

        tables_with_data = {r["resource_type"] for r in all_resources}
        logger.info(
            "Import complete: %d total GitLab resources from %d tables (%d warnings)",
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
            "provider": "GitLab",
            "account_id": baseurl,
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
        "account_id": baseurl,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate GitLab connection via GitLab API
# ===================================================================
def validate_gitlab_connection(
    baseurl: str,
    token: str,
) -> dict:
    """Validate a GitLab PAT by calling the GitLab API directly.

    Uses the GitLab REST API (GET /api/v4/user) rather than Steampipe so that
    validation works even when the Steampipe database is unavailable.
    """
    baseurl = (baseurl or "").strip().rstrip("/")
    token = (token or "").strip()

    if not baseurl.endswith("/api/v4"):
        baseurl = f"{baseurl}/api/v4"

    headers = {
        "PRIVATE-TOKEN": token,
        "Accept": "application/json",
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{baseurl}/user", headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            username = data.get("username", "unknown")
            return {
                "success": True,
                "users_found": 1,
                "message": f"Connected to GitLab as '{username}'.",
            }
        elif resp.status_code == 401:
            return {
                "success": False,
                "error": "GitLab authentication failed (401). Token is invalid or expired.",
            }
        elif resp.status_code == 403:
            return {
                "success": False,
                "error": "GitLab access denied (403). Token may lack the required permissions (read_api).",
            }
        else:
            return {
                "success": False,
                "error": f"GitLab API returned HTTP {resp.status_code}: {resp.text[:200]}",
            }
    except httpx.ConnectError:
        return {"success": False, "error": f"Could not connect to {baseurl}. Check the GitLab base URL."}
    except httpx.TimeoutException:
        return {"success": False, "error": f"Connection to {baseurl} timed out."}
    except Exception as e:
        return {"success": False, "error": str(e)}
