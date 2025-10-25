"""Incremental processing workflow for chat files.

Registers as "chat_incremental" workflow in Maxwell's registry.
Leverages Maxwell's content-addressable storage for deduplication:
- Tracks processed files in .maxwell/chat_registry.json
- Uses file content hashes (SHA256) to detect changes
- Only processes new/modified chat files
- Integrates with existing BaseWorkflow system

Usage:
    from maxwell.workflows.chat.incremental_processor import IncrementalChatWorkflow

    workflow = IncrementalChatWorkflow()
    result = workflow.run(chat_root=Path("~/.claude/projects"))
"""

__all__ = ["IncrementalChatWorkflow"]

import hashlib
import json
import logging
import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pymongo import MongoClient

from maxwell.registry import register_workflow
from maxwell.storage import ContentHasher
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowMetrics,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)
from maxwell.workflows.chat.parsers import ChatGPTParser, ClaudeParser


@dataclass
class ChatProcessingInputs:
    """Typed inputs for chat processing workflow."""

    chatgpt_path: Optional[str] = None
    claude_backup_path: Optional[str] = None
    claude_projects_path: Optional[str] = None
    dry_run: bool = False


@dataclass
class ChatProcessingOutputs:
    """Typed outputs for chat processing workflow."""

    processing_stats: Dict[str, Any]
    turns_processed: int
    sources_processed: int


logger = logging.getLogger(__name__)


