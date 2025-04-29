#!/usr/bin/env python
"""
Benchmark script to measure the performance of the plan-lint validation process.

This script measures validation times over multiple iterations to ensure
performance remains within acceptable limits.
"""

import os
import statistics
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(os.path.dirname(__file__)).parent)
sys.path.insert(0, project_root)

# Import after setting path - no longer marked as E402 because they follow sys.path modification
from examples.finance_agent_system.main import SAMPLE_PLANS
from examples.finance_agent_system.validator import validate_finance_plan


def benchmark_validation(iterations=100):
    """Benchmark the validation performance over a specified number of iterations."""
    results = {}

    print(f"Running benchmark with {iterations} iterations...")
    print("This may take a few seconds...")

    for plan_type, plan_data in SAMPLE_PLANS.items():
        print(f"Benchmarking plan type: {plan_type}")
        timings = []

        # Run the validation multiple times and measure execution time
        for _ in range(iterations):
            start_time = time.perf_counter()
            validate_finance_plan(plan_data)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000
            timings.append(execution_time_ms)

        # Calculate statistics
        results[plan_type] = {
            "min": min(timings),
            "max": max(timings),
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
        }

    return results


def main():
    """Execute the benchmark and display results."""
    # Run the benchmark
    results = benchmark_validation()

    # Print the results in a formatted table
    print("\nBenchmark Results (milliseconds):")
    print("-" * 60)
    print(f"{'Plan Type':<20} {'Min':>8} {'Max':>8} {'Mean':>8} {'Median':>8}")
    print("-" * 60)

    total_avg = 0
    count = 0

    for plan_type, stats in results.items():
        print(
            f"{plan_type:<20} {stats['min']:>8.2f} {stats['max']:>8.2f} "
            f"{stats['mean']:>8.2f} {stats['median']:>8.2f}"
        )
        total_avg += stats["mean"]
        count += 1

    print("-" * 60)
    overall_avg = total_avg / count
    print(f"Overall Average: {overall_avg:.2f} ms")

    # Check if we're meeting our target (50ms)
    target_ms = 50
    if overall_avg <= target_ms:
        print(f"\nPerformance is GOOD: {overall_avg:.2f}ms (target: {target_ms}ms)")
    else:
        print(
            f"\nPerformance needs improvement: {overall_avg:.2f}ms "
            f"(target: {target_ms}ms)"
        )


if __name__ == "__main__":
    main()
