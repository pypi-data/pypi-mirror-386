# LM Registry Configuration

Maxwell uses a flexible LLM registry system (`lm_registry.json`) to manage multiple language models and embedding services. The registry enables intelligent routing, health checking, and cost-aware scheduling.

## Overview

The registry allows you to declare all your LLMs and embeddings in one place, then Maxwell automatically selects the best one for each task based on:
- **Context size** - Does the prompt fit?
- **Capabilities** - Does it support reasoning/vision/code?
- **Speed** - How fast does it generate tokens?
- **Cost** - How much does it cost per 1K tokens?
- **Health** - Is the service currently reachable?
- **Budget** - Have we hit daily token limits?

## Registry Location

Maxwell searches for the registry in this order:
1. `.maxwell/lm_registry.json` (project-specific)
2. `~/.maxwell/lm_registry.json` (global default)

## Schema

```json
{
  "llms": [...],
  "embeddings": [...],
  "_schema_version": "1.0"
}
```

## LLM Configuration

Each LLM entry defines a language model backend:

```json
{
  "name": "qwen-coder-30b",
  "api_base": "http://100.116.54.128:11434",
  "model": "C:\\dev\\Qwen3-Coder-30B-A3B-Instruct-Q5_K_M.gguf",
  "backend": "llamacpp",
  "capabilities": {
    "max_tokens": 16384,
    "max_context": 32768,
    "speed_tokens_per_sec": 25,
    "reasoning": true,
    "vision": false
  },
  "default_temperature": 0.3,
  "tags": ["reasoning", "high-context", "coding"],
  "cost_per_1k_tokens": 0.0,
  "tier": "free",
  "daily_budget_tokens": null
}
```

### Fields

- **name** (required) - Unique identifier for this LLM
- **api_base** (required) - Base URL of the OpenAI-compatible API (e.g., `http://localhost:8000`)
- **model** (required) - Model name or path to GGUF file
- **backend** (required) - Backend type: `llamacpp | vllm | openai`
- **capabilities** (required) - Model capabilities:
  - `max_tokens` - Maximum tokens in completion
  - `max_context` - Maximum context window size
  - `speed_tokens_per_sec` - Average generation speed
  - `reasoning` - Supports chain-of-thought reasoning
  - `vision` - Supports image inputs
  - `code_specialized` - Specialized for code generation
- **default_temperature** (required) - Default sampling temperature (0.0-1.0)
- **tags** (optional) - List of semantic tags for filtering (e.g., `["reasoning", "fast", "coding"]`)
- **cost_per_1k_tokens** (optional, default: 0.0) - Cost per 1000 tokens (used for scheduling)
- **tier** (optional, default: "standard") - Service tier: `free | standard | premium`
- **daily_budget_tokens** (optional, default: null) - Maximum tokens per day (null = unlimited)

### Supported Backends

#### llama.cpp
Local inference with GGUF models. Supports grammar-constrained generation (GBNF).

```json
{
  "backend": "llamacpp",
  "api_base": "http://localhost:8080",
  "model": "/path/to/model.gguf"
}
```

#### vLLM
High-performance inference server optimized for throughput.

```json
{
  "backend": "vllm",
  "api_base": "http://localhost:8000",
  "model": "Qwen/Qwen3-VL-4B-Instruct"
}
```

#### OpenAI
Cloud-based API (requires API key in environment).

```json
{
  "backend": "openai",
  "api_base": "https://api.openai.com",
  "model": "gpt-4o-2024-05-13"
}
```

## Embedding Configuration

Each embedding entry defines an embedding model:

```json
{
  "name": "qwen-embed-4b",
  "api_base": "http://100.72.90.85:8001",
  "model": "Qwen/Qwen3-Embedding-4B",
  "dimension": 2560,
  "max_context": 4096,
  "specialized_for": ["code", "natural"],
  "tags": ["default", "general-purpose"]
}
```

### Fields

- **name** (required) - Unique identifier
- **api_base** (required) - Base URL of embedding API
- **model** (required) - Model name
- **dimension** (required) - Embedding vector dimension
- **max_context** (required) - Maximum input tokens
- **specialized_for** (optional) - List of specializations (e.g., `["code", "natural", "academic"]`)
- **tags** (optional) - Semantic tags (e.g., `["default", "fast"]`)

