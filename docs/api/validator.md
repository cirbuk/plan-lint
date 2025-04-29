# Validator API

This page documents the policy validator class for reusable validation.

## `PolicyValidator`

Class for creating a reusable validator with specific policies.

```python
from plan_lint.validator import PolicyValidator

validator = PolicyValidator(
    policy_files=["policies/security.yaml", "policies/custom.rego"],
    custom_validators=[my_custom_validator],
    allow_undefined_tools=False
)

result = validator.validate(plan, context={"user_role": "admin"})
```

### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `policy_files` | `List[str]` | List of policy file paths (YAML or Rego) |
| `custom_validators` | `List[Callable]` | Optional list of custom validator functions |
| `allow_undefined_tools` | `bool` | Whether to allow tools not defined in policies |

### Methods

#### `validate(plan, context=None, silent=False)`

Validate a plan using the configured policies.

```python
result = validator.validate(plan, context={"user_role": "admin"})
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan` | `Dict[str, Any]` or `Plan` | The plan to validate |
| `context` | `Dict[str, Any]` | Optional context information for validation |
| `silent` | `bool` | Whether to suppress console output |

Returns a `ValidationResult` object.

#### `add_policy_file(file_path)`

Add a policy file to the validator.

```python
validator.add_policy_file("policies/additional.yaml")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the policy file to add |

#### `add_custom_validator(validator_func)`

Add a custom validator function.

```python
validator.add_custom_validator(my_custom_validator)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `validator_func` | `Callable` | Custom validator function to add |

## Example Usage

```python
from plan_lint.validator import PolicyValidator
from plan_lint.types import Plan, PlanStep

# Create a validator with policies
validator = PolicyValidator(
    policy_files=["policies/security.yaml", "policies/operations.rego"]
)

# Validate a plan
plan = Plan(
    goal="Process customer refund",
    steps=[
        PlanStep(
            id="step1",
            tool="db.query_ro",
            args={
                "query": "SELECT account FROM customers WHERE id = ?",
                "params": ["customer-123"]
            }
        ),
        PlanStep(
            id="step2",
            tool="payments.transfer",
            args={
                "amount": 100.00,
                "account": "ACC-123"
            }
        )
    ]
)

# Validate with context
result = validator.validate(
    plan,
    context={
        "user_role": "admin",
        "environment": "production"
    }
)

# Check results
if result.valid:
    print("Plan is valid!")
else:
    for error in result.errors:
        print(f"Step {error.step}: {error.msg}")
```

## Web Service Integration

Example of using PolicyValidator in a web service:

```python
from flask import Flask, request, jsonify
from plan_lint.validator import PolicyValidator

app = Flask(__name__)

# Create a validator at service startup
validator = PolicyValidator(
    policy_files=["policies/security.yaml", "policies/operations.rego"]
)

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    
    plan = data.get("plan")
    context = data.get("context", {})
    
    if not plan:
        return jsonify({"error": "Missing plan"}), 400
    
    result = validator.validate(plan, context=context)
    
    return jsonify({
        "valid": result.valid,
        "risk_score": result.risk_score,
        "errors": [
            {
                "step": error.step,
                "code": error.code.name,
                "message": error.msg
            }
            for error in result.errors
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
```
