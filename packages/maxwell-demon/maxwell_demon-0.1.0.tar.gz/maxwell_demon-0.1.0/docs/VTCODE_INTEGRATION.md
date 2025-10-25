# vtcode Integration Strategy for Maxwell

## Overview

Instead of reimplementing code intelligence features from scratch, Maxwell can leverage **vtcode** for:
- File indexing with hash-based change detection
- Tree-sitter semantic parsing (Rust, Python, JS/TS, Go, Java)
- AST-based code search and refactoring (ast-grep)
- Regex search with context

**Division of Labor:**
- **vtcode**: Code-specific workflows (analysis, refactoring, semantic search)
- **Maxwell**: Document/chat workflows (PDFs, markdown, JSONL, semantic search)

## Integration Options

### Option 1: vtcode-indexer as Subprocess (Recommended)

**Use Case:** Code validation, code search, file change detection

**Implementation:**
```python
# src/maxwell/workflows/code_index.py
from pathlib import Path
import subprocess
import json

class VTCodeIndexer:
    """Wrapper around vtcode-indexer for code file indexing."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.index_dir = workspace_root / ".maxwell" / "vtcode-index"

    def index_workspace(self) -> dict:
        """Index code files using vtcode-indexer."""
        # Call vtcode CLI (if installed)
        result = subprocess.run(
            ["vtcode", "index", str(self.workspace_root)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Fallback to Maxwell's own indexer
            return self._fallback_index()

        # Parse vtcode's index output
        return json.loads(result.stdout)

    def search_code(self, pattern: str) -> list:
        """Search code using vtcode's grep."""
        result = subprocess.run(
            ["vtcode", "grep", pattern, str(self.workspace_root)],
            capture_output=True,
            text=True
        )

        # Parse search results
        return self._parse_search_results(result.stdout)
```

**Benefits:**
- Simple integration (subprocess calls)
- No dependency on Rust ecosystem
- vtcode handles Tree-sitter parsing
- Hash-based change detection (faster re-indexing)

**Drawbacks:**
- Requires vtcode installation (`cargo install vtcode`)
- IPC overhead (subprocess spawning)
- Parsing CLI output

**Best For:** Code validation workflows, project-wide code search

---

### Option 2: Complementary Tools (No Integration)

**Architecture:**
```
┌─────────────────────────────────────────┐
│          User Workflow                  │
└─────────────────────────────────────────┘
           │                  │
           │                  │
           v                  v
┌──────────────────┐  ┌─────────────────┐
│     vtcode       │  │    Maxwell      │
│                  │  │                 │
│ • Code analysis  │  │ • Doc search    │
│ • Refactoring    │  │ • PDF indexing  │
│ • ast-grep       │  │ • Chat search   │
│ • LLM coding     │  │ • Embeddings    │
└──────────────────┘  └─────────────────┘
```

**Use Cases:**
- **vtcode**: Interactive coding sessions, refactoring, code review
- **Maxwell**: Searching documentation, papers, chat logs, semantic search

**No integration needed** - use the right tool for the job!

**Benefits:**
- Each tool stays focused
- No coupling, easier maintenance
- Users choose based on task

**Best For:** Current Maxwell use cases (document search, chat indexing)

---

### Option 3: MCP Server (Future)

**Vision:** Expose vtcode and Maxwell as MCP servers that can call each other

```toml
# vtcode.toml - Configure Maxwell as MCP provider
[[mcp.providers]]
name = "maxwell"
enabled = true
command = "maxwell"
args = ["mcp-server"]
max_concurrent_requests = 4

[mcp.allowlist.providers.maxwell]
tools = ["semantic_search", "index_directory", "extract_pdf"]
```

```toml
# maxwell config - Configure vtcode as MCP provider
[[mcp.providers]]
name = "vtcode"
enabled = true
command = "vtcode"
args = ["mcp-server"]  # (if vtcode exposes MCP server mode)

[mcp.allowlist.providers.vtcode]
tools = ["ast_grep_search", "tree_sitter_parse", "code_analysis"]
```

**Workflow Example:**
1. User runs `maxwell complete-justification`
2. Maxwell needs to analyze code files
3. Maxwell calls vtcode via MCP: `ast_grep_search` to find functions
4. vtcode returns semantic analysis
5. Maxwell uses that to fill justification worksheet

**Benefits:**
- Structured tool exchange (JSON-RPC)
- Dynamic tool discovery
- Loose coupling (can swap implementations)

**Drawbacks:**
- Requires both tools to implement MCP server mode
- More complex setup
- Need MCP infrastructure

**Best For:** Advanced workflows requiring both semantic search AND code intelligence

