"""
Finance Agent System built with OpenAI Agents SDK.

This system demonstrates a realistic multi-agent architecture with plan validation
for financial operations, showing how plan-lint can be integrated to catch
potentially dangerous operations before they are executed.
"""

import asyncio
import json
import os
from typing import Any, Dict

from agents import Agent, Runner, Tool
from validator import validate_finance_plan

# Sample data for simulation
SAMPLE_ACCOUNTS = {
    "12345": {"name": "Alice Smith", "balance": 8500.00, "type": "checking"},
    "54321": {"name": "Bob Johnson", "balance": 12350.75, "type": "savings"},
    "98765": {"name": "Carol Davis", "balance": 2340.12, "type": "checking"},
}

TRANSACTION_HISTORY = [
    {
        "id": "tx001",
        "from": "12345",
        "to": "54321",
        "amount": 500.00,
        "date": "2023-05-15",
    },
    {
        "id": "tx002",
        "from": "54321",
        "to": "98765",
        "amount": 250.00,
        "date": "2023-05-17",
    },
    {
        "id": "tx003",
        "from": "98765",
        "to": "12345",
        "amount": 125.00,
        "date": "2023-05-20",
    },
]


# Tool implementations for the finance system
def query_account(account_id: str) -> Dict[str, Any]:
    """Query account details."""
    if account_id in SAMPLE_ACCOUNTS:
        return {"success": True, "account": SAMPLE_ACCOUNTS[account_id]}
    return {"success": False, "error": "Account not found"}


def get_transactions(account_id: str, days: int = 30) -> Dict[str, Any]:
    """Get transaction history for an account."""
    if account_id not in SAMPLE_ACCOUNTS:
        return {"success": False, "error": "Account not found"}

    # In real system, would filter by date
    transactions = [
        tx
        for tx in TRANSACTION_HISTORY
        if tx["from"] == account_id or tx["to"] == account_id
    ]

    return {"success": True, "transactions": transactions}


def execute_transfer(
    from_account: str, to_account: str, amount: float
) -> Dict[str, Any]:
    """Execute a transfer between accounts."""
    # In a real system, this would actually perform the transfer
    # Here we just validate the accounts exist
    if from_account not in SAMPLE_ACCOUNTS:
        return {"success": False, "error": "Source account not found"}

    if to_account not in SAMPLE_ACCOUNTS:
        return {"success": False, "error": "Destination account not found"}

    if SAMPLE_ACCOUNTS[from_account]["balance"] < amount:
        return {"success": False, "error": "Insufficient funds"}

    return {
        "success": True,
        "transaction_id": "tx" + str(len(TRANSACTION_HISTORY) + 1).zfill(3),
        "from": from_account,
        "to": to_account,
        "amount": amount,
    }


# Create the planning agent
planning_agent = Agent(
    name="FinancialPlanningAgent",
    instructions="""
    You are a financial planning agent that creates plans for financial operations.
    
    When a user requests a financial operation, you must:
    
    1. Create a structured JSON plan with specific steps to execute
    2. Each step should use one of the allowed financial tools
    3. Structure your plan in this format:
    
    {
      "goal": "Description of what we're trying to accomplish",
      "context": {
        "user_id": "user identifier",
        "relevant_context": "any other relevant context"
      },
      "steps": [
        {
          "id": "step-001",
          "tool": "tool_name",
          "args": {"param1": "value1", "param2": "value2"},
          "on_fail": "abort"
        },
        ...additional steps...
      ],
      "meta": {
        "planner": "FinancialPlanningAgent",
        "created_at": "current_timestamp"
      }
    }
    
    Remember that your plans will be validated for security before execution.
    """,
)

# Tools for the execution agent
plan_validation_tool = Tool.from_function(
    function=validate_finance_plan,
    name="validate_plan",
    description="Validates a financial operation plan for security and compliance",
)

account_query_tool = Tool.from_function(
    function=query_account,
    name="db.get_account_details",
    description="Get details for a specific account",
)

transaction_history_tool = Tool.from_function(
    function=get_transactions,
    name="db.get_transaction_history",
    description="Get transaction history for an account",
)

transfer_tool = Tool.from_function(
    function=execute_transfer,
    name="payments.transfer",
    description="Execute a transfer between accounts",
)

