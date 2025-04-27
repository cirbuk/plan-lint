"""
Loader module for plan-linter.

This module provides functionality for loading plans, schemas, and policies.
"""

import json
import os
from typing import Any, Dict, Optional

import jsonschema
import yaml

from plan_lint.types import Plan, Policy


def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a JSON schema from a file or use the default schema.

    Args:
        schema_path: Path to a JSON schema file. If None, use the default schema.

    Returns:
        The schema as a dictionary.
    """
    if schema_path is None:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(module_dir, "schemas", "plan.schema.json")

    with open(schema_path, "r") as f:
        return json.load(f)  # type: ignore[no-any-return]


def load_plan(plan_path: str) -> Plan:
    """
    Load a plan from a JSON file.

    Args:
        plan_path: Path to a JSON plan file.

    Returns:
        The plan as a Plan object.
    """
    with open(plan_path, "r") as f:
        plan_data = json.load(f)

    # Validate against schema
    schema = load_schema()
    try:
        jsonschema.validate(instance=plan_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Plan validation failed: {e}") from e

    return Plan.model_validate(plan_data)


def load_policy(policy_path: Optional[str] = None) -> Policy:
    """
    Load a policy from a YAML file.

    Args:
        policy_path: Path to a YAML policy file.

    Returns:
        The policy as a Policy object.
    """
    if policy_path is None:
        return Policy()

    try:
        with open(policy_path, "r") as f:
            policy_data = yaml.safe_load(f)

        if policy_data is None:
            return Policy()

        # Process the bounds to ensure they are proper lists of numbers
        if "bounds" in policy_data and policy_data["bounds"]:
            for key, value in policy_data["bounds"].items():
                if not isinstance(value, list):
                    # Try to convert to a list if possible
                    try:
                        policy_data["bounds"][key] = list(value)
                    except (TypeError, ValueError) as err:
                        raise ValueError(
                            f"Invalid bounds format for {key}: {value}"
                        ) from err

        return Policy.model_validate(policy_data)
    except Exception as e:
        raise ValueError(f"Failed to load policy from {policy_path}: {e}") from e
