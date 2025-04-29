# Enterprise Deployment

This guide provides strategies and best practices for deploying Plan-Lint in enterprise environments.

## Enterprise Deployment Considerations

Deploying Plan-Lint in enterprise environments requires attention to:

1. **Scalability**: Supporting validation across multiple teams and systems
2. **Security**: Ensuring policy enforcement and proper access controls
3. **Integration**: Connecting with existing enterprise systems and workflows
4. **Governance**: Establishing policy management and compliance processes
5. **Observability**: Monitoring and managing the validation ecosystem

## Deployment Architectures

### Centralized Architecture

A centralized deployment model provides a single source of truth for policies and validations:

```
┌───────────────────┐      ┌─────────────────────┐
│                   │      │                     │
│  Policy Authors   │─────▶│  Policy Repository  │
│                   │      │                     │
└───────────────────┘      └──────────┬──────────┘
                                      │
                                      ▼
┌───────────────────┐      ┌─────────────────────┐
│                   │      │                     │
│  Agent Systems    │─────▶│  Validation Service │
│                   │      │                     │
└───────────────────┘      └──────────┬──────────┘
                                      │
                                      ▼
┌───────────────────┐      ┌─────────────────────┐
│                   │      │                     │
│  Security Team    │◀─────│  Audit & Reports    │
│                   │      │                     │
└───────────────────┘      └─────────────────────┘
```

Benefits:
- Single source of truth for policies
- Consistent enforcement across the organization
- Centralized monitoring and reporting
- Easy to update policies organization-wide

### Federated Architecture

A federated deployment allows teams to manage their own policies within governance guardrails:

```
┌───────────────────┐      ┌─────────────────────┐
│                   │      │                     │
│  Global Policies  │─────▶│  Policy Registry    │
│                   │      │                     │
└───────────────────┘      └─────────┬───────────┘
                                     │
                                     ▼
┌───────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                   │      │                     │      │                     │
│  Team A Policies  │─────▶│  Team A Validator   │◀─────│  Team A Systems     │
│                   │      │                     │      │                     │
└───────────────────┘      └─────────────────────┘      └─────────────────────┘

┌───────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                   │      │                     │      │                     │
│  Team B Policies  │─────▶│  Team B Validator   │◀─────│  Team B Systems     │
│                   │      │                     │      │                     │
└───────────────────┘      └─────────────────────┘      └─────────────────────┘
```

Benefits:
- Local autonomy for teams
- Ability to customize policies for specific use cases
- Reduced central bottleneck
- Isolation for sensitive domains

## Installation Methods

### Enterprise Package Distribution

For controlled distribution and versioning:

```bash
# Create an enterprise distribution package
python -m build

# Install via private PyPI server
pip install plan-lint --index-url https://pypi.internal.company.com/simple

# Install from artifact repository
pip install plan-lint-1.0.0-py3-none-any.whl
```

### Docker-based Deployment

For containerized environments:

```dockerfile
# Base image with Plan-Lint
FROM python:3.9-slim

# Install Plan-Lint
RUN pip install plan-lint==1.0.0

# Add enterprise policies
COPY ./enterprise-policies /opt/plan-lint/policies

# Set default policy path
ENV PLAN_LINT_POLICY_PATH=/opt/plan-lint/policies/enterprise.yaml

# Create validation service
COPY ./validation-service /app
WORKDIR /app

# Run service
CMD ["python", "validation_service.py"]
```

### Kubernetes Deployment

For scalable, resilient deployments:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plan-lint-validator
  namespace: security
spec:
  replicas: 3
  selector:
    matchLabels:
      app: plan-lint-validator
  template:
    metadata:
      labels:
        app: plan-lint-validator
    spec:
      containers:
      - name: validator
        image: company-registry.com/plan-lint:1.0.0
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: PLAN_LINT_POLICY_PATH
          value: "/etc/planlint/policies"
        volumeMounts:
        - name: policy-volume
          mountPath: /etc/planlint/policies
          readOnly: true
      volumes:
      - name: policy-volume
        configMap:
          name: plan-lint-policies
---
apiVersion: v1
kind: Service
metadata:
  name: plan-lint-validator
  namespace: security
spec:
  selector:
    app: plan-lint-validator
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

## Policy Management

### Policy-as-Code

Implement Policy-as-Code practices for enterprise governance:

```yaml
# Organization structure for enterprise policies
policies/
  base/
    core-security.yaml     # Base security policies for all
  domains/
    finance/               # Finance-specific policies
      transactions.yaml
      sensitive-data.yaml
    healthcare/            # Healthcare-specific policies
      hipaa.yaml
      patient-data.yaml
  environments/
    production.yaml        # Production-only rules
    development.yaml       # Development exceptions
```

