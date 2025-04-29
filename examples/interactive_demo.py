#!/usr/bin/env python
"""
Interactive demo script for plan-lint's finance agent system.

This script provides a quick demonstration of plan-lint validating plans
in real-time with timing information - ideal for presentations and videos.
"""

import argparse
import os
import sys

from colorama import Fore, Style, init

# Initialize colorama
init()

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Define available scenarios and their descriptions
SCENARIOS = {
    "standard": "Standard account transfer (should pass validation)",
    "harmful": "Transaction query with SQL injection (should fail validation)",
    "excessive": "Large transfer exceeding limits (should fail validation)",
    "sensitive_data": "Profile update with sensitive data (should fail validation)",
}


def main():
    """Main entry point for the interactive demo."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run plan-lint finance demo")
    parser.add_argument(
        "--scenario",
        "-s",
        choices=list(SCENARIOS.keys()),
        default="harmful",
        help="Scenario to demonstrate (default: harmful)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Show user prompt and wait for keypress between steps",
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Run all scenarios in sequence"
    )
    args = parser.parse_args()

    # Show intro if running interactively
    if args.interactive:
        print(f"{Fore.GREEN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📊 PLAN-LINT FINANCIAL SECURITY DEMO{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 80}{Style.RESET_ALL}")
        print()
        print(
            "This demo shows how plan-lint validates agent-generated plans in real-time,"
        )
        print("preventing security issues before execution.")
        print()

        # List available scenarios
        print(f"{Fore.CYAN}Available Scenarios:{Style.RESET_ALL}")
        for key, desc in SCENARIOS.items():
            bullet = "✅" if key == "standard" else "❌"
            print(f"  {bullet} {key}: {desc}")
        print()

        if args.all:
            print(f"{Fore.YELLOW}Running all scenarios in sequence.{Style.RESET_ALL}")
            print("Press Enter after each scenario...")
            print()
        else:
            print(f"{Fore.YELLOW}Running scenario: {args.scenario}{Style.RESET_ALL}")
            print()

        input("Press Enter to start the demo...")

    # Import the main function to run scenarios
    from examples.finance_agent_system.main import (
        USER_PROMPTS,
        simulate_agent_execution,
    )

    # Function to run a single scenario
    def run_scenario(scenario):
        # These args would be used in a real CLI call, but we're importing directly
        # so we don't need them - just documenting what would be passed
        # scenario_args = ["--simulated", "--fast", "--scenario", scenario]

        # If running in interactive mode, show the user prompt first
        if args.interactive:
            user_prompt = USER_PROMPTS.get(scenario, "")
            print(f"\n{Fore.YELLOW}USER: {Style.RESET_ALL}{user_prompt}")
            print(f"{Fore.CYAN}[Agent is processing the request...]{Style.RESET_ALL}")
            input("Press Enter to see the generated plan and validation...")

        # Run the scenario
        simulate_agent_execution(scenario, live_mode=True, fast_mode=True)

        # Wait for user if interactive and running all scenarios
        if args.interactive and args.all:
            input("\nPress Enter for next scenario...")

    # Run the selected scenario(s)
    if args.all:
        for scenario in SCENARIOS.keys():
            run_scenario(scenario)
    else:
        run_scenario(args.scenario)

    # Final message
    if args.interactive:
        print(f"\n{Fore.GREEN}Demo complete!{Style.RESET_ALL}")
        print(
            "This demonstrates how plan-lint provides security validation in real-time"
        )
        print("for LLM-generated plans, preventing potentially dangerous operations.")
        print(
            f"\nUse {Fore.CYAN}python -m examples.finance_agent_system.main --help{Style.RESET_ALL} for more options."
        )


if __name__ == "__main__":
    main()
