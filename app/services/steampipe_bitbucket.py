"""
Dynamic Steampipe-based Bitbucket resource discovery.
Uses the turbot/bitbucket Steampipe plugin (``bitbucket_*`` tables).

Authentication uses the Atlassian account email plus an API token created at
https://bitbucket.org/account/settings/api-tokens/ (app passwords were
removed on July 28, 2026).

The plugin tables are queried in phases:

  Phase 1 — Context gathering: Discover the workspace slug (required — the
             workspace must be configured explicitly because Bitbucket
             deprecated the ``bitbucket_my_*`` discovery tables, which now
             return 410 Gone). We query the workspace-scoped tables that still
             work:
               - bitbucket_workspace      -> where slug = <workspace_slug>
               - bitbucket_project        -> where workspace_slug = <slug>
             and enumerate repositories via the REST API
             (GET /2.0/repositories/{workspace}) to collect their full names.

  Phase 2 — Qualifier queries: For each table that requires a qualifier, query
            with the appropriate WHERE clause derived from Phase 1 results:
              - bitbucket_workspace          -> where slug = <workspace_slug>
              - bitbucket_project            -> where workspace_slug = <slug>
              - bitbucket_repository         -> where full_name = <full_name>
              - bitbucket_branch_restriction -> where repository_full_name = <full_name>
              - bitbucket_workspace_member   -> where workspace_slug = <slug>

This mode is scoped to **asset inventory**: each table is queried for its
identifier column only (``uuid`` by default, ``id`` for
``bitbucket_branch_restriction``) so the inventory knows *what exists*
(id + provider + canonical type) without hydrating every column. Rows with
no resolvable id are skipped.

Performance design:
  - Inventory queries select only the identifier column (no hydrate columns
    → faster, fewer permission-gated API calls)
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

from app.mappers.canonical_map import BITBUCKET_STEAMPIPE_TABLE_TO_TYPE
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

# ---------------------------------------------------------------------------
# Qualifier map — defines what WHERE clause each table needs and where the
# qualifier value comes from.
# ---------------------------------------------------------------------------
# Tables qualified by the workspace slug
WORKSPACE_SLUG_QUALIFIER_TABLES = {
    "bitbucket_workspace",        # where slug = <slug>
    "bitbucket_project",          # where workspace_slug = <slug>
    "bitbucket_workspace_member", # where workspace_slug = <slug>
}

# Tables qualified by the repository full name (e.g. "workspace/repo")
REPOSITORY_QUALIFIER_TABLES = {
    "bitbucket_repository",          # where full_name = <full_name>
    "bitbucket_branch_restriction",  # where repository_full_name = <full_name>
}

# Context tables — handled in Phase 1, excluded from the batch loop.
# NOTE: the bitbucket_my_* tables are deprecated by Bitbucket (they hit the
# /2.0/user/permissions/* endpoints which now return 410 Gone), so they are
# kept here purely to keep them out of the Phase 2 batch loop. Phase 1 no
# longer queries them — it uses the workspace-scoped tables + the REST API.
CONTEXT_TABLES = {"bitbucket_my_workspace", "bitbucket_my_project", "bitbucket_my_repository"}

# ---------------------------------------------------------------------------
# Inventory-mode identifier column per table
# ---------------------------------------------------------------------------
# Asset inventory only needs a stable identifier per resource — the Bitbucket
# ``uuid``. Querying just the id column instead of ``select *`` skips every
# hydrate column (which can call extra Bitbucket APIs the token isn't
# authorised for) and makes imports much faster. It also sidesteps the buggy
# ``default_reviewers`` hydrate in steampipe-plugin-bitbucket v1.3.0 that
# panicked ``select *`` on ``bitbucket_repository`` — no safe-column list
# needed.
#
# Every Bitbucket table exposes ``uuid`` as the canonical id except
# ``bitbucket_branch_restriction``, whose YAML rule resolves ``$.id``.
TABLE_ID_COLUMN: dict[str, str] = {
    "bitbucket_branch_restriction": "id",
}


def _table_id_column(table_name: str) -> str:
    """Return the identifier column to select for a table (default ``uuid``)."""
    return TABLE_ID_COLUMN.get(table_name, "uuid")


def _table_select_sql(table_name: str) -> str:
    """Build the inventory SELECT for a table — just its identifier column."""
    id_col = _table_id_column(table_name)
    return f"select {id_col} from {table_name};"


# ===================================================================
# 1. Helper: resolve a stable resource_id from a row (Bitbucket-specific)
# ===================================================================
def resolve_resource_id(row: dict, table_name: str = "") -> str:
    """Pick the best identifier from a Bitbucket Steampipe row.

    In inventory mode the row carries only the identifier column declared in
    ``TABLE_ID_COLUMN`` (``uuid`` by default) — that is returned directly. If
    it is missing (e.g. a row that didn't come from a minimal select), fall
    back to the legacy priority list (readable fields first, then numeric id).
    """
    if table_name:
        col = _table_id_column(table_name)
        v = row.get(col)
        if v is not None and str(v).strip():
            return str(v)

    # Legacy fallback — Bitbucket resources use 'uuid' as the primary
    # identifier; prefer readable fields (full_name / name / slug / key).
    for key in (
        "uuid",
        "full_name",
        "name",
        "slug",
        "key",
        "account_id",
        "display_name",
        "self_link",
        "links",
    ):
        val = row.get(key)
        if val and isinstance(val, str):
            return val
        if key == "links" and isinstance(val, dict):
            html = val.get("html", {})
            href = html.get("href") if isinstance(html, dict) else None
            if href:
                return str(href)
    # Numeric id fallback
    for key in ("id", "user_id", "workspace_id", "project_id", "repository_id"):
        val = row.get(key)
        if val is not None:
            return str(val)
    # Last resort - first non-null string value
    for v in row.values():
        if v and isinstance(v, str):
            return v
    return "unknown"


# ===================================================================
# 2. Extract tags from a row (Bitbucket resources typically don't have tags)
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags if present (most Bitbucket resources don't have tags)."""
    raw = row.get("tags") or row.get("labels") or row.get("Topics")
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            return raw
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
def _row_to_entry(row: dict, table_name: str, canonical_type: str) -> dict | None:
    """Convert a single Steampipe row into a standardised resource entry dict.

    Returns ``None`` when the row has no resolvable identifier — such rows
    would collide on the (organization, provider, provider_resource_id)
    unique constraint, so they are skipped by callers.
    """
    rid = resolve_resource_id(row, table_name)
    if not rid or rid == "unknown":
        return None
    tags = extract_tags(row)

    # Build display name
    name = (
        row.get("name")
        or row.get("full_name")
        or row.get("slug")
        or row.get("key")
        or row.get("display_name")
        or row.get("account_id")
        or row.get("uuid")
        or rid
    )

    entry = {
        "resource_type": table_name,
        "resource_id": rid,
        "canonical_type": canonical_type,
        "region": "global",
        "provider": "Bitbucket",
        "name": name,
        "display_name": name,
        "tags": tags,
        "details": row,
    }

    # Extract common relationship references
    relationships = {}
    for ref_key in ("workspace_slug", "project_key", "repository_full_name", "full_name"):
        if ref_key in row and row[ref_key] is not None:
            relationships[ref_key] = row[ref_key]
    if relationships:
        entry["relationships"] = relationships

    return entry


# ===================================================================
# 5. Phase 1: Gather context (workspaces, projects, repositories)
# ===================================================================
def _list_workspace_repositories_via_api(
    base_url: str,
    username: str,
    app_password: str,
    workspace_slug: str,
) -> list[dict]:
    """List repositories in a workspace via the Bitbucket REST API.

    The ``bitbucket_my_repository`` Steampipe table used to enumerate the
    repositories the user can access, but Bitbucket deprecated its backing
    endpoint (``/2.0/user/permissions/*``) and the table now returns 410 Gone.
    The workspace-scoped endpoint ``GET /2.0/repositories/{workspace}`` still
    works, so we enumerate repositories with it and use the resulting full
    names as qualifiers for the ``bitbucket_repository`` Steampipe table.

    Returns a list of raw repository dicts (each has a ``full_name`` key).
    """
    if not workspace_slug:
        return []
    base_url = (base_url or "https://api.bitbucket.org/2.0").strip().rstrip("/")
    repos: list[dict] = []
    url = f"{base_url}/repositories/{workspace_slug}?pagelen=100"
    try:
        with httpx.Client(timeout=30) as client:
            while url:
                resp = client.get(url, auth=(username, app_password))
                if resp.status_code != 200:
                    logger.warning(
                        "REST repository list returned HTTP %d: %.200s",
                        resp.status_code, resp.text[:200],
                    )
                    break
                data = resp.json()
                repos.extend(data.get("values", []))
                url = data.get("next")
    except Exception as e:
        logger.warning("REST repository enumeration failed: %s", e)
    return repos


def _gather_context(
    install_dir: str,
    progress_callback: Optional[callable] = None,
    total_tables: int = 0,
    workspace_slug: Optional[str] = None,
    base_url: str = "https://api.bitbucket.org/2.0",
    username: str = "",
    app_password: str = "",
) -> dict:
    """Gather context information needed for qualifier queries.

    Returns a dict with:
      - workspace_slugs: set of workspace slugs
      - full_names: set of repository full names (from the REST API)
      - workspaces: list of raw workspace rows
      - projects: list of raw project rows
      - repositories: list of raw repository rows
      - warnings: any warnings encountered

    Bitbucket deprecated the ``bitbucket_my_*`` discovery tables (410 Gone), so
    discovery is scoped to the explicitly configured ``workspace_slug``:
      - bitbucket_workspace        -> where slug = <workspace_slug>
      - bitbucket_project          -> where workspace_slug = <workspace_slug>
      - repositories enumerated via GET /2.0/repositories/{workspace}
    """
    context: dict = {
        "workspace_slugs": set(),
        "full_names": set(),
        "workspaces": [],
        "projects": [],
        "repositories": [],
        "warnings": [],
    }

    requested_slug = (workspace_slug or "").strip()
    if not requested_slug:
        logger.warning("Context: workspace_slug is required for Bitbucket discovery")
        context["warnings"].append({
            "service": "Bitbucket", "action": "Config",
            "resource": "", "table": "",
            "message": (
                "A workspace slug is required for Bitbucket discovery. Bitbucket "
                "deprecated the workspace-listing endpoints (the bitbucket_my_* "
                "tables return 410 Gone), so add a workspace slug to the Bitbucket "
                "integration configuration (e.g. the 'my-company' in "
                "bitbucket.org/my-company)."
            ),
        })
        return context

    # --- Query bitbucket_workspace for the configured workspace ---
    workspaces = run_query(
        f"SELECT uuid FROM bitbucket_workspace WHERE slug = '{requested_slug}';",
        install_dir, CONTEXT_QUERY_TIMEOUT_SEC,
    )
    if workspaces:
        logger.info("Context: bitbucket_workspace returned %d workspace(s)", len(workspaces))
        context["workspaces"] = workspaces
        context["workspace_slugs"].add(requested_slug)
    else:
        logger.warning(
            "Context: bitbucket_workspace returned 0 workspaces for slug %s",
            requested_slug,
        )
        context["warnings"].append({
            "service": "Bitbucket", "action": "Scope",
            "resource": requested_slug, "table": "bitbucket_workspace",
            "message": (
                f"Workspace '{requested_slug}' was not found or the token does not "
                "have access to it. Check the workspace slug and the token scopes "
                "(Workspace: Read / Workspace membership: Read)."
            ),
        })

    if progress_callback:
        progress_callback({
            "total_tables": total_tables,
            "completed_tables": 1,
            "current_table": "bitbucket_workspace",
            "resources_found": len(context.get("workspaces", [])),
            "message": "Phase 1: workspace gathered, querying projects...",
            "warnings": context.get("warnings", [])[-20:],
        })

    # --- Query bitbucket_project for the configured workspace ---
    projects = run_query(
        f"SELECT uuid FROM bitbucket_project WHERE workspace_slug = '{requested_slug}';",
        install_dir, CONTEXT_QUERY_TIMEOUT_SEC,
    )
    if projects:
        logger.info("Context: bitbucket_project returned %d projects", len(projects))
        context["projects"] = projects
    else:
        logger.debug("Context: bitbucket_project returned 0 projects")

    if progress_callback:
        progress_callback({
            "total_tables": total_tables,
            "completed_tables": 2,
            "current_table": "bitbucket_project",
            "resources_found": len(context.get("workspaces", [])),
            "message": "Phase 1: projects gathered, enumerating repositories...",
            "warnings": context.get("warnings", [])[-20:],
        })

    # --- Enumerate repositories via the REST API (bitbucket_my_repository is 410 Gone) ---
    repositories = _list_workspace_repositories_via_api(
        base_url, username, app_password, requested_slug,
    )
    if repositories:
        logger.info(
            "Context: REST API returned %d repositories for %s",
            len(repositories), requested_slug,
        )
        context["repositories"] = repositories
        for r in repositories:
            full_name = r.get("full_name")
            if full_name:
                context["full_names"].add(full_name)
    else:
        logger.warning(
            "Context: no repositories found for workspace %s", requested_slug,
        )
        context["warnings"].append({
            "service": "Bitbucket", "action": "Context",
            "resource": requested_slug, "table": "bitbucket_repository",
            "message": (
                f"No repositories found in workspace '{requested_slug}'. Check that "
                "the API token has 'Repository: Read' scope."
            ),
        })

    if progress_callback:
        progress_callback({
            "total_tables": total_tables,
            "completed_tables": 3,
            "current_table": "bitbucket_repository",
            "resources_found": len(context.get("workspaces", [])),
            "message": f"Phase 1: gathered {len(context.get('workspace_slugs', set()))} workspace(s), "
                      f"{len(context.get('repositories', []))} repositories",
            "warnings": context.get("warnings", [])[-20:],
        })

    logger.info(
        "Context gathered: %d workspaces, %d projects, %d repositories",
        len(context["workspace_slugs"]), len(context["projects"]), len(context["repositories"]),
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

    Asset-inventory mode: selects only the identifier column (``uuid`` by
    default) so each row carries just the id. Rows with no resolvable id are
    skipped (``_row_to_entry`` returns ``None``). Selecting ``uuid`` alone
    also sidesteps the buggy ``default_reviewers`` hydrate that panicked
    ``select *`` on ``bitbucket_repository``.
    """
    columns = _table_id_column(table_name)
    if where:
        sql = f"select {columns} from {table_name} where {where};"
    else:
        sql = _table_select_sql(table_name)
    rows = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
    if rows:
        logger.debug("  %s %s -> %d rows", table_name, f"({where})" if where else "", len(rows))
        entries = []
        for r in rows:
            entry = _row_to_entry(r, table_name, canonical_type)
            if entry:
                entries.append(entry)
        return entries
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
    ``cancel_check`` is invoked before each qualifier query so a bulk-import
    cancellation interrupts a long table task between queries.
    """
    warnings: list[dict] = []
    entries: list[dict] = []

    if table_name in WORKSPACE_SLUG_QUALIFIER_TABLES:
        for slug in sorted(context.get("workspace_slugs", set())):
            if cancel_check:
                cancel_check()
            qualifier = "slug" if table_name == "bitbucket_workspace" else "workspace_slug"
            entries.extend(_query_where(table_name, canonical_type, install_dir,
                                        where=f"{qualifier} = '{slug}'"))
    elif table_name in REPOSITORY_QUALIFIER_TABLES:
        for full_name in sorted(context.get("full_names", set())):
            if cancel_check:
                cancel_check()
            qualifier = "full_name" if table_name == "bitbucket_repository" else "repository_full_name"
            entries.extend(_query_where(table_name, canonical_type, install_dir,
                                        where=f"{qualifier} = '{full_name}'"))
    else:
        # No qualifier needed — SELECT *
        entries = _query_where(table_name, canonical_type, install_dir)

    return table_name, entries, warnings


# ===================================================================
# 8. Main import function
# ===================================================================
def _write_bitbucket_spc(config_dir: Path, base_url: str, username: str, app_password: str) -> Path:
    """Write a bitbucket.spc connection config with the given credentials."""
    spc = f'''
connection "bitbucket" {{
  plugin = "bitbucket"
  username = "{username}"
  password = "{app_password}"
  base_url = "{base_url}"
}}
'''
    path = config_dir / "bitbucket.spc"
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
                        "service": "Bitbucket", "action": "Timeout",
                        "resource": "", "table": table,
                        "message": f"Query for {table} was cancelled due to overall timeout",
                    })
                except (ImportCancelledError, NetworkUnavailableError):
                    raise
                except Exception as e:
                    logger.warning("  %s -> error: %s", table, e)
                    all_warnings.append({
                        "service": "Bitbucket", "action": "Error",
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
                "service": "Bitbucket", "action": "Import",
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


async def import_bitbucket_resources_via_steampipe(
    base_url: str,
    username: str,
    app_password: str,
    db=None,
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
    workspace_slug: Optional[str] = None,
) -> dict:
    """
    Discover Bitbucket resources via Steampipe using email/username + API token.

    Flow:
      1. Create a temporary Steampipe config directory with credentials
      2. Phase 1: Gather context — the configured workspace (bitbucket_workspace
         where slug = ...), its projects (bitbucket_project where workspace_slug
         = ...) and its repositories (enumerated via the REST API)
      3. Phase 2: Query qualifier tables in parallel
      4. Map each result to the appropriate canonical type
      5. Return structured data ready for ingestion

    ``workspace_slug`` is REQUIRED — Bitbucket deprecated the workspace-listing
    endpoints (the bitbucket_my_* tables return 410 Gone), so discovery must be
    scoped to a single workspace.
    """
    base_url = (base_url or "https://api.bitbucket.org/2.0").strip().rstrip("/")

    # Point the network gate at the Bitbucket API so a connectivity probe
    # checks the same network path the Steampipe plugin uses.
    set_network_probe_url(base_url)
    username = (username or "").strip()
    app_password = (app_password or "").strip()
    workspace_slug = (workspace_slug or "").strip()

    if not username or not app_password:
        return {"resources_discovered": 0, "resources_detail": [], "warnings": [
            {"service": "Bitbucket", "action": "Config", "resource": "", "table": "",
             "message": "Bitbucket email and API token are required."},
        ]}

    if not workspace_slug:
        return {"resources_discovered": 0, "resources_detail": [], "warnings": [
            {"service": "Bitbucket", "action": "Config", "resource": "", "table": "",
             "message": (
                 "A workspace slug is required for Bitbucket discovery. Bitbucket "
                 "deprecated the workspace-listing endpoints (the bitbucket_my_* "
                 "tables return 410 Gone), so add a workspace slug to the Bitbucket "
                 "integration configuration (e.g. the 'my-company' in "
                 "bitbucket.org/my-company)."
             )},
        ]}

    # ---------------------------------------------------------------
    # Validate table-to-type mapping
    # ---------------------------------------------------------------
    if not BITBUCKET_STEAMPIPE_TABLE_TO_TYPE:
        logger.error("BITBUCKET_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
        return {"resources_discovered": 0, "resources_detail": []}

    # Build the batch table list (all tables except context tables)
    batch_tables = [
        (t, ct) for t, ct in BITBUCKET_STEAMPIPE_TABLE_TO_TYPE.items()
        if t not in CONTEXT_TABLES
    ]

    total_tables = len(batch_tables) + len(CONTEXT_TABLES)

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

        # Write bitbucket.spc with credentials
        _write_bitbucket_spc(config_dir, base_url, username, app_password)

        # ---------------------------------------------------------------
        # Phase 1: Gather context
        # ---------------------------------------------------------------
        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": "Phase 1: Gathering context (workspaces, projects, repositories)...",
                "warnings": [],
            })

        logger.info("Phase 1: Gathering context...")
        context = _gather_context(
            temp_dir,
            progress_callback=progress_callback,
            total_tables=total_tables,
            workspace_slug=workspace_slug,
            base_url=base_url,
            username=username,
            app_password=app_password,
        )
        all_warnings = list(context.get("warnings", []))
        all_resources: list[dict] = []

        # Context rows become assets too (the dedupe step removes overlap with
        # the qualifier queries below).
        for r in context.get("workspaces", []):
            entry = _row_to_entry(
                r, "bitbucket_workspace",
                BITBUCKET_STEAMPIPE_TABLE_TO_TYPE.get("bitbucket_workspace", "Organization"),
            )
            if entry:
                all_resources.append(entry)
        for r in context.get("projects", []):
            entry = _row_to_entry(
                r, "bitbucket_project",
                BITBUCKET_STEAMPIPE_TABLE_TO_TYPE.get("bitbucket_project", "Application"),
            )
            if entry:
                all_resources.append(entry)
        # NOTE: REST-enumerated repositories (context["repositories"]) are NOT
        # added here — they only feed context["full_names"]. The actual repo
        # resources come from the Phase 2 query `bitbucket_repository where
        # full_name = ...`, which returns the flattened columns (owner_display_name,
        # project_key, self_link, ...) the YAML rule expects. Adding the REST
        # rows first would make them win the dedupe-by-resource_id and discard
        # those richer steampipe rows.

        context_table_count = len(CONTEXT_TABLES)

        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": context_table_count,
                "current_table": "bitbucket_repository",
                "resources_found": len(all_resources),
                "message": f"Context gathered: {len(context.get('workspace_slugs', set()))} workspaces, "
                          f"{len(context.get('repositories', []))} repositories",
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
        # Deduplicate by resource_id
        # ---------------------------------------------------------------
        seen_ids: set[str] = set()
        deduped: list[dict] = []
        for r in all_resources:
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
            "Import complete: %d total Bitbucket resources from %d tables (%d warnings)",
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
            "provider": "Bitbucket",
            "account_id": base_url,
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
        "account_id": base_url,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate Bitbucket connection via Bitbucket REST API
# ===================================================================
def validate_bitbucket_connection(
    username: str,
    app_password: str,
    base_url: str = "https://api.bitbucket.org/2.0",
    workspace_slug: str = "",
) -> dict:
    """Validate Bitbucket credentials by calling the Bitbucket REST API.

    Uses GET /2.0/user with HTTP basic auth (Atlassian account email + API
    token — app passwords were removed on July 28, 2026). A workspace slug is
    required (Bitbucket deprecated the workspace-listing endpoints, so the
    import must be scoped to a single workspace); it is verified via
    GET /2.0/workspaces/{slug}.
    """
    base_url = (base_url or "https://api.bitbucket.org/2.0").strip().rstrip("/")
    username = (username or "").strip()
    app_password = (app_password or "").strip()
    slug = (workspace_slug or "").strip()

    if not username or not app_password:
        return {
            "success": False,
            "error": "Bitbucket email and API token are required.",
        }

    if not slug:
        return {
            "success": False,
            "error": (
                "A workspace slug is required for Bitbucket discovery. Bitbucket "
                "deprecated the workspace-listing endpoints (the bitbucket_my_* "
                "tables return 410 Gone), so add a workspace slug to the Bitbucket "
                "integration configuration (e.g. the 'my-company' in "
                "bitbucket.org/my-company)."
            ),
        }

    url = f"{base_url}/user"
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, auth=(username, app_password))

            if resp.status_code == 200:
                data = resp.json()
                display_name = data.get("display_name") or data.get("username") or "unknown"
                msg = f"Connected to Bitbucket as '{display_name}'."

                # Optional: verify the token can read the configured workspace
                if slug:
                    ws_resp = client.get(
                        f"{base_url}/workspaces/{slug}", auth=(username, app_password),
                    )
                    if ws_resp.status_code == 200:
                        ws = ws_resp.json()
                        ws_name = ws.get("name") or slug
                        msg = f"Connected to Bitbucket as '{display_name}' (workspace '{ws_name}')."
                    elif ws_resp.status_code == 404:
                        return {
                            "success": False,
                            "error": f"Workspace '{slug}' was not found. Check the workspace slug.",
                        }
                    elif ws_resp.status_code == 403:
                        return {
                            "success": False,
                            "error": (
                                f"The API token does not have access to workspace '{slug}'. "
                                "Add Workspace: Read / Workspace membership: Read to the token scopes."
                            ),
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Could not access workspace '{slug}' (HTTP {ws_resp.status_code}).",
                        }

                return {"success": True, "users_found": 1, "message": msg}
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "error": (
                        "Bitbucket authentication failed (401). App passwords were "
                        "removed on July 28, 2026 — create an API token at "
                        "bitbucket.org → Account settings → API tokens and use your "
                        "Atlassian account email as the username."
                    ),
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "error": (
                        "Bitbucket access denied (403). The API token lacks the "
                        "required scopes — grant Account: Read at minimum."
                    ),
                }
            else:
                return {
                    "success": False,
                    "error": f"Bitbucket API returned HTTP {resp.status_code}: {resp.text[:200]}",
                }
    except httpx.ConnectError:
        return {"success": False, "error": f"Could not connect to {base_url}. Check the base URL and network connectivity."}
    except httpx.TimeoutException:
        return {"success": False, "error": f"Connection to {base_url} timed out."}
    except Exception as e:
        return {"success": False, "error": str(e)}
