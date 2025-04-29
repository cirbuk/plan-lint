"""
OPA integration module for plan-lint.

This module provides functionality for evaluating plans against
policies written in Rego for the Open Policy Agent (OPA).
"""

from typing import Dict, Any, List, Optional, Union
import json
import logging
import subprocess
import tempfile
import os
from pathlib import Path

from plan_lint.types import Plan, Policy, PlanError, ErrorCode, ValidationResult, Status

# Configure logger
logger = logging.getLogger(__name__)


class OPAError(Exception):
    """Exception raised for OPA-related errors."""

    pass


def policy_to_rego(policy: Policy) -> str:
    """
    Convert a plan-lint Policy to a Rego policy.

    Args:
        policy: The plan-lint Policy object

    Returns:
        A Rego policy as a string
    """
    # Start with the package declaration
    rego_policy = "package planlint\n\n"

    # Default rule - deny by default, allow explicit
    rego_policy += "default allow = false\n\n"

    # Create allow rule based on tool allowlist
    if policy.allow_tools:
        tools_str = ", ".join([f'"{tool}"' for tool in policy.allow_tools])
        rego_policy += f"allowed_tools = [{tools_str}]\n\n"
        rego_policy += "allow {\n"
        rego_policy += "    # Check all steps use allowed tools\n"
        rego_policy += "    all_tools_allowed\n"
        rego_policy += "    # Check no bounds violations\n"
        rego_policy += "    no_bounds_violations\n"
        rego_policy += "    # Check no sensitive data\n"
        rego_policy += "    no_sensitive_data\n"
        rego_policy += "    # Check max steps not exceeded\n"
        rego_policy += "    steps_within_limit\n"
        rego_policy += "}\n\n"

        # Tool allowlist rule
        rego_policy += "all_tools_allowed {\n"
        rego_policy += "    # For each step\n"
        rego_policy += "    step := input.steps[_]\n"
        rego_policy += "    # The tool must be in the allowed list\n"
        rego_policy += "    tool := step.tool\n"
        rego_policy += "    tool == allowed_tools[_]\n"
        rego_policy += "}\n\n"

    # Bounds check
    if policy.bounds:
        rego_policy += "no_bounds_violations {\n"
        rego_policy += "    # For each step\n"
        rego_policy += "    step := input.steps[_]\n"
        rego_policy += "    tool := step.tool\n"
        rego_policy += "    args := step.args\n"

        # Add specific bound checks
        for bound_path, bound_values in policy.bounds.items():
            if len(bound_values) >= 2:
                min_val, max_val = bound_values[0], bound_values[1]
                parts = bound_path.split(".", 1)
                if len(parts) == 2:
                    tool_name, arg_name = parts
                    rego_policy += f"    # Check bounds for {bound_path}\n"
                    rego_policy += f'    tool == "{tool_name}" {{\n'
                    rego_policy += f'        args["{arg_name}"] >= {min_val}\n'
                    rego_policy += f'        args["{arg_name}"] <= {max_val}\n'
                    rego_policy += f"    }}\n"

        rego_policy += "}\n\n"

    # Sensitive data check using deny_tokens_regex
    if policy.deny_tokens_regex:
        patterns_str = ", ".join(
            [f'"{pattern}"' for pattern in policy.deny_tokens_regex]
        )
        rego_policy += f"sensitive_patterns = [{patterns_str}]\n\n"
        rego_policy += "no_sensitive_data {\n"
        rego_policy += "    # For each step\n"
        rego_policy += "    step := input.steps[_]\n"
        rego_policy += "    args_str := json.marshal(step.args)\n"
        rego_policy += "    # For each pattern\n"
        rego_policy += "    pattern := sensitive_patterns[_]\n"
        rego_policy += "    # No match should be found\n"
        rego_policy += "    not regex.match(pattern, args_str)\n"
        rego_policy += "}\n\n"

    # Max steps check
    rego_policy += f"steps_within_limit {{\n"
    rego_policy += f"    count(input.steps) <= {policy.max_steps}\n"
    rego_policy += f"}}\n\n"

    # Violations for detailed error reporting
    rego_policy += "# Gather violations for detailed error reporting\n"
    rego_policy += 'violations[{"step": step_idx, "code": "TOOL_DENY", "msg": msg}] {\n'
    rego_policy += "    step := input.steps[step_idx]\n"
    rego_policy += "    tool := step.tool\n"
    rego_policy += "    not tool == allowed_tools[_]\n"
    rego_policy += (
        '    msg := concat("", ["Tool \'", tool, "\' is not allowed by policy"])\n'
    )
    rego_policy += "}\n\n"

    # Bounds violations
    rego_policy += (
        'violations[{"step": step_idx, "code": "BOUND_VIOLATION", "msg": msg}] {\n'
    )
    rego_policy += "    step := input.steps[step_idx]\n"
    rego_policy += "    tool := step.tool\n"
    rego_policy += "    args := step.args\n"

    # Add specific bound violation checks
    for bound_path, bound_values in policy.bounds.items():
        if len(bound_values) >= 2:
            min_val, max_val = bound_values[0], bound_values[1]
            parts = bound_path.split(".", 1)
            if len(parts) == 2:
                tool_name, arg_name = parts
                rego_policy += f"    # Check violation for {bound_path}\n"
                rego_policy += f'    tool == "{tool_name}"\n'
                rego_policy += f'    arg_val := args["{arg_name}"]\n'
                rego_policy += f"    (arg_val < {min_val} or arg_val > {max_val})\n"
                rego_policy += f'    msg := concat("", ["Argument \'{arg_name}\' value ", to_string(arg_val), " is outside bounds [{min_val}, {max_val}]"])\n'

    rego_policy += "}\n\n"

    # Sensitive data violations
    rego_policy += (
        'violations[{"step": step_idx, "code": "RAW_SECRET", "msg": msg}] {\n'
    )
    rego_policy += "    step := input.steps[step_idx]\n"
    rego_policy += "    args_str := json.marshal(step.args)\n"
    rego_policy += "    pattern := sensitive_patterns[_]\n"
    rego_policy += "    regex.match(pattern, args_str)\n"
    rego_policy += '    msg := concat("", ["Potentially sensitive data matching pattern \'", pattern, "\' found in arguments"])\n'
    rego_policy += "}\n\n"

    # Max steps exceeded violation
    rego_policy += 'violations[{"code": "MAX_STEPS_EXCEEDED", "msg": msg}] {\n'
    rego_policy += f"    count(input.steps) > {policy.max_steps}\n"
    rego_policy += f'    msg := concat("", ["Plan has ", to_string(count(input.steps)), " steps, exceeding max of {policy.max_steps}"])\n'
    rego_policy += "}\n"

    return rego_policy


