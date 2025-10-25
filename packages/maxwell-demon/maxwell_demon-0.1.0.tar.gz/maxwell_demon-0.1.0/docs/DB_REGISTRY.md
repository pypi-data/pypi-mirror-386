# Database Registry Configuration

Maxwell uses `db_registry.json` to configure database connections for chat analytics and file indexing. This keeps database credentials and endpoints separate from code, similar to `lm_registry.json` for LLMs.

## Registry Location

Maxwell searches for the registry in this order:
1. `.maxwell/db_registry.json` (project-specific)
2. `~/.maxwell/db_registry.json` (global default)

## Schema

```json
{
  "qdrant": {
    "host": "localhost",
    "port": 6333,
    "api_key": null,
    "prefix": "maxwell"
  },
  "mongodb": {
    "uri": "mongodb://localhost:27017",
    "database": "maxwell",
    "prefix": "maxwell"
  },
  "_schema_version": "1.0"
}
```

## Configuration Fields

### Qdrant (Vector Database)
- **host** - Qdrant server hostname (default: `"localhost"`)
- **port** - Qdrant server port (default: `6333`)
- **api_key** - Optional API key for Qdrant Cloud
- **prefix** - Collection name prefix (default: `"maxwell"`)
  - Workflows create collections as: `{prefix}_{workflow}_{resource}`
  - Example: `maxwell_chat_messages`, `maxwell_search_chunks`

### MongoDB (Document Database)
- **uri** - MongoDB connection URI (default: `"mongodb://localhost:27017"`)
- **database** - Database name (default: `"maxwell"`)
- **prefix** - Collection name prefix (default: `"maxwell"`)
  - Workflows create collections as: `{prefix}_{workflow}_{resource}`
  - Example: `maxwell_chat_metadata`, `maxwell_validate_results`

## Namespacing Strategy

Maxwell treats databases as **shared filesystems** where we are **guests**. To avoid collisions:

1. **Each workflow gets its own namespace**: `{prefix}_{workflow}_*`
2. **Workflows never write to other workflows' collections**
3. **Users can share databases** by setting the same prefix
4. **Multi-tenant safe** - different prefixes = different Maxwell instances

### Collection Naming Convention

```
{prefix}_{workflow}_{resource}
```

Examples:
- `maxwell_chat_messages` - Chat workflow, message data
- `maxwell_chat_embeddings` - Chat workflow, vector embeddings
- `maxwell_search_chunks` - Search workflow, document chunks
- `maxwell_validate_cache` - Validation workflow, cached results
- `myteam_chat_messages` - Custom prefix for team isolation

## Example Configurations

### Local Development
```json
{
  "qdrant": {
    "host": "localhost",
    "port": 6333,
    "prefix": "maxwell_dev"
  },
  "mongodb": {
    "uri": "mongodb://localhost:27017",
    "database": "maxwell_dev",
    "prefix": "maxwell_dev"
  },
  "_schema_version": "1.0"
}
```

### Production (Qdrant Cloud)
```json
{
  "qdrant": {
    "host": "xyz-example.aws.cloud.qdrant.io",
    "port": 6333,
    "api_key": "your-api-key-here",
    "prefix": "maxwell_prod"
  },
  "mongodb": {
    "uri": "mongodb+srv://user:pass@cluster.mongodb.net/",
    "database": "maxwell_prod",
    "prefix": "maxwell_prod"
  },
  "_schema_version": "1.0"
}
```

### Internal Network (Tailscale)
```json
{
  "qdrant": {
    "host": "100.127.86.64",
    "port": 6333,
    "prefix": "maxwell"
  },
  "mongodb": {
    "uri": "mongodb://100.116.54.128:27017",
    "database": "maxwell",
    "prefix": "maxwell"
  },
  "_schema_version": "1.0"
}
```

### Team Shared Database (Multi-tenant)
```json
{
  "qdrant": {
    "host": "shared-qdrant.company.com",
    "port": 6333,
    "api_key": "${QDRANT_API_KEY}",
    "prefix": "team_dataeng"
  },
  "mongodb": {
    "uri": "${MONGODB_URI}",
    "database": "company_maxwell",
    "prefix": "team_dataeng"
  },
  "_schema_version": "1.0"
}
```

## Usage in Code

```python
from maxwell.config import load_db_registry

# Load database configuration
db_config = load_db_registry()

# Access Qdrant settings
qdrant_host = db_config["qdrant"]["host"]
qdrant_port = db_config["qdrant"]["port"]
qdrant_prefix = db_config["qdrant"].get("prefix", "maxwell")

# Access MongoDB settings
mongo_uri = db_config["mongodb"]["uri"]
mongo_db = db_config["mongodb"]["database"]
mongo_prefix = db_config["mongodb"].get("prefix", "maxwell")

# Construct workflow-specific collection names
workflow_name = "chat"  # or "search", "validate", etc.
qdrant_collection = f"{qdrant_prefix}_{workflow_name}_embeddings"
mongo_collection = f"{mongo_prefix}_{workflow_name}_metadata"

# Example: Chat workflow creates collections like:
# - maxwell_chat_messages (Qdrant)
# - maxwell_chat_metadata (MongoDB)

# Example: Search workflow creates collections like:
# - maxwell_search_chunks (Qdrant)
# - maxwell_search_index (MongoDB)
```

### Helper Function for Collection Names

```python
def get_collection_name(prefix: str, workflow: str, resource: str) -> str:
    """Generate namespaced collection name for workflow.

    Args:
        prefix: Collection prefix from db_registry.json
        workflow: Workflow name (e.g., "chat", "search", "validate")
        resource: Resource type (e.g., "messages", "embeddings", "results")

    Returns:
        Fully qualified collection name: {prefix}_{workflow}_{resource}

    Examples:
        >>> get_collection_name("maxwell", "chat", "messages")
        'maxwell_chat_messages'
        >>> get_collection_name("team_dataeng", "validate", "cache")
        'team_dataeng_validate_cache'
    """
    return f"{prefix}_{workflow}_{resource}"
```

## Security Best Practices

1. **Never commit credentials** - Add `db_registry.json` to `.gitignore` if it contains credentials
2. **Use environment variables** - For production, use env vars:
   ```json
   {
     "mongodb": {
       "uri": "${MONGODB_URI}"
     }
   }
   ```
3. **Separate dev/prod configs** - Use `.maxwell/db_registry.json` for project-specific overrides
4. **Read-only access** - Use read-only MongoDB users for analytics workflows

## See Also

- `docs/LM_REGISTRY.md` - LLM configuration guide
- `docs/MAXWELL_DIRECTORY.md` - Directory structure guide
- `src/maxwell/config.py` - Configuration loading implementation
