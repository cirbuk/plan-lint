# API Reference

The API Reference documentation has moved to the [API Reference](/api/) section of the documentation.

Please see the following pages for detailed API information:

- [API Overview](/api/)
- [Core API](/api/core/)
- [Types API](/api/types/)
- [Loader API](/api/loader/)
- [Rules API](/api/rules/)
- [Validator API](/api/validator/)

## Core Functions

### `validate_plan`

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

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan` | `Plan` | The agent plan to validate |
| `policy` | `Policy` | Policy object containing validation rules |
| `rego_policy` | `Optional[str]` | Optional Rego policy as a string |
| `use_opa` | `bool` | Whether to use OPA for validation (defaults to False) |

#### Returns

Returns a `ValidationResult` object containing:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | `Status` | Status of validation (PASS, WARN, ERROR) |
| `risk_score` | `float` | Risk score between 0.0 and 1.0 |
| `errors` | `List[PlanError]` | List of validation errors |
| `warnings` | `List[PlanWarning]` | List of validation warnings |

## Utility Functions

### `load_plan`

Load a plan from a JSON file.

```python
from plan_lint.loader import load_plan

plan = load_plan("path/to/plan.json")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_path` | `str` | Path to a JSON plan file |

#### Returns

Returns a `Plan` object.

### `load_policy`

Load a policy from a YAML or Rego file.

```python
from plan_lint.loader import load_policy

policy, rego_policy = load_policy("path/to/policy.yaml")
# or
policy, rego_policy = load_policy("path/to/policy.rego")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_path` | `Optional[str]` | Path to a policy file (YAML or Rego) |

#### Returns

Returns a tuple of (`Policy` object, Optional Rego policy string).

### `load_yaml_policy`

Load a policy specifically from a YAML file.

```python
from plan_lint.loader import load_yaml_policy

policy = load_yaml_policy("path/to/policy.yaml")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_path` | `str` | Path to a YAML policy file |

#### Returns

Returns a `Policy` object.

### `load_rego_policy`

Load a Rego policy from a file.

```python
from plan_lint.loader import load_rego_policy

rego_policy = load_rego_policy("path/to/policy.rego")
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_path` | `str` | Path to a Rego policy file |

#### Returns

Returns the Rego policy as a string.

## Data Types

### `Plan`

Represents an agent plan to be validated.

```python
from plan_lint.types import Plan, PlanStep

