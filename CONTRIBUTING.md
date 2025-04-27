# Contributing to Plan-Linter

Thank you for considering contributing to Plan-Linter! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Bug reports help us improve. When creating a bug report, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Environment details (OS, Python version, etc.)

### Suggesting Features

Feature suggestions are welcome. Please provide:

- A clear description of the feature
- The problem it solves
- Possible implementation approaches

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest` and `pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/your-username/plan-linter.git
   cd plan-linter
   ```

2. Create a virtual environment and install dependencies
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   pip install -e ".[dev]"
   ```

3. Setup pre-commit hooks
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings in Google style format
- Include type hints
- Add tests for new functionality

## Testing

Run tests with pytest:

```bash
pytest
```

## Documentation

- Update documentation for new features or changes
- Include docstrings for all public functions, classes, and methods

Thank you for contributing to Plan-Linter!
