# Types API

This page documents the data types used in Plan-Lint.

## `Plan`

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

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `goal` | `str` | The goal or purpose of the plan |
| `steps` | `List[PlanStep]` | Steps to be executed in the plan |
| `context` | `Optional[Dict[str, Any]]` | Additional context for the plan |
| `meta` | `Optional[Dict[str, Any]]` | Metadata about the plan |

## `PlanStep`

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

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier for the step |
| `tool` | `str` | The tool to be used in this step |
| `args` | `Dict[str, Any]` | Arguments to pass to the tool |
| `on_fail` | `str` | Action to take if step fails (default: "abort") |

## `Policy`

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

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `allow_tools` | `List[str]` | List of allowed tools |
| `bounds` | `Dict[str, List[Union[int, float]]]` | Parameter boundaries |
| `deny_tokens_regex` | `List[str]` | Patterns to reject |
| `max_steps` | `int` | Maximum allowed steps in a plan |
| `risk_weights` | `Dict[str, float]` | Weights for different violation types |
| `fail_risk_threshold` | `float` | Risk threshold for failing validation |

## `PlanError`

Represents an error found during plan validation.

```python
from plan_lint.types import PlanError, ErrorCode

error = PlanError(
    step=1,
    code=ErrorCode.TOOL_DENY,
    msg="Tool 'db.write' is not allowed by policy"
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `step` | `Optional[int]` | Index of the step where the error was found |
| `code` | `ErrorCode` | Error code |
| `msg` | `str` | Human-readable error message |

## `PlanWarning`

Represents a warning found during plan validation.

```python
from plan_lint.types import PlanWarning

warning = PlanWarning(
    step=1,
    code="PERFORMANCE",
    msg="This query might be slow for large datasets"
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `step` | `Optional[int]` | Index of the step where the warning was found |
| `code` | `str` | Warning code |
| `msg` | `str` | Human-readable warning message |

## `ErrorCode`

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

## `Status`

Enum of validation status values.

```python
from plan_lint.types import Status

Status.PASS    # Plan passed validation
Status.WARN    # Plan has warnings but passed
Status.ERROR   # Plan failed validation
```

## `ValidationResult`

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

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | `Status` | Status of validation (PASS, WARN, ERROR) |
| `risk_score` | `float` | Risk score between 0.0 and 1.0 |
| `errors` | `List[PlanError]` | List of validation errors |
| `warnings` | `List[PlanWarning]` | List of validation warnings |
