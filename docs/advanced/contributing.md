# Contributing

This guide explains how to contribute to the Plan-Lint project.

## Why Contribute?

Contributing to Plan-Lint helps:
- Improve security of AI agent systems
- Add new validation capabilities
- Fix bugs and enhance existing features
- Share your expertise with the community
- Shape the future of agent safety

## Ways to Contribute

There are many ways to contribute to Plan-Lint:

1. **Report Issues**: Report bugs, request features, or suggest improvements
2. **Improve Documentation**: Fix errors, add examples, or clarify explanations
3. **Develop Code**: Add features, fix bugs, or improve performance
4. **Share Policies**: Contribute policy examples for specific use cases
5. **Spread the Word**: Share your experience with Plan-Lint

## Development Environment Setup

### Prerequisites

- Python 3.9 or later
- Git
- A GitHub account

### Clone and Set Up the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/plan-lint.git
cd plan-lint

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=plan_lint tests/
```

## Contribution Workflow

### 1. Choose an Issue

- Browse the [issue tracker](https://github.com/yourusername/plan-lint/issues)
- Look for issues labeled `good first issue` if you're new
- Comment on an issue to indicate you're working on it

### 2. Create a Branch

```bash
# Update your main branch
git checkout main
git pull origin main

# Create a new branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Write code following the style guidelines
- Add tests for new features
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run tests to ensure everything works
pytest
```

### 5. Submit a Pull Request

```bash
# Push your branch to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub:
1. Go to the original repository
2. Click "New Pull Request"
3. Select your branch
4. Fill in the Pull Request template

## Code Style Guidelines

Plan-Lint follows these style guidelines:

- **PEP 8**: Follow Python's style guide
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Document classes and functions with docstrings
- **Commit Messages**: Write clear, concise commit messages

We use the following tools to enforce style:

```bash
# Run code formatters
black plan_lint tests

# Run linters
flake8 plan_lint tests
mypy plan_lint
```

## Adding New Features

### New Validators

To add a new validator:

1. Create a new file in `plan_lint/validators/`
2. Implement the validator class extending `BaseValidator`
3. Register your validator in `plan_lint/validators/__init__.py`
4. Add tests in `tests/validators/`
5. Update documentation in `docs/`

Example validator structure:

```python
from plan_lint.validators.base import BaseValidator, ValidationResult

class MyCustomValidator(BaseValidator):
    """Validator that checks for my custom condition."""
    
    def validate(self, plan, context=None):
        """Validate the plan."""
        violations = []
        
        # Implement validation logic
        for step in plan.get("steps", []):
            if self._check_violation(step):
                violations.append({
                    "rule": "my_custom_rule",
                    "message": "Description of the violation",
                    "severity": "medium",
                    "step_id": step.get("id")
                })
        
        return ValidationResult(violations)
    
    def _check_violation(self, step):
        """Helper method to check for violations."""
        # Implement check logic
        return False
```

### New Rule Types

To add a new rule type:

1. Update `plan_lint/rules/`
2. Add parser and validation logic
3. Update the schema in `plan_lint/schemas/`
4. Add tests in `tests/rules/`
5. Update documentation with examples

## Writing Tests

Plan-Lint uses pytest for testing. Follow these guidelines:

- Test each feature and edge case
- Use fixtures for reusable test data
- Structure tests following the project's organization
- Name tests descriptively (`test_should_detect_sql_injection`)

Example test:

```python
import pytest
from plan_lint import validate_plan
from plan_lint.loader import load_policy

@pytest.fixture
def vulnerable_plan():
    return {
        "steps": [
            {
                "id": "step1",
                "tool": "db.query",
                "parameters": {
                    "query": "SELECT * FROM users WHERE username = 'admin' OR 1=1"
                }
            }
        ]
    }

def test_should_detect_sql_injection(vulnerable_plan):
    policy = load_policy("tests/fixtures/sql_injection_policy.yaml")
    result = validate_plan(vulnerable_plan, policy)
    
    assert not result.is_valid
    assert len(result.violations) == 1
    assert result.violations[0].rule == "sql_injection"
```

## Updating Documentation

Documentation is crucial for Plan-Lint. When making changes:

1. Update relevant documentation files in `docs/`
2. Add examples for new features
3. Ensure code examples work correctly
4. Check for clarity and correctness

## Release Process

The release process follows these steps:

1. Update version in `setup.py` and `plan_lint/__init__.py`
2. Update `CHANGELOG.md` with new changes
3. Create a pull request for the release
4. After approval, merge to main
5. Create a new release on GitHub
6. CI/CD will publish to PyPI

## Community Guidelines

When contributing to Plan-Lint:

- Be respectful and inclusive
- Provide constructive feedback
- Help others with their contributions
- Follow the code of conduct

## Getting Help

If you need help with your contribution:

- Ask questions in the issue you're working on
- Join the community discussion forum
- Check existing documentation and examples

Thank you for contributing to Plan-Lint! Your efforts help make AI agent systems safer and more secure. 