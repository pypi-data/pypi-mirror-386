# Maxwell Reusable Components (Low-Entropy Architecture)

## Existing Components That Should Be Reused

### 1. File Discovery (`src/maxwell/discovery.py`)
**What it does:**
- Glob pattern matching (including recursive `**`)
- Exclude pattern support with directory pruning
- VCS directory handling (.git, .hg, .svn)
- Respects pyproject.toml configuration

**Currently duplicated in:**
- `justification.py`: `_discover_files()` method
- Should use: `discover_files()` from discovery module

**Benefits of reuse:**
- Battle-tested glob handling
- Consistent exclusion logic across workflows
- Single source of truth for file discovery

---

### 2. Content-Addressable Storage (`src/maxwell/storage.py`)
**What it does:**
- SHA256 content hashing (`ContentHasher`)
- SQLite-based embedding cache (`EmbeddingCache`)
- Distributed maps for chunk tracking (`LocalMap`)
- `.maxwell/` directory initialization

**Currently duplicated in:**
- `justification.py`: `_get_file_hash()`, `_load_cache()`, `_save_cache()`
- Should use: `ContentHasher`, `EmbeddingCache` from storage module

**Benefits of reuse:**
- Consistent hashing across workflows
- Shared cache for deduplication
- Unified storage architecture

---

### 3. Validation Engine (`src/maxwell/workflows/validate/`)
**What it does:**
- Plugin system for custom validators
- Runs validators on discovered files
- Returns structured `Finding` objects
- Severity levels (BLOCK, WARN, INFO)

**Currently duplicated in:**
- `justification.py`: Custom validate logic mixed with ruff/pyright
- Should compose: Call validate workflow, then add ruff/pyright on top

**Benefits of reuse:**
- Consistent validation interface
- Extensible via plugins
- Proper separation of concerns

---

### 4. AST Analysis (`src/maxwell/workflows/ast_analysis.py`)
**What it does:**
- libcst-based Python AST parsing
- Extracts classes, functions, imports, docstrings
- Detects test files and complexity hints
- Auto-generates compact file summaries

**Already being used:** ✓ (newly created, integrated in justification)

**Benefits:**
- Compact representation (90x compression)
- Structured context for LLM
- Fast (no LLM calls for Python files)

---

## Justification Refactoring Plan

### Current State (1400 lines, high entropy)
```
justification.py:
├── File discovery (duplicates discovery.py)
├── Caching (duplicates storage.py)
├── XML context building
├── LLM orchestration
├── Quality checks (ruff, pyright)
├── Worksheet generation
└── Everything mixed together
```

### Target State (low entropy, composable)
```
justification/
├── __init__.py              # Orchestrator (COMPOSE ONLY)
├── context_builder.py       # XML/structured context
├── quality_runner.py        # Compose validate + ruff + pyright
└── worksheet.py             # Output formatting

Reuses:
├── discovery.discover_files()           # File discovery
├── storage.ContentHasher()              # Hashing
├── storage.EmbeddingCache()             # Caching
├── ast_analysis.analyze_project_files() # AST summaries
└── validate.run_validation()            # Custom validators
```

### Benefits of Low-Entropy Architecture
1. **No duplication** - Each component has ONE implementation
2. **Easy testing** - Test small, focused modules
3. **Consistent behavior** - File discovery works same everywhere
4. **Faster development** - Compose instead of rewrite
5. **Better maintenance** - Bug fix in one place helps all workflows

---

## Next Steps

1. ✓ Document existing components
2. [ ] Create justification submodule structure
3. [ ] Extract unique logic (context building, LLM orchestration)
4. [ ] Replace duplicated code with imports from shared modules
5. [ ] Test that justification still works
6. [ ] Document composition patterns for future workflows

---

## Maxwell's Demon Philosophy

> "The demon sorts molecules, reducing entropy. Maxwell sorts code, reducing duplication."

**Low-entropy code means:**
- Each concept has ONE implementation
- Workflows COMPOSE existing pieces
- New workflows search for existing implementations FIRST
- Living up to our name: reducing chaos, increasing order
