# Justification Workflow - Modular Architecture

## Module Responsibilities (SOLID)

### 1. `file_analyzer.py`
**Single Responsibility:** Discover and analyze files

**What it does:**
- Discover files (reuses `maxwell.discovery`)
- Generate AST summaries for Python files
- Generate LLM summaries for non-Python files
- Cache summaries by content hash

**Outputs:**
```python
@dataclass
class FileAnalysisResult:
    file_path: Path
    summary: str        # AST or LLM-generated
    file_hash: str      # SHA256
    is_python: bool
    ast_analysis: Optional[FileAnalysis]  # If Python
```

---

### 2. `context_builder.py`
**Single Responsibility:** Build structured context for LLM

**What it does:**
- Take file analysis results
- Build XML tree structure
- Chunk context to fit in LLM window (30K tokens)
- Include project rules from AGENTS.instructions.md

**Outputs:**
```python
@dataclass
class StructuredContext:
    xml_chunks: List[str]  # XML chunks that fit in context
    file_count: int
    total_tokens: int
```

---

### 3. `llm_analyzer.py`
**Single Responsibility:** LLM-based architecture analysis

**What it does:**
- Take structured context chunks
- Analyze for misplaced/useless/redundant files
- Synthesize chunk analyses
- Extract structured issues

**Outputs:**
```python
@dataclass
class ArchitecturalIssue:
    title: str
    description: str
    category: str  # misplaced, useless, redundant, etc.
    priority: str  # HIGH, MEDIUM, LOW
    affected_files: List[str]
```

---

### 4. `quality_checks.py`
**Single Responsibility:** Run code quality tools

**What it does:**
- Run maxwell validate (custom validators)
- Run ruff (linting)
- Run pyright (type checking)
- Normalize findings to common format

**Outputs:**
```python
@dataclass
class QualityFinding:
    source: str  # validate, ruff, pyright
    rule_id: str
    severity: str  # BLOCK, WARN, INFO
    file_path: str
    line: int
    message: str
    suggestion: Optional[str]
```

---

### 5. `worksheet_generator.py`
**Single Responsibility:** Generate final markdown worksheet

**What it does:**
- Take architectural issues + quality findings
- Generate markdown worksheet with:
  - Summary statistics
  - Architectural issues section
  - Quality findings (grouped by severity)
  - File justification worksheet (with AST suggestions)
  - Issue resolution worksheet
- Include instructions for completion

**Outputs:**
- Markdown string ready to write to file

---

### 6. `__init__.py` (Orchestrator)
**Single Responsibility:** Compose all steps into workflow

**What it does:**
```python
class JustificationEngine(BaseWorkflow):
    def execute(self, project_root: Path, context: dict) -> WorkflowResult:
        # Step 1: Analyze files
        file_results = FileAnalyzer(self.fast_llm).analyze(project_root)

        # Step 2: Build context
        context = ContextBuilder().build(file_results, project_root)

        # Step 3: LLM analysis
        issues = LLMAnalyzer(self.orchestrator_llm).analyze(context)

        # Step 4: Quality checks
        findings = QualityChecker().check(project_root, file_results.files)

        # Step 5: Generate worksheet
        worksheet = WorksheetGenerator().generate(
            issues, findings, file_results, project_root
        )

        # Write worksheet
        output_path = project_root / ".maxwell" / "justification_worksheet.md"
        output_path.write_text(worksheet)

        return WorkflowResult(...)
```

---

## Benefits of This Architecture

1. **Easy to improve individual steps** - User can guide improvements per module
2. **Easy to test** - Each module has clear inputs/outputs
3. **Easy to swap** - Can replace LLM analyzer with different strategy
4. **Easy to understand** - Each file is <300 lines, single purpose
5. **Reuses existing code** - FileAnalyzer uses discovery.py, storage.py
6. **Low entropy** - Clear boundaries, no duplication

---

## Current Status

- [ ] file_analyzer.py
- [ ] context_builder.py
- [ ] llm_analyzer.py
- [ ] quality_checks.py
- [ ] worksheet_generator.py
- [ ] __init__.py (orchestrator)
- [ ] Move old justification.py to justification_legacy.py
- [ ] Test new modular version
