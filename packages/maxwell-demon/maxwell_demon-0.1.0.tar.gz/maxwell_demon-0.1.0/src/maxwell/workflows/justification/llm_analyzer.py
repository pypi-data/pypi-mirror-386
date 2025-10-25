"""LLM-based architectural analysis.

Single Responsibility: Use LLM to analyze codebase structure for issues.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from maxwell.workflows.justification.context_builder import StructuredContext

logger = logging.getLogger(__name__)


@dataclass
class ArchitecturalIssue:
    """Architectural issue found by LLM analysis."""

    title: str
    description: str
    category: str  # misplaced, useless, redundant, overly_large, consolidation
    priority: str  # HIGH, MEDIUM, LOW
    affected_files: List[str]


class LLMAnalyzer:
    """Use LLM to analyze codebase architecture."""

    def __init__(self, orchestrator_llm, max_tokens: int = 8192):
        """Initialize analyzer.

        Args:
            orchestrator_llm: LLM client for analysis
            max_tokens: Max tokens for LLM response

        """
        self.llm = orchestrator_llm
        self.max_tokens = max_tokens

    def analyze(
        self, context: StructuredContext, project_root: Path, project_rules: str = ""
    ) -> List[ArchitecturalIssue]:
        """Analyze codebase structure using LLM.

        Args:
            context: Structured context (XML chunks)
            project_root: Project root directory
            project_rules: Optional project-specific rules

        Returns:
            List of architectural issues

        """
        if not self.llm:
            logger.warning("LLM not available for architectural analysis")
            return []

        # Analyze each chunk
        chunk_analyses = []
        for i, chunk_xml in enumerate(context.xml_chunks):
            analysis = self._analyze_chunk(
                chunk_xml, i + 1, len(context.xml_chunks), project_root, project_rules
            )
            if analysis:
                chunk_analyses.append(analysis)

        # Extract issues from analyses
        issues = self._extract_issues(chunk_analyses)

        return issues

    def _analyze_chunk(
        self,
        chunk_xml: str,
        chunk_num: int,
        total_chunks: int,
        project_root: Path,
        project_rules: str,
    ) -> str:
        """Analyze a single XML chunk.

        Args:
            chunk_xml: XML content chunk
            chunk_num: Current chunk number
            total_chunks: Total number of chunks
            project_root: Project root directory
            project_rules: Project-specific rules

        Returns:
            Analysis text from LLM

        """
        # Build base prompt
        base_prompt = """Analyze this project's file structure for architectural issues.

**PROJECT ROOT PRINCIPLE**: A well-organized Python project keeps its root directory minimal.

**Root directory should ONLY contain**:
- Project metadata: setup.py, pyproject.toml, MANIFEST.in, tox.ini, LICENSE
- Single documentation entry point: README.md
- Configuration: .gitignore, .env.example
- Package entry points: __init__.py, __main__.py, conftest.py
- AI/Agent instructions: CLAUDE.md, AGENTS.instructions.md, *.instructions.md

**Everything else belongs in subdirectories**:
- Source code → src/ or package_name/
- Documentation → docs/
- Tests → tests/
- Examples → examples/"""

        # Add project rules if provided
        if project_rules:
            prompt = f"""{base_prompt}

**PROJECT-SPECIFIC RULES** (from AGENTS.instructions.md):
{project_rules}

**Codebase Structure** (Chunk {chunk_num}/{total_chunks}):
{chunk_xml}

**Task**: Identify architectural issues:
1. **Misplaced files**: Files in wrong locations (violating principles/rules)
2. **Useless files**: Dead code, backups, migration scripts
3. **Redundant files**: Duplicate functionality
4. **Overly large files**: Files >25000 bytes (poor modularity)
5. **Consolidation opportunities**: Files that should be merged

For each issue, provide:
- Title (brief)
- Description (why it's an issue)
- Category (misplaced/useless/redundant/overly_large/consolidation)
- Priority (HIGH/MEDIUM/LOW)
- Affected files (paths)

Be specific and actionable."""
        else:
            prompt = f"""{base_prompt}

**Codebase Structure** (Chunk {chunk_num}/{total_chunks}):
{chunk_xml}

**Task**: Identify architectural issues:
1. **Misplaced files**: Files in wrong locations
2. **Useless files**: Dead code, backups
3. **Redundant files**: Duplicate functionality
4. **Overly large files**: Files >25000 bytes
5. **Consolidation opportunities**: Files that should be merged

For each issue:
- Title (brief)
- Description (why it's an issue)
- Category (misplaced/useless/redundant/overly_large/consolidation)
- Priority (HIGH/MEDIUM/LOW)
- Affected files (paths)"""

        try:
            response = self.llm.generate(prompt, max_tokens=self.max_tokens, temperature=0.2)
            return response.strip() if response else ""
        except Exception as e:
            logger.error(f"Chunk {chunk_num} analysis failed: {e}")
            return ""

    def _extract_issues(self, chunk_analyses: List[str]) -> List[ArchitecturalIssue]:
        """Extract structured issues from LLM analyses.

        Args:
            chunk_analyses: List of analysis texts

        Returns:
            List of architectural issues

        """
        issues = []

        # Combine all analyses
        combined_analysis = "\n\n".join(chunk_analyses)

        # Simple pattern matching to extract issues
        # This is a basic implementation - could be improved with more sophisticated parsing

        # Look for common patterns like "Title:", "Description:", etc.
        sections = re.split(r"\n(?=\d+\.|##|\*\*)", combined_analysis)

        for section in sections:
            if not section.strip():
                continue

            # Try to extract structured info
            title_match = re.search(r"(?:Title|Issue):\s*(.+?)(?:\n|$)", section, re.IGNORECASE)
            desc_match = re.search(
                r"Description:\s*(.+?)(?:\n(?:Category|Priority|Files)|$)",
                section,
                re.IGNORECASE | re.DOTALL,
            )
            category_match = re.search(r"Category:\s*(\w+)", section, re.IGNORECASE)
            priority_match = re.search(r"Priority:\s*(HIGH|MEDIUM|LOW)", section, re.IGNORECASE)
            files_match = re.search(
                r"(?:Affected\s)?Files?:\s*(.+?)(?:\n\n|$)", section, re.IGNORECASE | re.DOTALL
            )

            if title_match:
                title = title_match.group(1).strip()
                description = desc_match.group(1).strip() if desc_match else section[:200]
                category = category_match.group(1).lower() if category_match else "other"
                priority = priority_match.group(1).upper() if priority_match else "MEDIUM"

                # Extract file paths
                affected_files = []
                if files_match:
                    files_text = files_match.group(1)
                    # Look for patterns like: - path/to/file.py
                    file_patterns = re.findall(r"[-•]\s*([^\s]+\.py)", files_text)
                    affected_files = file_patterns

                issues.append(
                    ArchitecturalIssue(
                        title=title,
                        description=description,
                        category=category,
                        priority=priority,
                        affected_files=affected_files,
                    )
                )

        return issues
