"""Configuration loading for maxwell.

Reads settings *only* from pyproject.toml under the [tool.maxwell] section.
No default values are assumed by this module. Callers must handle missing
configuration keys.

maxwell/src/maxwell/config.py
"""

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from maxwell.filesystem import find_package_root, walk_up_for_config

# === TYPE-SAFE CONFIGURATION MODELS ===


@dataclass
class FilePatternsConfig:
    """Configuration for file patterns."""

    include_globs: List[str] = field(default_factory=list)
    exclude_globs: List[str] = field(default_factory=list)
    max_file_size_mb: Optional[int] = None
    follow_symlinks: bool = False


@dataclass
class EmbeddingModelConfig:
    """Configuration for a specific embedding model."""

    api_url: str
    model: str
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 100


@dataclass
class EmbeddingConfig:
    """Complete embedding configuration."""

    code: EmbeddingModelConfig
    natural: EmbeddingModelConfig
    use_specialized: bool = True
    cache_embeddings: bool = True


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""

    backend: str = "qdrant"
    collection_name: str = "maxwell_embeddings"
    host: str = "localhost"
    port: int = 6333
    timeout: int = 30
    recreate_collection: bool = False


@dataclass
class ValidationConfig:
    """Validation engine configuration."""

    enabled: bool = True
    strict_mode: bool = False
    fail_fast: bool = True
    max_displayed_issues: int = 50
    auto_fix: bool = False


@dataclass
class ToolConfig:
    """Individual tool configuration."""

    enabled: bool = True
    timeout_seconds: Optional[int] = None
    max_retries: int = 0
    cache_results: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MaxwellConfig:
    """Complete Maxwell configuration."""

    # Core paths and patterns
    file_patterns: FilePatternsConfig = field(default_factory=FilePatternsConfig)

    # Service configurations with defaults
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)

    # Workflow configurations
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    # Tool configurations
    tools: Dict[str, ToolConfig] = field(default_factory=dict)

    # Development settings
    debug: bool = False
    log_level: str = "INFO"

    # Legacy embedding config (deprecated - use lm_pool instead)
    embeddings: Optional[EmbeddingConfig] = None


# === CONVERSION FUNCTIONS (JSON parsing only) ===


def from_json_dict(data: Dict[str, Any]) -> MaxwellConfig:
    """Convert parsed JSON dict to type-safe MaxwellConfig.

    Uses dataclass defaults instead of dict.get() fallbacks.
    """
    # Extract embeddings (legacy - optional)
    embedding_config: Optional[EmbeddingConfig] = None
    if "embeddings" in data:
        embedding_data = data["embeddings"]
        if "code_api_url" in embedding_data and "natural_api_url" in embedding_data:
            # Build code model config with explicit checks
            code_kwargs: Dict[str, Any] = {"api_url": embedding_data["code_api_url"]}
            if "code_model" in embedding_data:
                code_kwargs["model"] = embedding_data["code_model"]
            else:
                code_kwargs["model"] = "text-embedding-ada-002"

            code_model = EmbeddingModelConfig(**code_kwargs)

            # Build natural model config with explicit checks
            natural_kwargs: Dict[str, Any] = {"api_url": embedding_data["natural_api_url"]}
            if "natural_model" in embedding_data:
                natural_kwargs["model"] = embedding_data["natural_model"]
            else:
                natural_kwargs["model"] = "text-embedding-ada-002"

            natural_model = EmbeddingModelConfig(**natural_kwargs)

            # Build embedding config
            embedding_kwargs: Dict[str, Any] = {
                "code": code_model,
                "natural": natural_model,
            }
            if "use_specialized_embeddings" in embedding_data:
                embedding_kwargs["use_specialized"] = embedding_data["use_specialized_embeddings"]

            embedding_config = EmbeddingConfig(**embedding_kwargs)

    # Extract vector store config (use dataclass defaults)
    vector_config = VectorStoreConfig()
    if "vector_store" in data:
        vector_data = data["vector_store"]
        vector_kwargs: Dict[str, Any] = {}

        if "backend" in vector_data:
            vector_kwargs["backend"] = vector_data["backend"]
        if "qdrant_collection" in vector_data:
            vector_kwargs["collection_name"] = vector_data["qdrant_collection"]
        if "host" in vector_data:
            vector_kwargs["host"] = vector_data["host"]
        if "port" in vector_data:
            vector_kwargs["port"] = vector_data["port"]

        vector_config = VectorStoreConfig(**vector_kwargs)

    # Extract validation config (use dataclass defaults)
    validation_config = ValidationConfig()
    if "validation" in data:
        validation_data = data["validation"]
        validation_kwargs: Dict[str, Any] = {}

        if "enabled" in validation_data:
            validation_kwargs["enabled"] = validation_data["enabled"]
        if "strict_mode" in validation_data:
            validation_kwargs["strict_mode"] = validation_data["strict_mode"]
        if "fail_fast" in validation_data:
            validation_kwargs["fail_fast"] = validation_data["fail_fast"]
        if "max_displayed_issues" in validation_data:
            validation_kwargs["max_displayed_issues"] = validation_data["max_displayed_issues"]

        validation_config = ValidationConfig(**validation_kwargs)

    # Extract file patterns
    file_kwargs: Dict[str, Any] = {}
    if "include_globs" in data:
        file_kwargs["include_globs"] = data["include_globs"]
    if "exclude_globs" in data:
        file_kwargs["exclude_globs"] = data["exclude_globs"]

    file_config = FilePatternsConfig(**file_kwargs)

    # Extract tools
    tools_config: Dict[str, ToolConfig] = {}
    if "tool" in data:
        tools_data = data["tool"]
        for name, config_data in tools_data.items():
            tool_kwargs: Dict[str, Any] = {}

            if "enabled" in config_data:
                tool_kwargs["enabled"] = config_data["enabled"]
            if "timeout_seconds" in config_data:
                tool_kwargs["timeout_seconds"] = config_data["timeout_seconds"]
            if "max_retries" in config_data:
                tool_kwargs["max_retries"] = config_data["max_retries"]

            tools_config[name] = ToolConfig(**tool_kwargs)

    return MaxwellConfig(
        file_patterns=file_config,
        embeddings=embedding_config,
        vector_store=vector_config,
        validation=validation_config,
        tools=tools_config,
    )


