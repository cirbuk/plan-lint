# Loader API

This page documents the loader functions for loading plans, policies, and schemas.

## `load_plan`

Load a plan from a JSON file.

```python
from plan_lint.loader import load_plan

plan = load_plan("path/to/plan.json")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_path` | `str` | Path to a JSON plan file |

### Returns

Returns a `Plan` object.

## `load_policy`

Load a policy from a YAML or Rego file.

```python
from plan_lint.loader import load_policy

policy, rego_policy = load_policy("path/to/policy.yaml")
# or
policy, rego_policy = load_policy("path/to/policy.rego")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_path` | `Optional[str]` | Path to a policy file (YAML or Rego) |

### Returns

Returns a tuple of (`Policy` object, Optional Rego policy string).

## `load_yaml_policy`

Load a policy specifically from a YAML file.

```python
from plan_lint.loader import load_yaml_policy

policy = load_yaml_policy("path/to/policy.yaml")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_path` | `str` | Path to a YAML policy file |

### Returns

Returns a `Policy` object.

## `load_rego_policy`

Load a Rego policy from a file.

```python
from plan_lint.loader import load_rego_policy

rego_policy = load_rego_policy("path/to/policy.rego")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_path` | `str` | Path to a Rego policy file |

### Returns

Returns the Rego policy as a string.

## `load_schema`

Load a JSON schema for plan validation.

```python
from plan_lint.loader import load_schema

schema = load_schema()  # Use default schema
# or
schema = load_schema("path/to/custom/schema.json")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `schema_path` | `Optional[str]` | Path to a JSON schema file (None for default) |

### Returns

Returns the schema as a dictionary.

## Example Usage

```python
from plan_lint.loader import load_plan, load_policy
from plan_lint.core import validate_plan

# Load plan and policy
plan = load_plan("plans/customer_refund.json")
policy, rego_policy = load_policy("policies/security.yaml")

# Validate plan
result = validate_plan(plan, policy)

# For a Rego policy
policy, rego_policy = load_policy("policies/security.rego")
result = validate_plan(plan, policy, rego_policy=rego_policy, use_opa=True)
```
