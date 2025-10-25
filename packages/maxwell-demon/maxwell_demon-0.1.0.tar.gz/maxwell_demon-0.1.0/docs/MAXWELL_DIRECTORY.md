# The .maxwell Directory

Maxwell uses a `.maxwell/` directory for storing workflow outputs, caches, and logs. There's both a project-local `.maxwell/` and a global `~/.maxwell/` for shared configuration.

## Quick Answer

**Does .maxwell auto-gitignore itself?** Yes! Maxwell creates `.maxwell/.gitignore` containing just `*`, which gitignores the entire directory. This is because `.maxwell/` contains rebuildable caches and logs that shouldn't be committed to git.

## Actual Directory Structure

Here's what Maxwell actually creates:

```
project/
├── .maxwell/                           # Per-project Maxwell data
│   ├── .gitignore                      # Contains: *
│   ├── logs/                           # LLM request/response logs (JSONL)
│   │   ├── justification_20251023_075511.jsonl
│   │   └── justification_20251023_075511.log
│   ├── reports/                        # Workflow-generated reports
│   │   ├── justification_analysis_20251023_075511.md
│   │   └── project_analysis_20251023_075511.xml
│   ├── cache/                          # File summaries cache
│   │   └── file_summaries.json
│   ├── chat_registry_claude-projects.json  # Chat index metadata
│   └── chat_registry_claude-backup.json
└── your-files/

~/.maxwell/                             # Global configuration
├── lm_registry.json                    # LLM configuration (see docs/LM_REGISTRY.md)
├── chat_registry_claude.json           # Global chat index
└── plugins/                            # Global plugins
```

## .gitignore Explanation

`.maxwell/.gitignore` contains just:
```
*
```

