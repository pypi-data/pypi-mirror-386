"""Backup workflow for MongoDB and Qdrant chat data.

Registers as "chat_backup" workflow in Maxwell's registry.
Provides automated backup and recovery for chat analytics data:
- MongoDB metadata and turn collections
- Qdrant vector collections
- Configurable retention policies
- Incremental backup support

Usage:
    from maxwell.workflows.chat.backup_strategy import ChatBackupWorkflow

    workflow = ChatBackupWorkflow()
    result = workflow.run(backup_type="full", include_qdrant=True, include_mongodb=True)
"""

__all__ = [
    "ChatBackupManager",
    "ChatBackupWorkflow",
    "ChatBackupInputs",
    "ChatBackupOutputs",
    "MongoDBCollectionBackupResult",
    "QdrantCollectionBackupResult",
    "FullBackupResult",
    "RestoreResult",
    "BackupListResult",
    "print_backup_summary",
]

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pymongo
from qdrant_client import QdrantClient

from maxwell.registry import register_workflow
from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowConfig,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowPriority,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class MongoDBCollectionBackupResult:
    """Result from backing up a MongoDB collection."""

    collection: str
    document_count: int = 0
    file_size_mb: float = 0.0
    backup_file: str = ""
    error: Optional[str] = None


@dataclass
class QdrantCollectionBackupResult:
    """Result from backing up a Qdrant collection."""

    collection: str
    points_count: int = 0
    file_size_mb: float = 0.0
    backup_file: str = ""
    error: Optional[str] = None


@dataclass
class MongoDBBackupStats:
    """MongoDB backup statistics."""

    collections: List[MongoDBCollectionBackupResult] = field(default_factory=list)


@dataclass
class QdrantBackupStats:
    """Qdrant backup statistics."""

    collections: List[QdrantCollectionBackupResult] = field(default_factory=list)


@dataclass
class FullBackupResult:
    """Result from full backup operation."""

    backup_type: str
    timestamp: str
    backup_dir: str
    mongodb: MongoDBBackupStats
    qdrant: QdrantBackupStats
    total_size_mb: float
    success: bool


@dataclass
class RestoreResult:
    """Result from restore operation."""

    backup_timestamp: str
    mongodb: MongoDBBackupStats
    qdrant: QdrantBackupStats
    dry_run: bool
    success: bool


@dataclass
class BackupListResult:
    """Result from listing backups."""

    total_count: int
    total_size_mb: float
    latest_backup: Optional[str]
    backup_root: str = ""


@dataclass(frozen=True)
class ChatBackupInputs(WorkflowInputs):
    """Input schema for chat backup workflow."""

    backup_type: str = "full"
    include_qdrant: bool = True
    include_mongodb: bool = True
    dry_run: bool = False


@dataclass(frozen=True)
class ChatBackupOutputs(WorkflowOutputs):
    """Output schema for chat backup workflow."""

    backup_dir: str
    total_size_mb: float
    collections_backed_up: int
    success: bool


