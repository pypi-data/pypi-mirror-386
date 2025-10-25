"""Utility functions for maxwell workflows and tools.

Provides common utilities that workflows and scripts can use:
- Session identification (current directory as session ID)
- Timestamp generation (ISO 8601 format)
- Path normalization

maxwell/src/maxwell/utils.py
"""

import os
from datetime import datetime
from pathlib import Path


def get_session_id(path: Path | str | None = None) -> str:
    """Get session ID based on absolute path of directory.

    Args:
        path: Directory path to use. If None, uses current working directory.

    Returns:
        Absolute path as session identifier

    Examples:
        >>> get_session_id()
        '/home/user/Documents/project'
        >>> get_session_id('/tmp/work')
        '/tmp/work'

    """
    if path is None:
        return os.path.realpath(os.getcwd())

    return str(Path(path).resolve())


def get_timestamp(format: str = "iso") -> str:
    """Get current timestamp in specified format.

    Args:
        format: Output format. Options:
            - "iso": ISO 8601 format (default) - "2025-10-11T08:15:00.123456"
            - "iso_seconds": ISO 8601 with second precision - "2025-10-11T08:15:00"
            - "date": Date only - "2025-10-11"
            - "filename": Safe for filenames - "2025-10-11_08-15-00"
            - "unix": Unix timestamp (float)

    Returns:
        Formatted timestamp string

    Examples:
        >>> get_timestamp()
        '2025-10-11T08:15:00.123456'
        >>> get_timestamp("iso_seconds")
        '2025-10-11T08:15:00'
        >>> get_timestamp("filename")
        '2025-10-11_08-15-00'

    """
    now = datetime.now()

    if format == "iso":
        return now.isoformat()
    elif format == "iso_seconds":
        return now.strftime("%Y-%m-%dT%H:%M:%S")
    elif format == "date":
        return now.strftime("%Y-%m-%d")
    elif format == "filename":
        return now.strftime("%Y-%m-%d_%H-%M-%S")
    elif format == "unix":
        return str(now.timestamp())
    else:
        raise ValueError(f"Unknown timestamp format: {format}")


def normalize_path(path: Path | str) -> Path:
    """Normalize a path to absolute Path object.

    Args:
        path: Path to normalize (can be relative, absolute, or string)

    Returns:
        Absolute Path object with symlinks resolved

    """
    return Path(path).resolve()


__all__ = [
    "get_session_id",
    "get_timestamp",
    "normalize_path",
]
