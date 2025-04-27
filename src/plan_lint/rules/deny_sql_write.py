"""
Rule to deny SQL write operations.

This rule checks if any step attempts to execute write SQL operations.
"""

from typing import List, Optional

from plan_lint.types import ErrorCode, Plan, PlanError, PlanStep, Policy


def check_step(step: PlanStep, policy: Policy, step_idx: int) -> Optional[PlanError]:
    """
    Check if a step attempts to perform SQL write operations.

    Args:
        step: The plan step to check.
        policy: The policy to validate against.
        step_idx: Index of the step in the plan.

    Returns:
        An error if the step attempts to write to SQL, None otherwise.
    """
    # Check for SQL tool with write capability
    if step.tool.startswith("sql.") and step.tool != "sql.query_ro":
        return PlanError(
            step=step_idx,
            code=ErrorCode.TOOL_DENY,
            msg=f"SQL write operation '{step.tool}' is not allowed",
        )

    # Check for SQL query with write=true flag
    if step.tool == "sql.query" and step.args.get("can_write") is True:
        return PlanError(
            step=step_idx,
            code=ErrorCode.TOOL_DENY,
            msg="sql.query can_write=true is not allowed",
        )

    # Check for write SQL keywords in query
    if step.tool.startswith("sql.") and "query" in step.args:
        query = step.args["query"].upper()
        write_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]

        for keyword in write_keywords:
            if keyword in query:
                return PlanError(
                    step=step_idx,
                    code=ErrorCode.TOOL_DENY,
                    msg=f"SQL query contains write operation '{keyword}'",
                )

    return None


def check_plan(plan: Plan, policy: Policy) -> List[PlanError]:
    """
    Check if any step in the plan attempts to perform SQL write operations.

    Args:
        plan: The plan to check.
        policy: The policy to validate against.

    Returns:
        List of errors for any SQL write attempts.
    """
    errors = []

    for i, step in enumerate(plan.steps):
        error = check_step(step, policy, i)
        if error:
            errors.append(error)

    return errors
