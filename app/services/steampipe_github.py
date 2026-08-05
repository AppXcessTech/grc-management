"""
Dynamic Steampipe-based GitHub resource discovery.
Uses GitHub Steampipe table names and maps them to CanonicalTypes.

Authentication uses a GitHub Personal Access Token (PAT).

The GitHub Steampipe plugin requires many tables to be queried with specific
qualifiers (WHERE clauses). This module uses a two-phase approach:

  Phase 1 — Context gathering: Query context tables (github_my_repository,
             github_my_organization, github_team) to discover repos, orgs,
             and teams.

  Phase 2 — Qualifier queries: For each table category, query with the
            appropriate WHERE clause derived from Phase 1 results.

This mode is scoped to **asset inventory**: each table is queried for its
identifier column(s) only (``TABLE_ID_COLUMN``) so the inventory knows *what
exists* (id + provider + canonical type) without hydrating every column.
Composite identifiers (e.g. org variables are ``name`` + ``organization``)
are joined with ``:``. Context tables still select the extra columns they
need to derive qualifier values for Phase 2.

Performance design:
  - Inventory queries select only the identifier columns (no hydrate columns
    → faster, fewer permission-gated API calls)
  - Context queries run first (sequential, fast)
  - Qualifier queries run in parallel via ThreadPoolExecutor (max 5 concurrent)
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

from app.mappers.canonical_map import GITHUB_STEAMPIPE_TABLE_TO_TYPE, get_rule
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
# Inventory-mode identifier columns per table
# ---------------------------------------------------------------------------
# Asset inventory only needs a stable identifier per resource. Querying just
# the identifier column(s) instead of ``select *`` skips every hydrate column
# (which can call extra GitHub APIs the token isn't authorised for) and makes
# imports much faster.
#
# Composite identifiers (two columns) are joined with ``:`` when building the
# resource id, e.g. org variables are unique per (name, organization). The
# dependabot alert tables are namespaced by repository because alert numbers
# restart per repo. ``github_my_repository``/``github_my_organization`` map to
# ``id`` for inventory identity — context gathering still selects the extra
# columns (owner_login, name_with_owner, login) it needs for Phase 2.
TABLE_ID_COLUMN: dict[str, list[str]] = {
    # --- Identity / organization ---
    "github_user": ["id"],
    "github_organization_member": ["id"],
    "github_organization_external_identity": ["guid"],
    "github_my_organization": ["id"],
    "github_team": ["id"],
    "github_team_member": ["id"],
    "github_team_repository": ["id"],
    # --- Repository ---
    "github_repository": ["id"],
    "github_my_repository": ["id"],
    "github_repository_deployment": ["id"],
    "github_repository_environment": ["id"],
    "github_branch_protection": ["id"],
    "github_community_profile": ["repository_full_name"],
    "github_repository_ruleset": ["id"],
    "github_organization_ruleset": ["id"],
    "github_code_owner": ["repository_full_name", "line"],
    "github_repository_collaborator": ["repository_full_name", "user_login"],
    "github_repository_sbom": ["repository_full_name"],
    "github_repository_vulnerability_alert": ["repository_full_name", "number"],
    # --- Actions / pipelines ---
    "github_actions_artifact": ["id"],
    "github_actions_organization_variable": ["name", "organization"],
    "github_actions_repository_variable": ["name", "repository_full_name"],
    "github_actions_repository_runner": ["id"],
    "github_actions_repository_workflow_job": ["id"],
    "github_actions_repository_workflow_run": ["id"],
    "github_actions_repository_secret": ["repository_full_name", "name"],
    "github_workflow": ["id"],
    # --- Packages / audit / alerts ---
    "github_package": ["id"],
    "github_package_version": ["id"],
    "github_audit_log": ["id"],
    "github_organization_dependabot_alert": ["repository_full_name", "alert_number"],
    "github_repository_dependabot_alert": ["repository_full_name", "alert_number"],
}

# Extra columns to select for tables where the identifier alone is not enough
# to drive the import pipeline correctly. Currently used only for the identity
# tables: the import deduplicates Identity assets by ``login``/``user_login``
# so the same person appears once across github_user / organization_member /
# team_member / repository_collaborator / external_identity. These columns are
# NOT part of the resource id — they just ride along so dedup + display_name
# keep working in inventory mode.
TABLE_EXTRA_COLUMNS: dict[str, list[str]] = {
    "github_user": ["login"],
    "github_organization_member": ["login"],
    "github_team_member": ["login"],
    "github_organization_external_identity": ["user_login"],
}


def _table_id_columns(table_name: str) -> list[str]:
    """Return the identifier column(s) to select for a table.

    Defaults to ``id`` for tables without an explicit entry.
    """
    return TABLE_ID_COLUMN.get(table_name, ["id"])


def _table_select_columns(table_name: str) -> list[str]:
    """Return all columns to SELECT for a table (identifier + extras)."""
    return _table_id_columns(table_name) + TABLE_EXTRA_COLUMNS.get(table_name, [])


def _table_select_sql(table_name: str) -> str:
    """Build the inventory SELECT for a table — its identifier column(s) plus
    any dedup/display extras."""
    cols = ", ".join(_table_select_columns(table_name))
    return f"select {cols} from {table_name};"

# ---------------------------------------------------------------------------
# Qualifier map — defines what WHERE clause each table needs and where the
# qualifier value comes from.
#   qualifier:      column name in the WHERE clause (e.g. "organization")
#   value_source:   field name from context data (e.g. "owner_login")
# ---------------------------------------------------------------------------
TABLE_QUALIFIERS: dict[str, dict] = {
    # --- Organisation-scoped tables (need organization = '<owner_login>') ---
    "github_team":                      {"qualifier": "organization", "value_source": "owner_login"},
    "github_actions_organization_variable": {"qualifier": "organization", "value_source": "owner_login"},
    "github_organization_external_identity": {"qualifier": "organization", "value_source": "owner_login"},
    "github_organization_member":       {"qualifier": "organization", "value_source": "owner_login"},
    "github_audit_log":                 {"qualifier": "organization", "value_source": "owner_login"},
    "github_package":                   {"qualifier": "organization", "value_source": "owner_login"},
    "github_package_version":           {"qualifier": "organization", "value_source": "owner_login"},
    "github_organization_ruleset":      {"qualifier": "organization", "value_source": "owner_login"},
    "github_organization_dependabot_alert": {"qualifier": "organization", "value_source": "owner_login"},

    # --- Repository-scoped tables (need repository_full_name = '<name_with_owner>') ---
    "github_actions_repository_variable":  {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_actions_artifact":             {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_actions_repository_runner":    {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_actions_repository_workflow_job": {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_actions_repository_workflow_run": {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_actions_repository_secret":    {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_workflow":                     {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_environment":       {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_branch_protection":            {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_code_owner":                   {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_community_profile":            {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_ruleset":           {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_deployment":        {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_sbom":              {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_dependabot_alert":  {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_vulnerability_alert": {"qualifier": "repository_full_name", "value_source": "name_with_owner"},
    "github_repository_collaborator":      {"qualifier": "repository_full_name", "value_source": "name_with_owner"},

    # --- Tables needing full_name qualifier ---
    "github_repository":                  {"qualifier": "full_name", "value_source": "name_with_owner"},

    # --- Tables needing login qualifier ---
    "github_user":                        {"qualifier": "login", "value_source": "owner_login"},

    # --- Multi-qualifier tables (need organization + team_slug) ---
    # These require github_team to be queried in Phase 1 (context gathering)
    # so that team slugs are available to build the WHERE clause.
    "github_team_member": {
        "qualifiers": [
            {"qualifier": "organization", "value_source": "owner_login"},
            {"qualifier": "team_slug", "value_source": "team_slug"},
        ],
    },
    "github_team_repository": {
        "qualifiers": [
            {"qualifier": "organization", "value_source": "owner_login"},
            {"qualifier": "team_slug", "value_source": "team_slug"},
        ],
    },
}

# ===================================================================
# Token type helpers
# ===================================================================

def get_table_token_type(table_name: str) -> str:
    """Get the required token type for a given GitHub table.

    Returns ``"fine_grained"`` or ``"classic"`` based on the YAML rule.
    Defaults to ``"fine_grained"`` if the rule is not found.
    """
    try:
        rule = get_rule(table_name)
        return rule.token_type
    except KeyError:
        logger.debug(
            "No rule found for '%s' — defaulting to fine_grained", table_name
        )
        return "fine_grained"


def get_tables_by_token_type() -> tuple[list[str], list[str]]:
    """Split GitHub tables into those needing a fine-grained token and
    those needing a classic token.

    Returns (fine_grained_tables, classic_tables).
    """
    fine: list[str] = []
    classic: list[str] = []
    for table in GITHUB_STEAMPIPE_TABLE_TO_TYPE:
        tt = get_table_token_type(table)
        if tt == "classic":
            classic.append(table)
        else:
            fine.append(table)
    return fine, classic


# ===================================================================
# 1. Helper: resolve a stable resource_id from a row (GitHub-specific)
# ===================================================================
def resolve_resource_id(row: dict, table_name: str = "") -> str:
    """Pick the best identifier from a GitHub Steampipe row.

    In inventory mode the row carries only the identifier column(s) declared
    in ``TABLE_ID_COLUMN`` — those are returned directly (composite columns
    joined with ``:``). If the declared columns are missing (e.g. a row that
    didn't come from a minimal select), fall back to the legacy priority list.
    """
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

    # Legacy fallback — GitHub resources use 'node_id' (GraphQL ID) or 'id'
    # as primary identifiers.
    for key in (
        "node_id",
        "id",
        "name",
        "repository_full_name",
        "full_name",
        "login",
        "organization",
        "slug",
        "team_id",
        "workflow_id",
        "run_id",
        "job_id",
        "runner_id",
        "artifact_id",
        "package_id",
        "package_version_id",
        "environment_id",
        "deployment_id",
        "alert_id",
        "sbom_id",
        "ruleset_id",
        "branch_protection_id",
        "secret_name",
        "variable_name",
        "repository",
        "owner_login",
        "commit_sha",
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
# 2. Extract tags from a row (GitHub resources typically don't have tags)
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags if present (most GitHub resources don't have tags)."""
    raw = row.get("tags") or row.get("Topics") or row.get("topics")
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            if "Key" in raw[0] or "key" in raw[0]:
                return raw
            return [{"Key": t.get("key", t.get("Key", "")), "Value": t.get("value", t.get("Value", ""))} for t in raw]
        # If it's a list of strings (e.g., topics), convert to tags
        if raw and isinstance(raw[0], str):
            return [{"Key": t, "Value": t} for t in raw]
    if isinstance(raw, dict):
        return raw
    return None


# ===================================================================
# 3. Run a single Steampipe query
# ===================================================================
def run_query(sql: str, install_dir: str, timeout_sec: int = PER_QUERY_TIMEOUT_SEC) -> list[dict]:
    """Execute a Steampipe SQL query and return parsed rows."""
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
    # Skip rows with no identifier — they'd collide on the
    # (organization, provider, provider_resource_id) unique constraint.
    if not rid or rid == "unknown":
        return None
    tags = extract_tags(row)

    # Build display name
    name = (
        row.get("name")
        or row.get("full_name")
        or row.get("repository_full_name")
        or row.get("name_with_owner")
        or row.get("login")
        or row.get("organization")
        or row.get("slug")
        or row.get("node_id")
        or rid
    )

    entry = {
        "resource_type": table_name,
        "resource_id": rid,
        "canonical_type": canonical_type,
        "region": "global",
        "provider": "GitHub",
        "name": name,
        "display_name": name,
        "tags": tags,
        "details": row,
    }

    # Extract common relationship references
    relationships = {}
    for ref_key in (
        "organization", "Organization",
        "repository_full_name", "RepositoryFullName",
        "repository", "Repository",
        "owner_login", "OwnerLogin",
    ):
        if ref_key in row:
            rel_name = ref_key.replace("_", "").lower()
            relationships[rel_name] = row[ref_key]
    if relationships:
        entry["relationships"] = relationships

    return entry


# ===================================================================
# 5. Phase 1: Gather context (repos, orgs)
# ===================================================================
def _gather_context(
    install_dir: str,
    progress_callback: Optional[callable] = None,
    total_tables: int = 0,
) -> dict:
    """Gather context information needed for qualifier queries.

    ``progress_callback`` is invoked between the sequential context queries so
    that a bulk-import cancellation (which raises inside the callback) can
    interrupt context gathering promptly.

    Returns a dict with:
      - repositories: list of repo rows (with name_with_owner, owner_login, etc.)
      - owner_logins: set of unique owner logins
      - name_with_owners: list of unique name_with_owner values
      - organizations: list of org rows from github_my_organization
      - teams: list of team rows (with organization, slug, name, etc.)
      - warnings: any warnings encountered
    """
    context: dict = {
        "repositories": [],
        "owner_logins": set(),
        "name_with_owners": set(),  # set to prevent duplicate qualifier values
        "organizations": [],
        "teams": [],
        "warnings": [],
    }

    # --- Query github_my_repository ---
    # Inventory mode: select only the columns needed for context (owner_login,
    # name_with_owner for qualifiers) plus the repository id. This avoids the
    # JSONB columns (custom_properties, hooks) that can 403 with restricted
    # PATs — no information_schema round-trip needed.
    my_repo_sql = (
        "select id, owner_login, name_with_owner "
        "from github_my_repository;"
    )
    repo_rows = run_query(my_repo_sql, install_dir, CONTEXT_QUERY_TIMEOUT_SEC)
    if repo_rows:
        logger.info("Context: github_my_repository returned %d repos", len(repo_rows))
        context["repositories"] = repo_rows
        for r in repo_rows:
            login = r.get("owner_login")
            if login:
                context["owner_logins"].add(login)
            nwo = r.get("name_with_owner")
            if nwo:
                context["name_with_owners"].add(nwo)
    else:
        logger.warning("Context: github_my_repository returned 0 repos")
        context["warnings"].append({
            "service": "GitHub", "action": "Context",
            "resource": "", "table": "github_my_repository",
            "message": "No repositories found. Check that the token has repo access.",
        })

    if progress_callback:
        progress_callback({
            "total_tables": total_tables,
            "completed_tables": 1,
            "current_table": "github_my_repository",
            "resources_found": len(context.get("repositories", [])),
            "message": "Phase 1: repositories gathered, querying organizations...",
            "warnings": context.get("warnings", [])[-20:],
        })

    # --- Query github_my_organization ---
    org_rows = run_query(
        "select id, login from github_my_organization;",
        install_dir, CONTEXT_QUERY_TIMEOUT_SEC,
    )
    if org_rows:
        logger.info("Context: github_my_organization returned %d orgs", len(org_rows))
        context["organizations"] = org_rows
        for r in org_rows:
            login = r.get("login")
            if login:
                context["owner_logins"].add(login)

    if progress_callback:
        progress_callback({
            "total_tables": total_tables,
            "completed_tables": 2,
            "current_table": "github_my_organization",
            "resources_found": len(context.get("repositories", [])),
            "message": "Phase 1: organizations gathered, querying teams...",
            "warnings": context.get("warnings", [])[-20:],
        })

    # --- Query github_team for each org (needed for multi-qualifier tables like
    #     github_team_member and github_team_repository) ---
    owner_logins = list(context["owner_logins"])
    for team_idx, login in enumerate(owner_logins):
        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": 2,
                "current_table": "github_team",
                "resources_found": len(context.get("repositories", [])),
                "message": f"Phase 1: querying teams for '{login}' ({team_idx + 1}/{len(owner_logins)})...",
                "warnings": context.get("warnings", [])[-20:],
            })
        # Inventory mode: id + the columns needed for team qualifier queries
        # (organization, slug) and team display names (name).
        sql = (
            f"select id, organization, slug, name from github_team "
            f"where organization = '{login}';"
        )
        team_rows = run_query(sql, install_dir, CONTEXT_QUERY_TIMEOUT_SEC)
        if team_rows:
            logger.info("Context: github_team for '%s' returned %d teams", login, len(team_rows))
            for t in team_rows:
                t["_org_login"] = login  # tag with org for later use
            context["teams"].extend(team_rows)
        else:
            logger.debug("Context: github_team for '%s' returned 0 teams", login)

    if context["teams"]:
        logger.info("Context: %d total teams across %d orgs", len(context["teams"]), len(owner_logins))

    logger.info(
        "Context gathered: %d repos, %d orgs, %d teams, %d unique owners",
        len(context["repositories"]), len(context["organizations"]),
        len(context["teams"]), len(owner_logins),
    )

    return context