class IncrementalChatProcessor:
    """Incremental processor for chat logs with deduplication."""

    def __init__(
        self,
        chat_root: Path,
        maxwell_root: Optional[Path] = None,
        source_type: str = "claude",
        mongodb_uri: str = "mongodb://localhost:27017",
    ):
        """Initialize incremental processor.

        Args:
            chat_root: Root directory containing chat files
            maxwell_root: Maxwell project root (defaults to current working directory)
            source_type: Type of source ("claude", "chatgpt", "claude-backup")
            mongodb_uri: MongoDB connection URI

        """
        self.chat_root = Path(chat_root).resolve()
        self.maxwell_root = Path(maxwell_root).resolve() if maxwell_root else Path.cwd().resolve()
        self.source_type = source_type
        self.machine_hostname = socket.gethostname()

        # Maxwell storage paths
        self.maxwell_dir = self.maxwell_root / ".maxwell"
        self.registry_file = self.maxwell_dir / f"chat_registry_{source_type}.json"

        # Use Maxwell's content hasher for consistency
        self.hasher = ContentHasher()

        # MongoDB connection
        self.mongo_client = MongoClient(mongodb_uri)
        self.mongo_db = self.mongo_client["chat_analytics"]
        self.turns_collection = self.mongo_db["turns"]

        # Create indexes for deduplication
        self.turns_collection.create_index("turn_id", unique=True)
        self.turns_collection.create_index("source")
        self.turns_collection.create_index("conversation_id")

        # Ensure .maxwell directory exists
        self.maxwell_dir.mkdir(parents=True, exist_ok=True)

        # Load processed file registry
        self.registry = self._load_registry()

        logger.info("Initialized incremental chat processor")
        logger.info(f"Source type: {self.source_type}")
        logger.info(f"Chat root: {self.chat_root}")
        logger.info(f"Maxwell root: {self.maxwell_root}")
        logger.info(f"Machine: {self.machine_hostname}")
        logger.info(f"Previously processed files: {len(self.registry)}")

    def _load_registry(self) -> Dict[str, Dict]:
        """Load registry of processed files."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
        return {}

    def _save_registry(self):
        """Save registry of processed files."""
        try:
            with open(self.registry_file, "w") as f:
                json.dump(self.registry, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate content hash using Maxwell's hasher."""
        try:
            # Use Maxwell's content hasher for consistency
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return self.hasher.hash_content(content)
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return ""

    def _should_process_file(self, file_path: Path) -> tuple[bool, str]:
        """Check if file should be processed based on registry and hash.

        Returns:
            (should_process, reason)

        """
        if not file_path.exists():
            return False, "File does not exist"

        if not file_path.suffix == ".jsonl":
            return False, "Not a JSONL file"

        # Get current file hash using Maxwell's hasher
        current_hash = self._get_file_hash(file_path)
        if not current_hash:
            return False, "Failed to calculate hash"

        # Check registry
        file_key = str(file_path.relative_to(self.chat_root))
        if file_key in self.registry:
            processed_info = self.registry[file_key]
            if processed_info.get("content_hash") == current_hash:
                # Check if processing was complete
                if processed_info.get("status") == "completed":
                    return False, f"Already processed (hash: {current_hash[:8]}...)"
                else:
                    return True, f"Previously incomplete (hash: {current_hash[:8]}...)"

        return True, f"New or modified (hash: {current_hash[:8]}...)"

    def _register_file(self, file_path: Path, status: str, metadata: Optional[Dict] = None):
        """Register file as processed with its hash and metadata."""
        file_key = str(file_path.relative_to(self.chat_root))
        content_hash = self._get_file_hash(file_path)

        self.registry[file_key] = {
            "content_hash": content_hash,
            "status": status,
            "processed_at": datetime.now().isoformat(),
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "metadata": metadata or {},
        }

        self._save_registry()

    def discover_chat_files(self) -> Set[Path]:
        """Discover all chat files in directory tree."""
        chat_files = set()

        if not self.chat_root.exists():
            logger.error(f"Chat root does not exist: {self.chat_root}")
            return chat_files

        # Different discovery patterns based on source type
        if self.source_type == "chatgpt":
            # ChatGPT uses conversations.json
            for json_file in self.chat_root.rglob("conversations.json"):
                chat_files.add(json_file)
            logger.info(f"Discovered {len(chat_files)} ChatGPT conversation files")
        else:
            # Claude uses JSONL files
            for jsonl_file in self.chat_root.rglob("*.jsonl"):
                chat_files.add(jsonl_file)
            logger.info(f"Discovered {len(chat_files)} JSONL files")

        return chat_files

    def get_file_stats(self, file_path: Path) -> Dict:
        """Get basic statistics about a chat file."""
        try:
            line_count = sum(1 for _ in open(file_path, "r", encoding="utf-8"))
            file_size = file_path.stat().st_size

            return {
                "line_count": line_count,
                "file_size_bytes": file_size,
                "file_size_mb": file_size / (1024 * 1024),
            }
        except Exception as e:
            logger.error(f"Error getting stats for {file_path}: {e}")
            return {"line_count": 0, "file_size_bytes": 0, "file_size_mb": 0}

    def _create_turn_id(self, source: str, file_path: str, message_index: int) -> str:
        """Create unique turn ID."""
        id_string = f"{source}:{file_path}:{message_index}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]

    def _process_claude_file(self, file_path: Path) -> int:
        """Process Claude JSONL file and load into MongoDB."""
        try:
            parser = ClaudeParser(file_path)
            messages = list(parser.parse())

            if not messages:
                logger.warning(f"No messages found in {file_path}")
                return 0

            # Extract project info from path
            relative_path = file_path.relative_to(self.chat_root)
            project_path = str(relative_path.parent)
            conversation_title = file_path.stem

            # Process each message as a turn
            turns_inserted = 0
            for i, message in enumerate(messages):
                if message.role not in ["user", "assistant"]:
                    continue

                # Create turn document
                turn_id = self._create_turn_id(self.source_type, str(file_path), i)

                turn_doc = {
                    "turn_id": turn_id,
                    "source": self.source_type,
                    "conversation_id": conversation_title,
                    "title": conversation_title,
                    "file_path": str(file_path),
                    "project_path": project_path,
                    "role": message.role,
                    "content": message.text,
                    "timestamp": message.timestamp,
                    "message_index": message.message_index,
                    "total_messages": len(messages),
                    "machine": self.machine_hostname,
                    "account": self._extract_account_from_path(file_path),
                    "loaded_at": datetime.utcnow().isoformat(),
                    "combined_text": f"[{message.role.upper()}]: {message.text}",
                    "char_count": message.char_count,
                    "token_count": message.token_count,
                }

                # Upsert to avoid duplicates
                self.turns_collection.update_one(
                    {"turn_id": turn_id}, {"$set": turn_doc}, upsert=True
                )
                turns_inserted += 1

            logger.info(f"[OK] Processed {file_path.name}: {turns_inserted} turns")
            return turns_inserted

        except Exception as e:
            logger.error(f"Failed to process Claude file {file_path}: {e}")
            return 0

    def _process_chatgpt_file(self, file_path: Path) -> int:
        """Process ChatGPT conversations.json file and load into MongoDB."""
        try:
            parser = ChatGPTParser(file_path)
            messages = list(parser.parse())

            if not messages:
                logger.warning(f"No messages found in {file_path}")
                return 0

            # Group messages by conversation
            conversations = {}
            for msg in messages:
                conv_id = msg.conversation_id
                if conv_id not in conversations:
                    conversations[conv_id] = []
                conversations[conv_id].append(msg)

            # Process each conversation
            turns_inserted = 0
            for conv_id, conv_messages in conversations.items():
                # Get conversation metadata
                first_msg = conv_messages[0] if conv_messages else None
                if not first_msg:
                    continue

                for i, message in enumerate(conv_messages):
                    if message.role not in ["user", "assistant"]:
                        continue

                    # Create turn document
                    turn_id = self._create_turn_id(
                        "chatgpt", str(file_path), len(conversations[conv_id]) + i
                    )

                    turn_doc = {
                        "turn_id": turn_id,
                        "source": "chatgpt",
                        "conversation_id": message.conversation_id,
                        "title": message.conversation_title,
                        "file_path": str(file_path),
                        "role": message.role,
                        "content": message.text,
                        "timestamp": message.timestamp,
                        "message_index": i,
                        "total_messages": len(conv_messages),
                        "machine": self.machine_hostname,
                        "account": self._extract_account_from_path(file_path),
                        "loaded_at": datetime.utcnow().isoformat(),
                        "combined_text": f"[{message.role.upper()}]: {message.text}",
                        "char_count": message.char_count,
                        "token_count": message.token_count,
                    }

                    # Upsert to avoid duplicates
                    self.turns_collection.update_one(
                        {"turn_id": turn_id}, {"$set": turn_doc}, upsert=True
                    )
                    turns_inserted += 1

            logger.info(f"[OK] Processed {file_path.name}: {turns_inserted} turns")
            return turns_inserted

        except Exception as e:
            logger.error(f"Failed to process ChatGPT file {file_path}: {e}")
            return 0

    def _extract_account_from_path(self, file_path: Path) -> str:
        """Extract account name from file path."""
        path_str = str(file_path)

        # Look for common account patterns
        if "users/" in path_str:
            users_idx = path_str.find("users/")
            after_users = path_str[users_idx + 6 :]
            account = after_users.split("/")[0]
            return account

        # Look for home directory pattern
        if "/home/" in path_str:
            home_idx = path_str.find("/home/")
            after_home = path_str[home_idx + 6 :]
            account = after_home.split("/")[0]
            return account

        # Default to current user
        return os.getenv("USER", "unknown")

    def run_incremental(self, dry_run: bool = False) -> Dict:
        """Run incremental analysis.

        Args:
            dry_run: If True, only analyze what would be processed

        Returns:
            Analysis statistics

        """
        discovered_files = self.discover_chat_files()

        stats = {
            "total_files": len(discovered_files),
            "new_files": 0,
            "modified_files": 0,
            "unchanged_files": 0,
            "processing_errors": 0,
            "files_to_process": [],
            "total_size_mb": 0,
        }

        logger.info("Analyzing files for incremental processing...")

        for file_path in sorted(discovered_files):
            should_process, reason = self._should_process_file(file_path)

            if should_process:
                file_stats = self.get_file_stats(file_path)
                relative_path = str(file_path.relative_to(self.chat_root))

                file_info = {
                    "path": relative_path,
                    "reason": reason,
                    "size_mb": file_stats["file_size_mb"],
                    "line_count": file_stats["line_count"],
                }

                stats["files_to_process"].append(file_info)
                stats["total_size_mb"] += file_stats["file_size_mb"]

                # Determine if new or modified
                if relative_path in self.registry:
                    stats["modified_files"] += 1
                else:
                    stats["new_files"] += 1

                if not dry_run:
                    logger.info(f"Processing {file_path.name}: {reason}")
                    try:
                        # Mark as processing
                        self._register_file(file_path, "processing", file_stats)

                        # Process the file based on source type
                        if self.source_type in ["claude", "claude-backup"]:
                            turns_processed = self._process_claude_file(file_path)
                        elif self.source_type == "chatgpt":
                            turns_processed = self._process_chatgpt_file(file_path)
                        else:
                            logger.warning(f"Unknown source type: {self.source_type}")
                            turns_processed = 0

                        # Mark as completed
                        self._register_file(
                            file_path,
                            "completed",
                            {**file_stats, "turns_processed": turns_processed},
                        )
                        logger.info(
                            f"[OK] Completed processing {file_path.name}: {turns_processed} turns"
                        )

                    except Exception as e:
                        logger.error(f"Failed to process {file_path}: {e}")
                        self._register_file(file_path, "error", {"error": str(e)})
                        stats["processing_errors"] += 1
            else:
                stats["unchanged_files"] += 1
                logger.debug(f"Skipping {file_path.name}: {reason}")

        if dry_run:
            logger.info("DRY RUN - No files were actually processed")

        return stats

    def get_registry_status(self) -> Dict:
        """Get current registry status."""
        total_files = len(self.registry)
        completed_files = sum(
            1 for info in self.registry.values() if info.get("status") == "completed"
        )
        processing_files = sum(
            1 for info in self.registry.values() if info.get("status") == "processing"
        )
        error_files = sum(1 for info in self.registry.values() if info.get("status") == "error")

        return {
            "total_files": total_files,
            "completed": completed_files,
            "processing": processing_files,
            "errors": error_files,
            "completion_rate": completed_files / total_files if total_files > 0 else 0,
        }


