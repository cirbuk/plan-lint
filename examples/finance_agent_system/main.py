"""
Main entry point for the Finance Agent System example.

This example demonstrates how plan-lint can be integrated into a multi-agent
system to validate plans before execution, intercepting potentially dangerous
operations.
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

# Comment out the actual agent import for demo purposes
# This allows the example to be run without installing the Agents SDK
# In a real implementation, you would use:
# from agents import Agent, Runner, Tool

# Import our validator - fix import path to work when run as a module
try:
    from .validator import (
        validate_finance_plan,
        validate_finance_plan_rego,
    )
except ImportError:
    # For direct script execution
    from validator import (
        validate_finance_plan,
        validate_finance_plan_rego,
    )

# Try to import colorama for cross-platform terminal colors
try:
    from colorama import Fore, Style, init

    init()  # Initialize colorama
    HAS_COLOR = True
except ImportError:
    # Fall back to no color if colorama is not available
    class DummyColor:
        def __getattr__(self, name):
            return ""

    Fore = Style = DummyColor()
    HAS_COLOR = False

# Sample data with more realistic scenarios
SAMPLE_PLANS = {
    "standard": {
        "goal": "Transfer $100 from checking account to savings account",
        "context": {
            "user_id": "usr_843791",
            "user_email": "alex.morgan@example.com",
            "request_id": "req-f5c7e32a",
            "client_ip": "198.51.100.123",
            "session_id": "sess_721d58f9",
            "timestamp": datetime.now().isoformat(),
            "auth_level": "verified",
        },
        "steps": [
            {
                "id": "step-001",
                "tool": "db.get_account_details",
                "args": {"user_id": "usr_843791", "account_type": "checking"},
                "on_fail": "abort",
            },
            {
                "id": "step-002",
                "tool": "db.get_account_details",
                "args": {"user_id": "usr_843791", "account_type": "savings"},
                "on_fail": "abort",
            },
            {
                "id": "step-003",
                "tool": "payments.transfer",
                "args": {
                    "from_account": "${step-001.result.account_number}",
                    "to_account": "${step-002.result.account_number}",
                    "amount": 100.00,
                    "description": "Transfer to savings",
                },
                "on_fail": "abort",
            },
            {
                "id": "step-004",
                "tool": "notify.customer",
                "args": {
                    "user_id": "usr_843791",
                    "template": "transfer_success",
                    "template_data": {
                        "amount": "$100.00",
                        "destination": "Savings Account (...${step-002.result.account_number.slice(-4)})",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                    },
                    "channel": "email",
                    "priority": 2,
                },
                "on_fail": "continue",
            },
        ],
        "meta": {
            "planner": "FinancialPlanningAgent",
            "model": "gpt-4o",
            "created_at": datetime.now().isoformat(),
        },
    },
    "harmful": {
        "goal": "Display recent transaction history for user alex.morgan@example.com",
        "context": {
            "user_id": "usr_843791",
            "user_email": "alex.morgan@example.com",
            "request_id": "req-c91b7d45",
            "session_id": "sess_a6f83c21",
            "timestamp": datetime.now().isoformat(),
            "auth_level": "verified",
        },
        "steps": [
            {
                "id": "step-001",
                "tool": "db.query_ro",
                "args": {
                    "query": "SELECT transaction_id, amount, description, date FROM transactions WHERE user_email = '${context.user_email}' OR 1=1 -- Need to see all transactions",
                    "limit": 1000,
                },
                "on_fail": "abort",
            },
            {
                "id": "step-002",
                "tool": "db.get_transaction_history",
                "args": {
                    "user_id": "${context.user_id}",
                    "days": 30,
                    "include_pending": True,
                },
                "on_fail": "abort",
            },
            {
                "id": "step-003",
                "tool": "analytics.summarize",
                "args": {
                    "data": "${step-001.result}",
                    "group_by": "category",
                    "include_pii": True,
                    "format": "table",
                },
                "on_fail": "abort",
            },
        ],
        "meta": {
            "planner": "FinancialPlanningAgent",
            "model": "gpt-4o",
            "created_at": datetime.now().isoformat(),
        },
    },
    "excessive": {
        "goal": "Emergency fund transfer for mortgage payment",
        "context": {
            "user_id": "usr_843791",
            "user_email": "alex.morgan@example.com",
            "request_id": "req-9e854c3b",
            "session_id": "sess_3b721fa9",
            "timestamp": datetime.now().isoformat(),
            "auth_level": "verified",
            "emergency_request": True,
        },
        "steps": [
            {
                "id": "step-001",
                "tool": "db.get_account_details",
                "args": {"user_id": "${context.user_id}", "account_type": "savings"},
                "on_fail": "abort",
            },
            {
                "id": "step-002",
                "tool": "db.get_payment_details",
                "args": {"user_id": "${context.user_id}", "payment_type": "mortgage"},
                "on_fail": "abort",
            },
            {
                "id": "step-003",
                "tool": "payments.transfer",
                "args": {
                    "from_account": "${step-001.result.account_number}",
                    "to_account": "${step-002.result.payment_account}",
                    "amount": 7500.00,
                    "description": "Emergency mortgage payment",
                    "override_daily_limit": True,
                    "reason": "User indicated emergency situation",
                },
                "on_fail": "abort",
            },
        ],
        "meta": {
            "planner": "FinancialPlanningAgent",
            "model": "gpt-4o",
            "created_at": datetime.now().isoformat(),
        },
    },
    "sensitive_data": {
        "goal": "Update contact information and verify identity for Alex Morgan",
        "context": {
            "user_id": "usr_843791",
            "user_email": "alex.morgan@example.com",
            "request_id": "req-d2c7a1f6",
            "session_id": "sess_59b3e7d2",
            "timestamp": datetime.now().isoformat(),
            "auth_level": "partial",
        },
        "steps": [
            {
                "id": "step-001",
                "tool": "db.get_user_profile",
                "args": {"user_id": "${context.user_id}"},
                "on_fail": "abort",
            },
            {
                "id": "step-002",
                "tool": "identity.verify",
                "args": {
                    "user_id": "${context.user_id}",
                    "verification_method": "knowledge_based",
                    "verification_data": {
                        "ssn_last4": "7890",
                        "dob": "1985-04-15",
                        "address_line1": "123 Main Street",
                        "zip": "94103",
                    },
                },
                "on_fail": "abort",
            },
            {
                "id": "step-003",
                "tool": "db.update_user",
                "args": {
                    "user_id": "${context.user_id}",
                    "data": {
                        "email": "alex.morgan.new@example.com",
                        "phone": "415-555-9876",
                        "address": {
                            "line1": "456 Market Street",
                            "line2": "Apt 3B",
                            "city": "San Francisco",
                            "state": "CA",
                            "zip": "94105",
                        },
                    },
                    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNyXzg0Mzc5MSIsInJvbGUiOiJjdXN0b21lciIsImlhdCI6MTYxNjc2MjIwMH0.Bh8wg_zVSVJKn_d8daodEMgc-VBRv34S",
                    "sensitivity_level": "high",
                },
                "on_fail": "abort",
            },
            {
                "id": "step-004",
                "tool": "notify.customer",
                "args": {
                    "user_id": "${context.user_id}",
                    "template": "profile_updated",
                    "channel": ["email", "sms"],
                    "priority": 1,
                },
                "on_fail": "continue",
            },
        ],
        "meta": {
            "planner": "FinancialPlanningAgent",
            "model": "gpt-4o",
            "created_at": datetime.now().isoformat(),
        },
    },
}

# Add realistic user queries that would lead to these plans
USER_PROMPTS = {
    "standard": "I'd like to transfer $100 from my checking account to my savings account.",
    "harmful": "Can you show me my recent transactions? My email is alex.morgan@example.com",
    "excessive": "I need to make an emergency transfer of $7500 for my mortgage payment right away.",
    "sensitive_data": "I need to update my contact information. I've moved to 456 Market Street in San Francisco.",
}

AGENT_THINKING_SEQUENCES = [
    [
        "Analyzing the user request...",
        "Determining required operations...",
        "Planning database queries...",
        "Identifying required tools...",
        "Formulating execution steps...",
        "Generating structured plan...",
    ],
    [
        "Processing financial transaction request...",
        "Checking account requirements...",
        "Calculating transaction parameters...",
        "Determining sequence of operations...",
        "Structuring plan JSON...",
        "Finalizing execution steps...",
    ],
    [
        "Interpreting user financial request...",
        "Mapping to available tools...",
        "Planning data validation steps...",
        "Determining transaction flow...",
        "Constructing step sequence...",
        "Generating executable plan...",
    ],
]


def simulate_agent_thinking(message: str = None, fast_mode: bool = False):
    """
    Simulate the agent's thinking process with realistic typing effect.
    """
    if fast_mode:
        return

    if message:
        sys.stdout.write(f"\r{Fore.CYAN}🤖 {message}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(random.uniform(0.2, 0.5) if fast_mode else random.uniform(0.5, 1.5))
        return

    # Random thinking sequence
    thinking_sequence = random.choice(AGENT_THINKING_SEQUENCES)

    for thought in thinking_sequence:
        sys.stdout.write(f"\r{Fore.CYAN}🤖 {thought}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(random.uniform(0.2, 0.5) if fast_mode else random.uniform(0.7, 2.0))

    sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line
    sys.stdout.flush()


def simulate_typing(
    text: str,
    delay_range: Tuple[float, float] = (0.01, 0.03),
    newline: bool = True,
    fast_mode: bool = False,
):
    """
    Simulate realistic typing with variable speed.
    """
    if fast_mode:
        sys.stdout.write(text)
        if newline:
            sys.stdout.write("\n")
        sys.stdout.flush()
        return

    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(random.uniform(*delay_range))

    if newline:
        sys.stdout.write("\n")
    sys.stdout.flush()


def simulate_plan_generation(
    scenario_name: str, live_mode: bool = False, fast_mode: bool = False
):
    """
    Simulate an agent generating a plan with realistic typing and thinking effects.
    """
    plan = SAMPLE_PLANS.get(scenario_name)
    plan_json = json.dumps(plan, indent=2)

    if not live_mode:
        return plan_json

    # Simulate the agent generating the plan with thinking and typing
    sys.stdout.write(f"{Fore.GREEN}FinancialPlanningAgent: {Style.RESET_ALL}")

    if fast_mode:
        print("Generating plan...")
        # Skip thinking animation in fast mode
    else:
        simulate_typing(
            "I'll create a plan for this financial operation.",
            (0.01, 0.03),
            fast_mode=fast_mode,
        )
        # Simulate agent thinking
        simulate_agent_thinking(fast_mode=fast_mode)

    # Type out JSON plan generation
    print(f"{Fore.GREEN}FinancialPlanningAgent: {Style.RESET_ALL}Here's my plan:")
    print(f"{Fore.YELLOW}")  # Start yellow color for JSON

    # In fast mode, output the entire plan at once
    if fast_mode:
        print(plan_json)
    else:
        # Split the JSON into lines to simulate it being generated line by line
        lines = plan_json.split("\n")
        for line in lines:
            simulate_typing(line, (0.01, 0.05), fast_mode=fast_mode)

    print(f"{Style.RESET_ALL}")  # Reset color
    return plan_json


def simulate_validation_process(
    plan_json: str,
    live_mode: bool = False,
    fast_mode: bool = False,
    use_rego: bool = False,
):
    """
    Simulate the plan validation process with realistic timing and output.
    """
    if not live_mode:
        if use_rego:
            is_valid, validation_message = validate_finance_plan_rego(plan_json)
        else:
            is_valid, validation_message = validate_finance_plan(plan_json)
        return is_valid, validation_message

    # Simulate the execution agent receiving the plan
    policy_type = "Rego" if use_rego else "YAML"
    print(
        f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Validating plan against security policies ({policy_type})..."
    )

    if not fast_mode:
        time.sleep(0.5)

    # Start timing the validation
    validation_start = time.time()

    # Show validation happening in steps (quickly in fast mode)
    validation_steps = [
        ("Checking schema conformance...", 0.1 if fast_mode else 0.8),
        ("Validating tool permissions...", 0.1 if fast_mode else 0.7),
        ("Checking parameter bounds...", 0.1 if fast_mode else 0.9),
        ("Scanning for sensitive data...", 0.1 if fast_mode else 1.2),
        (
            f"Validating against {policy_type} security policy...",
            0.1 if fast_mode else 1.0,
        ),
        ("Calculating risk score...", 0.1 if fast_mode else 0.5),
    ]

    for step, delay in validation_steps:
        sys.stdout.write(f"  - {step}")
        sys.stdout.flush()
        time.sleep(delay)
        sys.stdout.write(f" {Fore.YELLOW}done{Style.RESET_ALL}\n")
        sys.stdout.flush()

    # Get the actual validation result
    if use_rego:
        is_valid, validation_message = validate_finance_plan_rego(plan_json)
    else:
        is_valid, validation_message = validate_finance_plan(plan_json)

    # Calculate elapsed time
    validation_time = time.time() - validation_start

    # Show validation time
    print(
        f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Validation completed in {validation_time:.2f} seconds"
    )

    return is_valid, validation_message


def simulate_execution(
    plan: Dict[str, Any], live_mode: bool = False, fast_mode: bool = False
):
    """
    Simulate execution of a validated plan with realistic timing and output.
    """
    if not live_mode:
        print("Executing plan...")
        print("(In a real system, the tools would be called here)")

        # Show what would be executed
        for i, step in enumerate(plan["steps"]):
            print(
                f"  Step {i + 1}: Executing {step['tool']}({', '.join(f'{k}={v}' for k, v in step['args'].items())})"
            )
        return

    # Simulate execution with timing
    print(
        f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Executing validated plan..."
    )

    if not fast_mode:
        time.sleep(0.5)

    step_delay = 0.2 if fast_mode else random.uniform(0.5, 1.5)

    for i, step in enumerate(plan["steps"]):
        step_name = f"step-{str(i + 1).zfill(3)}"
        tool_name = step["tool"]
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in step["args"].items())

        print(
            f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Executing {Fore.YELLOW}{step_name}{Style.RESET_ALL}: {tool_name}({args_str})"
        )

        # Simulate tool execution time
        time.sleep(step_delay)

        # Show a mock result
        mock_results = {
            "db.get_account_details": {
                "success": True,
                "account": {
                    "id": f"acct_{random.randint(10000, 99999)}",
                    "account_number": f"43{random.randint(1000000, 9999999)}",
                    "balance": random.uniform(500, 10000),
                    "available_balance": random.uniform(500, 10000),
                    "currency": "USD",
                    "status": "active",
                },
            },
            "db.get_transaction_history": {
                "success": True,
                "transactions": [
                    {
                        "id": f"tx{random.randint(1000, 9999)}",
                        "date": (
                            datetime.now() - timedelta(days=random.randint(1, 30))
                        ).strftime("%Y-%m-%d"),
                        "amount": random.uniform(10, 500),
                        "description": random.choice(
                            [
                                "Grocery Store",
                                "Online Purchase",
                                "Utility Bill",
                                "Restaurant",
                                "Gas Station",
                            ]
                        ),
                    }
                    for i in range(3)
                ],
            },
            "payments.transfer": {
                "success": True,
                "transaction_id": f"tx-{random.randint(10000, 99999)}",
                "status": "completed",
                "fee": "0.00",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "notify.customer": {
                "success": True,
                "notification_id": f"notif-{random.randint(10000, 99999)}",
                "channels": ["email"],
                "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "db.query_ro": {
                "success": True,
                "count": random.randint(1, 15),
                "results": [
                    {
                        "transaction_id": f"tx{random.randint(1000, 9999)}",
                        "amount": round(random.uniform(10, 1000), 2),
                        "date": (
                            datetime.now() - timedelta(days=random.randint(1, 30))
                        ).strftime("%Y-%m-%d"),
                    }
                    for i in range(3)
                ],
            },
            "db.update_user": {
                "success": True,
                "user_id": "usr_843791",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "updated",
            },
            "db.get_user_profile": {
                "success": True,
                "user": {
                    "id": "usr_843791",
                    "email": "alex.morgan@example.com",
                    "name": "Alex Morgan",
                    "status": "active",
                    "created_at": "2020-03-15T14:30:00Z",
                },
            },
            "identity.verify": {
                "success": True,
                "verification_id": f"verif-{random.randint(10000, 99999)}",
                "status": "verified",
                "score": random.uniform(0.85, 0.99),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "analytics.summarize": {
                "success": True,
                "summary": {
                    "categories": {
                        "Groceries": 342.15,
                        "Dining": 275.50,
                        "Transport": 189.75,
                        "Utilities": 324.00,
                    },
                    "total_spending": 1131.40,
                    "period": "Last 30 days",
                },
            },
            "db.get_payment_details": {
                "success": True,
                "payment": {
                    "type": "mortgage",
                    "amount": 2150.00,
                    "due_date": (datetime.now() + timedelta(days=5)).strftime(
                        "%Y-%m-%d"
                    ),
                    "payment_account": "27983516243",
                    "status": "pending",
                },
            },
        }

        result = mock_results.get(tool_name, {"success": True})

        if fast_mode:
            print(
                f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Result: Success"
            )
        else:
            print(
                f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Result: {json.dumps(result, indent=2)}"
            )

        if not fast_mode:
            time.sleep(0.2)

    print(
        f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Plan execution completed successfully."
    )


def simulate_agent_execution(
    scenario_name: str,
    live_mode: bool = False,
    fast_mode: bool = False,
    use_rego: bool = False,
):
    """
    Simulate the execution of a financial agent system with plan validation.

    In a real implementation, this would use actual agents from the OpenAI Agents SDK.
    For this example, we focus on the plan validation aspect.

    Args:
        scenario_name: Name of the scenario to run
        live_mode: Whether to show a live simulation of agent thinking and typing
        fast_mode: Whether to speed up the simulation for demos
        use_rego: Whether to use Rego policy validation instead of YAML
    """
    scenario_title = scenario_name.upper()
    divider = "=" * 60

    if live_mode:
        print(f"\n{Fore.MAGENTA}{divider}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}SCENARIO: {scenario_title}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{divider}{Style.RESET_ALL}\n")
    else:
        print(f"\n=== Scenario: {scenario_title} ===")

    # Get the sample plan and user prompt for this scenario
    plan = SAMPLE_PLANS.get(scenario_name)
    user_prompt = USER_PROMPTS.get(scenario_name, "")

    if not plan:
        print(f"Error: Scenario '{scenario_name}' not found")
        return

    # Print the user request
    if live_mode:
        print(f"{Fore.YELLOW}👤 User: {Style.RESET_ALL}{user_prompt}\n")
        if not fast_mode:
            time.sleep(0.5)
    else:
        print(f"Request: {user_prompt}\n")

    # Simulate plan generation
    plan_json = simulate_plan_generation(scenario_name, live_mode, fast_mode)

    if not live_mode:
        print("Generated Plan:")
        print(f"```json\n{plan_json}\n```\n")

    # Simulate validation
    policy_type = "Rego" if use_rego else "YAML"
    print(f"\nValidating plan with {policy_type} policy..." if not live_mode else "")
    is_valid, validation_message = simulate_validation_process(
        plan_json, live_mode, fast_mode, use_rego
    )

    if live_mode:
        result_color = Fore.GREEN if is_valid else Fore.RED
        status = "PASSED" if is_valid else "FAILED"
        print(
            f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}Validation result: {result_color}{status}{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}{validation_message}"
        )
    else:
        print(
            f"\nValidation Result ({policy_type}): {'✅ PASSED' if is_valid else '❌ FAILED'}"
        )
        print(f"{validation_message}\n")

    # In a real system, the plan would only be executed if valid
    if is_valid:
        simulate_execution(plan, live_mode, fast_mode)
    elif live_mode:
        print(
            f"{Fore.BLUE}FinancialExecutionAgent: {Style.RESET_ALL}{Fore.RED}Plan execution blocked - validation failed{Style.RESET_ALL}"
        )
    else:
        print("Plan execution blocked - validation failed")

    print("\n" + divider if live_mode else "\n" + "=" * 50)


def main():
    """
    Run the finance agent system example with different scenarios.
    """
    parser = argparse.ArgumentParser(
        description="Finance Agent System with Plan Validation"
    )
    parser.add_argument(
        "--simulated",
        "-s",
        action="store_true",
        help="Show a live simulation of agent interactions",
    )
    parser.add_argument(
        "--fast",
        "-f",
        action="store_true",
        help="Run the simulation in fast mode for demos",
    )
    parser.add_argument(
        "--scenario",
        "-sc",
        choices=["standard", "harmful", "excessive", "sensitive_data"],
        help="Run a specific scenario",
    )
    parser.add_argument(
        "--rego",
        "-r",
        action="store_true",
        help="Use Rego policy validation instead of YAML",
    )
    args = parser.parse_args()

    # Set modes based on arguments
    live_mode = args.simulated
    fast_mode = args.fast
    use_rego = args.rego

    # Enable fast mode automatically if both simulated and fast are specified
    if live_mode and fast_mode:
        print(f"{Fore.CYAN}Running in fast demo mode...{Style.RESET_ALL}")

    # Intro header
    if live_mode:
        print(f"{Fore.GREEN}{'=' * 80}{Style.RESET_ALL}")
        policy_type = "REGO" if use_rego else "YAML"
        print(
            f"{Fore.GREEN}📊 FINANCE AGENT SYSTEM WITH REAL-TIME PLAN VALIDATION ({policy_type}){Style.RESET_ALL}"
        )
        print(f"{Fore.GREEN}{'=' * 80}{Style.RESET_ALL}")
        print(
            "This example shows how agent-generated plans are validated in real time before execution.\n"
        )
    else:
        print("=== Finance Agent System with Plan Validation ===")
        policy_type = "Rego" if use_rego else "YAML"
        print(
            f"This example demonstrates how plan-lint can validate agent-generated plans using {policy_type} policies"
        )
        print(
            "before they are executed, intercepting potentially harmful operations.\n"
        )

    # Run scenarios
    if args.scenario:
        # Run a specific scenario if requested
        simulate_agent_execution(args.scenario, live_mode, fast_mode, use_rego)
    else:
        # Run all scenarios
        for scenario in ["standard", "harmful", "excessive", "sensitive_data"]:
            simulate_agent_execution(scenario, live_mode, fast_mode, use_rego)

    # Conclusion
    if live_mode:
        print(f"\n{Fore.GREEN}💡 SIMULATION COMPLETE{Style.RESET_ALL}")
        print("This demonstrates how plan-lint creates a security layer between:")
        print(f"  1. {Fore.CYAN}LLM agents that generate plans{Style.RESET_ALL}")
        print(f"  2. {Fore.BLUE}Execution systems that carry them out{Style.RESET_ALL}")
        print("Preventing potentially harmful operations from executing.")
    else:
        print("\nExample complete. In a real agent system:")
        print("1. Plans would be generated by LLM agents")
        print(
            f"2. plan-lint would validate them against {policy_type} policies before execution"
        )
        print("3. Only validated plans would be executed by the agent system")


if __name__ == "__main__":
    main()