def to_json_dict(config: MaxwellConfig) -> Dict[str, Any]:
    """Convert type-safe MaxwellConfig to JSON dict (for serialization)."""
    result: Dict[str, Any] = {
        "vector_store": {
            "backend": config.vector_store.backend,
            "qdrant_collection": config.vector_store.collection_name,
            "host": config.vector_store.host,
            "port": config.vector_store.port,
        },
        "validation": {
            "enabled": config.validation.enabled,
            "strict_mode": config.validation.strict_mode,
            "fail_fast": config.validation.fail_fast,
            "max_displayed_issues": config.validation.max_displayed_issues,
        },
        "include_globs": config.file_patterns.include_globs,
        "exclude_globs": config.file_patterns.exclude_globs,
        "tool": {
            name: {
                "enabled": tool_config.enabled,
                "timeout_seconds": tool_config.timeout_seconds,
                "max_retries": tool_config.max_retries,
            }
            for name, tool_config in config.tools.items()
        },
    }

    # Legacy embeddings (deprecated - use lm_pool instead)
    if config.embeddings:
        result["embeddings"] = {
            "code_api_url": config.embeddings.code.api_url,
            "natural_api_url": config.embeddings.natural.api_url,
            "code_model": config.embeddings.code.model,
            "natural_model": config.embeddings.natural.model,
            "use_specialized_embeddings": config.embeddings.use_specialized,
        }

    return result


logger = logging.getLogger(__name__)


def _find_config_file(project_root: Path) -> Path | None:
    """Find the config file (pyproject.toml) with maxwell settings."""
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                if "tool" in data and "maxwell" in data["tool"]:
                    return pyproject_path
        except Exception:
            pass

    return None


