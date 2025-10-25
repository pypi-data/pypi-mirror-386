"""Multi-format content extractors for Maxwell.

Extracts text from various file formats for semantic indexing:
- PDFs (via marker-pdf)
- Office docs (via markitdown: DOCX, PPTX, XLSX)
- Images (via markitdown: OCR)
- Audio (via markitdown: speech-to-text)
- And more

Content-addressable extraction cache:
- Extractions cached in ~/.maxwell/cache/extracted/{sha256}/
- Reuses existing parsed versions when available
- Global deduplication (same file = same hash = same extraction)
"""

__all__ = ["ExtractedContent", "ContentExtractor", "get_content_extractor"]

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from maxwell.types import (
    ChatExtractionResult,
    DocumentExtractionResult,
    FileMetadata,
    PDFExtractionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContent:
    """Content extracted from a file."""

    text: str
    metadata: Dict[str, Any]  # TODO: Make more specific with dataclass types
    images: List[Any]  # For PDFs with images


class ContentExtractor:
    """Extract text content from various file formats with content-addressable caching."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize extractors.

        Args:
            cache_dir: Cache directory for extractions (default: ~/.maxwell/cache/extracted)

        """
        self._marker_pdf = None
        self._markitdown = None
        self.cache_dir = cache_dir or Path.home() / ".maxwell" / "cache" / "extracted"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_marker_pdf(self):
        """Lazy load marker-pdf."""
        if self._marker_pdf is None:
            try:
                from marker.converters.pdf import PdfConverter
                from marker.models import create_model_dict

                self._marker_models = create_model_dict()
                self._marker_pdf = PdfConverter(artifact_dict=self._marker_models)
                logger.info("Loaded marker-pdf")
            except ImportError as e:
                logger.warning(f"marker-pdf not available: {e}")
        return self._marker_pdf

    def _get_markitdown(self):
        """Lazy load markitdown."""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown

                self._markitdown = MarkItDown()
                logger.info("Loaded markitdown")
            except ImportError as e:
                logger.warning(f"markitdown not available: {e}")
        return self._markitdown

    def _hash_file(self, path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_cache_path(self, path: Path) -> Path:
        """Get cache directory for this file's hash."""
        file_hash = self._hash_file(path)
        return self.cache_dir / file_hash

    def _load_pdf_parse_map(self) -> dict:
        """Load PDF parse mapping from ~/.maxwell/pdf_parse_map.json.

        Format:
        {
            "/absolute/path/to/paper.pdf": "/absolute/path/to/parsed/paper.md",
            "~/Documents/arxiv/*.pdf": "~/Documents/arxiv/parsed_papers/originals/*/paper.md"
        }

        Supports:
        - Absolute paths
        - ~ expansion
        - Glob patterns (for bulk mappings)
        """
        map_file = Path.home() / ".maxwell" / "pdf_parse_map.json"
        if not map_file.exists():
            return {}

        try:
            with open(map_file) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load PDF parse map: {e}")
            return {}

    def _check_existing_parse(self, path: Path) -> Optional[Path]:
        """Check if this PDF was already parsed.

        Checks in order:
        1. Explicit mapping in ~/.maxwell/pdf_parse_map.json
        2. Sibling 'parsed/' directory (convention-based)

        Examples:
        - praxis/paper.pdf → praxis/parsed/paper.md
        - praxis/paper.pdf → praxis/parsed/paper_name/paper.md
        - Mapped: /any/path/paper.pdf → /any/other/path/parsed.md

        """
        if path.suffix.lower() != ".pdf":
            return None

        # Strategy 1: Check explicit mapping
        parse_map = self._load_pdf_parse_map()
        path_str = str(path.resolve())

        # Try exact match first
        if path_str in parse_map:
            mapped_path = Path(parse_map[path_str]).expanduser()
            if mapped_path.exists():
                logger.info(f"Found mapped parse: {mapped_path}")
                return mapped_path

        # Try glob patterns (e.g., "~/Documents/arxiv/*.pdf")
        from glob import glob as glob_match

        for pattern, target_pattern in parse_map.items():
            if "*" in pattern:
                pattern_expanded = Path(pattern).expanduser()
                matches = glob_match(str(pattern_expanded))
                if path_str in matches:
                    # Resolve target (may also be a pattern)
                    target = Path(target_pattern).expanduser()
                    if target.exists():
                        logger.info(f"Found mapped parse (glob): {target}")
                        return target

        # Strategy 2: Check sibling parsed/ directory
        sibling_parsed = path.parent / "parsed"
        if not sibling_parsed.exists():
            return None

        # Direct match (paper.pdf -> parsed/paper.md)
        md_file = sibling_parsed / f"{path.stem}.md"
        if md_file.exists():
            logger.info(f"Found sibling parse: {md_file.relative_to(path.parent.parent)}")
            return md_file

        # Subdirectory match (paper.pdf -> parsed/paper_*/paper.md)
        for subdir in sibling_parsed.iterdir():
            if subdir.is_dir() and path.stem.lower() in subdir.name.lower():
                md_files = list(subdir.glob("*.md"))
                if md_files:
                    logger.info(
                        f"Found sibling parse: {md_files[0].relative_to(path.parent.parent)}"
                    )
                    return md_files[0]

        return None

    def _load_cached_extraction(self, cache_path: Path) -> Optional[ExtractedContent]:
        """Load extraction from cache."""
        metadata_file = cache_path / "metadata.json"
        text_file = cache_path / "extracted.md"

        if not (metadata_file.exists() and text_file.exists()):
            return None

        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
            text = text_file.read_text()

            # Load images if they exist
            images = []
            image_dir = cache_path / "images"
            if image_dir.exists():
                images = [str(img) for img in image_dir.glob("*")]

            logger.debug(f"Loaded cached extraction from {cache_path}")
            return ExtractedContent(text=text, metadata=metadata, images=images)
        except Exception as e:
            logger.warning(f"Failed to load cache from {cache_path}: {e}")
            return None

    def _save_to_cache(self, cache_path: Path, content: ExtractedContent):
        """Save extraction to cache."""
        try:
            cache_path.mkdir(parents=True, exist_ok=True)

            # Save metadata
            with open(cache_path / "metadata.json", "w") as f:
                json.dump(content.metadata, f, indent=2)

            # Save text
            (cache_path / "extracted.md").write_text(content.text)

            # Save images if any
            if content.images:
                image_dir = cache_path / "images"
                image_dir.mkdir(exist_ok=True)
                # Images are already saved by marker-pdf, just note their existence
                # in metadata

            logger.debug(f"Cached extraction to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save to cache {cache_path}: {e}")

    def can_extract(self, path: Path) -> bool:
        """Check if we can extract content from this file."""
        suffix = path.suffix.lower()

        # Claude chat logs (JSONL format)
        if suffix == ".jsonl":
            # Check if it's in .claude/projects directory
            if ".claude/projects/" in str(path):
                return True

        # Marker-pdf for high-quality PDF extraction (LaTeX, tables, figures)
        if suffix == ".pdf":
            return self._get_marker_pdf() is not None

        # Markitdown for Office docs, images, audio, etc.
        markitdown_formats = {
            ".docx",
            ".doc",  # Word
            ".pptx",
            ".ppt",  # PowerPoint
            ".xlsx",
            ".xls",  # Excel
            ".png",
            ".jpg",
            ".jpeg",  # Images (OCR)
            ".mp3",
            ".wav",  # Audio (speech-to-text)
            ".html",
            ".htm",  # HTML
            ".csv",
            ".json",
            ".xml",  # Structured
        }
        if suffix in markitdown_formats:
            return self._get_markitdown() is not None

        return False

    def extract(self, path: Path, max_chars: int = 10000) -> Optional[ExtractedContent]:
        """Extract content from file with content-addressable caching.

        Args:
            path: File to extract from
            max_chars: Maximum characters to extract

        Returns:
            Extracted content or None if extraction failed

        """
        # Check cache first (content-addressable deduplication)
        cache_path = self._get_cache_path(path)
        cached = self._load_cached_extraction(cache_path)
        if cached:
            logger.debug(f"Cache hit for {path.name}")
            return cached

        # For PDFs, check if there's an existing parse
        if path.suffix.lower() == ".pdf":
            existing_parse = self._check_existing_parse(path)
            if existing_parse:
                # Load existing parse and save to cache
                text = existing_parse.read_text()
                result = ExtractedContent(
                    text=text[:max_chars] if len(text) > max_chars else text,
                    metadata=asdict(
                        DocumentExtractionResult(
                            format="pdf",
                            source="existing_arxiv_parse",
                            path=str(existing_parse),
                        )
                    ),
                    images=[],  # Could enumerate images from directory if needed
                )
                self._save_to_cache(cache_path, result)
                return result

        # Extract fresh
        suffix = path.suffix.lower()
        try:
            if suffix == ".jsonl" and ".claude/projects/" in str(path):
                result = self._extract_claude_chat(path, max_chars)
            elif suffix == ".pdf":
                result = self._extract_pdf(path, max_chars)
            elif suffix in {
                ".docx",
                ".pptx",
                ".xlsx",
                ".png",
                ".jpg",
                ".jpeg",
                ".mp3",
                ".wav",
                ".html",
                ".csv",
                ".json",
                ".xml",
            }:
                result = self._extract_markitdown(path, max_chars)
            else:
                return None

            # Cache the result
            if result:
                self._save_to_cache(cache_path, result)

            return result
        except Exception as e:
            logger.error(f"Failed to extract {path}: {e}")
            return None

    def _extract_claude_chat(self, path: Path, max_chars: int) -> Optional[ExtractedContent]:
        """Extract conversational content from Claude Code chat logs (.jsonl).

        Format: One JSON object per line with message data.
        Extract user/assistant exchanges for searchable content.
        """
        try:
            chunks = []
            message_count = 0
            user_msgs = 0
            assistant_msgs = 0

            with open(path) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get("type")

                        # Extract user messages
                        if entry_type == "user":
                            msg = entry.get("message", {})
                            content = msg.get("content", [])
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text = block.get("text", "")
                                    if text and len(text) > 50:  # Skip very short messages
                                        chunks.append(f"[USER]: {text[:2000]}")  # Limit per message
                                        user_msgs += 1

                        # Extract assistant messages
                        elif entry_type == "assistant":
                            msg = entry.get("message", {})
                            content = msg.get("content", [])
                            for block in content:
                                if isinstance(block, dict):
                                    if block.get("type") == "text":
                                        text = block.get("text", "")
                                        if text and len(text) > 50:
                                            chunks.append(f"[ASSISTANT]: {text[:2000]}")
                                            assistant_msgs += 1

                        message_count += 1

                        # Stop if we've extracted enough
                        if sum(len(c) for c in chunks) > max_chars:
                            break

                    except json.JSONDecodeError:
                        continue

            # Combine chunks
            text = "\n\n".join(chunks)
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n[Truncated from {len(text)} chars]"

            return ExtractedContent(
                text=text,
                metadata=asdict(
                    ChatExtractionResult(
                        format="claude_chat_jsonl",
                        total_lines=message_count,
                        user_messages=user_msgs,
                        assistant_messages=assistant_msgs,
                        session_id=path.stem,
                    )
                ),
                images=[],
            )

        except Exception as e:
            logger.error(f"Failed to extract Claude chat from {path}: {e}")
            return None

    def _extract_pdf(self, path: Path, max_chars: int) -> Optional[ExtractedContent]:
        """Extract PDF using marker-pdf."""
        converter = self._get_marker_pdf()
        if not converter:
            return None

        try:
            # Convert PDF to markdown (use str, not Path)
            result = converter(str(path))
            full_text = result.markdown

            # Truncate if too long
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + f"\n\n[Truncated from {len(full_text)} chars]"

            return ExtractedContent(
                text=full_text,
                metadata=asdict(
                    PDFExtractionResult(
                        format="pdf",
                        pages=getattr(result, "pages", 0),
                        images=len(getattr(result, "images", [])),
                    )
                ),
                images=getattr(result, "images", []),
            )
        except Exception as e:
            logger.error(f"marker-pdf failed on {path}: {e}")
            return None

    def _extract_markitdown(self, path: Path, max_chars: int) -> Optional[ExtractedContent]:
        """Extract content using markitdown."""
        markitdown = self._get_markitdown()
        if not markitdown:
            return None

        try:
            # Convert to markdown
            result = markitdown.convert(str(path))
            text = result.text_content

            # Truncate if too long
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n[Truncated from {len(text)} chars]"

            return ExtractedContent(
                text=text,
                metadata=asdict(
                    FileMetadata(
                        format=path.suffix[1:],  # Remove dot
                        size_bytes=path.stat().st_size,
                    )
                ),
                images=[],
            )
        except Exception as e:
            logger.error(f"markitdown failed on {path}: {e}")
            return None


# Global singleton
_extractor = None


def get_content_extractor() -> ContentExtractor:
    """Get or create the global content extractor."""
    global _extractor
    if _extractor is None:
        _extractor = ContentExtractor()
    return _extractor
