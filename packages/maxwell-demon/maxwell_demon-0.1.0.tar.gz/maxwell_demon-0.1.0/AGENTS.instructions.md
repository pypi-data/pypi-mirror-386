# Maxwell Development Instructions

## Module Organization & Shared Code

**CRITICAL PRINCIPLE**: When modules at the same level share code (imports, utilities, types, or circular dependencies):

1. **Create a NEW submodule** (directory)
2. **Move BOTH modules** into that submodule
3. **Create a THIRD module** in the submodule for shared code/types
4. **Add `__init__.py`** to export public API
5. Both modules now import from the shared third module

**Examples:**

```
# BAD - Circular imports at same level
src/maxwell/
  module_a.py  # imports from module_b
  module_b.py  # imports from module_a  ❌

# BAD - Shared utilities at same level
src/maxwell/
  feature_a.py  # imports from utils.py
  feature_b.py  # imports from utils.py
  utils.py      # shared helpers  ❌

# GOOD - New submodule with shared code
src/maxwell/feature/          # NEW submodule
  __init__.py                 # NEW - exports public API
  types.py                    # NEW - shared types/utilities
  feature_a.py                # MOVED here, imports from .types
  feature_b.py                # MOVED here, imports from .types  ✅
```

**Key Steps:**
- Don't just add a third file at the same level - **create a submodule**
- **Move all related modules** into the submodule
- Shared code/utilities go in a dedicated module **inside** the submodule
- The `__init__.py` exposes what's needed externally

**Applies to:**
- ✅ Circular imports (module A ↔ module B)
- ✅ Shared utilities (multiple modules → shared utils)
- ✅ Shared types/base classes
- ✅ Any tightly coupled code

**Rationale**:
- Keeps related/coupled code together in one namespace
- Prevents circular dependencies
- Makes shared code ownership clear (part of the feature, not global)
- Reduces drift between tightly coupled modules
- No orphaned `utils.py` files at top level

**Real Example**: `BaseWorkflow` and workflow implementations:
- All in `workflows/` submodule
- Shared base classes in `workflows/base.py`
- Each workflow file imports from `workflows.base`
- No circular dependencies

## File Organization Rules

### Forbidden
- **NO `scripts/` directory** - Scripts go in project root or become proper modules
- **NO `utils/` directory** - Use properly named modules (`io/`, `fs/`, etc.)
- **NO one-off scripts** - Delete after use or integrate as modules

### Project Structure
```
maxwell/
├── src/maxwell/          # All Python source
├── tests/                # Tests
├── docs/                 # Documentation
├── .maxwell-*/           # Generated artifacts (gitignored)
├── pyproject.toml        # Project metadata
├── README.md             # Single entry doc
├── CLAUDE.md             # User instructions
└── AGENTS.instructions.md # This file
```

### Root Directory
**Only contains:**
- Metadata: `pyproject.toml`, `setup.py`, `LICENSE`
- Docs: `README.md`, `*.instructions.md`
- Config: `.gitignore`, `.env.example`
- Entry points: `__init__.py`, `__main__.py`, `conftest.py`
- Tool outputs: `coverage.xml`, `.coverage`

**Runtime resources** (ASCII art, templates) → `src/maxwell/` (for `importlib.resources`)

## Linting Pipeline

**Run in this exact order:**

```bash
isort src/ tests/              # 1. Sort imports
black src/ tests/              # 2. Format code
ruff check --fix src/ tests/   # 3. Lint
pyright src/                   # 4. Type check
```

**Why this order**: black reformats isort's multi-line imports, so black must run after isort.

## No Backward Compatibility

**CRITICAL PRINCIPLE**: Maxwell is pre-1.0 and under active development. **NO backward compatibility layers.**

- **NO deprecated functions/aliases** - Delete old code immediately
- **NO `@deprecated` decorators** - Remove, don't warn
- **NO legacy config support** - Migrate to new patterns directly
- **NO compatibility shims** - Clean breaks only

**When refactoring:**
1. User and assistant agree on new pattern
2. Delete old implementation entirely
3. Update all call sites immediately
4. No transition period, no warnings

**Examples:**
```python
# BAD - Backward compatibility alias
def get_llm():  # new
    ...

def get_language_model():  # deprecated alias ❌
    return get_llm()

# GOOD - Clean migration
def get_lm():  # new name agreed upon
    ...
# Old get_llm() deleted, all call sites updated ✅
```

**Rationale:**
- We're not at a stage where users depend on stability
- Backward compatibility adds complexity and confusion
- Clean breaks force consistency
- Easier to maintain and understand
- No accumulation of technical debt

## Type Safety

### Workflow Schemas
Each workflow defines typed input/output schemas **in the same file**:

```python
# my_workflow.py
from dataclasses import dataclass
from maxwell.workflows.base import BaseWorkflow, WorkflowInputs, WorkflowOutputs

@dataclass(frozen=True)
class MyInputs(WorkflowInputs):
    query: str
    limit: int = 10

@dataclass(frozen=True)
class MyOutputs(WorkflowOutputs):
    results: List[str]
    count: int

class MyWorkflow(BaseWorkflow):
    InputSchema = MyInputs
    OutputSchema = MyOutputs

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        inputs: MyInputs = self.parse_inputs(context)  # Type-safe!
        # ... work ...
        outputs = MyOutputs(results=results, count=len(results))
        return self.create_result(outputs)
```

**See** `SCHEMA_MIGRATION.md` for details.

### Type Definitions
- **Use `FrozenSet[T]`** for immutable collections (contracts, constants)
- **Use `dataclasses`** over dicts - NO `Dict[str, Any]`
- **Type annotate everything** - enable full pyright checking

## Development Workflow

1. Make changes
2. Run linting pipeline (isort → black → ruff → pyright)
3. Run tests: `tox -e py311`
4. If adding workflows: register with `@register_workflow` decorator

## Justification Workflow

**Resource-intensive** (8-10 min for 120 files):
- Analyzes file placement and architecture
- **Output is LLM-generated** - always review critically
- Can misunderstand runtime requirements

```bash
# Run in background
nohup python -c "..." > /tmp/justification.log 2>&1 &
tail -f .maxwell-legacy/logs/justification_*.log
```

## Workflow System

### Auto-Registration
Workflows in `src/maxwell/workflows/` automatically:
- Register in workflow registry (`@register_workflow`)
- Available via CLI: `maxwell workflow-id --param value`
- Accessible via Python API
- Exposed as MCP tools

### CLI Usage
```bash
maxwell list-workflows                    # List all workflows
maxwell tag_refactor --dry-run            # Run workflow
maxwell chat-search --query "embedding"   # Search workflows
```
---

**Last updated**: 2025-10-23