class ChatBackupManager:
    """Backup and recovery manager for chat analytics data."""

    def __init__(
        self,
        mongodb_uri: str = "mongodb://localhost:27017",
        mongodb_db: str = "chat_analytics",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        backup_root: Optional[Path] = None,
    ):
        """Initialize backup manager.

        Args:
            mongodb_uri: MongoDB connection URI
            mongodb_db: MongoDB database name
            qdrant_host: Qdrant host
            qdrant_port: Qdrant port
            backup_root: Root directory for backups (defaults to ~/.maxwell/backups)

        """
        self.mongodb_uri = mongodb_uri
        self.mongodb_db = mongodb_db
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port

        # Backup storage
        if backup_root:
            self.backup_root = Path(backup_root)
        else:
            # Use ~/.maxwell/backups by default
            self.backup_root = Path.home() / ".maxwell" / "backups"

        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_root / "backup_metadata.json"

        # Database connections
        self.mongo_client = None
        self.qdrant_client = None

        logger.info("Initialized backup manager")
        logger.info(f"Backup root: {self.backup_root}")

    def _connect_mongodb(self):
        """Connect to MongoDB."""
        if self.mongo_client is None:
            self.mongo_client = pymongo.MongoClient(self.mongodb_uri)
        return self.mongo_client

    def _connect_qdrant(self):
        """Connect to Qdrant."""
        if self.qdrant_client is None:
            self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        return self.qdrant_client

    def _create_backup_dir(self, backup_type: str = "full") -> Path:
        """Create backup directory with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / f"{backup_type}_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _get_backup_info(self) -> Dict:
        """Load backup metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load backup metadata: {e}")
        return {"backups": []}

    def _save_backup_info(self, backup_info: Dict):
        """Save backup metadata."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(backup_info, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")

    def backup_mongodb_collection(
        self, collection_name: str, backup_dir: Path
    ) -> MongoDBCollectionBackupResult:
        """Backup a single MongoDB collection to JSON."""
        try:
            client = self._connect_mongodb()
            db = client[self.mongodb_db]
            collection = db[collection_name]

            # Get all documents
            documents = list(collection.find({}))

            # Save to JSON file
            backup_file = backup_dir / f"{collection_name}.json"
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(documents, f, indent=2, default=str)

            result = MongoDBCollectionBackupResult(
                collection=collection_name,
                document_count=len(documents),
                file_size_mb=backup_file.stat().st_size / (1024 * 1024),
                backup_file=str(backup_file),
            )

            logger.info(
                f"Backed up {collection_name}: {result.document_count} documents ({result.file_size_mb:.1f}MB)"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to backup MongoDB collection {collection_name}: {e}")
            return MongoDBCollectionBackupResult(collection=collection_name, error=str(e))

    def backup_qdrant_collection(
        self, collection_name: str, backup_dir: Path
    ) -> QdrantCollectionBackupResult:
        """Backup a Qdrant collection to JSON."""
        try:
            client = self._connect_qdrant()

            # Get collection info
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count

            if points_count == 0:
                logger.info(f"Qdrant collection {collection_name} is empty, skipping backup")
                return QdrantCollectionBackupResult(
                    collection=collection_name,
                    points_count=0,
                    file_size_mb=0.0,
                )

            # Scroll through all points (with batch size to handle large collections)
            all_points = []
            scroll_result = client.scroll(collection_name=collection_name, limit=1000)

            points = scroll_result[0]  # points
            all_points.extend(points)

            # Continue scrolling if there are more points
            while len(points) == 1000:
                scroll_result = client.scroll(
                    collection_name=collection_name, limit=1000, offset=len(all_points)
                )
                points = scroll_result[0]
                all_points.extend(points)

            # Convert points to serializable format
            serializable_points = []
            for point in all_points:
                serializable_points.append(
                    {
                        "id": point.id,
                        "vector": (
                            point.vector.tolist()
                            if hasattr(point.vector, "tolist")
                            else point.vector
                        ),
                        "payload": point.payload,
                    }
                )

            # Save to JSON file
            backup_file = backup_dir / f"{collection_name}.json"
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(serializable_points, f, indent=2)

            result = QdrantCollectionBackupResult(
                collection=collection_name,
                points_count=len(all_points),
                file_size_mb=backup_file.stat().st_size / (1024 * 1024),
                backup_file=str(backup_file),
            )

            logger.info(
                f"Backed up Qdrant {collection_name}: {result.points_count} points ({result.file_size_mb:.1f}MB)"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to backup Qdrant collection {collection_name}: {e}")
            return QdrantCollectionBackupResult(collection=collection_name, error=str(e))

    def create_full_backup(
        self, include_qdrant: bool = True, include_mongodb: bool = True
    ) -> FullBackupResult:
        """Create a full backup of all chat data.

        Args:
            include_qdrant: Include Qdrant vector collections
            include_mongodb: Include MongoDB collections

        Returns:
            Backup result statistics

        """
        logger.info("Starting full backup...")
        backup_dir = self._create_backup_dir("full")

        timestamp = datetime.now().isoformat()
        mongodb_stats = MongoDBBackupStats()
        qdrant_stats = QdrantBackupStats()
        total_size_mb = 0.0

        # Backup MongoDB collections
        if include_mongodb:
            mongodb_collections = ["turns", "turn_metadata"]

            for collection_name in mongodb_collections:
                result = self.backup_mongodb_collection(collection_name, backup_dir)
                mongodb_stats.collections.append(result)
                if result.error is None:
                    total_size_mb += result.file_size_mb

        # Backup Qdrant collections
        if include_qdrant:
            try:
                client = self._connect_qdrant()
                collections = client.get_collections().collections
                qdrant_collection_names = [col.name for col in collections]

                for collection_name in qdrant_collection_names:
                    result = self.backup_qdrant_collection(collection_name, backup_dir)
                    qdrant_stats.collections.append(result)
                    if result.error is None:
                        total_size_mb += result.file_size_mb

            except Exception as e:
                logger.error(f"Failed to get Qdrant collections list: {e}")

        # Check if backup was successful
        all_collections = mongodb_stats.collections + qdrant_stats.collections
        has_errors = any(col.error is not None for col in all_collections)
        success = not has_errors

        # Create result dataclass
        backup_result = FullBackupResult(
            backup_type="full",
            timestamp=timestamp,
            backup_dir=str(backup_dir),
            mongodb=mongodb_stats,
            qdrant=qdrant_stats,
            total_size_mb=total_size_mb,
            success=success,
        )

        # Save backup manifest (convert dataclass to dict for JSON)
        from dataclasses import asdict

        manifest_file = backup_dir / "backup_manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(asdict(backup_result), f, indent=2, default=str)

        # Update backup registry
        backup_info = self._get_backup_info()
        backup_info["backups"].append(  # maxwell:ignore-dict-get (JSON metadata file)
            {
                "type": "full",
                "timestamp": timestamp,
                "backup_dir": str(backup_dir.relative_to(self.backup_root)),
                "total_size_mb": total_size_mb,
                "success": success,
            }
        )
        self._save_backup_info(backup_info)

        if success:
            logger.info(f"[OK] Full backup completed successfully ({total_size_mb:.1f}MB)")
        else:
            logger.error("[ERROR] Full backup completed with errors")

        return backup_result

    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backup_info = self._get_backup_info()
        return backup_info.get("backups", [])  # maxwell:ignore-dict-get (JSON metadata file)

    def restore_backup(self, backup_path: Path, dry_run: bool = False) -> Dict:
        """Restore from a backup directory.

        Args:
            backup_path: Path to backup directory
            dry_run: If True, only show what would be restored

        Returns:
            Restore statistics

        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup directory not found: {backup_path}")

        # Load backup manifest
        manifest_file = backup_path / "backup_manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"Backup manifest not found: {manifest_file}")

        with open(manifest_file, "r") as f:
            backup_manifest = json.load(f)

        logger.info(f"Restoring backup from {backup_path.name} (dry_run={dry_run})")

        restore_result = {
            "backup_timestamp": backup_manifest.get(
                "timestamp"
            ),  # maxwell:ignore-dict-get (JSON manifest)
            "mongodb": {"restored": 0, "errors": 0},
            "qdrant": {"restored": 0, "errors": 0},
            "dry_run": dry_run,
            "success": False,
        }

        if not dry_run:
            # Restore MongoDB collections
            if "mongodb" in backup_manifest and "collections" in backup_manifest["mongodb"]:
                client = self._connect_mongodb()
                db = client[self.mongodb_db]

                for collection_info in backup_manifest["mongodb"]["collections"]:
                    if "error" in collection_info:
                        logger.warning(
                            f"Skipping collection with backup error: {collection_info.get('collection')}"
                        )
                        continue

                    collection_name = collection_info["collection"]
                    backup_file = backup_path / f"{collection_name}.json"

                    if backup_file.exists():
                        try:
                            with open(backup_file, "r") as f:
                                documents = json.load(f)

                            # Drop existing collection
                            db.drop_collection(collection_name)
                            # Insert documents
                            if documents:
                                db[collection_name].insert_many(documents)

                            restore_result["mongodb"]["restored"] += 1
                            logger.info(
                                f"Restored MongoDB {collection_name}: {len(documents)} documents"
                            )

                        except Exception as e:
                            logger.error(f"Failed to restore MongoDB {collection_name}: {e}")
                            restore_result["mongodb"]["errors"] += 1
                    else:
                        logger.warning(f"Backup file not found for {collection_name}")

            # Restore Qdrant collections
            if "qdrant" in backup_manifest and "collections" in backup_manifest["qdrant"]:
                client = self._connect_qdrant()

                for collection_info in backup_manifest["qdrant"]["collections"]:
                    if "error" in collection_info or collection_info.get("skipped"):
                        logger.warning(f"Skipping collection: {collection_info.get('collection')}")
                        continue

                    collection_name = collection_info["collection"]
                    backup_file = backup_path / f"{collection_name}.json"

                    if backup_file.exists():
                        try:
                            with open(backup_file, "r") as f:
                                points_data = json.load(f)

                            if points_data and len(points_data) > 0:
                                # Delete existing collection
                                try:
                                    client.delete_collection(collection_name)
                                except Exception:
                                    pass  # Collection might not exist

                                # Recreate collection
                                from qdrant_client.models import Distance, VectorParams

                                client.create_collection(
                                    collection_name=collection_name,
                                    vectors_config=VectorParams(
                                        size=len(points_data[0]["vector"]), distance=Distance.COSINE
                                    ),
                                )

                                # Convert back to PointStruct and upload
                                from qdrant_client.models import PointStruct

                                points = []
                                for point_data in points_data:
                                    points.append(
                                        PointStruct(
                                            id=point_data["id"],
                                            vector=point_data["vector"],
                                            payload=point_data["payload"],
                                        )
                                    )

                                client.upsert(collection_name, points)

                                restore_result["qdrant"]["restored"] += 1
                                logger.info(
                                    f"Restored Qdrant {collection_name}: {len(points)} points"
                                )

                        except Exception as e:
                            logger.error(f"Failed to restore Qdrant {collection_name}: {e}")
                            restore_result["qdrant"]["errors"] += 1
                    else:
                        logger.warning(f"Backup file not found for {collection_name}")

        restore_result["success"] = (
            restore_result["mongodb"]["errors"] == 0 and restore_result["qdrant"]["errors"] == 0
        )

        if restore_result["success"]:
            action = "Would restore" if dry_run else "[OK] Successfully restored"
            logger.info(f"{action} backup from {backup_path.name}")
        else:
            logger.error("[ERROR] Restore completed with errors")

        return restore_result

    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 5) -> None:
        """Clean up old backups, keeping the most recent ones.

        Args:
            keep_days: Delete backups older than this many days
            keep_count: Always keep at least this many recent backups

        """
        backup_info = self._get_backup_info()
        backups = backup_info.get("backups", [])

        if len(backups) <= keep_count:
            logger.info(f"Only {len(backups)} backups exist, keeping all (minimum: {keep_count})")
            return

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Keep the most recent `keep_count` backups
        keep_backups = backups[:keep_count]

        # For additional backups, check age
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        for backup in backups[keep_count:]:
            try:
                backup_date = datetime.fromisoformat(backup.get("timestamp", ""))
                backup_dir = self.backup_root / backup.get("backup_dir", "")

                if backup_date < cutoff_date and backup_dir.exists():
                    # Remove backup directory
                    shutil.rmtree(backup_dir)
                    logger.info(f"Deleted old backup: {backup_dir.name}")

                    # Remove from registry
                    backup_info["backups"].remove(backup)

            except Exception as e:
                logger.error(f"Failed to cleanup backup {backup.get('backup_dir', 'unknown')}: {e}")

        self._save_backup_info(backup_info)

    def get_backup_summary(self) -> Dict:
        """Get summary of all backups."""
        backup_info = self._get_backup_info()
        backups = backup_info.get("backups", [])

        if not backups:
            return {"total_count": 0, "total_size_mb": 0, "latest_backup": None}

        total_size = sum(b.get("total_size_mb", 0) for b in backups)
        latest_backup = max(backups, key=lambda x: x.get("timestamp", "")) if backups else None

        return {
            "total_count": len(backups),
            "total_size_mb": total_size,
            "latest_backup": latest_backup.get("timestamp") if latest_backup else None,
            "backup_root": str(self.backup_root),
        }


