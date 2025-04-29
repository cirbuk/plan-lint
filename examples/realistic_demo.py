#!/usr/bin/env python
"""
Realistic demo script for plan-lint's finance agent system.
This shows realistic LLM plan generation time but actual (fast) validation speed.
"""

import sys
import os
import argparse
import time
import random
from colorama import init, Fore, Style

# Initialize colorama
init()

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the needed modules
from examples.finance_agent_system.main import SAMPLE_PLANS, USER_PROMPTS
from examples.finance_agent_system.validator import validate_finance_plan

# Define available scenarios and their descriptions
SCENARIOS = {
    "standard": "Standard account transfer (should pass validation)",
    "harmful": "Transaction query with SQL injection (should fail validation)",
    "excessive": "Large transfer exceeding limits (should fail validation)",
    "sensitive_data": "Profile update with sensitive data (should fail validation)",
}


def simulate_typing(text, delay_range=(0.01, 0.05), newline=True):
    """Simulate realistic typing with variable speed."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(random.uniform(*delay_range))

    if newline:
        sys.stdout.write("\n")
    sys.stdout.flush()


def simulate_thinking(steps, prefix="🤖 "):
    """Simulate the agent thinking process with steps."""
    for step in steps:
        sys.stdout.write(f"\r{Fore.CYAN}{prefix}{step}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(random.uniform(0.7, 1.5))

    # Clear line
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()


def run_scenario(scenario, fast_mode=False):
    """Run a scenario with slow plan generation but fast validation"""
    # Get the sample plan
    plan = SAMPLE_PLANS.get(scenario)
    user_prompt = USER_PROMPTS.get(scenario, "")

    # Show user prompt
    print(f"\n{Fore.YELLOW}USER: {Style.RESET_ALL}{user_prompt}")

    if not fast_mode:
        # Show agent thinking and slow plan generation
        print(f"\n{Fore.GREEN}FinancialPlanningAgent: {Style.RESET_ALL}")
        simulate_typing(
            "I'll create a plan for this financial operation.", delay_range=(0.03, 0.08)
        )

        # Simulate agent thinking
        thinking_steps = [
            "Analyzing the user request...",
            "Determining required operations...",
            "Planning database queries...",
            "Identifying required tools...",
            "Formulating execution steps...",
            "Generating structured plan...",
        ]
        simulate_thinking(thinking_steps)
    else:
        print(
            f"\n{Fore.GREEN}FinancialPlanningAgent: {Style.RESET_ALL}Generating plan..."
        )

    # Generate plan JSON
    import json

    plan_json = json.dumps(plan, indent=2)

    # Show the plan generation with typing effect
    print(f"{Fore.GREEN}FinancialPlanningAgent: {Style.RESET_ALL}Here's my plan:")
    print(f"{Fore.YELLOW}")  # Start yellow color for JSON

    if not fast_mode:
        # Split the JSON into lines to simulate it being generated line by line
        lines = plan_json.split("\n")
        for line in lines:
            simulate_typing(line, delay_range=(0.01, 0.03))
    else:
        print(plan_json)

    print(f"{Style.RESET_ALL}")  # Reset color

    # Now measure and run the validation with actual timing (fast)
    print(
        f"\n{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Validating plan against security policies..."
    )

    # Start timing the validation
    validation_start = time.time()

    # Get the actual validation result
    is_valid, validation_message = validate_finance_plan(plan_json)

    # Calculate elapsed time
    validation_time = time.time() - validation_start
    validation_time_ms = validation_time * 1000

    # Show validation result and time
    print(f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}{validation_message}")
    print(
        f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Validation completed in {validation_time_ms:.2f} milliseconds"
    )

    # Compare to simulated plan generation time (typical LLM response time is several seconds)
    # print(
    #     f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Validation is {5000 / validation_time_ms:.0f}x faster than typical LLM plan generation"
    # )

    if is_valid:
        print(f"{Fore.GREEN}✅ Plan approved{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Plan rejected{Style.RESET_ALL}")

    return is_valid


def main():
    """Main entry point for the demo."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Run plan-lint finance demo with realistic timing"
    )
    parser.add_argument(
        "--scenario",
        "-s",
        choices=list(SCENARIOS.keys()),
        default="harmful",
        help="Scenario to demonstrate (default: harmful)",
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Run all scenarios in sequence"
    )
    parser.add_argument(
        "--fast",
        "-f",
        action="store_true",
        help="Skip slow plan generation (for CI testing)",
    )
    args = parser.parse_args()

    print(f"{Fore.GREEN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📊 PLAN-LINT FINANCIAL SECURITY DEMO {Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'=' * 80}{Style.RESET_ALL}")
    print()

    # List available scenarios
    print(f"{Fore.CYAN}Available Scenarios:{Style.RESET_ALL}")
    for key, desc in SCENARIOS.items():
        bullet = "✅" if key == "standard" else "❌"
        print(f"  {bullet} {key}: {desc}")
    print()

    if args.all:
        print(f"{Fore.YELLOW}Running all scenarios in sequence.{Style.RESET_ALL}")
        print()

        for scenario in SCENARIOS.keys():
            print(f"\n{Fore.CYAN}Running scenario: {scenario}{Style.RESET_ALL}")
            run_scenario(scenario, args.fast)
    else:
        print(f"{Fore.YELLOW}Running scenario: {args.scenario}{Style.RESET_ALL}")
        print()
        run_scenario(args.scenario, args.fast)

    # print(f"\n{Fore.GREEN}Demo complete!{Style.RESET_ALL}")
    # print("This demonstrates how plan-lint provides near-instant security validation")
    # print(
    #     "for LLM-generated plans, preventing potentially dangerous operations before execution."
    # )


if __name__ == "__main__":
    main()
