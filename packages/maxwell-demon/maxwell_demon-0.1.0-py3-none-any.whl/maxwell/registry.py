"""Workflow registry for managing available workflows.

Simple registration system for BaseWorkflow subclasses.
Workflows must properly inherit from BaseWorkflow and implement required methods.

Supports plugin loading from:
- ~/.maxwell/plugins/ (global plugins)
- <project>/.maxwell/plugins/ (project-specific plugins)

Plugin Types:
- Python plugins: .py files with BaseWorkflow subclasses
- Script plugins: Executable scripts with .json metadata files

maxwell/src/maxwell/registry.py
"""

import importlib.util
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

__all__ = ["WorkflowRegistry", "register_workflow"]


@dataclass(frozen=True)
class ScriptWorkflowInputs(WorkflowInputs):
    """Generic inputs for script-based workflows."""

    pass


@dataclass(frozen=True)
class ScriptWorkflowOutputs(WorkflowOutputs):
    """Generic outputs for script-based workflows."""

    stdout: str
    stderr: str
    exit_code: int


class ScriptWorkflow(BaseWorkflow):
    """Adapter for executing external scripts as workflows."""

    InputSchema = ScriptWorkflowInputs
    OutputSchema = ScriptWorkflowOutputs

    def __init__(self, script_path: Path, metadata: Dict[str, Any]):
        """Initialize script workflow from metadata.

        Args:
            script_path: Path to executable script
            metadata: Workflow metadata (workflow_id, name, description, etc.)

        """
        self.script_path = script_path
        self.workflow_id = metadata["workflow_id"]
        self.name = metadata.get("name", self.workflow_id)
        self.description = metadata.get("description", "External script workflow")
        self.version = metadata.get("version", "1.0")
        self.category = metadata.get("category", "external")
        self.tags = set(metadata.get("tags", ["external", "script"]))
        self._parameters = metadata.get("parameters", [])
        super().__init__()

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Return CLI parameters from metadata."""
        return self._parameters

    def get_required_inputs(self) -> List[str]:
        """Return required inputs from parameters."""
        return [p["name"] for p in self._parameters if p.get("required", False)]

    def get_produced_outputs(self) -> List[str]:
        """Script workflows always produce stdout/stderr/exit_code."""
        return ["stdout", "stderr", "exit_code"]

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Return default config for script workflows."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=300,
            parameters={"root_dir": str(root_dir)},
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute the external script."""
        try:
            # Build command with arguments
            cmd = [str(self.script_path)]

            # Add arguments from context
            for param in self._parameters:
                param_name = param["name"]
                if param_name in context:
                    value = context[param_name]
                    cmd.extend([f"--{param_name}", str(value)])

            # Execute script
            logger.info(f"Executing script workflow: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300,
            )

            outputs = ScriptWorkflowOutputs(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )

            # Determine status based on exit code
            status = WorkflowStatus.COMPLETED if result.returncode == 0 else WorkflowStatus.FAILED

            return self.create_result(
                outputs=outputs,
                status=status,
                error_message=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message="Script execution timed out",
            )
        except Exception as e:
            self.metrics.errors_encountered = 1
            return self.create_result(
                outputs=None,
                status=WorkflowStatus.FAILED,
                error_message=f"Script execution failed: {str(e)}",
            )


