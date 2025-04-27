"""
CLI reporter for plan-linter.

This module provides functionality for rendering validation results as CLI output.
"""

import sys
from typing import TextIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from plan_lint.types import Status, ValidationResult


def report(result: ValidationResult, output: TextIO = sys.stdout) -> None:
    """
    Generate a CLI report from a validation result.

    Args:
        result: The validation result to report.
        output: Optional file-like object to write the report to.
    """
    console = Console(file=output)

    # Create header
    status_color = {
        Status.PASS: "green",
        Status.WARN: "yellow",
        Status.ERROR: "red",
    }.get(result.status, "white")

    status_text = Text(f"Status: {result.status.upper()}", style=status_color)
    risk_text = Text(f"Risk score: {result.risk_score:.2f}", style=status_color)

    console.print(
        Panel(
            f"{status_text}\n{risk_text}",
            title="Plan Validation Result",
            border_style=status_color,
        )
    )

    # Show errors if any
    if result.errors:
        errors_table = Table(title="Errors", border_style="red")
        errors_table.add_column("Step", style="cyan")
        errors_table.add_column("Code", style="magenta")
        errors_table.add_column("Message")

        for error in result.errors:
            step = str(error.step) if error.step is not None else "-"
            errors_table.add_row(step, str(error.code), error.msg)

        console.print(errors_table)

    # Show warnings if any
    if result.warnings:
        warnings_table = Table(title="Warnings", border_style="yellow")
        warnings_table.add_column("Step", style="cyan")
        warnings_table.add_column("Code", style="magenta")
        warnings_table.add_column("Message")

        for warning in result.warnings:
            step = str(warning.step) if warning.step is not None else "-"
            warnings_table.add_row(step, warning.code, warning.msg)

        console.print(warnings_table)

    # Print summary
    error_count = len(result.errors)
    warning_count = len(result.warnings)

    summary = []
    if error_count > 0:
        summary.append(f"{error_count} error(s)")
    if warning_count > 0:
        summary.append(f"{warning_count} warning(s)")

    if summary:
        console.print(f"Found {', '.join(summary)}")
    else:
        console.print("Plan validation passed with no issues", style="green")
