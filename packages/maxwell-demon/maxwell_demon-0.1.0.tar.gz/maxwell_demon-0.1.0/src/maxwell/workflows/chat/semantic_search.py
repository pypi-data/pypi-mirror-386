"""Chat search workflow for searching indexed chat logs.

Uses MongoDB + Qdrant to search chat conversations with semantic embeddings,
metadata filters, and text search.
"""

__all__ = [
    "ChatSearchResult",
    "ChatSearchInputs",
    "ChatSearchOutputs",
    "ChatSemanticSearchWorkflow",
]

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from qdrant_client import QdrantClient

from maxwell.lm_pool import get_embedding
from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowInputs,
    WorkflowMetrics,
    WorkflowOutputs,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatSearchInputs(WorkflowInputs):
    """Input schema for chat search workflow."""

    query: Optional[str] = None
    text: Optional[str] = None
    limit: int = 10
    format: str = "detailed"


@dataclass(frozen=True)
class ChatSearchOutputs(WorkflowOutputs):
    """Output schema for chat search workflow."""

    results: List[Dict[str, Any]]  # List of ChatSearchResult dicts
    results_count: int
    search_type: str
    report: str


@dataclass
class ChatSearchResult:
    """Result from chat search."""

    turn_id: str
    score: float
    user_text: str
    assistant_text: str
    topics: List[str]
    intent: str
    technologies: List[str]
    summary: str
    source: str
    embedding: Optional[List[float]] = None

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata dict for compatibility with topic analysis."""
        return {
            "turn_id": self.turn_id,
            "topics": self.topics,
            "intent": self.intent,
            "technologies": self.technologies,
            "summary": self.summary,
            "user_text": self.user_text,
            "assistant_text": self.assistant_text,
        }


@register_workflow
class ChatSemanticSearchWorkflow(BaseWorkflow):
    """Search chat logs using MongoDB + Qdrant embeddings."""

    # Workflow metadata for registry
    workflow_id: str = "chat-semantic-search"
    name: str = "Chat Semantic Search"
    description: str = (
        "Search indexed chat conversations using semantic search and metadata filters"
    )
    version: str = "1.0"
    category: str = "search"
    tags: set = {"chat", "search", "mongodb", "qdrant", "semantic"}

    InputSchema = ChatSearchInputs
    OutputSchema = ChatSearchOutputs

    def __init__(self):
        self.workflow_id = "chat-semantic-search"
        self.name = "Chat Semantic Search"
        self.description = (
            "Search indexed chat conversations using semantic search and metadata filters"
        )
        self.version = "1.0"
        super().__init__()

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=300,  # 5 minutes
            parameters={
                "root_dir": str(root_dir),
            },
        )

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Define CLI parameters for chat search."""
        return [
            {
                "name": "query",
                "type": str,
                "required": False,
                "help": "Search query for semantic search",
            },
            {
                "name": "text",
                "type": str,
                "required": False,
                "help": "Text regex search instead of semantic",
            },
            {
                "name": "limit",
                "type": int,
                "required": False,
                "default": 10,
                "help": "Number of results to return",
            },
            {
                "name": "format",
                "type": str,
                "required": False,
                "default": "detailed",
                "help": "Output format: detailed, topics-only, compact",
            },
        ]

    def get_required_inputs(self) -> List[str]:
        """Get list of required input keys."""
        return []  # No required inputs for search

    def get_produced_outputs(self) -> List[str]:
        """Get list of produced output keys."""
        return ["results", "report"]

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute chat search workflow."""
        try:
            # Parse typed inputs
            inputs: ChatSearchInputs = self.parse_inputs(context)  # type: ignore[assignment]

            # Initialize connections
            qdrant = QdrantClient(host="localhost", port=6333)
            mongo_client = MongoClient("mongodb://localhost:27017")
            mongo_db = mongo_client["chat_analytics"]
            turns_collection = mongo_db["turns"]
            metadata_collection = mongo_db["turn_metadata"]
            embedding_client = get_embedding()

            # Extract parameters from typed inputs
            query = inputs.query
            text_search = inputs.text or context.get("company")  # company fallback from old API
            topics = context.get("topic")  # Not in InputSchema yet
            intent = context.get("intent")  # Not in InputSchema yet
            technologies = context.get("technology")  # Not in InputSchema yet
            limit = inputs.limit
            format_type = inputs.format

            # Parse comma-separated lists
            topics_list = topics.split(",") if topics else None
            technologies_list = technologies.split(",") if technologies else None

            results = []

            # Determine search type and execute
            if text_search:
                # Text search
                pattern = text_search
                results = self._search_text(pattern, turns_collection, limit)
                search_type = f"Text search for: {pattern}"

            elif topics_list or intent or technologies_list:
                # Metadata search
                results = self._search_metadata(
                    metadata_collection,
                    turns_collection,
                    topics_list,
                    intent,
                    technologies_list,
                    limit,
                )
                search_type = "Metadata filtering"

            elif query:
                # Semantic search
                results = self._search_semantic(
                    query, embedding_client, qdrant, turns_collection, limit
                )
                search_type = f"Semantic search for: {query}"

            else:
                # No search parameters provided - return all results (for topic analysis)
                results = self._get_all_results(turns_collection, qdrant, limit)
                search_type = "All results (no filter)"

            # Format results
            report = self._format_results(results, format_type, search_type)

            # Create metrics
            metrics = WorkflowMetrics(
                start_time=0.0,
                end_time=0.0,
                files_processed=len(results),
                custom_metrics={"results_count": len(results), "search_type": search_type},
            )
            metrics.finalize()

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.COMPLETED,
                metrics=metrics,
                artifacts={
                    "results": results,
                    "results_count": len(results),
                    "search_type": search_type,
                    "report": report,
                },
            )

        except Exception as e:
            # Create metrics for failed case
            metrics = WorkflowMetrics(
                start_time=0.0, end_time=0.0, files_processed=0, errors_encountered=1
            )
            metrics.finalize()

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.FAILED,
                metrics=metrics,
                error_message=f"Semantic search failed: {str(e)}",
            )

    def _search_semantic(
        self, query: str, embedding_client, qdrant, turns_collection, limit: int
    ) -> List[ChatSearchResult]:
        """Search using semantic embeddings."""
        query_vector = embedding_client.embed(query)

        search_results = qdrant.query_points(
            collection_name="chat_turns", query=query_vector, limit=limit, with_payload=True
        )

        results = []
        for point in search_results.points:
            payload = point.payload
            turn_id = payload.get("turn_id", "Unknown")  # maxwell:ignore-dict-get (Qdrant payload)
            score = point.score

            # Get full conversation
            turn = turns_collection.find_one({"turn_id": turn_id})
            if turn:
                results.append(
                    ChatSearchResult(
                        turn_id=turn_id,
                        score=score,
                        user_text=turn.get("user", {}).get(
                            "text", ""
                        ),  # maxwell:ignore-dict-get (MongoDB doc)
                        assistant_text=turn.get("assistant", {}).get(
                            "text", ""
                        ),  # maxwell:ignore-dict-get (MongoDB doc)
                        topics=payload.get(
                            "topics", []
                        ),  # maxwell:ignore-dict-get (Qdrant payload)
                        intent=payload.get(
                            "intent", "N/A"
                        ),  # maxwell:ignore-dict-get (Qdrant payload)
                        technologies=payload.get(
                            "technologies", []
                        ),  # maxwell:ignore-dict-get (Qdrant payload)
                        summary=payload.get(
                            "summary", ""
                        ),  # maxwell:ignore-dict-get (Qdrant payload)
                        source=turn.get(
                            "source", "unknown"
                        ),  # maxwell:ignore-dict-get (MongoDB doc)
                    )
                )

        return results

    def _search_metadata(
        self,
        metadata_collection,
        turns_collection,
        topics: Optional[List[str]],
        intent: Optional[str],
        technologies: Optional[List[str]],
        limit: int,
    ) -> List[ChatSearchResult]:
        """Search using extracted metadata filters."""
        query = {}

        if topics:
            query["metadata.topics"] = {"$in": topics}
        if intent:
            query["metadata.intent"] = intent
        if technologies:
            query["metadata.technologies"] = {"$in": technologies}

        cursor = metadata_collection.find(query).limit(limit)
        results = []

        for doc in cursor:
            turn_id = doc["turn_id"]
            metadata = doc["metadata"]

            # Get full conversation
            turn = turns_collection.find_one({"turn_id": turn_id})
            if turn:
                results.append(
                    ChatSearchResult(
                        turn_id=turn_id,
                        score=1.0,  # Exact metadata match
                        user_text=turn.get("user", {}).get(
                            "text", ""
                        ),  # maxwell:ignore-dict-get (MongoDB doc)
                        assistant_text=turn.get("assistant", {}).get(
                            "text", ""
                        ),  # maxwell:ignore-dict-get (MongoDB doc)
                        topics=metadata.get(
                            "topics", []
                        ),  # maxwell:ignore-dict-get (MongoDB metadata)
                        intent=metadata.get(
                            "intent", "N/A"
                        ),  # maxwell:ignore-dict-get (MongoDB metadata)
                        technologies=metadata.get(
                            "technologies", []
                        ),  # maxwell:ignore-dict-get (MongoDB metadata)
                        summary=metadata.get(
                            "summary", ""
                        ),  # maxwell:ignore-dict-get (MongoDB metadata)
                        source=turn.get(
                            "source", "unknown"
                        ),  # maxwell:ignore-dict-get (MongoDB doc)
                    )
                )

        return results

    def _search_text(self, pattern: str, turns_collection, limit: int) -> List[ChatSearchResult]:
        """Search using regex text matching."""
        cursor = turns_collection.find(
            {
                "$or": [
                    {"user.text": {"$regex": pattern, "$options": "i"}},
                    {"assistant.text": {"$regex": pattern, "$options": "i"}},
                ]
            }
        ).limit(limit)

        results = []
        for turn in cursor:
            user_text = turn.get("user", {}).get(
                "text", ""
            )  # maxwell:ignore-dict-get (MongoDB doc)
            assistant_text = turn.get("assistant", {}).get(
                "text", ""
            )  # maxwell:ignore-dict-get (MongoDB doc)

            results.append(
                ChatSearchResult(
                    turn_id=turn["turn_id"],
                    score=1.0,
                    user_text=user_text,
                    assistant_text=assistant_text,
                    source=turn.get("source", "unknown"),  # maxwell:ignore-dict-get (MongoDB doc)
                    topics=[],
                    intent="N/A",
                    technologies=[],
                    summary="",
                )
            )

        return results

    def _format_results(
        self, results: List[ChatSearchResult], format_type: str, search_type: str
    ) -> str:
        """Format search results for display."""
        lines = []

        # Header
        lines.append(f"[SEARCH] {search_type}")
        lines.append(f"[RESULTS] Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            if format_type == "topics-only":
                # Topics-only display
                lines.append(f"Result {i}/{len(results)}")
                lines.append(f"[SCORE] {result.score:.3f} | {result.turn_id}")
                if result.topics:
                    lines.append(f"[TOPICS] {', '.join(result.topics)}")
                if result.intent != "N/A":
                    lines.append(f"[INTENT] {result.intent}")
                if result.technologies:
                    lines.append(f"[TECH] {', '.join(result.technologies)}")
                lines.append("-" * 80)

            elif format_type == "compact":
                # Compact display
                user_snippet = (
                    result.user_text[:80] + "..."
                    if len(result.user_text) > 80
                    else result.user_text
                )
                lines.append(f"{i}. {result.turn_id} ({result.score:.3f})")
                lines.append(f"   {user_snippet}")
                lines.append("")

            else:  # detailed (default)
                # Full display
                lines.append(f"Result {i}/{len(results)}")
                lines.append(f"[SCORE] {result.score:.3f} | {result.turn_id}")

                # Metadata
                if result.topics:
                    lines.append(f"[TOPICS] {', '.join(result.topics)}")
                if result.intent != "N/A":
                    lines.append(f"[INTENT] {result.intent}")
                if result.technologies:
                    lines.append(f"[TECH] {', '.join(result.technologies)}")
                if result.summary:
                    lines.append(f"[SUMMARY] {result.summary}")

                # Conversation snippet
                if result.user_text:
                    snippet = (
                        result.user_text[:150] + "..."
                        if len(result.user_text) > 150
                        else result.user_text
                    )
                    lines.append(f"[USER] {snippet}")

                if result.assistant_text:
                    snippet = (
                        result.assistant_text[:150] + "..."
                        if len(result.assistant_text) > 150
                        else result.assistant_text
                    )
                    lines.append(f"[ASSISTANT] {snippet}")

                    lines.append("-" * 80)

        lines.append(f"\n[COMPLETE] Search complete! Found {len(results)} results.")
        return "\n".join(lines)

    def _get_all_results(
        self, turns_collection, qdrant, limit: int = 100
    ) -> List[ChatSearchResult]:
        """Get all conversation results (for topic analysis)."""
        results = []

        # Query Qdrant directly to get points with embeddings
        try:
            # Scroll through Qdrant collection to get points
            scroll_result = qdrant.scroll(
                collection_name="chat_turns", limit=limit, with_vectors=True, with_payload=True
            )

            points = scroll_result[0]  # Get points from scroll result

            for point in points:
                turn_id = point.id
                embedding = point.vector
                payload = point.payload

                # Create result with existing embedding
                result = ChatSearchResult(
                    turn_id=str(turn_id),
                    score=1.0,  # No relevance score when getting all
                    user_text=payload.get(
                        "user_text", ""
                    ),  # maxwell:ignore-dict-get (Qdrant payload)
                    assistant_text=payload.get(
                        "assistant_text", ""
                    ),  # maxwell:ignore-dict-get (Qdrant payload)
                    topics=payload.get("topics", []),  # maxwell:ignore-dict-get (Qdrant payload)
                    intent=payload.get("intent", ""),  # maxwell:ignore-dict-get (Qdrant payload)
                    technologies=payload.get(
                        "technologies", []
                    ),  # maxwell:ignore-dict-get (Qdrant payload)
                    summary=payload.get("summary", ""),  # maxwell:ignore-dict-get (Qdrant payload)
                    source=payload.get(
                        "source", "unknown"
                    ),  # maxwell:ignore-dict-get (Qdrant payload)
                    embedding=(
                        embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
                    ),
                )
                results.append(result)

        except Exception as e:
            logger.error(f"Failed to retrieve embeddings from Qdrant: {e}")
            # Fallback: return empty results rather than crash
            pass

        return results
