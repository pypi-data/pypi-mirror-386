"""Tier 2 metadata extraction for chat turns using LLM.

Extracts structured metadata:
- Topics (organic tags like "maxwell-architecture", "bm25-search")
- Intent (question, explanation, debugging, implementation, planning)
- Technologies (python, mongodb, elasticsearch, etc.)
- Entities (files, functions, projects)

Caching:
- Results cached in MongoDB turn_metadata collection
- Only re-extract if turn content changes
- Extraction is on-demand, not batch

Usage:
    from metadata_extractor import MetadataExtractor

    extractor = MetadataExtractor()
    metadata = extractor.extract("turn_id_123")
    print(metadata.topics)  # ["maxwell", "bm25-search"]
"""

__all__ = ["MetadataExtractor"]

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from maxwell.lm_pool import get_embedding, get_lm

logger = logging.getLogger(__name__)


# ===== Pydantic Schema for Structured Metadata =====


class TurnEntities(BaseModel):
    """Entities extracted from a turn."""

    files: List[str] = Field(
        default_factory=list, description="Files mentioned (e.g., bm25_search.py)"
    )
    functions: List[str] = Field(
        default_factory=list, description="Functions/classes mentioned (e.g., BM25Searcher)"
    )
    projects: List[str] = Field(
        default_factory=list, description="Projects mentioned (e.g., maxwell)"
    )
    tools: List[str] = Field(
        default_factory=list, description="Tools/libraries mentioned (e.g., rank-bm25)"
    )


class TurnMetadata(BaseModel):
    """Tier 2 metadata for a conversation turn."""

    # Core metadata
    topics: List[str] = Field(
        default_factory=list,
        description="Organic topic tags (e.g., maxwell-architecture, bm25-search, chat-indexing)",
        max_length=10,
    )

    intent: str = Field(
        default="discussion",
        description="Primary intent: question, explanation, debugging, implementation, planning, discussion",
    )

    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies mentioned (e.g., python, mongodb, elasticsearch)",
        max_length=15,
    )

    entities: TurnEntities = Field(
        default_factory=TurnEntities,
        description="Structured entities (files, functions, projects, tools)",
    )

    # Optional high-level summary
    summary: Optional[str] = Field(
        None, description="One-sentence summary of the turn (optional)", max_length=500
    )

    # Extraction metadata
    extracted_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this metadata was extracted",
    )

    extractor_model: str = Field(default="unknown", description="Model used for extraction")


# ===== Metadata Extractor =====


