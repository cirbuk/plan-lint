# Risk Scoring

This page explains how Plan-Lint calculates risk scores for plans.

## Overview

Plan-Lint uses a risk scoring system to quantify the potential security and operational risks in a plan. Rather than simply providing a binary pass/fail result, risk scoring allows for more nuanced evaluation and helps prioritize concerns.

## Risk Score Calculation

A risk score is a value between 0.0 and 1.0 that represents the overall risk level of a plan:

- **0.0**: No risk detected
- **1.0**: Maximum risk level

The risk score is calculated by aggregating the individual risk scores of all detected violations in a plan.

### Basic Algorithm

In its simplest form, the risk score calculation follows these steps:

1. Assign a risk weight to each type of violation
2. Detect all violations in the plan
3. Sum the risk weights of all detected violations
4. Cap the total at 1.0 (if it exceeds 1.0)

### Example Calculation

Consider a plan with the following violations:

- SQL injection detected (risk weight: 0.6)
- Excessive transaction amount (risk weight: 0.4)
- Sensitive data exposure (risk weight: 0.5)

The total risk score would be: 0.6 + 0.4 + 0.5 = 1.5, but since risk scores are capped at 1.0, the final risk score would be 1.0.

## Risk Weights

Each type of violation is assigned a risk weight based on its potential security impact. Default risk weights include:

| Violation Type | Default Risk Weight |
|----------------|---------------------|
| SQL Injection | 0.6 |
| Sensitive Data Exposure | 0.5 |
| Excessive Transaction Amount | 0.4 |
| Unauthorized Tool Use | 0.9 |
| Parameter Bounds Violation | 0.3 |
| Too Many Steps | 0.2 |

### Customizing Risk Weights

You can customize risk weights in your YAML policy:

```yaml
risk_weights:
  sql_injection: 0.7       # Increase SQL injection weight
  sensitive_data: 0.6      # Increase sensitive data weight
  excessive_amount: 0.3    # Decrease excessive amount weight
  unauthorized_tool: 1.0   # Maximum weight for unauthorized tools
```

In Rego policies, risk weights are defined within the violation result:

```rego
violations[result] {
    # Violation logic
    
    result := {
        "rule": "sql_injection",
        "message": "SQL injection detected",
        "severity": "high",
        "category": "security",
        "step_id": step.id,
        "risk_score": 0.7  # Custom risk weight
    }
}
```

## Risk Thresholds

Plans are considered valid if their risk score is below a configured threshold. The default threshold is 0.8, but you can customize it in your policy:

### In YAML:

```yaml
fail_risk_threshold: 0.5  # More strict threshold
```

### In Rego:

```rego
# Allow rule - only allow plans with risk score below threshold
allow if {
    risk_score < 0.5  # Custom threshold
}
```

## Severity Levels

Risk scores are related to severity levels, but they are different concepts:

- **Risk Score**: A numerical value representing the overall risk (0.0 to 1.0)
- **Severity Level**: A categorical label for individual violations (low, medium, high, critical)

The mapping between severity levels and risk weights is approximate:

| Severity Level | Typical Risk Weight Range |
|----------------|---------------------------|
| Low | 0.1 - 0.3 |
| Medium | 0.3 - 0.5 |
| High | 0.5 - 0.7 |
| Critical | 0.7 - 1.0 |

## Risk Categories

Violations are also categorized by the type of risk they represent:

- **Security**: Risks related to security vulnerabilities (e.g., SQL injection)
- **Privacy**: Risks related to data privacy (e.g., sensitive data exposure)
- **Authorization**: Risks related to access control (e.g., unauthorized tool use)
- **Operational**: Risks related to system operations (e.g., excessive transaction amount)
- **Compliance**: Risks related to regulatory compliance

These categories help organize and prioritize risks in complex systems.

## Weighted Risk Aggregation

For more complex risk scoring, Plan-Lint can use weighted aggregation methods:

### Maximum Risk

Instead of summing all risks, take the maximum risk score:

```rego
risk_score = max_score {
    violation_scores := [v.risk_score | v := violations[_]]
    max_score := max(violation_scores)
}
```

### Weighted Average

Calculate a weighted average based on severity:

```rego
risk_score = weighted_score {
    # Get all violations with their severity weights
    violation_data := [[v.risk_score, severity_weight(v.severity)] | v := violations[_]]
    
    # Calculate weighted sum
    weighted_sum := sum([score * weight | [score, weight] := violation_data])
    
    # Calculate total weight
    total_weight := sum([weight | [_, weight] := violation_data])
    
    # Weighted average
    weighted_score := weighted_sum / total_weight
}

# Helper function to convert severity to weight
severity_weight(severity) = weight {
    severity == "critical"
    weight := 4
} else = weight {
    severity == "high"
    weight := 3
} else = weight {
    severity == "medium"
    weight := 2
} else = weight {
    severity == "low"
    weight := 1
}
```

## Risk Score in Validation Results

When using the Plan-Lint API, the validation result includes the calculated risk score:

```python
from plan_lint import validate_plan

result = validate_plan(plan, policy=policy)

print(f"Risk score: {result.risk_score}")
print(f"Valid: {result.valid}")

if not result.valid:
    for violation in result.violations:
        print(f"- {violation.rule}: {violation.message} ({violation.severity})")
```

## Advanced Risk Scoring with Context

Risk scoring can incorporate additional context to provide more accurate results:

```rego
# Adjust risk based on environment
risk_score = adjusted_score {
    # Base score calculation
    violation_scores := [v.risk_score | v := violations[_]]
    base_score := sum(violation_scores)
    
    # Environment-based adjustment
    environment := input.context.environment
    
    # Higher risk in production
    adjustment := environment == "production" ? 1.2 : 1.0
    
    # Apply adjustment but cap at 1.0
    adjusted_score := min(base_score * adjustment, 1.0)
}
```

## Best Practices

1. **Align with Security Policy**: Risk weights should reflect your organization's security priorities.
2. **Consistent Scoring**: Use consistent risk weights across policies.
3. **Regular Review**: Review and update risk weights as your security posture evolves.
4. **Contextualize Risks**: Use context information to adjust risk scores for different environments or use cases.
5. **Test Thoroughly**: Validate your risk scoring logic with a variety of plans to ensure it reflects actual risk levels.
6. **Document Thresholds**: Document and explain your risk thresholds to users so they understand the validation criteria.

## Example Risk Scoring Implementation

Here's a complete example of a Rego policy with sophisticated risk scoring:

```rego
package planlint

import future.keywords.in

# Default settings
default allow = false
default violations = []
default risk_score = 0.0

# Risk category weights 
# (security issues weighted higher than operational issues)
category_weights = {
    "security": 1.5,
    "privacy": 1.3,
    "authorization": 1.2,
    "operational": 1.0,
    "compliance": 1.4
}

# Allow rule with customizable threshold
allow if {
    # Get threshold from context or use default
    threshold := object.get(input.context, "risk_threshold", 0.8)
    
    # Plan is valid if risk score is below threshold
    risk_score < threshold
}

# Calculate risk score with category weighting
risk_score = final_score {
    # Early return if no violations
    count(violations) == 0
    final_score := 0.0
} else = final_score {
    # Get scores with category weights applied
    weighted_scores := [
        v.risk_score * category_weights[v.category] |
        v := violations[_]
    ]
    
    # Sum weighted scores and cap at 1.0
    total := sum(weighted_scores)
    final_score := min(total, 1.0)
}

# Detect violations (omitted for brevity)
# ...
```

By using sophisticated risk scoring, Plan-Lint can provide more accurate and meaningful validation results, helping you make informed decisions about plan execution.
