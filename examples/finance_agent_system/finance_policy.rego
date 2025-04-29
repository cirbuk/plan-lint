package planlint

# Financial Operations Security Policy
# Used by plan-linter to validate all agent-generated plans

# Default deny policy - all tools are denied unless explicitly allowed
default allow = false

# Default empty violations
default violations = []

# Default risk score is 0
default risk_score = 0.0

# Set of allowed tools for financial transactions
allowed_tools = {
    "make_transaction": {"min_amount": 0.01, "max_amount": 10000},
    "query_balance": {},
    "get_account_details": {},
    "query_transaction_history": {},
    "analyze_spending": {},
    "generate_report": {}
}

# Allow if all tools are allowed and risk score below threshold
allow if {
    all_tools_allowed
    risk_score < 0.8
}

# Check if all tools in the plan are allowed
all_tools_allowed if {
    # For every step in the plan
    steps := input.steps
    forbidden_tools := [tool | 
        tool := steps[_].tool
        not tool in object.keys(allowed_tools)
    ]
    count(forbidden_tools) == 0
}

# Set the risk score
risk_score = result if {
    result := calculate_risk_score
}

# Collect all violations for the response
violations = all_violations if {
    # Collect all types of violations
    all_violations := collect_violations
}

# Collect violations from all checks
collect_violations = result if {
    # Check each step for violations
    steps := input.steps
    tool_violations := [v |
        i := numbers.range(0, count(steps) - 1)[_]
        v := check_tool_bounds(i)
        v != null
    ]
    sensitive_data_violations := [v |
        i := numbers.range(0, count(steps) - 1)[_]
        v := check_sensitive_data(i)
        v != null
    ]
    sql_injection_violations := [v |
        i := numbers.range(0, count(steps) - 1)[_]
        v := check_sql_injection(i)
        v != null
    ]
    
    # Combine all violations
    result := array.concat(
        tool_violations,
        array.concat(
            sensitive_data_violations,
            sql_injection_violations
        )
    )
}

# Calculate risk score based on violations
calculate_risk_score = result if {
    # Get all violations
    all_violations := collect_violations
    
    # Base risk if exceeding bounds
    base_risk := 0.6
    
    # Additional risk per violation type
    additional_risk := {
        "EXCESSIVE_AMOUNT": 0.2,
        "INSUFFICIENT_AMOUNT": 0.1,
        "SENSITIVE_DATA": 0.2,
        "SQL_INJECTION": 0.4
    }
    
    # Calculate total risk by adding up all violations
    total_additional_risk := sum([additional_risk[v.code] | v := all_violations[_]])
    
    # Calculate score with base risk if there are violations
    has_violations := count(all_violations) > 0
    
    # Use base risk only if there are violations
    base_component := get_base_component(has_violations, base_risk)
    
    intermediate_score := base_component + total_additional_risk
    
    # Cap the risk score at 1.0
    result := cap_at_one(intermediate_score)
}

# Helper to get base component
get_base_component(has_violations, base_risk) = base_risk if {
    has_violations == true
}

get_base_component(has_violations, base_risk) = 0.0 if {
    has_violations == false
}

# Helper to cap a value at 1.0
cap_at_one(value) = capped if {
    value > 1.0
    capped := 1.0
}

cap_at_one(value) = value if {
    value <= 1.0
}

# Check if any transaction is too large
check_tool_bounds(i) = violation if {
    step := input.steps[i]
    step.tool == "make_transaction"
    amount := to_number(step.args.amount)
    tool_bounds := allowed_tools[step.tool]
    amount > tool_bounds.max_amount
    
    violation := {
        "step": i,
        "code": "EXCESSIVE_AMOUNT",
        "msg": sprintf("Transaction amount %f exceeds maximum limit of %f", [amount, tool_bounds.max_amount])
    }
}

# Check if any transaction is too small
check_tool_bounds(i) = violation if {
    step := input.steps[i]
    step.tool == "make_transaction"
    amount := to_number(step.args.amount)
    tool_bounds := allowed_tools[step.tool]
    amount < tool_bounds.min_amount
    
    violation := {
        "step": i,
        "code": "INSUFFICIENT_AMOUNT",
        "msg": sprintf("Transaction amount %f is below minimum limit of %f", [amount, tool_bounds.min_amount])
    }
}

# Check for potential sensitive data patterns
check_sensitive_data(i) = violation if {
    step := input.steps[i]
    
    # Define sensitive patterns
    patterns := ["password", "secret", "ssn", "socialSecurity", "creditCard", "account"]
    
    # Convert args to string
    arg_values := [lower(step.args[k]) | k := object.keys(step.args)[_]; k != "headers"]
    args_str := concat(" ", arg_values)
    
    # Check if any pattern is present
    some pattern
    contains(args_str, patterns[pattern])
    
    violation := {
        "step": i,
        "code": "SENSITIVE_DATA",
        "msg": "Potentially sensitive data pattern found in arguments"
    }
}

# Check for SQL injection patterns
check_sql_injection(i) = violation if {
    step := input.steps[i]
    
    # Define SQL injection patterns
    patterns := ["DROP TABLE", "DELETE FROM", "SELECT *", ";", "--", "1=1", "OR 1=1"]
    
    # Convert args to string
    arg_values := [lower(step.args[k]) | k := object.keys(step.args)[_]; k != "headers"]
    args_str := concat(" ", arg_values)
    
    # Check if any pattern is present
    some pattern
    pattern_lower := lower(patterns[pattern])
    contains(args_str, pattern_lower)
    
    violation := {
        "step": i,
        "code": "SQL_INJECTION",
        "msg": "Potential SQL injection pattern detected"
    }
}

# Metadata about the policy
metadata = {
    "name": "Financial Operations Security Policy",
    "version": "1.0",
    "description": "Policy for validating finance agent plans"
} 