class MetadataExtractor:
    """Extract structured metadata from chat turns using LLM."""

    def __init__(
        self,
        mongodb_uri: str = "mongodb://localhost:27017",
        mongodb_db: str = "chat_analytics",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
    ):
        """Initialize metadata extractor.

        Args:
            mongodb_uri: MongoDB connection URI
            mongodb_db: MongoDB database name
            qdrant_host: Qdrant host
            qdrant_port: Qdrant port

        """
        # MongoDB setup
        self.mongo_client = MongoClient(mongodb_uri)
        self.mongo_db = self.mongo_client[mongodb_db]
        self.turns_collection = self.mongo_db["turns"]
        self.metadata_collection = self.mongo_db["turn_metadata"]

        # Create indexes
        self.metadata_collection.create_index("turn_id", unique=True)
        self.metadata_collection.create_index("topics")
        self.metadata_collection.create_index("intent")
        self.metadata_collection.create_index("technologies")

        # Qdrant setup
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = "chat_turns"

        # Get embedding client
        self.embedding_client = get_embedding()
        embedding_dim = self.embedding_client.dimension

        # Create Qdrant collection if it doesn't exist
        try:
            self.qdrant_client.get_collection(self.collection_name)
            logger.info(f"Using existing Qdrant collection: {self.collection_name}")
        except Exception:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name} (dim={embedding_dim})")

        # Get LLM for extraction - use load balancing for optimal throughput
        # Prefer fastest LLM with sufficient context for metadata extraction
        self.llm = get_lm(min_context=8000, prefer_fastest=True)
        logger.info(
            f"MetadataExtractor initialized with LLM: {self.llm.spec.name} ({self.llm.spec.capabilities['speed_tokens_per_sec']} tok/s), Embedding: {self.embedding_client.name}"
        )

    def build_extraction_prompt(self, turn: Dict[str, Any]) -> str:
        """Build prompt for metadata extraction.

        Args:
            turn: Turn document from MongoDB

        Returns:
            Extraction prompt

        """
        user_text = turn.get("user", {}).get("text", "")
        assistant_text = turn.get("assistant", {}).get("text", "")

        # Smart truncation - dynamically derive from LLM spec instead of hardcoding
        # Get effective limits from LLM spec, fallback to safe defaults
        max_tokens = self.llm.spec.max_tokens  # type: ignore
        max_context = getattr(self.llm.spec, "max_context", max_tokens // 2)
        max_sequence_length = getattr(self.llm.spec, "max_sequence_length", max_tokens // 4)

        # Calculate reasonable token limits with safety margin
        # Use 90% of max_tokens for generation, 95% of max_context for safety
        generation_limit = int(max_tokens * 0.9)
        context_limit = int(max_context * 0.95)

        # Conservative character limit: 4 chars per token (adjustable)
        max_chars_per_message = max(generation_limit * 4, 8000)

        print(
            f"Using dynamic limits: max_tokens={max_tokens}, context_limit={context_limit}, generation_limit={generation_limit}, max_chars={max_chars_per_message}"
        )

        # Override for config loading
        self.max_tokens = max_tokens
        self.max_context = context_limit
        self.max_chars_per_message = max_chars_per_message

        if len(user_text) > max_chars_per_message:
            user_text = user_text[:max_chars_per_message] + "... [truncated]"
        if len(assistant_text) > max_chars_per_message:
            assistant_text = assistant_text[:max_chars_per_message] + "... [truncated]"

        prompt = f"""Extract structured metadata from this conversation turn.

USER MESSAGE:
{user_text}

ASSISTANT MESSAGE:
{assistant_text}

Extract the following metadata:

1. **topics**: List of 3-10 organic topic tags (lowercase, hyphen-separated)
   - Examples: "maxwell-architecture", "bm25-search", "chat-indexing", "debugging-import-errors"
   - Be specific and technical
   - Capture key themes and concepts discussed

2. **intent**: Primary intent of the conversation (choose ONE):
   - "question": User asking for help/clarification
   - "explanation": Assistant explaining a concept
   - "debugging": Troubleshooting errors or issues
   - "implementation": Building/coding something
   - "planning": Architectural or design decisions
   - "discussion": General discussion or brainstorming

3. **technologies**: List of technologies/tools mentioned
   - Examples: "python", "mongodb", "elasticsearch", "bm25", "docker"
   - Include programming languages, databases, libraries, frameworks
   - Lowercase

4. **entities**:
   - files: File names mentioned (e.g., "bm25_search.py", "turn_indexer.py")
   - functions: Functions/classes mentioned (e.g., "BM25Searcher", "search()")
   - projects: Project names (e.g., "maxwell", "professional-log")
   - tools: Specific tools/libraries (e.g., "rank-bm25", "pymongo")

5. **summary**: One-sentence summary of what happened in this turn (optional, max 200 chars)

Return ONLY a valid JSON object matching this schema:
{{
  "topics": ["topic1", "topic2", ...],
  "intent": "question|explanation|debugging|implementation|planning|discussion",
  "technologies": ["tech1", "tech2", ...],
  "entities": {{
    "files": ["file1.py", ...],
    "functions": ["Function1", ...],
    "projects": ["project1", ...],
    "tools": ["tool1", ...]
  }},
  "summary": "One sentence summary"
}}

Return ONLY the JSON, no other text."""

        return prompt

    def extract(self, turn_id: str, force_refresh: bool = False) -> Optional[TurnMetadata]:
        """Extract metadata for a turn.

        Args:
            turn_id: Turn ID to extract metadata for
            force_refresh: Force re-extraction even if cached

        Returns:
            TurnMetadata object, or None if extraction failed

        """
        # Check cache first
        if not force_refresh:
            cached = self.metadata_collection.find_one({"turn_id": turn_id})
            if cached:
                logger.debug(f"Using cached metadata for {turn_id}")
                # Convert MongoDB doc to TurnMetadata
                try:
                    return TurnMetadata(**cached["metadata"])
                except Exception as e:
                    logger.warning(f"Failed to parse cached metadata: {e}")

        # Get turn from database
        turn = self.turns_collection.find_one({"turn_id": turn_id})
        if not turn:
            logger.error(f"Turn not found: {turn_id}")
            return None

        # Build extraction prompt
        prompt = self.build_extraction_prompt(turn)

        # Extract with LLM
        try:
            logger.info(f"Extracting metadata for {turn_id} with {self.llm.spec.name}")
            # Use model's full max tokens capability
            response = self.llm.generate(
                prompt, max_tokens=self.llm.spec.max_tokens, temperature=0.1  # type: ignore
            )

            # Parse JSON response
            response_text = response.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            metadata_dict = json.loads(response_text)

            # Add extraction metadata
            metadata_dict["extractor_model"] = self.llm.spec.name
            metadata_dict["extracted_at"] = datetime.now().isoformat()

            # Validate with Pydantic
            metadata = TurnMetadata(**metadata_dict)

            # Cache metadata in MongoDB
            self.metadata_collection.update_one(
                {"turn_id": turn_id},
                {
                    "$set": {
                        "turn_id": turn_id,
                        "metadata": metadata.model_dump(),
                        "updated_at": datetime.now(),
                    }
                },
                upsert=True,
            )

            # Create embedding from topics + summary
            topics_str = " ".join(metadata.topics)
            summary_str = metadata.summary or ""
            embedding_text = f"{topics_str}. {summary_str}".strip()

            embedding = self.embedding_client.embed(embedding_text)
            if not isinstance(embedding, list):
                embedding = embedding.tolist()

            # Embedding is now logged in LLM pool, no need for separate logging

            # Store embedding in Qdrant
            point = PointStruct(
                id=hash(turn_id) & 0x7FFFFFFFFFFFFFFF,  # Convert to positive int
                vector=embedding,
                payload={
                    "turn_id": turn_id,
                    "topics": metadata.topics,
                    "summary": summary_str,
                    "intent": metadata.intent,
                    "source": turn.get("source", "unknown"),
                    "conversation_title": turn.get("conversation_title", ""),
                    "technologies": metadata.technologies,
                },
            )
            self.qdrant_client.upsert(collection_name=self.collection_name, points=[point])

            logger.info(f"✓ Extracted metadata and embedded for {turn_id}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to extract metadata for {turn_id}: {e}", exc_info=True)
            return None

    def extract_batch(
        self, turn_ids: List[str], force_refresh: bool = False
    ) -> Dict[str, Optional[TurnMetadata]]:
        """Extract metadata for multiple turns.

        Args:
            turn_ids: List of turn IDs
            force_refresh: Force re-extraction even if cached

        Returns:
            Dictionary mapping turn_id -> TurnMetadata

        """
        results = {}
        for turn_id in turn_ids:
            results[turn_id] = self.extract(turn_id, force_refresh=force_refresh)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get metadata extraction statistics.

        Returns:
            Dictionary with stats

        """
        total_turns = self.turns_collection.count_documents({})
        extracted_count = self.metadata_collection.count_documents({})

        # Count by intent
        intents = list(
            self.metadata_collection.aggregate(
                [{"$group": {"_id": "$metadata.intent", "count": {"$sum": 1}}}]
            )
        )

        # Most common topics
        topics = list(
            self.metadata_collection.aggregate(
                [
                    {"$unwind": "$metadata.topics"},
                    {"$group": {"_id": "$metadata.topics", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 20},
                ]
            )
        )

        # Most common technologies
        technologies = list(
            self.metadata_collection.aggregate(
                [
                    {"$unwind": "$metadata.technologies"},
                    {"$group": {"_id": "$metadata.technologies", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 20},
                ]
            )
        )

        return {
            "total_turns": total_turns,
            "extracted_count": extracted_count,
            "coverage": extracted_count / total_turns if total_turns > 0 else 0,
            "intents": {item["_id"]: item["count"] for item in intents},
            "top_topics": [(item["_id"], item["count"]) for item in topics],
            "top_technologies": [(item["_id"], item["count"]) for item in technologies],
        }


# ===== CLI Interface =====


def extract_cli(turn_id: str, force_refresh: bool = False):
    """CLI interface for metadata extraction.

    Args:
        turn_id: Turn ID to extract metadata for
        force_refresh: Force re-extraction even if cached

    """
    extractor = MetadataExtractor()
    metadata = extractor.extract(turn_id, force_refresh=force_refresh)

    if metadata:
        if metadata.summary:
            pass
    else:
        pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract metadata from chat turns")
    parser.add_argument("turn_id", type=str, help="Turn ID to extract metadata for")
    parser.add_argument("--force", action="store_true", help="Force re-extraction even if cached")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    extract_cli(args.turn_id, force_refresh=args.force)
