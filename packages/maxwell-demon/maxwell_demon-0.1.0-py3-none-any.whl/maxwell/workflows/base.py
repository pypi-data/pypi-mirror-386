"""Base workflow system for extensible analysis tasks.

Provides framework for creating modular, composable workflows with
built-in evaluation, metrics collection, and plugin integration.

maxwell/src/maxwell/workflows/base.py
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set, Type, TypeVar

logger = logging.getLogger(__name__)

__all__ = [
    "WorkflowStatus",
    "WorkflowPriority",
    "WorkflowConfig",
    "WorkflowMetrics",
    "WorkflowResult",
    "BaseWorkflow",
    "WorkflowInputs",
    "WorkflowOutputs",
]


# Workflow Schema System
# ----------------------
# Base classes for typed workflow inputs and outputs
# Each workflow defines its own schemas in the same file


@dataclass(frozen=True)
class WorkflowInputs:
    """Base class for all workflow input schemas.

    All workflow inputs should inherit from this class.
    Using frozen=True ensures immutability.
    """

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowInputs":
        """Create schema instance from dictionary with validation.

        Args:
            data: Dictionary of input parameters

        Returns:
            Validated schema instance

        Raises:
            TypeError: If required fields are missing or wrong type
            ValueError: If validation fails

        """
        # Get all field names and types
        field_names = {f.name for f in fields(cls)}

        # Filter dict to only include valid fields
        filtered_data = {k: v for k, v in data.items() if k in field_names}

        # Create instance (will raise TypeError if required fields missing)
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class WorkflowOutputs:
    """Base class for all workflow output schemas.

    All workflow outputs should inherit from this class.
    Using frozen=True ensures immutability.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        return asdict(self)