# ===================================================================
# 6. Phase 2: Query a single table with optional qualifier
# ===================================================================
def _query_with_qualifier(
    table_name: str,
    canonical_type: str,
    install_dir: str,
    qualifier_col: Optional[str] = None,
    qualifier_vals: Optional[list[str]] = None,
    cancel_check: Optional[callable] = None,
) -> tuple[list[dict], list[dict]]:
    """Query a single GitHub table, optionally with a WHERE qualifier.

    When qualifier_vals has multiple values, each value is queried in its own
    subprocess (since Steampipe requires operator '=' for some qualifiers).
    Queries run sequentially (not in parallel) to keep the implementation simple.
    ``cancel_check`` is invoked before each qualifier query so a bulk-import
    cancellation interrupts the loop between queries.

    Returns (entries, warnings).
    """
    warnings: list[dict] = []
    all_entries: list[dict] = []
    cols = ", ".join(_table_select_columns(table_name))

    if qualifier_col and qualifier_vals:
        # Query once per qualifier value
        for val in qualifier_vals:
            if cancel_check:
                cancel_check()
            if not val:
                continue
            sql = f"select {cols} from {table_name} where {qualifier_col} = '{val}';"
            rows = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
            if rows:
                for row in rows:
                    entry = _row_to_entry(row, table_name, canonical_type)
                    if entry:
                        all_entries.append(entry)
                logger.debug("  %s (WHERE %s='%s') -> %d rows", table_name, qualifier_col, val, len(rows))
    else:
        # No qualifier needed — minimal identifier-column SELECT
        sql = _table_select_sql(table_name)
        rows = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
        if rows:
            for row in rows:
                entry = _row_to_entry(row, table_name, canonical_type)
                if entry:
                    all_entries.append(entry)
            logger.debug("  %s -> %d rows", table_name, len(rows))

    return all_entries, warnings


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
    qualifier_info = TABLE_QUALIFIERS.get(table_name)

    if qualifier_info:
        # Check if this is a multi-qualifier table (needs multiple WHERE clauses)
        if "qualifiers" in qualifier_info:
            # Multi-qualifier query — iterate over teams
            entries = []
            warnings = []
            teams = context.get("teams", [])
            qualifiers = qualifier_info["qualifiers"]
            if not teams:
                logger.warning("No teams found in context for multi-qualifier table %s", table_name)
                return table_name, [], [{
                    "service": "GitHub", "action": "Query",
                    "resource": "", "table": table_name,
                    "message": f"No teams available for multi-qualifier query on {table_name}.",
                }]
            for team in teams:
                if cancel_check:
                    cancel_check()
                org = team.get("organization") or team.get("_org_login", "")
                slug = team.get("slug", "")
                if not org or not slug:
                    continue
                cols = ", ".join(_table_select_columns(table_name))
                sql = f"select {cols} from {table_name} where organization = '{org}' and team_slug = '{slug}';"
                rows = run_query(sql, install_dir, PER_QUERY_TIMEOUT_SEC)
                if rows:
                    for row in rows:
                        entry = _row_to_entry(row, table_name, canonical_type)
                        if entry:
                            entries.append(entry)
                    logger.debug("  %s (WHERE org='%s' slug='%s') -> %d rows",
                                 table_name, org, slug, len(rows))
            return table_name, entries, warnings

        # Single qualifier
        # Table needs a qualifier
        qualifier_col = qualifier_info["qualifier"]
        value_source = qualifier_info["value_source"]

        if value_source == "owner_login":
            vals = list(context.get("owner_logins", set()))
        elif value_source == "name_with_owner":
            vals = list(context.get("name_with_owners", []))
        else:
            vals = []

        entries, warnings = _query_with_qualifier(
            table_name, canonical_type, install_dir,
            qualifier_col=qualifier_col, qualifier_vals=vals,
            cancel_check=cancel_check,
        )
    else:
        # No qualifier needed (or table has custom handling)
        entries, warnings = _query_with_qualifier(
            table_name, canonical_type, install_dir,
            qualifier_col=None, qualifier_vals=None,
            cancel_check=cancel_check,
        )

    return table_name, entries, warnings


