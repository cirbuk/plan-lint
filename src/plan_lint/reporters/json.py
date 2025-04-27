"""
JSON reporter for plan-linter.

This module provides functionality for rendering validation results as JSON.
"""

import json
from typing import Dict, Optional, TextIO

from plan_lint.types import ValidationResult


def to_dict(result: ValidationResult) -> Dict:
    """
    Convert a ValidationResult to a dictionary.

    Args:
        result: The validation result to convert.

    Returns:
        Dictionary representation of the result.
    """
    return result.model_dump()


def report(result: ValidationResult, output: Optional[TextIO] = None) -> str:
    """
    Generate a JSON report from a validation result.

    Args:
        result: The validation result to report.
        output: Optional file-like object to write the report to.

    Returns:
        The JSON report as a string.
    """
    report_dict = to_dict(result)
    report_json = json.dumps(report_dict, indent=2)

    if output:
        output.write(report_json)

    return report_json
