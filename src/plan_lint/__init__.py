"""Plan-Lint - Static analysis toolkit for LLM agent plans."""

from plan_lint.core import validate_plan
from plan_lint.types import PlanError, ValidationResult

__version__ = "0.0.2"
__all__ = ["validate_plan", "ValidationResult", "PlanError"]
