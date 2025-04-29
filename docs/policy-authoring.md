# Policy Authoring Guide

This guide will help you create custom policies for Plan-Lint using the Rego policy language.

## Introduction to Rego

Plan-Lint uses [Rego](https://www.openpolicyagent.org/docs/latest/policy-language/), the policy language of Open Policy Agent (OPA), for defining validation rules. Rego is a declarative language specifically designed for expressing policies over complex data structures.

### Basic Rego Concepts

- **Rules**: Define conditions that should be met
- **Packages**: Group related rules together
- **Imports**: Include reusable functions or definitions
- **Variables**: Store intermediate values
- **Comprehensions**: Create collections by filtering and mapping

## Plan-Lint Policy Structure

### Package Naming

All Plan-Lint policies should be defined in the `planlint.custom` package:

```rego
package planlint.custom
```

### Basic Policy Format

A typical policy rule follows this pattern:

```rego
deny[result] {
    # Rule conditions
    # ...
    
    result := {
        "rule": "rule_name",
        "message": "Human-readable message explaining the violation",
        "severity": "high",  # "low", "medium", "high", or "critical"
        "category": "category_name",  # e.g., "security", "performance", etc.
        "step_id": "affected_step_id",
        "metadata": {
            # Additional information about the violation
        }
    }
}
```

### Available Input Data

In your policies, you have access to:

- `input.plan`: The full plan being validated
- `input.context`: Additional context data provided during validation

## Writing Your First Policy

Let's create a simple policy that detects file operations on sensitive paths:

```rego
package planlint.custom

import future.keywords.in

# Define sensitive paths
sensitive_paths := ["/etc/passwd", "/etc/shadow", "/var/log/auth.log"]

# Check if a file operation targets a sensitive path
deny[result] {
    some step in input.plan.steps
    step.tool == "file_operation"
    
    some path in sensitive_paths
    startswith(step.parameters.path, path)
    
    result := {
        "rule": "sensitive_path_access",
        "message": "Operation attempts to access a sensitive system path",
        "severity": "high",
        "category": "security",
        "step_id": step.id,
        "metadata": {
            "path": step.parameters.path,
            "operation": step.parameters.operation
        }
    }
}
```

## Advanced Policy Techniques

### Using Context Data

You can leverage context data to create more dynamic policies:

```rego
package planlint.custom

# Check if a requested permission exceeds user's role
deny[result] {
    some step in input.plan.steps
    step.tool == "request_permission"
    
    # Get user role from context
    user_role := input.context.user_role
    
    # Define allowed permissions per role
    allowed_permissions := {
        "user": ["read"],
        "editor": ["read", "write"],
        "admin": ["read", "write", "delete", "configure"]
    }
    
    # Check if requested permission is allowed for this role
    not step.parameters.permission in allowed_permissions[user_role]
    
    result := {
        "rule": "permission_exceeds_role",
        "message": sprintf("User with role '%s' cannot request '%s' permission", [user_role, step.parameters.permission]),
        "severity": "medium",
        "category": "access_control",
        "step_id": step.id,
        "metadata": {
            "requested_permission": step.parameters.permission,
            "user_role": user_role,
            "allowed_permissions": allowed_permissions[user_role]
        }
    }
}
```

### Step Dependencies Analysis

You can analyze dependencies between steps:

```rego
package planlint.custom

import future.keywords.in

# Detect when sensitive data is passed to network operations
deny[result] {
    # Find an authentication step
    some auth_step in input.plan.steps
    auth_step.tool == "authenticate"
    
    # Find a network request step
    some request_step in input.plan.steps
    request_step.tool == "http_request"
    
    # Check if auth data is referenced in request
    contains(request_step.parameters.url, sprintf("{{%s.result}}", [auth_step.id]))
    
    result := {
        "rule": "auth_data_in_url",
        "message": "Authentication data should not be included in URLs",
        "severity": "high",
        "category": "security",
        "step_id": request_step.id,
        "metadata": {
            "auth_step": auth_step.id,
            "url_parameter": request_step.parameters.url
        }
    }
}
```

## Using Rego Built-in Functions

Rego provides many [built-in functions](https://www.openpolicyagent.org/docs/latest/policy-reference/#built-in-functions) for processing data:

```rego
package planlint.custom

import future.keywords.in

# Check for excessively large array operations
deny[result] {
    some step in input.plan.steps
    step.tool == "process_array"
    
    # Convert to number if string
    array_size := to_number(step.parameters.size)
    
    # Check if exceeds threshold
    max_size := 10000
    array_size > max_size
    
    result := {
        "rule": "large_array_operation",
        "message": "Processing very large arrays can cause performance issues",
        "severity": "medium",
        "category": "performance",
        "step_id": step.id,
        "metadata": {
            "array_size": array_size,
            "max_recommended_size": max_size
        }
    }
}
```

## Pattern Matching and String Operations

Use pattern matching for detecting issues in string parameters:

```rego
package planlint.custom

import future.keywords.in

# Detect potential XSS vulnerabilities
deny[result] {
    some step in input.plan.steps
    step.tool == "render_html"
    
    # Look for common XSS patterns
    dangerous_patterns := [
        "<script>", 
        "javascript:", 
        "onerror=", 
        "onload="
    ]
    
    some pattern in dangerous_patterns
    contains(lower(step.parameters.content), pattern)
    
    result := {
        "rule": "potential_xss",
        "message": "HTML content contains potentially dangerous scripts",
        "severity": "critical",
        "category": "security",
        "step_id": step.id,
        "metadata": {
            "detected_pattern": pattern
        }
    }
}
```

## Testing Your Policies

It's important to test policies with both valid and invalid plans:

```rego
package planlint.test

import data.planlint.custom

# Test case for sensitive path access policy
test_sensitive_path_access {
    # Define test plan with violation
    plan := {
        "steps": [
            {
                "id": "step1",
                "tool": "file_operation",
                "parameters": {
                    "operation": "read",
                    "path": "/etc/passwd"
                }
            }
        ]
    }
    
    # Run the policy
    violations := custom.deny with input as {"plan": plan}
    
    # Check that a violation was detected
    count(violations) == 1
    violations[_].rule == "sensitive_path_access"
}

# Test case for safe path
test_safe_path {
    # Define test plan without violation
    plan := {
        "steps": [
            {
                "id": "step1",
                "tool": "file_operation",
                "parameters": {
                    "operation": "read",
                    "path": "/tmp/safe_file.txt"
                }
            }
        ]
    }
    
    # Run the policy
    violations := custom.deny with input as {"plan": plan}
    
    # Check that no violations were detected
    count(violations) == 0
}
```

To run these tests:

```bash
plan-lint test --policies your_policy.rego
```

## Organizing Multiple Policies

For larger projects, organize policies into themes:

```
policies/
  ├── security/
  │   ├── injection.rego
  │   ├── access_control.rego
  │   └── data_exposure.rego
  ├── performance/
  │   ├── resource_limits.rego
  │   └── efficiency.rego
  └── reliability/
      ├── error_handling.rego
      └── retries.rego
```

## Common Patterns for Plan-Lint Policies

### Detecting Dangerous Operations

```rego
package planlint.custom

import future.keywords.in

# List of dangerous system commands
dangerous_commands := [
    "rm -rf", 
    "dd if=", 
    "mkfs", 
    "> /dev/",
    ":(){ :|:& };:"  # Fork bomb
]

# Detect dangerous system commands
deny[result] {
    some step in input.plan.steps
    step.tool == "execute_command"
    
    some cmd in dangerous_commands
    contains(step.parameters.command, cmd)
    
    result := {
        "rule": "dangerous_system_command",
        "message": "Plan contains a potentially destructive system command",
        "severity": "critical",
        "category": "security",
        "step_id": step.id,
        "metadata": {
            "command": step.parameters.command,
            "detected_pattern": cmd
        }
    }
}
```

### Enforcing Tool Constraints

```rego
package planlint.custom

import future.keywords.in

# Limit the number of API calls in a plan
deny[result] {
    api_steps := [step | some step in input.plan.steps; step.tool == "api_call"]
    count(api_steps) > 5
    
    result := {
        "rule": "too_many_api_calls",
        "message": "Plan contains too many API calls which may lead to rate limiting",
        "severity": "medium",
        "category": "reliability",
        "step_id": api_steps[0].id,  # Reference the first API call
        "metadata": {
            "api_call_count": count(api_steps),
            "max_recommended": 5
        }
    }
}
```

### Contextual Validation

```rego
package planlint.custom

import future.keywords.in

# Validate operations based on business hours
deny[result] {
    # Only apply this rule if business_hours context is provided
    input.context.business_hours
    
    some step in input.plan.steps
    step.tool == "schedule_maintenance"
    
    # Convert maintenance time to number for comparison
    maintenance_hour := to_number(step.parameters.hour)
    
    # Check if maintenance is scheduled during business hours
    maintenance_hour >= input.context.business_hours.start
    maintenance_hour < input.context.business_hours.end
    
    result := {
        "rule": "maintenance_during_business_hours",
        "message": "Maintenance should be scheduled outside of business hours",
        "severity": "medium",
        "category": "operational",
        "step_id": step.id,
        "metadata": {
            "scheduled_hour": maintenance_hour,
            "business_hours": sprintf("%d-%d", [input.context.business_hours.start, input.context.business_hours.end])
        }
    }
}
```

## Best Practices

1. **Be Specific**: Target policies to specific tools or operations
2. **Use Severity Levels Consistently**: Follow these guidelines:
   - `critical`: Issues that must be fixed immediately
   - `high`: Significant security or reliability concerns
   - `medium`: Important but not critical issues
   - `low`: Minor concerns or best practice suggestions
3. **Include Helpful Messages**: Make policy violation messages actionable and clear
4. **Add Metadata**: Include relevant data to help developers understand and fix issues
5. **Test Thoroughly**: Create test cases for both compliant and non-compliant plans
6. **Consider Performance**: Complex policies might slow down validation; optimize when necessary

## Debugging Policies

When your policy isn't working as expected:

1. Use the `--debug` flag when running `plan-lint`:
   ```bash
   plan-lint validate --plan my_plan.json --policies my_policy.rego --debug
   ```

2. Add print statements for debugging:
   ```rego
   deny[result] {
       # ...
       print("Checking step:", step.id)
       print("Parameter value:", step.parameters.value)
       # ...
   }
   ```

3. Break down complex policies into smaller ones to isolate issues

## Policy Version Control

For maintainable policies:

1. Add headers with version and author information:
   ```rego
   # Policy: prevent_sensitive_data_exposure
   # Version: 1.2
   # Author: Security Team
   # Last Updated: 2023-10-15
   # Description: Prevents exposure of sensitive data in logs and external services
   package planlint.custom
   ```

2. Add comments explaining the rationale behind policy decisions

3. Consider using meaningful file names that describe the policy's purpose

## Example: Rate Limiting Policy

Complete policy example for enforcing API rate limits:

```rego
package planlint.custom

import future.keywords.in

# Rate limiting policy for API calls
# Checks that the same API endpoint isn't called too frequently within a plan

# Configuration
default max_calls_per_endpoint = 3

# Get customized limit from context if available
max_calls_per_endpoint = limit {
    limit := input.context.api_rate_limits.max_calls_per_endpoint
}

# Group API calls by endpoint
api_calls_by_endpoint[endpoint] = calls {
    # Collect all API call steps
    api_steps := [step | some step in input.plan.steps; step.tool == "api_call"]
    
    # Group by endpoint
    endpoints := {endpoint | some step in api_steps; endpoint := step.parameters.endpoint}
    
    # For each endpoint, collect all steps that call it
    some endpoint in endpoints
    calls := [step | some step in api_steps; step.parameters.endpoint == endpoint]
}

# Detect rate limit violations
deny[result] {
    some endpoint, calls in api_calls_by_endpoint
    count(calls) > max_calls_per_endpoint
    
    result := {
        "rule": "api_rate_limit_exceeded",
        "message": sprintf("Too many calls to API endpoint '%s'", [endpoint]),
        "severity": "medium",
        "category": "reliability",
        "step_id": calls[0].id,  # Reference the first call to this endpoint
        "metadata": {
            "endpoint": endpoint,
            "call_count": count(calls),
            "max_allowed": max_calls_per_endpoint,
            "all_calls": [step.id | some step in calls]
        }
    }
}
```

## Conclusion

Creating effective policies is an iterative process. Start with simple rules and gradually build more complex validation logic as your understanding of potential issues grows. Remember that policies should balance security with usability - overly strict policies might frustrate users and lead to workarounds.

For more examples and inspiration, check out the default policies included with Plan-Lint and the examples in the Plan-Lint documentation. 