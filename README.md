# 🛡️ plan-linter

*"Fail your agent's flight-plan in CI—before it fails production."*

`plan-linter` is an **open-source static analysis toolkit** for LLM agent **plans**.

It parses the machine-readable plan emitted by a planner/brain, validates it against
schemas, policy rules, and heuristics, and returns Pass / Fail with an
annotated risk-score JSON.

[![CI](https://github.com/cirbuk/plan-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/cirbuk/plan-lint/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/plan-lint.svg)](https://badge.fury.io/py/plan-lint)
[![Python Versions](https://img.shields.io/pypi/pyversions/plan-lint.svg)](https://pypi.org/project/plan-lint/)

## ✨ Features

| Capability | Description |
| --- | --- |
| **Schema validation** | JSON Schema/Pydantic v2 types for every step & arg |
| **Policy engine** | YAML/OPA rules: allow/deny tools, value bounds, scopes |
| **Data-flow analysis** | Detect raw secrets, PII, un-escaped SQL moving to dangerous sinks |
| **Loop detection** | Cycle check on step graph; flag unbounded recursions |
| **Risk scoring** | Heuristic risk score (0-1); fail threshold configurable |
| **Plugin rules** | Drop-in Python files → auto-discovered via `entry_points` |
| **CLI & JSON output** | Exit code for CI; detailed JSON for orchestrators |

## 📦 Installation

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

## 🚀 Quick Start

The simplest way to use plan-linter is to run it on a plan JSON file:

```bash
plan-lint path/to/plan.json
```

For a more advanced usage, you can provide a policy file:

```bash
plan-lint path/to/plan.json --policy path/to/policy.yaml
```

## 📝 Example Plan Format

```json
{
  "goal": "Update product prices with a discount",
  "context": {
    "user_id": "admin-012",
    "department": "sales"
  },
  "steps": [
    {
      "id": "step-001",
      "tool": "sql.query_ro",
      "args": {
        "query": "SELECT product_id, current_price FROM products"
      },
      "on_fail": "abort"
    },
    {
      "id": "step-002",
      "tool": "priceAPI.bulkUpdate",
      "args": {
        "product_ids": ["${step-001.result.product_id}"],
        "discount_pct": -20
      }
    }
  ],
  "meta": {
    "planner": "gpt-4o",
    "created_at": "2025-05-15T14:30:00Z"
  }
}
```

## 📋 Example Policy Format

```yaml
# policy.yaml
allow_tools:
  - sql.query_ro
  - priceAPI.bulkUpdate
bounds:
  priceAPI.bulkUpdate.discount_pct: [-40, 0]
deny_tokens_regex:
  - "AWS_SECRET"
  - "API_KEY"
max_steps: 50
risk_weights:
  tool_write: 0.4
  raw_secret: 0.5
  loop: 0.3
fail_risk_threshold: 0.8
```

## 🔍 Command Line Options

```
Usage: plan-lint [OPTIONS] PLAN_FILE

Options:
  --policy, -p TEXT     Path to the policy YAML file
  --schema, -s TEXT     Path to the JSON schema file
  --format, -f TEXT     Output format (cli or json) [default: cli]
  --output, -o TEXT     Path to write output [default: stdout]
  --fail-risk, -r FLOAT Risk score threshold for failure (0-1) [default: 0.8]
  --help                Show this message and exit
```

## 🧩 Adding Custom Rules

You can create custom rules by adding Python files to the `plan_lint/rules` directory. Each rule file should contain a `check_plan` function that takes a `Plan` and a `Policy` object and returns a list of `PlanError` objects.

Here's an example of a custom rule that checks for SQL write operations:

```python
from typing import List

from plan_lint.types import ErrorCode, Plan, PlanError, Policy

def check_plan(plan: Plan, policy: Policy) -> List[PlanError]:
    errors = []
    
    for i, step in enumerate(plan.steps):
        if step.tool.startswith("sql.") and "query" in step.args:
            query = step.args["query"].upper()
            write_keywords = ["INSERT", "UPDATE", "DELETE"]
            
            for keyword in write_keywords:
                if keyword in query:
                    errors.append(
                        PlanError(
                            step=i,
                            code=ErrorCode.TOOL_DENY,
                            msg=f"SQL query contains write operation '{keyword}'",
                        )
                    )
    
    return errors
```

## 🤝 Contributing

We welcome contributions from the community! To get started:

1. Check the [open issues](https://github.com/your-organization/plan-linter/issues) or create a new one to discuss your ideas
2. Fork the repository
3. Make your changes following our [contribution guidelines](CONTRIBUTING.md)
4. Submit a pull request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

## 🏗️ Development

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/your-organization/plan-linter.git
cd plan-linter

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

Thanks to all [contributors](https://github.com/your-organization/plan-linter/graphs/contributors) who have helped shape Plan-Linter!