This means **everything** in `.maxwell/` is gitignored. Why?
- **logs/** - Large JSONL files with LLM requests, debugging only
- **reports/** - Rebuildable workflow outputs (can be regenerated)
- **cache/** - File summaries that can be regenerated
- **chat_registry_*.json** - Index metadata that can be rebuilt

Maxwell treats `.maxwell/` as **ephemeral local state** - similar to `node_modules/` or `.pytest_cache/`.

## What's in Each Directory

### .maxwell/logs/
**Purpose: LLM debugging logs**

Contains JSONL files with full LLM request/response pairs:
```jsonl
{"timestamp": "...", "model": "qwen-coder-30b", "request": {...}, "response": {...}}
```

- One file per workflow session: `{workflow}_{timestamp}.jsonl`
- Useful for debugging LLM behavior
- Can be disabled with `NO_JSONL_LOGGING=1` env var

**Why gitignored?** Large files, debugging only, may contain sensitive prompts.

### .maxwell/reports/
**Purpose: Workflow output reports**

Contains human-readable reports from workflows:
- **Justification workflow** creates `justification_analysis_*.md` and `project_analysis_*.xml`
- Other workflows may create their own report files

**Why gitignored?** Rebuildable - you can re-run the workflow to regenerate.

### .maxwell/cache/
**Purpose: File metadata cache**

- `file_summaries.json` - Maps file hashes to LLM-generated summaries
- Used to avoid re-summarizing files that haven't changed

**Why gitignored?** Cache that can be regenerated (though wastes API calls).

### .maxwell/chat_registry_*.json
**Purpose: Chat index metadata**

Metadata for indexed Claude chat conversations:
- `chat_registry_claude-projects.json` - Active projects index
- `chat_registry_claude-backup.json` - Backup index

**Why gitignored?** Index metadata that can be rebuilt by re-indexing.

## Global Configuration (~/.maxwell/)

### lm_registry.json
**Purpose: LLM configuration**

Defines available LLMs and embeddings for Maxwell workflows. See [docs/LM_REGISTRY.md](LM_REGISTRY.md) for details.

Example:
```json
{
  "llms": [
    {
      "name": "qwen-coder-30b",
      "api_base": "http://localhost:8080",
      "model": "qwen-coder.gguf",
      "backend": "llamacpp",
      "capabilities": {"max_context": 32768, "reasoning": true}
    }
  ],
  "embeddings": [
    {
      "name": "qwen-embed-4b",
      "api_base": "http://localhost:8001",
      "model": "Qwen/Qwen3-Embedding-4B",
      "dimension": 2560
    }
  ]
}
```

### chat_registry_claude.json
**Purpose: Global chat index**

Global index of all indexed Claude chat conversations.

### plugins/
**Purpose: Global workflow plugins**

User-installed plugins available in all projects:
- Python plugins: `*.py` files with BaseWorkflow classes
- Script plugins: Executable files with `*.json` metadata

See [plugins/README.md](../plugins/README.md) for plugin development guide.

## Common Workflows and Their Output

### maxwell snapshot
```bash
maxwell snapshot --output snapshot.md
```
**Creates:** `snapshot.md` in current directory (NOT in `.maxwell/`)

### maxwell justification
```bash
maxwell justification
```
**Creates:**
- `.maxwell/reports/justification_analysis_{timestamp}.md` - Human-readable report
- `.maxwell/reports/project_analysis_{timestamp}.xml` - Structured XML
- `.maxwell/logs/justification_{timestamp}.jsonl` - LLM request logs

### maxwell chat-semantic-search
```bash
maxwell chat-semantic-search --query "PDF parsing"
```
**Uses:**
- `.maxwell/chat_registry_claude-projects.json` - Index metadata
- `~/.maxwell/lm_registry.json` - Embedding configuration

### maxwell validate
```bash
maxwell validate --fix
```
**Creates:**
- `.maxwell/reports/validation_{timestamp}.md` - Validation report (if workflow creates it)

## Environment Variables

### NO_JSONL_LOGGING
Disable LLM logging to save disk space:
```bash
NO_JSONL_LOGGING=1 maxwell justification
```

### LLM_SESSION_ID
Override session ID for log files:
```bash
LLM_SESSION_ID=my-analysis maxwell justification
```
Creates: `.maxwell/logs/my-analysis.jsonl`

## Should You Commit .maxwell/?

**No.** The `.maxwell/.gitignore` automatically prevents this by gitignoring everything (`*`).

**Why?**
- It's rebuildable - re-run workflows to regenerate reports
- Contains local caches specific to your machine
- May include sensitive LLM prompts in logs
- Similar to `node_modules/` or `.pytest_cache/` - local state only

**Exception:** If you want to share workflow reports with your team, copy them out of `.maxwell/reports/` to a different location (like `docs/analysis/`) before committing.

## Cleanup

### Safe to Delete
Everything in `.maxwell/` can be safely deleted:
```bash
rm -rf .maxwell/
```

Maxwell will recreate it on next use. Note:
- **Logs** - Will be lost (debugging info only)
- **Reports** - Can regenerate by re-running workflows
- **Cache** - Will be rebuilt (but may waste API calls for summaries)

### Avoid Deleting
- `~/.maxwell/lm_registry.json` - Your LLM configuration (backup before deleting)
- `~/.maxwell/plugins/` - Your custom plugins

## Troubleshooting

### Large .maxwell/logs/ directory
Logs can grow large over time:
```bash
du -sh .maxwell/logs
rm -rf .maxwell/logs/*  # Safe to delete
```

### Missing lm_registry.json
```bash
mkdir -p ~/.maxwell
# Create lm_registry.json - see docs/LM_REGISTRY.md for examples
```

### .maxwell not gitignored
If you see `.maxwell/` in git status:
```bash
# Check if .gitignore exists and contains *
cat .maxwell/.gitignore

# If missing, create it:
echo '*' > .maxwell/.gitignore
```

Maxwell should create this automatically, but you can create it manually if needed.

## Best Practices

1. **Don't commit** `.maxwell/` - It's automatically gitignored
2. **Clean logs periodically** - They can grow large
3. **Backup lm_registry.json** - It's your LLM configuration
4. **Share reports externally** - Copy from `.maxwell/reports/` to `docs/` if team needs them
5. **Use NO_JSONL_LOGGING=1** - If you don't need debugging logs

## See Also

- `docs/LM_REGISTRY.md` - LLM configuration guide
- `plugins/README.md` - Plugin development guide
- `src/maxwell/storage.py` - Storage implementation (init_maxwell_dir function)
