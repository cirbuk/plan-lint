# Custom Rule Development

This page guides you through creating custom validation rules for Plan-Lint.

## Overview

Plan-Lint allows you to extend its validation capabilities by creating custom rules. Custom rules can help you enforce organization-specific policies, business logic, or unique security requirements not covered by built-in rules.

There are three main approaches to developing custom rules for Plan-Lint:

1. **YAML Rules**: Simple, declarative rules for common validation patterns
2. **Rego Policies**: Complex, powerful rules using the Open Policy Agent's Rego language
3. **Python Extensions**: Programmatic rules with full access to the Plan-Lint API

## Creating YAML Rules

YAML rules provide a straightforward way to define validation logic using a declarative syntax. They are best suited for simple validation scenarios.

### Basic Structure

A basic YAML policy file looks like this:

```yaml
# custom_policy.yaml
allow_tools:
  - db.query_ro
  - payments.transfer.small
  - notify.email

bounds:
  payments.transfer.small.amount: [0.01, 100.00]

deny_tokens_regex:
  - "DROP TABLE"
  - "1=1"
  - "password"
  - "secret"

risk_weights:
  sql_injection: 0.8
  sensitive_data_exposure: 0.7
  unauthorized_tool: 0.9

fail_risk_threshold: 0.5
max_steps: 15
```

### Available Rule Types

YAML policies support several rule types:

| Rule Type | Description | Example |
|-----------|-------------|---------|
| `allow_tools` | List of allowed tools | `- db.query_ro` |
| `bounds` | Parameter boundaries | `payments.transfer.amount: [0.01, 1000.00]` |
| `deny_tokens_regex` | Patterns to reject | `- "DROP TABLE"` |
| `risk_weights` | Custom risk scores | `sql_injection: 0.8` |
| `fail_risk_threshold` | Maximum tolerated risk | `0.5` |
| `max_steps` | Maximum plan steps | `15` |

### Custom Tool Patterns

You can define custom tool patterns to match specific tool name patterns:

```yaml
# Custom tool pattern for small payments
tool_patterns:
  payments.transfer.small:
    pattern: "payments.transfer"
    conditions:
      - "parameters.amount <= 100.0"
```

This defines a virtual tool type `payments.transfer.small` that will match any `payments.transfer` tool with an amount parameter less than or equal to 100.0.

### Using Custom YAML Rules

To use your custom YAML rules:

```python
from plan_lint import validate_plan

plan = {
    "goal": "Process customer refund",
    "steps": [
        # Plan steps here
    ]
}

result = validate_plan(plan, policy_files=["path/to/custom_policy.yaml"])
```

## Creating Rego Policies

Rego is a powerful policy language that provides more flexibility and expressiveness than YAML.

### Basic Structure

A basic Rego policy file looks like this:

```rego
# custom_policy.rego
package planlint

import future.keywords.in

# Default deny
default allow = false

# Set of allowed tools
allowed_tools = {
    "db.query_ro",
    "payments.transfer",
    "notify.email"
}

# Allow if no violations
allow {
    count(violations) == 0
}

# Define violations
violations[result] {
    # Get the step
    step := input.plan.steps[_]
    
    # Check if tool is allowed
    not step.tool in allowed_tools
    
    # Create violation result
    result := {
        "rule": "unauthorized_tool",
        "message": sprintf("Tool '%s' is not authorized", [step.tool]),
        "severity": "high",
        "step_id": step.id
    }
}

# Example parameter boundary check
violations[result] {
    # Get the step
    step := input.plan.steps[_]
    step.tool == "payments.transfer"
    
    # Check amount boundaries
    amount := to_number(step.parameters.amount)
    amount > 1000.00
    
    # Create violation result
    result := {
        "rule": "parameter_bounds",
        "message": sprintf("Amount %f exceeds maximum allowed (1000.00)", [amount]),
        "severity": "medium",
        "step_id": step.id
    }
}

# Calculate risk score (0.0 to 1.0)
risk_score = score {
    # Define risk weights for different violations
    weights := {
        "unauthorized_tool": 0.9,
        "parameter_bounds": 0.6,
        "sql_injection": 0.8
    }
    
    # Sum up risk weights for all violations
    total_weight := sum([weights[v.rule] | v := violations[_]; v.rule in weights])
    
    # Cap at 1.0
    score := min(total_weight, 1.0)
}
```

### Accessing Plan Data

In Rego policies, you can access the plan data through the `input` document:

```rego
# Access plan goal
goal := input.plan.goal

# Access plan steps
steps := input.plan.steps

# Access context
user_role := input.context.user_role

# Access a specific step
first_step := input.plan.steps[0]

# Access a parameter in a step
amount := input.plan.steps[0].parameters.amount
```

### Advanced Rego Examples

#### Context-Based Authorization

