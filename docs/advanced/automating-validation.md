# Automating Validation

This page explains how to automate the validation of plans with Plan-Lint.

## Automation Methods

Plan-Lint offers several ways to automate plan validation:

1. **Command Line Interface (CLI)**: For batch processing or scripting
2. **Python API**: For programmatic integration
3. **Webhook Endpoints**: For event-driven validation
4. **Scheduled Jobs**: For periodic validation

## CLI Automation

The Plan-Lint CLI is designed for automation and can be easily integrated into shell scripts.

### Batch Processing

You can validate multiple plans with a single command:

```bash
# Validate all plans in a directory
plan-lint validate-batch --plans-dir ./plans/ --policy policy.yaml

# Process with glob patterns
plan-lint validate-batch --plans-pattern "./plans/**/*.json" --policy-dir ./policies/
```

### Exit Codes

Plan-Lint CLI returns meaningful exit codes for automation:

- `0`: All plans are valid (no violations found)
- `1`: At least one plan has violations
- `2`: Validation error (invalid input, missing policy, etc.)

### Generating Reports

```bash
# Generate JSON report
plan-lint validate --plan plan.json --policy policy.yaml --report-format json --output report.json

# Generate HTML report
plan-lint validate --plan plan.json --policy policy.yaml --report-format html --output report.html
```

## Python API Automation

Plan-Lint's Python API allows for deep integration into your applications.

### Basic Validation

```python
from plan_lint import validate_plan
from plan_lint.loader import load_plan, load_policy

# Load plan and policy
plan = load_plan("path/to/plan.json")
policy = load_policy("path/to/policy.yaml")

# Validate
result = validate_plan(plan, policy)

# Check result
if result.is_valid:
    print("Plan is valid!")
else:
    print(f"Plan has {len(result.violations)} violations")
    for violation in result.violations:
        print(f"- {violation.rule}: {violation.message}")
```

### Batch Processing

```python
import glob
import json
from plan_lint import validate_plan
from plan_lint.loader import load_plan, load_policy

# Load policy
policy = load_policy("policy.yaml")

# Get all plan files
plan_files = glob.glob("plans/*.json")

# Process each plan
results = {}
for plan_file in plan_files:
    # Load plan
    plan = load_plan(plan_file)
    
    # Validate
    result = validate_plan(plan, policy)
    
    # Store result
    results[plan_file] = {
        "is_valid": result.is_valid,
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "severity": v.severity,
                "step_id": v.step_id
            } for v in result.violations
        ]
    }

# Write report
with open("validation_report.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Streaming Plans

For high-throughput scenarios, you can stream plans through the validation system:

```python
import json
from plan_lint import PlanValidator
from plan_lint.loader import load_policy

# Create validator
policy = load_policy("policy.yaml")
validator = PlanValidator(policy)

# Function to process stream
def process_plan_stream(stream):
    for line in stream:
        # Parse plan from line
        plan_data = json.loads(line)
        
        # Validate
        result = validator.validate(plan_data)
        
        # Process result
        if not result.is_valid:
            yield (plan_data.get("id", "unknown"), result.violations)

# Example: process from file
with open("plans_stream.jsonl") as f:
    for plan_id, violations in process_plan_stream(f):
        print(f"Plan {plan_id} has violations")
```

## Webhook Integration

You can set up a Plan-Lint webhook server to validate plans on demand.

### Simple Flask Server

```python
from flask import Flask, request, jsonify
from plan_lint import validate_plan
from plan_lint.loader import load_policy

app = Flask(__name__)

# Load policy at startup
policy = load_policy("policy.yaml")

