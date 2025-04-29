.PHONY: install install-dev install-docs test lint format clean docs serve-docs build-docs cleanup-docs

# Default target
all: install-dev lint test

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-docs:
	pip install -e ".[docs]"

# Testing and quality targets
test:
	pytest

test-cov:
	pytest --cov=plan_lint --cov-report=term --cov-report=html

lint:
	ruff check .
	black --check .
	isort --check-only --profile black .
	mypy .

format:
	ruff check --fix .
	black .
	isort --profile black .

# Documentation targets
docs: build-docs

serve-docs:
	mkdocs serve

build-docs:
	mkdocs build

cleanup-docs:
	@echo "Cleaning up duplicate documentation files..."
	@rm -f docs/documentation/api-reference.md
	@rm -f docs/documentation/examples.md
	@rm -f docs/documentation/getting-started.md
	@rm -f docs/documentation/policy-authoring-guide.md
	@rm -f docs/documentation/policy-authoring.md
	@rm -f docs/documentation/user-guide.md
	@echo "Documentation cleanup complete."

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help
help:
	@echo "Available targets:"
	@echo "  install      - Install package"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  install-docs - Install package with documentation dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code"
	@echo "  docs         - Build documentation"
	@echo "  serve-docs   - Serve documentation locally"
	@echo "  build-docs   - Build static documentation"
	@echo "  cleanup-docs - Remove duplicate documentation files"
	@echo "  clean        - Clean build artifacts" 