"""
Tests for the Open Policy Agent (OPA) integration module.
"""

import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from plan_lint.opa import (
    evaluate_with_opa,
    is_opa_installed,
    is_rego_policy,
    load_rego_policy_file,
    policy_to_rego,
)
from plan_lint.types import ErrorCode, Plan, Policy, Status

# Sample plan data for testing
SAMPLE_PLAN = Plan(
    goal="test goal",
    context={},
    steps=[
        {
            "id": "step1",
            "tool": "allowed_tool",
            "args": {"arg1": "value1"},
            "on_fail": "abort",
        }
    ],
    meta={},
)

SAMPLE_PLAN_WITH_DISALLOWED_TOOL = Plan(
    goal="test goal",
    context={},
    steps=[
        {
            "id": "step1",
            "tool": "disallowed_tool",
            "args": {"arg1": "value1"},
            "on_fail": "abort",
        }
    ],
    meta={},
)

SAMPLE_POLICY = Policy(
    allow_tools=["allowed_tool"],
    max_steps=10,
    deny_tokens_regex=["secret", "password"],
    fail_risk_threshold=0.5,
)


class TestOPAModule(unittest.TestCase):
    """Test case for the OPA module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create sample policy file
        self.policy_path = os.path.join(self.temp_dir.name, "test_policy.rego")
        with open(self.policy_path, "w") as f:
            f.write(
                'package planlint\ndefault allow = false\nallow { input.steps[_].tool == "allowed_tool" }'
            )

    def test_policy_to_rego_conversion(self):
        """Test conversion of a Policy object to Rego code."""
        rego_policy = policy_to_rego(SAMPLE_POLICY)

        # Basic checks
        self.assertIn("package planlint", rego_policy)
        self.assertIn("default allow = false", rego_policy)
        self.assertIn("allowed_tools = [", rego_policy)
        self.assertIn('"allowed_tool"', rego_policy)

        # Functional checks (would parse and compile correctly)
        self.assertIn("all_tools_allowed {", rego_policy)
        self.assertIn("steps_within_limit {", rego_policy)
        self.assertIn("violations[", rego_policy)

    @patch("subprocess.run")
    def test_is_opa_installed(self, mock_run):
        """Test detecting if OPA is installed."""
        # Test when OPA is installed
        mock_run.return_value = MagicMock()
        self.assertTrue(is_opa_installed())

        # Test when OPA is not installed
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(is_opa_installed())

    def test_is_rego_policy(self):
        """Test detection of Rego policy content."""
        valid_policy = (
            'package planlint\ndefault allow = false\nallow { input.goal == "valid" }'
        )
        invalid_policy = '{"policy": "not rego"}'

        self.assertTrue(is_rego_policy(valid_policy))
        self.assertFalse(is_rego_policy(invalid_policy))

    def test_load_rego_policy_file(self):
        """Test loading Rego policy from file."""
        # Test loading valid file
        content = load_rego_policy_file(self.policy_path)
        self.assertIn("package planlint", content)

        # Test with nonexistent file
        with self.assertRaises(FileNotFoundError):
            load_rego_policy_file("/nonexistent/path/policy.rego")

    @patch("subprocess.run")
    def test_evaluate_with_opa_success(self, mock_run):
        """Test successful OPA evaluation."""
        # Mock successful OPA evaluation
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(
            {
                "result": [
                    {"expressions": [{"value": {"allow": True, "violations": []}}]}
                ]
            }
        )
        mock_run.return_value = mock_process

        result = evaluate_with_opa(SAMPLE_PLAN, SAMPLE_POLICY)
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(len(result.errors), 0)

    @patch("subprocess.run")
    def test_evaluate_with_opa_violations(self, mock_run):
        """Test OPA evaluation with violations."""
        # Mock OPA evaluation with violations
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(
            {
                "result": [
                    {
                        "expressions": [
                            {
                                "value": {
                                    "allow": False,
                                    "violations": [
                                        {
                                            "step": 0,
                                            "code": "TOOL_DENY",
                                            "msg": "Tool 'disallowed_tool' is not allowed by policy",
                                        }
                                    ],
                                }
                            }
                        ]
                    }
                ]
            }
        )
        mock_run.return_value = mock_process

        result = evaluate_with_opa(SAMPLE_PLAN_WITH_DISALLOWED_TOOL, SAMPLE_POLICY)
        self.assertEqual(result.status, Status.ERROR)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, ErrorCode.TOOL_DENY)

    @patch("subprocess.run")
    def test_evaluate_with_opa_failure(self, mock_run):
        """Test handling of OPA evaluation failures."""
        # Mock OPA process failure
        mock_run.side_effect = subprocess.SubprocessError("OPA failed")

        result = evaluate_with_opa(SAMPLE_PLAN, SAMPLE_POLICY)
        self.assertEqual(result.status, Status.ERROR)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, ErrorCode.SCHEMA_INVALID)


if __name__ == "__main__":
    unittest.main()