plan = Plan(
    goal="Process customer refund",
    steps=[
        PlanStep(
            id="step1",
            tool="db.query",
            args={"query": "SELECT * FROM users"}
        ),
        PlanStep(
            id="step2",
            tool="notify.email",
            args={"to": "user@example.com", "body": "Your refund is processed"}
        )
    ],
    context={"user_id": "123"}
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `goal` | `str` | The goal or purpose of the plan |
| `steps` | `List[PlanStep]` | Steps to be executed in the plan |
| `context` | `Optional[Dict[str, Any]]` | Additional context for the plan |
| `meta` | `Optional[Dict[str, Any]]` | Metadata about the plan |

### `PlanStep`

Represents a single step in an agent plan.

```python
from plan_lint.types import PlanStep

step = PlanStep(
    id="step1",
    tool="db.query",
    args={"query": "SELECT * FROM users"},
    on_fail="abort"
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier for the step |
| `tool` | `str` | The tool to be used in this step |
| `args` | `Dict[str, Any]` | Arguments to pass to the tool |
| `on_fail` | `str` | Action to take if step fails (default: "abort") |

### `Policy`

Represents a policy for plan validation.

```python
from plan_lint.types import Policy

policy = Policy(
    allow_tools=["db.query_ro", "notify.email"],
    bounds={"payments.transfer.amount": [0.01, 1000.00]},
    deny_tokens_regex=["password", "secret", "DROP TABLE"],
    max_steps=10,
    risk_weights={"TOOL_DENY": 0.8, "RAW_SECRET": 0.6},
    fail_risk_threshold=0.7
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `allow_tools` | `List[str]` | List of allowed tools |
| `bounds` | `Dict[str, List[Union[int, float]]]` | Parameter boundaries |
| `deny_tokens_regex` | `List[str]` | Patterns to reject |
| `max_steps` | `int` | Maximum allowed steps in a plan |
| `risk_weights` | `Dict[str, float]` | Weights for different violation types |
| `fail_risk_threshold` | `float` | Risk threshold for failing validation |

### `PlanError`

Represents an error found during plan validation.

```python
from plan_lint.types import PlanError, ErrorCode

error = PlanError(
    step=1,
    code=ErrorCode.TOOL_DENY,
    msg="Tool 'db.write' is not allowed by policy"
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `step` | `Optional[int]` | Index of the step where the error was found |
| `code` | `ErrorCode` | Error code |
| `msg` | `str` | Human-readable error message |

### `PlanWarning`

Represents a warning found during plan validation.

```python
from plan_lint.types import PlanWarning

warning = PlanWarning(
    step=1,
    code="PERFORMANCE",
    msg="This query might be slow for large datasets"
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `step` | `Optional[int]` | Index of the step where the warning was found |
| `code` | `str` | Warning code |
| `msg` | `str` | Human-readable warning message |

### `ErrorCode`

Enum of error codes for plan validation failures.

```python
from plan_lint.types import ErrorCode

# Available error codes
ErrorCode.SCHEMA_INVALID      # Invalid plan schema
ErrorCode.TOOL_DENY           # Unauthorized tool
ErrorCode.BOUND_VIOLATION     # Parameter out of bounds
ErrorCode.RAW_SECRET          # Sensitive data exposure
ErrorCode.LOOP_DETECTED       # Circular dependency detected
ErrorCode.MAX_STEPS_EXCEEDED  # Too many steps in plan
ErrorCode.MISSING_HANDLER     # Missing error handler
```

### `Status`

Enum of validation status values.

```python
from plan_lint.types import Status

Status.PASS    # Plan passed validation
Status.WARN    # Plan has warnings but passed
Status.ERROR   # Plan failed validation
```

### `ValidationResult`

Contains the results of plan validation.

```python
from plan_lint.types import ValidationResult, Status

result = ValidationResult(
    status=Status.ERROR,
    risk_score=0.6,
    errors=[error1, error2],
    warnings=[warning1]
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | `Status` | Status of validation (PASS, WARN, ERROR) |
| `risk_score` | `float` | Risk score between 0.0 and 1.0 |
| `errors` | `List[PlanError]` | List of validation errors |
| `warnings` | `List[PlanWarning]` | List of validation warnings |

## Examples

### Basic Validation

```python
from plan_lint.core import validate_plan
from plan_lint.loader import load_plan, load_policy
from plan_lint.types import Status

# Load plan and policy
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
```

### Using Rego Policies

```python
from plan_lint.core import validate_plan
from plan_lint.loader import load_plan, load_policy

# Load plan and policy
plan = load_plan("plans/customer_refund.json")
policy, rego_policy = load_policy("policies/security.rego")

# Validate with Rego policy
result = validate_plan(plan, policy, rego_policy=rego_policy, use_opa=True)

# Check results
if result.status == Status.PASS:
    print("Plan is valid!")
else:
    print(f"Plan validation failed with risk score: {result.risk_score}")
    for error in result.errors:
        print(f"Step {error.step}: {error.msg} ({error.code})")
```

### Creating Plans Programmatically

```python
from plan_lint.core import validate_plan
from plan_lint.types import Plan, PlanStep, Policy

# Create a plan programmatically
plan = Plan(
    goal="Send account statement to user",
    steps=[
        PlanStep(
            id="step1",
            tool="db.query_ro",
            args={
                "query": "SELECT balance FROM accounts WHERE user_id = ?",
                "params": ["user-123"]
            }
        ),
        PlanStep(
            id="step2",
            tool="notify.email",
            args={
                "to": "user@example.com",
                "subject": "Your Account Statement",
                "body": "Your current balance is $5000"
            }
        )
    ],
    context={"user_id": "user-123"}
)

# Create a policy programmatically
policy = Policy(
    allow_tools=["db.query_ro", "notify.email"],
    bounds={},
    deny_tokens_regex=["password", "secret", "DROP TABLE"],
    max_steps=5
)

# Validate plan
result = validate_plan(plan, policy)
```

### Calculating Risk Score

```python
from plan_lint.core import calculate_risk_score
from plan_lint.types import PlanError, ErrorCode

# Define errors and risk weights
errors = [
    PlanError(step=1, code=ErrorCode.RAW_SECRET, msg="Sensitive data detected"),
    PlanError(step=2, code=ErrorCode.BOUND_VIOLATION, msg="Amount exceeds maximum")
]

warnings = []
risk_weights = {
    "raw_secret": 0.7,
    "bound_violation": 0.4
}

# Calculate risk score
risk_score = calculate_risk_score(errors, warnings, risk_weights)
print(f"Risk score: {risk_score}")  # Output: Risk score: 1.0 