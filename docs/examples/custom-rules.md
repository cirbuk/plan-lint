# Custom Rules Examples

This page demonstrates how to create and use custom validation rules with Plan-Lint.

## Overview of Custom Rules

Plan-Lint allows you to extend its validation capabilities with custom rules, which can be created in three main ways:

1. **YAML Rules**: Simple, declarative rules for common patterns
2. **Rego Policies**: Advanced rules using Open Policy Agent's Rego language
3. **Python Functions**: Programmatic rules with full access to the Plan-Lint API

## Custom YAML Rules

YAML rules are the simplest way to define custom validation patterns.

### Example: Custom Transaction Limits

```yaml
# custom_transaction_policy.yaml
allow_tools:
  - db.query_ro
  - payments.transfer.small
  - payments.transfer.medium
  - payments.transfer.large
  - notify.email

# Define custom tools with conditions
tool_patterns:
  payments.transfer.small:
    pattern: "payments.transfer"
    conditions:
      - "parameters.amount <= 100.0"
  
  payments.transfer.medium:
    pattern: "payments.transfer"
    conditions:
      - "parameters.amount > 100.0"
      - "parameters.amount <= 1000.0"
  
  payments.transfer.large:
    pattern: "payments.transfer"
    conditions:
      - "parameters.amount > 1000.0"
      - "parameters.amount <= 10000.0"

# Define different bounds for each tool
bounds:
  payments.transfer.small.amount: [0.01, 100.00]
  payments.transfer.medium.amount: [100.01, 1000.00]
  payments.transfer.large.amount: [1000.01, 10000.00]

# Additional security rules
deny_tokens_regex:
  - "DROP TABLE"
  - "1=1"
  - "password"
  - "secret"
```

This policy creates three different levels of payment transactions, each with its own validation rules.

### Using Custom YAML Rules

```bash
plan-lint validate --plan payment_plan.json --policy custom_transaction_policy.yaml
```

## Custom Rego Policies

Rego provides a powerful language for expressing complex validation rules.

### Example: Role-Based Access Control

```rego
# role_based_policy.rego
package planlint

import future.keywords.in

# Default deny
default allow = false

# Allow if no violations found
allow {
    count(violations) == 0
}

# Define role-based tool access
allowed_tools_by_role := {
    "admin": {
        "db.query": true,
        "db.write": true,
        "payments.transfer": true,
        "system.configure": true
    },
    "operator": {
        "db.query": true,
        "payments.transfer": true
    },
    "viewer": {
        "db.query_ro": true
    }
}

# Check if tool is allowed for user role
violations[result] {
    # Get user role from context
    role := input.context.user_role
    
    # Get current step
    step := input.plan.steps[i]
    
    # Get allowed tools for this role
    role_tools := allowed_tools_by_role[role]
    
    # Check if tool is allowed for this role
    not step.tool in keys(role_tools)
    
    # Create violation result
    result := {
        "rule": "role_authorization",
        "message": sprintf("User with role '%s' is not authorized to use tool '%s'", [role, step.tool]),
        "severity": "high",
        "step_id": step.id
    }
}

# Check transaction limits by role
violations[result] {
    # Get user role from context
    role := input.context.user_role
    
    # Get current step
    step := input.plan.steps[i]
    
    # Only check payment steps
    step.tool == "payments.transfer"
    
    # Define limits by role
    limits := {
        "admin": 10000.0,
        "operator": 1000.0,
        "viewer": 0.0
    }
    
    # Get amount
    amount := to_number(step.parameters.amount)
    
    # Check if amount exceeds limit for role
    amount > limits[role]
    
    # Create violation result
    result := {
        "rule": "transaction_limit",
        "message": sprintf("Transaction amount %f exceeds limit of %f for role '%s'", [amount, limits[role], role]),
        "severity": "high", 
        "step_id": step.id
    }
}
```

### Using Custom Rego Policies

```bash
plan-lint validate --plan payment_plan.json --policy role_based_policy.rego --context context.json
```

Where `context.json` might look like:

```json
{
  "user_role": "operator",
  "environment": "production"
}
```

## Custom Python Rules

For the most flexibility, you can define custom validation functions in Python.

### Example: Business Hours Validation

