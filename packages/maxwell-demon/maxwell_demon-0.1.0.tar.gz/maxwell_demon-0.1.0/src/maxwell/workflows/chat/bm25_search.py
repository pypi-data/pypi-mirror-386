"""BM25 search workflow for chat turns - fast keyword-based retrieval.

Architecture:
- BM25Okapi algorithm for keyword scoring
- Simple tokenization (lowercase + split)
- Index built on-demand from MongoDB turns collection
- Fast search: ~5ms for 5,812 turns
- Maxwell workflow interface for MCP access

Usage:
    # Direct usage
    from maxwell.workflows.chat.bm25_search import BM25Searcher

    searcher = BM25Searcher()
    results = searcher.search("maxwell architecture deduplication", top_k=10)

    # Via Maxwell workflow
    from maxwell.registry import get_workflow

    workflow = get_workflow("chat-bm25-search")
    result = workflow.execute(Path.cwd(), {"query": "maxwell architecture", "limit": 10})
"""

__all__ = [
    "BM25Searcher",
    "ChatBM25SearchWorkflow",
    "BM25SearchInputs",
    "BM25SearchOutputs",
    "BM25IndexStats",
]

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from rank_bm25 import BM25Okapi

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


@dataclass
class BM25IndexStats:
    """Statistics about BM25 index."""

    total_turns: int
    chatgpt_turns: int
    claude_turns: int
    machines: Dict[str, int]
    index_built: bool


@dataclass(frozen=True)
class BM25SearchInputs(WorkflowInputs):
    """Input schema for BM25 search workflow."""

    query: str
    limit: int = 10
    source: Optional[str] = None


@dataclass(frozen=True)
class BM25SearchOutputs(WorkflowOutputs):
    """Output schema for BM25 search workflow."""

    results: List[Dict[str, Any]]
    results_count: int
    search_type: str
    report: str


def tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase + split on whitespace/punctuation.

    Args:
        text: Text to tokenize

    Returns:
        List of tokens

    """
    # Lowercase and split on whitespace/punctuation
    text = text.lower()
    # Keep alphanumeric and some technical chars (-, _, .)
    tokens = re.findall(r"\b[\w\-_.]+\b", text)
    return tokens


class BM25Searcher:
    """BM25 search over chat turns."""

    def __init__(
        self, mongodb_uri: str = "mongodb://localhost:27017", mongodb_db: str = "chat_analytics"
    ):
        """Initialize BM25 searcher.

        Args:
            mongodb_uri: MongoDB connection URI
            mongodb_db: MongoDB database name

        """
        self.mongo_client = MongoClient(mongodb_uri)
        self.mongo_db = self.mongo_client[mongodb_db]
        self.turns_collection = self.mongo_db["turns"]

        # BM25 index (built on-demand)
        self.bm25 = None
        self.corpus = None  # List of turn documents
        self.tokenized_corpus = None  # Tokenized documents

        logger.info("BM25Searcher initialized")

    def build_index(self, rebuild: bool = False):
        """Build BM25 index from turns collection.

        Args:
            rebuild: Force rebuild even if index exists

        """
        if self.bm25 is not None and not rebuild:
            logger.info("BM25 index already built")
            return

        logger.info("Building BM25 index from turns collection...")

        # Load all turns
        self.corpus = list(self.turns_collection.find({}))
        logger.info(f"Loaded {len(self.corpus)} turns")

        if not self.corpus:
            logger.warning("No turns found in collection")
            return

        # Tokenize all combined_text fields
        self.tokenized_corpus = [
            tokenize(turn.get("combined_text", ""))  # maxwell:ignore-dict-get (MongoDB doc)
            for turn in self.corpus
        ]

        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        logger.info("✓ BM25 index built")

    def search(
        self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search turns using BM25.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional MongoDB filters (e.g., {"source": "chatgpt"})

        Returns:
            List of turn documents with scores

        """
        # Build index if needed
        if self.bm25 is None:
            self.build_index()

        if not self.corpus or self.bm25 is None:
            return []

        # Tokenize query
        query_tokens = tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Apply filters if provided
        if filters:
            valid_indices = []
            for i, turn in enumerate(self.corpus):
                match = all(turn.get(key) == value for key, value in filters.items())
                if match:
                    valid_indices.append(i)

            # Filter scores
            filtered_results = [(i, scores[i]) for i in valid_indices]
        else:
            filtered_results = list(enumerate(scores))

        # Sort by score descending
        filtered_results.sort(key=lambda x: x[1], reverse=True)

        # Take top-k
        top_results = filtered_results[:top_k]

        # Build result documents
        results = []
        for idx, score in top_results:
            turn = self.corpus[idx].copy()
            turn["bm25_score"] = float(score)
            results.append(turn)

        return results

    def search_by_source(self, query: str, source: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search within a specific source (chatgpt or claude).

        Args:
            query: Search query
            source: "chatgpt" or "claude"
            top_k: Number of results to return

        Returns:
            List of turn documents with scores

        """
        return self.search(query, top_k=top_k, filters={"source": source})

    def search_by_machine(self, query: str, machine: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search Claude turns from a specific machine.

        Args:
            query: Search query
            machine: Machine name (e.g., "vanguard", "backup-mac")
            top_k: Number of results to return

        Returns:
            List of turn documents with scores

        """
        return self.search(query, top_k=top_k, filters={"machine": machine})

    def get_stats(self) -> BM25IndexStats:
        """Get index statistics.

        Returns:
            BM25IndexStats with index stats

        """
        if self.bm25 is None:
            self.build_index()

        if not self.corpus:
            return BM25IndexStats(
                total_turns=0,
                chatgpt_turns=0,
                claude_turns=0,
                machines={},
                index_built=self.bm25 is not None,
            )

        total_turns = len(self.corpus)

        # Count by source
        chatgpt_count = sum(
            1 for t in self.corpus if t.get("source") == "chatgpt"
        )  # maxwell:ignore-dict-get (MongoDB doc)
        claude_count = sum(
            1 for t in self.corpus if t.get("source") == "claude"
        )  # maxwell:ignore-dict-get (MongoDB doc)

        # Count by machine (Claude only)
        machines: Dict[str, int] = {}
        for turn in self.corpus:
            if turn.get("source") == "claude":  # maxwell:ignore-dict-get (MongoDB doc)
                machine = turn.get("machine", "unknown")  # maxwell:ignore-dict-get (MongoDB doc)
                machines[machine] = machines.get(machine, 0) + 1

        return BM25IndexStats(
            total_turns=total_turns,
            chatgpt_turns=chatgpt_count,
            claude_turns=claude_count,
            machines=machines,
            index_built=self.bm25 is not None,
        )


@register_workflow
class ChatBM25SearchWorkflow(BaseWorkflow):
    """Chat BM25 search workflow - Maxwell workflow interface for BM25Searcher."""

    # Workflow metadata
    workflow_id: str = "chat-bm25-search"
    name: str = "Chat BM25 Search"
    description: str = "Search chat conversations using BM25 keyword matching"
    version: str = "1.0"
    category: str = "chat-search"
    tags: set = {"bm25", "search", "chat", "keyword"}

    InputSchema = BM25SearchInputs
    OutputSchema = BM25SearchOutputs

    def __init__(self):
        self.workflow_id = "chat-bm25-search"
        self.name = "Chat BM25 Search"
        self.description = "Search chat conversations using BM25 keyword matching"
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
        """Define CLI parameters for maxwell chat-bm25-search command.

        CLI Usage:
            maxwell chat-bm25-search --query "your search query" [--limit 10] [--source chatgpt|claude]

        Examples:
            # Search all chat conversations
            maxwell chat-bm25-search --query "maxwell architecture"

            # Search only ChatGPT conversations
            maxwell chat-bm25-search --query "python programming" --source chatgpt --limit 5

            # Search only Claude conversations
            maxwell chat-bm25-search --query "file system" --source claude

        """
        return [
            {
                "name": "query",
                "type": str,
                "required": True,
                "help": "Search query for BM25 keyword search",
            },
            {
                "name": "limit",
                "type": int,
                "required": False,
                "default": 10,
                "help": "Number of results to return (default: 10)",
            },
            {
                "name": "source",
                "type": str,
                "required": False,
                "help": "Filter by source: chatgpt or claude",
            },
        ]

    def get_required_inputs(self) -> List[str]:
        """Get required inputs."""
        return ["query"]

    def get_produced_outputs(self) -> List[str]:
        """Get produced outputs."""
        return ["results", "report"]

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute BM25 search using BM25Searcher.

        Args:
            project_root: Root directory (not used for chat search)
            context: Dictionary containing search parameters

        Returns:
            WorkflowResult with BM25 search results and formatted report

        """
        try:
            # Parse typed inputs
            inputs: BM25SearchInputs = self.parse_inputs(context)  # type: ignore[assignment]

            # Use BM25Searcher directly
            searcher = BM25Searcher()

            # Apply source filter if provided
            filters = {"source": inputs.source} if inputs.source else None
            results = searcher.search(inputs.query, top_k=inputs.limit, filters=filters)

            # Format results
            report = self._format_results(results, inputs.query, inputs.source)

            # Get search stats
            stats = searcher.get_stats()

            # Return success
            metrics = WorkflowMetrics(
                start_time=0.0,
                end_time=0.0,
                files_processed=len(results),
                custom_metrics={
                    "results_count": len(results),
                    "search_type": "BM25",
                    "query": inputs.query,
                    "source_filter": inputs.source,
                    "total_turns_indexed": stats.total_turns,
                },
            )
            metrics.finalize()

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.COMPLETED,
                metrics=metrics,
                artifacts={
                    "results": results,
                    "results_count": len(results),
                    "search_type": "BM25",
                    "query": inputs.query,
                    "source_filter": inputs.source,
                    "stats": stats,
                    "report": report,
                },
            )

        except Exception as e:
            logger.error(f"BM25 search failed: {e}", exc_info=True)
            metrics = WorkflowMetrics(
                start_time=0.0, end_time=0.0, files_processed=0, errors_encountered=1
            )
            metrics.finalize()

            return WorkflowResult(
                workflow_id=self.workflow_id,
                status=WorkflowStatus.FAILED,
                metrics=metrics,
                error_message=f"BM25 search failed: {str(e)}",
            )

    def _format_results(
        self, results: List[Dict[str, Any]], query: str, source_filter: Optional[str] = None
    ) -> str:
        """Format BM25 results for display.

        Args:
            results: List of BM25 search results
            query: Original search query
            source_filter: Optional source filter applied

        Returns:
            Formatted string for display

        """
        lines = []
        lines.append(f"[SEARCH] BM25 search for: {query}")
        if source_filter:
            lines.append(f"🎯 Source filter: {source_filter}")
        lines.append(f"[STATS] Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            turn_id = result.get("turn_id", "Unknown")
            score = result.get("bm25_score", 0.0)
            source = result.get("source", "unknown")
            machine = result.get("machine", "")
            project_path = result.get("project_path", "")
            combined_text = result.get("combined_text", "")

            lines.append(f"Result {i}/{len(results)}")
            lines.append(f"🎯 Score: {score:.3f} | ID: {turn_id} | Source: {source}")

            if machine:
                lines.append(f"🖥️  Machine: {machine}")
            if project_path:
                lines.append(f"📁 Project: {project_path}")

            if combined_text:
                snippet = combined_text[:150] + "..." if len(combined_text) > 150 else combined_text
                lines.append(f"📄 Content: {snippet}")

            lines.append("-" * 80)

        lines.append(f"\n✨ Search complete! Found {len(results)} results.")
        return "\n".join(lines)


def search_cli(query: str, top_k: int = 10, source: Optional[str] = None):
    """CLI interface for BM25 search.

    Args:
        query: Search query
        top_k: Number of results to return
        source: Optional source filter ("chatgpt" or "claude")

    """
    searcher = BM25Searcher()

    # Search
    if source:
        results = searcher.search_by_source(query, source, top_k=top_k)
    else:
        results = searcher.search(query, top_k=top_k)

    # Display results
    if not results:
        print(f"No results found for query: {query}")
        return

    print(f"Found {len(results)} results for query: {query}")
    if source:
        print(f"Source: {source}")
    print("-" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.get('bm25_score', 0.0):.3f}")
        print(f"   ID: {result.get('turn_id', 'Unknown')}")
        print(f"   Source: {result.get('source', 'unknown')}")

        if result.get("machine"):
            print(f"   Machine: {result['machine']}")
        if result.get("project_path"):
            print(f"   Project: {result['project_path']}")

        # Show preview
        combined = result.get("combined_text", "")
        preview = combined[:300].replace("\n", " ")
        print(f"   Preview: {preview}...")

    # Show stats
    stats = searcher.get_stats()
    print("\n[STATS] Index Stats:")
    print(f"   Total turns: {stats.total_turns}")
    print(f"   ChatGPT turns: {stats.chatgpt_turns}")
    print(f"   Claude turns: {stats.claude_turns}")

    if stats.machines:
        print(f"   Machines: {stats.machines}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BM25 search for chat turns")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument(
        "--source", type=str, choices=["chatgpt", "claude"], help="Filter by source"
    )

    args = parser.parse_args()

    search_cli(args.query, top_k=args.top_k, source=args.source)
