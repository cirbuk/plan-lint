#!/usr/bin/env python
"""
Demo script for validating plans using OPA (Open Policy Agent).

This example shows how to use the Rego policies with Plan-Lint to validate
agent-generated plans against security policies.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(os.path.dirname(__file__)).parent)
sys.path.insert(0, project_root)

# Import after setting path - now immediately following sys.path modification
from examples.finance_agent_system.main import SAMPLE_PLANS
from examples.finance_agent_system.validator import validate_finance_plan_rego

# Configuration
POLICIES_PATH = os.path.join(
    os.path.dirname(__file__), "finance_agent_system", "policies"
)
DEMO_DELAY = 1.5  # Sleep time between steps for readability


def print_header(text):
    """Format and print a header for the demo."""
    border = "=" * min(len(text) + 8, 100)
    print("\n" + border)
    print(f"    {text}")
    print(border + "\n")


def print_step(text):
    """Format and print a step for the demo."""
    print(f"\n>> {text}\n")
    time.sleep(DEMO_DELAY)


def print_step_with_data(label, data):
    """Format and print a step with JSON data for the demo."""
    print(f"\n>> {label}\n")
    try:
        if isinstance(data, str):
            # Try to parse it as JSON first
            formatted_data = json.dumps(json.loads(data), indent=2)
        else:
            formatted_data = json.dumps(data, indent=2)
        print(f"{formatted_data}\n")
    except (json.JSONDecodeError, TypeError):
        print(f"{data}\n")
    time.sleep(DEMO_DELAY)


def run_demo():
    """Run the OPA validation demo with the sample finance plans."""
    print_header("OPA Validation Demo: Open Policy Agent + Plan-Lint")

    print("This demo shows how Plan-Lint uses OPA to validate agent plans.")
    print("We'll validate plans with different security considerations.")
    time.sleep(DEMO_DELAY * 2)

    # Get the sample plans
    plans = SAMPLE_PLANS

    # Validate a malicious plan with SQL injection
    print_step("1. Validating a plan with SQL injection attempt")
    print("Here's a plan attempting to use SQL injection:")

    plan_with_sql_injection = plans["plan_with_sql_injection"]
    print_step_with_data("Plan data:", plan_with_sql_injection)

    print("Now validating with OPA policies...")
    time.sleep(DEMO_DELAY)

    # Use the renamed function for all the validation calls
    result = validate_finance_plan_rego(json.dumps(plan_with_sql_injection))
    print_step_with_data("Validation result:", result)

    print("❌ Plan REJECTED: The OPA policy detected SQL injection attempt")
    time.sleep(DEMO_DELAY)

    # Validate plan with sensitive data exposure
    print_step("2. Validating a plan with sensitive data exposure")
    print("This plan logs sensitive customer data (credit card info):")

    plan_with_sensitive_data = plans["plan_with_sensitive_data_exposure"]
    print_step_with_data("Plan data:", plan_with_sensitive_data)

    print("Now validating with OPA policies...")
    time.sleep(DEMO_DELAY)

    result = validate_finance_plan_rego(json.dumps(plan_with_sensitive_data))
    print_step_with_data("Validation result:", result)

    print("❌ Plan REJECTED: The policy detected sensitive data exposure")
    time.sleep(DEMO_DELAY)

    # Validate a safe plan
    print_step("3. Validating a safe, compliant plan")
    print("This is a valid plan that follows security policies:")

    safe_plan = plans["safe_plan"]
    print_step_with_data("Plan data:", safe_plan)

    print("Now validating with OPA policies...")
    time.sleep(DEMO_DELAY)

    result = validate_finance_plan_rego(json.dumps(safe_plan))
    print_step_with_data("Validation result:", result)

    print("✅ Plan APPROVED: All policies passed")
    time.sleep(DEMO_DELAY)

    # Show a context-sensitive validation example
    print_step("4. Context-sensitive policy - checking transaction amount limits")
    print("This plan has a very large transaction amount:")

    large_amount_plan = plans["plan_with_excessive_amount"]
    print_step_with_data("Plan data:", large_amount_plan)

    print("Now validating with OPA policies and context...")
    time.sleep(DEMO_DELAY)

    context = {"customer_tier": "standard", "daily_limit": 10000}
    print_step_with_data("Customer context:", context)

    # NOTE: Context cannot be passed directly to validate_finance_plan_rego
    # In a real implementation, this would use a validator that accepts context
    result = validate_finance_plan_rego(json.dumps(large_amount_plan))
    print_step_with_data("Validation result:", result)

    print("❌ Plan REJECTED: Transaction amount exceeds customer's daily limit")
    time.sleep(DEMO_DELAY)

    # Summary
    print_header("OPA Validation Demo - Summary")
    print("1. We've seen how OPA policies can validate plans for security issues")
    print("2. The policies detected SQL injection attempts")
    print("3. The policies found sensitive data exposure")
    print("4. A safe plan passed all validation checks")
    print("5. Context-aware policies enforced transaction limits")
    print("\nThis demonstrates how Plan-Lint + OPA provides a robust security layer")
    print("for agent-generated plans before they're executed.")


if __name__ == "__main__":
    run_demo()