def evaluate_with_opa(
    plan: Plan, policy: Policy, rego_policy: Optional[str] = None
) -> ValidationResult:
    """
    Evaluate a plan against a policy using OPA.

    Args:
        plan: The plan to evaluate
        policy: The plan-lint Policy object
        rego_policy: Optional pre-generated Rego policy as a string

    Returns:
        ValidationResult object with errors and risk score
    """
    # Convert plan to JSON for OPA input
    plan_json = json.loads(plan.json())

    # Generate Rego policy if not provided
    if rego_policy is None:
        rego_policy = policy_to_rego(policy)

    # Create temporary files for policy and input
    policy_path = None
    input_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".rego", delete=False
        ) as policy_file:
            policy_file.write(rego_policy)
            policy_path = policy_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as input_file:
            json.dump(plan_json, input_file)
            input_path = input_file.name

        # Run OPA evaluation
        try:
            # Check if OPA is installed
            try:
                subprocess.run(["opa", "version"], check=True, capture_output=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                raise OPAError(
                    "OPA executable not found. Please install OPA and ensure it's in your PATH."
                )

            # Evaluate policy
            result = subprocess.run(
                [
                    "opa",
                    "eval",
                    "-d",
                    policy_path,
                    "-i",
                    input_path,
                    "data.planlint.allow",
                    "data.planlint.violations",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse OPA output
            opa_result = json.loads(result.stdout)

            # Extract allow/deny result
            is_allowed = False
            if "result" in opa_result and len(opa_result["result"]) > 0:
                is_allowed = (
                    opa_result["result"][0]
                    .get("expressions", [{}])[0]
                    .get("value", False)
                )

            # Extract violations
            violations = []
            if "result" in opa_result and len(opa_result["result"]) > 1:
                violations_result = (
                    opa_result["result"][1].get("expressions", [{}])[0].get("value", [])
                )
                for v in violations_result:
                    violations.append(v)

            # Convert violations to PlanError objects
            errors = []
            for v in violations:
                errors.append(
                    PlanError(
                        step=v.get("step"),
                        code=getattr(ErrorCode, v.get("code", "SCHEMA_INVALID")),
                        msg=v.get("msg", "Unknown error"),
                    )
                )

            # Calculate risk score using plan-lint's logic
            from plan_lint.core import calculate_risk_score

            risk_score = calculate_risk_score(errors, [], policy.risk_weights)

            # Determine status
            status = Status.PASS
            if errors:
                status = Status.ERROR

            # Override status based on risk threshold
            if risk_score >= policy.fail_risk_threshold:
                status = Status.ERROR

            return ValidationResult(
                status=status, risk_score=risk_score, errors=errors, warnings=[]
            )

        except subprocess.SubprocessError as e:
            raise OPAError(f"OPA evaluation failed: {e}")

    finally:
        # Clean up temporary files
        for path in [policy_path, input_path]:
            if path and os.path.exists(path):
                os.unlink(path)

    # This should never be reached, but just in case
    return ValidationResult(
        status=Status.ERROR,
        risk_score=1.0,
        errors=[
            PlanError(
                code=ErrorCode.SCHEMA_INVALID, msg="OPA evaluation failed unexpectedly"
            )
        ],
        warnings=[],
    )


def is_rego_policy(policy_content: str) -> bool:
    """
    Check if a string appears to be a Rego policy.

    Args:
        policy_content: String content to check

    Returns:
        True if it appears to be a Rego policy, False otherwise
    """
    # Basic heuristic: check for package declaration and rule definitions
    return "package" in policy_content and any(
        rule in policy_content for rule in ["default ", " = ", "{", "input."]
    )


def load_rego_policy_file(filepath: Union[str, Path]) -> str:
    """
    Load a Rego policy from a file.

    Args:
        filepath: Path to the Rego policy file

    Returns:
        The Rego policy as a string
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Rego policy file not found: {filepath}")

    with open(path, "r") as f:
        return f.read()
