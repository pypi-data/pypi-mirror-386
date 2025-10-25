"""Build structured context for LLM analysis.

Single Responsibility: Create XML context from file analysis results.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List

from maxwell.workflows.justification.file_analyzer import FileAnalysisResult


@dataclass
class StructuredContext:
    """Structured context for LLM analysis."""

    xml_chunks: List[str]  # XML chunks that fit in LLM context
    file_count: int
    total_size: int  # Total characters


class ContextBuilder:
    """Build structured XML context for LLM."""

    def __init__(self, max_chunk_tokens: int = 30000):
        """Initialize builder.

        Args:
            max_chunk_tokens: Max tokens per chunk (default 30K)

        """
        self.max_chunk_tokens = max_chunk_tokens
        # Estimate 3 chars per token
        self.max_chunk_chars = max_chunk_tokens * 3

    def build(
        self, file_results: List[FileAnalysisResult], project_root: Path, project_rules: str = ""
    ) -> StructuredContext:
        """Build structured context from file analysis results.

        Args:
            file_results: List of file analysis results
            project_root: Project root directory
            project_rules: Optional project-specific rules from AGENTS.instructions.md

        Returns:
            StructuredContext with XML chunks

        """
        # Build XML tree
        xml_root = self._build_xml_tree(file_results, project_root)

        # Convert to string
        xml_string = ET.tostring(xml_root, encoding="unicode")

        # Chunk if needed
        chunks = self._chunk_xml(xml_string)

        return StructuredContext(
            xml_chunks=chunks, file_count=len(file_results), total_size=len(xml_string)
        )

    def _build_xml_tree(
        self, file_results: List[FileAnalysisResult], project_root: Path
    ) -> ET.Element:
        """Build XML tree from file results.

        Args:
            file_results: List of file analysis results
            project_root: Project root directory

        Returns:
            XML root element

        """
        project_elem = ET.Element("project", name=project_root.name, path=str(project_root))

        # Group files by directory
        dir_structure = {}
        for result in file_results:
            relative = result.file_path.relative_to(project_root)
            parts = relative.parts

            current = dir_structure
            for part in parts[:-1]:  # All but filename
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add file
            filename = parts[-1]
            current[filename] = result

        # Build XML recursively
        self._add_to_xml(project_elem, dir_structure, "")

        return project_elem

    def _add_to_xml(self, parent_elem: ET.Element, structure: dict, base_path: str):
        """Recursively add structure to XML.

        Args:
            parent_elem: Parent XML element
            structure: Directory structure dict
            base_path: Base path for relative paths

        """
        for name, content in sorted(structure.items()):
            if isinstance(content, dict):
                # It's a directory
                dir_elem = ET.SubElement(
                    parent_elem, "directory", name=name, path=f"{base_path}/{name}".strip("/")
                )
                self._add_to_xml(dir_elem, content, f"{base_path}/{name}".strip("/"))
            else:
                # It's a file (FileAnalysisResult)
                result: FileAnalysisResult = content
                # Compute relative path from base_path and filename
                rel_path = f"{base_path}/{name}".strip("/")
                file_elem = ET.SubElement(
                    parent_elem,
                    "file",
                    name=name,
                    path=rel_path,
                    size=str(result.file_path.stat().st_size if result.file_path.exists() else 0),
                )

                # Add summary
                summary_elem = ET.SubElement(file_elem, "summary")
                summary_elem.text = result.summary

    def _chunk_xml(self, xml_content: str) -> List[str]:
        """Chunk XML content to fit in LLM context.

        Args:
            xml_content: Full XML string

        Returns:
            List of XML chunks

        """
        # If fits in one chunk, return as-is
        if len(xml_content) <= self.max_chunk_chars:
            return [xml_content]

        # Otherwise, chunk by directory groups
        # For now, simple approach: split at </directory> boundaries
        chunks = []
        current_chunk = []
        current_size = 0

        lines = xml_content.split("\n")

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.max_chunk_chars and current_chunk:
                # Save current chunk
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size

        # Add remaining
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def load_project_rules(self, project_root: Path) -> str:
        """Load project-specific rules from AGENTS.instructions.md.

        Args:
            project_root: Project root directory

        Returns:
            Project rules string or empty if not found

        """
        agents_file = project_root / "AGENTS.instructions.md"

        if not agents_file.exists():
            return ""

        try:
            content = agents_file.read_text()

            # Extract file organization section
            if "## File Organization & Project Structure Rules" in content:
                start = content.find("## File Organization & Project Structure Rules")
                next_section = content.find("\n## ", start + 1)

                if next_section == -1:
                    return content[start:]
                else:
                    return content[start:next_section]

            return ""
        except Exception:
            return ""
