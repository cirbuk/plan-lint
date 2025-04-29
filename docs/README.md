# Plan-Lint SDK

This directory contains the documentation for Plan-Lint, a static analysis toolkit for validating LLM agent plans before execution.

## Documentation Structure

The documentation is organized into the following sections:

- **Introduction** (`index.md`): Overview of Plan-Lint
- **Getting Started** (`getting-started.md`): Installation and basic usage
- **Policy Authoring Guide** (`policy-authoring.md`): Writing policies for Plan-Lint
- **Examples**: Real-world examples of using Plan-Lint
- **Documentation**: Detailed guides on various aspects of Plan-Lint
- **API Reference**: Detailed information about the Plan-Lint API
- **Advanced**: Advanced configurations and integrations

## Building the Documentation

To build and serve the documentation locally:

```bash
# Install the package with documentation dependencies
pip install -e ".[docs]"

# Serve the documentation (with live reload)
make serve-docs
# OR
mkdocs serve

# Build the static site
make build-docs
# OR
mkdocs build
```

The documentation is built using [MkDocs](https://www.mkdocs.org/) with the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.

## Contributing to the Documentation

We welcome contributions to improve the documentation! Here are some guidelines:

1. **File Locations**: Documentation files should be placed in the appropriate directory based on their category:
   - Example files go in `docs/examples/`
   - API documentation goes in `docs/api/`
   - General documentation goes in `docs/documentation/`
   - Advanced topics go in `docs/advanced/`

2. **Navigation**: The navigation structure is defined in `mkdocs.yml`. If you add a new file, update the `nav` section in `mkdocs.yml` to include it.

3. **Style Guidelines**:
   - Use clear, concise language
   - Include code examples where appropriate
   - Use headings to organize content
   - Add links to related documentation

4. **Testing**: After making changes, build the documentation locally to make sure it looks as expected.

5. **Cleanup**: After completing your changes, run `make cleanup-docs` to remove any duplicate documentation files.

## Documentation TODO

The following areas of documentation still need to be improved:

1. Expand API reference with more details and examples
2. Add more real-world examples for different use cases
3. Improve advanced integration guides
4. Add more diagrams and visual aids

If you'd like to contribute to any of these areas, please submit a pull request! 