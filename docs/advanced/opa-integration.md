# OPA Integration

This page explains how to integrate Plan-Lint with the Open Policy Agent (OPA) for advanced policy enforcement.

## What is OPA?

[Open Policy Agent (OPA)](https://www.openpolicyagent.org/) is an open-source, general-purpose policy engine that enables unified policy enforcement across the stack. OPA provides a high-level declarative language called Rego for expressing policies.

Plan-Lint leverages OPA to provide powerful policy validation capabilities for agent plans.

## Benefits of OPA Integration

Integrating Plan-Lint with OPA offers several advantages:

1. **Powerful Policy Expression**: Rego is a purpose-built language for policy that can express complex validation rules
2. **Separation of Concerns**: Keep policy logic separate from your application code
3. **Consistent Enforcement**: Apply the same policies across different environments and systems
4. **Scalability**: OPA is designed for high-performance policy evaluation
5. **Ecosystem**: Benefit from OPA's tooling, documentation, and community

## Setup OPA for Plan-Lint

To use OPA with Plan-Lint, you need to install OPA:

### Local Installation

```bash
# Download OPA binary
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x opa
sudo mv opa /usr/local/bin/

# Verify the installation
opa version
```

### Docker Installation

```bash
docker pull openpolicyagent/opa:latest
```

### Python OPA Client Installation

Plan-Lint includes the necessary OPA client, but if you want to use it directly:

```bash
pip install opa-python
```

## Writing Rego Policies for Plan-Lint

Rego policies for Plan-Lint should be organized under the `planlint` package.

### Basic Policy Structure

```rego
# basic.rego
package planlint

import future.keywords.in

# Default deny
default allow = false

# Allow if no violations found
allow {
    count(violations) == 0
}

# Define violations
violations[result] {
    # Get a step from the plan
    step := input.plan.steps[_]
    
    # Example validation: Check if tool is allowed
    not step.tool in ["db.query_ro", "notify.email"]
    
    # Create a violation result
    result := {
        "rule": "unauthorized_tool",
        "message": sprintf("Tool '%s' is not allowed", [step.tool]),
        "severity": "high",
        "step_id": step.id
    }
}
```

### Input Structure

When Plan-Lint sends a plan to OPA for validation, it provides the following input structure:

```json
{
  "plan": {
    "goal": "Plan goal",
    "steps": [
      {
        "id": "step1",
        "tool": "db.query_ro",
        "parameters": {...}
      },
      ...
    ],
    "context": {...}
  },
  "context": {
    // Additional context provided during validation
    "user_role": "admin",
    "environment": "production",
    ...
  }
}
```

### Accessing Plan Data in Rego

```rego
# Access plan steps
step := input.plan.steps[_]

# Access step parameters
query := step.parameters.query

# Access plan context
user_role := input.context.user_role
```

## Using OPA with Plan-Lint

### Command Line

To validate a plan with a Rego policy:

```bash
plan-lint validate --plan plan.json --policy policy.rego --use-opa
```

### Programmatic Usage

```python
from plan_lint import validate_plan
from plan_lint.loader import load_plan, load_policy

# Load plan and policy
plan = load_plan("plan.json")
policy, rego_policy = load_policy("policy.rego")

# Validate with OPA
result = validate_plan(
    plan,
    policy,
    rego_policy=rego_policy,
    use_opa=True,
    context={"user_role": "admin"}
)
```

## Advanced Rego Policy Examples

### Role-Based Access Control

```rego
package planlint

import future.keywords.in

# Define role permissions
role_permissions := {
    "admin": {
        "db.query": true,
        "db.write": true,
        "payments.transfer": true,
        "system.configure": true
    },
    "operator": {
        "db.query": true,
        "db.query_ro": true,
        "payments.transfer": true
    },
    "viewer": {
        "db.query_ro": true
    }
}

# Tool permission check
violations[result] {
    # Get user role
    role := input.context.user_role
    
    # Get step
    step := input.plan.steps[i]
    
    # Get permissions for this role
    permissions := role_permissions[role]
    
    # Check if tool is allowed
    not step.tool in keys(permissions)
    
    result := {
        "rule": "role_authorization",
        "message": sprintf("User with role '%s' is not authorized to use tool '%s'", [role, step.tool]),
        "severity": "high",
        "step_id": step.id
    }
}
```

### Dependency Validation

```rego
package planlint

# Validate step dependencies
violations[result] {
    # Get step with dependencies
    step := input.plan.steps[i]
    step.depends_on
    
    # Check if any dependency is missing
    some dep in step.depends_on
    
    # Get all step IDs
    step_ids := {s.id | s := input.plan.steps[_]}
    
    # Check if dependency exists
    not dep in step_ids
    
    result := {
        "rule": "missing_dependency",
        "message": sprintf("Step '%s' depends on non-existent step '%s'", [step.id, dep]),
        "severity": "high",
        "step_id": step.id
    }
}

# Detect circular dependencies
violations[result] {
    # Get a step
    step := input.plan.steps[i]
    
    # Check if it depends on itself (directly or indirectly)
    depends_on_self(step.id, step.depends_on)
    
    result := {
        "rule": "circular_dependency",
        "message": sprintf("Step '%s' has a circular dependency", [step.id]),
        "severity": "high",
        "step_id": step.id
    }
}

# Helper function to check for circular dependencies
depends_on_self(id, deps) {
    # Direct dependency
    id in deps
} else {
    # Indirect dependency
    some dep in deps
    some step in input.plan.steps
    step.id == dep
    step.depends_on
    depends_on_self(id, step.depends_on)
}
```

### Complex Data Validation

```rego
package planlint

# Validate that email notifications match transaction recipients
violations[result] {
    # Find payment steps
    payment_step := input.plan.steps[i]
    payment_step.tool == "payments.transfer"
    recipient_account := payment_step.parameters.to_account
    
    # Find email notification steps that depend on this payment
    notification_steps := [step |
        step := input.plan.steps[_];
        step.tool == "notify.email";
        payment_step.id in step.depends_on
    ]
    
    # Check if we have at least one notification
    count(notification_steps) > 0
    
    # Check if we have recipient account info in context
    account_info := [account |
        account := input.context.accounts[_];
        account.account_number == recipient_account
    ]
    
    count(account_info) > 0
    recipient_email := account_info[0].email
    
    # Check if any notification is sent to the account owner
    not any([
        step.parameters.to == recipient_email |
        step := notification_steps[_]
    ])
    
    result := {
        "rule": "missing_recipient_notification",
        "message": sprintf("No notification sent to account owner of %s", [recipient_account]),
        "severity": "medium",
        "step_id": payment_step.id
    }
}
```

## Testing Rego Policies

OPA provides tools for testing your policies. Create a `test` directory with test cases:

```
policies/
  security.rego
  rbac.rego
test/
  security_test.rego
  rbac_test.rego
```

### Example Test

```rego
# test/security_test.rego
package planlint.test

import data.planlint

test_sql_injection {
    # Test input
    input := {
        "plan": {
            "steps": [
                {
                    "id": "step1",
                    "tool": "db.query",
                    "parameters": {
                        "query": "SELECT * FROM users WHERE username = 'admin' OR 1=1"
                    }
                }
            ]
        }
    }
    
    # Expected violations
    violations := planlint.violations with input as input
    count(violations) == 1
    violations[_].rule == "sql_injection"
}
```

### Running Tests

```bash
opa test -v policies/ test/
```

## OPA HTTP API Service

You can also run OPA as a service and have Plan-Lint communicate with it via HTTP:

### Start OPA Server

```bash
opa run --server --addr :8181 policies/
```

### Configure Plan-Lint to Use OPA Server

```python
from plan_lint import validate_plan
from plan_lint.opa import OPAClient

# Create OPA client
opa_client = OPAClient(url="http://localhost:8181")

# Validate with remote OPA
result = validate_plan(
    plan,
    policy,
    opa_client=opa_client,
    context={"user_role": "admin"}
)
```

## Performance Considerations

- **Policy Indexing**: Use indexing in Rego to improve performance
- **Batching**: For bulk validation, use batch requests to OPA
- **Local OPA**: For performance-critical applications, use the embedded OPA mode

## Integration with OPA Bundle Server

For enterprise environments, you can use OPA's bundle feature to distribute policies:

```bash
# Start OPA with bundle server
opa run --server --addr :8181 --bundle https://example.com/bundles/planlint
```

This allows centralized policy management and updates without requiring changes to your application code.

By leveraging OPA with Plan-Lint, you can implement sophisticated policy validation for your agent plans that goes well beyond the built-in capabilities, while maintaining a clean separation between your policy logic and application code.