### Versioning and Distribution

Version and distribute policies through CI/CD:

```yaml
# .gitlab-ci.yml example
stages:
  - lint
  - test
  - build
  - deploy

policy-lint:
  stage: lint
  script:
    - plan-lint lint --policy-dir policies/

policy-test:
  stage: test
  script:
    - plan-lint test-policies --policy-dir policies/ --test-dir policy-tests/

policy-bundle:
  stage: build
  script:
    - plan-lint bundle --policy-dir policies/ --output policy-bundle.tar.gz
  artifacts:
    paths:
      - policy-bundle.tar.gz

deploy-policies:
  stage: deploy
  script:
    - aws s3 cp policy-bundle.tar.gz s3://company-policies/plan-lint/
    - kubectl create configmap plan-lint-policies --from-file=policies/ -o yaml --dry-run=client | kubectl apply -f -
```

### Policy Inheritance and Composition

Implement policy hierarchy for maintainability:

```yaml
# Base policy with common rules
# base.yaml
policies:
  - name: base
    rules:
      - rule: prevent_sql_injection
        severity: critical
        description: "Prevents SQL injection attacks"
        pattern:
          tool: db.query
          operation: matches
          value: "'; DROP TABLE|1=1|--"

# Team policy extending base
# team-finance.yaml
extends:
  - base.yaml
policies:
  - name: finance
    rules:
      - rule: check_transaction_limits
        severity: high
        description: "Ensures transactions are within limits"
        pattern:
          tool: payments.transfer
          operation: amount_gt
          value: 10000
```

## Security & Compliance

### Role-Based Access Control

Implement RBAC for policy management:

```yaml
# RBAC configuration
roles:
  policy_admin:
    description: "Full access to policy management"
    permissions:
      - create_policy
      - read_policy
      - update_policy
      - delete_policy
      - apply_policy
      
  policy_viewer:
    description: "Can view policies but not modify"
    permissions:
      - read_policy
      
  validator:
    description: "Can validate plans against policies"
    permissions:
      - read_policy
      - validate_plan
```

### Policy Signing

Implement policy signing for integrity:

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def sign_policy(policy_path, private_key_path, password=None):
    # Load policy
    with open(policy_path, 'rb') as f:
        policy_data = f.read()
    
    # Load private key
    with open(private_key_path, 'rb') as key_file:
        private_key = load_pem_private_key(
            key_file.read(),
            password=password.encode() if password else None
        )
    
    # Sign policy
    signature = private_key.sign(
        policy_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Save signature
    signature_path = f"{policy_path}.sig"
    with open(signature_path, 'wb') as f:
        f.write(signature)
    
    return signature_path
```

### Audit Logging

Implement comprehensive audit logging:

```python
import logging
import json
from datetime import datetime

# Configure structured logging
logger = logging.getLogger("plan_lint.audit")
logger.setLevel(logging.INFO)

# Add handler for audit logs
handler = logging.FileHandler("/var/log/plan-lint/audit.log")
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def audit_validation(plan_id, policy_id, user, result):
    """Log an audit entry for plan validation."""
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "validate_plan",
        "plan_id": plan_id,
        "policy_id": policy_id,
        "user": user,
        "result": {
            "is_valid": result.is_valid,
            "violation_count": len(result.violations),
            "violations": [v.to_dict() for v in result.violations]
        }
    }
    logger.info(json.dumps(audit_entry))
```

## Integration with Enterprise Systems

### Identity & Access Management

Integrate with enterprise IAM solutions:

```python
from flask import Flask, request, jsonify
import requests
from plan_lint import validate_plan
from plan_lint.loader import load_policy

app = Flask(__name__)

# Load policy
policy = load_policy("enterprise-policy.yaml")

