#!/usr/bin/env python
"""
Test script for OPA integration with the Finance Agent System.

This script tests whether OPA is correctly set up and can evaluate the Rego policy
against a sample plan.
"""

import json
import os
import subprocess
import sys
import tempfile

# Add the project root to the Python path if needed
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Try import from the finance agent system
try:
    from validator import is_opa_installed, validate_finance_plan_rego
except ImportError:
    print("Error: Cannot import from validator.py")
    sys.exit(1)


def check_opa_installation():
    """Check if OPA is installed and available."""
    if is_opa_installed():
        print("✅ OPA is installed and available")

        # Run version check to get more information
        try:
            result = subprocess.run(
                ["opa", "version"], check=True, capture_output=True, text=True
            )
            print(f"OPA version: {result.stdout.strip()}")
        except subprocess.SubprocessError as e:
            print(f"⚠️ OPA version check failed: {e}")
    else:
        print("❌ OPA is not installed or not in PATH")
        print(
            "Please install OPA from https://www.openpolicyagent.org/docs/latest/#1-download-opa"
        )
        print("Falling back to built-in validation")


def test_direct_opa_evaluation(plan_json, policy_path):
    """Test OPA evaluation directly without going through plan-lint."""
    print("\n🔍 Testing direct OPA evaluation...")

    # Create temporary files for policy and input
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as input_file:
        input_file.write(plan_json)
        input_path = input_file.name

    try:
        # Run OPA evaluation with a combined query
        cmd = [
            "opa",
            "eval",
            "-d",
            policy_path,
            "-i",
            input_path,
            "data.planlint",  # Request the entire planlint package data
        ]

        print(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print("OPA evaluation succeeded:")
        print(result.stdout)

        # Try to parse the JSON result
        try:
            import json

            data = json.loads(result.stdout)

            # Extract the values we care about
            if "result" in data and len(data["result"]) > 0:
                result_data = data["result"][0]["expressions"][0]["value"]

                allow = result_data.get("allow", False)
                violations = result_data.get("violations", [])
                risk_score = result_data.get("risk_score", 0.0)

                print("\nExtracted data:")
                print(f"- allow: {allow}")
                print(f"- risk_score: {risk_score}")
                print(f"- violations count: {len(violations)}")
                if violations:
                    print(f"- first violation: {violations[0]}")

        except Exception as e:
            print(f"Error parsing JSON result: {e}")

    except subprocess.SubprocessError as e:
        print(f"❌ OPA evaluation failed: {e}")
        if hasattr(e, "stdout"):
            print(f"Command output (stdout): {e.stdout}")
        if hasattr(e, "stderr"):
            print(f"Command output (stderr): {e.stderr}")
    finally:
        # Clean up temporary file
        if os.path.exists(input_path):
            os.unlink(input_path)


def test_validator_integration(plan_json):
    """Test OPA integration through the validator."""
    print("\n🔍 Testing validator integration with OPA...")

    is_valid, message = validate_finance_plan_rego(plan_json)

    print(f"Plan validation {'succeeded' if is_valid else 'failed'}")
    print(f"Message: {message}")


def main():
    """Main function."""
    print("=== OPA Integration Test for Finance Agent System ===")

    # Check if OPA is installed
    check_opa_installation()

    # Get the policy path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    policy_path = os.path.join(current_dir, "finance_policy.rego")

    if not os.path.exists(policy_path):
        print(f"❌ Policy file not found: {policy_path}")
        sys.exit(1)

    print(f"Using policy file: {policy_path}")

    # Create a simple plan for testing
    plan = {
        "goal": "Transfer $100 from checking account to savings account",
        "context": {
            "user_id": "usr_123456",
            "user_email": "user@example.com",
            "request_id": "req-abcdef",
            "session_id": "sess-123456",
            "timestamp": "2025-04-29T00:00:00",
            "auth_level": "verified",
        },
        "steps": [
            {
                "id": "step-001",
                "tool": "db.get_account_details",
                "args": {"user_id": "usr_123456", "account_type": "checking"},
                "on_fail": "abort",
            },
            {
                "id": "step-002",
                "tool": "payments.transfer",
                "args": {
                    "from_account": "1234567890",
                    "to_account": "0987654321",
                    "amount": 100.0,
                    "description": "Transfer to savings",
                },
                "on_fail": "abort",
            },
        ],
        "meta": {"planner": "TestPlanner", "created_at": "2025-04-29T00:00:00"},
    }

    plan_json = json.dumps(plan, indent=2)

    # Test direct OPA evaluation
    test_direct_opa_evaluation(plan_json, policy_path)

    # Test validator integration
    test_validator_integration(plan_json)


if __name__ == "__main__":
    main()
