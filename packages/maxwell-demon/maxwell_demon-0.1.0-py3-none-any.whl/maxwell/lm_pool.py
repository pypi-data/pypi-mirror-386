"""LLM and Embedding Pool Manager.

Flexible resource registry that allows users to declare all their LLMs and embeddings,
then intelligently selects the best one for each task based on capabilities.

Usage:
    pool = LLMPool.from_registry()

    # Select by name
    llm = pool.get_lm("qwen-coder-30b")

    # Select by capability
    fast_llm = pool.select_llm(min_speed=50, reasoning=True)
    vision_llm = pool.select_llm(vision=True)

    # Get default embedding
    embed = pool.get_embedding("default")
"""

__all__ = ["LLMPool", "LLMClient", "LLMSpec", "get_lm", "get_embedding"]

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Module-level session ID cache (one per process/CLI execution)
_SESSION_ID_CACHE = None


def _get_or_create_session_id():
    """Get or create a session ID that persists for the entire CLI execution."""
    global _SESSION_ID_CACHE

    if _SESSION_ID_CACHE is not None:
        return _SESSION_ID_CACHE

    # Try environment variable first
    session_id = os.getenv("LLM_SESSION_ID")
    if session_id:
        _SESSION_ID_CACHE = session_id
        return session_id

    # Generate from calling script + timestamp (once per execution)
    import sys

    calling_script = "unknown"
    if len(sys.argv) > 0:
        script_path = Path(sys.argv[0])
        calling_script = script_path.stem

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    _SESSION_ID_CACHE = f"{calling_script}_{timestamp}"

    return _SESSION_ID_CACHE


