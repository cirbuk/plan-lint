"""
Tests for the OPA integration module.
"""

import json
import os
import unittest
from unittest import mock
from typing import Dict, Any

import pytest

from plan_lint.types import Plan, Policy, Status
from plan_lint.opa import policy_to_rego, is_rego_policy, OPAError


class TestOPAIntegration:
    """Tests for OPA integration."""

    def test_policy_to_rego_conversion(self):
        """Test converting a YAML policy to Rego."""
        # Create a simple policy
        policy = Policy(
            allow_tools=["tool1", "tool2"],
            bounds={"tool1.arg1": [0, 100]},
            deny_tokens_regex=["SECRET", "PASSWORD"],
            max_steps=5,
        )

        # Convert to Rego
        rego = policy_to_rego(policy)

        # Check that the Rego policy contains expected elements
        assert "package planlint" in rego
        assert 'allowed_tools = ["tool1", "tool2"]' in rego
        assert "tool1.arg1" in rego
        assert "0" in rego and "100" in rego
        assert 'sensitive_patterns = ["SECRET", "PASSWORD"]' in rego
        assert "count(input.steps) <= 5" in rego

    def test_is_rego_policy(self):
        """Test detection of Rego policies."""
        # Valid Rego policy
        rego_policy = """
        package planlint

        default allow = false

        allow {
            input.user == "admin"
        }
        """
        assert is_rego_policy(rego_policy) is True

        # Not a Rego policy
        not_rego = """
        {
            "key": "value"
        }
        """
        assert is_rego_policy(not_rego) is False

    @mock.patch("plan_lint.opa.subprocess.run")
    def test_evaluate_with_opa_success(self, mock_run):
        """Test successful evaluation with OPA."""
        # Skip if OPA binary is not available
        pytest.importorskip("plan_lint.opa")

        # Create a Plan and Policy for testing
        plan = Plan(
            goal="Test plan",
            steps=[
                {
                    "id": "step-001",
                    "tool": "allowed_tool",
                    "args": {"param1": "value1"},
                    "on_fail": "abort",
                }
            ],
        )

        policy = Policy(
            allow_tools=["allowed_tool"],
            max_steps=10,
        )

        # Mock subprocess.run to simulate OPA evaluation result
        mock_process = mock.Mock()
        mock_process.stdout = json.dumps(
            {
                "result": [
                    {"expressions": [{"value": True}]},  # allow = true
                    {"expressions": [{"value": []}]},  # No violations
                ]
            }
        )
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Import OPA module locally to allow mocking
        from plan_lint.opa import evaluate_with_opa

        # Run the evaluation
        result = evaluate_with_opa(plan, policy)

        # Check results
        assert result.status == Status.PASS
        assert result.risk_score == 0.0
        assert len(result.errors) == 0

    @mock.patch("plan_lint.opa.subprocess.run")
    def test_evaluate_with_opa_violation(self, mock_run):
        """Test OPA evaluation with policy violations."""
        # Skip if OPA binary is not available
        pytest.importorskip("plan_lint.opa")

        # Create a Plan and Policy for testing
        plan = Plan(
            goal="Test plan",
            steps=[
                {
                    "id": "step-001",
                    "tool": "disallowed_tool",
                    "args": {"param1": "value1"},
                    "on_fail": "abort",
                }
            ],
        )

        policy = Policy(
            allow_tools=["allowed_tool"], max_steps=10, risk_weights={"tool_deny": 0.5}
        )

        # Mock subprocess.run to simulate OPA evaluation result
        mock_process = mock.Mock()
        mock_process.stdout = json.dumps(
            {
                "result": [
                    {"expressions": [{"value": False}]},  # allow = false
                    {
                        "expressions": [
                            {
                                "value": [
                                    {
                                        "step": 0,
                                        "code": "TOOL_DENY",
                                        "msg": "Tool 'disallowed_tool' is not allowed by policy",
                                    }
                                ]
                            }
                        ]
                    },  # Violations
                ]
            }
        )
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Import OPA module locally to allow mocking
        from plan_lint.opa import evaluate_with_opa

        # Run the evaluation
        result = evaluate_with_opa(plan, policy)

        # Check results
        assert result.status == Status.ERROR
        assert result.risk_score == 0.5
        assert len(result.errors) == 1
        assert result.errors[0].code == "TOOL_DENY"

    @mock.patch("plan_lint.opa.subprocess.run")
    def test_opa_executable_not_found(self, mock_run):
        """Test handling when OPA executable is not found."""
        # Skip if OPA binary is not available
        pytest.importorskip("plan_lint.opa")

        # Create a Plan and Policy for testing
        plan = Plan(
            goal="Test plan",
            steps=[
                {
                    "id": "step-001",
                    "tool": "some_tool",
                    "args": {"param1": "value1"},
                    "on_fail": "abort",
                }
            ],
        )

        policy = Policy()

        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'opa'")

        # Import OPA module locally to allow mocking
        from plan_lint.opa import evaluate_with_opa

        # Check that OPAError is raised
        with pytest.raises(OPAError, match="OPA executable not found"):
            evaluate_with_opa(plan, policy)


# These tests are run conditionally if OPA is installed
@pytest.mark.skipif(
    os.system("which opa > /dev/null 2>&1") != 0,
    reason="OPA executable not found in PATH",
)
class TestOPAWithExecutable:
    """Tests that require the actual OPA executable."""

    def test_end_to_end_opa_validation(self):
        """Test end-to-end OPA validation with a real policy and plan."""
        from plan_lint.core import validate_plan

        # Create a simple plan that should pass
        plan = Plan(
            goal="Test plan",
            steps=[
                {
                    "id": "step-001",
                    "tool": "allowed_tool",
                    "args": {"param1": "value1"},
                    "on_fail": "abort",
                }
            ],
        )

        # Create a policy
        policy = Policy(
            allow_tools=["allowed_tool", "another_tool"],
            max_steps=10,
        )

        # Test with OPA validation
        result = validate_plan(plan, policy, use_opa=True)

        # Should pass
        assert result.status == Status.PASS
        assert len(result.errors) == 0

        # Now test with a plan that should fail
        bad_plan = Plan(
            goal="Test plan",
            steps=[
                {
                    "id": "step-001",
                    "tool": "disallowed_tool",
                    "args": {"param1": "value1"},
                    "on_fail": "abort",
                }
            ],
        )

        # Test with OPA validation
        result = validate_plan(bad_plan, policy, use_opa=True)

        # Should fail
        assert result.status == Status.ERROR
        assert len(result.errors) > 0
        assert any(error.code == "TOOL_DENY" for error in result.errors)
