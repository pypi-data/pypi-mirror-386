"""Complete justification workflow - auto-fill justifications and resolutions.

Uses a large-context LLM to:
- Fill in file justifications
- Suggest resolutions for architectural issues
- Suggest fixes for quality findings
- Update status fields in JSON
"""

__all__ = ["CompleteJustificationWorkflow"]

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowPriority,
    WorkflowResult,
)

logger = logging.getLogger(__name__)


@register_workflow
class CompleteJustificationWorkflow(BaseWorkflow):
    """Auto-complete justification worksheet using large-context LLM."""

    # Workflow metadata
    workflow_id: str = "complete-justification"
    name: str = "Complete Justification Analysis"
    description: str = "Auto-fill justifications and resolutions using large-context LLM"
    version: str = "1.0"
    category: str = "analysis"
    tags: set = {"code-quality", "llm-analysis", "completion"}

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize completion workflow (LLM loading deferred until execute)."""
        self.workflow_id = "complete-justification"
        self.name = "Complete Justification Analysis"
        self.description = "Auto-fill justifications and resolutions using large-context LLM"
        self.version = "1.0"
        super().__init__(config)
        self.config = config or WorkflowConfig()

        # LLM initialization is LAZY - only happens on first execute()
        self._llm_initialized = False
        self.llm = None

    def _init_llm(self):
        """Initialize large-context LLM from pool (lazy - called on first execute)."""
        if self._llm_initialized:
            return  # Already initialized

        try:
            from maxwell.lm_pool import get_lm

            # Use 32K context (batched processing handles the rest)
            self.llm = get_lm(min_context=32000)  # 32K+ context

            logger.info(f"Large-context LLM initialized: {self.llm.spec.name}")
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
            self.llm = None

        self._llm_initialized = True

    def execute(self, project_root: Path, context: Dict) -> WorkflowResult:
        """Execute completion workflow.

        Args:
            project_root: Project root directory
            context: Execution context (can specify justification_path)

        Returns:
            WorkflowResult

        """
        from maxwell.workflows.base import WorkflowMetrics, WorkflowStatus

        start_time = time.time()

        # Lazy initialization - only happens on first execute()
        if not self._llm_initialized:
            self._init_llm()

        if not self.llm:
            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.FAILED,
                metrics=WorkflowMetrics(start_time=start_time, end_time=time.time()),
                error_message="No large-context LLM available (need 32K+ context)",
            )

        try:
            result = self.run_completion(project_root, context)

            end_time = time.time()
            metrics = WorkflowMetrics(
                start_time=start_time,
                end_time=end_time,
                custom_metrics={
                    "items_completed": result.get("items_completed", 0),
                },
            )
            metrics.finalize()

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.COMPLETED if result.get("success") else WorkflowStatus.FAILED,
                metrics=metrics,
                artifacts={
                    "completed_json": result.get("output_path", ""),
                },
                error_message=result.get("error"),
            )
        except Exception as e:
            end_time = time.time()
            metrics = WorkflowMetrics(start_time=start_time, end_time=end_time)
            metrics.finalize()

            logger.exception(f"Completion workflow failed: {e}")

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.FAILED,
                metrics=metrics,
                error_message=str(e),
            )

    def run_completion(self, project_root: Path, context: dict) -> dict:
        """Run completion workflow with batched processing.

        Args:
            project_root: Project root directory
            context: Execution context

        Returns:
            Dict with success, output_path, items_completed

        """
        start_time = time.time()
        project_root = project_root.resolve()

        # Find latest justification JSON
        justification_path = context.get("justification_path")
        if not justification_path:
            reports_dir = project_root / ".maxwell" / "reports"
            json_files = sorted(reports_dir.glob("justification_*.json"), reverse=True)
            if not json_files:
                raise ValueError("No justification JSON found - run 'maxwell justification' first")
            justification_path = json_files[0]
        else:
            justification_path = Path(justification_path)

        logger.info(f"Completing justification: {justification_path}")

        # Load JSON
        with open(justification_path) as f:
            data = json.load(f)

        # Load artifacts
        cache_dir = Path(data["metadata"]["cache_dir"])
        xml_context_path = Path(data["metadata"]["artifacts"]["xml_context"])
        ast_dir = Path(data["metadata"]["artifacts"]["ast_analyses"])

        logger.info(f"Loading artifacts from: {cache_dir}")

        # Load XML context (truncate if needed)
        xml_context = xml_context_path.read_text()
        if len(xml_context) > 30000:
            xml_context = xml_context[:30000] + "\n\n... [truncated] ..."

        # Process in batches
        logger.info("Phase 1: Completing architectural issues...")
        self._complete_architectural_issues(data, xml_context, project_root)

        logger.info("Phase 2: Completing blocking quality findings...")
        self._complete_quality_findings(data, xml_context, project_root, ast_dir)

        logger.info("Phase 3: Completing file justifications...")
        self._complete_file_justifications(data, xml_context, project_root, ast_dir)

        # Save completed JSON
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = (
            project_root / ".maxwell" / "reports" / f"justification_{timestamp}_completed.json"
        )
        output_path.write_text(json.dumps(data, indent=2))

        duration = time.time() - start_time

        # Count completed items
        items_completed = (
            sum(1 for issue in data["architectural_issues"] if issue.get("resolution"))
            + sum(1 for finding in data["quality_findings"] if finding.get("resolution"))
            + sum(1 for file in data["files"] if file.get("justification"))
        )

        logger.info(f"Completion finished in {duration:.1f}s - {items_completed} items completed")
        logger.info(f"Output: {output_path}")

        return {
            "success": True,
            "output_path": str(output_path),
            "items_completed": items_completed,
            "duration": duration,
        }

    def _complete_architectural_issues(self, data: dict, xml_context: str, project_root: Path):
        """Complete architectural issues (all at once, usually <10 items).

        Args:
            data: Justification data (modified in-place)
            xml_context: XML context of codebase
            project_root: Project root directory

        """
        issues = data["architectural_issues"]
        if not issues:
            return

        prompt = f"""# Architectural Issues Resolution

