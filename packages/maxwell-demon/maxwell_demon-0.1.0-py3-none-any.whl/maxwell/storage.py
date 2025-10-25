"""Content-addressable storage for Maxwell.

Architecture:
1. Content hashing (SHA256) - deduplication
2. SQLite cache (~/.maxwell/cache.db) - hash → embedding
3. Distributed maps (.maxwell/map.json) - hash → locations
"""

__all__ = ["EmbeddingCache", "ChunkLocation", "ContentHasher"]

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    import numpy as np
else:
    # Lazy import - only needed for embedding storage
    np = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class ChunkLocation:
    """Location of a content chunk."""

    file_path: str  # Relative to project root
    line_start: int
    line_end: int
    size_bytes: int
    last_modified: int


@dataclass
class ChunkMetadata:
    """Metadata for a content chunk."""

    chunk_hash: str
    locations: List[ChunkLocation]
    content_preview: str  # First 500 chars


class EmbeddingCache:
    """Global embedding cache using SQLite."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache.

        Args:
            cache_dir: Cache directory (defaults to ~/.maxwell/)

        """
        if cache_dir is None:
            cache_dir = Path.home() / ".maxwell"

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "cache.db"

        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_hash TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    created_at INTEGER NOT NULL,
                    last_accessed INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 1
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_last_accessed
                ON embeddings(last_accessed)
            """
            )

    def get(self, chunk_hash: str):  # type: ignore[no-untyped-def]
        """Get embedding from cache.

        Args:
            chunk_hash: SHA256 hash of content

        Returns:
            Embedding vector or None if not cached

        """
        import numpy as np

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT embedding FROM embeddings WHERE chunk_hash = ?", (chunk_hash,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            # Update access stats
            import time

            conn.execute(
                """UPDATE embeddings
                   SET last_accessed = ?, access_count = access_count + 1
                   WHERE chunk_hash = ?""",
                (int(time.time()), chunk_hash),
            )

            # Deserialize numpy array
            return np.frombuffer(row[0], dtype=np.float32)

    def put(self, chunk_hash: str, embedding):  # type: ignore[no-untyped-def]
        """Store embedding in cache.

        Args:
            chunk_hash: SHA256 hash of content
            embedding: Embedding vector (numpy array)

        """
        import numpy as np
        import time

        now = int(time.time())

        # Serialize numpy array to bytes
        embedding_bytes = embedding.astype(np.float32).tobytes()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO embeddings
                   (chunk_hash, embedding, created_at, last_accessed)
                   VALUES (?, ?, ?, ?)""",
                (chunk_hash, embedding_bytes, now, now),
            )

    def stats(self) -> Dict:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT
                    COUNT(*) as total,
                    SUM(access_count) as total_accesses,
                    AVG(access_count) as avg_accesses
                   FROM embeddings"""
            )
            row = cursor.fetchone()

            return {
                "total_embeddings": row[0],
                "total_accesses": row[1] or 0,
                "avg_accesses": row[2] or 0,
                "db_size_mb": self.db_path.stat().st_size / 1024 / 1024,
            }


class ContentHasher:
    """Content hashing utilities."""

    @staticmethod
    def hash_content(content: str) -> str:
        """Hash content using SHA256.

        Args:
            content: Text content

        Returns:
            Hex digest of SHA256 hash

        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_file(path: Path) -> str:
        """Hash file content.

        Args:
            path: File path

        Returns:
            Hex digest of SHA256 hash

        """
        content = path.read_text(errors="ignore")
        return ContentHasher.hash_content(content)