def verify_token(token):
    """Verify JWT token with enterprise IAM."""
    response = requests.get(
        "https://auth.company.com/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return None

@app.route('/validate', methods=['POST'])
def validate():
    # Get auth token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    # Verify token
    user_info = verify_token(token)
    if not user_info:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check permissions
    if "validate_plan" not in user_info.get("permissions", []):
        return jsonify({"error": "Forbidden"}), 403
    
    # Get plan from request
    plan_data = request.json
    
    # Validate plan
    result = validate_plan(plan_data, policy)
    
    # Log validation for audit
    audit_validation(
        plan_id=plan_data.get("id", "unknown"),
        policy_id="enterprise-policy",
        user=user_info["username"],
        result=result
    )
    
    # Return result
    return jsonify({
        "is_valid": result.is_valid,
        "violations": [v.to_dict() for v in result.violations]
    })
```

### SIEM Integration

Forward validation results to enterprise SIEM systems:

```python
import json
import socket
from plan_lint import validate_plan

def send_to_siem(event):
    """Send event to SIEM system via syslog."""
    syslog_host = "siem.company.com"
    syslog_port = 514
    
    # Format as CEF (Common Event Format)
    cef_event = (
        f"CEF:0|PlanLint|Validator|1.0|{event['rule']}|{event['message']}|"
        f"{event['severity']}|planId={event['plan_id']} stepId={event['step_id']}"
    )
    
    # Send via syslog
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(cef_event.encode(), (syslog_host, syslog_port))
    sock.close()

def validate_with_siem(plan, policy):
    """Validate plan and send violations to SIEM."""
    result = validate_plan(plan, policy)
    
    if not result.is_valid:
        for violation in result.violations:
            # Create event for SIEM
            event = {
                "rule": violation.rule,
                "message": violation.message,
                "severity": violation.severity,
                "plan_id": plan.get("id", "unknown"),
                "step_id": violation.step_id
            }
            
            # Send to SIEM
            send_to_siem(event)
    
    return result
```

### CI/CD Integration

Integrate Plan-Lint into enterprise CI/CD pipelines:

```yaml
# GitHub Actions workflow example
name: Agent Plan Validation

on:
  push:
    branches: [ main ]
    paths:
      - 'agent/plans/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'agent/plans/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install plan-lint
      
      - name: Fetch policies
        run: |
          # Pull policies from secure storage
          aws s3 cp s3://company-policies/plan-lint/policy-bundle.tar.gz .
          tar -xzf policy-bundle.tar.gz
      
      - name: Validate plans
        run: |
          plan-lint validate-batch \
            --plans-dir agent/plans/ \
            --policy-dir policies/ \
            --report-format json \
            --output validation-report.json
      
      - name: Check for violations
        run: |
          python -c "
          import json
          with open('validation-report.json') as f:
              report = json.load(f)
          critical_violations = 0
          for plan_result in report.values():
              for violation in plan_result['violations']:
                  if violation['severity'] == 'critical':
                      critical_violations += 1
          exit(1 if critical_violations > 0 else 0)
          "
      
      - name: Upload report as artifact
        uses: actions/upload-artifact@v2
        with:
          name: validation-report
          path: validation-report.json
```

## High Availability & Disaster Recovery

### Redundant Deployment

Implement redundancy for critical environments:

```yaml
# Kubernetes StatefulSet for HA deployment
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: plan-lint-validator
  namespace: security
spec:
  serviceName: "plan-lint-validator"
  replicas: 3
  selector:
    matchLabels:
      app: plan-lint-validator
  template:
    metadata:
      labels:
        app: plan-lint-validator
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - plan-lint-validator
              topologyKey: "kubernetes.io/hostname"
      containers:
      - name: validator
        image: company-registry.com/plan-lint:1.0.0
        volumeMounts:
        - name: policy-storage
          mountPath: /etc/planlint/policies
  volumeClaimTemplates:
  - metadata:
      name: policy-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

### Backup & Recovery

Implement policy backup and recovery:

```bash
#!/bin/bash
# policy-backup.sh

# Set variables
BACKUP_DIR="/mnt/backups/plan-lint"
POLICY_DIR="/etc/planlint/policies"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/policy-backup-$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_FILE $POLICY_DIR

# Rotate backups (keep last 10)
ls -t $BACKUP_DIR/policy-backup-*.tar.gz | tail -n +11 | xargs rm -f

# Store metadata
echo "{\"timestamp\": \"$DATE\", \"file\": \"$BACKUP_FILE\", \"size\": $(stat -c%s $BACKUP_FILE)}" > $BACKUP_DIR/latest-backup.json

# Optional: Send to remote storage
aws s3 cp $BACKUP_FILE s3://company-backups/plan-lint/
```

## Monitoring & Observability

### Metrics for Enterprise Monitoring

Expose comprehensive metrics:

```python
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
import time

# Define metrics
VALIDATION_COUNT = Counter(
    'plan_lint_validations_total', 
    'Total number of validations',
    ['team', 'environment']
)

VIOLATION_COUNT = Counter(
    'plan_lint_violations_total', 
    'Total number of violations', 
    ['rule', 'severity', 'team']
)

VALIDATION_TIME = Histogram(
    'plan_lint_validation_seconds', 
    'Time spent validating plans',
    ['plan_size', 'policy_size']
)

POLICY_RULES = Gauge(
    'plan_lint_policy_rules', 
    'Number of rules in policy',
    ['policy']
)

VALIDATION_ERRORS = Counter(
    'plan_lint_validation_errors_total', 
    'Total number of validation errors',
    ['error_type']
)

# Start metrics server
start_http_server(8000)
```

### Health Checks

Implement comprehensive health checks:

```python
from flask import Flask, jsonify
import os
import json
import psutil
import yaml

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Basic health check."""
    return jsonify({"status": "healthy"})

@app.route('/health/ready')
def readiness_check():
    """Readiness check with policy verification."""
    try:
        # Check policy files
        policy_dir = os.environ.get("PLAN_LINT_POLICY_PATH", "/etc/planlint/policies")
        policy_files = [f for f in os.listdir(policy_dir) if f.endswith(('.yaml', '.yml'))]
        
        # Check if we can parse a policy
        if policy_files:
            with open(os.path.join(policy_dir, policy_files[0])) as f:
                yaml.safe_load(f)
        
        # Check system resources
        system_metrics = {
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # Ready if resources are available
        is_ready = (
            system_metrics["memory_percent"] < 90 and
            system_metrics["cpu_percent"] < 90 and
            system_metrics["disk_percent"] < 90
        )
        
        return jsonify({
            "status": "ready" if is_ready else "not_ready",
            "policy_count": len(policy_files),
            "system_metrics": system_metrics
        })
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "error": str(e)
        }), 503

@app.route('/health/deep')
def deep_health_check():
    """Deep health check with policy validation test."""
    try:
        # Run a test validation
        from plan_lint import validate_plan
        from plan_lint.loader import load_policy
        
        # Test plan
        test_plan = {
            "goal": "health check",
            "steps": [
                {
                    "id": "step1",
                    "tool": "health.check",
                    "parameters": {}
                }
            ]
        }
        
        # Load and validate against default policy
        policy_path = os.environ.get("PLAN_LINT_POLICY_PATH", "/etc/planlint/policies")
        if os.path.isdir(policy_path):
            policy_files = [f for f in os.listdir(policy_path) if f.endswith(('.yaml', '.yml'))]
            if policy_files:
                policy_path = os.path.join(policy_path, policy_files[0])
        
        policy = load_policy(policy_path)
        result = validate_plan(test_plan, policy)
        
        return jsonify({
            "status": "healthy",
            "policy_validation_works": True,
            "policy_path": policy_path
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
```

## Enterprise Best Practices

1. **Policy Governance**:
   - Establish a policy review and approval process
   - Document policy rationale and scope
   - Perform regular policy audits
   - Monitor policy effectiveness metrics

2. **Deployment Strategy**:
   - Implement canary deployments for policy updates
   - Use blue/green deployments for validator service
   - Gradually roll out policy changes to minimize disruption
   - Create policy simulation environments

3. **Security Hardening**:
   - Run validators with minimal permissions
   - Use secure communication channels (mTLS)
   - Encrypt sensitive data in transit and at rest
   - Implement strict network policies for validator services

4. **Performance at Scale**:
   - Use caching to reduce validation overhead
   - Implement horizontal scaling based on validation load
   - Optimize policy evaluation with proper rule ordering
   - Use distributed processing for large-scale validation

5. **Compliance & Reporting**:
   - Generate compliance reports for regulatory requirements
   - Track policy exceptions and approvals
   - Maintain validation audit trails for compliance evidence
   - Create dashboards for policy effectiveness

## Sample Enterprise Architecture

For large enterprises, a complete architecture might include:

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Policy Authoring   │─────▶│  Policy Registry    │─────▶│  Policy CI/CD       │
│  & Management UI    │      │  (Version Control)  │      │                     │
│                     │      │                     │      │                     │
└─────────────────────┘      └─────────────────────┘      └──────────┬──────────┘
                                                                     │
                                                                     ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Validation Service │◀─────│  Policy Distributor │◀─────│  Policy Bundles     │
│  (HA Cluster)       │      │                     │      │                     │
│                     │      │                     │      │                     │
└─────────┬───────────┘      └─────────────────────┘      └─────────────────────┘
          │
          ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Agent Systems      │─────▶│  Results Database   │─────▶│  Analytics &        │
│                     │      │                     │      │  Dashboards         │
│                     │      │                     │      │                     │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
                                      │
                                      ▼
                             ┌─────────────────────┐      ┌─────────────────────┐
                             │                     │      │                     │
                             │  Enterprise SIEM    │─────▶│  Security Response  │
                             │                     │      │  Team               │
                             │                     │      │                     │
                             └─────────────────────┘      └─────────────────────┘
```

By following these enterprise deployment practices, organizations can successfully integrate Plan-Lint into their security and governance frameworks, ensuring that agent plans adhere to corporate policies and regulatory requirements. 