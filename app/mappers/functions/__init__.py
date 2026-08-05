"""Registry for Python functions referenced by canonical mapping rules.

Rules can declare ``type: function`` mappings that reference a registered
function by name.  This module provides the ``register`` decorator and the
``call_function`` dispatcher.

Usage::

    from app.mappers.functions import register

    @register("aws_iam_privilege_check")
    def check_privileges(attached_policy_arns: list, inline_policies: list) -> bool:
        ...
"""

from typing import Any, Callable

_FUNCTIONS: dict[str, Callable] = {}


def register(name: str) -> Callable:
    """Decorator that registers a function so the rules engine can call it."""

    def decorator(fn: Callable) -> Callable:
        if name in _FUNCTIONS:
            raise ValueError(f"Function '{name}' is already registered")
        _FUNCTIONS[name] = fn
        return fn

    return decorator


def call_function(ref: str, args: list[Any], source_data: dict) -> Any:
    """Look up a registered function and call it with resolved arguments.

    Each arg that looks like a JSONPath expression (``$.xxx``) is resolved
    against *source_data* first.
    """
    fn = _FUNCTIONS.get(ref)
    if fn is None:
        raise ValueError(f"Unknown function reference '{ref}' — has it been registered?")

    resolved_args = [_resolve_arg(a, source_data) for a in (args or [])]
    return fn(*resolved_args)


def _resolve_arg(arg: Any, source_data: dict) -> Any:
    """Resolve an argument — strings starting with ``$.`` are treated as
    JSONPath paths into ``source_data``; everything else is returned as-is.
    """
    if isinstance(arg, str) and arg.startswith("$."):
        return _resolve_jsonpath(arg, source_data)
    return arg


def _resolve_jsonpath(expr: str, data: dict) -> Any:
    """Resolve a simple dotted JSONPath like ``$.name`` or ``$.details.arn``."""
    parts = expr.lstrip("$.").split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


# Import function modules so their @register decorators run
# (lazy imports — safe because this module is loaded at startup)
from app.mappers.functions import aws_iam  # noqa: E402, F401
