# Finance Agent System

This example demonstrates using Plan-Lint to validate financial transaction plans.

## System Overview

The Finance Agent System is a multi-agent system designed for secure transaction processing. It consists of:

1. **Orchestrator Agent**: Coordinates the overall workflow
2. **Transaction Agent**: Processes financial transactions
3. **Analysis Agent**: Analyzes transaction patterns
4. **Plan Validator**: Validates operational plans before execution

## Security Concerns

Financial systems require rigorous security measures. Common vulnerabilities include:

- SQL injection in transaction queries
- Excessive transaction amounts
- Unauthorized access to accounts
- Sensitive data exposure in logs

## Sample Plan

Here's a sample financial transaction plan:

```json
{
  "goal": "Process customer refund",
  "steps": [
    {
      "id": "step1",
      "tool": "db.query_ro",
      "parameters": {
        "query": "SELECT account_balance FROM accounts WHERE id = ?",
        "params": ["ACC-123"]
      }
    },
    {
      "id": "step2",
      "tool": "payments.transfer",
      "parameters": {
        "from_account": "COMPANY-MAIN",
        "to_account": "ACC-123",
        "amount": 500.00,
        "reason": "Customer refund"
      },
      "depends_on": ["step1"]
    },
    {
      "id": "step3",
      "tool": "notify.email",
      "parameters": {
        "to": "customer@example.com",
        "subject": "Refund Processed",
        "body": "Your refund of $500.00 has been processed."
      },
      "depends_on": ["step2"]
    },
    {
      "id": "step4",
      "tool": "db.write",
      "parameters": {
        "query": "UPDATE refund_requests SET status = ? WHERE id = ?",
        "params": ["COMPLETED", "REQ-456"]
      },
      "depends_on": ["step2"]
    }
  ],
  "context": {
    "customer_id": "CUST-789",
    "request_id": "REQ-456",
    "refund_amount": 500.00
  }
}
```

## Validation Policy

Here's a YAML policy specifically designed for financial transactions:

```yaml
# finance_policy.yaml
allow_tools:
  - db.query_ro
  - db.write
  - payments.transfer.small
  - notify.email
  - audit.log

bounds:
  payments.transfer.small.amount: [0.01, 1000.00]
  
deny_tokens_regex:
  - "DROP TABLE"
  - "1=1"
  - "password"
  - "secret"
  - "apikey"

tool_patterns:
  payments.transfer.small:
    pattern: "payments.transfer"
    conditions:
      - "parameters.amount <= 1000.0"

risk_weights:
  sql_injection: 0.8
  sensitive_data_exposure: 0.7
  excessive_amount: 0.6
  unauthorized_tool: 0.9

fail_risk_threshold: 0.5
max_steps: 10
```

## Running Validation

To validate the finance plan against this policy:

```bash
plan-lint validate --plan finance_plan.json --policy finance_policy.yaml
```

## Handling Violations

Here are some common violations and how to address them:

### Excessive Transaction Amount

```
Violation: Parameter 'amount' value 5000.00 is outside bounds [0.01, 1000.00]
```

**Solution**: Break large transactions into smaller amounts or require additional authorization steps.

### SQL Injection Risk

```
Violation: Potential SQL injection detected in query
```

**Solution**: Always use parameterized queries with placeholders.

### Missing Audit Trail

```
Violation: Financial transaction missing corresponding audit logging step
```

**Solution**: Add an audit.log step after each financial transaction:

```json
{
  "id": "audit_step",
  "tool": "audit.log",
  "parameters": {
    "event": "REFUND_PROCESSED",
    "details": {
      "amount": 500.00,
      "accounts": {
        "from": "COMPANY-MAIN",
        "to": "ACC-123"
      }
    }
  },
  "depends_on": ["step2"]
}
```

## Integration with Agent System

In a production environment, the Plan Validator would be integrated directly into the agent workflow:

```python
from plan_lint import validate_plan
from plan_lint.loader import load_policy

# Load the finance policy
finance_policy, rego_policy = load_policy("finance_policy.yaml")

def validate_finance_plan(plan, context=None):
    """
    Validate a financial transaction plan before execution.
    
    Args:
        plan: The plan to validate
        context: Optional context information
        
    Returns:
        (is_valid, violations): Tuple of validation result and any violations
    """
    # Add additional context for validation
    if context is None:
        context = {}
    
    context["environment"] = "production"
    context["transaction_limits"] = {
        "standard": 1000.00,
        "premium": 5000.00
    }
    
    # Validate the plan
    result = validate_plan(plan, finance_policy, context=context)
    
    return result.valid, result.errors
```

By integrating Plan-Lint into your financial agent system, you can ensure that all plans are validated against security policies before execution, reducing the risk of financial fraud, data breaches, and operational errors.
