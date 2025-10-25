"""Type definitions for Maxwell domain objects.

Contains dataclass definitions for non-workflow types:
- LLM specifications
- Extraction results
- File metadata

Workflow-related types (WorkflowInputs, WorkflowOutputs) are in workflows/base.py.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChatExtractionResult:
    """Result from extracting chat content."""

    format: str
    total_lines: int
    user_messages: int
    assistant_messages: int
    session_id: str


@dataclass
class DocumentExtractionResult:
    """Result from extracting document content."""

    format: str
    source: str
    path: str


@dataclass
class PDFExtractionResult:
    """Result from extracting PDF content."""

    format: str
    pages: int
    images: int


@dataclass
class FileMetadata:
    """Metadata about extracted files."""

    format: str
    size_bytes: int


@dataclass
class LLMSpec:
    """Specification for an LLM model."""

    model: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@dataclass
class LLMRequest:
    """Request to an LLM."""

    input: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@dataclass
class LLMResponse:
    """Response from an LLM."""

    content: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    model: str = ""


@dataclass
class Message:
    """Chat message with role and content."""

    role: str
    content: str


@dataclass
class LLMUsage:
    """Usage statistics from LLM API."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
