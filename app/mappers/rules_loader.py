"""Loader that scans the `rules/` directory and builds an in-memory index of
canonical mapping rules.

Directory structure::

    rules/
      <canonical_category>/   (e.g. identity/, compute/, storage/)
        <source_table>.yaml    (e.g. aws_iam_user.yaml)

Each YAML file defines a ``CanonicalMappingRule`` whose ``source_table``
field is used as the lookup key.
"""

import logging
from pathlib import Path

import yaml

from app.mappers.rule import CanonicalMappingRule

logger = logging.getLogger(__name__)

# Path to the rules directory (relative to the project root)
RULES_DIR = Path(__file__).resolve().parent.parent.parent / "rules"


def _parse_mappings(raw: dict) -> dict:
    """Parse the `mappings` section of a rule.

    Supports three syntaxes:

    1. Simple JSONPath::

        display_name: "$.name"

    2. Expression with type key::

        status:
          type: expression
          expr: "$.password_last_used != null ? 'active' : 'inactive'"

    3. Function reference::

        privileged:
          type: function
          ref: aws_iam_privilege_check
          args: ["attached_policy_arns", "inline_policies"]
    """
    if not raw:
        return {}
    parsed: dict = {}
    for field_name, config in raw.items():
        if isinstance(config, str):
            # Simple: "field_name: $.source.path"
            parsed[field_name] = {
                "type": "simple",
                "source_path": config,
            }
        elif isinstance(config, dict):
            entry = dict(config)
            entry.setdefault("type", "simple")
            parsed[field_name] = entry
    return parsed


def load_all_rules(rules_dir: Path | None = None) -> dict[str, CanonicalMappingRule]:
    """Walk the ``rules/`` directory tree and load every ``.yaml`` file.

    Returns a dict keyed by ``source_table`` name so callers can do
    ``lookup[table_name]`` to retrieve the matching rule.
    """
    if rules_dir is None:
        rules_dir = RULES_DIR

    if not rules_dir.is_dir():
        logger.warning("Rules directory %s does not exist — no rules loaded", rules_dir)
        return {}

    rules: dict[str, CanonicalMappingRule] = {}
    loaded = 0

    for yaml_path in sorted(rules_dir.rglob("*.yaml")):
        # The parent directory name is the canonical category
        category_dir = yaml_path.parent.name

        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
        except Exception as exc:
            logger.error("Failed to parse %s: %s", yaml_path, exc)
            continue

        if not isinstance(data, dict):
            logger.warning("Skipping %s — not a valid YAML mapping", yaml_path)
            continue

        source_table = data.get("source_table")
        if not source_table:
            logger.warning("Skipping %s — missing 'source_table' field", yaml_path)
            continue

        # If the YAML doesn't explicitly set canonical_category, use the
        # directory name (mapped to CanonicalType's name field).
        canonical_category = data.get("canonical_category")
        if not canonical_category:
            # Capitalize first letter of directory name as a fallback
            canonical_category = category_dir.capitalize()

        mappings = _parse_mappings(data.get("mappings", {}))

        rule = CanonicalMappingRule(
            source_table=source_table,
            canonical_category=canonical_category,
            provider=data.get("provider", "Other"),
            token_type=data.get("token_type", "fine_grained"),
            canonical_id_template=data.get("canonical_id_template"),
            mappings=mappings,
            defaults=data.get("defaults", {}),
            # Support both `required_fields` and `required_canonical_fields` (user's
    # preferred naming from the template).
    required_fields=data.get("required_fields") or data.get("required_canonical_fields", []),
            version=data.get("version", 1),
            last_modified=data.get("last_modified"),
            owner=data.get("owner"),
        )

        rules[source_table] = rule
        loaded += 1

    logger.info("Loaded %d canonical mapping rules from %s", loaded, rules_dir)
    return rules


def build_type_map(rules: dict[str, CanonicalMappingRule]) -> dict[str, str]:
    """Build a flat ``{source_table: canonical_category_value}`` map.

    This is the equivalent of the old ``STEAMPIPE_TABLE_TO_TYPE`` /
    ``AZURE_STEAMPIPE_TABLE_TO_TYPE`` dicts.
    """
    return {
        table: rule.canonical_category
        for table, rule in rules.items()
    }
