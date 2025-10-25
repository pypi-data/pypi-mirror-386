"""Chat conversation parsers for ChatGPT and Claude.

Unified parser system that handles both ChatGPT export (conversations.json)
and Claude projects (.jsonl files).
"""

__all__ = ["Message", "ChatGPTParser", "ClaudeParser"]

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Unified message representation for ChatGPT and Claude conversations."""

    message_id: str
    conversation_id: str
    conversation_title: str
    role: str  # user, assistant, system, tool
    text: str
    timestamp: Optional[float]
    message_index: int  # Position in conversation
    parent_id: Optional[str]
    source: str  # "chatgpt" or "claude"

    # Metadata
    token_count: int
    char_count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        return asdict(self)

    def get_hash(self) -> str:
        """Generate hash for deduplication."""
        content = f"{self.conversation_id}:{self.message_index}:{self.text}"
        return hashlib.sha256(content.encode()).hexdigest()


class ChatGPTParser:
    """Parser for ChatGPT export JSON files.

    Handles conversations.json export format with nested message mappings.

    Usage:
        parser = ChatGPTParser(Path("/path/to/conversations.json"))
        for message in parser.parse():
            print(message.text)
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    def parse(self) -> Iterator[Message]:
        """Parse ChatGPT export and yield individual messages."""
        logger.info(f"Parsing ChatGPT export: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if this is a single conversation or array of conversations
        if isinstance(data, list):
            total_convs = len(data)
            logger.info(f"Found {total_convs} ChatGPT conversations")
            for i, conversation in enumerate(data, 1):
                yield from self._parse_conversation(conversation)
        elif isinstance(data, dict) and "mapping" in data:
            # Single conversation
            yield from self._parse_conversation(data)
        else:
            logger.error("Unknown ChatGPT export format")
            return

    def _parse_conversation(self, conversation: dict) -> Iterator[Message]:
        """Parse a single conversation and yield messages in chronological order."""
        conv_id = conversation.get("id", self._generate_conv_id(conversation))
        conv_title = conversation.get("title", "Untitled Conversation")
        mapping = conversation.get("mapping", {})

        if not mapping:
            logger.warning(f"Empty conversation: {conv_title}")
            return

        # Build ordered message list by walking the graph
        messages = self._walk_graph(mapping)

        # Yield messages with metadata
        for idx, msg_data in enumerate(messages):
            msg_obj = msg_data.get("message")
            if not msg_obj:
                continue

            author = msg_obj.get("author", {})
            role = author.get("role", "unknown")
            content = msg_obj.get("content", {})

            # Extract text from content
            text = self._extract_text(content)
            if not text or len(text.strip()) < 10:
                continue  # Skip very short messages

            message = Message(
                message_id=msg_obj.get("id", f"{conv_id}-{idx}"),
                conversation_id=conv_id,
                conversation_title=conv_title,
                role=role,
                text=text.strip(),
                timestamp=msg_obj.get("create_time"),
                message_index=idx,
                parent_id=msg_data.get("parent"),
                source="chatgpt",
                token_count=self._estimate_tokens(text),
                char_count=len(text),
            )

            yield message

    def _walk_graph(self, mapping: dict) -> list:
        """Walk the conversation graph to get messages in chronological order.

        ChatGPT stores conversations as a directed graph with parent/children.
        We need to find the root and follow the main path.
        """
        # Find root node (no parent)
        root_id = None
        for node_id, node in mapping.items():
            if node.get("parent") is None:
                root_id = node_id
                break

        if not root_id:
            logger.warning("No root node found, using first node")
            root_id = next(iter(mapping.keys()))

        # Walk from root following children (depth-first, first child)
        messages = []
        visited = set()
        stack = [root_id]

        while stack:
            current_id = stack.pop(0)

            if current_id in visited or current_id not in mapping:
                continue

            visited.add(current_id)
            node = mapping[current_id]

            # Add message if it exists
            if node.get("message"):
                messages.append(node)

            # Add first child to stack (main conversation path)
            children = node.get("children", [])
            if children:
                # Follow first child (main path)
                stack.insert(0, children[0])

        return messages

    def _extract_text(self, content: dict) -> str:
        """Extract text from content object."""
        if not content:
            return ""

        content_type = content.get("content_type", "")

        # Handle text content
        if content_type == "text":
            parts = content.get("parts", [])
            return "".join(str(p) for p in parts if p)

        # Handle code content
        elif content_type == "code":
            return content.get("text", "")

        # Handle other types
        else:
            # Try to extract any text field
            return content.get("text", "") or str(content.get("parts", ""))

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4

    def _generate_conv_id(self, conversation: dict) -> str:
        """Generate conversation ID from metadata."""
        title = conversation.get("title", "")
        create_time = conversation.get("create_time", 0)
        content = f"{title}:{create_time}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


class ClaudeParser:
    """Parser for Claude Code chat logs (.jsonl files).

    Handles the JSONL format from ~/.claude/projects/

    Usage:
        parser = ClaudeParser(Path("~/.claude/projects/some-project/conversation.jsonl"))
        for message in parser.parse():
            print(message.text)
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

    def parse(self) -> Iterator[Message]:
        """Parse Claude JSONL and yield individual messages."""
        logger.info(f"Parsing Claude conversation: {self.file_path}")

        conversation_id = self.file_path.stem
        # Try to extract a title from parent directory or filename
        conversation_title = self.file_path.parent.name or self.file_path.stem

        message_index = 0

        with open(self.file_path, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_type = entry.get("type")

                    # Only process user and assistant messages
                    if entry_type not in ("user", "assistant"):
                        continue

                    # Extract message object
                    message_obj = entry.get("message", {})
                    content = message_obj.get("content", [])

                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        # Handle both dict and string content blocks
                        if isinstance(block, str):
                            text_parts.append(block)
                        elif isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))

                    if not text_parts:
                        continue

                    text = "\n".join(text_parts)
                    if len(text.strip()) < 10:
                        continue  # Skip very short messages

                    timestamp_str = entry.get("timestamp", "")
                    timestamp = self._parse_timestamp(timestamp_str)

                    message_id = entry.get("id", f"{conversation_id}-{message_index}")

                    message = Message(
                        message_id=message_id,
                        conversation_id=conversation_id,
                        conversation_title=conversation_title,
                        role=message_obj.get("role", entry_type),
                        text=text.strip(),
                        timestamp=timestamp,
                        message_index=message_index,
                        parent_id=None,  # Claude JSONL doesn't have parent references
                        source="claude",
                        token_count=self._estimate_tokens(text),
                        char_count=len(text),
                    )

                    yield message
                    message_index += 1

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line in {self.file_path}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message in {self.file_path}: {e}")
                    continue

    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """Parse ISO timestamp to Unix epoch."""
        if not timestamp_str:
            return None

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4