# ===================================================================
# 8. Main import function
# ===================================================================
def _write_github_spc(config_dir: Path, token: str) -> Path:
    """Write a github.spc connection config with the given token."""
    spc = f'''
connection "github" {{
  plugin = "github"
  token  = "{token}"
}}
'''
    path = config_dir / "github.spc"
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
    """Query a batch of tables in parallel.

    Args:
        tables: List of (table_name, canonical_type) tuples to query.
        temp_dir: Steampipe install directory.
        context: Context dict with owner_logins, name_with_owners, etc.
        completed: Counter of completed tables so far.
        total_tables: Total number of tables across all batches (for progress).
        all_resources: Shared list to collect entries (modified in place).
        all_warnings: Shared list to collect warnings (modified in place).
        progress_callback: Optional callback for progress updates.

    Returns:
        Updated completed counter.
    """
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
                        "service": "GitHub", "action": "Timeout",
                        "resource": "", "table": table,
                        "message": f"Query for {table} was cancelled due to overall timeout",
                    })
                except (ImportCancelledError, NetworkUnavailableError):
                    raise
                except Exception as e:
                    logger.warning("  %s -> error: %s", table, e)
                    all_warnings.append({
                        "service": "GitHub", "action": "Error",
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
                "service": "GitHub", "action": "Import",
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


async def import_github_resources_via_steampipe(
    github_token: str,
    classic_token: str | None = None,
    db=None,
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
) -> dict:
    """
    Discover GitHub resources via Steampipe using Personal Access Tokens.

    Supports two token types:
      - ``github_token`` (fine-grained, required): Used for most tables
        (repositories, teams, members, branch protection, etc.)
      - ``classic_token`` (classic, optional): Needed for tables that require
        classic PAT scope (audit log, user identity, external identity)

    If ``classic_token`` is not provided, classic-required tables are skipped
    gracefully with a warning surfaced in the UI.

    Flow:
      1. Split tables by required token type
      2. Create a temporary Steampipe config directory with credentials
      3. Phase 1: Gather context (repos, orgs, teams) using fine-grained token
      4. Phase 2a: Query fine-grained tables in parallel
      5. Phase 2b: If classic token available, swap config and query classic tables
      6. Map each result to the appropriate canonical type
      7. Return structured data ready for ingestion
    """
    # ---------------------------------------------------------------
    # Split tables by token type
    # ---------------------------------------------------------------
    fine_grained_tables, classic_tables = get_tables_by_token_type()

    # Remove context tables from the fine-grained list (they're handled in Phase 1)
    context_tables = {"github_my_repository", "github_my_organization", "github_team"}
    fine_grained_tables = [t for t in fine_grained_tables if t not in context_tables]
    classic_tables = [t for t in classic_tables if t not in context_tables]

    has_classic = bool(classic_token and classic_token.strip())

    logger.info(
        "Token setup: fine_grained_token=%s, classic_token=%s. "
        "Tables: %d fine-grained, %d classic-required.",
        "<set>" if github_token else "<empty>",
        "<set>" if has_classic else "<not provided>",
        len(fine_grained_tables), len(classic_tables),
    )

    # Point the network gate at the GitHub API so a connectivity probe
    # checks the same network path the Steampipe plugin uses.
    set_network_probe_url("https://api.github.com")

    total_tables = (
        len(fine_grained_tables)
        + (len(classic_tables) if has_classic else 0)
        + 3  # context tables: my_repository, my_organization, team
    )

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

        # Write github.spc with fine-grained token (used for context + fine-grained tables)
        _write_github_spc(config_dir, github_token)

        # ---------------------------------------------------------------
        # Validate table-to-type mapping
        # ---------------------------------------------------------------
        if not GITHUB_STEAMPIPE_TABLE_TO_TYPE:
            logger.error("GITHUB_STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
            return {"resources_discovered": 0, "resources_detail": []}

        # ---------------------------------------------------------------
        # Phase 1: Gather context
        # ---------------------------------------------------------------
        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": "Phase 1: Gathering context (repositories, organizations)...",
                "warnings": [],
            })

        logger.info("Phase 1: Gathering context...")
        context = _gather_context(
            temp_dir,
            progress_callback=progress_callback,
            total_tables=total_tables,
        )
        all_warnings = list(context.get("warnings", []))
        all_resources: list[dict] = []

        # Phase 1 tables count as completed
        context_table_count = 3  # github_my_repository + github_my_organization + github_team

        if progress_callback:
            progress_callback({
                "total_tables": total_tables,
                "completed_tables": context_table_count,
                "current_table": "github_my_repository",
                "resources_found": len(context.get("repositories", [])),
                "message": f"Context gathered: {len(context.get('repositories', []))} repos, "
                          f"{len(context.get('owner_logins', set()))} owners, "
                          f"{len(context.get('teams', []))} teams",
                "warnings": all_warnings[-20:],
            })

        # ---------------------------------------------------------------
        # Phase 2a: Query fine-grained tables (with fine-grained token)
        # ---------------------------------------------------------------
        completed = context_table_count

        if fine_grained_tables:
            fine_batch = [(t, GITHUB_STEAMPIPE_TABLE_TO_TYPE[t]) for t in fine_grained_tables]
            logger.info(
                "Phase 2a: Querying %d fine-grained tables (max %d concurrent)",
                len(fine_batch), MAX_CONCURRENT_QUERIES,
            )
            completed = _query_table_batch(
                fine_batch, temp_dir, context,
                completed, total_tables,
                all_resources, all_warnings, progress_callback,
                cancel_check,
            )

        # ---------------------------------------------------------------
        # Phase 2b: Query classic-required tables (if classic token available)
        # ---------------------------------------------------------------
        if classic_tables:
            if has_classic:
                # Swap config to classic token
                _write_github_spc(config_dir, classic_token.strip())

                classic_batch = [(t, GITHUB_STEAMPIPE_TABLE_TO_TYPE[t]) for t in classic_tables]
                logger.info(
                    "Phase 2b: Querying %d classic-required tables with classic token",
                    len(classic_batch),
                )
                completed = _query_table_batch(
                    classic_batch, temp_dir, context,
                    completed, total_tables,
                    all_resources, all_warnings, progress_callback,
                    cancel_check,
                )
            else:
                # No classic token — skip these tables gracefully
                for table in classic_tables:
                    completed += 1
                    all_warnings.append({
                        "service": "GitHub", "action": "Skipped",
                        "resource": "", "table": table,
                        "message": (
                            f"'{table}' requires a classic PAT. "
                            "Connect a classic token to enable audit log "
                            "and user-identity sync."
                        ),
                    })
                    if progress_callback:
                        progress_callback({
                            "total_tables": total_tables,
                            "completed_tables": completed,
                            "current_table": table,
                            "resources_found": len(all_resources),
                            "message": f"Skipped {table} (needs classic token)",
                            "warnings": all_warnings[-20:],
                        })

        # ---------------------------------------------------------------
        # Add teams from context to resources
        # ---------------------------------------------------------------
        # NOTE: Repos are NOT re-added here because github_repository (Phase 2a)
        # already captures every repo via the full_name qualifier. Adding them
        # again from context would create duplicate assets.
        # Teams however need to be added here because github_team is excluded
        # from Phase 2a (it's a context-only table used for multi-qualifier
        # queries like github_team_member / github_team_repository).
        for t in context.get("teams", []):
            entry = _row_to_entry(t, "github_team",
                                  GITHUB_STEAMPIPE_TABLE_TO_TYPE.get("github_team", "Group"))
            if not entry:
                continue
            entry["action"] = "discovered"
            all_resources.append(entry)

        # ---------------------------------------------------------------
        # Deduplicate by resource_id (or login for Identity types)
        # ---------------------------------------------------------------
        # GitHub has 5 identity tables (organization_member, team_member, user,
        # repository_collaborator, external_identity) that can all return the same
        # person with different resource_ids (team_member uses the team-membership
        # node_id, repo_collaborator uses a different node_id, etc.).
        # For Identity entries, dedup by the user's login from details, since
        # that is consistent across all tables.  Non-identity entries still dedup
        # by resource_id as before.
        seen_ids: set[str] = set()
        deduped: list[dict] = []
        for r in all_resources:
            is_identity = r.get("canonical_type") == "Identity"
            if is_identity:
                # Extract login directly from raw details — this is reliable
                # across all identity tables (login / user_login are always present
                # and consistent for the same person).
                details = r.get("details", {}) or {}
                dedup_key = details.get("login") or details.get("user_login") or r.get("display_name", "") or r.get("resource_id", "")
            else:
                dedup_key = r.get("resource_id", "")
            if not dedup_key or dedup_key == "unknown":
                deduped.append(r)
            elif dedup_key not in seen_ids:
                seen_ids.add(dedup_key)
                deduped.append(r)
        duplicates_removed = len(all_resources) - len(deduped)
        if duplicates_removed:
            logger.warning(
                "Removed %d duplicate resource entries (dedup by %s)",
                duplicates_removed,
                "login for Identity, resource_id for others",
            )
        all_resources = deduped

        tables_with_data = {r["resource_type"] for r in all_resources}
        logger.info(
            "Import complete: %d total GitHub resources from %d tables (%d warnings)",
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
            "provider": "GitHub",
            "account_id": "github",
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
        "account_id": "github",
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: Validate GitHub connection via GitHub API
# ===================================================================
def validate_github_connection(
    github_token: str,
) -> dict:
    """Validate a GitHub PAT by calling the GitHub API directly.

    Uses the GitHub REST API (GET /user) rather than Steampipe so that
    validation works even when the Steampipe database is unavailable.
    """
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AppXcess-GRC/1.0",
    }
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get("https://api.github.com/user", headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            login = data.get("login", "unknown")
            return {
                "success": True,
                "users_found": 1,
                "message": f"Connected to GitHub as '{login}'.",
            }
        elif resp.status_code == 401:
            body = resp.text[:200]
            return {
                "success": False,
                "error": f"GitHub authentication failed (401). Token is invalid or expired. {body}",
            }
        elif resp.status_code == 403:
            body = resp.text[:200]
            return {
                "success": False,
                "error": f"GitHub access denied (403). Token may lack permissions. {body}",
            }
        else:
            return {
                "success": False,
                "error": f"GitHub API returned HTTP {resp.status_code}: {resp.text[:200]}",
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Could not connect to api.github.com. Check network connectivity."}
    except httpx.TimeoutException:
        return {"success": False, "error": "Connection to api.github.com timed out."}
    except Exception as e:
        return {"success": False, "error": str(e)}