class LLMSpec(BaseModel):
    """Specification for an LLM (OpenAI-compatible client)."""

    name: str
    api_base: str = Field(..., description="Base URL (e.g., http://host:port)")
    model: str
    backend: str  # vllm | llamacpp | openai
    capabilities: Dict[str, Any]
    default_temperature: float
    tags: List[str] = Field(default_factory=list)

    # Cost and scheduling metadata
    cost_per_1k_tokens: float = Field(default=0.0, description="Cost per 1K tokens (0 = free)")
    tier: str = Field(default="standard", description="Service tier: free | standard | premium")
    daily_budget_tokens: Optional[int] = Field(
        default=None, description="Max tokens/day (None = unlimited)"
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMSpec":
        """Create from dictionary with Pydantic validation."""
        return cls(**data)  # Pydantic handles validation automatically

    def matches(
        self,
        min_speed: Optional[float] = None,
        min_context: Optional[int] = None,
        reasoning: Optional[bool] = None,
        vision: Optional[bool] = None,
        code_specialized: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Check if this LLM matches the given requirements."""
        caps = self.capabilities

        if min_speed is not None and caps.get("speed_tokens_per_sec", 0) < min_speed:
            return False

        if min_context is not None and caps.get("max_context", 0) < min_context:
            return False

        if reasoning is not None and caps.get("reasoning", False) != reasoning:
            return False

        if vision is not None and caps.get("vision", False) != vision:
            return False

        if code_specialized is not None and caps.get("code_specialized", False) != code_specialized:
            return False

        if tags is not None:
            if not all(tag in self.tags for tag in tags):
                return False

        return True


class EmbeddingSpec(BaseModel):
    """Specification for an embedding model (OpenAI-compatible client)."""

    name: str
    api_base: str = Field(..., description="Base URL (e.g., http://host:port)")
    model: str
    dimension: int
    max_context: int = Field(..., description="Maximum context length in tokens")
    specialized_for: List[str]
    tags: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingSpec":
        """Create from dictionary with Pydantic validation."""
        return cls(**data)  # Pydantic handles validation automatically

    def embed(self, text: str) -> List[float]:
        """Embed text using this embedding model.

        Args:
            text: Text to embed (will be truncated to max_context)

        Returns:
            Embedding vector as list of floats

        """
        import requests

        # Truncate to fit within token limit (rough estimate: 4 chars per token)
        max_chars = self.max_context * 4
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.debug(f"Truncated text to {max_chars} chars for embedding")

        # Construct full endpoint URL (OpenAI-compatible)
        endpoint_url = f"{self.api_base.rstrip('/')}/v1/embeddings"
        response = requests.post(
            endpoint_url,
            json={"input": text, "model": self.model},
            timeout=30,
        )
        response.raise_for_status()
        embedding = response.json()["data"][0]["embedding"]

        # JSONL logging for embeddings (same as LLM generation)
        import json as json_module
        import os
        from pathlib import Path

        # Skip if JSONL logging disabled
        if os.getenv("NO_JSONL_LOGGING"):
            return embedding

        # Use same logging logic as LLM generation
        base_dir = Path.cwd() / ".maxwell"
        log_dir = base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Use cached session ID (shared across all calls in this execution)
        session_id = _get_or_create_session_id()
        jsonl_file = log_dir / f"{session_id}.jsonl"

        # Create embedding log entry
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "model": self.model,
            "type": "embedding",
            "request": {"input": text, "model": self.model},
            "response": {
                "embedding": embedding,
                "dimensions": len(embedding),
                "min_value": min(embedding),
                "max_value": max(embedding),
                "mean_value": sum(embedding) / len(embedding),
                "first_10": embedding[:10],
                "last_10": embedding[-10:],
                "range": [min(embedding), max(embedding)],
            },
            "response_raw": {"data": [{"embedding": embedding}]},
            "grammar_used": False,
        }

        with open(jsonl_file, "a", encoding="utf-8") as f:
            f.write(json_module.dumps(log_entry) + "\n")

        return embedding


class LLMPool:
    """Pool manager for LLMs and embeddings with health checking."""

    def __init__(self, llms: List[LLMSpec], embeddings: List[EmbeddingSpec]):
        self.llms = {llm.name: llm for llm in llms}
        self.embeddings = {emb.name: emb for emb in embeddings}

        # Sort LLMs by speed for default selection
        self._llms_by_speed = sorted(
            llms, key=lambda x: x.capabilities.get("speed_tokens_per_sec", 0), reverse=True
        )

        # Health check cache: {service_name: (is_healthy, timestamp)}
        self._health_cache: Dict[str, tuple[bool, float]] = {}
        self._health_check_ttl = 30.0  # Cache health status for 30 seconds

        # Usage tracking for budget enforcement
        self._usage_tracker: Dict[str, Dict[str, int]] = {}  # {llm_name: {date: tokens_used}}
        self._load_usage_tracker()

    def _load_usage_tracker(self):
        """Load usage tracking data from cache file."""
        cache_file = Path.home() / ".maxwell" / "llm_usage.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    self._usage_tracker = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load usage tracker: {e}")
                self._usage_tracker = {}
        else:
            self._usage_tracker = {}

    def _save_usage_tracker(self):
        """Save usage tracking data to cache file."""
        cache_file = Path.home() / ".maxwell" / "llm_usage.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(self._usage_tracker, f, indent=2)

    def _track_usage(self, llm_name: str, tokens: int):
        """Track token usage for budget enforcement."""
        today = datetime.date.today().isoformat()

        if llm_name not in self._usage_tracker:
            self._usage_tracker[llm_name] = {}

        self._usage_tracker[llm_name][today] = self._usage_tracker[llm_name].get(today, 0) + tokens
        self._save_usage_tracker()

    def _check_budget(self, llm: LLMSpec, estimated_tokens: int) -> bool:
        """Check if LLM has budget remaining for this request."""
        if llm.daily_budget_tokens is None:
            return True  # Unlimited

        today = datetime.date.today().isoformat()
        used_today = self._usage_tracker.get(llm.name, {}).get(today, 0)

        return (used_today + estimated_tokens) <= llm.daily_budget_tokens

    @staticmethod
    def estimate_tokens(text: str, max_completion: int = 0) -> tuple[int, int]:
        """Estimate (prompt_tokens, total_tokens) from text.

        Uses tiktoken-like heuristic: ~4 chars per token.

        Args:
            text: Input text
            max_completion: Expected completion tokens

        Returns:
            (prompt_tokens, total_tokens)

        """
        # Rough heuristic: 4 chars/token (works reasonably for English + code)
        prompt_tokens = max(1, len(text) // 4)
        total_tokens = prompt_tokens + max_completion
        return prompt_tokens, total_tokens

    def score_llm(
        self,
        llm: LLMSpec,
        estimated_tokens: int,
        time_cost_weight: float = 1.0,
    ) -> float:
        """Score an LLM for a given request (higher = better).

        Scoring considers:
        - Monetary cost (static from API pricing)
        - Time cost (dynamic from speed)
        - Context utilization (prefer ~70% utilization)
        - Budget availability

        Args:
            llm: LLM to score
            estimated_tokens: Total tokens (prompt + completion)
            time_cost_weight: Weight for time vs money (0-10, default 1.0)

        Returns:
            Score (higher = better fit), or -1 if impossible

        """
        # Check hard constraints
        max_context = llm.capabilities.get("max_context", 4096)
        if estimated_tokens > max_context:
            return -1.0  # Impossible - doesn't fit

        if not self._check_budget(llm, estimated_tokens):
            logger.debug(f"{llm.name} over budget, skipping")
            return -1.0  # Over budget

        # Calculate monetary cost (negative because lower is better)
        monetary_cost = -llm.cost_per_1k_tokens * (estimated_tokens / 1000)

        # Calculate time cost (negative because slower is worse)
        speed = llm.capabilities.get("speed_tokens_per_sec", 25)
        time_seconds = estimated_tokens / speed
        time_cost = -time_cost_weight * time_seconds

        # Calculate utilization score (prefer ~70% utilization)
        utilization = estimated_tokens / max_context
        utilization_bonus = 1.0 - abs(utilization - 0.7)  # 0-1, peaks at 70%

        # Combined score
        total_score = monetary_cost + time_cost + utilization_bonus

        logger.debug(
            f"{llm.name}: score={total_score:.2f} "
            f"(money={monetary_cost:.2f}, time={time_cost:.2f}, "
            f"util={utilization_bonus:.2f}, {utilization*100:.0f}% full)"
        )

        return total_score

    def select_optimal_llm(
        self,
        prompt: str,
        max_completion: int = 512,
        time_cost_weight: float = 1.0,
        **capability_filters,
    ) -> LLMSpec:
        """Select optimal LLM using intelligent scoring.

        Args:
            prompt: Input prompt text
            max_completion: Expected completion tokens
            time_cost_weight: How much to value speed (0-10)
                - 0.0 = only minimize monetary cost
                - 1.0 = balanced (default)
                - 10.0 = maximize speed regardless of cost
            **capability_filters: Additional filters (reasoning, vision, etc.)

        Returns:
            Best LLM spec for this request

        Example:
            # For cheap batch processing (prefer free internal LLMs)
            llm = pool.select_optimal_llm(prompt, time_cost_weight=0.1)

            # For interactive user-facing (prefer speed)
            llm = pool.select_optimal_llm(prompt, time_cost_weight=10.0)

            # For balanced workloads
            llm = pool.select_optimal_llm(prompt, time_cost_weight=1.0)

        """
        # Estimate request size
        prompt_tokens, total_tokens = self.estimate_tokens(prompt, max_completion)

        logger.debug(
            f"Request size: ~{total_tokens} tokens ({prompt_tokens} prompt + {max_completion} completion)"
        )

        # Get healthy candidates matching capability filters
        healthy = self.get_healthy_llms()
        candidates = [llm for llm in healthy if llm.matches(**capability_filters)]

        if not candidates:
            raise ValueError(f"No healthy LLMs matching filters: {capability_filters}")

        # Score each candidate
        scored = [(self.score_llm(llm, total_tokens, time_cost_weight), llm) for llm in candidates]
        scored = [
            (score, llm) for score, llm in scored if score != -1.0
        ]  # Filter impossible (keep negative scores, they're valid costs)

        if not scored:
            raise ValueError(
                f"No LLMs can handle {total_tokens} tokens "
                f"(max available: {max([llm.capabilities.get('max_context', 0) for llm in candidates])})"
            )

        # Sort by score (best first)
        scored.sort(reverse=True, key=lambda x: x[0])
        best_score, best_llm = scored[0]

        logger.info(
            f"Selected {best_llm.name} (score={best_score:.2f}, "
            f"cost=${best_llm.cost_per_1k_tokens * total_tokens / 1000:.4f}, "
            f"tier={best_llm.tier})"
        )

        return best_llm

    @classmethod
    def from_registry(cls, registry_path: Optional[Path] = None) -> "LLMPool":
        """Load pool from registry JSON file.

        Search order:
        1. Provided registry_path
        2. .maxwell/lm_registry.json in current directory
        3. ~/.maxwell/lm_registry.json (global default)
        """
        if registry_path is None:
            # Try local first
            local_registry = Path.cwd() / ".maxwell" / "lm_registry.json"
            if local_registry.exists():
                registry_path = local_registry
            else:
                # Fall back to global
                global_registry = Path.home() / ".maxwell" / "lm_registry.json"
                if global_registry.exists():
                    registry_path = global_registry
                else:
                    raise FileNotFoundError(
                        "No LLM registry found. Create .maxwell/llm_registry.json or ~/.maxwell/llm_registry.json"
                    )

        with open(registry_path) as f:
            data = json.load(f)

        llms = [LLMSpec.from_dict(llm_data) for llm_data in data.get("llms", [])]
        embeddings = [EmbeddingSpec.from_dict(emb_data) for emb_data in data.get("embeddings", [])]

        logger.info(
            f"Loaded LLM pool from {registry_path}: {len(llms)} LLMs, {len(embeddings)} embeddings"
        )

        return cls(llms, embeddings)

    def _check_service_health(self, api_base: str) -> bool:
        """Check if a service is healthy by making a test request.

        Args:
            api_base: Base API URL (e.g., http://localhost:8000)

        Returns:
            True if service is healthy and responsive

        """
        import requests

        try:
            # Try /health endpoint first (common pattern)
            health_url = f"{api_base.rstrip('/')}/health"
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                return True
        except Exception:
            pass

        try:
            # Fallback: try /v1/models endpoint (OpenAI-compatible)
            models_url = f"{api_base.rstrip('/')}/v1/models"
            response = requests.get(models_url, timeout=2)
            if response.status_code == 200:
                return True
        except Exception:
            pass

        # Service is unreachable
        return False

    def is_service_healthy(self, name: str, llm_spec: Optional[LLMSpec] = None) -> bool:
        """Check if a service is healthy (with caching).

        Args:
            name: Service name
            llm_spec: LLM spec (optional, will look up if not provided)

        Returns:
            True if service is healthy

        """
        import time

        # Check cache first
        if name in self._health_cache:
            is_healthy, timestamp = self._health_cache[name]
            if time.time() - timestamp < self._health_check_ttl:
                return is_healthy

        # Get spec if not provided
        if llm_spec is None:
            if name in self.llms:
                llm_spec = self.llms[name]
            elif name in self.embeddings:
                # For embeddings, just check the API base
                emb_spec = self.embeddings[name]
                is_healthy = self._check_service_health(emb_spec.api_base)
                self._health_cache[name] = (is_healthy, time.time())
                return is_healthy
            else:
                # Unknown service
                return False

        # Check health using api_base (no need to extract!)
        is_healthy = self._check_service_health(llm_spec.api_base)

        # Update cache
        self._health_cache[name] = (is_healthy, time.time())

        if not is_healthy:
            logger.warning(f"Service {name} ({llm_spec.api_base}) is unhealthy or unreachable")

        return is_healthy

    def get_healthy_llms(self) -> List[LLMSpec]:
        """Get list of all healthy LLMs.

        Returns:
            List of LLM specs for services that are currently healthy

        """
        healthy = []
        for name, spec in self.llms.items():
            if self.is_service_healthy(name, spec):
                healthy.append(spec)
        return healthy

    def get_lm(self, name: str) -> LLMSpec:
        """Get LLM by name."""
        if name not in self.llms:
            raise KeyError(
                f"LLM '{name}' not found in registry. Available: {list(self.llms.keys())}"
            )
        return self.llms[name]

    def select_llm(
        self,
        min_speed: Optional[float] = None,
        min_context: Optional[int] = None,
        reasoning: Optional[bool] = None,
        vision: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        prefer_fastest: bool = True,
        check_health: bool = True,
    ) -> LLMSpec:
        """Select best LLM matching the given criteria (only healthy services).

        Args:
            min_speed: Minimum tokens/sec speed requirement
            min_context: Minimum context length requirement
            reasoning: Must have reasoning capability
            vision: Must have vision capability
            tags: Must have all these tags
            prefer_fastest: If True, return fastest match; otherwise return first match
            check_health: If True, only return healthy services (default)

        Returns:
            LLMSpec matching the criteria

        Raises:
            ValueError: If no LLM matches the criteria

        """
        # Filter by criteria
        candidates = [
            llm
            for llm in self._llms_by_speed
            if llm.matches(
                min_speed, min_context, reasoning, vision, None, tags
            )  # code_specialized=None
        ]

        # Filter by health if requested
        if check_health:
            healthy_candidates = [
                llm for llm in candidates if self.is_service_healthy(llm.name, llm)
            ]

            if healthy_candidates:
                candidates = healthy_candidates
            else:
                logger.warning(
                    "No healthy LLMs found matching criteria. "
                    "Falling back to all candidates (unhealthy services may fail)."
                )

        if not candidates:
            raise ValueError(
                f"No LLM found matching criteria: min_speed={min_speed}, min_context={min_context}, "
                f"reasoning={reasoning}, vision={vision}, tags={tags}"
            )

        if prefer_fastest:
            selected = candidates[0]  # Already sorted by speed
        else:
            selected = candidates[0]

        logger.info(
            f"Selected LLM: {selected.name} (healthy={self.is_service_healthy(selected.name, selected)})"
        )
        return selected

    def get_fastest_llm(self, check_health: bool = True) -> LLMSpec:
        """Get the fastest available LLM (only healthy by default).

        Args:
            check_health: If True, only return healthy services (default)

        Returns:
            Fastest LLM spec

        Raises:
            ValueError: If no healthy LLMs available

        """
        if check_health:
            healthy = self.get_healthy_llms()
            if healthy:
                # Sort by speed
                fastest = sorted(
                    healthy,
                    key=lambda x: x.capabilities.get("speed_tokens_per_sec", 0),
                    reverse=True,
                )[0]
                logger.info(f"Fastest healthy LLM: {fastest.name}")
                return fastest
            else:
                logger.warning("No healthy LLMs found. Falling back to fastest registered LLM.")

        return self._llms_by_speed[0]

    def get_embedding(self, name_or_tag: str = "default") -> EmbeddingSpec:
        """Get embedding by name or tag."""
        # Try exact name match first
        if name_or_tag in self.embeddings:
            return self.embeddings[name_or_tag]

        # Try tag match
        for emb in self.embeddings.values():
            if name_or_tag in emb.tags:
                return emb

        raise KeyError(
            f"Embedding '{name_or_tag}' not found. Available: {list(self.embeddings.keys())}"
        )

    def list_llms(self) -> List[str]:
        """List all available LLM names."""
        return list(self.llms.keys())

    def list_embeddings(self) -> List[str]:
        """List all available embedding names."""
        return list(self.embeddings.keys())


class LLMClient:
    """LLM client with GBNF grammar support for structured output."""

    def __init__(self, llm_spec: LLMSpec):
        """Initialize with an LLM spec from the pool."""
        self.spec = llm_spec

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        pydantic_model: Optional[Any] = None,
        grammar: Optional[str] = None,
    ) -> str:
        """Generate text from a prompt with optional GBNF grammar constraints.

        Args:
            prompt: User prompt
            temperature: Sampling temperature (default: from spec)
            max_tokens: Max tokens to generate (default: from spec)
            system_prompt: Optional system prompt
            pydantic_model: Pydantic model to auto-generate GBNF grammar (mutually exclusive with grammar)
            grammar: Pre-generated GBNF grammar string (mutually exclusive with pydantic_model)

        Returns:
            Generated text constrained by grammar if provided

        """
        import requests

        temp = temperature if temperature is not None else self.spec.default_temperature
        max_tok = (
            max_tokens if max_tokens is not None else self.spec.capabilities.get("max_tokens", 2000)
        )

        # Auto-generate grammar from Pydantic model if provided
        if pydantic_model is not None and grammar is None:
            from maxwell.pydantic_gbnf import generate_gbnf_grammar_and_documentation

            grammar, _ = generate_gbnf_grammar_and_documentation([pydantic_model])
            logger.debug(f"Auto-generated GBNF grammar from {pydantic_model.__name__}")
        elif pydantic_model is not None and grammar is not None:
            raise ValueError("Cannot specify both pydantic_model and grammar - choose one")

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request payload
        payload = {
            "model": self.spec.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tok,
        }

        # Add grammar if provided (llama.cpp specific)
        if grammar and self.spec.backend == "llamacpp":
            payload["grammar"] = grammar

        # Make request (OpenAI-compatible)
        endpoint_url = f"{self.spec.api_base.rstrip('/')}/v1/chat/completions"
        response = requests.post(endpoint_url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        # JSONL logging for debugging
        import json as json_module
        import os
        from pathlib import Path

        # Create logs directory relative to current working directory (can be disabled with NO_JSONL_LOGGING env var)
        if os.getenv("NO_JSONL_LOGGING"):
            return data["choices"][0]["message"]["content"]

        # Use execution directory for logs (current working directory)
        base_dir = Path.cwd() / ".maxwell"
        log_dir = base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Use workflow config session_id if available, otherwise generate
        session_id = None
        if isinstance(messages, dict) and "workflow_config" in messages:  # type: ignore[unreachable]
            config = messages["workflow_config"]  # type: ignore[index]
            if hasattr(config, "session_id") and config.session_id:
                session_id = config.session_id
                logger.info(f"Using workflow session ID: {session_id}")
            else:
                session_id = _get_or_create_session_id()
                logger.info(f"No workflow session ID, using generated: {session_id}")
        else:
            # Fallback for non-workflow calls
            session_id = _get_or_create_session_id()
            logger.info(f"No workflow config, using generated session ID: {session_id}")

        jsonl_file = log_dir / f"{session_id}.jsonl"

        logger.info(f"JSONL logging enabled: {jsonl_file}")

        # Log request/response pair
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "model": self.spec.model,
            "request": messages,
            "response": data,
            "response_raw": data,
            "grammar_used": grammar is not None,
        }

        with open(jsonl_file, "a", encoding="utf-8") as f:
            f.write(json_module.dumps(log_entry) + "\n")

        return data["choices"][0]["message"]["content"]


def get_lm(
    name: Optional[str] = None,
    prompt: Optional[str] = None,
    max_completion: int = 512,
    time_cost_weight: float = 1.0,
    **selection_kwargs,
) -> LLMClient:
    """Get a language model (LM) client from the pool.

    Args:
        name: Specific LM name, or None to select by capabilities
        prompt: Optional prompt for intelligent routing (enables scheduler)
        max_completion: Expected completion tokens (used with prompt)
        time_cost_weight: How much to value speed vs cost (0-10, used with prompt)
        **selection_kwargs: Capability filters (min_speed, reasoning, vision, etc.)

    Returns:
        LLMClient ready to use

    Examples:
        # Get default (fastest) LM
        lm = get_lm()

        # Get specific LM by name
        lm = get_lm("qwen-coder-30b")

        # Intelligent routing based on prompt size
        lm = get_lm(prompt="Write a function...", time_cost_weight=1.0)

        # Select by capabilities
        lm = get_lm(reasoning=True, min_speed=50)
        lm = get_lm(vision=True)

    """
    pool = LLMPool.from_registry()

    if name:
        spec = pool.get_lm(name)
    elif prompt:
        # Use intelligent routing when prompt is provided
        spec = pool.select_optimal_llm(
            prompt,
            max_completion=max_completion,
            time_cost_weight=time_cost_weight,
            **selection_kwargs,
        )
    elif selection_kwargs:
        spec = pool.select_llm(**selection_kwargs)
    else:
        spec = pool.get_fastest_llm()

    if not spec:
        raise ValueError(f"No LM found matching criteria: name={name}, {selection_kwargs}")

    return LLMClient(spec)


def get_embedding(name: str = "default") -> EmbeddingSpec:
    """Get an embedding model from the pool.

    Args:
        name: Embedding name or tag (default: "default")

    Returns:
        EmbeddingSpec with embed() method

    Examples:
        # Get default embedding
        emb = get_embedding()
        vector = emb.embed("some text")

        # Get specific embedding by name
        emb = get_embedding("qwen-embed-4b")

    """
    pool = LLMPool.from_registry()
    spec = pool.get_embedding(name)

    if not spec:
        raise ValueError(f"Embedding '{name}' not found. Available: {pool.list_embeddings()}")

    return spec
