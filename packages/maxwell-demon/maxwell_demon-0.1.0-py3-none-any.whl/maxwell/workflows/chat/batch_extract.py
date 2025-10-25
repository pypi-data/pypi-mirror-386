"""Batch metadata extraction for all chat turns.

Processes all 5,812 turns to extract metadata and embeddings.
Stores metadata in MongoDB and embeddings in Qdrant.

Usage:
    python -m maxwell.workflows.implementations.chat.batch_extract

Progress tracking:
    - Shows progress every 100 turns
    - Saves intermediate results
    - Handles failures gracefully
"""

__all__ = ["batch_extract_all"]

import logging
import time
from pathlib import Path
from typing import Optional

from pymongo import MongoClient

from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


def batch_extract_all(
    mongodb_uri: str = "mongodb://localhost:27017",
    mongodb_db: str = "chat_analytics",
    limit: Optional[int] = None,
    skip_existing: bool = True,
) -> None:
    """Extract metadata and embeddings for all turns.

    Args:
        mongodb_uri: MongoDB connection URI
        mongodb_db: MongoDB database name
        limit: Optional limit on number of turns to process (for testing)
        skip_existing: Skip turns that already have metadata cached

    """
    # Set session ID for logging
    import datetime
    import os

    if not os.getenv("LLM_SESSION_ID"):
        session_id = f"batch_extract_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.environ["LLM_SESSION_ID"] = session_id
        logger.info(f"Set LLM session ID: {session_id}")

        # Prepend legacy logs if they exist
        log_dir = Path.cwd() / ".maxwell" / "logs"
        legacy_file = log_dir / "legacy_batch_extract_20251021.jsonl"
        current_file = log_dir / f"{session_id}.jsonl"

        if legacy_file.exists():
            logger.info(f"Prepending legacy logs from {legacy_file}")
            # Copy legacy content to new session file
            import shutil

            shutil.copy2(legacy_file, current_file)
            logger.info(f"Copied {legacy_file.stat().st_size:,} bytes to {current_file}")
        else:
            # Create empty file to start logging
            current_file.touch()
    else:
        logger.info(f"Using existing LLM session ID: {os.getenv('LLM_SESSION_ID')}")

    # Setup
    mongo_client = MongoClient(mongodb_uri)
    mongo_db = mongo_client[mongodb_db]
    turns_collection = mongo_db["turns"]
    metadata_collection = mongo_db["turn_metadata"]

    extractor = MetadataExtractor(mongodb_uri=mongodb_uri, mongodb_db=mongodb_db)

    # Get all turn IDs
    logger.info("Fetching turn IDs from MongoDB...")
    if skip_existing:
        # Get turns without metadata
        existing_turn_ids = set(
            doc["turn_id"] for doc in metadata_collection.find({}, {"turn_id": 1})
        )
        all_turns = list(turns_collection.find({}, {"turn_id": 1}))
        turn_ids = [t["turn_id"] for t in all_turns if t["turn_id"] not in existing_turn_ids]
        logger.info(
            f"Found {len(all_turns)} total turns, {len(existing_turn_ids)} already processed"
        )
        logger.info(f"Processing {len(turn_ids)} remaining turns")
    else:
        turn_ids = [t["turn_id"] for t in turns_collection.find({}, {"turn_id": 1})]
        logger.info(f"Processing all {len(turn_ids)} turns")

    if limit:
        turn_ids = turn_ids[:limit]
        logger.info(f"Limited to first {limit} turns")

    if not turn_ids:
        logger.info("No turns to process!")
        return

    # Process turns with load balancing across multiple LLMs
    success_count = 0
    fail_count = 0
    start_time = time.time()

    # Get all available LLMs for parallel processing
    from maxwell.lm_pool import LLMClient, LLMPool

    pool = LLMPool.from_registry()
    available_llms = list(pool.llms.values())
    logger.info(
        f"Load balancing across {len(available_llms)} LLMs: {[llm.name for llm in available_llms]}"
    )

    # Create multiple extractors, one per LLM
    extractors = []
    for llm_spec in available_llms:
        extractor = MetadataExtractor(mongodb_uri=mongodb_uri, mongodb_db=mongodb_db)
        extractor.llm = LLMClient(llm_spec)  # Override with specific LLM
        extractors.append(extractor)
        logger.info(
            f"Created extractor for {llm_spec.name} ({llm_spec.capabilities['speed_tokens_per_sec']} tok/s)"
        )

    # Use round-robin assignment of turns to extractors
    from itertools import cycle

    extractor_cycle = cycle(extractors)

    # Process turns in parallel using threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def extract_turn(turn_id: str, extractor_instance: MetadataExtractor):
        """Extract metadata for a single turn using the specified extractor."""
        try:
            metadata = extractor_instance.extract(turn_id, force_refresh=not skip_existing)
            return turn_id, metadata, None
        except Exception as e:
            return turn_id, None, str(e)

    # Submit all turns for parallel processing
    with ThreadPoolExecutor(max_workers=len(extractors)) as executor:
        # Create future tasks
        future_to_turn = {}
        for turn_id in turn_ids:
            extractor = next(extractor_cycle)
            future = executor.submit(extract_turn, turn_id, extractor)
            future_to_turn[future] = turn_id

        # Process completed tasks
        for future in as_completed(future_to_turn):
            turn_id, metadata, error = future.result()
            if metadata:
                success_count += 1
            else:
                fail_count += 1
                if error:
                    logger.warning(f"Failed to extract {turn_id}: {error}")

    # Final stats
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("BATCH EXTRACTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total processed: {len(turn_ids)}")
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info(f"Time: {elapsed/60:.1f} minutes")
    logger.info(f"Rate: {len(turn_ids)/elapsed:.1f} turns/sec")

    # Show collection stats
    total_metadata = metadata_collection.count_documents({})
    logger.info(f"\nTotal metadata in MongoDB: {total_metadata:,}")

    # Show Qdrant stats
    try:
        from qdrant_client import QdrantClient

        qdrant = QdrantClient(host="localhost", port=6333)
        info = qdrant.get_collection("chat_turns")
        logger.info(f"Total embeddings in Qdrant: {info.points_count:,}")
    except Exception as e:
        logger.warning(f"Could not get Qdrant stats: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch extract metadata for all chat turns")
    parser.add_argument("--limit", type=int, help="Limit number of turns to process (for testing)")
    parser.add_argument("--force", action="store_true", help="Re-extract even if metadata exists")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    batch_extract_all(limit=args.limit, skip_existing=not args.force)