class WorkflowRegistry:
    """Registry for managing available workflows."""

    def __init__(self):
        self._workflows: Dict[str, Type[BaseWorkflow]] = {}
        self._loaded = False

    def register(self, workflow_class: Type[BaseWorkflow]) -> None:
        """Register a workflow class that inherits from BaseWorkflow."""
        if not issubclass(workflow_class, BaseWorkflow):
            raise TypeError(f"{workflow_class.__name__} must inherit from BaseWorkflow")

        # Create temporary instance to get workflow_id
        temp_instance = workflow_class()
        workflow_id = temp_instance.workflow_id

        if not workflow_id:
            raise ValueError(f"Workflow {workflow_class.__name__} must define workflow_id")

        if workflow_id in self._workflows:
            logger.warning(f"Overwriting existing workflow: {workflow_id}")

        self._workflows[workflow_id] = workflow_class
        logger.debug(f"Registered workflow: {workflow_id}")

    def get_workflow(self, workflow_id: str) -> Optional[Type[BaseWorkflow]]:
        """Get workflow class by ID."""
        self._ensure_loaded()
        return self._workflows.get(workflow_id)

    def get_all_workflows(self) -> Dict[str, Type[BaseWorkflow]]:
        """Get all registered workflows."""
        self._ensure_loaded()
        return self._workflows.copy()

    def list_workflow_ids(self) -> List[str]:
        """List all workflow IDs."""
        self._ensure_loaded()
        return list(self._workflows.keys())

    def unregister(self, workflow_id: str) -> bool:
        """Unregister a workflow."""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            logger.debug(f"Unregistered workflow: {workflow_id}")
            return True
        return False

    def clear(self) -> None:
        """Clear all registered workflows."""
        self._workflows.clear()
        self._loaded = False
        logger.debug("Cleared all workflows from registry")

    def load_plugins(self, plugin_dirs: Optional[List[Path]] = None) -> None:
        """Load plugins from directories.

        Args:
            plugin_dirs: List of directories to search for plugins.
                        Defaults to ~/.maxwell/plugins/ and .maxwell/plugins/

        """
        if plugin_dirs is None:
            plugin_dirs = []
            # Global plugins
            global_plugins = Path.home() / ".maxwell" / "plugins"
            if global_plugins.exists():
                plugin_dirs.append(global_plugins)

            # Project-specific plugins
            project_plugins = Path.cwd() / ".maxwell" / "plugins"
            if project_plugins.exists():
                plugin_dirs.append(project_plugins)

        for plugin_dir in plugin_dirs:
            if not plugin_dir.exists():
                continue

            logger.debug(f"Loading plugins from {plugin_dir}")

            # Load Python plugins (.py files)
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue  # Skip private modules
                self._load_python_plugin(py_file)

            # Load script plugins (executable + .json metadata)
            for json_file in plugin_dir.glob("*.json"):
                script_path = json_file.with_suffix("")  # Remove .json extension
                if script_path.exists() and script_path.stat().st_mode & 0o111:
                    self._load_script_plugin(script_path, json_file)

    def _load_python_plugin(self, py_file: Path) -> None:
        """Load a Python plugin module."""
        try:
            module_name = f"maxwell_plugin_{py_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, str(py_file))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Find BaseWorkflow subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseWorkflow)
                        and attr is not BaseWorkflow
                    ):
                        self.register(attr)
                        logger.info(f"Loaded Python plugin: {attr_name} from {py_file.name}")
        except Exception as e:
            logger.error(f"Failed to load Python plugin {py_file}: {e}")

    def _load_script_plugin(self, script_path: Path, metadata_path: Path) -> None:
        """Load an external script plugin with metadata."""
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)

            if "workflow_id" not in metadata:
                logger.error(f"Script plugin {script_path.name} missing 'workflow_id' in metadata")
                return

            # Create a ScriptWorkflow wrapper class
            workflow_class = type(
                f"ScriptWorkflow_{metadata['workflow_id']}",
                (ScriptWorkflow,),
                {"__init__": lambda self: ScriptWorkflow.__init__(self, script_path, metadata)},
            )

            self.register(workflow_class)
            logger.info(f"Loaded script plugin: {metadata['workflow_id']} from {script_path.name}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata for {script_path.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load script plugin {script_path}: {e}")

    def _ensure_loaded(self) -> None:
        """Ensure workflows are loaded (triggers plugin loading on first access)."""
        if not self._loaded:
            self.load_plugins()
            self._loaded = True


# Initialize single module-level registry instance
_workflow_registry = WorkflowRegistry()

# Export as workflow_registry for backward compatibility
workflow_registry = _workflow_registry


def get_workflow_registry() -> WorkflowRegistry:
    return _workflow_registry


def register_workflow(
    workflow_class: Type[BaseWorkflow],
) -> Type[BaseWorkflow]:
    """Decorator for registering workflows."""
    _workflow_registry.register(workflow_class)
    return workflow_class
