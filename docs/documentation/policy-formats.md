# Policy Formats

This page explains the different formats supported by Plan-Lint for defining policies.

## Overview

Plan-Lint supports two main policy formats:

1. **YAML Policies**: A simpler, declarative format for defining basic rules
2. **Rego Policies**: A powerful policy language for expressing complex rules

Each format has its own advantages, and you can choose the one that best fits your needs.

## YAML Policies

YAML policies provide a simple, declarative way to define validation rules. They are easy to write and understand, making them a good choice for basic validation scenarios.

### Basic Structure

YAML policies are structured as key-value pairs defining rules:

```yaml
# List of allowed tools
allow_tools:
  - db.query_ro
  - notify.email
  - payments.transfer

# Parameter boundaries
bounds:
  payments.transfer.amount: [0.01, 10000]  # Numeric boundaries
  notify.email.to_list: [1, 100]           # List size boundaries

# Patterns to detect
deny_tokens_regex:
  - "password"
  - "secret"
  - "apikey"
  - "\\bsql\\b"

# Risk weights for violations
risk_weights:
  excessive_amount: 0.4
  sensitive_data: 0.5
  sql_injection: 0.6

# Threshold for failing validation
fail_risk_threshold: 0.8

# Maximum number of steps allowed in a plan
max_steps: 20
```

### Available Rules

| Rule | Description | Example |
|------|-------------|---------|
| `allow_tools` | List of permitted tools | `- db.query_ro` |
| `bounds` | Parameter boundaries | `payments.amount: [0.01, 10000]` |
| `deny_tokens_regex` | Prohibited patterns | `- "password"` |
| `allow_tokens_regex` | Permitted patterns | `- "safe_pattern"` |
| `risk_weights` | Violation risk weights | `sql_injection: 0.6` |
| `fail_risk_threshold` | Risk threshold | `0.8` |
| `max_steps` | Maximum plan steps | `20` |

### Example YAML Policy

Here's a complete example of a YAML policy:

```yaml
# policy.yaml
allow_tools:
  - db.query_ro
  - db.query
  - payments.transfer
  - analytics.summarize
  - notify.customer

bounds:
  payments.transfer.amount: [0.01, 10000.00]
  db.query.limit: [1, 1000]
  
deny_tokens_regex:
  - "1=1"
  - "OR 1=1"
  - "DROP TABLE"
  - "--"
  - "password"
  - "secret"
  - "apikey"
  - "creditCard"
  - "ssn"
  
risk_weights:
  tool_deny: 0.9
  excessive_amount: 0.4
  insufficient_amount: 0.1
  sensitive_data: 0.5
  sql_injection: 0.6
  
fail_risk_threshold: 0.8
max_steps: 10
```

### Loading a YAML Policy

```python
from plan_lint import validate_plan
from plan_lint.loader import load_policy

# Load the YAML policy
policy = load_policy("path/to/policy.yaml")

# Validate a plan against the policy
result = validate_plan(plan, policy=policy)
```

## Rego Policies

