"""
Rule to detect raw secrets in plans.

This rule checks if any step contains raw secrets or sensitive information.
"""

import re
from typing import List

from plan_lint.types import ErrorCode, Plan, PlanError, PlanStep, Policy


def check_step(step: PlanStep, policy: Policy, step_idx: int) -> List[PlanError]:
    """
    Check if a step contains raw secrets or sensitive information.

    Args:
        step: The plan step to check.
        policy: The policy to validate against.
        step_idx: Index of the step in the plan.

    Returns:
        List of errors for any detected secrets.
    """
    errors = []
    step_str = str(step.args)

    # Check for patterns defined in policy
    for pattern in policy.deny_tokens_regex:
        matches = re.findall(pattern, step_str)

        if matches:
            errors.append(
                PlanError(
                    step=step_idx,
                    code=ErrorCode.RAW_SECRET,
                    msg=(
                        f"Potentially sensitive data matching pattern '{pattern}' "
                        f"found in arguments"
                    ),
                )
            )

    # Additional built-in patterns
    builtin_patterns = [
        # API keys and tokens
        r"[a-zA-Z0-9]{32,}",  # Long alphanumeric strings
        r"key-[a-zA-Z0-9]{16,}",
        r"token-[a-zA-Z0-9]{16,}",
        r"[a-zA-Z0-9_\-]{24}\.[a-zA-Z0-9_\-]{6}\.[a-zA-Z0-9_\-]{27}",  # JWT format
        # Credentials
        r"password\s*[=:]\s*['\"]?[\w\-\!\@\#\$\%\^\&\*\(\)]{8,}['\"]?",
        r"passwd\s*[=:]\s*['\"]?[\w\-\!\@\#\$\%\^\&\*\(\)]{8,}['\"]?",
        # AWS
        r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
    ]

    for pattern in builtin_patterns:
        matches = re.findall(pattern, step_str)

        if matches:
            errors.append(
                PlanError(
                    step=step_idx,
                    code=ErrorCode.RAW_SECRET,
                    msg="Potentially sensitive data detected in arguments",
                )
            )
            # Only report once for built-in patterns
            break

    return errors


def check_plan(plan: Plan, policy: Policy) -> List[PlanError]:
    """
    Check if any step in the plan contains raw secrets.

    Args:
        plan: The plan to check.
        policy: The policy to validate against.

    Returns:
        List of errors for any detected secrets.
    """
    errors = []

    for i, step in enumerate(plan.steps):
        step_errors = check_step(step, policy, i)
        errors.extend(step_errors)

    return errors