class LocalMap:
    """Distributed map tracking chunks in a directory."""

    def __init__(self, directory: Path):
        """Initialize map.

        Args:
            directory: Directory containing .maxwell/

        """
        self.directory = directory
        self.map_dir = directory / ".maxwell"
        self.map_path = self.map_dir / "map.json"

        self.chunks: Dict[str, ChunkLocation] = {}

        # Load existing map
        if self.map_path.exists():
            self.load()

    def load(self):
        """Load map from disk."""
        try:
            with open(self.map_path, "r") as f:
                data = json.load(f)

            self.chunks = {
                chunk_hash: ChunkLocation(**loc)
                for chunk_hash, loc in data.get("chunks", {}).items()
            }

            logger.debug(f"Loaded map with {len(self.chunks)} chunks")
        except Exception as e:
            logger.warning(f"Failed to load map from {self.map_path}: {e}")
            self.chunks = {}

    def save(self):
        """Save map to disk."""
        self.map_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "chunks": {
                chunk_hash: {
                    "file_path": loc.file_path,
                    "line_start": loc.line_start,
                    "line_end": loc.line_end,
                    "size_bytes": loc.size_bytes,
                    "last_modified": loc.last_modified,
                }
                for chunk_hash, loc in self.chunks.items()
            },
        }

        with open(self.map_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved map with {len(self.chunks)} chunks")

    def add_chunk(self, chunk_hash: str, location: ChunkLocation):
        """Add chunk to map."""
        self.chunks[chunk_hash] = location

    def get_location(self, chunk_hash: str) -> Optional[ChunkLocation]:
        """Get location of chunk."""
        return self.chunks.get(chunk_hash)

    def remove_chunk(self, chunk_hash: str):
        """Remove chunk from map."""
        self.chunks.pop(chunk_hash, None)


class ContentStore:
    """Content-addressable storage combining cache + maps."""

    def __init__(self, root: Path, cache_dir: Optional[Path] = None):
        """Initialize storage.

        Args:
            root: Project root directory
            cache_dir: Global cache directory

        """
        self.root = root
        # Cache removed - embeddings stored directly in Qdrant
        # self.cache = None  # Embeddings stored directly in Qdrant
        self.hasher = ContentHasher()

        # Track all maps in the project
        self.maps: Dict[Path, LocalMap] = {}

        # Initialize .maxwell directory structure
        self._init_maxwell_dir()

    def _init_maxwell_dir(self):
        """Initialize .maxwell directory with proper structure and gitignore.

        Storage tiers:
        - data/: JSONL files (committed to git)
        - indexes/: SQLite query layer (gitignored, rebuildable)
        - extracted/: Cached PDF extractions (gitignored, can be remote)
        - index/: Hierarchy JSON (gitignored, rebuildable)
        """
        maxwell_dir = self.root / ".maxwell"
        maxwell_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (maxwell_dir / "data").mkdir(exist_ok=True)
        (maxwell_dir / "indexes").mkdir(exist_ok=True)
        (maxwell_dir / "extracted").mkdir(exist_ok=True)
        (maxwell_dir / "index").mkdir(exist_ok=True)

        # Create .gitignore
        gitignore_path = maxwell_dir / ".gitignore"
        gitignore_content = """# Maxwell ephemeral indexes (rebuildable from data/)
indexes/
index/

# Content-addressable cache (local extractions, can be rebuilt or fetched from remote)
extracted/

# SQLite databases
*.db
*.db-shm
*.db-wal

# Keep the immutable data (JSONL graph files)
!data/
!data/*.jsonl
"""

        # Only write if doesn't exist or is different
        if not gitignore_path.exists() or gitignore_path.read_text() != gitignore_content:
            gitignore_path.write_text(gitignore_content)
            logger.info(f"Created {gitignore_path}")

    def get_map(self, directory: Path) -> LocalMap:
        """Get or create map for directory."""
        if directory not in self.maps:
            self.maps[directory] = LocalMap(directory)
        return self.maps[directory]

    def save_all_maps(self):
        """Save all maps to disk."""
        for map_obj in self.maps.values():
            map_obj.save()

    def add_file(self, file_path: Path, embedding, content: str) -> str:  # type: ignore[no-untyped-def]
        """Add file to content store.

        Args:
            file_path: Absolute file path
            embedding: Pre-computed embedding (numpy array)
            content: File content

        Returns:
            Content hash

        """
        # Hash content
        chunk_hash = self.hasher.hash_content(content)

        # Cache embedding (idempotent) - DEPRECATED: embeddings stored in Qdrant
        # self.cache.put(chunk_hash, embedding)

        # Add to local map
        directory = file_path.parent
        local_map = self.get_map(directory)

        location = ChunkLocation(
            file_path=str(file_path.relative_to(self.root)),
            line_start=1,
            line_end=len(content.splitlines()),
            size_bytes=len(content.encode("utf-8")),
            last_modified=int(file_path.stat().st_mtime),
        )

        local_map.add_chunk(chunk_hash, location)

        return chunk_hash

    def get_embedding(self, chunk_hash: str):  # type: ignore[no-untyped-def]
        """Get embedding for chunk hash (returns numpy array or None).

        DEPRECATED: Embeddings now stored directly in Qdrant.
        """
        # return self.cache.get(chunk_hash)
        return None  # Embeddings stored in Qdrant, not in local cache

    def find_locations(self, chunk_hash: str) -> List[ChunkLocation]:
        """Find all locations of a chunk across project."""
        locations = []

        for local_map in self.maps.values():
            loc = local_map.get_location(chunk_hash)
            if loc:
                locations.append(loc)

        return locations
