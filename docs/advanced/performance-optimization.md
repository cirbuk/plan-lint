# Performance Optimization

This guide provides strategies for optimizing Plan-Lint performance in high-throughput environments.

## Understanding Performance Factors

Several factors affect Plan-Lint's validation performance:

1. **Plan Size and Complexity**: Larger plans with more steps take longer to validate
2. **Policy Complexity**: More complex policies and rules increase processing time
3. **Validation Volume**: High-throughput scenarios require different optimization strategies
4. **Available Resources**: CPU, memory, and I/O constraints impact performance

## Optimization Strategies

### Policy Optimization

The most effective way to improve performance is to optimize your policies:

#### Rule Simplification

```yaml
# Before: Complex nested conditions
- rule: check_sql_injection
  description: Detects SQL injection attempts
  pattern:
    tool: sql_query
    operation: contains
    value: "'; DROP TABLE"
    or:
      - pattern:
          operation: contains
          value: "1=1"
      - pattern:
          operation: contains
          value: "-- "
      - pattern:
          operation: contains
          value: "/*"

# After: Simplified with regex
- rule: check_sql_injection
  description: Detects SQL injection attempts
  pattern:
    tool: sql_query
    operation: matches
    value: "'; DROP TABLE|1=1|-- |/\\*"
```

#### Efficient Rule Order

Order rules with most frequent violations first to fail fast:

```yaml
policies:
  - name: efficient_policy
    rules:
      # Common violations first
      - rule: check_basic_syntax
        severity: error
      - rule: check_sql_injection
        severity: error
      # Less common violations later
      - rule: check_excessive_permissions
        severity: warning
```

#### Avoid Redundant Rules

Combine related checks to reduce overhead:

```yaml
# Before: Separate rules
- rule: check_email_retrieval
  pattern:
    tool: email_api
    operation: equals
    action: "get"

- rule: check_email_data_access
  pattern:
    tool: email_api
    operation: equals
    data_type: "sensitive"

# After: Combined rule
- rule: check_email_sensitive_data
  pattern:
    tool: email_api
    and:
      - pattern:
          operation: equals
          action: "get"
      - pattern:
          operation: equals
          data_type: "sensitive"
```

### Implementation Optimization

#### Validator Reuse

Create a validator once and reuse it for multiple validations:

```python
from plan_lint import PlanValidator
from plan_lint.loader import load_policy

# Load policy once
policy = load_policy("policy.yaml")

# Create validator once
validator = PlanValidator(policy)

# Use for multiple validations
def validate_plans(plans):
    results = []
    for plan in plans:
        result = validator.validate(plan)
        results.append(result)
    return results
```

#### Batch Processing

Process multiple plans in a single operation:

```python
from plan_lint import batch_validate_plans
from plan_lint.loader import load_policy, load_plans

# Load policy
policy = load_policy("policy.yaml")

# Load multiple plans
plans = load_plans("plans/*.json")

# Validate all at once
results = batch_validate_plans(plans, policy)
```

#### Parallel Processing

Use multi-threading or multiprocessing for parallel validation:

```python
import concurrent.futures
from plan_lint import validate_plan
from plan_lint.loader import load_policy, load_plan

def validate_worker(plan_path):
    # Each worker loads the policy (or use a shared policy with thread-safety)
    policy = load_policy("policy.yaml")
    plan = load_plan(plan_path)
    return validate_plan(plan, policy)

# List of plan paths
plan_paths = ["plan1.json", "plan2.json", "plan3.json", ...]

# Process in parallel
with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(validate_worker, plan_paths))
```

#### Memory Management

For large validation jobs, manage memory usage:

```python
import gc
from plan_lint import validate_plan
from plan_lint.loader import load_policy, load_plan

def validate_with_memory_management(plan_paths, batch_size=100):
    # Load policy once
    policy = load_policy("policy.yaml")
    
    results = []
    
    # Process in batches
    for i in range(0, len(plan_paths), batch_size):
        batch = plan_paths[i:i+batch_size]
        
        # Process batch
        batch_results = []
        for path in batch:
            plan = load_plan(path)
            result = validate_plan(plan, policy)
            batch_results.append((path, result))
        
        # Store results
        results.extend(batch_results)
        
        # Force garbage collection
        gc.collect()
    
    return results
```

### Stream Processing

For continuous validation, use stream processing techniques:

```python
import json
from plan_lint import validate_plan
from plan_lint.loader import load_policy

def validate_stream(input_stream, output_stream):
    # Load policy once
    policy = load_policy("policy.yaml")
    
    # Process stream
    for line in input_stream:
        # Parse plan
        plan = json.loads(line)
        
        # Validate
        result = validate_plan(plan, policy)
        
        # Write result
        output_stream.write(json.dumps({
            "plan_id": plan.get("id", "unknown"),
            "is_valid": result.is_valid,
            "violations": [v.to_dict() for v in result.violations]
        }) + "\n")
        output_stream.flush()
```

