#!/usr/bin/env python
"""
Example script demonstrating how to use Plan-Lint to validate agent plans.

This script shows basic validation functionality with built-in policies.
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(os.path.dirname(__file__)).parent)
sys.path.insert(0, project_root)

# Import after setting path - now immediately following sys.path modification
from plan_lint.core import validate_plan
from plan_lint.types import Plan, Policy


def create_sample_plan(include_sql_injection=False):
    """Create a sample plan for validation demonstration.

    Args:
        include_sql_injection: Whether to include a SQL injection attempt

    Returns:
        A Plan object for testing
    """
    # Create a basic query
    query = "SELECT * FROM users WHERE id = $1"

    # Optionally add SQL injection
    if include_sql_injection:
        query = "SELECT * FROM users WHERE id = '" + "${user_id}' OR '1'='1"

    # Create the plan with appropriate steps
    return Plan(
        goal="Fetch user data",
        context={"user_id": "12345"},
        steps=[
            {
                "id": "step1",
                "tool": "database.query",
                "args": {"query": query, "parameters": ["${context.user_id}"]},
                "on_fail": "abort",
            }
        ],
        meta={"author": "plan-lint-demo"},
    )


def main():
    """Run the validation demonstration."""
    # Create a safe plan
    safe_plan = create_sample_plan(include_sql_injection=False)
    print("=== Safe Plan ===")
    print(json.dumps(safe_plan.model_dump(), indent=2))

    # Create a policy
    policy = Policy(
        allow_tools=["database.query", "http.get"],
        max_steps=5,
        deny_tokens_regex=["OR '1'='1", "--", "DROP TABLE"],
    )
    print("\n=== Policy ===")
    print(json.dumps(policy.model_dump(), indent=2))

    # Validate the safe plan
    print("\n=== Validating Safe Plan ===")
    result = validate_plan(safe_plan, policy)
    print(f"Status: {result.status}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")

    # Create a malicious plan with SQL injection
    malicious_plan = create_sample_plan(include_sql_injection=True)
    print("\n=== Malicious Plan (with SQL Injection) ===")
    print(json.dumps(malicious_plan.model_dump(), indent=2))

    # Validate the malicious plan
    print("\n=== Validating Malicious Plan ===")
    result = validate_plan(malicious_plan, policy)
    print(f"Status: {result.status}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Errors: {len(result.errors)}")

    # Print detailed errors
    if result.errors:
        print("\nDetailed Errors:")
        for error in result.errors:
            print(f"  - Step {error.step}: {error.code} - {error.msg}")


if __name__ == "__main__":
    main()
