# Chat Workflows - Unified ChatGPT & Claude Analysis

Organized workflow module for parsing, indexing, and analyzing both ChatGPT and Claude conversations.

## Structure

```
chat/
├── __init__.py          # Module exports
├── parsers.py           # ChatGPT and Claude conversation parsers
├── indexer.py           # MongoDB indexing for both sources
├── insights.py          # Deep analysis and insights extraction
└── README.md            # This file
```

## Modules

### parsers.py

Unified message parsers for both ChatGPT and Claude conversations.

**ChatGPTParser**: Handles `conversations.json` export format
- Parses nested message mappings
- Walks conversation graph to get chronological order
- Source: `/home/mithranmohanraj/Documents/chatgpt/conversations.json`

**ClaudeParser**: Handles `.jsonl` conversation files
- Parses JSONL format from `~/.claude/projects/`
- Extracts user/assistant messages
- Source: `~/.claude/projects/*.jsonl`

**Message**: Unified dataclass representing a message from either source
```python
@dataclass
class Message:
    message_id: str
    conversation_id: str
    conversation_title: str
    role: str  # user, assistant, system, tool
    text: str
    timestamp: Optional[float]
    message_index: int
    parent_id: Optional[str]
    source: str  # "chatgpt" or "claude"
    token_count: int
    char_count: int
```

### indexer.py

MongoDB indexer for chat messages from both sources.

**ChatIndexer**: Loads messages into MongoDB `chat_analytics` database
- Creates indexes for fast querying
- Handles deduplication
- Generates conversation summaries
- Adds temporal fields for analytics (year, month, day_of_week, hour_of_day)

**Collections**:
- `messages`: Individual messages with full metadata
- `conversations`: Aggregated conversation summaries

**Usage**:
```python
from maxwell.workflows.implementations.chat.indexer import ChatIndexer

indexer = ChatIndexer()
indexer.setup_collections()

# Index ChatGPT
indexer.index_chatgpt(Path("/home/mithranmohanraj/Documents/chatgpt/conversations.json"))

# Index Claude
indexer.index_claude(Path("~/.claude/projects").expanduser())

# Create summaries
indexer.create_conversation_summaries()

# Get stats
stats = indexer.get_stats()
```

**CLI**:
```bash
# Index ChatGPT
python -m maxwell.workflows.implementations.chat.indexer chatgpt /path/to/conversations.json

# Index Claude
python -m maxwell.workflows.implementations.chat.indexer claude ~/.claude/projects

# View stats
python -m maxwell.workflows.implementations.chat.indexer stats
```

### insights.py

Deep analysis workflow for extracting insights from indexed conversations.

**ChatInsightsWorkflow**: Maxwell workflow for analyzing conversations
- Clustering conversations by semantic similarity
- Extracting key topics per cluster
- Generating insights using LLM
- Supports "organic" mode (no predefined topic count)
- Handles both ChatGPT global memory and Claude long conversations

**Features**:
- Embedding-based clustering (HDBSCAN)
- LLM-powered insight generation with GBNF structured output
- Temporal awareness (analyzes recent conversations)
- Source awareness (ChatGPT vs Claude)

**Usage**:
```python
from pathlib import Path
from maxwell.workflows.implementations.chat.insights import ChatInsightsWorkflow

workflow = ChatInsightsWorkflow()
result = workflow.execute(
    Path.cwd(),
    {
        'method': 'deep',
        'days': 7,
        'limit': 200,
        'max_topics': 50,
        'organic': True
    }
)
```

## Data Flow

### Indexing Pipeline

1. **Parse** conversations using `ChatGPTParser` or `ClaudeParser`
2. **Index** messages to MongoDB using `ChatIndexer`
3. **Summarize** conversations (aggregate stats)

### Insights Pipeline

1. **Query** MongoDB for recent conversations
2. **Embed** conversation summaries using Qwen3-4B-Embed
3. **Cluster** conversations using HDBSCAN
4. **Generate** insights per cluster using LLM with GBNF
5. **Aggregate** global themes across all clusters

## Database Schema

### messages Collection

```javascript
{
  message_id: "unique-id",
  conversation_id: "conv-id",
  conversation_title: "Title",
  role: "user" | "assistant" | "system" | "tool",
  text: "Message content",
  timestamp: 1234567890.123,
  message_index: 0,
  parent_id: "parent-msg-id",
  source: "chatgpt" | "claude",
  token_count: 100,
  char_count: 400,

  // Derived temporal fields
  year: 2025,
  month: "2025-10",
  day_of_week: "Monday",
  hour_of_day: 14
}
```

### conversations Collection

```javascript
{
  conversation_id: "conv-id",
  title: "Conversation Title",
  source: "chatgpt" | "claude",
  message_count: 42,
  first_message: 1234567890.123,
  last_message: 1234567999.456,
  roles: ["user", "assistant"],
  total_tokens: 4200,
  total_chars: 16800
}
```

## Current Status

**Indexed Data** (as of 2025-10-21):
- Total conversations: 686
- Total messages: 90,117
- ChatGPT: 548 conversations (80%), 7,374 messages (8.2%)
- Claude: 138 conversations (20%), 82,743 messages (91.8%)

**Database**: MongoDB `chat_analytics` on localhost:27017

## Integration Points

### Backward Compatibility

The old `chat_insights.py` location is maintained as a shim:
```python
# Old import (still works)
from maxwell.workflows.implementations.chat_insights import ChatInsightsWorkflow

# New import (preferred)
from maxwell.workflows.implementations.chat.insights import ChatInsightsWorkflow
```

### Future Work

1. **Merge with Maxwell document indexer**: Currently `extractors.py` is at maxwell root and only handles Claude. Should integrate both parsers.

2. **LSTM-style summarization for ChatGPT**: Treat ChatGPT conversations as one continuous thread with global memory, using backward summarization from cluster entry points.

3. **Unified language model pool**: Merge `embedding_client.py` and `llm_pool.py` into single `language_model_pool.py`.

## Dependencies

- **MongoDB**: For message storage and analytics
- **pymongo**: MongoDB client
- **LLMPool**: For embeddings and LLM inference
- **scikit-learn**: For clustering (HDBSCAN)
- **Maxwell workflows**: Base workflow infrastructure