def print_backup_summary(backup_result: Dict) -> None:
    """Print formatted backup summary."""
    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)
    print(f"Backup type: {backup_result['backup_type']}")
    print(f"Timestamp: {backup_result['timestamp']}")
    print(f"Directory: {backup_result['backup_dir']}")
    print(f"Total size: {backup_result['total_size_mb']:.1f}MB")
    print(f"Success: {'[OK]' if backup_result['success'] else '[ERROR]'}")

    if backup_result.get("mongodb", {}).get("collections"):
        print("\nMongoDB Collections:")
        for col in backup_result["mongodb"]["collections"]:
            if "error" in col:
                print(f"  [ERROR] {col['collection']}: {col['error']}")
            else:
                print(
                    f"  [OK] {col['collection']}: {col['document_count']} docs ({col['file_size_mb']:.1f}MB)"
                )

    if backup_result.get("qdrant", {}).get("collections"):
        print("\nQdrant Collections:")
        for col in backup_result["qdrant"]["collections"]:
            if col.get("skipped"):
                print(f"  [SKIP] {col['collection']}: empty, skipped")
            elif "error" in col:
                print(f"  [ERROR] {col['collection']}: {col['error']}")
            else:
                print(
                    f"  [OK] {col['collection']}: {col['points_count']} points ({col['file_size_mb']:.1f}MB)"
                )

    print("=" * 60)


