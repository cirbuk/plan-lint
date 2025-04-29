# API Reference Overview

This section provides detailed information about the Plan-Lint API.

## API Sections

The Plan-Lint API is organized into the following sections:

- **[Core](core.md)**: Core functions for validating plans
- **[Types](types.md)**: Data types for representing plans, steps, policies, and validation results
- **[Loader](loader.md)**: Functions for loading plans, policies, and schemas
- **[Rules](rules.md)**: Rule validation functions for checking specific aspects of plans
- **[Validator](validator.md)**: Reusable validator class for validating plans against policies

## Quick Start

Here's a quick example to get you started with the Plan-Lint API:

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

## Installation

To use the Plan-Lint API, first install the package:

```bash
pip install plan-lint
```

## Python Version Compatibility

Plan-Lint requires Python 3.8 or later.

## Error Handling

Plan-Lint functions raise exceptions in the following cases:

- `ValueError`: Invalid plan or policy structure
- `FileNotFoundError`: Referenced plan or policy file not found
- `jsonschema.exceptions.ValidationError`: Plan schema validation failure

Always handle these exceptions in production code:

```python
from plan_lint.loader import load_plan, load_policy
from plan_lint.core import validate_plan
import jsonschema

try:
    plan = load_plan("plans/customer_refund.json")
    policy, rego_policy = load_policy("policies/security.yaml")
    result = validate_plan(plan, policy)
    
    # Process result...
    
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid plan or policy: {e}")
except jsonschema.exceptions.ValidationError as e:
    print(f"Plan schema validation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```
