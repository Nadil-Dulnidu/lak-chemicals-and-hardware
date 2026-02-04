"""
Configuration loader module to load settings from config.json file.
"""

import json
import os
from typing import Any, Optional, Dict
from contextlib import contextmanager
from copy import deepcopy


class ConfigLoader:
    """Singleton class to load and access configuration from config.json"""

    _instance = None
    _config = None
    _config_overrides = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from config.json file"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json"
        )

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            self._config = json.load(f)

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            keys: Keys to traverse the configuration dictionary
            default: Default value if key is not found

        Returns:
            Configuration value or default

        Examples:
            config.get('google', 'api_key')
            config.get('logging', 'level', default='INFO')
        """
        # Check for overrides first
        override_key = ".".join(keys)
        if override_key in self._config_overrides:
            return self._config_overrides[override_key]

        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def set_override(self, *keys: str, value: Any) -> None:
        """
        Temporarily override a configuration value.

        Args:
            keys: Keys to identify the configuration value
            value: The override value
        """
        override_key = ".".join(keys)
        self._config_overrides[override_key] = value

    def clear_override(self, *keys: str) -> None:
        """
        Clear a temporary configuration override.

        Args:
            keys: Keys to identify the configuration value
        """
        override_key = ".".join(keys)
        if override_key in self._config_overrides:
            del self._config_overrides[override_key]

    def clear_all_overrides(self) -> None:
        """Clear all temporary configuration overrides"""
        self._config_overrides.clear()

    def reload(self) -> None:
        """Reload configuration from file"""
        self._load_config()


# Singleton instance
_config_loader = None


def get_config() -> ConfigLoader:
    """Get the singleton ConfigLoader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_config_value(*keys: str, default: Any = None) -> Any:
    """
    Convenience function to get a configuration value.

    Args:
        keys: Keys to traverse the configuration dictionary
        default: Default value if key is not found

    Returns:
        Configuration value or default

    Examples:
        get_config_value('google', 'api_key')
        get_config_value('logging', 'level', default='INFO')
    """
    return get_config().get(*keys, default=default)


@contextmanager
def config_override(*keys: str, value: Any):
    """
    Context manager to temporarily override a configuration value.

    Args:
        keys: Keys to identify the configuration value
        value: The override value

    Example:
        with config_override('google', 'api_key', value='temp_key'):
            # Use temporary key
            pass
        # Original key is restored
    """
    config = get_config()
    config.set_override(*keys, value=value)
    try:
        yield
    finally:
        config.clear_override(*keys)
