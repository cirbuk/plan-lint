# Getting Started with Plan-Linter

This guide will help you get up and running with Plan-Linter.

## Installation

### Using pip

```bash
pip install plan-lint
```

### From source

```bash
git clone https://github.com/your-organization/plan-linter.git
cd plan-linter
pip install -e .
```

## Basic Usage

The simplest way to use Plan-Linter is to run it on a JSON plan file:

```bash
plan-lint path/to/plan.json
```

This will validate the plan against the default schema and report any issues.

## Using a Policy File

For more control, create a policy YAML file:

```yaml
# policy.yaml
allow_tools:
  - sql.query_ro
  - priceAPI.calculate
bounds:
  priceAPI.calculate.discount_pct: [-40, 0]
deny_tokens_regex:
  - "AWS_SECRET"
  - "API_KEY"
max_steps: 50
risk_weights:
  tool_write: 0.4
  raw_secret: 0.5
fail_risk_threshold: 0.8
```

Then run Plan-Linter with the policy:

```bash
plan-lint path/to/plan.json --policy policy.yaml
```

## Output Formats

Plan-Linter can output in different formats:

### CLI (default)

```bash
plan-lint path/to/plan.json
```

This shows a rich formatted report in the terminal.

### JSON

```bash
plan-lint path/to/plan.json --format json
```

This outputs a machine-readable JSON report.

### Saving Output

To save the output to a file:

```bash
plan-lint path/to/plan.json --output results.txt
```

Or for JSON:

```bash
plan-lint path/to/plan.json --format json --output results.json
```

## CI Integration

Plan-Linter can be integrated into CI pipelines. Add this to your GitHub workflow:

```yaml
- name: Lint agent plan
  run: |
    plan-lint path/to/plan.json --policy policy.yaml
```

The command will return a non-zero exit code if the plan fails validation, which will fail the CI step.

## Next Steps

- Learn about the [Plan Format](plan-format.md)
- Understand the [Policy Format](policy-format.md)
- Create [Custom Rules](custom-rules.md) 