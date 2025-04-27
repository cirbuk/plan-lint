"""
Type definitions for plan-linter.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Status(str, Enum):
    """Status of a plan validation."""

    PASS = "pass"
    WARN = "warn"
    ERROR = "error"


class ErrorCode(str, Enum):
    """Error codes for plan validation failures."""

    SCHEMA_INVALID = "SCHEMA_INVALID"
    TOOL_DENY = "TOOL_DENY"
    BOUND_VIOLATION = "BOUND_VIOLATION"
    RAW_SECRET = "RAW_SECRET"
    LOOP_DETECTED = "LOOP_DETECTED"
    MAX_STEPS_EXCEEDED = "MAX_STEPS_EXCEEDED"
    MISSING_HANDLER = "MISSING_HANDLER"


class PlanError(BaseModel):
    """An error found during plan validation."""

    step: Optional[int] = None
    code: ErrorCode
    msg: str


class PlanWarning(BaseModel):
    """A warning found during plan validation."""

    step: Optional[int] = None
    code: str
    msg: str


class PlanStepArg(BaseModel):
    """A single argument for a plan step."""

    name: str
    value: Any


class PlanStep(BaseModel):
    """A single step in a plan."""

    id: str
    tool: str
    args: Dict[str, Any]
    on_fail: str = "abort"


class Plan(BaseModel):
    """A complete plan to be validated."""

    goal: str
    context: Optional[Dict[str, Any]] = Field(default_factory=lambda: {})
    steps: List[PlanStep]
    meta: Optional[Dict[str, Any]] = Field(default_factory=lambda: {})


class PolicyRule(BaseModel):
    """A single policy rule."""

    name: str
    description: str


class Policy(BaseModel):
    """A complete policy for plan validation."""

    allow_tools: List[str] = Field(default_factory=list)
    bounds: Dict[str, List[Union[int, float]]] = Field(default_factory=lambda: {})
    deny_tokens_regex: List[str] = Field(default_factory=list)
    max_steps: int = 100
    risk_weights: Dict[str, float] = Field(default_factory=lambda: {})
    fail_risk_threshold: float = 0.8


class ValidationResult(BaseModel):
    """Result of a plan validation."""

    status: Status
    risk_score: float
    errors: List[PlanError] = Field(default_factory=list)
    warnings: List[PlanWarning] = Field(default_factory=list)