```rego
violations[result] {
    # Get user role from context
    role := input.context.user_role
    
    # Role-specific allowed tools
    allowed_tools_by_role := {
        "admin": {"db.query", "db.write", "payments.transfer"},
        "editor": {"db.query", "payments.view"},
        "viewer": {"db.query_ro"}
    }
    
    # Get allowed tools for this role
    role_tools := allowed_tools_by_role[role]
    
    # Check each step
    step := input.plan.steps[_]
    not step.tool in role_tools
    
    result := {
        "rule": "role_authorization",
        "message": sprintf("Role '%s' is not authorized to use tool '%s'", [role, step.tool]),
        "severity": "high",
        "step_id": step.id
    }
}
```

#### Dependency Chain Analysis

```rego
# Detect circular dependencies
violations[result] {
    # Get a step
    step := input.plan.steps[_]
    
    # Check if this step is in its own dependency chain
    is_circular := depends_on_self(step.id, step.depends_on)
    is_circular
    
    result := {
        "rule": "circular_dependency",
        "message": sprintf("Step '%s' has a circular dependency", [step.id]),
        "severity": "high",
        "step_id": step.id
    }
}

# Recursive function to check for circular dependencies
depends_on_self(id, deps) {
    # Direct dependency on self
    id in deps
} else {
    # Check indirect dependencies
    some dep in deps
    some step in input.plan.steps
    step.id == dep
    step.depends_on
    depends_on_self(id, step.depends_on)
}
```

### Using Custom Rego Policies

To use your custom Rego policies:

```python
from plan_lint import validate_plan

plan = {
    "goal": "Process customer refund",
    "steps": [
        # Plan steps here
    ]
}

result = validate_plan(plan, policy_files=["path/to/custom_policy.rego"])
```

## Creating Python Extensions

For the most complex validation logic, you can write custom Python rules that have full access to the Plan-Lint API.

### Basic Python Rule

```python
from typing import List, Dict, Any
from plan_lint.types import Plan, PlanError, ErrorCode

def check_custom_requirements(plan: Plan, context: Dict[str, Any] = None) -> List[PlanError]:
    """Custom rule to check specific business requirements."""
    errors = []
    
    # Example: Ensure payments to certain accounts are limited
    for i, step in enumerate(plan.steps):
        if step.tool == "payments.transfer":
            amount = float(step.parameters.get("amount", 0))
            account = step.parameters.get("account", "")
            
            # Check for high-risk accounts
            high_risk_accounts = ["ACC123", "ACC456"]
            if account in high_risk_accounts and amount > 500:
                errors.append(
                    PlanError(
                        step=i,
                        code=ErrorCode.CUSTOM,
                        msg=f"Payments to high-risk account {account} must be less than $500 (found ${amount})",
                    )
                )
    
    return errors
```

### Integrating Custom Python Rules

To use your custom Python rules, create a module and import it into your validation code:

```python
from plan_lint import validate_plan
from my_custom_rules import check_custom_requirements

plan = {
    "goal": "Process customer refund",
    "steps": [
        # Plan steps here
    ]
}

# Register custom rule with the validator
custom_validators = [check_custom_requirements]

result = validate_plan(plan, custom_validators=custom_validators)
```

### Advanced Python Rule Examples

#### Cross-Step Correlation

```python
def check_cross_step_correlation(plan: Plan, context: Dict[str, Any] = None) -> List[PlanError]:
    """Check that the email recipient matches the transaction recipient."""
    errors = []
    
    # Find payment and notification steps
    payment_steps = []
    notification_steps = []
    
    for i, step in enumerate(plan.steps):
        if step.tool == "payments.transfer":
            payment_steps.append((i, step))
        elif step.tool == "notify.email":
            notification_steps.append((i, step))
    
    # Check that each payment has a matching notification
    for i, payment_step in payment_steps:
        recipient_account = payment_step.parameters.get("recipient_account", "")
        recipient_email = None
        
        # Try to find the recipient's email from context
        if context and "accounts" in context:
            for account in context["accounts"]:
                if account.get("account_number") == recipient_account:
                    recipient_email = account.get("email")
        
        if recipient_email:
            # Check if there's a notification to the correct recipient
            notification_found = False
            for j, notification_step in notification_steps:
                if notification_step.parameters.get("to") == recipient_email:
                    notification_found = True
                    break
            
            if not notification_found:
                errors.append(
                    PlanError(
                        step=i,
                        code=ErrorCode.CUSTOM,
                        msg=f"Payment to account {recipient_account} must be accompanied by an email notification to {recipient_email}",
                    )
                )
    
    return errors
```

#### Time-Based Restrictions