def _load_parent_config(project_root: Path, current_config_path: Path) -> dict | None:
    """Load parent configuration for inheritance."""
    # Walk up from the project root to find parent configurations
    parent_path = project_root.parent

    while parent_path != parent_path.parent:  # Stop at filesystem root
        # Check for pyproject.toml
        parent_config = parent_path / "pyproject.toml"
        if parent_config.exists() and parent_config != current_config_path:
            try:
                with open(parent_config, "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "maxwell" in data["tool"]:
                        maxwell_config = data["tool"]["maxwell"]
                        logger.debug(f"Found parent config in {parent_config}")
                        return maxwell_config
            except Exception:
                pass

        parent_path = parent_path.parent

    return None


if sys.version_info >= (3, 11):

    import tomllib
else:

    try:

        import tomli as tomllib
    except ImportError as e:

        raise ImportError(
            "maxwell requires Python 3.11+ or the 'tomli' package "
            "to parse pyproject.toml on Python 3.10. "
            "Hint: Try running: pip install tomli"
        ) from e


@dataclass
class ProjectConfig:
    """Legacy wrapper for backwards compatibility."""

    project_root: Optional[Path]
    config: MaxwellConfig


def load_hierarchical_config(start_path: Path) -> MaxwellConfig:
    """Loads maxwell configuration with hierarchical merging.

    1. Loads local config (file patterns, local settings)
    2. Walks up to find parent config (LLM settings, shared config)
    3. Merges them: local config takes precedence for file patterns,
       parent config provides LLM settings

    Args:
    start_path: The directory to start searching from.

    Returns:
    A Config object with merged local and parent settings.

    """
    # Find local config first
    local_root = find_package_root(start_path)
    local_settings = {}

    if local_root:
        pyproject_path = local_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "maxwell" in data["tool"]:
                        local_settings = data["tool"]["maxwell"]
                        logger.info(f"Loaded local maxwell config from {pyproject_path}")
            except Exception as e:
                logger.warning(f"Failed to load local config from {pyproject_path}: {e}")

    # Walk up to find parent config with LLM settings
    parent_settings = {}
    current_path = start_path.parent if start_path.is_file() else start_path

    while current_path.parent != current_path:
        parent_pyproject = current_path / "pyproject.toml"
        if parent_pyproject.exists() and parent_pyproject != (
            local_root / "pyproject.toml" if local_root else None
        ):
            try:
                with open(parent_pyproject, "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "maxwell" in data["tool"]:
                        parent_settings = data["tool"]["maxwell"]
                        logger.info(f"Found parent maxwell config at {parent_pyproject}")
                        break
            except Exception as e:
                logger.debug(f"Failed to read {parent_pyproject}: {e}")
        current_path = current_path.parent

    # Merge configs in order: parent -> local
    # This allows: parent provides base (e.g., shared settings for team)
    #              local overrides file patterns for project
    merged_settings = parent_settings.copy()

    # Local config takes precedence for file discovery patterns
    if local_settings:
        for key in ["include_globs", "exclude_globs", "ignore"]:
            if key in local_settings:
                merged_settings[key] = local_settings[key]

        # Also copy other local-specific settings
        for key in local_settings:
            if key not in ["include_globs", "exclude_globs", "ignore"]:
                merged_settings[key] = local_settings[key]

    return from_json_dict(merged_settings)


def load_config(start_path: Path) -> MaxwellConfig:
    """Loads maxwell configuration with auto-discovery fallback.

    First tries manual config from pyproject.toml, then falls back to
    zero-config auto-discovery for seamless single->multi-project scaling.

    Args:
    start_path: The directory to start searching upwards for pyproject.toml.

    Returns:
    A MaxwellConfig object with either manual or auto-discovered settings.

    maxwell/src/maxwell/config.py

    """
    project_root = walk_up_for_config(start_path)
    loaded_settings: dict[str, Any] = {}

    # Try auto-discovery first for zero-config scaling
    try:
        from maxwell.auto_discovery import discover_and_configure  # type: ignore

        auto_config = discover_and_configure(start_path)

        # If we found a multi-project setup, use auto-discovery by default
        if (
            "discovered_topology" in auto_config
            and auto_config["discovered_topology"] == "multi_project"
        ):
            logger.info(f"Auto-discovered multi-project setup from {start_path}")
            # Convert auto-discovered config to maxwell config format
            loaded_settings = _convert_auto_config_to_maxwell(auto_config)
            project_root = project_root or start_path

            # Still allow manual config to override auto-discovery
            manual_override = _load_manual_config(project_root)
            if manual_override:
                logger.debug("Manual config found, merging with auto-discovery")
                loaded_settings.update(manual_override)

            return from_json_dict(loaded_settings)

    except ImportError:
        logger.debug("Auto-discovery not available, using manual config only")
    except Exception as e:
        logger.debug(f"Auto-discovery failed: {e}, falling back to manual config")

    if not project_root:
        logger.warning(
            f"Could not find project root (pyproject.toml) searching from '{start_path}'. "
            "No configuration will be loaded."
        )
        return from_json_dict(loaded_settings)

    # Try to load from pyproject.toml
    pyproject_path = _find_config_file(project_root)
    logger.debug(f"Found project root: {project_root}")

    if not pyproject_path:
        logger.debug(f"No maxwell configuration found in {project_root}")
        return from_json_dict({})

    logger.debug(f"Attempting to load config from: {pyproject_path}")

    try:
        with open(pyproject_path, "rb") as f:
            full_toml_config = tomllib.load(f)
        logger.debug(f"Parsed {pyproject_path.name}")

        # Validate required configuration structure explicitly
        if "tool" not in full_toml_config or not isinstance(full_toml_config["tool"], dict):
            logger.warning("pyproject.toml [tool] section is missing or invalid")
            maxwell_config = {}
        else:
            tool_section = full_toml_config["tool"]
            if "maxwell" in tool_section:
                maxwell_config = tool_section["maxwell"]
            else:
                maxwell_config = {}

        if isinstance(maxwell_config, dict):
            loaded_settings = maxwell_config
            # Check for parent config inheritance
            parent_config = _load_parent_config(project_root, pyproject_path)
            if parent_config:
                # Merge parent config with local config (local takes precedence)
                merged_settings = parent_config.copy()
                merged_settings.update(loaded_settings)
                loaded_settings = merged_settings
                logger.debug("Merged parent configuration")

            if loaded_settings:
                logger.debug(f"Loaded [tool.maxwell] settings from {pyproject_path}")
                logger.debug(f"Loaded settings: {loaded_settings}")
            else:
                logger.info(
                    f"Found {pyproject_path}, but the [tool.maxwell] section is empty or missing."
                )
        else:
            logger.warning(
                f"[tool.maxwell] section in {pyproject_path} is not a valid table (dictionary). "
                "Ignoring this section."
            )

    except FileNotFoundError:

        logger.error(
            f"pyproject.toml not found at {pyproject_path} despite project root detection."
        )
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Error parsing {pyproject_path}: {e}. Using empty configuration.")
    except OSError as e:
        logger.error(f"Error reading {pyproject_path}: {e}. Using empty configuration.")
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error processing configuration from {pyproject_path}: {e}")
        logger.debug("Unexpected error loading config", exc_info=True)

    return from_json_dict(loaded_settings)


def _convert_auto_config_to_maxwell(auto_config: dict[str, Any]) -> dict[str, Any]:
    """Convert auto-discovered config to maxwell config format."""
    maxwell_config: dict[str, Any] = {}

    # Auto-route validation based on discovered services
    services = auto_config["services"] if "services" in auto_config else {}
    routing = auto_config["auto_routing"] if "auto_routing" in auto_config else {}

    # Set include globs based on discovered projects
    include_globs = []
    for service_info in services.values():
        service_path = Path(service_info["path"])
        include_globs.extend([f"{service_path.name}/src/**/*.py", f"{service_path.name}/**/*.py"])

    maxwell_config["include_globs"] = include_globs

    # Configure distributed services if available
    if (
        "discovered_topology" in auto_config
        and auto_config["discovered_topology"] == "multi_project"
    ):
        maxwell_config["distributed"] = {
            "enabled": True,
            "auto_discovered": True,
            "services": services,
            "routing": routing,
        }

        # Use shared resources if discovered
        if "shared_resources" in auto_config:
            shared_resources = auto_config["shared_resources"]
            if "vector_stores" in shared_resources and shared_resources["vector_stores"]:
                maxwell_config["vector_store"] = {
                    "backend": "qdrant",
                    "qdrant_collection": shared_resources["vector_stores"][0],
                }

    return maxwell_config


def _load_manual_config(project_root: Path | None) -> dict[str, Any]:
    """Load manual configuration from pyproject.toml."""
    if not project_root:
        return {}

    pyproject_path = project_root / "pyproject.toml"
    logger.debug(f"Attempting to load manual config from: {pyproject_path}")

    try:
        with open(pyproject_path, "rb") as f:
            full_toml_config = tomllib.load(f)
        logger.debug("Parsed pyproject.toml")

        # Validate required configuration structure explicitly
        if "tool" not in full_toml_config or not isinstance(full_toml_config["tool"], dict):
            logger.warning("pyproject.toml [tool] section is missing or invalid")
            return {}

        tool_section = full_toml_config["tool"]
        if "maxwell" in tool_section:
            maxwell_config = tool_section["maxwell"]
        else:
            maxwell_config = {}

        if isinstance(maxwell_config, dict):
            if maxwell_config:
                logger.debug(f"Loaded manual [tool.maxwell] settings from {pyproject_path}")
                return maxwell_config
            else:
                logger.debug(f"Found {pyproject_path}, but [tool.maxwell] section is empty")
                return {}
        else:
            logger.warning(
                f"[tool.maxwell] section in {pyproject_path} is not a valid table. Ignoring."
            )
            return {}

    except FileNotFoundError:
        logger.debug(f"No pyproject.toml found at {pyproject_path}")
        return {}
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Error parsing {pyproject_path}: {e}")
        return {}
    except OSError as e:
        logger.error(f"Error reading {pyproject_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading manual config: {e}")
        return {}


__all__ = [
    "MaxwellConfig",
    "ProjectConfig",  # Legacy wrapper
    "load_config",
    "load_hierarchical_config",
    "from_json_dict",
    "to_json_dict",
    # Dataclass types
    "FilePatternsConfig",
    "EmbeddingModelConfig",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "ValidationConfig",
    "ToolConfig",
]
