# Rule Types

This page describes the different types of rules available in Plan-Lint.

## Overview

Plan-Lint offers a variety of rule types to validate different aspects of agent plans. These rules help ensure plans are secure, efficient, and compliant with your organization's policies before execution.

Rules are implemented as either built-in checks in the Plan-Lint core or as policy rules in YAML or Rego formats.

## Security Rules

Security rules focus on identifying potential security vulnerabilities in plans.

### SQL Injection Detection

Detects potential SQL injection vulnerabilities in database queries.

**YAML Configuration:**
```yaml
deny_tokens_regex:
  - "1=1"
  - "OR 1=1"
  - "DROP TABLE"
  - "--"
  - ";"
```

**Rego Implementation:**
```rego
violations[result] {
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
        "step_id": step.id
    }
}
```

### Sensitive Data Exposure

Identifies exposure of sensitive information like passwords, API keys, and tokens.

**YAML Configuration:**
```yaml
deny_tokens_regex:
  - "password"
  - "apikey"
  - "token"
  - "secret"
  - "credential"
```

**Rego Implementation:**
```rego
violations[result] {
    step := input.plan.steps[_]
    
    # Sensitive parameter patterns
    sensitive_patterns := ["password", "secret", "token", "key", "credential"]
    some param_name, param_value in step.parameters
    
    some pattern in sensitive_patterns
    contains(lower(param_name), pattern)
    
    result := {
        "rule": "sensitive_data_exposure",
        "message": sprintf("Step contains sensitive parameter '%s'", [param_name]),
        "severity": "high",
        "category": "privacy",
        "step_id": step.id
    }
}
```

### Command Injection

Detects potential command injection vulnerabilities in shell commands.

**YAML Configuration:**
```yaml
deny_tokens_regex:
  - "&&"
  - "||"
  - ";"
  - "`"
  - "\\$\\("  # Escape for regex
```

**Rego Implementation:**
```rego
violations[result] {
    step := input.plan.steps[_]
    step.tool == "execute_command"
    
    # Command injection patterns
    patterns := ["&&", "||", ";", "`", "$("]
    
    # Check if command contains any dangerous patterns
    command := step.parameters.command
    some pattern in patterns
    contains(command, pattern)
    
    result := {
        "rule": "command_injection",
        "message": sprintf("Potential command injection detected: %s", [pattern]),
        "severity": "critical",
        "category": "security",
        "step_id": step.id
    }
}
```

## Authorization Rules

Authorization rules validate that plans only use tools and resources they are authorized to use.

### Tool Authorization

Verifies that a plan only uses allowed tools.

**YAML Configuration:**
```yaml
allow_tools:
  - db.query_ro
  - payments.transfer
  - notify.email
```

**Rego Implementation:**
```rego
violations[result] {
    step := input.plan.steps[_]
    
    # List of allowed tools
    allowed_tools := {
        "db.query_ro": true,
        "payments.transfer": true,
        "notify.email": true
    }
    
    # Check if tool is not in allowed list
    not allowed_tools[step.tool]
    
    result := {
        "rule": "unauthorized_tool",
        "message": sprintf("Tool '%s' is not authorized", [step.tool]),
        "severity": "high",
        "category": "authorization",
        "step_id": step.id
    }
}
```

### Role-Based Access Control

Validates that plans only use tools appropriate for the user's role.

**Rego Implementation:**
```rego
violations[result] {
    # Get user role from context
    role := input.context.user_role
    
    # Role-specific allowed tools
    allowed_tools_by_role := {
        "admin": {"db.query", "db.write", "payments.transfer", "system.configure"},
        "editor": {"db.query", "payments.transfer"},
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
        "category": "authorization",
        "step_id": step.id
    }
}
```

## Operational Rules

Operational rules ensure that plans follow operational best practices and constraints.

### Parameter Boundaries

Enforces limits on parameter values, such as transaction amounts or query limits.

**YAML Configuration:**
```yaml
bounds:
  payments.transfer.amount: [0.01, 10000.00]
  db.query.limit: [1, 1000]