@app.route('/validate', methods=['POST'])
def validate():
    # Get plan from request
    plan_data = request.json
    
    # Validate plan
    result = validate_plan(plan_data, policy)
    
    # Return result
    return jsonify({
        "is_valid": result.is_valid,
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "severity": v.severity,
                "step_id": v.step_id
            } for v in result.violations
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### FastAPI Implementation

For a more robust webhook server:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from plan_lint import validate_plan
from plan_lint.loader import load_policy

app = FastAPI(title="Plan-Lint API")

# Load policies
default_policy = load_policy("policy.yaml")
policies = {
    "default": default_policy,
    "strict": load_policy("strict_policy.yaml"),
    "enterprise": load_policy("enterprise_policy.yaml")
}

class Plan(BaseModel):
    goal: str = Field(..., description="The goal of the plan")
    steps: List[Dict[str, Any]] = Field(..., description="The steps of the plan")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class ValidationRequest(BaseModel):
    plan: Plan
    policy_name: Optional[str] = Field("default", description="Policy to use for validation")
    context: Optional[Dict[str, Any]] = Field(None, description="Validation context")

class ValidationResponse(BaseModel):
    is_valid: bool
    violations: List[Dict[str, Any]]

@app.post("/api/validate", response_model=ValidationResponse)
async def validate(request: ValidationRequest):
    # Get policy
    if request.policy_name not in policies:
        raise HTTPException(status_code=400, detail=f"Unknown policy: {request.policy_name}")
    
    policy = policies[request.policy_name]
    
    # Validate plan
    result = validate_plan(request.plan.dict(), policy, context=request.context)
    
    # Return result
    return {
        "is_valid": result.is_valid,
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "severity": v.severity,
                "step_id": v.step_id
            } for v in result.violations
        ]
    }

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
```

## Scheduled Validation

For scenarios where plans need to be validated on a schedule, you can set up cron jobs or other scheduling systems.

### Cron Job Example

```bash
# /etc/cron.d/plan-lint
# Run plan validation every hour
0 * * * * planlint-user /usr/local/bin/plan-lint validate-batch --plans-dir /var/plans --policy /etc/planlint/policy.yaml --output /var/log/planlint/$(date +\%Y\%m\%d\%H).json
```

### Airflow DAG

For more complex scheduling with Apache Airflow:

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import glob
import json
from plan_lint import validate_plan
from plan_lint.loader import load_plan, load_policy

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'plan_lint_validation',
    default_args=default_args,
    description='Validate plans with Plan-Lint',
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

# Task to list plans
list_plans = BashOperator(
    task_id='list_plans',
    bash_command='ls -1 /path/to/plans/*.json > /tmp/plans_to_validate.txt',
    dag=dag,
)

# Task to validate plans
def validate_plans():
    # Load policy
    policy = load_policy("/path/to/policy.yaml")
    
    # Get plan files
    with open("/tmp/plans_to_validate.txt") as f:
        plan_files = [line.strip() for line in f]
    
    # Validate each plan
    results = {}
    for plan_file in plan_files:
        plan = load_plan(plan_file)
        result = validate_plan(plan, policy)
        results[plan_file] = {
            "is_valid": result.is_valid,
            "violations": [v.to_dict() for v in result.violations]
        }
    
    # Write report
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    report_path = f"/path/to/reports/validation_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return report_path

validate_task = PythonOperator(
    task_id='validate_plans',
    python_callable=validate_plans,
    dag=dag,
)

# Define task order
list_plans >> validate_task
```

## Integration with Message Queues

For high-scale automation, you can integrate Plan-Lint with message queues like RabbitMQ or Kafka.

### RabbitMQ Consumer

```python
import pika
import json
from plan_lint import validate_plan
from plan_lint.loader import load_policy

# Load policy
policy = load_policy("policy.yaml")

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queues
channel.queue_declare(queue='plans_to_validate')
channel.queue_declare(queue='validation_results')

# Define callback
def callback(ch, method, properties, body):
    # Parse plan
    plan_data = json.loads(body)
    
    # Validate plan
    result = validate_plan(plan_data, policy)
    
    # Create result message
    result_message = {
        "plan_id": plan_data.get("id", "unknown"),
        "is_valid": result.is_valid,
        "violations": [
            {
                "rule": v.rule,
                "message": v.message,
                "severity": v.severity,
                "step_id": v.step_id
            } for v in result.violations
        ]
    }
    
    # Publish result
    channel.basic_publish(
        exchange='',
        routing_key='validation_results',
        body=json.dumps(result_message)
    )
    
    # Acknowledge message
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Set up consumer
channel.basic_consume(
    queue='plans_to_validate',
    on_message_callback=callback
)

# Start consuming
print('Waiting for plans to validate. To exit press CTRL+C')
channel.start_consuming()
```