## Infrastructure Optimization

### Caching Strategy

Implement caching for plans that are validated frequently:

```python
import hashlib
import json
import redis
from plan_lint import validate_plan
from plan_lint.loader import load_policy

# Connect to Redis
cache = redis.Redis(host='localhost', port=6379, db=0)

def cached_validate(plan, policy=None, cache_ttl=3600):
    if policy is None:
        policy = load_policy("policy.yaml")
    
    # Generate cache key
    plan_hash = hashlib.md5(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    policy_hash = hashlib.md5(json.dumps(policy, sort_keys=True).encode()).hexdigest()
    cache_key = f"planlint:validation:{plan_hash}:{policy_hash}"
    
    # Check cache
    cached_result = cache.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # Validate
    result = validate_plan(plan, policy)
    
    # Cache result
    cache.setex(
        cache_key,
        cache_ttl,
        json.dumps({
            "is_valid": result.is_valid,
            "violations": [v.to_dict() for v in result.violations]
        })
    )
    
    return result
```

### Distributed Processing

For very high throughput, distribute validation across multiple nodes:

```python
# Worker code (validate_worker.py)
from celery import Celery
from plan_lint import validate_plan
from plan_lint.loader import load_policy

app = Celery('validate_worker', broker='pyamqp://guest@localhost//')

@app.task
def validate_task(plan_data, policy_path="policy.yaml"):
    policy = load_policy(policy_path)
    result = validate_plan(plan_data, policy)
    return {
        "is_valid": result.is_valid,
        "violations": [v.to_dict() for v in result.violations]
    }

# Client code
from validate_worker import validate_task

# Submit plan for validation
result = validate_task.delay(plan_data)

# Get result when ready
validation_result = result.get()
```

### Service Scaling

For cloud deployments, consider auto-scaling validation services:

```yaml
# Kubernetes deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plan-lint-validator
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
        image: planlint/validator:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        env:
        - name: POLICY_PATH
          value: "/etc/planlint/policy.yaml"
---
apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: plan-lint-validator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: plan-lint-validator
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Profiling and Benchmarking

### Performance Profiling

Use profiling to identify bottlenecks:

```python
import cProfile
import pstats
from plan_lint import validate_plan
from plan_lint.loader import load_policy, load_plan

def profile_validation():
    # Load data
    policy = load_policy("policy.yaml")
    plan = load_plan("plan.json")
    
    # Profile
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run validation
    result = validate_plan(plan, policy)
    
    # Disable profiler
    profiler.disable()
    
    # Print stats
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(20)  # Print top 20 time-consuming operations
    
    return result

profile_validation()
```

### Benchmarking

Measure validation performance across different scenarios:

```python
import time
import statistics
from plan_lint import validate_plan
from plan_lint.loader import load_policy, load_plan

def benchmark_validation(plan_paths, iterations=10):
    # Load policy
    policy = load_policy("policy.yaml")
    
    # Results
    results = {}
    
    for path in plan_paths:
        # Load plan
        plan = load_plan(path)
        
        # Run benchmark
        times = []
        for _ in range(iterations):
            start = time.time()
            validate_plan(plan, policy)
            end = time.time()
            times.append(end - start)
        
        # Calculate stats
        results[path] = {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0
        }
    
    return results

# Run benchmark
benchmark_results = benchmark_validation([
    "small_plan.json",
    "medium_plan.json",
    "large_plan.json"
])

# Print results
for path, stats in benchmark_results.items():
    print(f"Plan: {path}")
    print(f"  Min: {stats['min']:.6f}s")
    print(f"  Max: {stats['max']:.6f}s")
    print(f"  Mean: {stats['mean']:.6f}s")
    print(f"  Median: {stats['median']:.6f}s")
    print(f"  StdDev: {stats['stdev']:.6f}s")
```

## Best Practices Summary

1. **Policy Optimization**:
   - Simplify complex rules
   - Order rules efficiently
   - Use regex for pattern matching when appropriate
   - Avoid redundant checks

2. **Implementation Optimization**:
   - Reuse validator instances
   - Process plans in batches
   - Use parallel processing for high volumes
   - Manage memory usage for large workloads

3. **Infrastructure Optimization**:
   - Implement caching for repeated validations
   - Use distributed processing for high throughput
   - Scale validation services based on demand
   - Allocate appropriate resources based on workload

4. **Continual Improvement**:
   - Profile to identify bottlenecks
   - Benchmark to establish performance baselines
   - Monitor performance in production
   - Refine policies based on performance data

By following these optimization strategies, you can significantly improve Plan-Lint's performance, especially in high-throughput environments where validation speed is critical. 