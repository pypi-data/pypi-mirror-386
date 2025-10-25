"""Run code quality checks (validate, ruff, pyright).

Single Responsibility: Execute external quality tools and normalize findings.
"""

__all__ = ["QualityChecker", "QualityFinding"]

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class QualityFinding:
    """Normalized quality finding from any source."""

    source: str  # validate, ruff, pyright
    rule_id: str
    severity: str  # BLOCK, WARN, INFO
    file_path: str
    line: int
    column: int
    message: str
    suggestion: str | None = None


class QualityChecker:
    """Run code quality tools and normalize findings."""

    def check_all(self, project_root: Path, files: List[Path]) -> List[QualityFinding]:
        """Run all quality checks.

        Args:
            project_root: Project root directory
            files: List of files to check

        Returns:
            List of normalized quality findings

        """
        findings = []

        # Run validate (custom validators)
        try:
            validate_findings = self.run_validate(project_root)
            findings.extend(validate_findings)
        except Exception as e:
            logger.warning(f"Validate check failed: {e}")

        # Run ruff (linting)
        try:
            ruff_findings = self.run_ruff(project_root)
            findings.extend(ruff_findings)
        except Exception as e:
            logger.warning(f"Ruff check failed: {e}")

        # Run pyright (type checking)
        try:
            pyright_findings = self.run_pyright(project_root)
            findings.extend(pyright_findings)
        except Exception as e:
            logger.warning(f"Pyright check failed: {e}")

        return findings

    def run_validate(self, project_root: Path) -> List[QualityFinding]:
        """Run maxwell validate workflow.

        Args:
            project_root: Project root directory

        Returns:
            List of findings from custom validators

        """
        from maxwell.config import load_hierarchical_config
        from maxwell.workflows.validate.validation_engine import run_plugin_validation

        # Load config and run validation
        config = load_hierarchical_config(project_root)
        runner = run_plugin_validation(config, project_root)

        # Normalize findings
        findings = []
        for finding in runner.findings:
            findings.append(
                QualityFinding(
                    source="validate",
                    rule_id=finding.rule_id,
                    severity=finding.severity.value,  # Severity is an enum
                    file_path=str(finding.file_path),
                    line=finding.line,
                    column=finding.column,
                    message=finding.message,
                    suggestion=finding.suggestion,
                )
            )

        return findings

    def run_ruff(self, project_root: Path) -> List[QualityFinding]:
        """Run ruff linter.

        Args:
            project_root: Project root directory

        Returns:
            List of findings from ruff

        """
        import sys

        # Try to find ruff in the same Python environment
        ruff_path = Path(sys.executable).parent / "ruff"
        if not ruff_path.exists():
            ruff_path = "ruff"  # Fall back to PATH

        try:
            result = subprocess.run(
                [str(ruff_path), "check", ".", "--output-format=json"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if not result.stdout:
                return []

            ruff_data = json.loads(result.stdout)

            findings = []
            for item in ruff_data:
                # Map ruff severity to our standard
                severity = "WARN"  # Default
                if item.get("fix"):
                    severity = "INFO"  # Auto-fixable = less severe

                findings.append(
                    QualityFinding(
                        source="ruff",
                        rule_id=item.get("code", "unknown"),
                        severity=severity,
                        file_path=str(item.get("filename", "")),
                        line=item.get("location", {}).get("row", 0),
                        column=item.get("location", {}).get("column", 0),
                        message=item.get("message", ""),
                        suggestion=item.get("fix", {}).get("message") if item.get("fix") else None,
                    )
                )

            return findings

        except FileNotFoundError:
            logger.warning("Ruff not found - skipping ruff check")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("Ruff check timed out")
            return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse ruff output")
            return []
        except Exception as e:
            logger.warning(f"Ruff check failed: {e}")
            return []

    def run_pyright(self, project_root: Path) -> List[QualityFinding]:
        """Run pyright type checker.

        Args:
            project_root: Project root directory

        Returns:
            List of findings from pyright

        """
        import sys

        # Try to find pyright in the same Python environment
        pyright_path = Path(sys.executable).parent / "pyright"
        if not pyright_path.exists():
            pyright_path = "pyright"  # Fall back to PATH

        try:
            result = subprocess.run(
                [str(pyright_path), "--outputjson"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if not result.stdout:
                return []

            pyright_data = json.loads(result.stdout)

            findings = []
            for diagnostic in pyright_data.get("generalDiagnostics", []):
                # Map pyright severity to our standard
                severity_map = {"error": "BLOCK", "warning": "WARN", "information": "INFO"}

                severity = severity_map.get(diagnostic.get("severity", "information"), "INFO")

                findings.append(
                    QualityFinding(
                        source="pyright",
                        rule_id=diagnostic.get("rule", "type-error"),
                        severity=severity,
                        file_path=str(diagnostic.get("file", "")),
                        line=diagnostic.get("range", {}).get("start", {}).get("line", 0) + 1,
                        column=diagnostic.get("range", {}).get("start", {}).get("character", 0),
                        message=diagnostic.get("message", ""),
                        suggestion=None,
                    )
                )

            return findings

        except FileNotFoundError:
            logger.warning("Pyright not found - skipping type check")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("Pyright check timed out")
            return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse pyright output")
            return []
        except Exception as e:
            logger.warning(f"Pyright check failed: {e}")
            return []

    def group_by_severity(self, findings: List[QualityFinding]) -> Dict[str, List[QualityFinding]]:
        """Group findings by severity.

        Args:
            findings: List of findings

        Returns:
            Dict of severity -> findings

        """
        grouped = {"BLOCK": [], "WARN": [], "INFO": []}

        for finding in findings:
            severity = finding.severity
            if severity in grouped:
                grouped[severity].append(finding)

        return grouped

    def group_by_source(self, findings: List[QualityFinding]) -> Dict[str, List[QualityFinding]]:
        """Group findings by source tool.

        Args:
            findings: List of findings

        Returns:
            Dict of source -> findings

        """
        grouped = {"validate": [], "ruff": [], "pyright": []}

        for finding in findings:
            source = finding.source
            if source in grouped:
                grouped[source].append(finding)

        return grouped