def print_analysis_summary(stats: Dict):
    """Print formatted analysis summary."""
    print("\n" + "=" * 60)
    print("INCREMENTAL CHAT PROCESSING ANALYSIS")
    print("=" * 60)
    print(f"Total JSONL files discovered: {stats['total_files']}")
    print(f"Files to process: {stats['new_files'] + stats['modified_files']}")
    print(f"  New files: {stats['new_files']}")
    print(f"  Modified files: {stats['modified_files']}")
    print(f"Unchanged files: {stats['unchanged_files']}")
    print(f"Total size to process: {stats['total_size_mb']:.1f}MB")
    print(f"Processing errors: {stats['processing_errors']}")

    if stats["files_to_process"]:
        print("\nFiles that would be processed:")
        for file_info in stats["files_to_process"][:10]:  # Show first 10
            print(
                f"  {file_info['path']} ({file_info['size_mb']:.1f}MB, {file_info['line_count']} lines) - {file_info['reason']}"
            )

        if len(stats["files_to_process"]) > 10:
            print(f"  ... and {len(stats['files_to_process']) - 10} more files")
    else:
        print("\n[OK] All files are up to date!")

    print("=" * 60)


class IncrementalChatWorkflow(BaseWorkflow):
    """Incremental chat processing workflow that integrates with Maxwell's registry."""

    def __init__(self):
        self.workflow_id = "chat_upsert"
        self.name = "Chat Upsert Processor"
        self.description = "Upserts chat files into MongoDB with deduplication"
        self.version = "1.0"
        super().__init__()

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=3600,  # 1 hour
            cache_results=True,
            parameters={
                "chat_root": str(root_dir),
                "maxwell_root": str(root_dir),
            },
        )

    def get_required_inputs(self) -> List[str]:
        """Get required input field names."""
        return []  # No required inputs - all sources are optional

    def get_produced_outputs(self) -> List[str]:
        """Get output field names this workflow produces."""
        return ["processing_stats", "turns_processed", "sources_processed"]

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        """Define CLI parameters for maxwell chat-incremental command.

        CLI Usage:
            maxwell chat-incremental --source-path /path/to/chats --type claude [--dry-run]
            maxwell chat-incremental --source-path /path/to/chatgpt --type chatgpt [--dry-run]

        Examples:
            # Process Claude projects (default)
            maxwell chat-incremental

            # Process specific source with type
            maxwell chat-incremental --source-path ~/Documents/chatgpt --type chatgpt
            maxwell chat-incremental --source-path ~/Documents/claude-backup --type claude

            # Dry run to see what would be processed
            maxwell chat-incremental --dry-run

        """
        return [
            {
                "name": "source_path",
                "type": str,
                "required": False,
                "help": "Path to chat source directory (default: ~/.claude/projects)",
                "default": "~/.claude/projects",
            },
            {
                "name": "type",
                "type": str,
                "required": False,
                "help": "Source type: claude or chatgpt (auto-detect if not specified)",
                "choices": ["claude", "chatgpt"],
            },
            {
                "name": "dry_run",
                "type": bool,
                "required": False,
                "help": "Only analyze what would be processed without making changes",
                "default": False,
            },
            {
                "name": "limit",
                "type": int,
                "required": False,
                "help": "Limit number of turns to process (for smoke testing)",
                "default": None,
            },
        ]

    def execute(self, project_root: Path, context: Dict) -> WorkflowResult:
        """Execute incremental chat processing for all sources."""
        start_time = time.time()

        # Parse CLI parameters from context
        source_path = context.get("source_path", "~/.claude/projects")
        source_type = context.get("type")  # claude, chatgpt, or None for auto-detect

        # Build sources list from CLI parameters
        sources = []
        source_path = Path(source_path).expanduser()

        if source_type:
            # Use specified type
            sources.append(
                {
                    "name": f"{source_type}-specified",
                    "path": source_path,
                    "source_type": source_type,
                }
            )
        else:
            # Auto-detect: if conversations.json exists, assume ChatGPT, else Claude
            if (source_path / "conversations.json").exists():
                sources.append(
                    {"name": "chatgpt-detected", "path": source_path, "source_type": "chatgpt"}
                )
            else:
                sources.append(
                    {"name": "claude-detected", "path": source_path, "source_type": "claude"}
                )

        inputs = ChatProcessingInputs(
            chatgpt_path=str(source_path) if source_type == "chatgpt" else None,
            claude_backup_path=str(source_path) if source_type == "claude" else None,
            claude_projects_path=str(source_path) if not source_type else None,
            dry_run=context.get("dry_run", False),
        )

        maxwell_root = project_root
        total_stats = {
            "total_sources": len(sources),
            "sources_processed": 0,
            "total_files": 0,
            "total_turns_processed": 0,
            "total_errors": 0,
            "source_details": [],
        }

        logger.info(f"🚀 Starting incremental chat processing for {len(sources)} sources...")

        # Process each source
        for source in sources:
            source_name = source["name"]
            source_path = source["path"]

            if not source_path.exists():
                logger.warning(f"Source path does not exist: {source_path}")
                continue

            logger.info(f"Processing source: {source_name} from {source_path}")

            try:
                # Initialize processor for this source type
                processor = IncrementalChatProcessor(
                    chat_root=source_path,
                    maxwell_root=maxwell_root,
                    source_type=source["source_type"],
                )

                # Run incremental processing
                stats = processor.run_incremental(dry_run=inputs.dry_run)

                # Count total turns processed (need to check registry for this)
                turns_processed = sum(
                    info.get("metadata", {}).get("turns_processed", 0)
                    for info in processor.registry.values()
                    if info.get("status") == "completed"
                )

                source_detail = {
                    "source": source_name,
                    "path": str(source_path),
                    "total_files": stats["total_files"],
                    "new_files": stats["new_files"],
                    "modified_files": stats["modified_files"],
                    "turns_processed": turns_processed,
                    "processing_errors": stats["processing_errors"],
                }

                total_stats["source_details"].append(source_detail)
                total_stats["total_files"] += stats["total_files"]
                total_stats["total_turns_processed"] += turns_processed
                total_stats["total_errors"] += stats["processing_errors"]
                total_stats["sources_processed"] += 1

                logger.info(
                    f"[OK] {source_name}: {stats['new_files'] + stats['modified_files']} files, {turns_processed} turns"
                )

            except Exception as e:
                logger.error(f"Failed to process source {source_name}: {e}")
                total_stats["total_errors"] += 1

        # Create result
        end_time = time.time()
        status = (
            WorkflowStatus.COMPLETED if total_stats["total_errors"] == 0 else WorkflowStatus.FAILED
        )

        # Create metrics
        metrics = WorkflowMetrics(
            start_time=start_time,
            end_time=end_time,
            files_processed=total_stats["total_files"],
            errors_encountered=total_stats["total_errors"],
        )
        metrics.finalize()

        # Run batch extract if not dry run
        limit = context.get("limit")
        if not inputs.dry_run and status == WorkflowStatus.COMPLETED:

            logger.info("🚀 Running batch extract for embeddings...")
            try:
                # Simple batch extract for embeddings directly here
                from pymongo import MongoClient
                from qdrant_client import QdrantClient
                from qdrant_client.http.models import Distance, PointStruct, VectorParams

                from maxwell.lm_pool import get_embedding

                client = MongoClient("mongodb://localhost:27017")
                db = client.chat_turns
                collection = db.turns

                # Build query filter
                query = {}
                if limit:
                    query = {"$or": [{"role": "user"}, {"role": "assistant"}]}

                # Get turns to process
                cursor = collection.find(query).sort("timestamp", -1)
                if limit:
                    cursor = cursor.limit(limit)

                turns_to_process = list(cursor)
                logger.info(f"Creating embeddings for {len(turns_to_process)} turns...")

                # Create embeddings
                embedding_client = get_embedding()
                qdrant = QdrantClient(url="http://localhost:6333")

                # Ensure collection exists
                collection_name = "chat_turns"
                try:
                    qdrant.get_collection(collection_name)
                except Exception:
                    qdrant.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=2560, distance=Distance.COSINE),
                    )

                points = []
                for turn in turns_to_process:
                    text = turn.get("content", "")
                    if text and len(text.strip()) > 10:
                        # Create embedding
                        embedding = embedding_client.create_embedding(text)  # type: ignore

                        points.append(
                            PointStruct(
                                id=turn["turn_id"],
                                vector=embedding,
                                payload={
                                    "turn_id": turn["turn_id"],
                                    "content": text[:500],  # First 500 chars for preview
                                    "role": turn.get("role"),
                                    "source": turn.get("source"),
                                    "timestamp": turn.get("timestamp"),
                                    "conversation_id": turn.get("conversation_id"),
                                    "content_length": len(text),
                                },
                            )
                        )

                # Batch upsert to Qdrant
                if points:
                    qdrant.upsert(collection_name=collection_name, points=points)
                    logger.info(f"[OK] Created {len(points)} embeddings in Qdrant")
                    total_stats["embeddings_created"] = len(points)
                else:
                    logger.warning("[WARN] No valid content found for embeddings")

            except Exception as e:
                logger.error(f"[ERROR] Batch extract failed: {e}")
                import traceback

                traceback.print_exc()

        # Create result using BaseWorkflow method
        result = WorkflowResult(
            workflow_id=self.workflow_id,
            status=status,
            metrics=metrics,
            artifacts={
                "processing_summary": total_stats,
                "sources_processed": total_stats["sources_processed"],
                "total_files_processed": total_stats["total_files"],
                "total_turns_processed": total_stats["total_turns_processed"],
                "total_errors": total_stats["total_errors"],
                "dry_run": context.get("dry_run", False),
                "limit": limit,
                "data_quality_completed": "data_quality_issues" in total_stats,
                "embeddings_created": total_stats.get("embeddings_created", 0),
            },
            error_message=(
                None
                if status == WorkflowStatus.COMPLETED
                else f"Processing completed with {total_stats['total_errors']} errors"
            ),
        )

        return result


# Register the workflow in Maxwell's registry
@register_workflow
class RegisteredIncrementalChatWorkflow(IncrementalChatWorkflow):
    """Registered version of IncrementalChatWorkflow."""

    def __init__(self):
        # Call parent __init__ to set workflow_id
        super().__init__()
