# API Reference

This document provides detailed information about the Plan-Lint API, including the main functions, classes, and their parameters.

## Core Functions

### `validate_plan`

The primary function for validating plans against policies.

```python
def validate_plan(
    plan: Dict[str, Any],
    policies: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Validate a plan against policies.
    
    Args:
        plan: The plan to validate, containing steps and their tools/parameters
        policies: Optional list of paths to policy files. If None, uses default policies
        context: Optional context information to provide to the policies
        config: Optional configuration for the validation process
    
    Returns:
        A ValidationResult object containing validation results
    """
```

### `load_policy`

Load a Rego policy from a file.

```python
def load_policy(
    policy_path: str
) -> str:
    """
    Load a Rego policy file.
    
    Args:
        policy_path: Path to the Rego policy file
    
    Returns:
        The policy content as a string
    
    Raises:
        FileNotFoundError: If the policy file doesn't exist
    """
```

### `format_plan`

Format a plan to ensure it meets the expected structure for validation.

```python
def format_plan(
    plan: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format a plan to ensure it has the expected structure.
    
    Args:
        plan: The plan to format
    
    Returns:
        The formatted plan
    """
```

## Classes

### `ValidationResult`

Contains the results of plan validation.

```python
class ValidationResult:
    """
    Result of a plan validation.
    
    Attributes:
        valid (bool): Whether the plan is valid according to all policies
        violations (List[PolicyViolation]): List of policy violations found
        details (Dict[str, Any]): Additional details about the validation
    
    Methods:
        to_dict(): Convert the result to a dictionary
        to_json(): Convert the result to a JSON string
    """
    
    @property
    def valid(self) -> bool:
        """Whether the plan is valid (no violations)."""
    
    @property
    def violations(self) -> List["PolicyViolation"]:
        """List of policy violations."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
    
    def to_json(self, **kwargs) -> str:
        """Convert the result to a JSON string."""
```

### `PolicyViolation`

Represents a violation of a policy rule.

```python
class PolicyViolation:
    """
    Represents a violation of a policy rule.
    
    Attributes:
        rule (str): The policy rule that was violated
        message (str): Description of the violation
        severity (str): Severity level ('low', 'medium', 'high', 'critical')
        category (str): Category of the violation (e.g., 'security', 'privacy')
        step_id (Optional[str]): ID of the step that caused the violation
        metadata (Dict[str, Any]): Additional metadata about the violation
    """
    
    @property
    def rule(self) -> str:
        """The policy rule that was violated."""
    
    @property
    def message(self) -> str:
        """Description of the violation."""
    
    @property
    def severity(self) -> str:
        """Severity level of the violation."""
    
    @property
    def category(self) -> str:
        """Category of the violation."""
    
    @property
    def step_id(self) -> Optional[str]:
        """ID of the step that caused the violation, if applicable."""
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata about the violation."""
```

### `PolicyEngine`

Manages policy evaluation using the Open Policy Agent.

```python
class PolicyEngine:
    """
    Engine for evaluating Rego policies against plans.
    
    Methods:
        evaluate(plan, policies, context): Evaluate policies against a plan
    """
    
    def evaluate(
        self,
        plan: Dict[str, Any],
        policies: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate policies against a plan.
        
        Args:
            plan: The plan to evaluate
            policies: List of policy file paths
            context: Optional context information
        
        Returns:
            Evaluation results as a dictionary
        """
```

## CLI Commands

### `plan-lint validate`

Command-line interface for validating plans.

```
Usage: plan-lint validate [OPTIONS] PLAN_FILE

  Validate a plan against policies.

Options:
  --policies PATH...  Custom policy files to use
  --context FILE      JSON file containing context information
  --output FORMAT     Output format (text, json, yaml) [default: text]
  --config FILE       Configuration file
  --help              Show this message and exit
```

### `plan-lint test`

Command-line interface for testing policies.

```
Usage: plan-lint test [OPTIONS] [TEST_DIR]

  Run policy tests.

Options:
  --policies PATH...  Custom policy files to test
  --verbose           Show detailed test output
  --help              Show this message and exit
```

## Constants

### Severity Levels

```python
class Severity:
    """Severity levels for policy violations."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### Violation Categories

```python
class Category:
    """Categories for policy violations."""
    
    SECURITY = "security"
    PRIVACY = "privacy"
    AUTHORIZATION = "authorization"
    COMPLIANCE = "compliance"
    RESOURCE = "resource"
    GENERAL = "general"
```

## Error Classes

### `PolicyError`

Base class for policy-related errors.

```python
class PolicyError(Exception):
    """Base class for policy-related errors."""
```

### `PolicyLoadError`

Error raised when a policy cannot be loaded.

```python
class PolicyLoadError(PolicyError):
    """Raised when a policy cannot be loaded."""
```

### `PolicyEvaluationError`

Error raised when policy evaluation fails.

```python
class PolicyEvaluationError(PolicyError):
    """Raised when policy evaluation fails."""
```

## Utility Functions

### `get_default_policies`

Get the paths to the default policy files.

```python
def get_default_policies() -> List[str]:
    """
    Get the paths to the default policy files.
    
    Returns:
        List of paths to default policy files
    """
```

### `load_context`

Load context information from a file.

```python
def load_context(context_path: str) -> Dict[str, Any]:
    """
    Load context information from a JSON file.
    
    Args:
        context_path: Path to the context file
    
    Returns:
        Context information as a dictionary
    
    Raises:
        FileNotFoundError: If the context file doesn't exist
        json.JSONDecodeError: If the context file is not valid JSON
    """
``` 