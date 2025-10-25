# Maxwell

**Semantic workflow automation for codebases and documents** - A CLI-first tool for content analysis, search, and code quality.

Maxwell provides a plugin-like workflow system where each workflow is a self-contained analyzer, generator, or searcher. All workflows use the same CLI pattern: `maxwell <workflow-id> [options]`.

## Features

- **Workflow-based architecture** - Extensible plugin system for analysis tasks
- **Semantic search** - Find documents and conversations by meaning using embeddings
- **Multi-format extraction** - PDFs (marker-pdf), Office docs (markitdown), Claude chat logs (.jsonl)
- **Code analysis** - Justification analysis, validation, and quality checks
- **Codebase snapshots** - Generate markdown documentation of entire codebases
- **Content-addressable storage** - Files identified by SHA256 hash, global deduplication
- **Distributed architecture** - Each directory has `.maxwell/` (like `.git/`)

## Installation

```bash
pip install -e .
```

## Quick Start

### List Available Workflows

```bash
maxwell list-workflows
```

### Generate a Codebase Snapshot

Create a markdown file with filesystem tree and file contents:

```bash
maxwell snapshot --output SNAPSHOT.md
```

### Search Chat Conversations

Find discussions using semantic search:

```bash
maxwell chat-semantic-search --query "PDF parsing marker-pdf" --top-k 5
```

Or use BM25 keyword search:

```bash
maxwell chat-bm25-search --query "marker-pdf import error" --limit 10
```

### Analyze Code Architecture

Run LLM-powered justification analysis to find misplaced/redundant files:

```bash
maxwell justification
```

### Validate Code Quality

Run validators to check code quality and style:

```bash
maxwell validate --fix
```

### Utilities

Get timestamps and session IDs for scripting:

```bash
maxwell get-time --format iso
maxwell get-session
```

## Available Workflows

Run `maxwell list-workflows` for the full list. Key workflows:

- **snapshot** - Generate codebase documentation (markdown with tree + contents)
- **justification** - LLM-powered code architecture analysis
- **chat-semantic-search** - Semantic search over indexed chat logs
- **chat-bm25-search** - Keyword search over chat conversations
- **chat_upsert** - Index chat files into MongoDB with deduplication
- **validate** - Code quality validation with auto-fix
- **tag_refactor** - Format semantic HTML tags in markdown files
- **get-time** / **get-session** - Utility workflows for timestamps and session IDs

## Configuration

Add to `pyproject.toml`:

```toml
[tool.maxwell]
include_globs = [
    "*.md", "**/*.md",
    "*.pdf", "**/*.pdf",
    "**/.claude/projects/*.jsonl"    # Include chat logs
]
exclude_globs = [
    ".maxwell/**",
    ".git/**",
    "__pycache__/**",
    "*.pyc"
]

# Validation rules (optional)
[tool.maxwell.validation]
rules = { EMOJI-USAGE = "BLOCK", DICT-GET-FALLBACK = "WARN" }
```

## Architecture

```
project/
├── .maxwell/                      # Like .git/, per-directory
│   ├── data/                      # Workflow-specific data (committed to git)
│   ├── indexes/                   # SQLite indexes (gitignored, rebuildable)
│   ├── extracted/                 # Cached extractions (gitignored)
│   └── .gitignore                 # Auto-created
└── your-files/

~/.maxwell/                        # Global cache
└── cache.db                       # Shared embedding cache (deduplication)
```

## What Gets Indexed

Maxwell can work with:
- **Markdown files** (`.md`)
- **PDFs** (`.pdf`) - reuses existing parsed versions when available
- **Claude chat logs** (`.jsonl` in `.claude/projects/`)
- **Office documents** (`.docx`, `.pptx`, `.xlsx`)
- **Python code** (`.py`) - semantic code analysis

## Extending Maxwell

### Plugin System

Maxwell supports external plugins without modifying core code. Plugins are loaded from:
- `~/.maxwell/plugins/` (global plugins)
- `<project>/.maxwell/plugins/` (project-specific plugins)

**Two plugin types:**

1. **Python plugins**: `.py` files with `BaseWorkflow` subclasses
2. **Script plugins**: Executable scripts with `.json` metadata

Example script plugin:

```bash
#!/usr/bin/env bash
# ~/.maxwell/plugins/hello
echo "Hello from Maxwell plugin!"
```

```json
{
  "workflow_id": "hello",
  "name": "Hello Plugin",
  "description": "Simple hello world plugin",
  "category": "utility"
}
```

See [plugins/README.md](./plugins/README.md) for detailed plugin development guide.

### Core Workflow Development

To add workflows to Maxwell core:

1. Create a Python file in `src/maxwell/workflows/`
2. Define a `BaseWorkflow` subclass with `@register_workflow` decorator
3. Implement `execute()`, `get_cli_parameters()`, and schema classes
4. Import your workflow in `src/maxwell/workflows/__init__.py`

Example:

```python
from maxwell.workflows.base import BaseWorkflow
from maxwell.registry import register_workflow

@register_workflow
class MyWorkflow(BaseWorkflow):
    workflow_id = "my-workflow"
    name = "My Custom Workflow"
    description = "Does something cool"

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        # Your logic here
        pass
```

## Development

See [AGENTS.instructions.md](./AGENTS.instructions.md) for development guidelines.

### Testing

```bash
# Run formatters and linters
isort src/
black src/
ruff check --fix src/
pyright src/
```

## Documentation

- [Development Instructions](./AGENTS.instructions.md)
- [Claude Code Config](./.claude/settings.json)
- [MCP Documentation](./docs/README_MCP.md)
- [Schema Migration Guide](./docs/SCHEMA_MIGRATION.md)

## License

See LICENSE file.
