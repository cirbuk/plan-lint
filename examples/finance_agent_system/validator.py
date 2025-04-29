"""
Plan validation module for the finance agent system.

This module integrates plan-lint for validating agent-generated plans
before they are executed, providing a critical security layer.
"""

import json
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional, Tuple

from plan_lint.core import validate_plan
from plan_lint.loader import is_rego_policy_file, load_policy, load_rego_policy
from plan_lint.types import (
    ErrorCode,
    Plan,
    PlanError,
    PlanStep,
    Status,
    ValidationResult,
)

# Path to the policy file, relative to this script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_POLICY_PATH = os.path.join(CURRENT_DIR, "finance_policy.yaml")
DEFAULT_REGO_POLICY_PATH = os.path.join(CURRENT_DIR, "finance_policy.rego")


def is_opa_installed() -> bool:
    """
    Check if OPA (Open Policy Agent) is installed.

    Returns:
        True if OPA is available, False otherwise.
    """
    try:
        subprocess.run(["opa", "version"], check=True, capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def direct_opa_evaluation(plan: Plan, rego_policy_path: str) -> ValidationResult:
    """
    Directly evaluate a plan against a Rego policy using OPA.

    Args:
        plan: The plan to evaluate
        rego_policy_path: Path to the Rego policy file

    Returns:
        ValidationResult with the evaluation results
    """
    # Convert plan to JSON for OPA input
    plan_json = json.loads(plan.json())

    # Create temporary files for input
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as input_file:
        json.dump(plan_json, input_file)
        input_path = input_file.name

    try:
        # Run OPA evaluation
        cmd = [
            "opa",
            "eval",
            "-d",
            rego_policy_path,
            "-i",
            input_path,
            "data.planlint",  # Request the entire planlint package
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Parse the result
        data = json.loads(result.stdout)

        if "result" in data and len(data["result"]) > 0:
            result_data = data["result"][0]["expressions"][0]["value"]

            # Extract the information
            # We don't need to use 'allow' since we determine validity
            # based on other factors
            violations = result_data.get("violations", [])
            risk_score = result_data.get("risk_score", 0.0)

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

            # Determine status
            status = Status.PASS
            if errors:
                status = Status.ERROR

            return ValidationResult(
                status=status, risk_score=risk_score, errors=errors, warnings=[]
            )

        # Default error response
        return ValidationResult(
            status=Status.ERROR,
            risk_score=1.0,
            errors=[
                PlanError(
                    code=ErrorCode.SCHEMA_INVALID,
                    msg="OPA evaluation failed: Invalid response format",
                )
            ],
            warnings=[],
        )

    except subprocess.SubprocessError as e:
        return ValidationResult(
            status=Status.ERROR,
            risk_score=1.0,
            errors=[
                PlanError(
                    code=ErrorCode.SCHEMA_INVALID, msg=f"OPA evaluation failed: {e}"
                )
            ],
            warnings=[],
        )
    finally:
        # Clean up temporary file
        if os.path.exists(input_path):
            os.unlink(input_path)


class PlanValidator:
    """
    Validates agent-generated plans against security policies using plan-lint.

    This class serves as the security gateway between agent planning and execution,
    ensuring all operations conform to organizational security policies.
    """

    def __init__(self, policy_path: Optional[str] = None, use_rego: bool = False):
        """
        Initialize the plan validator with a policy.

        Args:
            policy_path: Path to the policy file (YAML or Rego).
                If None, uses the default.
            use_rego: Whether to explicitly use the Rego policy.
        """
        self.rego_policy = None
        self.has_opa = is_opa_installed()

        # Determine which policy file to use
        if policy_path is None:
            if use_rego:
                policy_path = DEFAULT_REGO_POLICY_PATH
            else:
                policy_path = DEFAULT_POLICY_PATH

        # Check if the policy is a Rego policy
        self.is_rego = use_rego or (policy_path and is_rego_policy_file(policy_path))
        self.rego_policy_path = policy_path if self.is_rego else None

        # Load the policy and rego_policy (if applicable)
        policy_obj, rego_policy_str = load_policy(policy_path)
        self.policy = policy_obj  # Always a Policy object

        if self.is_rego:
            # Use the rego policy string returned or load it explicitly
            self.rego_policy = rego_policy_str

            # If rego_policy is still None, explicitly load it (fallback)
            if self.rego_policy is None and os.path.exists(policy_path):
                self.rego_policy = load_rego_policy(policy_path)

            # If OPA is not available, log a warning
            if not self.has_opa:
                print(
                    "Warning: OPA is not installed. Falling back to built-in validation."
                )

    def validate_plan_json(self, plan_json: str) -> Dict[str, Any]:
        """
        Validate a plan provided as a JSON string.

        Args:
            plan_json: The plan as a JSON string.

        Returns:
            Dictionary with validation results.
        """
        try:
            # Parse JSON
            plan_data = json.loads(plan_json)

            # Create a Plan object
            return self.validate_plan_dict(plan_data)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "status": "error",
                "risk_score": 1.0,
                "errors": [{"code": "SCHEMA_INVALID", "msg": "Invalid JSON format"}],
                "warnings": [],
            }

    def validate_plan_dict(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a plan provided as a dictionary.

        Args:
            plan_data: The plan as a dictionary.

        Returns:
            Dictionary with validation results.
        """
        try:
            # First, ensure it has the required structure
            if not self._has_valid_structure(plan_data):
                return {
                    "valid": False,
                    "status": "error",
                    "risk_score": 1.0,
                    "errors": [
                        {
                            "code": "SCHEMA_INVALID",
                            "msg": "Plan missing required fields",
                        }
                    ],
                    "warnings": [],
                }

            # Convert to Plan object
            plan = Plan(
                goal=plan_data.get("goal", ""),
                context=plan_data.get("context", {}),
                steps=[
                    PlanStep(
                        id=step.get("id", f"step-{i:03d}"),
                        tool=step.get("tool", ""),
                        args=step.get("args", {}),
                        on_fail=step.get("on_fail", "abort"),
                    )
                    for i, step in enumerate(plan_data.get("steps", []))
                ],
                meta=plan_data.get("meta", {}),
            )

            # Determine how to validate the plan
            if self.is_rego and self.has_opa and self.rego_policy_path:
                # Use direct OPA evaluation for Rego policies
                validation_result = direct_opa_evaluation(plan, self.rego_policy_path)
            else:
                # Use the plan-lint validation method (built-in or OPA)
                validation_result = validate_plan(
                    plan,
                    self.policy,
                    rego_policy=self.rego_policy,
                    use_opa=False,  # Always use built-in validation through plan-lint
                )

            # Format the result
            result = {
                "valid": validation_result.status != Status.ERROR
                and validation_result.risk_score < self.policy.fail_risk_threshold,
                "status": validation_result.status,
                "risk_score": validation_result.risk_score,
                "errors": [
                    {"step": e.step, "code": e.code, "msg": e.msg}
                    for e in validation_result.errors
                ],
                "warnings": [
                    {"step": w.step, "code": w.code, "msg": w.msg}
                    for w in validation_result.warnings
                ],
            }

            return result
        except Exception as e:
            return {
                "valid": False,
                "status": "error",
                "risk_score": 1.0,
                "errors": [{"code": "VALIDATION_ERROR", "msg": str(e)}],
                "warnings": [],
            }

    def _has_valid_structure(self, plan_data: Dict[str, Any]) -> bool:
        """
        Check if the plan has the minimum required structure.

        Args:
            plan_data: The plan dictionary.

        Returns:
            True if valid structure, False otherwise.
        """
        # Minimum requirements: goal and steps array
        if "goal" not in plan_data:
            return False

        if "steps" not in plan_data or not isinstance(plan_data["steps"], list):
            return False

        # Each step needs at least an id, tool, and args
        for step in plan_data["steps"]:
            if not isinstance(step, dict):
                return False

            if "tool" not in step:
                return False

            if "args" not in step or not isinstance(step["args"], dict):
                return False

        return True

    def format_validation_error(self, result: Dict[str, Any]) -> str:
        """
        Format validation errors into a user-friendly string.

        Args:
            result: Validation result from validate_plan_json.

        Returns:
            Formatted error message.
        """
        if result.get("valid", False):
            return "Plan validation passed!"

        lines = ["❌ Plan validation failed:"]

        if result.get("risk_score", 0) >= self.policy.fail_risk_threshold:
            threshold = self.policy.fail_risk_threshold
            lines.append(
                f"- Risk score {result['risk_score']:.2f} exceeds threshold {threshold}"
            )

        for error in result.get("errors", []):
            step = error.get("step")
            step_info = f" (step {step})" if step is not None else ""
            lines.append(f"- {error.get('code')}{step_info}: {error.get('msg')}")

        for warning in result.get("warnings", []):
            step = warning.get("step")
            step_info = f" (step {step})" if step is not None else ""
            lines.append(f"- Warning{step_info}: {warning.get('msg')}")

        # If using Rego but OPA not installed, add an informative message
        if self.is_rego and not self.has_opa:
            lines.append(
                "- Note: OPA is not installed. Used built-in validation instead of Rego."
            )

        return "\n".join(lines)


# Helper function to make it easier to use with YAML policy
def validate_finance_plan(plan_json: str) -> Tuple[bool, str]:
    """
    Validate a financial transaction plan and get formatted results.

    Args:
        plan_json: The plan as a JSON string.

    Returns:
        Tuple of (is_valid, formatted_message)
    """
    validator = PlanValidator()
    result = validator.validate_plan_json(plan_json)
    is_valid = result.get("valid", False)
    message = (
        validator.format_validation_error(result)
        if not is_valid
        else "Plan validation passed!"
    )
    return is_valid, message


# Helper function to make it easier to use with Rego policy
def validate_finance_plan_rego(plan_json: str) -> Tuple[bool, str]:
    """
    Validate a financial transaction plan using Rego policy and get formatted results.

    Args:
        plan_json: The plan as a JSON string.

    Returns:
        Tuple of (is_valid, formatted_message)
    """
    validator = PlanValidator(use_rego=True)
    result = validator.validate_plan_json(plan_json)
    is_valid = result.get("valid", False)

    # Generate appropriate message
    if is_valid:
        message = "Plan validation passed with Rego policy!"
        if not validator.has_opa:
            message = (
                "Plan validation passed! "
                "(Using built-in validation as OPA is not installed)"
            )
    else:
        message = validator.format_validation_error(result)

    return is_valid, message
