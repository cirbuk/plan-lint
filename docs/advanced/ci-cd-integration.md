# CI/CD Integration

This page explains how to integrate Plan-Lint into CI/CD pipelines.

## Benefits of CI/CD Integration

Integrating Plan-Lint into your CI/CD pipelines offers several advantages:

1. **Automated Validation**: Automatically check agent plans before they reach production
2. **Early Detection**: Catch harmful or non-compliant plans early in the development lifecycle
3. **Consistent Enforcement**: Apply the same policies across all environments
4. **Quality Gates**: Create security and compliance gates for agent plans
5. **Audit Trail**: Maintain records of plan validations for compliance needs

## Integration Patterns

### Pre-Deployment Validation

Validate plans before deployment to catch issues early:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│             │      │             │      │             │      │             │
│  Commit     │─────▶│  Build      │─────▶│  Validate   │─────▶│  Deploy     │
│             │      │             │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
```

### Environmental Progression

Apply different policies as plans move through environments:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│             │      │             │      │             │      │             │
│  Dev        │─────▶│  Test       │─────▶│  Staging    │─────▶│  Production │
│  Validation │      │  Validation │      │  Validation │      │  Validation │
│             │      │             │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
```

### Policy Testing

Test policies themselves to ensure they work as expected:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│             │      │             │      │             │
│  Policy     │─────▶│  Policy     │─────▶│  Policy     │
│  Changes    │      │  Tests      │      │  Deployment │
│             │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
```

## GitHub Actions Integration

### Basic Validation Workflow

A simple GitHub Actions workflow to validate plans:

```yaml
# .github/workflows/validate-plans.yml
name: Validate Agent Plans

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'plans/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'plans/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install plan-lint
      
      - name: Validate plans
        run: |
          plan-lint validate-batch \
            --plans-dir plans/ \
            --policy policies/security.yaml \
            --report-format json \
            --output validation-report.json
      
      - name: Check for critical violations
        run: |
          python -c "
          import json
          import sys
          
          with open('validation-report.json') as f:
              report = json.load(f)
          
          critical_violations = 0
          for plan_path, result in report.items():
              for violation in result.get('violations', []):
                  if violation.get('severity') == 'critical':
                      critical_violations += 1
                      print(f'CRITICAL: {violation.get(\"message\")} in {plan_path}')
          
          sys.exit(1 if critical_violations > 0 else 0)
          "
      
      - name: Upload validation report
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: validation-report.json
```

### Multi-Environment Validation

A workflow that validates against multiple environment policies:

```yaml
# .github/workflows/multi-env-validation.yml
name: Multi-Environment Validation

on:
  push:
    branches: [ main ]
    paths:
      - 'plans/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [development, staging, production]
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install plan-lint
      
      - name: Validate plans for ${{ matrix.environment }}
        run: |
          plan-lint validate-batch \
            --plans-dir plans/ \
            --policy policies/${{ matrix.environment }}.yaml \
            --report-format json \
            --output ${{ matrix.environment }}-report.json
      
      - name: Check for violations
        run: |
          python -c "
          import json
          import sys
          
          with open('${{ matrix.environment }}-report.json') as f:
              report = json.load(f)
          
          # For production, any violation is a failure
          # For staging, only critical and high are failures
          # For development, only critical is a failure
          environment = '${{ matrix.environment }}'
          failure_severities = ['critical'] if environment == 'development' else (['critical', 'high'] if environment == 'staging' else ['critical', 'high', 'medium', 'low'])
          
          violations = 0
          for plan_path, result in report.items():
              for violation in result.get('violations', []):
                  if violation.get('severity') in failure_severities:
                      violations += 1
                      print(f'{violation.get(\"severity\").upper()}: {violation.get(\"message\")} in {plan_path}')
          
          sys.exit(1 if violations > 0 else 0)
          "
      
      - name: Upload validation report
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.environment }}-report
          path: ${{ matrix.environment }}-report.json
```

### Scheduled Policy Application

A workflow that runs validation on a schedule:

```yaml
# .github/workflows/scheduled-validation.yml
name: Scheduled Validation

