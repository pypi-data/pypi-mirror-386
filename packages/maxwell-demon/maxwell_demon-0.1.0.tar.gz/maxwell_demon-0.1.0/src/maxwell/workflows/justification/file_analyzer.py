"""File discovery and analysis for justification workflow.

Single Responsibility: Discover files and generate compact summaries.
Reuses: maxwell.discovery, maxwell.storage, maxwell.workflows.ast_analysis
"""

__all__ = ["FileAnalysisResult", "FileAnalyzer"]

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from maxwell.config import MaxwellConfig
from maxwell.discovery import discover_files
from maxwell.filesystem import is_binary
from maxwell.storage import ContentHasher
from maxwell.workflows.ast_analysis import FileAnalysis, analyze_python_file


@dataclass
class FileAnalysisResult:
    """Result of analyzing a single file."""

    file_path: Path
    summary: str  # AST or LLM-generated
    file_hash: str  # SHA256
    is_python: bool
    ast_analysis: Optional[FileAnalysis] = None


class FileAnalyzer:
    """Discover and analyze files with AST (Python) or LLM (others)."""

    def __init__(self, fast_llm=None):
        """Initialize analyzer.

        Args:
            fast_llm: Optional LLM client for non-Python files

        """
        self.fast_llm = fast_llm
        self.hasher = ContentHasher()
        self.summary_cache: Dict[str, str] = {}

    def discover_files(self, project_root: Path, config: MaxwellConfig) -> List[Path]:
        """Discover files to analyze.

        Args:
            project_root: Project root directory
            config: Maxwell configuration

        Returns:
            List of file paths to analyze

        """
        # Reuse discovery module (low entropy!)
        return discover_files([], config)

    def analyze_files(
        self, files: List[Path], project_root: Path, cache: Optional[Dict[str, str]] = None
    ) -> List[FileAnalysisResult]:
        """Analyze all files and generate summaries.

        Args:
            files: List of files to analyze
            project_root: Project root directory
            cache: Optional cache of file_hash -> summary

        Returns:
            List of file analysis results

        """
        if cache:
            self.summary_cache = cache

        results = []

        for file_path in files:
            result = self.analyze_file(file_path)
            if result:
                results.append(result)

        return results

    def analyze_file(self, file_path: Path) -> Optional[FileAnalysisResult]:
        """Analyze a single file.

        Args:
            file_path: Path to file

        Returns:
            FileAnalysisResult or None if analysis failed

        """
        # Hash file content
        file_hash = self.hasher.hash_file(file_path)

        # Check cache
        if file_hash in self.summary_cache:
            summary = self.summary_cache[file_hash]
            is_python = file_path.suffix == ".py"

            # Get AST analysis if Python
            ast_analysis = None
            if is_python:
                ast_analysis = analyze_python_file(file_path)

            return FileAnalysisResult(
                file_path=file_path,
                summary=summary,
                file_hash=file_hash,
                is_python=is_python,
                ast_analysis=ast_analysis,
            )

        # Try AST first for Python files (fast, compact!)
        if file_path.suffix == ".py":
            ast_summary = self._summarize_with_ast(file_path)
            if ast_summary:
                self.summary_cache[file_hash] = ast_summary
                return FileAnalysisResult(
                    file_path=file_path,
                    summary=ast_summary,
                    file_hash=file_hash,
                    is_python=True,
                    ast_analysis=analyze_python_file(file_path),
                )

        # Fall back to LLM for non-Python files
        if self.fast_llm:
            llm_summary = self._summarize_with_llm(file_path)
            if llm_summary:
                self.summary_cache[file_hash] = llm_summary
                return FileAnalysisResult(
                    file_path=file_path,
                    summary=llm_summary,
                    file_hash=file_hash,
                    is_python=False,
                    ast_analysis=None,
                )

        return None

    def _summarize_with_ast(self, file_path: Path) -> Optional[str]:
        """Generate compact summary using AST analysis.

        Args:
            file_path: Path to Python file

        Returns:
            Compact AST-based summary or None if parsing failed

        """
        analysis = analyze_python_file(file_path)
        if not analysis:
            return None

        # Build compact summary
        parts = []

        if analysis.classes:
            classes_str = ", ".join(analysis.classes[:5])
            if len(analysis.classes) > 5:
                classes_str += f" (+{len(analysis.classes) - 5} more)"
            parts.append(f"Classes: {classes_str}")

        if analysis.functions:
            if not analysis.classes:
                # Only show functions if no classes
                funcs_str = ", ".join(analysis.functions[:5])
                if len(analysis.functions) > 5:
                    funcs_str += f" (+{len(analysis.functions) - 5} more)"
                parts.append(f"Functions: {funcs_str}")
            else:
                parts.append(f"{len(analysis.functions)} functions")

        if analysis.imports:
            key_imports = [imp for imp in analysis.imports[:10] if not imp.startswith("_")]
            if key_imports:
                imports_str = ", ".join(key_imports[:5])
                if len(key_imports) > 5:
                    imports_str += "..."
                parts.append(f"Imports: {imports_str}")

        if analysis.has_tests:
            parts.append("[WARNING] Test file")

        if analysis.complexity_hints:
            parts.append(f"[WARNING] {len(analysis.complexity_hints)} complexity warnings")

        summary_text = ". ".join(parts) + "."

        # Prepend docstring if present
        if analysis.docstring:
            first_sentence = analysis.docstring.split(".")[0] + "."
            summary_text = f"{first_sentence} {summary_text}"

        return summary_text

    def _summarize_with_llm(self, file_path: Path) -> Optional[str]:
        """Generate summary using LLM (for non-Python files).

        Args:
            file_path: Path to file

        Returns:
            LLM-generated summary or None if failed

        """
        if not self.fast_llm:
            return None

        # Check if binary
        if is_binary(file_path):
            return "[Binary file - cannot summarize]"

        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                return "[Empty file]"

            # Simple prompt for fast LLM
            prompt = f"""File: {file_path.name}

```
{content[:2000]}
```

Output a 1-2 sentence summary of what this file does. No preamble:"""

            response = self.fast_llm.generate(prompt, max_tokens=100, temperature=0.1)
            return response.strip() if response else None

        except Exception:
            return None

    def load_cache(self, cache_path: Path) -> Dict[str, str]:
        """Load summary cache from disk.

        Args:
            cache_path: Path to cache file (JSON)

        Returns:
            Dict of file_hash -> summary

        """
        import json

        if not cache_path.exists():
            return {}

        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_cache(self, cache_path: Path) -> None:
        """Save summary cache to disk.

        Args:
            cache_path: Path to cache file (JSON)

        """
        import json

        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, "w") as f:
            json.dump(self.summary_cache, f, indent=2)
