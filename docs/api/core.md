# Core API

This page documents the core functions of Plan-Lint.

## `validate_plan`

The main function for validating agent plans.

```python
from plan_lint.core import validate_plan

result = validate_plan(
    plan,
    policy,
    rego_policy=None,
    use_opa=False
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan` | `Plan` | The agent plan to validate |
| `policy` | `Policy` | Policy object containing validation rules |
| `rego_policy` | `Optional[str]` | Optional Rego policy as a string |
| `use_opa` | `bool` | Whether to use OPA for validation (defaults to False) |

### Returns

Returns a `ValidationResult` object containing:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | `Status` | Status of validation (PASS, WARN, ERROR) |
| `risk_score` | `float` | Risk score between 0.0 and 1.0 |
| `errors` | `List[PlanError]` | List of validation errors |
| `warnings` | `List[PlanWarning]` | List of validation warnings |

## `calculate_risk_score`

Calculate a risk score for the plan based on errors and warnings.

```python
from plan_lint.core import calculate_risk_score

risk_score = calculate_risk_score(errors, warnings, risk_weights)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `errors` | `List[PlanError]` | List of errors found during validation |
| `warnings` | `List[PlanWarning]` | List of warnings found during validation |
| `risk_weights` | `Dict[str, float]` | Dictionary mapping error/warning types to weights |

### Returns

Returns a float between 0.0 and 1.0 representing the risk score.

## Example Usage

```python
from plan_lint.core import validate_plan, calculate_risk_score
from plan_lint.loader import load_plan, load_policy
from plan_lint.types import Status, PlanError, ErrorCode

# Basic validation example
plan = load_plan("plans/customer_refund.json")
policy, rego_policy = load_policy("policies/security.yaml")

# Validate plan
result = validate_plan(plan, policy)

# Check results
if result.status == Status.PASS:
    print("Plan is valid!")
else:
    print(f"Plan validation failed with risk score: {result.risk_score}")
    for error in result.errors:
        print(f"Step {error.step}: {error.msg} ({error.code})")

# Manual risk score calculation
errors = [
    PlanError(step=1, code=ErrorCode.RAW_SECRET, msg="Sensitive data detected"),
    PlanError(step=2, code=ErrorCode.BOUND_VIOLATION, msg="Amount exceeds maximum")
]
warnings = []
risk_weights = {
    "raw_secret": 0.7,
    "bound_violation": 0.4
}

risk_score = calculate_risk_score(errors, warnings, risk_weights)
print(f"Risk score: {risk_score}")
```