class ChatBackupWorkflow(BaseWorkflow):
    """Backup workflow that integrates with Maxwell's registry."""

    InputSchema = ChatBackupInputs
    OutputSchema = ChatBackupOutputs

    def __init__(self):
        self.workflow_id = "chat_backup"
        self.name = "Chat Data Backup"
        self.description = "Creates automated backups of MongoDB and Qdrant chat data"
        self.version = "1.0"
        super().__init__()

    def get_required_inputs(self) -> Set[str]:
        """Get required input data keys."""
        return set()  # No required inputs

    def get_produced_outputs(self) -> Set[str]:
        """Get output data keys this workflow produces."""
        return {"backup_result", "backup_dir", "collections_backed_up"}

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        """Get workflow configuration."""
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.HIGH,
            timeout_seconds=7200,  # 2 hours
            cache_results=False,  # Backups shouldn't be cached
            parameters={
                "backup_root": str(root_dir / ".maxwell" / "backups"),
                "mongodb_uri": "mongodb://localhost:27017",
                "mongodb_db": "chat_analytics",
                "qdrant_host": "localhost",
                "qdrant_port": 6333,
                "include_mongodb": True,
                "include_qdrant": True,
            },
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        """Execute backup workflow."""
        # Initialize backup manager
        backup = ChatBackupManager(
            mongodb_uri=context.get("mongodb_uri", "mongodb://localhost:27017"),
            mongodb_db=context.get("mongodb_db", "chat_analytics"),
            qdrant_host=context.get("qdrant_host", "localhost"),
            qdrant_port=context.get("qdrant_port", 6333),
            backup_root=Path(context.get("backup_root", "~/.maxwell/backups")),
        )

        # Run backup
        include_mongodb = context.get("include_mongodb", True)
        include_qdrant = context.get("include_qdrant", True)

        backup_result = backup.create_full_backup(
            include_mongodb=include_mongodb, include_qdrant=include_qdrant
        )

        # Create result
        status = WorkflowStatus.COMPLETED if backup_result.success else WorkflowStatus.FAILED
        result = WorkflowResult(
            workflow_id=self.workflow_id,
            status=status,
            metrics=self.metrics,
            artifacts={
                "backup_result": backup_result,
                "backup_dir": backup_result.backup_dir,
                "backup_type": backup_result.backup_type,
                "collections_backed_up": len(backup_result.mongodb.collections)
                + len(backup_result.qdrant.collections),
            },
        )

        return result


# Register workflow in Maxwell's registry
@register_workflow
class RegisteredChatBackupWorkflow(ChatBackupWorkflow):
    """Registered version of ChatBackupWorkflow."""

    def __init__(self):
        # Call parent __init__ to set workflow_id
        super().__init__()
