"""Chat workflow package for Maxwell.

Provides workflows for chat processing:
- chat_incremental: Incremental processing with deduplication
- chat_backup: Backup and restore functionality
- chat_semantic_search: Semantic search with Qdrant
- chat_bm25_search: BM25 keyword search
- metadata_extractor: Metadata extraction and quality control

Note: Chat workflows require optional dependencies.
Install with: pip install maxwell-demon[chat]

Usage:
    from maxwell.workflows.chat import (
        RegisteredIncrementalChatWorkflow,
        RegisteredChatBackupWorkflow,
        ChatSemanticSearchWorkflow,
        ChatBM25SearchWorkflow,
        MetadataExtractor
    )
"""

import logging

logger = logging.getLogger(__name__)

# Try to import chat workflows - only available if optional dependencies installed
__all__ = []

try:
    from .bm25_search import BM25Searcher, ChatBM25SearchWorkflow  # noqa: F401

    __all__.extend(["BM25Searcher", "ChatBM25SearchWorkflow"])
except ImportError as e:
    logger.debug(f"BM25 search not available (missing dependencies): {e}")

try:
    from .incremental_processor import RegisteredIncrementalChatWorkflow  # noqa: F401

    __all__.append("RegisteredIncrementalChatWorkflow")
except ImportError as e:
    logger.debug(f"Incremental processor not available (missing dependencies): {e}")

try:
    from .metadata_extractor import MetadataExtractor, TurnMetadata  # noqa: F401

    __all__.extend(["MetadataExtractor", "TurnMetadata"])
except ImportError as e:
    logger.debug(f"Metadata extractor not available (missing dependencies): {e}")

try:
    from .parsers import ChatGPTParser, ClaudeParser, Message  # noqa: F401

    __all__.extend(["ChatGPTParser", "ClaudeParser", "Message"])
except ImportError as e:
    logger.debug(f"Parsers not available (missing dependencies): {e}")

try:
    from .semantic_search import ChatSemanticSearchWorkflow  # noqa: F401

    __all__.append("ChatSemanticSearchWorkflow")
except ImportError as e:
    logger.debug(f"Semantic search not available (missing dependencies): {e}")

# Inform user if no chat workflows loaded
if not __all__:
    logger.info("Chat workflows not available. Install with: pip install maxwell-demon[chat]")
