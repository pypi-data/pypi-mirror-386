"""Public API for executing Maxwell workflows programmatically.

Provides clean library interface for workflow execution without subprocess overhead.
"""

import json
import logging
from dataclasses import MISSING, asdict, dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from maxwell.registry import workflow_registry
from maxwell.workflows.base import BaseWorkflow, WorkflowResult, WorkflowStatus

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

__all__ = [
    "WorkflowMetadata",
    "list_workflows",
    "get_workflow_info",
    "execute_workflow",
    "workflow_result_to_dict",
]


@dataclass
class WorkflowMetadata:
    """Metadata about an available workflow."""

    workflow_id: str
    name: str
    description: str
    version: str
    category: str
    tags: List[str]
    parameters: List[Dict[str, Any]]
    required_inputs: List[str]
    produced_outputs: List[str]

    @classmethod
    def from_workflow_class(cls, workflow_class: type[BaseWorkflow]) -> "WorkflowMetadata":
        """Initialize from workflow class."""
        # Create temporary instance to get metadata
        instance = workflow_class()

        return cls(
            workflow_id=instance.workflow_id,
            name=instance.name,
            description=instance.description,
            version=instance.version,
            category=instance.category,
            tags=list(instance.tags) if instance.tags else [],
            parameters=(
                instance.get_cli_parameters() if hasattr(instance, "get_cli_parameters") else []
            ),
            required_inputs=(
                [
                    f.name
                    for f in fields(instance.InputSchema)
                    if f.default is MISSING and f.default_factory is MISSING
                ]
                if instance.InputSchema
                else []
            ),
            produced_outputs=(
                [f.name for f in fields(instance.OutputSchema)] if instance.OutputSchema else []
            ),
        )


def list_workflows() -> List[WorkflowMetadata]:
    """List all available workflows with their metadata.

    Returns:
        List of WorkflowMetadata objects for all registered workflows

    """
    workflows = []
    for workflow_id, workflow_class in workflow_registry.get_all_workflows().items():
        try:
            metadata = WorkflowMetadata.from_workflow_class(workflow_class)
            workflows.append(metadata)
        except Exception as e:
            logger.warning(f"Failed to get metadata for workflow {workflow_id}: {e}")

    return workflows


def get_workflow_info(workflow_id: str) -> Optional[WorkflowMetadata]:
    """Get detailed information about a specific workflow.

    Args:
        workflow_id: ID of the workflow

    Returns:
        WorkflowMetadata if found, None otherwise

    """
    workflow_class = workflow_registry.get_workflow(workflow_id)
    if not workflow_class:
        return None

    try:
        return WorkflowMetadata.from_workflow_class(workflow_class)
    except Exception as e:
        logger.error(f"Failed to get metadata for workflow {workflow_id}: {e}")
        return None


def execute_workflow(
    workflow_id: str,
    project_root: Optional[Path] = None,
    context: Optional[Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any]]]] = None,
) -> WorkflowResult:
    """Execute a workflow by ID.

    Args:
        workflow_id: ID of the workflow to execute
        project_root: Project root directory (defaults to cwd)
        context: Execution context/parameters

    Returns:
        WorkflowResult with execution results

    Raises:
        ValueError: If workflow not found

    """
    # Get workflow class
    workflow_class = workflow_registry.get_workflow(workflow_id)
    if not workflow_class:
        available = workflow_registry.list_workflow_ids()
        raise ValueError(
            f"Workflow '{workflow_id}' not found. " f"Available workflows: {', '.join(available)}"
        )

    # Set defaults
    if project_root is None:
        project_root = Path.cwd()
    if context is None:
        context = {}

    # Execute workflow
    try:
        logger.info(f"Executing workflow: {workflow_id}")
        workflow = workflow_class()
        result = workflow.execute(project_root, context)
        logger.info(f"Workflow {workflow_id} completed with status: {result.status.value}")
        return result

    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
        from maxwell.workflows.base import WorkflowMetrics

        # Return failed result
        metrics = WorkflowMetrics(start_time=0.0, end_time=0.0, errors_encountered=1)
        metrics.finalize()

        return WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED,
            metrics=metrics,
            error_message=str(e),
        )


def workflow_result_to_dict(
    result: WorkflowResult,
) -> Dict[str, Union[str, int, float, bool, List[Any], Dict[str, Any]]]:
    """Convert WorkflowResult to JSON-serializable dictionary.

    Args:
        result: WorkflowResult to convert

    Returns:
        Dictionary representation

    """
    data = asdict(result)

    # Convert enums to strings
    if "status" in data:
        data["status"] = result.status.value

    # Convert any remaining non-serializable objects
    return json.loads(json.dumps(data, default=str))
