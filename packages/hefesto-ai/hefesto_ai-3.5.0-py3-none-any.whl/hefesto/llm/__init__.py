"""LLM integration modules for Hefesto."""

# Phase 0 (Free - MIT License)
from hefesto.llm.suggestion_validator import (
    SuggestionValidator,
    SuggestionValidationResult,
    get_validator,
)
from hefesto.llm.feedback_logger import (
    FeedbackLogger,
    SuggestionFeedback,
    get_feedback_logger,
)
from hefesto.llm.budget_tracker import (
    BudgetTracker,
    TokenUsage,
    get_budget_tracker,
)
from hefesto.llm.validators import (
    validate_syntax,
    validate_no_secrets,
    validate_safe_category,
    validate_function_structure,
)

__all__ = [
    # Validators
    "SuggestionValidator",
    "SuggestionValidationResult",
    "get_validator",
    "validate_syntax",
    "validate_no_secrets",
    "validate_safe_category",
    "validate_function_structure",
    # Feedback
    "FeedbackLogger",
    "SuggestionFeedback",
    "get_feedback_logger",
    # Budget
    "BudgetTracker",
    "TokenUsage",
    "get_budget_tracker",
]

# Phase 1 (Pro - Commercial License)
try:
    from hefesto.llm.semantic_analyzer import (
        SemanticAnalyzer,
        CodeEmbedding,
        get_semantic_analyzer,
    )
    __all__.extend([
        "SemanticAnalyzer",
        "CodeEmbedding",
        "get_semantic_analyzer",
    ])
    _PRO_AVAILABLE = True
except ImportError:
    _PRO_AVAILABLE = False