```python
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from plan_lint.types import Plan, PlanError, ErrorCode

def business_hours_validator(plan: Plan, context: Optional[Dict[str, Any]] = None) -> List[PlanError]:
    """
    Validate that certain operations only occur during business hours.
    
    Args:
        plan: The plan to validate
        context: Optional context information
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Define business hours
    business_start = time(9, 0)  # 9:00 AM
    business_end = time(17, 0)   # 5:00 PM
    
    # Get current time from context or use system time
    current_time = datetime.now().time()
    if context and "current_time" in context:
        time_str = context["current_time"]
        try:
            # Parse time string (assuming format like "14:30")
            hour, minute = map(int, time_str.split(":"))
            current_time = time(hour, minute)
        except (ValueError, TypeError):
            pass
    
    # Check if we're in business hours
    is_business_hours = (
        current_time >= business_start and 
        current_time <= business_end
    )
    
    # High-risk operations to check
    high_risk_operations = [
        "payments.transfer",
        "user.create_admin",
        "system.configure",
        "db.write"
    ]
    
    # Check each step
    for i, step in enumerate(plan.steps):
        if any(step.tool.startswith(op) for op in high_risk_operations):
            # If outside business hours, add an error
            if not is_business_hours:
                errors.append(
                    PlanError(
                        step=i,
                        code=ErrorCode.CUSTOM,
                        msg=f"Operation '{step.tool}' can only be performed during business hours (9:00 AM - 5:00 PM)"
                    )
                )
                
            # Check for large amounts in any payment
            if step.tool == "payments.transfer":
                amount = float(step.parameters.get("amount", 0))
                if amount > 10000:
                    errors.append(
                        PlanError(
                            step=i,
                            code=ErrorCode.CUSTOM,
                            msg=f"Large transfers (${amount}) require additional approval"
                        )
                    )
    
    return errors
```

### Using Custom Python Rules

To use custom Python validators:

1. Create a Python module with your validation functions
2. Import and register your validators

```python
from plan_lint import validate_plan
from plan_lint.loader import load_plan, load_policy
from my_custom_validators import business_hours_validator

# Load plan and policy
plan = load_plan("payment_plan.json")
policy, rego_policy = load_policy("payment_policy.yaml")

# Set up context
context = {
    "user_role": "operator",
    "current_time": "14:30"
}

# Validate with custom validator
result = validate_plan(
    plan,
    policy,
    custom_validators=[business_hours_validator],
    context=context
)

# Check results
if result.valid:
    print("Plan is valid!")
else:
    for error in result.errors:
        print(f"Step {error.step}: {error.msg}")
```

## Combining Multiple Custom Rules

For comprehensive validation, combine different rule types:

```python
from plan_lint import validate_plan
from plan_lint.loader import load_plan, load_policy
from my_custom_validators import (
    business_hours_validator,
    data_sensitivity_validator,
    audit_trail_validator
)

# Load a Python plan object
plan = load_plan("complex_plan.json")

# Load multiple policies
yaml_policy, _ = load_policy("security_basics.yaml")
_, rego_policy = load_policy("role_based_access.rego")

# Custom Python validators
custom_validators = [
    business_hours_validator,
    data_sensitivity_validator,
    audit_trail_validator
]

# Validate with all rules
result = validate_plan(
    plan,
    yaml_policy,
    rego_policy=rego_policy,
    custom_validators=custom_validators,
    context={"user_role": "operator", "environment": "production"}
)
```

## CI/CD Integration Example

You can integrate custom rules into your CI/CD pipeline:

```yaml
# .github/workflows/validate-plans.yml
name: Validate Agent Plans

on:
  pull_request:
    paths:
      - 'plans/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install plan-lint
          pip install -e ./custom_validators
      
      - name: Validate plans
        run: |
          python -c "
          import glob
          import json
          import sys
          from plan_lint import validate_plan
          from plan_lint.loader import load_plan, load_policy
          from custom_validators import register_validators
          
          # Load all custom validators
          custom_validators = register_validators()
          
          # Load policies
          policy, rego_policy = load_policy('policies/security.yaml')
          
          failed = False
          
          for plan_file in glob.glob('plans/**/*.json'):
              print(f'Validating {plan_file}...')
              with open(plan_file, 'r') as f:
                  plan_data = json.load(f)
              
              plan = load_plan(plan_file)
              
              # Set context based on environment
              context = {
                  'environment': 'ci',
                  'user_role': 'automation'
              }
              
              # Validate plan
              result = validate_plan(
                  plan,
                  policy,
                  rego_policy=rego_policy,
                  custom_validators=custom_validators,
                  context=context
              )
              
              if not result.valid:
                  print(f'❌ {plan_file} failed validation:')
                  for error in result.errors:
                      print(f'  - Step {error.step}: {error.msg}')
                  failed = True
              else:
                  print(f'✅ {plan_file} passed validation')
          
          if failed:
              sys.exit(1)
          "
```

By creating custom validation rules, you can extend Plan-Lint to address your organization's specific security and operational requirements. 