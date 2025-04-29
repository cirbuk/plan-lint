"""
Loader module for plan-linter.

This module provides functionality for loading plans, schemas, and policies.
"""

import json
import os
from typing import Any, Dict, Optional, Tuple

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


def is_rego_policy_file(filepath: str) -> bool:
    """
    Check if a file appears to be a Rego policy file based on its extension or content.

    Args:
        filepath: Path to the file to check

    Returns:
        True if the file is likely a Rego policy, False otherwise
    """
    # Check file extension
    if filepath.endswith(".rego"):
        return True

    # Check content for Rego syntax
    try:
        with open(filepath, "r") as f:
            content = f.read(1000)  # Read first 1000 chars to check
            return "package" in content and any(
                rule in content for rule in ["default ", " = ", "{", "input."]
            )
    except Exception:
        return False

    return False


def load_policy(policy_path: Optional[str] = None) -> Tuple[Policy, Optional[str]]:
    """
    Load a policy file.

    Args:
        policy_path: Path to policy file (YAML or Rego format)

    Returns:
        A tuple of (Policy object, Optional Rego policy string)
        For YAML policies, the Policy object is populated and Rego string is None
        For Rego policies, a default Policy object is returned with the Rego
        content as a string
    """
    if policy_path is None:
        return Policy(), None

    try:
        # Check if this is a Rego policy file
        if is_rego_policy_file(policy_path):
            # Load the Rego policy as a string
            with open(policy_path, "r") as f:
                rego_content = f.read()

            # Return a default Policy object and the Rego content
            return Policy(), rego_content

        # Otherwise, treat as YAML policy
        with open(policy_path, "r") as f:
            policy_data = yaml.safe_load(f)

        if policy_data is None:
            return Policy(), None

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

        return Policy.model_validate(policy_data), None
    except Exception as e:
        raise ValueError(f"Failed to load policy from {policy_path}: {e}") from e


def load_yaml_policy(policy_path: str) -> Policy:
    """
    Load a policy specifically from a YAML file.

    Args:
        policy_path: Path to a YAML policy file.

    Returns:
        The policy as a Policy object.
    """
    policy, _ = load_policy(policy_path)
    return policy


def load_rego_policy(policy_path: str) -> str:
    """
    Load a Rego policy from a file.

    Args:
        policy_path: Path to a Rego policy file.

    Returns:
        The Rego policy as a string.
    """
    if not is_rego_policy_file(policy_path):
        raise ValueError(
            f"File does not appear to be a valid Rego policy: {policy_path}"
        )

    with open(policy_path, "r") as f:
        return f.read()