# Create the execution agent
execution_agent = Agent(
    name="FinancialExecutionAgent",
    instructions="""
    You are a financial execution agent that executes validated plans.
    
    IMPORTANT: You must ALWAYS validate plans before executing them.
    
    For any financial plan given to you:
    
    1. First use the validate_plan tool to check if the plan is secure
    2. If the plan fails validation, explain why and DO NOT proceed with execution
    3. If the plan passes validation, execute each step in order using the appropriate tools
    4. Report the result of each step's execution
    
    Safety is your top priority. Never execute a plan that fails validation.
    """,
    tools=[
        plan_validation_tool,
        account_query_tool,
        transaction_history_tool,
        transfer_tool,
    ],
)

# Create an analysis agent
analysis_agent = Agent(
    name="FinancialAnalysisAgent",
    instructions="""
    You are a financial analysis agent that examines transaction patterns.
    
    You can access account details and transaction history, but you CANNOT
    modify account data or execute transactions.
    
    Always validate any plan before analyzing data.
    """,
    tools=[plan_validation_tool, account_query_tool, transaction_history_tool],
)

# Orchestrator agent to coordinate the system
orchestrator_agent = Agent(
    name="FinancialOrchestratorAgent",
    instructions="""
    You are the orchestrator for a financial agent system.
    
    Your job is to:
    1. Understand the user's request
    2. Determine which specialized agent should handle it
    3. Convert the request into an appropriate input for that agent
    
    For planning financial operations: Use the planning agent
    For executing validated plans: Use the execution agent
    For analyzing transaction data: Use the analysis agent
    
    Always ensure that any plan is validated before execution.
    """,
)


# Main function to run different scenarios
async def handle_financial_request(request: str, scenario: str = "standard") -> str:
    """
    Process a financial request through the agent system.

    Args:
        request: The user's financial request
        scenario: Which scenario to demonstrate ("standard", "harmful", "excessive")

    Returns:
        Result of processing the request
    """
    # First, have the orchestrator understand the request
    # We keep the result variable even though it's not used directly,
    # as we want the orchestrator to process the request
    _ = await orchestrator_agent.run(query=request, params={"user_context": request})

    # Get the planning agent to create a plan
    planning_message = f"Create a step-by-step plan to: {request}"
    planning_result = await Runner.run(planning_agent, planning_message)

    # Extract the plan JSON
    plan_json = planning_result.final_output

    # Simulate the different scenarios by injecting issues into the plan
    try:
        plan_data = json.loads(plan_json)

        # For harmful scenario, inject SQL injection
        if scenario == "harmful":
            for step in plan_data.get("steps", []):
                if step.get("tool", "").startswith("db."):
                    if "query" in step.get("args", {}):
                        step["args"]["query"] += " OR 1=1"
                    elif "account_id" in step.get("args", {}):
                        step["args"]["account_id"] += "'; DROP TABLE accounts; --"

        # For excessive scenario, set amount too high
        elif scenario == "excessive":
            for step in plan_data.get("steps", []):
                if step.get("tool", "") == "payments.transfer" and "amount" in step.get(
                    "args", {}
                ):
                    step["args"]["amount"] = 15000.00  # Exceeds policy limit

        # Convert back to JSON
        plan_json = json.dumps(plan_data, indent=2)
    except json.JSONDecodeError:
        # If we can't parse the JSON, leave it as is
        pass

    # Have execution agent validate and execute the plan
    execution_message = f"""
    I have a financial operation plan to execute:
    
    ```json
    {plan_json}
    ```
    
    Please validate this plan and if it passes validation, execute it.
    If it fails validation, explain why and don't execute it.
    """

    execution_result = await Runner.run(execution_agent, execution_message)

    return execution_result.final_output


# Example usage
async def main():
    """Run example scenarios."""
    scenarios = {
        "standard": "Transfer $100 from account 12345 to account 54321",
        "harmful": "Get transaction history for account 12345",
        "excessive": "Transfer $7000 from account 54321 to account 98765",
    }

    print("=== Finance Agent System with Plan Validation ===\n")

    for name, request in scenarios.items():
        print(f"\n=== Scenario: {name.upper()} ===")
        print(f"Request: {request}\n")
        result = await handle_financial_request(request, name)
        print(f"Result:\n{result}\n")
        print("=" * 50)


if __name__ == "__main__":
    # Ensure OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your_key_here")
        exit(1)

    asyncio.run(main())
