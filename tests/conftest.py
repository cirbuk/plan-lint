"""
Pytest configuration for plan-linter tests.
"""

import json
import sys
from pathlib import Path

import pytest

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_plan():
    """
    Fixture providing a sample plan for testing.
    """
    return {
        "goal": "Test goal",
        "context": {"user_id": "test-user"},
        "steps": [
            {
                "id": "step-001",
                "tool": "sql.query",
                "args": {"query": "SELECT * FROM users", "can_write": True},
            },
            {
                "id": "step-002",
                "tool": "api.call",
                "args": {"auth_token": "AWS_SECRET_123"},
            },
        ],
        "meta": {"planner": "test-planner", "created_at": "2025-05-15T14:30:00Z"},
    }


@pytest.fixture
def sample_policy():
    """
    Fixture providing a sample policy for testing.
    """
    return {
        "allow_tools": ["sql.query_ro", "api.call"],
        "bounds": {"price.discount.discount_pct": [-40, 0]},
        "deny_tokens_regex": ["AWS_SECRET", "API_KEY"],
        "max_steps": 10,
        "risk_weights": {"tool_deny": 0.4, "raw_secret": 0.5, "loop": 0.3},
        "fail_risk_threshold": 0.8,
    }


@pytest.fixture
def sample_plan_file(tmp_path, sample_plan):
    """
    Fixture providing a temporary file with a sample plan.
    """
    plan_file = tmp_path / "test_plan.json"
    with open(plan_file, "w") as f:
        json.dump(sample_plan, f)
    return plan_file


@pytest.fixture
def sample_policy_file(tmp_path, sample_policy):
    """
    Fixture providing a temporary file with a sample policy.
    """
    policy_file = tmp_path / "test_policy.yaml"
    with open(policy_file, "w") as f:
        f.write("allow_tools:\n")
        for tool in sample_policy["allow_tools"]:
            f.write(f"  - {tool}\n")

        f.write("bounds:\n")
        for key, value in sample_policy["bounds"].items():
            f.write(f"  {key}: {value}\n")

        f.write("deny_tokens_regex:\n")
        for pattern in sample_policy["deny_tokens_regex"]:
            f.write(f'  - "{pattern}"\n')

        f.write(f"max_steps: {sample_policy['max_steps']}\n")

        f.write("risk_weights:\n")
        for key, value in sample_policy["risk_weights"].items():
            f.write(f"  {key}: {value}\n")

        f.write(f"fail_risk_threshold: {sample_policy['fail_risk_threshold']}\n")

    return policy_file
