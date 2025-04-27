"""
Tests for the CLI module.
"""

import json

import pytest
from typer.testing import CliRunner

from plan_lint.cli import app


@pytest.fixture
def runner():
    """Fixture for creating a CLI runner."""
    return CliRunner()


def test_cli_with_valid_plan(runner, sample_plan_file, sample_policy_file):
    """Test CLI with a valid plan."""
    result = runner.invoke(
        app, [str(sample_plan_file), "--policy", str(sample_policy_file)]
    )

    # Should fail due to policy violation
    assert result.exit_code == 1


def test_cli_json_output(runner, sample_plan_file, sample_policy_file, tmp_path):
    """Test CLI with JSON output."""
    output_file = tmp_path / "output.json"

    result = runner.invoke(
        app,
        [
            str(sample_plan_file),
            "--policy",
            str(sample_policy_file),
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )

    # Should fail due to policy violation
    assert result.exit_code == 1

    # Check output file
    assert output_file.exists()

    with open(output_file, "r") as f:
        output_data = json.load(f)

    assert "status" in output_data
    assert output_data["status"] == "error"
    assert "risk_score" in output_data
    assert "errors" in output_data
