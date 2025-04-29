# Plan Structure

This page explains the structure of plans that can be validated by Plan-Lint.

## Overview

A plan in Plan-Lint represents a sequence of steps that an AI agent intends to execute. The plan is structured as a JSON object with specific fields that allow Plan-Lint to analyze it for potential security and operational issues.

## Plan Format

Plans are represented as JSON objects with the following structure:

```json
{
  "goal": "Human-readable description of what the plan aims to accomplish",
  "steps": [
    {
      "id": "unique-step-identifier",
      "tool": "tool_to_execute",
      "parameters": {
        "param1": "value1",
        "param2": "value2"
      },
      "on_fail": "abort",
      "depends_on": ["previous-step-id"]
    }
  ],
  "context": {
    "key1": "value1",
    "key2": "value2"
  },
  "meta": {
    "planner": "model-name",
    "created_at": "timestamp"
  }
}
```

### Required Fields

- **steps**: An array of execution steps that make up the plan (required)

### Optional Fields

- **goal**: A human-readable description of what the plan aims to accomplish
- **context**: Additional context information relevant to the plan
- **meta**: Metadata about the plan such as which model generated it

## Step Structure

Each step in the plan represents an individual action to be executed. Steps have the following structure:

```json
{
  "id": "step1",
  "tool": "tool_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "on_fail": "abort",
  "depends_on": ["step0"]
}
```

### Required Fields

- **id**: A unique identifier for the step (string)
- **tool**: The name of the tool or function to execute (string)
- **parameters**: An object containing the parameters for the tool execution (object)

### Optional Fields

- **on_fail**: What to do if this step fails (options: "abort", "continue")
- **depends_on**: Array of step IDs that must complete before this step can execute

## Parameter References

Parameters can reference the outputs of previous steps using the syntax `{{step_id.result}}` or `${step_id.result}`. For example:

```json
{
  "id": "step2",
  "tool": "send_email",
  "parameters": {
    "body": "The account balance is {{step1.result.balance}}",
    "to": "${step1.result.email}"
  },
  "depends_on": ["step1"]
}
```

This allows steps to use the outputs of previous steps as inputs, creating a workflow.

## Special Tool Patterns

Plan-Lint recognizes special patterns in the tool names to apply specific validations:

- **db.query**: Database query operations
- **db.query_ro**: Read-only database queries
- **db.write**: Database write operations
- **payments.**: Payment operations (e.g., `payments.transfer`)
- **notify.**: Notification operations (e.g., `notify.email`)
- **file.**: File operations

These patterns help Plan-Lint apply the appropriate security checks based on the type of operation.

## Example Plan

Here's a complete example of a plan that queries a database and sends an email:

```json
{
  "goal": "Send monthly account statement to user",
  "steps": [
    {
      "id": "step1",
      "tool": "db.query_ro",
      "parameters": {
        "query": "SELECT balance, email FROM accounts WHERE user_id = $1",
        "args": ["user-123"]
      }
    },
    {
      "id": "step2",
      "tool": "notify.email",
      "parameters": {
        "to": "{{step1.result.email}}",
        "subject": "Your Monthly Statement",
        "body": "Your current balance is ${{step1.result.balance}}"
      },
      "depends_on": ["step1"]
    }
  ],
  "context": {
    "user_id": "user-123",
    "month": "January 2025"
  },
  "meta": {
    "planner": "gpt-4o",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

## Best Practices

When working with plans, follow these best practices:

1. **Use Unique IDs**: Ensure each step has a unique ID.
2. **Explicit Dependencies**: Always specify step dependencies using the `depends_on` field.
3. **Minimal Permissions**: Use the most restrictive tool possible (e.g., `db.query_ro` instead of `db.query`).
4. **Parameter Sanitization**: Ensure user inputs are properly sanitized before including them in step parameters.
5. **Clear Goal Description**: Include a clear, human-readable goal to make the plan's purpose obvious.

## API Usage

Here's how to create and validate a plan using the Plan-Lint API:

```python
from plan_lint import validate_plan
from plan_lint.types import Plan, PlanStep

# Create a plan programmatically
plan = Plan(
    goal="Send notification to user",
    steps=[
        PlanStep(
            id="step1",
            tool="db.query_ro",
            parameters={
                "query": "SELECT email FROM users WHERE id = $1",
                "args": ["user-456"]
            }
        ),
        PlanStep(
            id="step2",
            tool="notify.email",
            parameters={
                "to": "{{step1.result.email}}",
                "subject": "Notification",
                "body": "This is a notification"
            },
            depends_on=["step1"]
        )
    ],
    context={"user_id": "user-456"}
)

# Validate the plan
result = validate_plan(plan)

if result.valid:
    print("Plan is valid!")
else:
    print("Plan validation failed:")
    for violation in result.violations:
        print(f"- {violation.rule}: {violation.message}")
```