on:
  schedule:
    # Run every night at midnight
    - cron: '0 0 * * *'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install plan-lint requests
      
      - name: Fetch latest plans
        run: |
          # Example: Pull plans from a repository or API
          python -c "
          import requests
          import json
          import os
          
          # Create plans directory
          os.makedirs('plans', exist_ok=True)
          
          # Fetch plans from API
          response = requests.get('https://api.example.com/agent-plans')
          plans = response.json()
          
          # Save plans to files
          for i, plan in enumerate(plans):
              with open(f'plans/plan_{i}.json', 'w') as f:
                  json.dump(plan, f, indent=2)
          "
      
      - name: Validate plans
        run: |
          plan-lint validate-batch \
            --plans-dir plans/ \
            --policy policies/production.yaml \
            --report-format json \
            --output validation-report.json
      
      - name: Send report to monitoring system
        run: |
          python -c "
          import json
          import requests
          
          with open('validation-report.json') as f:
              report = json.load(f)
              
          # Send to monitoring system
          requests.post(
              'https://monitoring.example.com/webhooks/planlint',
              json={
                  'timestamp': '$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")',
                  'report': report
              }
          )
          "
```

## GitLab CI Integration

### Basic Validation Pipeline

A GitLab CI pipeline to validate plans:

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - report

variables:
  PYTHON_VERSION: "3.9"

validate-plans:
  stage: validate
  image: python:${PYTHON_VERSION}
  script:
    - pip install plan-lint
    - plan-lint validate-batch --plans-dir plans/ --policy policies/security.yaml --report-format json --output validation-report.json
  artifacts:
    paths:
      - validation-report.json
    expire_in: 1 week

generate-report:
  stage: report
  image: python:${PYTHON_VERSION}
  script:
    - pip install plan-lint matplotlib pandas
    - python -c "
        import json
        import pandas as pd
        import matplotlib.pyplot as plt
        
        # Load report
        with open('validation-report.json') as f:
            report = json.load(f)
        
        # Extract violations
        violations = []
        for plan_path, result in report.items():
            for v in result.get('violations', []):
                violations.append({
                    'plan': plan_path,
                    'rule': v.get('rule'),
                    'severity': v.get('severity'),
                    'message': v.get('message'),
                    'step_id': v.get('step_id')
                })
        
        # Create dataframe
        df = pd.DataFrame(violations)
        
        # Generate stats
        if not df.empty:
            # Count by severity
            severity_counts = df['severity'].value_counts()
            
            # Plot
            plt.figure(figsize=(10, 6))
            severity_counts.plot(kind='bar')
            plt.title('Violations by Severity')
            plt.tight_layout()
            plt.savefig('violations_by_severity.png')
            
            # Output stats to file
            with open('violation_stats.txt', 'w') as f:
                f.write(f'Total violations: {len(violations)}\n\n')
                f.write('Violations by severity:\n')
                for severity, count in severity_counts.items():
                    f.write(f'- {severity}: {count}\n')
        else:
            with open('violation_stats.txt', 'w') as f:
                f.write('No violations found. All plans are valid!\n')
      "
  artifacts:
    paths:
      - validation-report.json
      - violation_stats.txt
      - violations_by_severity.png
    expire_in: 1 month
  dependencies:
    - validate-plans
```

### Policy Testing Pipeline

A pipeline to test policies before deployment:

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - deploy

variables:
  PYTHON_VERSION: "3.9"

lint-policies:
  stage: lint
  image: python:${PYTHON_VERSION}
  script:
    - pip install plan-lint pyyaml
    - |
      python -c "
      import yaml
      import glob
      import sys
      
      errors = 0
      for file in glob.glob('policies/*.yaml'):
          try:
              with open(file) as f:
                  data = yaml.safe_load(f)
              print(f'✅ {file} is valid YAML')
          except yaml.YAMLError as e:
              print(f'❌ Error in {file}: {e}')
              errors += 1
      
      sys.exit(errors)
      "