```python
import datetime

def check_time_restrictions(plan: Plan, context: Dict[str, Any] = None) -> List[PlanError]:
    """Check that high-value transfers are only scheduled during business hours."""
    errors = []
    
    # Define business hours
    business_start = datetime.time(9, 0)  # 9:00 AM
    business_end = datetime.time(17, 0)   # 5:00 PM
    
    # Get current time, or use time from context if provided
    current_time = datetime.datetime.now().time()
    if context and "current_time" in context:
        current_time = context["current_time"]
    
    # Check each payment step
    for i, step in enumerate(plan.steps):
        if step.tool == "payments.transfer":
            amount = float(step.parameters.get("amount", 0))
            
            # Check if it's a high-value transfer (over $10,000)
            if amount > 10000:
                # Check if current time is within business hours
                is_business_hours = (
                    current_time >= business_start and 
                    current_time <= business_end
                )
                
                if not is_business_hours:
                    errors.append(
                        PlanError(
                            step=i,
                            code=ErrorCode.CUSTOM,
                            msg=f"High-value transfers (${amount}) can only be scheduled during business hours (9:00 AM - 5:00 PM)",
                        )
                    )
    
    return errors
```

## Best Practices for Custom Rules

### Rule Design

1. **Focus on Specific Concerns**: Each rule should address a specific security or operational concern.
2. **Balance Security and Usability**: Rules that are too restrictive may lead to workarounds.
3. **Provide Clear Error Messages**: Help users understand why a plan failed validation and how to fix it.
4. **Use Appropriate Severity Levels**: Use severity levels (e.g., high, medium, low) to indicate the importance of a violation.

### Performance Considerations

1. **Optimize Rule Evaluation**: For Rego policies, use indexing to improve performance:
   ```rego
   # Inefficient
   violations[result] {
       step := input.plan.steps[_]
       step.tool == "db.query"
       # ...
   }
   
   # Efficient (indexed)
   db_query_steps[step] {
       step := input.plan.steps[_]
       step.tool == "db.query"
   }
   
   violations[result] {
       step := db_query_steps[_]
       # ...
   }
   ```

2. **Minimize External API Calls**: If your rules need to make external API calls, consider caching results.

### Testing Custom Rules

Always test your custom rules with both valid and invalid plans:

```python
import unittest
from plan_lint import validate_plan
from my_custom_rules import check_custom_requirements

class TestCustomRules(unittest.TestCase):
    def test_valid_plan(self):
        plan = {
            "goal": "Process small refund",
            "steps": [
                {
                    "id": "step1",
                    "tool": "payments.transfer",
                    "parameters": {
                        "amount": "50.00",
                        "account": "ACC789"
                    }
                }
            ]
        }
        
        result = validate_plan(
            plan, 
            custom_validators=[check_custom_requirements]
        )
        
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_invalid_plan(self):
        plan = {
            "goal": "Process large refund",
            "steps": [
                {
                    "id": "step1",
                    "tool": "payments.transfer",
                    "parameters": {
                        "amount": "1000.00",
                        "account": "ACC123"  # High-risk account
                    }
                }
            ]
        }
        
        result = validate_plan(
            plan, 
            custom_validators=[check_custom_requirements]
        )
        
        self.assertFalse(result.valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("high-risk account", result.errors[0].msg)

if __name__ == "__main__":
    unittest.main()
```

## Packaging and Distribution

For organization-wide use, consider packaging your custom rules:

### Directory Structure

```
my-custom-rules/
├── pyproject.toml
├── README.md
├── src/
│   └── my_custom_rules/
│       ├── __init__.py
│       ├── python_rules.py
│       └── policies/
│           ├── custom_policy.yaml
│           └── custom_policy.rego
└── tests/
    └── test_rules.py
```

### Package Installation

```bash
pip install my-custom-rules
```

### Usage After Packaging

```python
from plan_lint import validate_plan
from my_custom_rules import get_custom_validators, get_policy_files

plan = {
    "goal": "Process customer refund",
    "steps": [
        # Plan steps here
    ]
}

result = validate_plan(
    plan, 
    custom_validators=get_custom_validators(),
    policy_files=get_policy_files()
)
```

## Integration with CI/CD

To enforce policy compliance in your CI/CD pipeline:

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
          pip install plan-lint my-custom-rules
      
      - name: Validate plans
        run: |
          python -c "
          import glob
          import json
          import sys
          from plan_lint import validate_plan
          from my_custom_rules import get_custom_validators, get_policy_files
          
          failed = False
          for plan_file in glob.glob('plans/**/*.json'):
              with open(plan_file, 'r') as f:
                  plan = json.load(f)
              
              result = validate_plan(
                  plan, 
                  custom_validators=get_custom_validators(),
                  policy_files=get_policy_files()
              )
              
              if not result.valid:
                  print(f'❌ {plan_file} failed validation:')
                  for error in result.errors:
                      print(f'  - {error.msg}')
                  failed = True
              else:
                  print(f'✅ {plan_file} passed validation')
          
          if failed:
              sys.exit(1)
          "
```

## Conclusion

Custom rules allow you to tailor Plan-Lint's validation to your specific requirements. By using the appropriate rule type (YAML, Rego, or Python) for your needs, you can create a comprehensive validation framework that ensures all agent-generated plans comply with your security and operational policies.

For more examples and detailed API documentation, refer to the API Reference section and the Examples page.
