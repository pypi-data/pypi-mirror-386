"""Codebase snapshot generation workflow.

Creates a single markdown file containing the filesystem tree and file contents.
"""

__all__ = ["SnapshotWorkflow", "SnapshotInputs", "SnapshotOutputs"]

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from maxwell.discovery import discover_files
from maxwell.filesystem import get_relative_path, is_binary
from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

FILES_KEY = "__FILES__"


@dataclass(frozen=True)
class CLIParameter:
    """CLI parameter definition."""

    name: str
    type: type
    required: bool
    help: str
    default: Any = None


@dataclass(frozen=True)
class SnapshotInputs(WorkflowInputs):
    """Input schema for snapshot workflow."""

    output: str = "SNAPSHOT.md"  # Output markdown file path
    target: Optional[str] = None  # Optional target directory (default: project root)
    stdout: bool = False  # Output to stdout instead of file


@dataclass(frozen=True)
class SnapshotOutputs(WorkflowOutputs):
    """Output schema for snapshot workflow."""

    snapshot_path: str
    files_included: int
    binary_files: int


@register_workflow
class SnapshotWorkflow(BaseWorkflow):
    """Generate a markdown snapshot of the codebase."""

    workflow_id: str = "snapshot"
    name: str = "Codebase Snapshot"
    description: str = "Generate a markdown file with filesystem tree and file contents"
    version: str = "2.0"
    category: str = "documentation"
    tags: set = {"snapshot", "documentation", "markdown"}

    InputSchema = SnapshotInputs
    OutputSchema = SnapshotOutputs

    def __init__(self):
        self.workflow_id = "snapshot"
        self.name = "Codebase Snapshot"
        self.description = "Generate a markdown file with filesystem tree and file contents"
        self.version = "2.0"
        super().__init__()

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        from dataclasses import asdict

        params = [
            CLIParameter(
                name="output",
                type=str,
                required=False,
                default="SNAPSHOT.md",
                help="Output markdown file path",
            ),
            CLIParameter(
                name="target",
                type=str,
                required=False,
                default=None,
                help="Target directory to snapshot (default: project root)",
            ),
            CLIParameter(
                name="stdout",
                type=bool,
                required=False,
                default=False,
                help="Output to stdout instead of file",
            ),
        ]
        return [asdict(p) for p in params]

    def get_required_inputs(self) -> List[str]:
        return []

    def get_produced_outputs(self) -> List[str]:
        return ["snapshot_path"]

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=300,
            parameters={"root_dir": str(root_dir)},
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute snapshot generation."""
        try:
            inputs: SnapshotInputs = self.parse_inputs(context)  # type: ignore[assignment]

            # Load Maxwell config
            from maxwell.config import load_hierarchical_config

            config = load_hierarchical_config(project_root)

            # Determine output path
            output_path = Path(inputs.output)
            if not output_path.is_absolute():
                output_path = project_root / output_path
            absolute_output_path = output_path.resolve()

            # Determine target paths
            if inputs.target:
                target_path = Path(inputs.target)
                if not target_path.is_absolute():
                    target_path = project_root / target_path
                target_paths = [target_path]
            else:
                target_paths = [project_root]

            logger.info(f"Creating snapshot: output={output_path}, target={target_paths}")

            # Discover files
            discovered_files = discover_files(
                paths=target_paths,
                config=config,
                explicit_exclude_paths={absolute_output_path},
            )

            logger.info(f"Discovered {len(discovered_files)} files")

            # Categorize files (FULL or BINARY)
            file_infos: List[tuple[Path, str]] = []

            for abs_file_path in discovered_files:
                try:
                    rel_path_obj = get_relative_path(abs_file_path, project_root)
                except ValueError:
                    logger.warning(f"Skipping file outside project root: {abs_file_path}")
                    continue

                if is_binary(abs_file_path):
                    cat = "BINARY"
                else:
                    cat = "FULL"
                file_infos.append((abs_file_path, cat))

            file_infos.sort(key=lambda x: x[0])

            # Count categories
            binary_count = sum(1 for _, cat in file_infos if cat == "BINARY")

            # Build tree structure
            tree: dict = {}
            for f_path, f_cat in file_infos:
                try:
                    relative_path_obj = get_relative_path(f_path, project_root)
                    relative_parts = relative_path_obj.parts
                except ValueError:
                    continue

                node = tree
                for i, part in enumerate(relative_parts):
                    if not part:
                        continue

                    is_last_part = i == len(relative_parts) - 1

                    if is_last_part:
                        if FILES_KEY not in node:
                            node[FILES_KEY] = []
                        node[FILES_KEY].append((f_path, f_cat))
                    else:
                        if part not in node:
                            node[part] = {}
                        node = node[part]

            # Write snapshot markdown file or to stdout
            import sys

            if inputs.stdout:
                logger.info("Writing snapshot to stdout")
                outfile = sys.stdout
            else:
                logger.info(f"Writing snapshot to {output_path}")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                outfile = open(absolute_output_path, "w", encoding="utf-8")

            try:
                outfile.write("# Snapshot\n\n")

                # Write Filesystem Tree
                outfile.write("## Filesystem Tree\n\n```\n")
                tree_root_name = project_root.name if project_root.name else str(project_root)
                outfile.write(f"{tree_root_name}/\n")
                self._write_tree(outfile, tree, "")
                outfile.write("```\n\n")

                # Write File Contents
                outfile.write("## File Contents\n\n")
                outfile.write("Files are ordered alphabetically by path.\n\n")

                for f, cat in file_infos:
                    try:
                        relpath_header = get_relative_path(f, project_root)
                        outfile.write(f"### File: {relpath_header}\n\n")

                        if cat == "BINARY":
                            outfile.write(
                                "```\n[Binary File - Content not displayed]\n```\n\n---\n"
                            )
                        else:  # FULL
                            lang = self._get_language(f)
                            outfile.write(f"```{lang}\n")
                            try:
                                with open(f, encoding="utf-8", errors="ignore") as infile:
                                    content = infile.read()
                                    if not content.endswith("\n"):
                                        content += "\n"
                                    outfile.write(content)
                            except (OSError, UnicodeDecodeError) as e:
                                outfile.write(f"[Error reading file: {e}]\n")
                            outfile.write("```\n\n---\n")

                    except (OSError, ValueError, TypeError) as e:
                        logger.error(f"Error processing file {f}: {e}")
                        outfile.write(f"### File: {f} (Error)\n\n[Error: {e}]\n\n---\n")

                outfile.write("\n")
            finally:
                # Close file only if we opened it (not stdout)
                if not inputs.stdout:
                    outfile.close()

            outputs = SnapshotOutputs(
                snapshot_path=str(output_path),
                files_included=len(file_infos),
                binary_files=binary_count,
            )

            logger.info(f"Snapshot created: {len(file_infos)} files ({binary_count} binary)")

            return self.create_result(outputs)

        except Exception as e:
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message=f"Snapshot failed: {str(e)}",
            )

    def _write_tree(self, outfile, node: dict, prefix=""):
        """Recursively write directory tree structure."""
        dirs = sorted([k for k in node if k != FILES_KEY])
        files_data: List[tuple[Path, str]] = sorted(
            node.get(FILES_KEY, []), key=lambda x: x[0].name
        )

        entries = dirs + [f_info[0].name for f_info in files_data]

        for i, name in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            outfile.write(f"{prefix}{connector}")

            if name in dirs:
                outfile.write(f"{name}/\n")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._write_tree(outfile, node[name], new_prefix)
            else:
                file_info_tuple = next((info for info in files_data if info[0].name == name), None)
                file_cat = "FULL"
                if file_info_tuple:
                    file_cat = file_info_tuple[1]

                binary_indicator = " (BINARY)" if file_cat == "BINARY" else ""
                outfile.write(f"{name}{binary_indicator}\n")

    def _get_language(self, file_path: Path) -> str:
        """Guess language for syntax highlighting based on extension."""
        ext = file_path.suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".less": "less",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
            ".ps1": "powershell",
            ".bat": "batch",
            ".sql": "sql",
            ".dockerfile": "dockerfile",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".gitignore": "gitignore",
            ".env": "bash",
            ".tf": "terraform",
            ".hcl": "terraform",
            ".lua": "lua",
            ".perl": "perl",
            ".pl": "perl",
            ".r": "r",
            ".ex": "elixir",
            ".exs": "elixir",
            ".dart": "dart",
            ".groovy": "groovy",
            ".gradle": "groovy",
            ".vb": "vbnet",
            ".fs": "fsharp",
            ".fsi": "fsharp",
            ".fsx": "fsharp",
            ".fsscript": "fsharp",
        }
        return mapping.get(ext, "")
