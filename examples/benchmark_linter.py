#!/usr/bin/env python
"""
Benchmark script for measuring the actual performance of plan-lint.
This script measures the raw performance of the validation process
without any artificial delays.
"""

import json
import time
import statistics
import os
import sys

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from examples.finance_agent_system.validator import validate_finance_plan
from examples.finance_agent_system.main import SAMPLE_PLANS


def benchmark_validation(iterations=100):
    """
    Benchmark the plan validation performance.

    Args:
        iterations: Number of validation runs to perform

    Returns:
        Dictionary with timing statistics in milliseconds
    """
    # Get sample plans from the examples
    plans = SAMPLE_PLANS

    results = {}

    # Test each plan type
    for plan_name, plan_data in plans.items():
        print(f"Benchmarking plan type: {plan_name}")
        plan_json = json.dumps(plan_data)

        # Run multiple iterations to get accurate timing
        execution_times = []
        for i in range(iterations):
            start_time = time.time()

            # Run the actual validation (without any display or artificial delays)
            validate_finance_plan(plan_json)

            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            execution_times.append(execution_time_ms)

        # Calculate statistics
        results[plan_name] = {
            "min_ms": min(execution_times),
            "max_ms": max(execution_times),
            "mean_ms": statistics.mean(execution_times),
            "median_ms": statistics.median(execution_times),
            "iterations": iterations,
        }

    return results


def main():
    """Main entry point for the benchmark script."""
    print("Benchmarking plan-lint validator...")
    print("Running validation without any artificial delays or simulations")
    print("-" * 70)

    # Run the benchmark
    results = benchmark_validation(iterations=100)

    # Display results
    print("\nBenchmark Results:\n")
    print(
        f"{'Plan Type':<15} {'Min (ms)':<10} {'Max (ms)':<10} {'Mean (ms)':<10} {'Median (ms)':<12}"
    )
    print("-" * 70)

    for plan_name, stats in results.items():
        print(
            f"{plan_name:<15} {stats['min_ms']:<10.2f} {stats['max_ms']:<10.2f} {stats['mean_ms']:<10.2f} {stats['median_ms']:<12.2f}"
        )

    # Calculate overall average
    all_means = [stats["mean_ms"] for stats in results.values()]
    overall_mean = statistics.mean(all_means)

    print("-" * 70)
    print(f"Overall average validation time: {overall_mean:.2f} ms")

    # Validate against your 50ms target
    if overall_mean < 50:
        print("\n✅ Validation is UNDER the 50ms target")
    else:
        print(
            f"\n❌ Validation is OVER the 50ms target ({overall_mean:.2f} ms vs 50 ms)"
        )


if __name__ == "__main__":
    main()
