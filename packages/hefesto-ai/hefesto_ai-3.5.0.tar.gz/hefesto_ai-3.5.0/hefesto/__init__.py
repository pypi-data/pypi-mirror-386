"""
HEFESTO - AI-Powered Code Quality Guardian

An autonomous agent that provides intelligent code refactoring,
security analysis, and quality assurance using Gemini AI.

Copyright © 2025 Narapa LLC, Miami, Florida
"""

from hefesto.__version__ import __version__

# Core exports (Phase 0 - Free)
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

# Pro exports (Phase 1 - Paid)
try:
    from hefesto.llm.semantic_analyzer import (
        SemanticAnalyzer,
        CodeEmbedding,
        get_semantic_analyzer,
    )
    from hefesto.llm.cicd_feedback_collector import (
        CICDFeedbackCollector,
        DeploymentFeedback,
        TestFeedback,
        get_cicd_collector,
    )
    _PRO_FEATURES_AVAILABLE = True
except ImportError:
    _PRO_FEATURES_AVAILABLE = False


__all__ = [
    "__version__",
    # Phase 0
    "SuggestionValidator",
    "SuggestionValidationResult",
    "get_validator",
    "FeedbackLogger",
    "SuggestionFeedback",
    "get_feedback_logger",
    "BudgetTracker",
    "TokenUsage",
    "get_budget_tracker",
]

# Add Pro features if available
if _PRO_FEATURES_AVAILABLE:
    __all__.extend([
        "SemanticAnalyzer",
        "CodeEmbedding",
        "get_semantic_analyzer",
        "CICDFeedbackCollector",
        "DeploymentFeedback",
        "TestFeedback",
        "get_cicd_collector",
    ])


def is_pro() -> bool:
    """Check if Pro features are available."""
    return _PRO_FEATURES_AVAILABLE


def get_info() -> dict:
    """Get package information."""
    return {
        "version": __version__,
        "pro_features": _PRO_FEATURES_AVAILABLE,
        "license": "Dual (MIT + Commercial)",
    }