```

**Rego Implementation:**
```rego
violations[result] {
    step := input.plan.steps[_]
    step.tool == "payments.transfer"
    
    # Check amount boundaries
    amount := to_number(step.parameters.amount)
    min_amount := 0.01
    max_amount := 10000.00
    
    # Check if amount is outside boundaries
    amount < min_amount or amount > max_amount
    
    result := {
        "rule": "parameter_bounds",
        "message": sprintf("Amount %f is outside allowed range [%f, %f]", [amount, min_amount, max_amount]),
        "severity": "medium",
        "category": "operational",
        "step_id": step.id
    }
}
```

### Step Limit

Ensures that plans don't have too many steps, which could indicate complexity issues.

**YAML Configuration:**
```yaml
max_steps: 20
```

**Rego Implementation:**
```rego
violations[result] {
    # Count steps in plan
    step_count := count(input.plan.steps)
    
    # Maximum allowed steps
    max_steps := 20
    
    # Check if too many steps
    step_count > max_steps
    
    result := {
        "rule": "too_many_steps",
        "message": sprintf("Plan has %d steps, exceeding maximum of %d", [step_count, max_steps]),
        "severity": "low",
        "category": "operational",
        "step_id": input.plan.steps[0].id
    }
}
```

### Dependency Validation

Verifies that step dependencies are correctly configured.

**Rego Implementation:**
```rego
violations[result] {
    # Check each step with dependencies
    step := input.plan.steps[_]
    step.depends_on
    
    # Get all step IDs
    step_ids := {s.id | s := input.plan.steps[_]}
    
    # Check if any dependency is missing
    some dep in step.depends_on
    not dep in step_ids
    
    result := {
        "rule": "invalid_dependency",
        "message": sprintf("Step '%s' depends on non-existent step '%s'", [step.id, dep]),
        "severity": "medium",
        "category": "operational",
        "step_id": step.id
    }
}
```

## Compliance Rules

Compliance rules ensure that plans adhere to regulatory and organizational compliance requirements.

### Data Retention

Ensures that plans don't retain sensitive data longer than necessary.

**Rego Implementation:**
```rego
violations[result] {
    # Check for data storage steps
    step := input.plan.steps[_]
    step.tool in ["db.write", "file.write", "storage.save"]
    
    # Check if retention period is specified
    not step.parameters.retention_period
    
    # Check if data is sensitive
    some param_name, param_value in step.parameters
    contains(lower(param_name), "data")
    
    result := {
        "rule": "data_retention",
        "message": "Data storage operation missing retention period",
        "severity": "medium",
        "category": "compliance",
        "step_id": step.id
    }
}
```

### Audit Logging

Verifies that sensitive operations include appropriate audit logging.

**Rego Implementation:**
```rego
violations[result] {
    # Sensitive operations that require audit logging
    sensitive_tools := {"payments.transfer", "db.write", "user.create", "user.delete"}
    
    # Check each step
    step := input.plan.steps[_]
    step.tool in sensitive_tools
    
    # Check if there's an audit logging step that depends on this step
    audit_step_exists := some audit_step in input.plan.steps; 
        audit_step.tool == "audit.log" and 
        step.id in audit_step.depends_on
    
    not audit_step_exists
    
    result := {
        "rule": "missing_audit_logging",
        "message": sprintf("Sensitive operation '%s' is missing audit logging", [step.tool]),
        "severity": "medium",
        "category": "compliance",
        "step_id": step.id
    }
}
```

## Custom Rules

Plan-Lint allows you to define custom rules tailored to your specific needs.

### Custom Rego Rules

You can create custom rules by defining new violation detection logic in Rego:

```rego
# Custom rule to detect excessive API calls to the same endpoint
violations[result] {
    # Group steps by API endpoint
    api_steps := [step | step := input.plan.steps[_]; step.tool == "api.call"]
    endpoints := {endpoint | step := api_steps[_]; endpoint := step.parameters.endpoint}
    
    # Check each endpoint
    some endpoint in endpoints
    endpoint_steps := [step | step := api_steps[_]; step.parameters.endpoint == endpoint]
    
    # Check if too many calls to same endpoint
    count(endpoint_steps) > 5
    
    result := {
        "rule": "excessive_api_calls",
        "message": sprintf("Too many API calls (%d) to endpoint '%s'", [count(endpoint_steps), endpoint]),
        "severity": "medium",
        "category": "operational",
        "step_id": endpoint_steps[0].id
    }
}
```

### Custom Python Rules

For more complex rules, you can implement custom Python rules by extending the Plan-Lint API:

```python
from typing import List
from plan_lint.types import Plan, PlanError, ErrorCode

def check_resource_throttling(plan: Plan) -> List[PlanError]:
    """Custom rule to detect excessive resource usage."""
    errors = []
    
    # Group steps by resource type
    resource_usage = {}
    for i, step in enumerate(plan.steps):
        resource = step.tool.split('.')[0]
        if resource not in resource_usage:
            resource_usage[resource] = []
        resource_usage[resource].append(i)
    
    # Check for excessive usage of any resource
    for resource, steps in resource_usage.items():
        if len(steps) > 10:
            errors.append(
                PlanError(
                    step=steps[0],
                    code=ErrorCode.CUSTOM,
                    msg=f"Excessive use of resource '{resource}' ({len(steps)} steps)",
                )
            )
    
    return errors
```

## Rule Severity Levels

Plan-Lint uses several severity levels to indicate the importance of rule violations:

- **Critical**: Severe issues that must be addressed immediately (e.g., command injection)
- **High**: Significant security or operational concerns (e.g., SQL injection, sensitive data exposure)
- **Medium**: Important issues that should be addressed (e.g., parameter bounds violations)
- **Low**: Minor issues or best practice recommendations (e.g., too many steps)

## Creating Effective Rules

When creating rules for Plan-Lint, follow these best practices:

1. **Be Specific**: Target your rules to address specific security or operational concerns.
2. **Provide Clear Messages**: Ensure violation messages clearly explain the issue and how to fix it.
3. **Balance Security and Usability**: Overly restrictive rules can lead to workarounds or reduced adoption.
4. **Test Thoroughly**: Validate your rules against a variety of plans, both valid and invalid.
5. **Document**: Document your rules, including their purpose, severity, and potential remediation actions.

## Using Rules Effectively

To get the most out of Plan-Lint rules:

1. **Start with Built-in Rules**: Begin with Plan-Lint's built-in security and operational rules.
2. **Customize for Your Environment**: Adjust rule parameters to match your specific requirements.
3. **Layer Rules**: Combine different rule types to create comprehensive validation coverage.
4. **Regular Updates**: Review and update your rules as your security requirements evolve.
5. **Integrate with CI/CD**: Automate plan validation with your CI/CD pipeline to catch issues early.
