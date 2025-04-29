---
title: Plan-Lint SDK 
---

# Plan-Lint SDK

<div class="grid cards" markdown>

- :material-shield-check:{ .lg .middle } __Validate LLM Agent Plans__

    ---

    Static analysis toolkit for checking and validating agent plans before they execute.

    [:octicons-arrow-right-24: Getting started](#getting-started)

- :material-notebook-edit:{ .lg .middle } __Policy Authoring__

    ---

    Learn to write Rego policies that define security boundaries for your agents.

    [:octicons-arrow-right-24: Policy guide](documentation/policy-authoring-guide.md)

- :material-certificate:{ .lg .middle } __MCP Integration__

    ---

    Integrate plan-lint with MCP servers for enhanced security.

    [:octicons-arrow-right-24: MCP Integration](documentation/mcp-integration.md)

- :material-code-braces:{ .lg .middle } __API Reference__

    ---

    Comprehensive API documentation for plan-lint.

    [:octicons-arrow-right-24: API Reference](api/index.md)

</div>

## What is Plan-Lint?

Plan-Lint is a static analysis toolkit for validating LLM agent plans before execution. It provides a robust security layer that can prevent harmful actions, detect suspicious patterns, and enforce authorization policies - all before any code executes.

```python
from plan_lint import validate_plan

# Your agent generates a plan
plan = agent.generate_plan(user_query)

# Validate the plan against your policies
validation_result = validate_plan(plan, policies=["policies/security.rego"])

if validation_result.valid:
    # Execute the plan only if it passed validation
    agent.execute_plan(plan)
else:
    # Handle validation failure
    print(f"Plan validation failed: {validation_result.violations}")
```

## Getting Started

### Installation

```bash
pip install plan-lint
```

### Basic Usage

```python
from plan_lint import validate_plan

# Validate a plan against security policies
result = validate_plan(
    plan_data,
    policies=["path/to/policies/security.rego"]
)

if result.valid:
    print("Plan is valid")
else:
    print(f"Plan validation failed with {len(result.violations)} violations:")
    for violation in result.violations:
        print(f" - {violation.message}")
```

## Key Features

- **Static Analysis**: Validate plans before execution to prevent security issues
- **Rego Policies**: Use OPA's Rego language to define flexible, powerful policies
- **Integration**: Works with OpenAI, Anthropic, and custom agent frameworks
- **MCP Support**: Integrates with MCP servers for OAuth-aware policy enforcement
- **Custom Rules**: Define your own security policies based on your specific needs

## Examples

Check out our [examples](examples/index.md) to see Plan-Lint in action. 