## Containerized Validation

You can containerize Plan-Lint for consistent deployment across environments:

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy policies and application
COPY policies/ ./policies/
COPY app.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3'

services:
  plan-lint:
    build: .
    volumes:
      - ./plans:/app/plans
      - ./reports:/app/reports
    environment:
      - POLICY_PATH=/app/policies/policy.yaml
      - REPORT_DIR=/app/reports
    ports:
      - "8000:8000"
```

## Monitoring and Alerting

For production deployments, you can add monitoring and alerting:

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, start_http_server
import time

# Define metrics
VALIDATION_COUNT = Counter('plan_lint_validations_total', 'Total number of validations')
VIOLATION_COUNT = Counter('plan_lint_violations_total', 'Total number of violations', ['rule', 'severity'])
VALIDATION_TIME = Histogram('plan_lint_validation_seconds', 'Time spent validating plans')

# Start metrics server
start_http_server(8000)

# Instrumented validation function
def validate_with_metrics(plan, policy):
    # Count validation
    VALIDATION_COUNT.inc()
    
    # Time validation
    start_time = time.time()
    with VALIDATION_TIME.time():
        result = validate_plan(plan, policy)
    
    # Count violations
    for violation in result.violations:
        VIOLATION_COUNT.labels(
            rule=violation.rule,
            severity=violation.severity
        ).inc()
    
    return result
```

### Slack Alerts

```python
import requests
import json

def send_slack_alert(webhook_url, plan_id, violations):
    # Skip if no violations
    if not violations:
        return
    
    # Create message
    message = {
        "text": f"🚨 Plan '{plan_id}' has validation violations",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Plan Validation Failed: {plan_id}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(violations)}* violations were found in the plan."
                }
            }
        ]
    }
    
    # Add violation details
    for violation in violations[:5]:  # Limit to first 5
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{violation['rule']}* ({violation['severity']})\n{violation['message']}"
            }
        })
    
    # Add footer if more violations
    if len(violations) > 5:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"_...and {len(violations) - 5} more violations_"
            }
        })
    
    # Send message
    response = requests.post(
        webhook_url,
        data=json.dumps(message),
        headers={"Content-Type": "application/json"}
    )
    
    return response.status_code == 200
```

## Best Practices for Automation

1. **Version Your Policies**: Use version control for policies to track changes
2. **Staged Rollout**: Implement new policies in monitoring mode before enforcing
3. **Performance Optimization**: For high-throughput scenarios:
   - Load policies once and reuse the validator instance
   - Use batch processing when possible
   - Consider multi-threading for parallel validation
4. **Error Handling**: Implement robust error handling and fallbacks
5. **Logging**: Add detailed logging for troubleshooting
6. **Authentication**: Secure webhook endpoints with proper authentication
7. **Caching**: Consider caching validation results for identical plans

## Example: Complete Automated Workflow

Here's an example workflow for automated validation in a production environment:

1. **Agent generates plan**
2. **Plan is submitted to validation queue**
3. **Validation service processes plan**:
   - Applies relevant policies based on context
   - Records metrics and logs
   - Stores validation result
4. **Action based on result**:
   - If valid: Execute plan
   - If invalid: Block execution, notify appropriate team
5. **Monitoring system alerts on anomalies**:
   - High violation rates
   - Validation service performance issues
   - Policy application errors

By automating validation with Plan-Lint, you can ensure consistent policy enforcement across your agent systems, reducing risk and increasing operational efficiency.
