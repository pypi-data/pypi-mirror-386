"""Utility workflows for common Maxwell operations.

Simple utility workflows for timestamps, session IDs, and file operations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from maxwell.registry import register_workflow
from maxwell.utils import get_session_id, get_timestamp
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

# Workflow Schemas
# ----------------


@dataclass(frozen=True)
class GetTimeInputs(WorkflowInputs):
    """Input schema for timestamp workflow."""

    format: str = "iso"  # iso, iso_seconds, date, filename, unix


@dataclass(frozen=True)
class GetTimeOutputs(WorkflowOutputs):
    """Output schema for timestamp workflow."""

    timestamp: str
    format: str


@dataclass(frozen=True)
class GetSessionInputs(WorkflowInputs):
    """Input schema for session ID workflow."""

    path: Optional[str] = None


@dataclass(frozen=True)
class GetSessionOutputs(WorkflowOutputs):
    """Output schema for session ID workflow."""

    session_id: str


@dataclass(frozen=True)
class FindChatFilesInputs(WorkflowInputs):
    """Input schema for find chat files workflow."""

    directory: str = "."
    recursive: bool = True


@dataclass(frozen=True)
class FindChatFilesOutputs(WorkflowOutputs):
    """Output schema for find chat files workflow."""

    chat_files: List[str]
    count: int
    search_directory: str


@register_workflow
class GetTimeWorkflow(BaseWorkflow):
    """Get current timestamp in various formats."""

    workflow_id: str = "get-time"
    name: str = "Get Timestamp"
    description: str = "Get current timestamp in various formats (iso, date, filename, unix)"
    version: str = "1.0"
    category: str = "utility"
    tags: set = {"timestamp", "time", "utility"}

    # Typed schemas
    InputSchema = GetTimeInputs
    OutputSchema = GetTimeOutputs

    def __init__(self):
        self.workflow_id = "get-time"
        self.name = "Get Timestamp"
        self.description = "Get current timestamp in various formats (iso, date, filename, unix)"
        self.version = "1.0"
        super().__init__()

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "format",
                "type": str,
                "required": False,
                "default": "iso",
                "help": "Timestamp format: iso, iso_seconds, date, filename, unix",
            }
        ]

    def get_required_inputs(self) -> List[str]:
        return []

    def get_produced_outputs(self) -> List[str]:
        return ["timestamp"]

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.LOW,
            timeout_seconds=30,  # 30 seconds
            parameters={
                "root_dir": str(root_dir),
            },
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute timestamp generation with typed schemas."""
        try:
            inputs: GetTimeInputs = self.parse_inputs(context)  # type: ignore[assignment]
            timestamp = get_timestamp(inputs.format)

            outputs = GetTimeOutputs(timestamp=timestamp, format=inputs.format)
            return self.create_result(outputs)

        except Exception as e:
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message=f"Failed to get timestamp: {str(e)}",
            )


@register_workflow
class GetSessionWorkflow(BaseWorkflow):
    """Get current session ID (absolute path)."""

    workflow_id: str = "get-session"
    name: str = "Get Session ID"
    description: str = "Get current session ID (absolute path of current directory)"
    version: str = "1.0"
    category: str = "utility"
    tags: set = {"session", "path", "utility"}

    # Typed schemas
    InputSchema = GetSessionInputs
    OutputSchema = GetSessionOutputs

    def __init__(self):
        self.workflow_id = "get-session"
        self.name = "Get Session ID"
        self.description = "Get current session ID (absolute path of current directory)"
        self.version = "1.0"
        super().__init__()

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "path",
                "type": str,
                "required": False,
                "help": "Path to get session ID for (default: current directory)",
            }
        ]

    def get_required_inputs(self) -> List[str]:
        return []

    def get_produced_outputs(self) -> List[str]:
        return ["session_id"]

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.LOW,
            timeout_seconds=30,  # 30 seconds
            parameters={
                "root_dir": str(root_dir),
            },
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute session ID generation with typed schemas."""
        try:
            inputs: GetSessionInputs = self.parse_inputs(context)  # type: ignore[assignment]
            session_id = get_session_id(inputs.path)

            outputs = GetSessionOutputs(session_id=session_id)
            return self.create_result(outputs)

        except Exception as e:
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message=f"Failed to get session ID: {str(e)}",
            )


class FindChatFilesWorkflow(BaseWorkflow):
    """Find Claude chat log files in a directory."""

    workflow_id: str = "find-chatfiles"
    name: str = "Find Chat Files"
    description: str = "Find Claude chat log files (.jsonl) in directory tree"
    version: str = "1.0"
    category: str = "utility"
    tags: set = {"chat", "files", "claude", "jsonl"}

    # Typed schemas
    InputSchema = FindChatFilesInputs
    OutputSchema = FindChatFilesOutputs

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "directory",
                "type": str,
                "required": False,
                "help": "Directory to search (default: current directory)",
            },
            {
                "name": "recursive",
                "type": bool,
                "required": False,
                "default": True,
                "help": "Search recursively in subdirectories",
            },
        ]

    def get_required_inputs(self) -> List[str]:
        return []

    def get_produced_outputs(self) -> List[str]:
        return ["chat_files"]

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute chat file search with typed schemas."""
        try:
            inputs: FindChatFilesInputs = self.parse_inputs(context)  # type: ignore[assignment]

            search_path = Path(inputs.directory)
            if not search_path.is_absolute():
                search_path = project_root / search_path

            if inputs.recursive:
                chat_files = list(search_path.rglob("*.jsonl"))
            else:
                chat_files = list(search_path.glob("*.jsonl"))

            # Filter for Claude-style chat files (those that look like they're from .claude/projects/)
            claude_chat_files = []
            for file_path in chat_files:
                # Check if file looks like a Claude chat file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("{") and "role" in first_line.lower():
                            claude_chat_files.append(str(file_path))
                except Exception:
                    pass  # Skip files that can't be read

            # Update metrics
            self.metrics.files_processed = len(claude_chat_files)

            outputs = FindChatFilesOutputs(
                chat_files=claude_chat_files,
                count=len(claude_chat_files),
                search_directory=str(search_path),
            )
            return self.create_result(outputs)

        except Exception as e:
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message=f"Failed to find chat files: {str(e)}",
            )