## Usage Examples

### Get Default LLM (Fastest)

```python
from maxwell.lm_pool import get_lm

lm = get_lm()
response = lm.generate("Write a function to parse JSON")
```

### Get Specific LLM by Name

```python
lm = get_lm("qwen-coder-30b")
response = lm.generate("Explain how transformers work")
```

### Intelligent Routing (Prompt-Based)

Maxwell automatically selects the best LLM based on prompt size:

```python
# For short interactive queries (prefer speed)
lm = get_lm(prompt="Quick question", time_cost_weight=10.0)

# For long batch processing (prefer cost)
lm = get_lm(prompt=long_document, time_cost_weight=0.1)
```

### Select by Capabilities

```python
# Vision model
lm = get_lm(vision=True)

# Reasoning model with large context
lm = get_lm(reasoning=True, min_context=32000)

# Fast model for code
lm = get_lm(tags=["coding"], min_speed=100)
```

### Get Embedding

```python
from maxwell.lm_pool import get_embedding

embed = get_embedding("default")
vector = embed.embed("Some text to embed")
```

## Health Checking

Maxwell automatically checks service health before selecting an LLM:

- Tries `/health` endpoint first
- Falls back to `/v1/models` (OpenAI-compatible)
- Caches health status for 30 seconds
- Skips unhealthy services in selection

## Budget Tracking

Set `daily_budget_tokens` to limit usage:

```json
{
  "name": "gpt-4o",
  "daily_budget_tokens": 100000,
  "cost_per_1k_tokens": 0.005
}
```

Maxwell tracks usage in `~/.maxwell/llm_usage.json` and automatically skips over-budget LLMs.

## Scheduling Algorithm

When multiple LLMs match requirements, Maxwell scores them:

```python
score = -monetary_cost - (time_cost_weight * time_seconds) + utilization_bonus
```

- **monetary_cost** - Negative cost per token
- **time_seconds** - Estimated generation time
- **time_cost_weight** - How much you value speed (0-10)
- **utilization_bonus** - Prefers ~70% context utilization

Higher score = better fit for this request.

## Example Registry

```json
{
  "llms": [
    {
      "name": "qwen-coder-30b",
      "api_base": "http://100.116.54.128:11434",
      "model": "C:\\dev\\Qwen3-Coder-30B-A3B-Instruct-Q5_K_M.gguf",
      "backend": "llamacpp",
      "capabilities": {
        "max_tokens": 16384,
        "max_context": 32768,
        "speed_tokens_per_sec": 25,
        "reasoning": true,
        "vision": false
      },
      "default_temperature": 0.3,
      "tags": ["reasoning", "high-context", "coding"],
      "cost_per_1k_tokens": 0.0,
      "tier": "free"
    },
    {
      "name": "qwen-vl-4b",
      "api_base": "http://100.127.86.64:8001",
      "model": "Qwen/Qwen3-VL-4B-Instruct",
      "backend": "vllm",
      "capabilities": {
        "max_tokens": 2048,
        "max_context": 4096,
        "speed_tokens_per_sec": 150,
        "reasoning": false,
        "vision": true
      },
      "default_temperature": 0.7,
      "tags": ["vision", "small", "fast"],
      "cost_per_1k_tokens": 0.0,
      "tier": "free"
    }
  ],
  "embeddings": [
    {
      "name": "qwen-embed-4b",
      "api_base": "http://100.72.90.85:8001",
      "model": "Qwen/Qwen3-Embedding-4B",
      "dimension": 2560,
      "max_context": 4096,
      "specialized_for": ["code", "natural"],
      "tags": ["default", "general-purpose"]
    }
  ],
  "_schema_version": "1.0"
}
```

## Tips

1. **Use tags** for semantic filtering (e.g., `["coding", "fast", "vision"]`)
2. **Set realistic speeds** - Measure actual tokens/sec for accurate scheduling
3. **Configure budgets** for paid APIs to avoid surprises
4. **Health checks** run automatically - no manual intervention needed
5. **Local first** - Put free local models before paid APIs for cost savings

## See Also

- `src/maxwell/lm_pool.py` - Implementation
- `maxwell justification` - Example workflow using LLM pool
