"""Rules engine — the core that applies YAML-defined mappings to source data.

Flow
====

1. A raw JSON row arrives from Steampipe (e.g. an ``aws_iam_user`` row).
2. The engine looks up the matching ``CanonicalMappingRule`` by ``source_table``.
3. For each entry in ``rule.mappings`` it:
   - Resolves the JSONPath against the source data (simple case)
   - Evaluates the expression (expression case)
   - Calls the registered function (function case)
4. It applies ``rule.defaults``.
5. It builds the ``provider_resource_id`` from ``rule.canonical_id_template``.
6. It validates ``rule.required_fields``.
7. It returns a canonical dict ready for ingestion.
"""

import logging
import re
from typing import Any

from app.mappers.rule import CanonicalMappingRule
from app.mappers.functions import call_function
from app.models.enums import CanonicalType

logger = logging.getLogger(__name__)

# The set of all valid canonical category values (the 44 CanonicalType values)
_VALID_CANONICAL_CATEGORIES: set[str] = {ct.value for ct in CanonicalType}

# (source_table, field) pairs already reported as missing a required field
_REQUIRED_FIELD_WARNED: set[tuple[str, str]] = set()


# ---------------------------------------------------------------------------
# JSONPath resolver
# ---------------------------------------------------------------------------

def resolve_jsonpath(expr: str, data: dict) -> Any:
    """Resolve a dotted JSONPath expression against *data*.

    Supports three forms:

    - Simple path: ``$.name``, ``$.details.arn``
    - ``or``-chain: ``$.name or $.Name or $.arn``
    - Literal string: any value not starting with ``$.``
    """
    expr = expr.strip()

    # If it's not a JSONPath expression, return as-is
    if not expr.startswith("$."):
        return expr

    # Handle "or" chains
    if " or " in expr:
        for candidate in expr.split(" or "):
            result = _resolve_single_path(candidate.strip(), data)
            if result is not None and result != "":
                return result
        return None

    return _resolve_single_path(expr, data)


def _resolve_single_path(expr: str, data: dict) -> Any:
    """Resolve a single dotted path like ``$.name`` or ``$.details.arn``."""
    parts = expr.lstrip("$.").split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if idx < len(current) else None
        else:
            return None
    return current


# ---------------------------------------------------------------------------
# Expression evaluator
# ---------------------------------------------------------------------------

# Safe built-ins allowed in expressions
_SAFE_BUILTINS = {
    "True": True,
    "False": False,
    "None": None,
    # JSON-style null (used in YAML rules) aliases Python's None
    "null": None,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "len": len,
    "list": list,
    "dict": dict,
    "isinstance": isinstance,
    "type": type,
    "abs": abs,
    "min": min,
    "max": max,
    "any": any,
    "all": all,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "range": range,
    "map": map,
    "filter": filter,
    "sum": sum,
    "round": round,
    "not": lambda a: not a,
}


_EXPRESSION_GLOBALS = {
    "__builtins__": {},
    **_SAFE_BUILTINS,
}

# Matches a C-style ternary at the top level: ``cond ? A : B``
_C_TERNARY_RE = re.compile(r"^(.*?)\s*\?\s*(.*?)\s*:\s*(.*?)$")


def _translate_c_ternary(expr: str) -> str:
    """Convert a C-style ternary ``cond ? A : B`` to Python ``A if cond else B``.

    Rules authored with JSON-ish syntax (e.g.
    ``$.tags.Name != null ? $.tags.Name : $.instance_id``) use the C-style
    ternary. Python's ``eval`` cannot parse ``?:``, so translate it before
    evaluation. Nested ternaries are not supported (none in the rule set).
    """
    m = _C_TERNARY_RE.match(expr.strip())
    if not m:
        return expr
    cond, if_true, if_false = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    return f"{if_true} if {cond} else {if_false}"


def evaluate_expression(expr: str, source_data: dict) -> Any:
    """Evaluate a simple expression against *source_data*.

    The expression can reference source fields using JSONPath syntax
    (``$.field``, ``$.nested.field``) which gets resolved first before
    the expression is evaluated.
    """
    # First, resolve any JSONPath references in the expression
    resolved_expr = _resolve_jsonpath_refs(expr, source_data)
    # Then translate C-style ternaries (``?:``) to Python ternary form
    resolved_expr = _translate_c_ternary(resolved_expr)

    try:
        result = eval(resolved_expr, _EXPRESSION_GLOBALS, {"data": source_data})
        return result
    except Exception as exc:
        logger.warning("Expression evaluation failed: %s → %s", expr, exc)
        return None


_JSONPATH_RE = re.compile(r"\$\.([a-zA-Z_][a-zA-Z0-9_.]*)")


