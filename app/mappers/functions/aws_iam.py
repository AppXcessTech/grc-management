"""AWS IAM functions for the canonical mapping rules engine.

Each function is registered with ``@register(...)`` so the rules engine
can look them up by name from the YAML ``ref`` field.
"""

from app.mappers.functions import register


@register("aws_iam_privilege_check")
def check_privilege(attached_policy_arns: list, inline_policies: list) -> bool:
    """Determine whether an IAM principal has elevated privileges.

    Called by rules like::

        privileged:
          type: function
          ref: aws_iam_privilege_check
          args: ["$.attached_policy_arns", "$.inline_policies"]
    """
    if not attached_policy_arns and not inline_policies:
        return False

    # Common AWS-managed admin policies
    admin_policy_arns = {
        "arn:aws:iam::aws:policy/AdministratorAccess",
        "arn:aws:iam::aws:policy/IAMFullAccess",
        "arn:aws:iam::aws:policy/PowerUserAccess",
    }

    for arn in (attached_policy_arns or []):
        if arn in admin_policy_arns:
            return True

    # Check inline policies for any that contain "Resource": "*" and "Action": "*"
    for policy in (inline_policies or []):
        if isinstance(policy, dict):
            doc = policy.get("policy_document") or {}
            statements = doc.get("Statement", [])
            if isinstance(statements, dict):
                statements = [statements]
            for stmt in statements:
                if stmt.get("Effect") == "Allow":
                    resource = stmt.get("Resource", "")
                    action = stmt.get("Action", "")
                    if resource == "*" or (isinstance(action, str) and action == "*"):
                        return True
    return False


@register("aws_iam_inactive_days")
def check_inactive_days(password_last_used: str | None) -> int | None:
    """Calculate days since last password use.

    Returns the number of days, or ``None`` if never used.
    """
    if not password_last_used:
        return None

    from datetime import datetime, timezone

    try:
        last_used = datetime.fromisoformat(password_last_used.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - last_used
        return delta.days
    except (ValueError, TypeError):
        return None