---

## Recommended Approach for v0.1.0

**Use Option 2: Complementary Tools (No Integration)**

**Rationale:**
1. **Maxwell's core strength**: Document/chat search with embeddings
2. **vtcode's core strength**: Code analysis with Tree-sitter/ast-grep
3. **Minimal overlap**: Maxwell doesn't need code refactoring, vtcode doesn't do PDF extraction
4. **Focus**: Ship Maxwell v0.1.0 focused on semantic search, not code intelligence

**What Maxwell Should Focus On:**
- ✅ Document indexing (PDFs, markdown, chat logs)
- ✅ Semantic search with embeddings
- ✅ Content-addressable storage
- ✅ Hierarchical indexing
- ✅ Validation workflows (using ruff/black/pyright directly)

**What to Defer:**
- ❌ Tree-sitter parsing (use vtcode if needed)
- ❌ AST-based refactoring (vtcode handles this)
- ❌ Code complexity analysis (vtcode + ruff handle this)

---

## Future Integration Path

**Phase 1: v0.1.0** - Ship Maxwell as document search tool
- No vtcode integration
- Focus on semantic search, PDF extraction, chat indexing

**Phase 2: v0.2.0** - Add code search via vtcode subprocess
- Implement `VTCodeIndexer` wrapper (Option 1)
- Use for `maxwell validate` code analysis
- Fallback to native tools if vtcode not installed

**Phase 3: v0.3.0** - MCP integration
- Expose Maxwell as MCP server (search tools)
- Connect to vtcode as MCP client (code tools)
- Enable cross-tool workflows

---

## Lessons from vtcode for Maxwell

### 1. Pluggable Storage Architecture

**vtcode pattern:**
```rust
pub trait IndexStorage: Send + Sync {
    fn init(&self, index_dir: &Path) -> Result<()>;
    fn persist(&self, index_dir: &Path, entry: &FileIndex) -> Result<()>;
}
```

**Apply to Maxwell:**
```python
from abc import ABC, abstractmethod

class EmbeddingStore(ABC):
    @abstractmethod
    def store_embedding(self, content_hash: str, embedding: np.ndarray):
        pass

    @abstractmethod
    def get_embedding(self, content_hash: str) -> np.ndarray | None:
        pass

class SQLiteEmbeddingStore(EmbeddingStore):
    # Current implementation

class QdrantEmbeddingStore(EmbeddingStore):
    # Future: Remote vector DB
```

### 2. Hash-Based Change Detection

**vtcode approach:**
```rust
let hash = calculate_hash(&content);  // DefaultHasher
if cached_hash == hash {
    return Ok(());  // Skip re-indexing
}
```

**Apply to Maxwell:**
- Already using SHA256 for content-addressable storage ✅
- Could add modified time checks for faster skips
- Implement incremental indexing

### 3. Trait-Based Filters

**vtcode pattern:**
```rust
pub trait TraversalFilter: Send + Sync {
    fn should_descend(&self, path: &Path, config: &Config) -> bool;
    fn should_index_file(&self, path: &Path, config: &Config) -> bool;
}
```

**Apply to Maxwell:**
```python
class IndexFilter(ABC):
    @abstractmethod
    def should_index(self, path: Path) -> bool:
        pass

class GlobFilter(IndexFilter):
    def should_index(self, path: Path) -> bool:
        return any(path.match(glob) for glob in self.include_globs)

class GitignoreFilter(IndexFilter):
    def should_index(self, path: Path) -> bool:
        # Use pathspec library
        return not self.gitignore.match_file(path)

class CompositeFilter(IndexFilter):
    def should_index(self, path: Path) -> bool:
        return all(f.should_index(path) for f in self.filters)
```

### 4. Markdown-Backed Storage

**vtcode approach:**
```rust
let markdown = format!(
    "# File Index: {}\n\n\
    - **Path**: {}\n\
    - **Hash**: {}\n\
    - **Modified**: {}\n",
    entry.path, entry.hash, entry.modified
);
fs::write(index_path, markdown)?;
```

**Apply to Maxwell:**
- Already using JSON for hierarchy ✅
- Consider markdown format for `.maxwell/index/` for git-friendliness
- Human-readable diffs in git

---

## Conclusion

**For v0.1.0:** Ship Maxwell as focused document search tool. No vtcode integration needed.

**Future:** Add vtcode subprocess calls for code intelligence if needed (v0.2.0+).

**Long-term:** MCP integration enables cross-tool workflows (v0.3.0+).

**Key Insight:** vtcode and Maxwell are **complementary**, not competing. Use the right tool for the job.
