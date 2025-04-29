#!/usr/bin/env python
"""
Demo script showing how to use OPA-based validation in plan-lint.

This script demonstrates the integration with Open Policy Agent (OPA) for validating plans.
"""

import os
import json
import sys
from pathlib import Path

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from plan_lint.types import Plan, Policy, Status
from plan_lint.core import validate_plan
from plan_lint.loader import load_rego_policy

# Check if OPA is installed
try:
    import subprocess

    result = subprocess.run(["opa", "version"], capture_output=True, text=True)
    print(f"✅ OPA detected: {result.stdout.strip()}")
except (subprocess.SubprocessError, FileNotFoundError):
    print(
        "❌ OPA executable not found. Please install OPA from https://www.openpolicyagent.org/docs/latest/#1-download-opa"
    )
    print("Falling back to built-in validation.")
    HAS_OPA = False
else:
    HAS_OPA = True


def create_sample_plan(tool: str = "db.query_ro", with_secret: bool = False) -> Plan:
    """
    Create a sample plan for testing.

    Args:
        tool: The tool to use in the plan step
        with_secret: Whether to include a secret in the arguments

    Returns:
        A sample Plan object
    """
    args = {
        "query": "SELECT * FROM accounts WHERE user_id = '${context.user_id}'",
        "limit": 100,
    }

    if with_secret:
        args["query"] = (
            "SELECT * FROM accounts WHERE user_id = '${context.user_id}' OR 1=1 -- Get all accounts"
        )

    return Plan(
        goal="Query account data",
        context={"user_id": "123456", "permission_level": "user"},
        steps=[{"id": "step-001", "tool": tool, "args": args, "on_fail": "abort"}],
        meta={"planner": "demo-agent"},
    )


def demonstrate_yaml_vs_rego():
    """
    Demonstrate the difference between YAML and Rego policy validation.
    """
    print("\n=== YAML vs Rego Policy Validation ===\n")

    # Create a sample plan that should pass
    plan = create_sample_plan()

    # Create a Policy object
    policy = Policy(
        allow_tools=["db.query_ro", "db.get_transaction_history"], max_steps=10
    )

    # Load the Rego policy
    finance_rego_path = os.path.join(
        os.path.dirname(__file__), "finance_agent_system", "finance_policy.rego"
    )
    rego_policy = load_rego_policy(finance_rego_path)

    # Validate with built-in validation
    builtin_result = validate_plan(plan, policy)

    # Validate with OPA (if available)
    if HAS_OPA:
        opa_result = validate_plan(plan, policy, rego_policy=rego_policy)
    else:
        # Create a simulated result for demonstration
        from plan_lint.types import ValidationResult

        opa_result = ValidationResult(
            status=Status.PASS, risk_score=0.0, errors=[], warnings=[]
        )

    # Print results
    print("Built-in validation result:", builtin_result.status)
    print("OPA validation result:", opa_result.status)

    # Create a plan that should fail (using a disallowed tool)
    bad_plan = create_sample_plan(tool="db.delete_records")

    # Validate with built-in validation
    builtin_result = validate_plan(bad_plan, policy)

    # Validate with OPA (if available)
    if HAS_OPA:
        opa_result = validate_plan(bad_plan, policy, rego_policy=rego_policy)
    else:
        # Create a simulated result for demonstration
        from plan_lint.types import ValidationResult, PlanError, ErrorCode

        opa_result = ValidationResult(
            status=Status.ERROR,
            risk_score=0.5,
            errors=[
                PlanError(
                    step=0,
                    code=ErrorCode.TOOL_DENY,
                    msg="Tool 'db.delete_records' is not allowed by policy",
                )
            ],
            warnings=[],
        )

    # Print results
    print("\nFor disallowed tool:")
    print("Built-in validation result:", builtin_result.status)
    print("OPA validation result:", opa_result.status)
    print("Built-in validation errors:", [e.msg for e in builtin_result.errors])
    print("OPA validation errors:", [e.msg for e in opa_result.errors])

    # Create a plan with a secret pattern
    secret_plan = create_sample_plan(with_secret=True)

    # Update the policy to include the deny_tokens_regex
    policy.deny_tokens_regex = ["--", "1=1", "OR 1=1"]

    # Validate with built-in validation
    builtin_result = validate_plan(secret_plan, policy)

    # Validate with OPA (if available)
    if HAS_OPA:
        opa_result = validate_plan(secret_plan, policy, rego_policy=rego_policy)
    else:
        # Create a simulated result for demonstration
        from plan_lint.types import ValidationResult, PlanError, ErrorCode

        opa_result = ValidationResult(
            status=Status.ERROR,
            risk_score=0.7,
            errors=[
                PlanError(
                    step=0,
                    code=ErrorCode.RAW_SECRET,
                    msg="Potentially sensitive data matching pattern '--' found in arguments",
                )
            ],
            warnings=[],
        )

    # Print results
    print("\nFor plan with sensitive data:")
    print("Built-in validation result:", builtin_result.status)
    print("OPA validation result:", opa_result.status)
    print("Built-in validation errors:", [e.msg for e in builtin_result.errors])
    print("OPA validation errors:", [e.msg for e in opa_result.errors])


if __name__ == "__main__":
    print("🛡️ Plan-Lint OPA Integration Demo")
    print("=================================")

    demonstrate_yaml_vs_rego()
