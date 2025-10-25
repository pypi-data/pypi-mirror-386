"""Worksheet Management Workflow - Simple Batch Output.

Dead simple:
1. Group all pending issues by file
2. Return file with MOST pending issues
3. Output to stdout for Claude Code to read
4. Provide --mark-completed to update worksheet

No LLM, no state files, just deterministic batching.
"""

from __future__ import annotations

__all__ = ["WorksheetManagerWorkflow"]

import hashlib
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowMetrics,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


@register_workflow
class WorksheetManagerWorkflow(BaseWorkflow):
    """Workflow for extracting next batch of tasks from justification worksheet.

    Groups pending issues by file, returns file with most issues.
    Simple, deterministic, no LLM overhead.
    """

    workflow_id: str = "justification-worksheet-manager"
    name: str = "Worksheet Issue Resolution"
    description: str = "Actually fix code issues from justification analysis"
    version: str = "1.0"
    category: str = "maintenance"
    tags: set = {"code-fixing", "automation", "justification"}

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute worksheet manager.

        Args:
            project_root: Project root directory
            context: Execution context (supports 'worksheet_path' and 'mark_completed' params)

        Returns:
            WorkflowResult with biggest batch

        """
        start_time = time.time()

        # Get worksheet path from context or find latest
        worksheet_path = context.get("worksheet_path")
        if worksheet_path:
            justification_file = Path(worksheet_path)
            if not justification_file.exists():
                return self.create_error_result(
                    f"Worksheet file not found: {worksheet_path}", start_time
                )
        else:
            justification_file = self._find_latest_justification(project_root)
            if not justification_file:
                return self.create_error_result(
                    "No completed justification file found. Run 'maxwell justification' first.",
                    start_time,
                )

        # Load worksheet data
        try:
            with open(justification_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            return self.create_error_result(f"Failed to read justification file: {e}", start_time)

        # Check if we're marking a file as completed
        mark_completed = context.get("mark_completed")
        if mark_completed:
            disagree = context.get("disagree", False)
            return self._mark_file_completed(
                justification_file, data, mark_completed, disagree, project_root, start_time
            )

        # Group pending issues by file
        batches = self._group_by_file(data)

        if not batches:
            print("\n✅ ALL TASKS COMPLETED! No pending issues in worksheet.\n")
            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.COMPLETED,
                metrics=WorkflowMetrics(start_time=start_time, end_time=time.time()),
                artifacts={"all_completed": True},
            )

        # Get file with MOST pending issues (biggest batch)
        biggest_batch = max(batches, key=lambda b: b["total_issues"])

        # Compute and store codebase hash before work begins
        codebase_hash = self._compute_codebase_hash(project_root)
        if codebase_hash:
            biggest_batch["codebase_hash"] = codebase_hash
            # Store hash in worksheet for verification
            data["current_batch_hash"] = codebase_hash
            try:
                with open(justification_file, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to store hash in worksheet: {e}")

        # Output to stdout for Claude Code
        self._print_batch(biggest_batch, len(batches))

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.COMPLETED,
            metrics=WorkflowMetrics(start_time=start_time, end_time=time.time()),
            artifacts={
                "file": biggest_batch["file"],
                "total_issues": biggest_batch["total_issues"],
                "remaining_files": len(batches) - 1,
                "codebase_hash": codebase_hash,
            },
        )

    def _find_latest_justification(self, project_root: Path) -> Optional[Path]:
        """Find the most recent completed justification file."""
        reports_dir = project_root / ".maxwell" / "reports"
        if not reports_dir.exists():
            return None

        completed_files = list(reports_dir.glob("justification_*completed.json"))
        if not completed_files:
            regular_files = list(reports_dir.glob("justification_*.json"))
            if regular_files:
                completed_files = regular_files

        if not completed_files:
            return None

        return max(completed_files, key=lambda p: p.stat().st_mtime)

    def _group_by_file(self, data: Dict[str, Any]) -> List[Dict]:
        """Group all pending issues by file.

        Returns:
            List of batches, each representing one file with its issues

        """
        batches = []

        # 1. Quality findings (blocking + warnings)
        quality_findings = data.get("quality_findings", [])
        pending_quality = [f for f in quality_findings if f.get("status") != "completed"]

        by_file = {}
        for finding in pending_quality:
            file_path = finding.get("file_path", "unknown")
            if file_path not in by_file:
                by_file[file_path] = {
                    "file": file_path,
                    "quality_issues": [],
                    "total_issues": 0,
                }
            by_file[file_path]["quality_issues"].append(finding)
            by_file[file_path]["total_issues"] += 1

        # Add to batches
        for file_batch in by_file.values():
            batches.append(file_batch)

        # 2. Architectural issues (not file-specific, treat as separate batch)
        arch_issues = data.get("architectural_issues", [])
        pending_arch = [i for i in arch_issues if i.get("status") != "completed"]

        if pending_arch:
            batches.append(
                {
                    "file": "ARCHITECTURAL_ISSUES",
                    "arch_issues": pending_arch,
                    "total_issues": len(pending_arch),
                }
            )

        # 3. Missing justifications
        files = data.get("files", [])
        missing_justifications = [f for f in files if f.get("justification_status") != "documented"]

        if missing_justifications:
            batches.append(
                {
                    "file": "MISSING_JUSTIFICATIONS",
                    "missing_justifications": missing_justifications,
                    "total_issues": len(missing_justifications),
                }
            )

        return batches

    def _compute_codebase_hash(self, project_root: Path) -> str:
        """Compute hash of current codebase state using snapshot.

        Args:
            project_root: Project root directory

        Returns:
            SHA256 hash of snapshot output

        """
        try:
            # Run snapshot to stdout
            result = subprocess.run(
                ["maxwell", "snapshot", "--stdout"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.warning(f"Snapshot failed for hash computation: {result.stderr}")
                return ""

            # Hash the snapshot output
            return hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()

        except Exception as e:
            logger.warning(f"Failed to compute codebase hash: {e}")
            return ""

    def _verify_justifications_exist(self, data: Dict[str, Any], project_root: Path) -> int:
        """Verify that files have written justifications explaining why they exist.

        Args:
            data: Worksheet data
            project_root: Project root directory

        Returns:
            Number of files still missing justifications

        """
        missing_count = 0
        files_to_check = []

        for file_info in data.get("files", []):
            status = file_info.get("justification_status")
            if status != "documented":
                files_to_check.append(file_info)

                # Check if justification field exists and has content
                justification = file_info.get("justification", "").strip()

                if not justification or len(justification) < 20:
                    print(f"❌ Missing justification: {file_info.get('path')}")
                    print(f"   Status: {status}")
                    print(f"   Justification: {justification[:50] if justification else '(empty)'}")
                    missing_count += 1

        if files_to_check:
            print(
                f"\n[INFO] Checked {len(files_to_check)} files, {missing_count} still need justifications"
            )

        return missing_count

    def _print_batch(self, batch: Dict, total_batches: int):
        """Print ONE batch to stdout for Claude Code to read."""
        print("\n" + "=" * 80)
        print(f"NEXT BATCH: {batch['file']}")
        print(f"({batch['total_issues']} issues, {total_batches - 1} other files pending)")
        print("=" * 80)
        print()
        print("INSTRUCTIONS (see AGENTS.instructions.md):")
        print()
        print("1. INTERNAL vs EXTERNAL data:")
        print("   - Internal: Use typed dataclasses + strict access (no dict.get)")
        print("   - External: MongoDB/JSON/TOML - dict.get() is appropriate at IO boundary")
        print()
        print("2. For workflows with Dict[str, Any] context:")
        print("   - Define InputSchema dataclass (see AGENTS.instructions.md line 143-171)")
        print("   - Use self.parse_inputs(context) for type-safe access")
        print("   - Replace context.get('field', default) with inputs.field")
        print()
        print("3. For dict.get() issues:")
        print("   - If reading from MongoDB/external JSON: KEEP (use --disagree)")
        print("   - If reading from internal structures: FIX (use dataclass)")
        print()
        print("4. After fixing, verify changes made:")
        print("   - Guardrail will check codebase hash changed")
        print("   - Or use --disagree if false positive")
        print()
        print("=" * 80)

        # Quality issues
        if "quality_issues" in batch:
            print(f"\nQuality Issues ({len(batch['quality_issues'])}):\n")
            for i, finding in enumerate(batch["quality_issues"], 1):
                severity = finding.get("severity", "WARN")
                line = finding.get("line", "?")
                msg = finding.get("message", "")
                print(f"{i}. [{severity}] Line {line}: {msg}")
                if finding.get("suggestion"):
                    print(f"   → {finding['suggestion']}")
                print()

        # Architectural issues
        if "arch_issues" in batch:
            print(f"\nArchitectural Issues ({len(batch['arch_issues'])}):\n")
            for i, issue in enumerate(batch["arch_issues"], 1):
                print(f"{i}. {issue.get('title', '')}")
                print(f"   Resolution: {issue.get('resolution', '')}")
                print()

        # Missing justifications
        if "missing_justifications" in batch:
            print(f"\nMissing Justifications ({len(batch['missing_justifications'])} files):\n")
            for i, file_info in enumerate(batch["missing_justifications"][:10], 1):
                print(f"{i}. {file_info.get('path', '')}")
                if file_info.get("summary"):
                    print(f"   Summary: {file_info['summary'][:80]}...")
                print()
            if len(batch["missing_justifications"]) > 10:
                print(f"   ... and {len(batch['missing_justifications']) - 10} more\n")

        print("=" * 80)
        print("\nAfter fixing these issues:")
        print(f"   maxwell justification-worksheet-manager --mark-completed {batch['file']}")
        print("\nTo disagree with false positives:")
        print(
            f"   maxwell justification-worksheet-manager --mark-completed {batch['file']} --disagree"
        )
        print("\n" + "=" * 80 + "\n")

    def _mark_file_completed(
        self,
        justification_file: Path,
        data: Dict[str, Any],
        file_path: str,
        disagree: bool,
        project_root: Path,
        start_time: float,
    ) -> WorkflowResult:
        """Mark all issues for a file as completed.

        Args:
            justification_file: Path to worksheet JSON
            data: Worksheet data
            file_path: File to mark as completed
            disagree: Whether user disagrees with the issues (bypasses hash check)
            project_root: Project root directory
            start_time: Workflow start time

        Returns:
            WorkflowResult with completion status

        """
        # Guardrail: Check if codebase actually changed
        if not disagree:
            stored_hash = data.get("current_batch_hash")
            if stored_hash:
                current_hash = self._compute_codebase_hash(project_root)
                if current_hash == stored_hash:
                    error_msg = (
                        "❌ GUARDRAIL: No code changes detected!\n\n"
                        "The codebase hash hasn't changed since this batch was presented.\n"
                        "Either:\n"
                        "  1. Make actual code changes to fix the issues, OR\n"
                        "  2. Use --disagree if you believe these are false positives\n\n"
                        "Usage: maxwell worksheet-manager --mark-completed <file> --disagree"
                    )
                    print(error_msg)
                    return self.create_error_result(error_msg, start_time)
                else:
                    print("✅ Code changes detected (hash changed)")
            else:
                print("⚠️  No stored hash found - skipping guardrail check")

        if disagree:
            print("📝 Marking as completed (--disagree flag: user overrides issues)")

        # Guardrail: Check justifications for MISSING_JUSTIFICATIONS batch
        if file_path == "MISSING_JUSTIFICATIONS" and not disagree:
            missing_count = self._verify_justifications_exist(data, project_root)
            if missing_count > 0:
                error_msg = (
                    f"❌ GUARDRAIL: {missing_count} files still lack architectural justifications!\n\n"
                    "Each file needs a 'justification' explaining WHY it exists:\n"
                    "  - What problem does this file solve?\n"
                    "  - Why is it separate from other files?\n"
                    "  - Is it still needed or could it be merged/removed?\n\n"
                    "Add justifications to the worksheet JSON, then re-run.\n\n"
                    "Or use --disagree to skip this check:\n"
                    "  maxwell justification-worksheet-manager --mark-completed MISSING_JUSTIFICATIONS --disagree"
                )
                print(error_msg)
                return self.create_error_result(error_msg, start_time)
            else:
                print("✅ All files have proper justifications")

        # Count issues marked
        marked = 0

        # Mark quality findings
        for finding in data.get("quality_findings", []):
            if finding.get("file_path") == file_path and finding.get("status") != "completed":
                finding["status"] = "completed"
                marked += 1

        # Mark architectural issues (special case)
        if file_path == "ARCHITECTURAL_ISSUES":
            for issue in data.get("architectural_issues", []):
                if issue.get("status") != "completed":
                    issue["status"] = "completed"
                    marked += 1

        # Mark missing justifications (special case)
        if file_path == "MISSING_JUSTIFICATIONS":
            for file_info in data.get("files", []):
                if file_info.get("justification_status") != "documented":
                    file_info["justification_status"] = "documented"
                    marked += 1

        # Write back to worksheet
        try:
            with open(justification_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"\n✅ Marked {marked} issues as completed for {file_path}\n")
        except Exception as e:
            return self.create_error_result(f"Failed to update worksheet: {e}", start_time)

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.COMPLETED,
            metrics=WorkflowMetrics(start_time=start_time, end_time=time.time()),
            artifacts={
                "file": file_path,
                "issues_marked": marked,
            },
        )

    def create_error_result(self, error_message: str, start_time: float) -> WorkflowResult:
        """Create error result."""
        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=WorkflowStatus.FAILED,
            metrics=WorkflowMetrics(start_time=start_time, end_time=time.time()),
            error_message=error_message,
        )

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Define CLI parameters for worksheet manager.

        Returns:
            List of parameter definitions for argparse

        """
        return [
            {
                "name": "worksheet_path",
                "type": str,
                "required": False,
                "help": "Path to justification worksheet JSON (defaults to latest)",
            },
            {
                "name": "mark_completed",
                "type": str,
                "required": False,
                "help": "Mark all issues for this file as completed",
            },
            {
                "name": "disagree",
                "type": bool,
                "required": False,
                "default": False,
                "help": "Mark as completed without code changes (disagree with issues)",
            },
        ]

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        from maxwell.workflows.base import WorkflowPriority

        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.HIGH,
            timeout_seconds=600,
            parameters={
                "root_dir": str(root_dir),
            },
        )