Project: {project_root}

## Codebase Summary
{xml_context}

## Issues to Resolve

{json.dumps(issues, indent=2)}

For each issue, provide a specific, actionable resolution. Output JSON array (one item per issue):
```json
[
  {{"resolution": "Move X to Y because...", "status": "reviewed"}},
  {{"resolution": "Refactor Z to use...", "status": "reviewed"}},
  ...
]
```
"""
        assert self.llm is not None, "LLM not initialized"
        response = self.llm.generate(prompt, max_tokens=2048, temperature=0.2)
        # Apply by position
        for idx, completion in enumerate(self._parse_json_response(response)):
            if idx < len(issues):
                issues[idx]["resolution"] = completion.get("resolution", "")
                issues[idx]["status"] = completion.get("status", "reviewed")

    def _complete_quality_findings(
        self, data: dict, xml_context: str, project_root: Path, ast_dir: Path
    ):
        """Complete quality findings in batches (focus on blocking first).

        Args:
            data: Justification data (modified in-place)
            xml_context: XML context
            project_root: Project root
            ast_dir: AST analyses directory

        """
        findings = data["quality_findings"]

        # Focus on blocking issues only (usually <30)
        blocking = [f for f in findings if f["severity"] == "BLOCK"]
        if not blocking or len(blocking) > 50:
            logger.info(f"Skipping {len(blocking)} blocking findings (too many or none)")
            return

        # Process in batches of 10
        batch_size = 10
        for i in range(0, len(blocking), batch_size):
            batch = blocking[i : i + batch_size]

            prompt = f"""# Quality Findings Resolution (Batch {i//batch_size + 1})

Project: {project_root}

## Findings (BLOCKING)

{json.dumps(batch, indent=2)}

For each finding, suggest a specific fix. Output JSON array (one item per finding):
```json
[
  {{"resolution": "Replace X with Y", "status": "reviewed"}},
  {{"resolution": "Add type hint", "status": "reviewed"}},
  ...
]
```
"""
            assert self.llm is not None, "LLM not initialized"
            response = self.llm.generate(prompt, max_tokens=1024, temperature=0.2)
            # Map back to original findings list (by position in batch)
            for batch_idx, item in enumerate(self._parse_json_response(response)):
                if batch_idx < len(batch):
                    # Find this batch item in the original findings list
                    orig_idx = findings.index(batch[batch_idx])
                    findings[orig_idx]["resolution"] = item.get("resolution", "")
                    findings[orig_idx]["status"] = item.get("status", "reviewed")

    def _complete_file_justifications(
        self, data: dict, xml_context: str, project_root: Path, ast_dir: Path
    ):
        """Complete file justifications in batches.

        Args:
            data: Justification data (modified in-place)
            xml_context: XML context
            project_root: Project root
            ast_dir: AST analyses directory

        """
        files = data["files"]

        # Process in batches of 20
        batch_size = 20
        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]

            # Load AST for this batch
            ast_summaries = []
            for file_entry in batch:
                file_name = Path(file_entry["path"]).name
                ast_file = ast_dir / f"{file_name}.json"
                if ast_file.exists():
                    ast_data = json.loads(ast_file.read_text())
                    ast_summaries.append(
                        {
                            "path": file_entry["path"],
                            "summary": file_entry["summary"],
                            "ast": ast_data.get("suggested_justification", ""),
                        }
                    )
                else:
                    ast_summaries.append(
                        {
                            "path": file_entry["path"],
                            "summary": file_entry["summary"],
                        }
                    )

            prompt = f"""# File Justifications (Batch {i//batch_size + 1})

Project: {project_root}

## Files

{json.dumps(ast_summaries, indent=2)}

For each file, provide a 1-2 sentence justification explaining:
- What it does
- Why it's needed
- How it fits into the architecture

Output JSON:
```json
[
  {{"path": "src/...", "justification": "...", "status": "documented"}},
  ...
]
```
"""
            assert self.llm is not None, "LLM not initialized"
            response = self.llm.generate(prompt, max_tokens=2048, temperature=0.2)
            completions = self._parse_json_response(response)

            # Apply to files
            for completion in completions:
                for file_entry in batch:
                    if file_entry["path"] == completion.get("path"):
                        file_entry["justification"] = completion.get("justification", "")
                        file_entry["justification_status"] = completion.get("status", "documented")
                        break

    def _apply_resolutions(self, items: list, response: str):
        """Apply resolutions from LLM response to items list.

        Args:
            items: List of items to update (modified in-place)
            response: LLM response with resolutions

        """
        completions = self._parse_json_response(response)
        for completion in completions:
            idx = completion.get("index", 0)
            if idx < len(items):
                items[idx]["resolution"] = completion.get("resolution", "")
                items[idx]["status"] = completion.get("status", "reviewed")

    def _parse_json_response(self, response: str) -> list:
        """Parse JSON from LLM response.

        Args:
            response: LLM response (may contain markdown code blocks)

        Returns:
            Parsed JSON list

        """
        try:
            # Extract JSON from code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return []

    def get_required_inputs(self) -> set:
        """Requires justification JSON (or finds latest automatically)."""
        return set()

    def get_produced_outputs(self) -> set:
        """Produces completed justification JSON."""
        return {"completed_justification_json"}

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.LOW,  # Run after justification
            timeout_seconds=600,  # 10 minutes
            parameters={
                "root_dir": str(root_dir),
            },
        )
