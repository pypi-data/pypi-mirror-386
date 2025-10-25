"""Validation workflow - runs validators and reports findings.

Wraps the existing validation_engine into a proper workflow that integrates
with the Maxwell workflow system.
"""

__all__ = [
    "ValidateWorkflow",
    "CLIParameter",
    "FindingModel",
    "ValidationSummary",
    "ValidateInputs",
    "ValidateOutputs",
]

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from maxwell.config import load_config
from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowResult,
    WorkflowStatus,
)
from maxwell.workflows.validate.validation_engine import run_plugin_validation
from maxwell.workflows.validate.validators import Finding

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CLIParameter:
    """CLI parameter definition."""

    name: str
    type: type
    required: bool
    help: str
    default: Any = None


@dataclass(frozen=True)
class FindingModel:
    """Model for a validation finding."""

    rule_id: str
    message: str
    file_path: str
    severity: str
    line: int = 0
    column: int = 0
    context: str = ""
    suggestion: Optional[str] = None

    @classmethod
    def from_finding(cls, finding: Finding) -> "FindingModel":
        """Convert from validators.Finding to dataclass."""
        return cls(
            rule_id=finding.rule_id,
            message=finding.message,
            file_path=str(finding.file_path),
            line=finding.line,
            column=finding.column,
            severity=finding.severity.value,
            context=finding.context,
            suggestion=finding.suggestion,
        )


@dataclass(frozen=True)
class ValidationSummary:
    """Summary of validation results by severity."""

    info: int = 0
    warn: int = 0
    block: int = 0
    total: int = 0


@dataclass(frozen=True)
class ValidateInputs(WorkflowInputs):
    """Validate workflow inputs."""

    paths: Optional[str] = None
    format: str = "human"
    fix: bool = False


@dataclass(frozen=True)
class ValidateOutputs(WorkflowOutputs):
    """Validate workflow outputs."""

    findings: List[FindingModel] = field(default_factory=list)
    summary: ValidationSummary = field(default_factory=ValidationSummary)
    has_blocking_issues: bool = False
    formatted_output: str = ""
    fixes_applied: Optional[Dict[str, int]] = None


@register_workflow
class ValidateWorkflow(BaseWorkflow):
    """Validation workflow for running code quality checks."""

    workflow_id: str = "validate"
    name: str = "Code Validation"
    description: str = "Run validators to check code quality, consistency, and style"
    version: str = "1.0"
    category: str = "quality"
    tags: set = {"validation", "linting", "quality", "code-review"}

    InputSchema = ValidateInputs
    OutputSchema = ValidateOutputs

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Define CLI parameters for validation."""
        from dataclasses import asdict

        params = [
            CLIParameter(
                name="paths",
                type=str,
                required=False,
                help="Specific file paths to validate (comma-separated). If not provided, uses include_globs from config.",
            ),
            CLIParameter(
                name="format",
                type=str,
                required=False,
                default="human",
                help="Output format: human, json, sarif, github",
            ),
            CLIParameter(
                name="fix",
                type=bool,
                required=False,
                default=False,
                help="Automatically fix issues where validators support auto-fixing (like emoji removal)",
            ),
        ]
        return [asdict(p) for p in params]

    def _apply_autofixes(self, runner, project_root: Path) -> Dict[str, int]:
        """Apply auto-fixes to files with fixable findings.

        Args:
            runner: PluginValidationRunner with findings
            project_root: Project root directory

        Returns:
            Dictionary mapping file paths to number of fixes applied

        """
        from collections import defaultdict

        from maxwell.workflows.validate.validators.types import get_validator

        fixes_applied = defaultdict(int)

        # Group findings by file
        findings_by_file = defaultdict(list)
        for finding in runner.findings:
            findings_by_file[str(finding.file_path)].append(finding)

        # Process each file
        for file_path_str, findings in findings_by_file.items():
            file_path = Path(file_path_str)

            # Check if file exists and is writable
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"Skipping fixes for {file_path}: file not found")
                continue

            # Get fixable findings for this file
            fixable_findings = []
            for finding in findings:
                validator_class = get_validator(finding.rule_id)
                if validator_class:
                    validator = validator_class()  # Instantiate the validator
                    if hasattr(validator, "can_fix") and validator.can_fix(finding):  # type: ignore
                        fixable_findings.append((finding, validator))

            if not fixable_findings:
                continue

            # Sort by line number (descending) to avoid offset issues
            fixable_findings.sort(key=lambda x: x[0].line, reverse=True)

            # Read file content
            try:
                content = file_path.read_text()
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                continue

            # Apply fixes
            for finding, validator in fixable_findings:
                try:
                    content = validator.apply_fix(content, finding)
                    fixes_applied[file_path_str] += 1
                    logger.info(f"Applied fix for {finding.rule_id} at {file_path}:{finding.line}")
                except Exception as e:
                    logger.error(
                        f"Failed to apply fix for {finding.rule_id} at {file_path}:{finding.line}: {e}"
                    )

            # Write fixed content back
            if fixes_applied[file_path_str] > 0:
                try:
                    file_path.write_text(content)
                    logger.info(f"Wrote {fixes_applied[file_path_str]} fixes to {file_path}")
                except Exception as e:
                    logger.error(f"Failed to write fixes to {file_path}: {e}")
                    fixes_applied[file_path_str] = 0

        return dict(fixes_applied)

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute validation workflow."""
        try:
            # Parse inputs
            inputs: ValidateInputs = self.parse_inputs(context)

            # Load config
            config = load_config(project_root)

            # Get optional path override
            include_globs_override = None
            if inputs.paths:
                path_list = [Path(p.strip()) for p in inputs.paths.split(",")]
                include_globs_override = path_list

            # Run validation
            logger.info("Running validation...")
            runner = run_plugin_validation(
                config=config,
                project_root=project_root,
                include_globs_override=include_globs_override,
            )

            # Apply auto-fixes if requested
            fixes_applied = {}
            if inputs.fix:
                fixes_applied = self._apply_autofixes(runner, project_root)

            # Convert findings to dataclass models
            finding_models = [FindingModel.from_finding(f) for f in runner.findings]

            # Build summary
            raw_summary = runner.get_summary()
            summary = ValidationSummary(
                info=raw_summary["INFO"],
                warn=raw_summary["WARN"],
                block=raw_summary["BLOCK"],
                total=len(runner.findings),
            )

            # Format output
            formatted_output = runner.format_output(inputs.format)

            # Add fix summary to formatted output if fixes were applied
            if fixes_applied:
                fix_summary = f"\n\n[AUTO-FIX] Applied {sum(fixes_applied.values())} fixes across {len(fixes_applied)} files:\n"
                for file_path, count in sorted(fixes_applied.items()):
                    fix_summary += f"  - {file_path}: {count} fixes\n"
                formatted_output += fix_summary

            # Create typed outputs
            outputs = ValidateOutputs(
                findings=finding_models,
                summary=summary,
                has_blocking_issues=runner.has_blocking_issues(),
                formatted_output=formatted_output,
                fixes_applied=fixes_applied if fixes_applied else None,
            )

            # Determine status based on blocking issues
            status = (
                WorkflowStatus.FAILED if runner.has_blocking_issues() else WorkflowStatus.COMPLETED
            )

            return self.create_result(outputs=outputs, status=status)

        except Exception as e:
            logger.error(f"Validation workflow failed: {str(e)}")
            return self.create_result(
                status=WorkflowStatus.FAILED, error_message=f"Validation workflow failed: {str(e)}"
            )