test-policies:
  stage: test
  image: python:${PYTHON_VERSION}
  script:
    - pip install plan-lint
    - |
      for policy in policies/*.yaml; do
        echo "Testing $policy..."
        
        # Run against known-good plans (should pass)
        plan-lint validate-batch --plans-dir test-plans/valid/ --policy $policy || exit 1
        
        # Run against known-bad plans (should fail)
        if plan-lint validate-batch --plans-dir test-plans/invalid/ --policy $policy --quiet; then
          echo "❌ Error: Policy $policy failed to detect invalid plans"
          exit 1
        else
          echo "✅ Policy $policy correctly identified invalid plans"
        fi
      done

deploy-policies:
  stage: deploy
  image: python:${PYTHON_VERSION}
  script:
    - pip install plan-lint
    - |
      # Bundle policies
      plan-lint bundle --policy-dir policies/ --output policies-bundle.tar.gz
      
      # Deploy to policy server
      curl -X POST \
        -F "policies=@policies-bundle.tar.gz" \
        -H "Authorization: Bearer ${POLICY_SERVER_TOKEN}" \
        https://policy-server.example.com/api/v1/policies/upload
  only:
    - main
```

## Azure DevOps Integration

### Azure Pipelines YAML

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main
    - release/*
  paths:
    include:
    - plans/*
    - policies/*

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: Validate
  jobs:
  - job: ValidatePlans
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '3.9'
        addToPath: true
    
    - script: |
        python -m pip install --upgrade pip
        pip install plan-lint
      displayName: 'Install dependencies'
    
    - script: |
        plan-lint validate-batch \
          --plans-dir $(System.DefaultWorkingDirectory)/plans/ \
          --policy $(System.DefaultWorkingDirectory)/policies/security.yaml \
          --report-format json \
          --output $(Build.ArtifactStagingDirectory)/validation-report.json
      displayName: 'Validate plans'
    
    - script: |
        python -c "
        import json
        import sys
        
        with open('$(Build.ArtifactStagingDirectory)/validation-report.json') as f:
            report = json.load(f)
        
        critical_violations = 0
        for plan_path, result in report.items():
            for violation in result.get('violations', []):
                if violation.get('severity') == 'critical':
                    critical_violations += 1
                    print(f'##vso[task.logissue type=error;]CRITICAL: {violation.get(\"message\")} in {plan_path}')
        
        print(f'##vso[task.setvariable variable=criticalViolations;]{critical_violations}')
        "
      displayName: 'Check for critical violations'
    
    - script: |
        if [ $(criticalViolations) -gt 0 ]; then
          echo "##vso[task.complete result=Failed;]Critical violations found"
        fi
      displayName: 'Fail if critical violations exist'
    
    - task: PublishBuildArtifacts@1
      inputs:
        pathtoPublish: '$(Build.ArtifactStagingDirectory)/validation-report.json'
        artifactName: 'ValidationReport'
      displayName: 'Publish Validation Report'

- stage: Deploy
  dependsOn: Validate
  condition: succeeded()
  jobs:
  - job: DeployPlans
    steps:
    - task: DownloadBuildArtifacts@0
      inputs:
        buildType: 'current'
        downloadType: 'single'
        artifactName: 'ValidationReport'
        downloadPath: '$(System.ArtifactsDirectory)'
    
    - script: |
        echo "Deploying validated plans..."
        # Add deployment steps here
      displayName: 'Deploy plans'
```

## Jenkins Integration

### Jenkinsfile with Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent {
        docker {
            image 'python:3.9'
        }
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                python -m pip install --upgrade pip
                pip install plan-lint
                '''
            }
        }
        
        stage('Validate') {
            steps {
                sh '''
                plan-lint validate-batch \
                  --plans-dir ./plans/ \
                  --policy ./policies/security.yaml \
                  --report-format json \
                  --output validation-report.json
                '''
                
                script {
                    def report = readJSON file: 'validation-report.json'
                    def criticalViolations = 0
                    
                    report.each { planPath, result ->
                        result.violations.each { violation ->
                            if (violation.severity == 'critical') {
                                criticalViolations++
                                echo "CRITICAL: ${violation.message} in ${planPath}"
                            }
                        }
                    }
                    
                    if (criticalViolations > 0) {
                        currentBuild.result = 'FAILURE'
                        error "Found ${criticalViolations} critical violations"
                    }
                }
                
                archiveArtifacts artifacts: 'validation-report.json', fingerprint: true
            }
        }
        
        stage('Deploy') {
            when {
                expression { currentBuild.resultIsBetterOrEqualTo('SUCCESS') }
            }
            steps {
                echo "Deploying validated plans..."
                // Add deployment steps here
            }
        }
    }
    
    post {
        always {
            sh '''
            if [ -f validation-report.json ]; then
                python -c "
                import json
                
                with open('validation-report.json') as f:
                    report = json.load(f)
                
                total_violations = 0
                for plan_path, result in report.items():
                    total_violations += len(result.get('violations', []))
                
                print(f'Total violations: {total_violations}')
                "
            fi
            '''
        }
    }
}
```

## CircleCI Integration

### CircleCI Config

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  validate:
    docker:
      - image: cimg/python:3.9
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: |
            python -m pip install --upgrade pip
            pip install plan-lint
      - run:
          name: Validate plans
          command: |
            plan-lint validate-batch \
              --plans-dir ./plans/ \
              --policy ./policies/security.yaml \
              --report-format json \
              --output validation-report.json
      - run:
          name: Check for violations
          command: |
            python -c "
            import json
            import sys
            
            with open('validation-report.json') as f:
                report = json.load(f)
            
            critical_violations = 0
            for plan_path, result in report.items():
                for violation in result.get('violations', []):
                    if violation.get('severity') == 'critical':
                        critical_violations += 1
                        print(f'CRITICAL: {violation.get(\"message\")} in {plan_path}')
            
            if critical_violations > 0:
                print(f'Found {critical_violations} critical violations')
                sys.exit(1)
            else:
                print('No critical violations found')
            "
      - store_artifacts:
          path: validation-report.json
          destination: validation-report.json

  deploy:
    docker:
      - image: cimg/python:3.9
    steps:
      - checkout
      - run:
          name: Deploy validated plans
          command: |
            echo "Deploying validated plans..."
            # Add deployment steps here

workflows:
  version: 2
  validate-and-deploy:
    jobs:
      - validate
      - deploy:
          requires:
            - validate
          filters:
            branches:
              only: main
```

## Best Practices for CI/CD Integration

1. **Policy Version Control**: 
   - Keep policies in version control alongside application code
   - Use policy versioning to track changes over time
   - Require code reviews for policy changes

2. **Fail Fast**: 
   - Validate plans early in the CI/CD pipeline
   - Create focused policies for specific issues
   - Exit as soon as critical violations are detected

3. **Environment-Specific Policies**:
   - Create gradual policy progression from development to production
   - Be more permissive in dev, strict in production
   - Match policies to environment security requirements

4. **Handling Results**:
   - Generate reports for validation results
   - Archive validation reports as artifacts
   - Create dashboards to track violation trends

5. **Non-Blocking Modes**:
   - Use monitoring mode for new policies before enforcing
   - Consider warning vs. blocking based on severity
   - Implement notification channels for different severities

6. **Policy Testing**:
   - Create test cases for policies with known-good and known-bad plans
   - Validate that policies detect what they should
   - Test policy changes before deploying them

7. **Integration with Compliance**:
   - Send validation results to compliance systems
   - Generate evidence for audit requirements
   - Track exceptions and approvals

## Example: Complete CI/CD Workflow for Agent Plans

A complete workflow might include:

1. **Develop**:
   - Author agent plans
   - Run local validation with dev policies
   - Commit to feature branch

2. **Build**:
   - Trigger CI pipeline
   - Validate against development policies
   - Run unit tests for plans

3. **Test**:
   - Deploy to test environment
   - Run integration tests
   - Validate against staging policies

4. **Deploy**:
   - Request approval if needed
   - Validate against production policies
   - Deploy to production

5. **Monitor**:
   - Collect runtime metrics
   - Validate plans periodically
   - Alert on policy violations

By integrating Plan-Lint into your CI/CD pipelines, you ensure that agent plans adhere to security and compliance requirements before they reach production, reducing risk and increasing confidence in automated systems.