For more advanced policy definitions, Plan-Lint supports [Rego](https://www.openpolicyagent.org/docs/latest/policy-language/), the policy language of Open Policy Agent (OPA). Rego provides a powerful and flexible way to define complex validation rules.

### Basic Structure

A Rego policy for Plan-Lint typically includes:

```rego
package planlint

import future.keywords.in

# Default deny policy - all plans are denied unless explicitly allowed
default allow = false

# Default empty violations
default violations = []

# Default risk score is 0
default risk_score = 0.0

# Define allowed tools and other policy components
allowed_tools = {
    "db.query_ro": {},
    "notify.email": {},
    "payments.transfer": {"min_amount": 0.01, "max_amount": 10000}
}

# Allow rule - defines when a plan should be allowed
allow if {
    # Add conditions for allowing a plan
    all_tools_allowed
    risk_score < 0.8
}

# Helper rule - check if all tools in the plan are allowed
all_tools_allowed if {
    # Logic to check if all tools are allowed
    tools_in_plan := [step.tool | step := input.plan.steps[_]]
    not_allowed := [tool | tool := tools_in_plan[_]; not tool in object.keys(allowed_tools)]
    count(not_allowed) == 0
}

# Define violations
violations[result] {
    # Logic to detect violations
    step := input.plan.steps[_]
    step.tool == "payments.transfer"
    amount := to_number(step.parameters.amount)
    
    # Check if the amount exceeds the maximum allowed
    max_amount := allowed_tools["payments.transfer"].max_amount
    amount > max_amount
    
    # Return a violation result
    result := {
        "rule": "excessive_amount",
        "message": sprintf("Amount %f exceeds maximum allowed %f", [amount, max_amount]),
        "severity": "high",
        "category": "security",
        "step_id": step.id
    }
}

# Calculate risk score based on violations
risk_score = total {
    violation_scores := [violation.risk_score | violation := violations[_]]
    total := sum(violation_scores)
}
```

### Input Structure

In your Rego policies, you have access to the plan via the `input` document:

```rego
input.plan.steps      # Array of plan steps
input.plan.goal       # Plan goal (if provided)
input.plan.context    # Plan context (if provided)
input.context         # Additional context provided during validation
```

### Example Rego Policy

Here's a more complete example of a Rego policy for Plan-Lint:

```rego
package planlint

import future.keywords.in

# Default deny policy
default allow = false
default violations = []
default risk_score = 0.0

# Set of allowed tools with constraints
allowed_tools = {
    "db.query_ro": {},
    "db.query": {"max_joins": 3},
    "payments.transfer": {"min_amount": 0.01, "max_amount": 10000},
    "notify.email": {"max_recipients": 100},
    "analytics.summarize": {}
}

# Allow rule - defines when a plan should be allowed
allow if {
    all_tools_allowed
    risk_score < 0.8
}

# Check if all tools in the plan are allowed
all_tools_allowed if {
    tools_in_plan := [step.tool | step := input.plan.steps[_]]
    not_allowed := [tool | tool := tools_in_plan[_]; not tool in object.keys(allowed_tools)]
    count(not_allowed) == 0
}

# Collect all violations
violations = all_violations {
    all_violations := array.concat(
        sql_injection_violations,
        excessive_amount_violations,
        sensitive_data_violations
    )
}

# Detect SQL injection vulnerabilities
sql_injection_violations[result] {
    step := input.plan.steps[_]
    step.tool in ["db.query", "db.query_ro"]
    
    # SQL injection patterns
    patterns := ["'--", "1=1", "'; DROP", "OR 1=1"]
    
    # Check if query contains any dangerous patterns
    query := lower(step.parameters.query)
    some pattern in patterns
    contains(query, pattern)
    
    result := {
        "rule": "sql_injection",
        "message": sprintf("Potential SQL injection detected in query: %s", [pattern]),
        "severity": "high",
        "category": "security",
        "step_id": step.id,
        "risk_score": 0.8
    }
}

# Detect excessive transaction amounts
excessive_amount_violations[result] {
    step := input.plan.steps[_]
    step.tool == "payments.transfer"
    
    amount := to_number(step.parameters.amount)
    max_amount := allowed_tools["payments.transfer"].max_amount
    amount > max_amount
    
    result := {
        "rule": "excessive_amount",
        "message": sprintf("Transaction amount %f exceeds maximum allowed %f", [amount, max_amount]),
        "severity": "high",
        "category": "security",
        "step_id": step.id,
        "risk_score": 0.6
    }
}

# Detect sensitive data exposure
sensitive_data_violations[result] {
    step := input.plan.steps[_]
    
    # Look for sensitive parameter names
    sensitive_patterns := ["password", "secret", "token", "key", "credential"]
    some param_name, param_value in step.parameters
    
    some pattern in sensitive_patterns
    contains(lower(param_name), pattern)
    
    result := {
        "rule": "sensitive_data_exposure",
        "message": sprintf("Step contains sensitive parameter '%s'", [param_name]),
        "severity": "medium",
        "category": "privacy",
        "step_id": step.id,
        "risk_score": 0.5
    }
}

# Calculate risk score based on violations
risk_score = total {
    violation_scores := [v.risk_score | v := violations[_]]
    total := sum(violation_scores)
}
```

### Loading a Rego Policy

```python
from plan_lint import validate_plan
from plan_lint.loader import load_policy

# Load the Rego policy
policy_path = "path/to/policy.rego"
_, rego_policy = load_policy(policy_path)

# Validate a plan against the Rego policy
result = validate_plan(plan, rego_policy=rego_policy, use_opa=True)
```

## Choosing a Policy Format

Here's a comparison to help you choose the right policy format:

| Feature | YAML Policies | Rego Policies |
|---------|--------------|---------------|
| **Ease of Use** | Simple to write and understand | More complex but powerful |
| **Flexibility** | Limited to predefined rules | Unlimited flexibility |
| **Logic Complexity** | Basic constraints | Complex logical expressions |
| **Custom Rules** | Limited to existing rule types | Custom rule definition |
| **Use Case** | Simple security rules | Complex security policies |

## Best Practices

1. **Start Simple**: Begin with YAML policies for basic validation needs.
2. **Modular Policies**: Split complex Rego policies into logical modules.
3. **Test Thoroughly**: Test policies against both valid and invalid plans.
4. **Clear Messages**: Write clear violation messages to help users understand issues.
5. **Progressive Enhancement**: Gradually add more sophisticated rules as needed.
6. **Severity Levels**: Use consistent severity levels across policies.

## Converting Between Formats

Plan-Lint provides utilities to convert between YAML and Rego formats:

```python
from plan_lint.converter import yaml_to_rego

# Convert a YAML policy to Rego
yaml_policy_path = "path/to/policy.yaml"
rego_policy = yaml_to_rego(yaml_policy_path)

# Save the Rego policy
with open("policy.rego", "w") as f:
    f.write(rego_policy)
```

This allows you to start with a simpler YAML policy and convert it to Rego when you need more complex validation logic.
