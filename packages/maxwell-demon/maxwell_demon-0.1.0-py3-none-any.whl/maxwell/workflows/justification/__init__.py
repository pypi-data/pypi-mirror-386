"""Modular justification workflow - thin orchestrator.

Architecture:
- file_analyzer: File discovery + AST/LLM summarization
- context_builder: Build XML context for LLM
- llm_analyzer: Architectural analysis with LLM
- quality_checks: Run validate/ruff/pyright
- worksheet_generator: Generate markdown worksheet

Single Responsibility: Compose modules, manage workflow lifecycle, maintain BaseWorkflow interface.
"""

from __future__ import annotations

__all__ = ["JustificationEngine"]

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from maxwell.workflows.base import WorkflowResult

from maxwell.config import load_hierarchical_config
from maxwell.registry import register_workflow
from maxwell.workflows.base import BaseWorkflow, WorkflowConfig, WorkflowPriority

# Import justification workflows to register them
from maxwell.workflows.justification import complete_justification, worksheet_manager  # noqa: F401

# Import modular components
from maxwell.workflows.justification.context_builder import ContextBuilder
from maxwell.workflows.justification.file_analyzer import FileAnalyzer
from maxwell.workflows.justification.llm_analyzer import LLMAnalyzer
from maxwell.workflows.justification.quality_checks import QualityChecker

logger = logging.getLogger(__name__)


