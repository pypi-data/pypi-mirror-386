"""AST-based code analysis for Python files.

Inspired by vtcode's Tree-sitter approach, but using libcst (Maxwell's existing dependency).
Used by justification workflow to auto-suggest file purposes and detect code smells.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import libcst as cst


@dataclass
class FileAnalysis:
    """Analysis results for a single Python file."""

    path: Path
    classes: List[str]
    functions: List[str]
    imports: List[str]
    docstring: str | None
    has_tests: bool
    complexity_hints: List[str]
    suggested_justification: str


class PythonASTAnalyzer(cst.CSTVisitor):
    """LibCST visitor to extract structural information from Python files."""

    def __init__(self):
        self.classes: List[str] = []
        self.functions: List[str] = []
        self.imports: List[str] = []
        self.docstring: str | None = None
        self.has_tests: bool = False
        self.complexity_hints: List[str] = []

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Extract class names."""
        class_name = node.name.value
        self.classes.append(class_name)

        # Check for test classes
        if class_name.startswith("Test") or "test" in class_name.lower():
            self.has_tests = True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Extract function names and detect tests."""
        func_name = node.name.value
        self.functions.append(func_name)

        # Check for test functions
        if func_name.startswith("test_"):
            self.has_tests = True

        # Detect complexity hints (many parameters)
        param_count = len(node.params.params)
        if param_count > 7:
            self.complexity_hints.append(
                f"Function {func_name} has many parameters (>{param_count})"
            )

    def visit_Import(self, node: cst.Import) -> None:
        """Extract import statements."""
        for name in node.names:
            if isinstance(name, cst.ImportAlias):
                import_value = name.name.value
                if isinstance(import_value, str):
                    self.imports.append(import_value)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Extract from...import statements."""
        if node.module:
            # Build full module name from AST nodes
            parts = self._extract_module_name(node.module)
            if parts:
                self.imports.append(".".join(parts))

    def _extract_module_name(self, node) -> List[str]:
        """Recursively extract module name from import node."""
        if isinstance(node, cst.Name):
            return [node.value]
        elif isinstance(node, cst.Attribute):
            # Traverse attribute chain: a.b.c
            base_parts = self._extract_module_name(node.value)
            base_parts.append(node.attr.value)
            return base_parts
        return []

    def visit_Module(self, node: cst.Module) -> None:
        """Extract module-level docstring."""
        # Check first statement for docstring
        if node.body and len(node.body) > 0:
            first_stmt = node.body[0]
            if isinstance(first_stmt, cst.SimpleStatementLine):
                if len(first_stmt.body) > 0:
                    stmt = first_stmt.body[0]
                    if isinstance(stmt, cst.Expr) and isinstance(stmt.value, cst.SimpleString):
                        # Remove quotes (triple or single)
                        raw = stmt.value.value
                        # Strip quotes: """...""" or '''...''' or "..." or '...'
                        self.docstring = raw.strip('"""').strip("'''").strip('"').strip("'")


def analyze_python_file(file_path: Path) -> FileAnalysis | None:
    """Analyze a Python file using libcst.

    Args:
        file_path: Path to Python file

    Returns:
        FileAnalysis with extracted structure, or None if parsing fails

    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = cst.parse_module(content)
        visitor = PythonASTAnalyzer()
        tree.visit(visitor)  # Correct libcst API

        # Generate suggested justification based on content
        justification = _suggest_justification(
            file_path=file_path,
            classes=visitor.classes,
            functions=visitor.functions,
            imports=visitor.imports,
            has_tests=visitor.has_tests,
            docstring=visitor.docstring,
        )

        return FileAnalysis(
            path=file_path,
            classes=visitor.classes,
            functions=visitor.functions,
            imports=visitor.imports,
            docstring=visitor.docstring,
            has_tests=visitor.has_tests,
            complexity_hints=visitor.complexity_hints,
            suggested_justification=justification,
        )
    except Exception:
        # Parsing failed (syntax error, encoding issue, etc.)
        return None


def _suggest_justification(
    file_path: Path,
    classes: List[str],
    functions: List[str],
    imports: List[str],
    has_tests: bool,
    docstring: str | None,
) -> str:
    """Auto-suggest a file justification based on AST analysis.

    Args:
        file_path: Path to the file
        classes: List of class names found
        functions: List of function names found
        imports: List of imported modules
        has_tests: Whether file contains tests
        docstring: Module docstring if present

    Returns:
        Suggested justification text

    """
    parts = []

    # Use docstring if available
    if docstring:
        # Limit to first sentence or 100 chars
        short_doc = docstring.split(".")[0] if "." in docstring else docstring
        if len(short_doc) > 100:
            short_doc = short_doc[:97] + "..."
        parts.append(short_doc.strip())

    # Describe file type
    if has_tests:
        parts.append("Test file")
    elif file_path.name == "__init__.py":
        parts.append("Package initialization")
    elif file_path.name == "cli.py":
        parts.append("Command-line interface")
    elif file_path.name == "config.py":
        parts.append("Configuration management")
    elif file_path.name == "main.py" or file_path.name == "__main__.py":
        parts.append("Entry point")

    # Describe contents
    if classes:
        if len(classes) == 1:
            parts.append(f"Defines {classes[0]} class")
        elif len(classes) <= 3:
            parts.append(f"Defines: {', '.join(classes)}")
        else:
            parts.append(f"Defines {len(classes)} classes")

    if functions and not classes:
        # Only mention top-level functions if no classes (avoid clutter)
        if len(functions) <= 3:
            parts.append(f"Functions: {', '.join(functions[:3])}")
        else:
            parts.append(f"Provides {len(functions)} utility functions")

    # Mention key dependencies
    important_imports = [
        imp
        for imp in imports
        if any(key in imp for key in ["pydantic", "requests", "rich", "click", "flask", "fastapi"])
    ]
    if important_imports:
        parts.append(f"Uses {', '.join(important_imports[:2])}")

    # Fallback
    if not parts:
        parts.append("Python module")

    return ". ".join(parts) + "."


def analyze_project_files(project_root: Path, files: List[Path]) -> Dict[Path, FileAnalysis]:
    """Analyze multiple Python files in a project.

    Args:
        project_root: Root directory of project (unused but kept for API consistency)
        files: List of Python files to analyze

    Returns:
        Dict mapping file paths to their analysis results

    """
    results = {}

    for file_path in files:
        if file_path.suffix == ".py":
            analysis = analyze_python_file(file_path)
            if analysis:
                results[file_path] = analysis

    return results


def generate_dependency_graph(analyses: Dict[Path, FileAnalysis]) -> Dict[str, List[str]]:
    """Build a simple dependency graph from import analysis.

    Args:
        analyses: Dict of file analyses

    Returns:
        Dict mapping file names to list of imported module names

    """
    graph = {}

    for file_path, analysis in analyses.items():
        graph[str(file_path)] = analysis.imports

    return graph
