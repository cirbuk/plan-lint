# 🛡️ plan-linter

*"Secure your AI agents. Lint your LLM-generated plans before they break things."*

## 🚨 Why Plan Linting Matters

Modern AI agents dynamically generate plans at runtime — deciding what actions to take, what tools to call, what goals to pursue.
But LLMs hallucinate. Plans are often invalid, broken, unsafe, or even harmful

- Unsafe: Plans might trigger dangerous tool use (e.g., "delete all data")
- Invalid: Plans can miss mandatory parameters or violate tool schemas
- Incoherent: Plans can contradict agent goals or deadlock execution
- Unexecutable: Plans can reference missing tools or invalid operations

plan-lint is a lightweight open source linter designed to validate, catch, and flag these dangerous plans before your agents act on them.

Protect your users. Safeguard your agents. Build responsibly.


`plan-lint` is an **open-source static analysis toolkit** for LLM agent **plans**.

It parses the machine-readable plan emitted by a planner/brain, validates it against
schemas, policy rules, and heuristics, and returns Pass / Fail with an
annotated risk-score JSON.

[![CI](https://github.com/cirbuk/plan-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/cirbuk/plan-lint/actions/workflows/ci.yml)
[![Publish to PyPI](https://github.com/cirbuk/plan-lint/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/cirbuk/plan-lint/actions/workflows/pypi-publish.yml)
[![Documentation](https://github.com/cirbuk/plan-lint/actions/workflows/docs.yml/badge.svg)](https://github.com/cirbuk/plan-lint/actions/workflows/docs.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/plan-lint.svg)](https://pypi.org/project/plan-lint/)
[![Python Versions](https://img.shields.io/pypi/pyversions/plan-lint.svg)](https://pypi.org/project/plan-lint/)

## 📦 Installation

### Using pip
```bash
pip install plan-lint
```

### From source
```bash
git clone https://github.com/cirbuk/plan-lint.git
cd plan-lint
pip install -e .
```

## 🚀 Quick Start

The simplest way to use plan-linter is to run it on a plan JSON file:

```bash
plan-lint path/to/plan.json
```

or use in your application
```python
from plan_lint import lint_plan

errors = lint_plan(plan_object)
if errors:
    print(errors)
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

For detailed information on creating policies, including advanced YAML policies and Rego policies with Open Policy Agent integration, see our [Policy Authoring Guide](docs/policy-authoring.md).

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

## 🛡️ Built for:
	•	LLM-based Agents (LangGraph, Autogen, CrewAI)
	•	Reasoning Engines (Tree of Thought, CoT, ReAct, DEPS)
	•	Custom AI Workflows (internal agent systems)
	•	Enterprise LLM Deployments (risk & compliance sensitive)

## 🧩 Extending plan-lint

Want to create your own checks?
	•	Fork the repo
	•	Add new rule modules inside /rules
	•	Register the rule in rule_registry.py

Check out the [Developer Guide](https://cirbuk.github.io/plan-lint/) .

## 🤝 Contributing

We welcome contributions from the community! To get started:

1. Check the [open issues](https://github.com/cirbuk/plan-lint/issues) or create a new one to discuss your ideas
2. Fork the repository
3. Make your changes following our [contribution guidelines](CONTRIBUTING.md)
4. Submit a pull request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

## 🏗️ Development

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/cirbuk/plan-lint.git
cd plan-lint

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 🌟 If you like this project…

Please star this repo!
It helps others discover the project and contributes to safer AI systems globally.
Together, we can build trustworthy agentic infrastructures. 💬

## 🛠️ Roadmap
	•	Auto-Fix simple errors
	•	VS Code extension for live linting
	•	GitHub Action for Plan Safety in CI/CD
	•	Plan Complexity Scorer
	•	Enterprise Mode (fine-grained custom policy linting)


## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.