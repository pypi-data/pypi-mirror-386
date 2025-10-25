"""Maxwell CLI - Dynamic workflow registry only.

This is a minimal CLI wrapper that sets up the workflow registry
and lets all workflows register themselves dynamically.
No hardcoded functionality - everything goes through the registry.
"""

import datetime
import shutil
import sys
from importlib import resources
from pathlib import Path

from maxwell.api import list_workflows
from maxwell.registry import get_workflow_registry
from maxwell.workflows.base import WorkflowConfig


def scale_ascii_art(
    art: str,
    target_width: int | None = None,
    target_height: int | None = None,
    reserved_lines: int = 10,
) -> str:
    """Scale ASCII art to fit terminal, leaving room for text output.

    Args:
        art: ASCII art string (can be multi-line)
        target_width: Target width in columns. If None, uses 80% of terminal width
        target_height: Target height in lines. If None, uses terminal height minus reserved_lines
        reserved_lines: Number of lines to reserve for text output (default: 10)

    Returns:
        Scaled ASCII art string

    """
    lines = art.splitlines()
    if not lines:
        return art

    # Get terminal dimensions
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))

    # Find original dimensions
    original_width = max(len(line) for line in lines)
    original_height = len(lines)

    # Determine target dimensions
    if target_width is None:
        target_width = int(terminal_size.columns * 0.8)  # Use 80% of terminal width

    if target_height is None:
        target_height = max(5, terminal_size.lines - reserved_lines)  # Leave room for text

    # Calculate scale factors for width and height
    width_scale = target_width / original_width
    height_scale = target_height / original_height

    # Use the smaller scale to maintain aspect ratio and fit constraints
    scale = min(width_scale, height_scale)

    # Scale by skipping lines and characters
    scaled_lines = []
    for i, line in enumerate(lines):
        # Skip lines based on scale
        if i % max(1, int(1 / scale)) != 0:
            continue

        # Sample characters from line
        scaled_line = ""
        for j in range(len(line)):
            if j % max(1, int(1 / scale)) == 0:
                scaled_line += line[j]

        scaled_lines.append(scaled_line)

    return "\n".join(scaled_lines)


def print_demon(additional_text: str = "") -> None:
    """Print the Maxwell demon ASCII art scaled to fit terminal, with readable text below.

    Args:
        additional_text: Text to append below the ASCII art (unscaled, stays readable)

    """
    try:
        # Load DEMON.txt from package resources
        demon_art = resources.read_text("maxwell", "DEMON.txt")

        # Count lines needed for text output
        text_lines = additional_text.count("\n") + 1 if additional_text else 0

        # Scale ASCII art, reserving vertical space for text
        scaled_art = scale_ascii_art(demon_art, reserved_lines=text_lines + 2)

        # Print scaled art, then unscaled text
        print(scaled_art)
        if additional_text:
            print(additional_text)
    except Exception:
        # Silently fail if ASCII art not found
        pass


def main() -> int:
    """Main CLI entry point - workflow registry only."""
    try:
        # Get workflow registry (auto-discovers workflows)
        registry = get_workflow_registry()

        # Get available workflows
        available_workflows = registry.list_workflow_ids()

        # Handle CLI arguments
        if len(sys.argv) < 2:
            # Print demon banner with help text
            help_text = (
                "\nMaxwell - Semantic search and workflow automation\n\n"
                "Usage: maxwell <workflow-id> [options]\n"
                "       maxwell list-workflows\n"
            )
            print_demon(help_text)
            for workflow_id in available_workflows:
                workflow_class = registry.get_workflow(workflow_id)
                if workflow_class:
                    workflow = workflow_class()
            return 0

        workflow_id = sys.argv[1]

        # Handle special commands
        if workflow_id == "list-workflows":
            workflows = list_workflows()
            print("\nAvailable Maxwell workflows:\n")
            for w in workflows:
                print(f"  {w.workflow_id:<30} {w.name:<30} ({w.category})")
                if w.description:
                    print(f"    {w.description}")
            return 0

        # Check if workflow exists
        if workflow_id not in available_workflows:
            print(f"Unknown workflow: {workflow_id}")
            print("Use 'list-workflows' to see available workflows")
            return 1

        # Execute workflow with remaining arguments
        workflow_class = registry.get_workflow(workflow_id)
        if not workflow_class:
            return 1

        workflow = workflow_class()
        project_root = Path.cwd()

        # Parse workflow-specific arguments using argparse
        import argparse

        parser = argparse.ArgumentParser(
            prog=f"maxwell {workflow_id}", description=workflow.description
        )

        # Add workflow parameters
        for param in workflow.get_cli_parameters():
            name = param["name"]

            if "type" in param:
                param_type = param["type"]
            else:
                param_type = str

            if "required" in param:
                required = param["required"]
            else:
                required = False

            if "default" in param:
                default = param["default"]
            else:
                default = None

            if "help" in param:
                help_text = param["help"]
            else:
                help_text = ""

            # Handle boolean flags specially
            if param_type is bool:
                parser.add_argument(
                    f"--{name}",
                    action="store_true",
                    default=default if default is not None else False,
                    help=help_text,
                )
            elif required and default is None:
                parser.add_argument(f"--{name}", type=param_type, required=required, help=help_text)
            else:
                parser.add_argument(f"--{name}", type=param_type, default=default, help=help_text)

        # Parse arguments
        args = vars(parser.parse_args(sys.argv[2:]))

        # Create workflow config with session ID for consistent logging
        session_id = f"{workflow.workflow_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config = WorkflowConfig(
            session_id=session_id,
            project_root=project_root,
        )

        # Execute the workflow with config
        result = workflow.execute_with_config(project_root, args, config)

        # Handle result
        from maxwell.workflows.base import WorkflowStatus

        if result.status == WorkflowStatus.COMPLETED:
            if result.artifacts and "report" in result.artifacts:
                pass
            else:
                if result.artifacts:
                    pass
            return 0
        else:
            return 1

    except KeyboardInterrupt:
        return 130
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