@register_workflow
class JustificationEngine(BaseWorkflow):
    """Modular justification engine - composes focused modules."""

    # Workflow metadata for registry
    workflow_id: str = "justification"
    name: str = "Code Justification Analysis"
    description: str = "Analyze code architecture for misplaced/useless/redundant files using LLM"
    version: str = "4.0"  # Bumped for modular rewrite
    category: str = "analysis"
    tags: set = {"code-quality", "llm-analysis", "architecture"}

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize workflow (LLM loading deferred until execute)."""
        self.workflow_id = "justification"
        self.name = "Code Justification Analysis"
        self.description = (
            "Analyze code architecture for misplaced/useless/redundant files using LLM"
        )
        self.version = "4.0"
        super().__init__(config)
        self.config = config or WorkflowConfig()

        # LLM initialization is LAZY - only happens on first execute()
        self._llm_initialized = False
        self.fast_llm = None
        self.orchestrator_llm = None
        self.fast_max_tokens = 2048
        self.orchestrator_max_tokens = 8192

        # Module initialization is also lazy (needs LLM clients)
        self.file_analyzer = None
        self.context_builder = None
        self.llm_analyzer = None
        self.quality_checker = None

        # Logging setup (deferred until execute)
        self.timestamp = None
        self._logging_setup = False

    def _init_llm(self):
        """Initialize LM clients from pool (lazy - called on first execute)."""
        if self._llm_initialized:
            return  # Already initialized

        try:
            from maxwell.lm_pool import get_lm

            # Fast LM for file summaries (needs ~16K context for large files)
            self.fast_llm = get_lm(min_context=16000)
            # Large-context LM for architectural analysis
            self.orchestrator_llm = get_lm(min_context=32000)

            # Extract capabilities
            self.fast_max_tokens = self.fast_llm.spec.capabilities.get("max_tokens", 2048)
            self.orchestrator_max_tokens = self.orchestrator_llm.spec.capabilities.get(
                "max_tokens", 8192
            )

            logger.info(
                f"LM pool initialized (fast: {self.fast_llm.spec.name}, "
                f"orchestrator: {self.orchestrator_llm.spec.name})"
            )
        except Exception as e:
            logger.warning(f"LM not available: {e}")
            self.fast_llm = None
            self.orchestrator_llm = None
            self.fast_max_tokens = 2048
            self.orchestrator_max_tokens = 8192

        # Initialize modular components now that we have LLMs
        self.file_analyzer = FileAnalyzer(fast_llm=self.fast_llm)
        self.context_builder = ContextBuilder(max_chunk_tokens=30000)
        self.llm_analyzer = LLMAnalyzer(
            orchestrator_llm=self.orchestrator_llm,
            max_tokens=self.orchestrator_max_tokens,
        )
        self.quality_checker = QualityChecker()

        self._llm_initialized = True

    def _setup_logging(self, project_root: Path):
        """Set up logging for this run."""
        if self._logging_setup:
            return

        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        logs_dir = project_root / ".maxwell" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Auto-create .gitignore in .maxwell/
        maxwell_gitignore = project_root / ".maxwell" / ".gitignore"
        if not maxwell_gitignore.exists():
            maxwell_gitignore.write_text("*\n")

        self._logging_setup = True
        logger.info(f"Logging initialized for run: {self.timestamp}")

    def execute(self, project_root: Path, context: dict) -> "WorkflowResult":
        """Execute justification analysis workflow.

        Args:
            project_root: Project root directory
            context: Execution context (unused currently)

        Returns:
            WorkflowResult with status, metrics, artifacts

        """
        from maxwell.workflows.base import WorkflowMetrics, WorkflowResult, WorkflowStatus

        start_time = time.time()

        try:
            # Lazy initialization - only happens on first execute()
            if not self._llm_initialized:
                self._init_llm()

            # Setup logging
            self._setup_logging(project_root)

            # Run modular workflow
            result = self.run_justification(project_root)

            # Build metrics
            end_time = time.time()
            metrics = WorkflowMetrics(
                start_time=start_time,
                end_time=end_time,
                files_processed=result.get("files_analyzed", 0),
                custom_metrics={
                    "cache_hits": result.get("cache_hits", 0),
                    "cache_misses": result.get("cache_misses", 0),
                    "architectural_issues": result.get("architectural_issues", 0),
                    "quality_findings": result.get("quality_findings", 0),
                },
            )
            metrics.finalize()

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.COMPLETED if result.get("success") else WorkflowStatus.FAILED,
                metrics=metrics,
                artifacts={
                    "json_output": result.get("json_output", ""),
                    "cache_dir": result.get("cache_dir", ""),
                },
                error_message=result.get("error"),
            )
        except Exception as e:
            end_time = time.time()
            metrics = WorkflowMetrics(start_time=start_time, end_time=end_time)
            metrics.finalize()

            logger.exception(f"Justification workflow failed: {e}")

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.FAILED,
                metrics=metrics,
                error_message=str(e),
            )

    def run_justification(self, project_root: Path) -> dict:
        """Run modular justification workflow.

        Args:
            project_root: Project root directory

        Returns:
            Dict with success, worksheet, metrics

        """
        start_time = time.time()
        project_root = project_root.resolve()

        logger.info(f"Starting justification analysis for: {project_root}")

        # Ensure components are initialized
        assert self.file_analyzer is not None, "file_analyzer not initialized"
        assert self.context_builder is not None, "context_builder not initialized"
        assert self.llm_analyzer is not None, "llm_analyzer not initialized"
        assert self.quality_checker is not None, "quality_checker not initialized"

        # Step 1: Discover and analyze files
        logger.info("Step 1: Discovering and analyzing files...")
        config = load_hierarchical_config(project_root)
        files = self.file_analyzer.discover_files(project_root, config)
        logger.info(f"Discovered {len(files)} files")

        # Load cache and analyze files
        cache_path = project_root / ".maxwell" / "cache" / "file_summaries.json"
        cache = self.file_analyzer.load_cache(cache_path)
        file_results = self.file_analyzer.analyze_files(files, project_root, cache=cache)

        # Save cache
        self.file_analyzer.save_cache(cache_path)

        cache_hits = sum(1 for r in file_results if r.file_hash in cache)
        cache_misses = len(file_results) - cache_hits

        logger.info(f"File analysis complete: {cache_hits} cached, {cache_misses} new")

        # Step 2: Build structured context for LLM
        logger.info("Step 2: Building XML context...")
        project_rules = self.context_builder.load_project_rules(project_root)
        context = self.context_builder.build(file_results, project_root, project_rules)
        logger.info(
            f"Context built: {context.file_count} files, "
            f"{context.total_size:,} chars, {len(context.xml_chunks)} chunks"
        )

        # Step 3: LLM architectural analysis
        logger.info("Step 3: Running LLM architectural analysis...")
        arch_issues = self.llm_analyzer.analyze(context, project_root, project_rules)
        logger.info(f"Found {len(arch_issues)} architectural issues")

        # Step 4: Quality checks (validate, ruff, pyright)
        logger.info("Step 4: Running quality checks...")
        quality_findings = self.quality_checker.check_all(project_root, files)
        logger.info(f"Found {len(quality_findings)} quality findings")

        # Group by severity for reporting
        by_severity = self.quality_checker.group_by_severity(quality_findings)
        logger.info(
            f"  - Blocking: {len(by_severity['BLOCK'])}, "
            f"Warnings: {len(by_severity['WARN'])}, "
            f"Info: {len(by_severity['INFO'])}"
        )

        # Step 5: Save artifacts to cache
        logger.info("Step 5: Saving artifacts...")
        cache_dir = project_root / ".maxwell" / "cache" / f"justification_{self.timestamp}"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Save XML context (xml_chunks are already strings)
        xml_path = cache_dir / "context.xml"
        xml_path.write_text("\n\n<!-- CHUNK SEPARATOR -->\n\n".join(context.xml_chunks))
        logger.info(f"Saved XML context: {xml_path} ({len(context.xml_chunks)} chunks)")

        # Save AST analyses
        ast_dir = cache_dir / "ast"
        ast_dir.mkdir(exist_ok=True)
        for result in file_results:
            if result.ast_analysis:
                ast_file = ast_dir / f"{result.file_path.name}.json"
                import json

                ast_data = {
                    "path": str(result.file_path.relative_to(project_root)),
                    "classes": result.ast_analysis.classes,
                    "functions": result.ast_analysis.functions,
                    "imports": result.ast_analysis.imports,
                    "docstring": result.ast_analysis.docstring,
                    "has_tests": result.ast_analysis.has_tests,
                    "complexity_hints": result.ast_analysis.complexity_hints,
                    "suggested_justification": result.ast_analysis.suggested_justification,
                }
                ast_file.write_text(json.dumps(ast_data, indent=2))
        logger.info(
            f"Saved {len([r for r in file_results if r.ast_analysis])} AST analyses: {ast_dir}"
        )

        # Step 6: Generate JSON output
        logger.info("Step 6: Generating JSON output...")
        json_path = project_root / ".maxwell" / "reports" / f"justification_{self.timestamp}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        self._save_json_output(
            json_path, arch_issues, quality_findings, file_results, project_root, cache_dir
        )

        duration = time.time() - start_time
        logger.info(f"Analysis complete in {duration:.1f}s")
        logger.info(f"  JSON output: {json_path}")
        logger.info(f"  Cached artifacts: {cache_dir}")

        # Print follow-up instructions
        print("\n" + "=" * 80)
        print("JUSTIFICATION ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\nFound {len(quality_findings)} quality issues in {len(file_results)} files")
        print(f"Found {len(arch_issues)} architectural issues")
        print("\nNext steps:")
        print("  1. Review guidelines: AGENTS.instructions.md")
        print("  2. Fix issues systematically: maxwell justification-worksheet-manager")
        print(
            "  3. After fixing each file: maxwell justification-worksheet-manager --mark-completed <file>"
        )
        print("\n" + "=" * 80 + "\n")

        return {
            "success": True,
            "json_output": str(json_path),
            "cache_dir": str(cache_dir),
            "files_analyzed": len(file_results),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "architectural_issues": len(arch_issues),
            "quality_findings": len(quality_findings),
            "duration": duration,
        }

    def _save_json_output(
        self,
        json_path: Path,
        arch_issues,
        quality_findings,
        file_results,
        project_root: Path,
        cache_dir: Path,
    ):
        """Save JSON output for deterministic progress tracking.

        Args:
            json_path: Path to JSON output file
            arch_issues: List of architectural issues
            quality_findings: List of quality findings
            file_results: List of file analysis results
            project_root: Project root directory
            cache_dir: Path to cache directory with artifacts

        """
        import json

        output = {
            "metadata": {
                "timestamp": self.timestamp,
                "project_root": str(project_root),
                "files_analyzed": len(file_results),
                "cache_dir": str(cache_dir),
                "artifacts": {
                    "xml_context": str(cache_dir / "context.xml"),
                    "ast_analyses": str(cache_dir / "ast"),
                },
            },
            "summary": {
                "architectural_issues": len(arch_issues),
                "quality_findings": {
                    "total": len(quality_findings),
                    "blocking": len([f for f in quality_findings if f.severity == "BLOCK"]),
                    "warnings": len([f for f in quality_findings if f.severity == "WARN"]),
                    "info": len([f for f in quality_findings if f.severity == "INFO"]),
                },
            },
            "architectural_issues": [
                {
                    "title": issue.title,
                    "description": issue.description,
                    "category": issue.category,
                    "priority": issue.priority,
                    "affected_files": issue.affected_files,
                    "status": "pending",  # For tracking: pending, reviewed, fixed
                }
                for issue in arch_issues
            ],
            "quality_findings": [
                {
                    "source": finding.source,
                    "rule_id": finding.rule_id,
                    "severity": finding.severity,
                    "file_path": finding.file_path,
                    "line": finding.line,
                    "column": finding.column,
                    "message": finding.message,
                    "suggestion": finding.suggestion,
                    "status": "pending",  # For tracking: pending, fixed
                }
                for finding in quality_findings
            ],
            "files": [
                {
                    "path": str(result.file_path.relative_to(project_root)),
                    "is_python": result.is_python,
                    "summary": result.summary,
                    "justification_status": "pending",  # For tracking: pending, reviewed, documented
                }
                for result in file_results
            ],
        }

        json_path.write_text(json.dumps(output, indent=2))

    def get_required_inputs(self) -> set:
        """No required inputs."""
        return set()

    def get_produced_outputs(self) -> set:
        """Produces justification JSON with cached artifacts."""
        return {"justification_json", "xml_context", "ast_analyses"}

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=1800,  # 30 minutes
            parameters={
                "root_dir": str(root_dir),
            },
        )
