# SQL Injection Prevention

This example shows how Plan-Lint can detect and prevent SQL injection vulnerabilities.

## Understanding SQL Injection

SQL injection is a code injection technique that exploits vulnerabilities in applications that interact with databases. Attackers can insert malicious SQL code that can:

- Bypass authentication
- Access sensitive data
- Modify database content
- Delete database data
- Execute administrative operations

## Vulnerable Plan Example

Consider a plan with a potential SQL injection vulnerability:

```json
{
  "goal": "Retrieve user information",
  "steps": [
    {
      "id": "step1",
      "tool": "db.query",
      "parameters": {
        "query": "SELECT * FROM users WHERE username = '" + user_input + "'"
      }
    },
    {
      "id": "step2",
      "tool": "notify.email",
      "parameters": {
        "to": "admin@example.com",
        "subject": "User Query Results",
        "body": "Query results: {{step1.result}}"
      },
      "depends_on": ["step1"]
    }
  ]
}
```

In this example, the user input is directly concatenated into the SQL query, creating a vulnerability. If a malicious user provides input like `admin' OR '1'='1`, the query becomes:

```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1'
```

This would return all users in the database, potentially exposing sensitive information.

## Detection with Plan-Lint

Plan-Lint can detect potential SQL injection vulnerabilities in plans. To validate the plan:

```bash
plan-lint validate --plan vulnerable_query_plan.json
```

Plan-Lint would produce output similar to:

```
Validation Results:
✘ Plan validation failed with 1 violation

Violations:
- [HIGH] sql_injection: Potential SQL injection detected in query (step: step1)
  SQL query contains string concatenation patterns which is a common indicator of SQL injection vulnerability
```

## SQL Injection Policy

A policy to detect SQL injection might look like this:

```yaml
# sql_security_policy.yaml
allow_tools:
  - db.query
  - db.query_ro
  - notify.email
  
deny_tokens_regex:
  - "'.*--"
  - "1=1"
  - "'; DROP"
  - "'.*OR.*'.*=.*'"
  - "'.*AND.*'.*=.*'"
  
risk_weights:
  sql_injection: 0.9
  
fail_risk_threshold: 0.3
```

## Fixed Plan Example

A safer version of the plan would use parameterized queries:

```json
{
  "goal": "Retrieve user information",
  "steps": [
    {
      "id": "step1",
      "tool": "db.query",
      "parameters": {
        "query": "SELECT * FROM users WHERE username = ?",
        "params": [user_input]
      }
    },
    {
      "id": "step2",
      "tool": "notify.email",
      "parameters": {
        "to": "admin@example.com",
        "subject": "User Query Results",
        "body": "Query results: {{step1.result}}"
      },
      "depends_on": ["step1"]
    }
  ]
}
```

In this fixed example:

1. User input is provided as a parameter rather than being concatenated into the query
2. The database driver handles proper escaping of the input
3. The query structure remains constant regardless of input values

## Advanced SQL Injection Prevention

### Using Prepared Statements

For more complex queries, use prepared statements with named parameters:

```json
{
  "id": "step1",
  "tool": "db.query",
  "parameters": {
    "query": "SELECT * FROM users WHERE username = :username AND status = :status",
    "params": {
      "username": user_input,
      "status": "active"
    }
  }
}
```

### Custom Validation Rules

You can create custom SQL validation rules for specific database systems:

```python
from typing import List
from plan_lint.types import Plan, PlanError, ErrorCode

def check_sql_patterns(plan: Plan) -> List[PlanError]:
    """Check for problematic SQL patterns specific to your database."""
    errors = []
    
    for i, step in enumerate(plan.steps):
        if step.tool.startswith("db."):
            query = step.parameters.get("query", "")
            
            # Check for database-specific issues
            if "INFORMATION_SCHEMA" in query:
                errors.append(
                    PlanError(
                        step=i,
                        code=ErrorCode.CUSTOM,
                        msg="Query attempts to access system tables"
                    )
                )
            
            # Check for unparameterized LIKE queries
            if "LIKE '%" in query:
                errors.append(
                    PlanError(
                        step=i,
                        code=ErrorCode.CUSTOM,
                        msg="LIKE statements should use parameters for pattern values"
                    )
                )
    
    return errors
```

## Integration with Data Access Layer

For production systems, consider implementing a data access layer that enforces parameterized queries:

```python
from plan_lint import validate_plan
from plan_lint.types import Plan, PlanStep

def create_db_query_step(query: str, params: list) -> PlanStep:
    """
    Create a safe database query step that enforces parameterization.
    
    Args:
        query: SQL query with parameter placeholders
        params: List of parameter values
        
    Returns:
        A safe PlanStep for database queries
    """
    # Validate that the query uses parameters
    if "?" not in query and ":" not in query:
        raise ValueError("Query must use parameterized format")
    
    return PlanStep(
        id="db_query",
        tool="db.query_ro",
        parameters={
            "query": query,
            "params": params
        }
    )
```

By using Plan-Lint to validate database operations in your agent plans, you can significantly reduce the risk of SQL injection vulnerabilities and maintain a more secure system.