def _resolve_jsonpath_refs(expr: str, source_data: dict) -> str:
    """Replace ``$.field`` references in an expression with their resolved values.

    ``$.name`` → ``'actual_value'``  (quoted string)
    ``$.count`` → ``42``             (unquoted number)
    ``$.flag`` → ``True``            (unquoted bool)
    ``$.missing`` → ``None``         (unquoted None)
    """
    def _replacer(m: re.Match) -> str:
        path = "$." + m.group(1)
        value = resolve_jsonpath(path, source_data)
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)
        # String — quote it safely
        return repr(str(value))

    return _JSONPATH_RE.sub(_replacer, expr)


# ---------------------------------------------------------------------------
# ID template processor
# ---------------------------------------------------------------------------

def process_id_template(template: str, source_data: dict) -> str:
    """Process a canonical_id_template against source_data.

    Supports:
    - JSONPath: ``$.arn`` — extracts the value at that path
    - Template with placeholders: ``aws:iam_user:{arn}`` — ``{field}`` becomes
      the value of ``$.field``
    """
    template = template.strip()

    # JSONPath expression (starts with $.)
    if template.startswith("$."):
        value = resolve_jsonpath(template, source_data)
        return str(value) if value is not None else "unknown"

    # Template with {placeholders} — replace each {key} with the value at $.key
    def _replace_placeholder(m: re.Match) -> str:
        key = m.group(1)
        value = resolve_jsonpath(f"$.{key}", source_data)
        return str(value) if value is not None else f"{{{key}}}"

    return re.sub(r"\{(\w+)\}", _replace_placeholder, template)


# ---------------------------------------------------------------------------
# Main engine entrypoint
# ---------------------------------------------------------------------------

FieldValue = Any


def apply_rule(
    rule: CanonicalMappingRule,
    source_data: dict,
) -> dict[str, FieldValue]:
    """Apply a single mapping rule to source data, producing a canonical dict.

    The returned dict contains:

    * ``canonical_category`` — from the rule
    * ``source_table`` — from the rule
    * ``provider`` — from the rule
    * ``provider_resource_id`` — generated from the ID template
    * All mapped fields from ``rule.mappings``
    * All default values from ``rule.defaults``

    The output is designed to be compatible with ``CanonicalAssetData`` and
    the downstream ingestion pipeline.
    """
    result: dict[str, FieldValue] = {
        "canonical_type": rule.canonical_category,
        "source_table": rule.source_table,
    }

    # --- Process mappings ---
    for field_name, mapping in rule.mappings.items():
        mapping_type = mapping.get("type", "simple")

        try:
            if mapping_type == "simple":
                source_path = mapping.get("source_path", "")
                value = resolve_jsonpath(source_path, source_data)
            elif mapping_type == "expression":
                expr = mapping.get("expr", "")
                value = evaluate_expression(expr, source_data)
            elif mapping_type == "function":
                ref = mapping.get("ref", "")
                args = mapping.get("args", [])
                value = call_function(ref, args, source_data)
            else:
                logger.warning("Unknown mapping type '%s' for field '%s'", mapping_type, field_name)
                continue

            if value is not None:
                result[field_name] = value
        except Exception as exc:
            logger.warning("Mapping failed for field '%s' in rule '%s': %s",
                           field_name, rule.source_table, exc)

    # --- Apply defaults ---
    for key, value in rule.defaults.items():
        result.setdefault(key, value)

    # --- Resolve provider_resource_id ---
    if rule.canonical_id_template:
        result["provider_resource_id"] = process_id_template(
            rule.canonical_id_template, source_data
        )
    else:
        result["provider_resource_id"] = source_data.get("arn") or source_data.get("id") or "unknown"

    # --- Provider ---
    result.setdefault("provider", rule.provider)

    # --- Validate canonical_category is one of the 44 valid CanonicalType values ---
    cat = result.get("canonical_type", "")
    if cat not in _VALID_CANONICAL_CATEGORIES:
        raise ValueError(
            f"Rule '{rule.source_table}' produced invalid canonical_category "
            f"'{cat}'. Must be one of the {len(_VALID_CANONICAL_CATEGORIES)} "
            f"CanonicalType values: {sorted(_VALID_CANONICAL_CATEGORIES)}"
        )

    # --- Validate per-rule required fields ---
    # A missing required field is logged once per (table, field) instead of
    # once per resource — inventory-mode arn-only discovery intentionally
    # omits fields like `status`, and per-resource warnings would flood logs.
    for field in rule.required_fields:
        if field not in result or result[field] is None:
            key = (rule.source_table, field)
            if key not in _REQUIRED_FIELD_WARNED:
                _REQUIRED_FIELD_WARNED.add(key)
                logger.warning(
                    "Required field '%s' is missing after applying rule '%s'",
                    field, rule.source_table,
                )

    return result
