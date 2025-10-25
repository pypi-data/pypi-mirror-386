"""Workflow implementations package.

Contains all concrete workflow implementations organized by functionality.

Responsibility: Workflow implementation organization only.
Individual workflow logic belongs in specific implementation modules.

maxwell/src/maxwell/workflow/implementations/__init__.py
"""

# Import all workflows to trigger @register_workflow decorators
# Chat workflows are optional (require extra dependencies)
try:
    from . import chat  # noqa: F401 - Import to trigger @register_workflow decorators

    _chat_available = True
except ImportError:
    _chat_available = False

from . import justification, snapshot, tag_refactor, utilities, validate  # Import other workflows

# Import available implementations - avoid circular imports by importing lazily
__all__ = [
    # Submodules (imported for @register_workflow decorator side effects)
    "justification",
    "snapshot",
    "tag_refactor",
    "utilities",
    "validate",
    # Helper functions for lazy imports
    "get_justification_engine",
    "get_tag_refactor_workflow",
    "run_tag_refactor",
]

# Add chat to __all__ if available
if _chat_available:
    __all__.insert(0, "chat")


# Lazy imports to avoid circular dependencies
def get_justification_engine():  # type: ignore[no-untyped-def]
    """Get JustificationEngine class."""
    from .justification import JustificationEngine

    return JustificationEngine


def get_tag_refactor_workflow():  # type: ignore[no-untyped-def]
    """Get TagRefactorWorkflow class."""
    from .tag_refactor import TagRefactorWorkflow

    return TagRefactorWorkflow


def run_tag_refactor(*args, **kwargs):  # type: ignore[no-untyped-def]
    """Run tag refactoring workflow (convenience function)."""
    from .tag_refactor import run_tag_refactor as _run

    return _run(*args, **kwargs)
