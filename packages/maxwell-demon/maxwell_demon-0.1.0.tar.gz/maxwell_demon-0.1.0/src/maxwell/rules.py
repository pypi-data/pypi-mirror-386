"""Rule management system for maxwell.

Handles rule configuration, severity overrides, and policy management.

maxwell/src/maxwell/rules.py
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from maxwell.config import MaxwellConfig
from maxwell.workflows.validate.validators import BaseValidator, Severity, plugin_manager

logger = logging.getLogger(__name__)


class DefaultSeverity(Enum):
    """Predefined severity levels for consistency."""

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


__all__ = ["RuleEngine", "create_default_rule_config", "DefaultSeverity"]


class RuleEngine:
    """Manages rule configuration and policy decisions."""

    def __init__(self, config: MaxwellConfig):
        """Initialize rule engine with configuration.

        Args:
            config: Configuration object from pyproject.toml

        """
        self.config = config
        self._rule_overrides: dict[str, Severity] = {}
        self._enabled_plugins: Set[str] = set()
        self._load_rule_config()

    def _load_rule_config(self):
        """Load rule configuration from config."""
        # Load rule severity overrides
        rules_config = {}  # TODO: Update MaxwellConfig to include rules field
        if isinstance(rules_config, dict):
            for rule_id, setting in rules_config.items():
                if isinstance(setting, str):
                    try:
                        self._rule_overrides[rule_id] = Severity(setting.upper())
                    except ValueError as e:
                        logger.debug(
                            f"Invalid severity setting for rule {rule_id}: {setting} - {e}"
                        )
                        pass
                elif isinstance(setting, bool):
                    # Boolean: True=default severity, False=OFF
                    if not setting:
                        self._rule_overrides[rule_id] = Severity.OFF

        # Load disabled validators from ignore list
        ignore_codes = []  # TODO: Update MaxwellConfig to include ignore field
        if isinstance(ignore_codes, list):
            for rule_id in ignore_codes:
                if isinstance(rule_id, str):
                    self._rule_overrides[rule_id] = Severity.OFF

        # Load enabled plugins
        plugins_config = {}  # TODO: Update MaxwellConfig to include plugins field
        if isinstance(plugins_config, dict):
            enabled = plugins_config.get("enabled", ["maxwell.core"])
            if isinstance(enabled, list):
                self._enabled_plugins.update(enabled)
            elif isinstance(enabled, str):
                self._enabled_plugins.add(enabled)

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled (not set to OFF)."""
        severity = self._rule_overrides.get(rule_id)
        return severity != Severity.OFF if severity else True

    def get_rule_severity(self, rule_id: str, default: Severity = Severity.WARN) -> Severity:
        """Get effective severity for a rule."""
        # Primary: semantic rule IDs
        severity = self._rule_overrides.get(rule_id)
        if severity is not None:
            return severity

        return default

    def create_validator_instance(
        self, validator_class: type[BaseValidator]
    ) -> Optional[BaseValidator]:
        """Create validator instance with configured severity.

        Args:
            validator_class: Validator class to instantiate

        Returns:
            Validator instance or None if rule is disabled

        """
        if not self.is_rule_enabled(validator_class.rule_id):
            return None

        severity = self.get_rule_severity(validator_class.rule_id, validator_class.default_severity)

        return validator_class(severity=severity, config=self.config)

    def get_enabled_validators(self) -> List[BaseValidator]:
        """Get all enabled validator instances."""
        validators = []
        all_validators = plugin_manager.get_all_validators()

        for _, validator_class in all_validators.items():
            instance = self.create_validator_instance(validator_class)
            if instance:
                validators.append(instance)

        return validators

    def filter_enabled_validators(
        self, validator_classes: List[type[BaseValidator]]
    ) -> List[BaseValidator]:
        """Filter and instantiate only enabled validators from a list."""
        validators = []
        for validator_class in validator_classes:
            instance = self.create_validator_instance(validator_class)
            if instance:
                validators.append(instance)
        return validators

    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of rule configuration."""
        all_validators = plugin_manager.get_all_validators()
        enabled_count = sum(1 for rule_id in all_validators.keys() if self.is_rule_enabled(rule_id))

        return {
            "total_rules": len(all_validators),
            "enabled_rules": enabled_count,
            "disabled_rules": len(all_validators) - enabled_count,
            "overrides": len(self._rule_overrides),
            "plugins": list(self._enabled_plugins),
        }


def create_default_rule_config() -> Dict[str, Any]:
    """Create default rule configuration for new projects."""
    return {
        "rules": {
            # Semantic rule IDs (primary system)
            "DOCSTRING-MISSING": DefaultSeverity.INFO.value,  # Missing docstring is just info
            "EXPORTS-MISSING-ALL": DefaultSeverity.WARN.value,  # Missing __all__ is warning
            "PRINT-STATEMENT": DefaultSeverity.WARN.value,  # Print statements are warnings
            "EMOJI-IN-STRING": DefaultSeverity.WARN.value,  # Emojis can cause encoding issues
            "TODO-FOUND": DefaultSeverity.INFO.value,  # TODOs are informational
            "PARAMETERS-KEYWORD-ONLY": DefaultSeverity.INFO.value,  # Parameter suggestions are info
        },
        "plugins": {"enabled": ["maxwell.core"]},
    }
