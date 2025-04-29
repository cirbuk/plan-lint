# Rules API

This page documents the rule validation functions of Plan-Lint.

## Built-in Rule Functions

Plan-Lint provides several built-in rule functions for validating different aspects of plans.

### `check_tools_allowed`

Check if a step's tool is allowed by the policy.

```python
from plan_lint.core import check_tools_allowed

error = check_tools_allowed(step, allowed_tools, step_idx)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `step` | `PlanStep` | The plan step to check |
| `allowed_tools` | `List[str]` | List of allowed tool names |
| `step_idx` | `int` | Index of the step in the plan |

### Returns

Returns a `PlanError` if the tool is not allowed, `None` otherwise.

### `check_bounds`

Check if a step's arguments are within bounds defined by the policy.

```python
from plan_lint.core import check_bounds

errors = check_bounds(step, bounds, step_idx)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `step` | `PlanStep` | The plan step to check |
| `bounds` | `Dict[str, List[float]]` | Dictionary mapping tool.arg paths to [min, max] bounds |
| `step_idx` | `int` | Index of the step in the plan |

### Returns

Returns a list of `PlanError` for any bounds violations.

### `check_raw_secrets`

Check if a step contains raw secrets or sensitive data.

```python
from plan_lint.core import check_raw_secrets

errors = check_raw_secrets(step, deny_patterns, step_idx)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `step` | `PlanStep` | The plan step to check |
| `deny_patterns` | `List[str]` | List of regex patterns to deny |
| `step_idx` | `int` | Index of the step in the plan |

### Returns

Returns a list of `PlanError` for any detected secrets.

### `detect_cycles`

Detect cycles in the plan's step dependencies.

```python
from plan_lint.core import detect_cycles

error = detect_cycles(plan)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan` | `Plan` | The plan to check |

### Returns

Returns a `PlanError` if a cycle is detected, `None` otherwise.

## Creating Custom Rule Functions

You can create custom rule functions to add your own validation logic:

```python
from typing import List, Dict, Any, Optional
from plan_lint.types import Plan, PlanStep, PlanError, ErrorCode

def check_custom_rule(
    plan: Plan, 
    context: Optional[Dict[str, Any]] = None
) -> List[PlanError]:
    """
    Custom rule to validate some aspect of the plan.
    
    Args:
        plan: The plan to validate
        context: Optional context information
        
    Returns:
        List of errors found during validation
    """
    errors = []
    
    # Example: Check that payment operations have an approval step
    for i, step in enumerate(plan.steps):
        if step.tool.startswith("payments."):
            # Look for an approval step that depends on this payment
            approval_step_exists = False
            for j, other_step in enumerate(plan.steps):
                if (other_step.tool == "approval.request" and 
                    step.id in other_step.depends_on):
                    approval_step_exists = True
                    break
            
            if not approval_step_exists:
                errors.append(
                    PlanError(
                        step=i,
                        code=ErrorCode.CUSTOM,
                        msg=f"Payment operation in step {step.id} requires an approval step"
                    )
                )
    
    return errors
```

## Using Custom Rules

You can use custom rules with the `validate_plan` function:

```python
from plan_lint.core import validate_plan
from my_custom_rules import check_custom_rule

# Load plan and policy
plan = load_plan("plans/customer_refund.json")
policy, rego_policy = load_policy("policies/security.yaml")

# Create custom validators list
custom_validators = [check_custom_rule]

# Validate with custom rules
result = validate_plan(
    plan, 
    policy,
    custom_validators=custom_validators,
    context={"user_role": "admin"}
)
```