# Type variables for generic workflow schemas
InputSchemaT = TypeVar("InputSchemaT", bound=WorkflowInputs)
OutputSchemaT = TypeVar("OutputSchemaT", bound=WorkflowOutputs)


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowPriority(Enum):
    """Workflow execution priority."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""

    # Execution context (shared across all components)
    session_id: Optional[str] = None  # Set by CLI for consistent logging
    project_root: Optional[Path] = None  # Set by CLI for context

    # Basic settings
    enabled: bool = True
    priority: WorkflowPriority = WorkflowPriority.MEDIUM
    timeout_seconds: Optional[int] = None

    # Dependencies and requirements
    required_tools: Set[str] = field(default_factory=set)
    required_data: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)  # Other workflow IDs

    # Execution settings
    parallel_execution: bool = False
    max_retries: int = 0
    cache_results: bool = True

    # Input/output settings
    input_filters: Dict[str, Any] = field(default_factory=dict)
    output_format: str = "json"

    # Custom parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    def get_log_file(self) -> Optional[Path]:
        """Get JSONL log file for this session."""
        if self.session_id and self.project_root:
            return self.project_root / ".maxwell" / "logs" / f"{self.session_id}.jsonl"
        return None


@dataclass
class WorkflowMetrics:
    """Metrics collected during workflow execution."""

    # Timing metrics
    start_time: float
    end_time: Optional[float] = None
    execution_time_seconds: Optional[float] = None

    # Resource metrics
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

    # Analysis metrics
    files_processed: int = 0
    findings_generated: int = 0
    errors_encountered: int = 0

    # Quality metrics
    confidence_score: float = 0.0
    accuracy_score: Optional[float] = None
    coverage_percentage: Optional[float] = None

    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def finalize(self):
        """Finalize metrics calculation."""
        if self.end_time and self.start_time:
            self.execution_time_seconds = self.end_time - self.start_time


@dataclass
class WorkflowResult:
    """Result of workflow execution."""

    # Execution info
    workflow_id: str
    status: WorkflowStatus
    metrics: WorkflowMetrics

    # Results
    findings: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Metadata
    timestamp: str = ""
    version: str = "1.0"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")


class BaseWorkflow(ABC):
    """Abstract base class for maxwell workflows.

    Workflows can use typed schemas for type-safe inputs/outputs:

    Example:
        @dataclass(frozen=True)
        class MyInputs(WorkflowInputs):
            query: str
            limit: int = 10

        @dataclass(frozen=True)
        class MyOutputs(WorkflowOutputs):
            results: List[str]
            count: int

        class MyWorkflow(BaseWorkflow):
            InputSchema = MyInputs
            OutputSchema = MyOutputs

            def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
                # Automatic schema conversion
                inputs = self.InputSchema.from_dict(context)
                # Now you have typed access: inputs.query, inputs.limit

                # Do work...
                results = ["result1", "result2"]

                # Return with typed outputs
                outputs = MyOutputs(results=results, count=len(results))
                return self.create_result(outputs)

    """

    # Workflow identification
    workflow_id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0"

    # Workflow categorization
    category: str = "analysis"  # analysis, validation, reporting, maintenance
    tags: Set[str] = set()

    # Typed schema support (optional - workflows can define these)
    InputSchema: ClassVar[Optional[Type[WorkflowInputs]]] = None
    OutputSchema: ClassVar[Optional[Type[WorkflowOutputs]]] = None

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize workflow with configuration."""
        self.config = config or WorkflowConfig()
        self.metrics = WorkflowMetrics(start_time=time.time())
        self._status = WorkflowStatus.PENDING

        # Validate workflow setup
        self._validate_configuration()

    @abstractmethod
    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute the workflow with given context.

        Args:
            project_root: Root directory of the project
            context: Execution context with shared data

        Returns:
            WorkflowResult with findings and artifacts

        """
        pass

    def execute_with_config(
        self, project_root: Path, context: Dict[str, Any], config: WorkflowConfig
    ) -> WorkflowResult:
        """Execute workflow with configuration (including session).

        This is the preferred entry point as it ensures consistent session
        ID logging across all workflow components.

        Args:
            project_root: Root directory of the project
            context: Execution context with shared data
            config: Workflow configuration with session_id

        Returns:
            WorkflowResult with findings and artifacts

        """
        # Ensure config is set on workflow
        self.config = config

        # Add session ID to context for components that need it
        if config.session_id:
            context["session_id"] = config.session_id

        # Add config to context for LLM pool
        context["workflow_config"] = config

        return self.execute(project_root, context)

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Get CLI parameter definitions for this workflow.

        Returns list of parameter definitions, each with:
        - name: Parameter name (str)
        - type: click type (str, int, Path, etc.)
        - required: Whether required (bool)
        - help: Help text (str)
        - default: Default value (optional)

        Example:
            return [
                {"name": "source", "type": str, "required": True, "help": "Source type"},
                {"name": "user", "type": str, "required": True, "help": "Username"},
                {"name": "machine", "type": str, "required": False, "help": "Machine name"},
            ]

        """
        return []  # Default: no additional parameters

    # Schema-based workflow helpers
    # -----------------------------

    def uses_schemas(self) -> bool:
        """Check if this workflow uses typed schemas."""
        return self.InputSchema is not None and self.OutputSchema is not None

    def parse_inputs(self, context: Dict[str, Any]) -> InputSchemaT:  # type: ignore[type-var]
        """Parse context dict into typed inputs schema.

        Args:
            context: Raw input dictionary

        Returns:
            Validated input schema instance

        Raises:
            ValueError: If InputSchema not defined or validation fails

        """
        if self.InputSchema is None:
            raise ValueError(f"Workflow {self.workflow_id} does not define InputSchema")

        return self.InputSchema.from_dict(context)  # type: ignore[return-value]

    def create_result(
        self,
        outputs: Optional[WorkflowOutputs] = None,
        status: WorkflowStatus = WorkflowStatus.COMPLETED,
        error_message: Optional[str] = None,
    ) -> WorkflowResult:
        """Create WorkflowResult from typed outputs.

        Args:
            outputs: Typed output schema (if None, creates minimal result)
            status: Workflow execution status
            error_message: Error message if failed

        Returns:
            WorkflowResult with typed outputs converted to artifacts

        """
        self.metrics.finalize()

        # Convert outputs to artifacts dict
        artifacts = outputs.to_dict() if outputs is not None else {}

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=status,
            metrics=self.metrics,
            artifacts=artifacts,
            error_message=error_message,
        )

    def can_execute(self, context: Dict[str, Any]) -> bool:
        """Check if workflow can execute with given context."""
        # Check if enabled
        if not self.config.enabled:
            return False

        # Note: Input validation now happens in parse_inputs() via InputSchema dataclass
        # Required fields without defaults will raise an error during instantiation

        # Check required tools
        if self.config.required_tools:
            # This would check for tool availability
            pass

        return True

    def estimate_execution_time(self, context: Dict[str, Any]) -> float:
        """Estimate execution time in seconds based on context."""
        # Default implementation - workflows can override
        base_time = 10.0  # 10 seconds base

        # Scale by number of files if available
        if "file_count" in context:
            file_count = context["file_count"]
            base_time += file_count * 0.1  # 0.1 seconds per file

        return base_time

    def get_dependencies(self) -> List[str]:
        """Get list of workflow IDs this workflow depends on."""
        return self.config.dependencies

    def get_priority(self) -> WorkflowPriority:
        """Get workflow execution priority."""
        return self.config.priority

    def supports_parallel_execution(self) -> bool:
        """Check if workflow supports parallel execution."""
        return self.config.parallel_execution

    def _validate_configuration(self):
        """Validate workflow configuration."""
        if not self.workflow_id:
            raise ValueError(f"Workflow {self.__class__.__name__} must define workflow_id")

        if not self.name:
            raise ValueError(f"Workflow {self.workflow_id} must define name")

    def _update_status(self, status: WorkflowStatus):
        """Update workflow execution status."""
        self._status = status

        if status == WorkflowStatus.COMPLETED:
            self.metrics.end_time = time.time()
            self.metrics.finalize()

    def _create_result(
        self,
        status: WorkflowStatus,
        findings: Optional[List[Dict[str, Any]]] = None,
        artifacts: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> WorkflowResult:
        """Create workflow result."""
        self._update_status(status)

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=status,
            metrics=self.metrics,
            findings=findings or [],
            artifacts=artifacts or {},
            error_message=error_message,
        )

    async def _execute_with_error_handling(
        self, project_root: Path, context: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute workflow with comprehensive error handling."""
        try:
            self._update_status(WorkflowStatus.RUNNING)

            # Check timeout
            if self.config.timeout_seconds:
                # Implementation would use asyncio.wait_for
                pass

            # Execute the workflow
            result = self.execute(project_root, context)

            # Validate result
            if result.status == WorkflowStatus.PENDING:
                result.status = WorkflowStatus.COMPLETED

            return result

        except Exception as e:
            logger.error(f"Workflow {self.workflow_id} failed: {e}", exc_info=True)
            self.metrics.errors_encountered += 1

            return self._create_result(WorkflowStatus.FAILED, error_message=str(e))

    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """Get criteria for evaluating workflow effectiveness."""
        return {
            "performance": {
                "max_execution_time": 60.0,  # seconds
                "max_memory_usage": 500.0,  # MB
            },
            "quality": {
                "min_confidence_score": 0.7,
                "min_coverage_percentage": 80.0,
            },
            "reliability": {
                "max_error_rate": 0.05,  # 5%
                "max_timeout_rate": 0.01,  # 1%
            },
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.workflow_id}, status={self._status.value})"
