"""Tag refactoring workflow for markdown documentation.

Formats semantic HTML tags (like <mithranm>, <claude>) in markdown files
to be on separate lines for improved readability and consistency.

This is a linting/formatting operation that ensures documentation tags
follow a consistent style across projects.

maxwell/src/maxwell/workflows/implementations/tag_refactor.py
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

__all__ = ["TagRefactorWorkflow", "refactor_tags_in_file", "refactor_tags_in_content"]


def refactor_tags_in_content(content: str) -> str:
    r"""Format semantic HTML tags to be on separate lines for readability.

    Only modifies custom tags (like <mithranm>, <claude>), leaves standard
    markdown/HTML tags alone.

    Args:
        content: Markdown content to process

    Returns:
        Reformatted content with tags on separate lines

    Examples:
        >>> content = '<mithranm topic="test">Question here</mithranm>'
        >>> refactor_tags_in_content(content)
        '\\n<mithranm topic="test">\\nQuestion here\\n</mithranm>\\n'

    """
    # Pattern to match opening tags like <mithranm ...> or <claude ...>
    # Captures: tag name and attributes
    opening_pattern = r"<(\w+)([^>]*)>"

    # Pattern to match closing tags like </mithranm> or </claude>
    closing_pattern = r"</(\w+)>"

    # Standard HTML/markdown tags to skip
    standard_tags = {
        "sup",
        "span",
        "a",
        "img",
        "div",
        "p",
        "br",
        "hr",
        "em",
        "strong",
        "code",
        "pre",
    }

    def format_opening_tag(match):
        tag_name = match.group(1)
        attributes = match.group(2)

        # Only format custom tags, skip standard HTML
        if tag_name.lower() in standard_tags:
            return match.group(0)

        # Put tag on its own line with newline after
        return f"\n<{tag_name}{attributes}>\n"

    def format_closing_tag(match):
        tag_name = match.group(1)

        # Only format custom tags
        if tag_name.lower() in standard_tags:
            return match.group(0)

        # Put closing tag on its own line with newline after
        return f"\n</{tag_name}>\n"

    # Apply formatting
    result = re.sub(opening_pattern, format_opening_tag, content)
    result = re.sub(closing_pattern, format_closing_tag, result)

    # Clean up excessive newlines (more than 2 in a row)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def refactor_tags_in_file(file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Refactor tags in a single markdown file.

    Args:
        file_path: Path to markdown file
        dry_run: If True, don't write changes, just report what would change

    Returns:
        Dict with keys:
            - success: bool
            - modified: bool (whether content changed)
            - error: Optional[str]
            - original_size: int
            - new_size: int

    """
    try:
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Refactor
        refactored_content = refactor_tags_in_content(original_content)

        # Check if modified
        modified = refactored_content != original_content

        # Write back if not dry run and content changed
        if modified and not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(refactored_content)

        return {
            "success": True,
            "modified": modified,
            "error": None,
            "original_size": len(original_content),
            "new_size": len(refactored_content),
        }

    except Exception as e:
        logger.error(f"Failed to refactor {file_path}: {e}")
        return {
            "success": False,
            "modified": False,
            "error": str(e),
            "original_size": 0,
            "new_size": 0,
        }


@register_workflow
class TagRefactorWorkflow(BaseWorkflow):
    """Workflow for refactoring semantic tags in markdown files.

    This workflow scans markdown files for custom semantic HTML tags
    (like <mithranm>, <claude>) and reformats them to be on separate
    lines for improved readability.

    Configuration parameters:
        - dry_run: bool - If True, report changes without modifying files
        - include_patterns: List[str] - Glob patterns for files to include
        - exclude_patterns: List[str] - Glob patterns for files to exclude
    """

    workflow_id = "tag_refactor"
    name = "Tag Refactoring"
    description = "Format semantic HTML tags in markdown files"
    version = "1.0"
    category = "formatting"
    tags = {"markdown", "formatting", "linting", "documentation"}

    def __init__(self):
        self.workflow_id = "tag_refactor"
        self.name = "Tag Refactoring"
        self.description = "Format semantic HTML tags in markdown files"
        self.version = "1.0"
        super().__init__()

    def get_required_inputs(self) -> Set[str]:
        """No required inputs - operates on filesystem."""
        return set()

    def get_produced_outputs(self) -> Set[str]:
        """Produces list of modified files."""
        return {"modified_files", "tag_refactor_stats"}

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=600,  # 10 minutes
            parameters={
                "root_dir": str(root_dir),
            },
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute tag refactoring on markdown files.

        Args:
            project_root: Root directory of the project
            context: Execution context with parameters

        Returns:
            WorkflowResult with findings and statistics

        """
        dry_run = self.config.parameters.get("dry_run", False)
        include_patterns = self.config.parameters.get("include_patterns", ["**/*.md"])
        exclude_patterns = self.config.parameters.get("exclude_patterns", [])

        # Find markdown files
        markdown_files = []
        for pattern in include_patterns:
            markdown_files.extend(project_root.glob(pattern))

        # Filter out exclusions
        excluded = set()
        for pattern in exclude_patterns:
            excluded.update(project_root.glob(pattern))

        markdown_files = [f for f in markdown_files if f not in excluded and f.is_file()]

        logger.info(f"Found {len(markdown_files)} markdown files to process")

        # Process each file
        modified_files = []
        stats = {
            "total_files": len(markdown_files),
            "modified_files": 0,
            "failed_files": 0,
            "total_size_before": 0,
            "total_size_after": 0,
        }

        findings = []

        for file_path in markdown_files:
            result = refactor_tags_in_file(file_path, dry_run=dry_run)

            stats["total_size_before"] += result["original_size"]
            stats["total_size_after"] += result["new_size"]

            if not result["success"]:
                stats["failed_files"] += 1
                findings.append(
                    {
                        "type": "error",
                        "file": str(file_path.relative_to(project_root)),
                        "message": result["error"],
                    }
                )
                continue

            if result["modified"]:
                stats["modified_files"] += 1
                modified_files.append(str(file_path.relative_to(project_root)))
                findings.append(
                    {
                        "type": "modified" if not dry_run else "would_modify",
                        "file": str(file_path.relative_to(project_root)),
                        "size_change": result["new_size"] - result["original_size"],
                    }
                )

            self.metrics.files_processed += 1

        # Update metrics
        self.metrics.findings_generated = len(findings)

        # Create result
        return self._create_result(
            status=WorkflowStatus.COMPLETED,
            findings=findings,
            artifacts={
                "modified_files": modified_files,
                "tag_refactor_stats": stats,
                "dry_run": dry_run,
            },
        )


def run_tag_refactor(
    project_root: Path,
    dry_run: bool = False,
    include_patterns: List[str] | None = None,
    exclude_patterns: List[str] | None = None,
) -> WorkflowResult:
    """Convenience function to run tag refactoring workflow.

    Args:
        project_root: Root directory to process
        dry_run: If True, report changes without modifying files
        include_patterns: Glob patterns for files to include (default: ["**/*.md"])
        exclude_patterns: Glob patterns for files to exclude

    Returns:
        WorkflowResult with findings and statistics

    Examples:
        >>> from pathlib import Path
        >>> result = run_tag_refactor(Path.cwd(), dry_run=True)
        >>> print(f"Would modify {result.artifacts['tag_refactor_stats']['modified_files']} files")

    """
    config = WorkflowConfig(
        parameters={
            "dry_run": dry_run,
            "include_patterns": include_patterns or ["**/*.md"],
            "exclude_patterns": exclude_patterns or [],
        }
    )

    workflow = TagRefactorWorkflow(config)
    return workflow.execute(project_root, {})
