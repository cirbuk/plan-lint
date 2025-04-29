"""
Command-line interface for plan-linter.

This module provides the main CLI entry point for the tool.
"""

import importlib
import os
import sys
from typing import Callable, Dict, Optional

import typer
from rich.console import Console

from plan_lint import core
from plan_lint.loader import load_plan, load_policy, is_rego_policy_file
from plan_lint.reporters import cli as cli_reporter
from plan_lint.reporters import json as json_reporter
from plan_lint.types import Status, ValidationResult, Policy

# Initialize the CLI app
app = typer.Typer(
    name="plan-lint",
    help="A static analysis toolkit for LLM agent plans",
    add_completion=False,
)

console = Console()


def load_rules() -> Dict[str, Callable]:
    """
    Load all rule modules from the rules directory.

    Returns:
        Dictionary mapping rule names to check_plan functions.
    """
    rules: Dict[str, Callable] = {}
    rules_dir = os.path.join(os.path.dirname(__file__), "rules")

    if not os.path.exists(rules_dir):
        return rules

    for filename in os.listdir(rules_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f"plan_lint.rules.{module_name}")
                if hasattr(module, "check_plan"):
                    rules[module_name] = module.check_plan
            except ImportError:
                console.print(
                    f"[yellow]Warning: Failed to load rule module {module_name}[/]"
                )

    return rules


@app.command(name="")
def lint_plan(
    plan_file: str = typer.Argument(..., help="Path to the plan JSON file"),
    policy_file: Optional[str] = typer.Option(
        None, "--policy", "-p", help="Path to the policy file (YAML or Rego)"
    ),
    policy_type: str = typer.Option(
        "auto",
        "--policy-type",
        "-t",
        help="Policy type: 'yaml', 'rego', or 'auto' (detect automatically)",
    ),
    schema_file: Optional[str] = typer.Option(
        None, "--schema", "-s", help="Path to the JSON schema file"
    ),
    output_format: str = typer.Option(
        "cli", "--format", "-f", help="Output format (cli or json)"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Path to write output (default: stdout)"
    ),
    fail_risk: float = typer.Option(
        0.8, "--fail-risk", "-r", help="Risk score threshold for failure (0-1)"
    ),
    use_opa: bool = typer.Option(
        False, "--opa", help="Use OPA for validation even for YAML policies"
    ),
) -> None:
    """
    Validate a plan against a policy and schema.
    """
    try:
        # Load the plan
        plan = load_plan(plan_file)

        # Determine policy type if auto
        is_rego = False
        if policy_file and policy_type.lower() in ("auto", "rego"):
            if policy_type.lower() == "rego" or is_rego_policy_file(policy_file):
                is_rego = True

        # Load the policy
        policy_obj, rego_policy = load_policy(policy_file)
        policy_obj.fail_risk_threshold = fail_risk

        # Load rules
        rules = load_rules()

        # Validate the plan
        if is_rego or rego_policy or use_opa:
            # Use OPA validation
            base_result = core.validate_plan(
                plan, policy_obj, rego_policy, use_opa=True
            )
        else:
            # Use built-in validation
            base_result = core.validate_plan(plan, policy_obj)

        # Apply additional rules
        all_errors = list(base_result.errors)

        for rule_name, check_plan in rules.items():
            try:
                rule_errors = check_plan(plan, policy_obj)
                all_errors.extend(rule_errors)
            except Exception as e:
                console.print(f"[yellow]Warning: Rule {rule_name} failed: {e}[/]")

        # Calculate final risk score
        risk_score = core.calculate_risk_score(
            all_errors, base_result.warnings, policy_obj.risk_weights
        )

        # Determine final status
        status = Status.PASS
        if all_errors:
            status = Status.ERROR
        elif base_result.warnings:
            status = Status.WARN

        # Override status based on risk threshold
        if risk_score >= policy_obj.fail_risk_threshold:
            status = Status.ERROR

        # Create the final result
        result = ValidationResult(
            status=status,
            risk_score=risk_score,
            errors=all_errors,
            warnings=base_result.warnings,
        )

        # Write the report
        output_stream = open(output_file, "w") if output_file else sys.stdout

        try:
            if output_format.lower() == "json":
                json_reporter.report(result, output_stream)
            else:
                cli_reporter.report(result, output_stream)
        finally:
            if output_file and output_stream:
                output_stream.close()

        # Exit with appropriate code
        if status == Status.ERROR:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    app()
