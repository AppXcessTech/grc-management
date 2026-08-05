"""
Canonical mapping — loaded from YAML rule files under ``rules/``.

This module exists for backward compatibility with code that imports
``STEAMPIPE_TABLE_TO_TYPE``, ``AZURE_STEAMPIPE_TABLE_TO_TYPE``,
``OKTA_STEAMPIPE_TABLE_TO_TYPE``, ``GITHUB_STEAMPIPE_TABLE_TO_TYPE``,
``GITLAB_STEAMPIPE_TABLE_TO_TYPE``, ``BITBUCKET_STEAMPIPE_TABLE_TO_TYPE``
and ``get_type()``.  The authoritative source of truth is now the YAML
files in the ``rules/`` directory.
"""

import logging

from app.mappers.rules_loader import load_all_rules, build_type_map
from app.mappers.rule import CanonicalMappingRule

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load rules from YAML on first import
# ---------------------------------------------------------------------------
_ALL_RULES: dict[str, CanonicalMappingRule] = load_all_rules()
_TYPE_MAP: dict[str, str] = build_type_map(_ALL_RULES) if _ALL_RULES else {}


def _split_by_provider() -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str], dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    """Split the full type map into provider-specific dicts.

    Returns (aws, azure, gcp, okta, github, gitlab, microsoft365, bitbucket).
    """
    aws = {}
    azure = {}
    gcp = {}
    okta = {}
    github = {}
    gitlab = {}
    microsoft365 = {}
    bitbucket = {}
    for table, ctype in _TYPE_MAP.items():
        if table.startswith("aws_"):
            aws[table] = ctype
        elif table.startswith("azure_"):
            azure[table] = ctype
        elif table.startswith("gcp_"):
            gcp[table] = ctype
        elif table.startswith("okta_"):
            okta[table] = ctype
        elif table.startswith("github_"):
            github[table] = ctype
        elif table.startswith("gitlab_"):
            gitlab[table] = ctype
        elif table.startswith("microsoft365_"):
            microsoft365[table] = ctype
        elif table.startswith("bitbucket_"):
            bitbucket[table] = ctype
    return aws, azure, gcp, okta, github, gitlab, microsoft365, bitbucket


STEAMPIPE_TABLE_TO_TYPE, AZURE_STEAMPIPE_TABLE_TO_TYPE, GCP_STEAMPIPE_TABLE_TO_TYPE, OKTA_STEAMPIPE_TABLE_TO_TYPE, GITHUB_STEAMPIPE_TABLE_TO_TYPE, GITLAB_STEAMPIPE_TABLE_TO_TYPE, M365_STEAMPIPE_TABLE_TO_TYPE, BITBUCKET_STEAMPIPE_TABLE_TO_TYPE = _split_by_provider()


def get_type(table_name: str) -> str:
    """Look up the canonical category (e.g. ``"Compute"``) for a Steampipe
    table name.

    Raises ``KeyError`` for unmapped tables so they fail loudly at
    collection time rather than silently dropping into the wrong bucket.
    """
    try:
        return _TYPE_MAP[table_name]
    except KeyError:
        raise KeyError(
            f"No canonical type mapping for table '{table_name}'. "
            f"Add a rule file under rules/<category>/{table_name}.yaml."
        )


def get_rule(table_name: str) -> CanonicalMappingRule:
    """Look up the full ``CanonicalMappingRule`` for a Steampipe table name.

    Returns the complete rule object (with mappings, defaults, etc.)
    so callers can use ``rules_engine.apply_rule()`` for rich ingestion.

    Raises ``KeyError`` for unmapped tables.
    """
    try:
        return _ALL_RULES[table_name]
    except KeyError:
        raise KeyError(
            f"No canonical mapping rule for table '{table_name}'. "
            f"Add a rule file under rules/<category>/{table_name}.yaml."
        )


def reload_rules() -> None:
    """Reload all rules from disk (useful for testing or hot-reload)."""
    global _ALL_RULES, _TYPE_MAP
    global STEAMPIPE_TABLE_TO_TYPE, AZURE_STEAMPIPE_TABLE_TO_TYPE, GCP_STEAMPIPE_TABLE_TO_TYPE, OKTA_STEAMPIPE_TABLE_TO_TYPE, GITHUB_STEAMPIPE_TABLE_TO_TYPE, GITLAB_STEAMPIPE_TABLE_TO_TYPE, M365_STEAMPIPE_TABLE_TO_TYPE, BITBUCKET_STEAMPIPE_TABLE_TO_TYPE
    _ALL_RULES = load_all_rules()
    _TYPE_MAP = build_type_map(_ALL_RULES) if _ALL_RULES else {}
    STEAMPIPE_TABLE_TO_TYPE, AZURE_STEAMPIPE_TABLE_TO_TYPE, GCP_STEAMPIPE_TABLE_TO_TYPE, OKTA_STEAMPIPE_TABLE_TO_TYPE, GITHUB_STEAMPIPE_TABLE_TO_TYPE, GITLAB_STEAMPIPE_TABLE_TO_TYPE, M365_STEAMPIPE_TABLE_TO_TYPE, BITBUCKET_STEAMPIPE_TABLE_TO_TYPE = _split_by_provider()
    logger.info("Reloaded %d canonical mapping rules", len(_ALL_RULES))
