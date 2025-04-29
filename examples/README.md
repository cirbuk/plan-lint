# Plan-Lint Examples

This directory contains examples of how to use plan-lint in various scenarios.

## Demo Scripts

### Realistic Demo

The `realistic_demo.py` script provides a realistic demonstration of plan-lint's validation capabilities with proper timing comparison. The demo:

1. Simulates a slow LLM plan generation process (typical of real-world agent systems)
2. Shows the near-instant validation speed of plan-lint
3. Contrasts the two to demonstrate the efficiency of client-side validation

```bash
# Run the default scenario (harmful SQL injection)
python examples/realistic_demo.py

# Try a specific scenario
python examples/realistic_demo.py --scenario excessive

# Run all scenarios in sequence
python examples/realistic_demo.py --all

# Run in fast mode (for CI testing, skips slow plan generation)
python examples/realistic_demo.py --fast
```

### Interactive Demo

The `interactive_demo.py` script provides an interactive demo that pauses between steps, ideal for presentations and videos:

```bash
# Run in interactive mode (pauses for user input)
python examples/interactive_demo.py --interactive

# Run all scenarios sequentially
python examples/interactive_demo.py --all --interactive

# Run a specific scenario
python examples/interactive_demo.py --scenario standard --interactive
```

### Available Scenarios

All demo scripts support these scenarios:

- **standard**: Standard account transfer (should pass validation)
- **harmful**: Transaction query with SQL injection (should fail validation)
- **excessive**: Large transfer exceeding limits (should fail validation)
- **sensitive_data**: Profile update with sensitive data (should fail validation)

## Finance Agent System

The `finance_agent_system` directory contains a more complete example of an agent-based financial system that uses plan-lint for validation:

```bash
# Run the finance agent system example
python run_finance_example.py
```

## Benchmarking

For performance testing, use the benchmark script:

```bash
# Run performance benchmark (100 iterations per plan type)
python examples/benchmark_linter.py
```

The benchmark script measures the raw validation performance across different plan types, showing that plan-lint's validation typically completes in under 1ms.

## Available Examples

### Finance Agent System

A realistic example of integrating plan-lint into a multi-agent financial system built with the OpenAI Agents SDK. This example shows how to:

1. Create a security validation layer between planning and execution agents
2. Intercept potentially dangerous operations before they execute
3. Detect SQL injection, excessive transaction amounts, and data leaks

[View Finance Agent System Example](./finance_agent_system)

## Running the Examples

Each example contains detailed instructions in its own README. Generally, you can run an example by:

1. Installing the requirements:
   ```bash
   pip install -e .[dev]
   ```

2. Running the example script:
   ```bash
   python examples/finance_agent_system/main.py
   ```

## Creating Your Own Integration

To adapt these examples for your own agentic system:

1. Create a policy file tailored to your domain's security requirements
2. Set up a validation layer between planning and execution components
3. Ensure plans are only executed after passing validation

See the individual examples for specific implementation patterns. 