"""Maxwell: Code Quality and Style Validator

A focused code analysis tool for Python projects.
"""

from pathlib import Path

from maxwell.config import MaxwellConfig, load_config
from maxwell.lm_pool import LLMPool, get_lm
from maxwell.types import LLMSpec
from maxwell.utils import get_session_id, get_timestamp, normalize_path
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowMetrics,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

__version__ = "0.1.0"


# Lazy import for workflows to avoid circular dependencies
from maxwell.registry import register_workflow


def refactor_tags(project_root: str | Path | None = None, dry_run: bool = False) -> WorkflowResult:
    """Refactor semantic HTML tags in markdown files.

    Args:
        project_root: Directory to process (defaults to current directory)
        dry_run: If True, preview changes without modifying files

    Returns:
        WorkflowResult with refactoring statistics

    Example:
        >>> import maxwell
        >>> result = maxwell.refactor_tags(dry_run=True)
        >>> print(f"Would modify {len(result.artifacts['modified_files'])} files")

    """
    from pathlib import Path

    from maxwell.workflows.tag_refactor import run_tag_refactor

    path = Path(project_root) if project_root else Path.cwd()
    return run_tag_refactor(path, dry_run=dry_run)  # type: ignore[no-any-return]


__all__ = [
    # Configuration
    "MaxwellConfig",
    "load_config",
    # LM Pool
    "get_lm",
    "LLMPool",
    "LLMSpec",
    # Utilities
    "get_session_id",
    "get_timestamp",
    "normalize_path",
    # Workflow Base Classes
    "BaseWorkflow",
    "WorkflowConfig",
    "WorkflowMetrics",
    "WorkflowPriority",
    "WorkflowResult",
    "WorkflowStatus",
    "register_workflow",
    # Workflows
    "refactor_tags",
]
