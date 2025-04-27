# Plan-Linter Documentation

Welcome to the Plan-Linter documentation! This tool helps you validate LLM agent plans against security policies and schemas.

## Table of Contents

- [Getting Started](getting-started.md)
- [README](../README.md)
- [Contributing](../CONTRIBUTING.md)
- [Implementation Details](../IMPLEMENTATION.md)

## Overview

Plan-Linter is a static analysis toolkit that checks LLM agent plans before they execute. By validating plans against policies, schemas, and security rules, it helps prevent dangerous operations, data leaks, and buggy sequences.

## Key Features

- **Schema Validation**: Ensure plans conform to the expected JSON schema
- **Policy Rules**: Define allowed tools, parameter bounds, and other constraints
- **Security Checks**: Detect secrets, PII, and other sensitive data in plans
- **Loop Detection**: Identify cycles in step dependencies
- **Risk Scoring**: Get a quantitative measure of plan safety

## Quick Links

- [GitHub Repository](https://github.com/cirbuk/plan-lint)
- [Issue Tracker](https://github.com/cirbuk/plan-lint/issues)
- [Changelog](../CHANGELOG.md) 