"""
Core module for plan-linter.

This module provides the main functionality for validating plans against policies.
"""

import re
from typing import Dict, List, Optional

from plan_lint.types import (
    ErrorCode,
    Plan,
    PlanError,
    PlanStep,
    PlanWarning,
    Policy,
    Status,
    ValidationResult,
)


def check_tools_allowed(
    step: PlanStep, allowed_tools: List[str], step_idx: int
) -> Optional[PlanError]:
    """
    Check if a step's tool is allowed by the policy.

    Args:
        step: The plan step to check.
        allowed_tools: List of allowed tool names.
        step_idx: Index of the step in the plan.

    Returns:
        An error if the tool is not allowed, None otherwise.
    """
    if not allowed_tools or step.tool in allowed_tools:
        return None

    return PlanError(
        step=step_idx,
        code=ErrorCode.TOOL_DENY,
        msg=f"Tool '{step.tool}' is not allowed by policy",
    )


def check_bounds(
    step: PlanStep, bounds: Dict[str, List[float]], step_idx: int
) -> List[PlanError]:
    """
    Check if a step's arguments are within bounds defined by the policy.

    Args:
        step: The plan step to check.
        bounds: Dictionary mapping tool.arg paths to [min, max] bounds.
        step_idx: Index of the step in the plan.

    Returns:
        List of errors for any bounds violations.
    """
    errors = []

    for bound_path, bound_values in bounds.items():
        try:
            # Split the path into tool name and arg name
            parts = bound_path.split(".", 1)
            if len(parts) != 2:
                continue

            tool_name, arg_name = parts

            # Check if this bound applies to the current step
            if step.tool != tool_name:
                continue

            # Check if the step has this argument
            if arg_name not in step.args:
                continue

            # Get the argument value
            arg_value = step.args[arg_name]

            # Check if the value is a number
            if not isinstance(arg_value, (int, float)):
                continue

            # Check if bound values has at least 2 elements
            if len(bound_values) < 2:
                continue

            # Get the min and max values
            min_val, max_val = bound_values[0], bound_values[1]

            # Check if the value is within bounds
            if arg_value < min_val or arg_value > max_val:
                errors.append(
                    PlanError(
                        step=step_idx,
                        code=ErrorCode.BOUND_VIOLATION,
                        msg=(
                            f"Argument '{arg_name}' value {arg_value} is outside "
                            f"bounds [{min_val}, {max_val}]"
                        ),
                    )
                )
        except (ValueError, IndexError, TypeError):
            # Log but continue if there's an issue with parsing the bounds
            continue

    return errors


def check_raw_secrets(
    step: PlanStep, deny_patterns: List[str], step_idx: int
) -> List[PlanError]:
    """
    Check if a step contains raw secrets or sensitive data.

    Args:
        step: The plan step to check.
        deny_patterns: List of regex patterns to deny.
        step_idx: Index of the step in the plan.

    Returns:
        List of errors for any detected secrets.
    """
    errors = []
    step_str = str(step.args)

    for pattern in deny_patterns:
        try:
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
        except re.error:
            # Skip invalid regex patterns
            continue

    return errors


def detect_cycles(plan: Plan) -> Optional[PlanError]:
    """
    Detect cycles in the plan's step dependencies.

    Args:
        plan: The plan to check.

    Returns:
        An error if a cycle is detected, None otherwise.
    """
    # Simple implementation - a more robust version would parse step references
    # from args and build a proper dependency graph
    visited = set()
    step_ids = set(step.id for step in plan.steps)

    # Check for references to other steps
    for i, step in enumerate(plan.steps):
        step_str = str(step.args)
        for step_id in step_ids:
            if step_id in step_str and step_id != step.id:
                # Check for cycles (very naive implementation)
                if step.id in visited:
                    return PlanError(
                        step=i,
                        code=ErrorCode.LOOP_DETECTED,
                        msg=f"Cycle detected involving step {step.id}",
                    )
                visited.add(step.id)

    return None


def calculate_risk_score(
    errors: List[PlanError], warnings: List[PlanWarning], risk_weights: Dict[str, float]
) -> float:
    """
    Calculate a risk score for the plan based on errors and warnings.

    Args:
        errors: List of errors found during validation.
        warnings: List of warnings found during validation.
        risk_weights: Dictionary mapping error/warning types to weights.

    Returns:
        A risk score between 0 and 1.
    """
    if not errors and not warnings:
        return 0.0

    score = 0.0
    error_types = {str(error.code).lower() for error in errors}

    # Add base score for each type of error
    for error_type in error_types:
        weight = risk_weights.get(error_type, 0.2)
        score += weight

    # Cap at 1.0
    return min(score, 1.0)


def validate_plan(plan: Plan, policy: Policy) -> ValidationResult:
    """
    Validate a plan against a policy.

    Args:
        plan: The plan to validate.
        policy: The policy to validate against.

    Returns:
        A ValidationResult object.
    """
    errors: List[PlanError] = []
    warnings: List[PlanWarning] = []

    # Check if plan has too many steps
    if len(plan.steps) > policy.max_steps:
        errors.append(
            PlanError(
                code=ErrorCode.MAX_STEPS_EXCEEDED,
                msg=(
                    f"Plan has {len(plan.steps)} steps, "
                    f"exceeding max of {policy.max_steps}"
                ),
            )
        )

    # Check for cycles
    cycle_error = detect_cycles(plan)
    if cycle_error:
        errors.append(cycle_error)

    # Validate each step
    for i, step in enumerate(plan.steps):
        # Check tools allowed
        tool_error = check_tools_allowed(step, policy.allow_tools, i)
        if tool_error:
            errors.append(tool_error)

        # Check bounds
        bound_errors = check_bounds(step, policy.bounds, i)
        errors.extend(bound_errors)

        # Check for secrets
        secret_errors = check_raw_secrets(step, policy.deny_tokens_regex, i)
        errors.extend(secret_errors)

    # Calculate risk score
    risk_score = calculate_risk_score(errors, warnings, policy.risk_weights)

    # Determine status
    status = Status.PASS
    if errors:
        status = Status.ERROR
    elif warnings:
        status = Status.WARN

    return ValidationResult(
        status=status,
        risk_score=risk_score,
        errors=errors,
        warnings=warnings,
    )
