# Examples Overview

This section provides practical examples of using Plan-Lint to validate AI agent plans.

## Available Examples

Plan-Lint can be used in various scenarios to validate AI agent plans. We provide several examples to demonstrate its capabilities:

### [Finance Agent System](finance-agent-system.md)

This example demonstrates how to use Plan-Lint to validate financial transaction plans, including:

- Detecting excessive transaction amounts
- Validating proper account access
- Ensuring proper audit logging
- Preventing sensitive data exposure

### [SQL Injection Prevention](sql-injection.md)

Learn how Plan-Lint detects and prevents SQL injection vulnerabilities in database queries:

- Identifying vulnerable query patterns
- Using parameterized queries
- Creating custom SQL validation rules
- Integrating with data access layers

### [Custom Rules](custom-rules.md)

Discover how to extend Plan-Lint with custom validation rules for your specific needs:

- Creating Python validation functions
- Developing Rego policies
- Defining YAML rule patterns
- Integrating custom rules with CI/CD pipelines

## Using the Examples

Each example provides:

1. **Problem Description**: What security or operational issue is being addressed
2. **Vulnerable Plan**: An example of a problematic plan
3. **Validation Policy**: The Plan-Lint policy to detect the issue
4. **Fixed Plan**: A corrected version that addresses the vulnerability
5. **Integration Code**: How to integrate the validation into your systems

You can use these examples as templates for your own implementations or as learning resources to understand common validation patterns.

## Running the Examples

To run any of the examples, make sure you have Plan-Lint installed:

```bash
pip install plan-lint
```

Then, follow the specific instructions in each example page. Typically, you'll:

1. Save the example plan to a JSON file
2. Save the policy to a YAML or Rego file
3. Run the validation command
4. Examine the results

For example:

```bash
plan-lint validate --plan example_plan.json --policy example_policy.yaml
```

We encourage you to modify the examples to fit your specific use cases and experiment with different validation rules.
