"""
Configuration Utilities

Generic utilities for working with configuration files (JSON, TOML).
Provides functions for loading, merging, and accessing nested config data.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    tomllib = None

logger = logging.getLogger(__name__)


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse JSON file with error handling.

    Args:
        file_path (Path): Path to JSON file

    Returns:
        Dict[str, Any]: Parsed JSON content

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "r") as f:
            content = json.load(f)

        logger.debug(f"Loaded configuration from {file_path}")
        return content

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to load {file_path}: {str(e)}")


def load_toml(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse TOML file with error handling.

    Requires Python 3.11+ with built-in tomllib support.

    Args:
        file_path (Path): Path to TOML file

    Returns:
        Dict[str, Any]: Parsed TOML content

    Raises:
        RuntimeError: If tomllib is not available (Python < 3.11)
        FileNotFoundError: If file doesn't exist
        ValueError: If TOML is invalid
    """
    if tomllib is None:
        raise RuntimeError(
            "Python 3.11+ is required for TOML parsing. "
            "Current Python version does not include tomllib."
        )

    try:
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "rb") as f:
            content = tomllib.load(f)

        logger.debug(f"Loaded TOML configuration from {file_path}")
        return content

    except Exception as e:
        raise ValueError(f"Failed to parse TOML file {file_path}: {str(e)}")


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge multiple configuration dictionaries.

    Later configs override earlier ones. Nested dictionaries are merged recursively.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Dict[str, Any]: Merged configuration

    Example:
        >>> base = {"db": {"host": "localhost", "port": 5432}}
        >>> env = {"db": {"port": 3306}, "cache": True}
        >>> merge_configs(base, env)
        {"db": {"host": "localhost", "port": 3306}, "cache": True}
    """
    merged = {}

    for config in configs:
        if config:
            deep_update(merged, config)

    return merged


def deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
    """
    Deep update dictionary with nested structure in-place.

    Recursively updates nested dictionaries. Non-dict values are overwritten.

    Args:
        base_dict (Dict[str, Any]): Base dictionary to update (modified in-place)
        update_dict (Dict[str, Any]): Updates to apply

    Example:
        >>> config = {"db": {"host": "localhost"}}
        >>> deep_update(config, {"db": {"port": 5432}})
        >>> config
        {"db": {"host": "localhost", "port": 5432}}
    """
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            deep_update(base_dict[key], value)
        else:
            base_dict[key] = value


def get_nested_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get nested configuration value using dot notation.

    Args:
        config (Dict[str, Any]): Configuration dictionary
        key_path (str): Dot-separated key path (e.g., "database.timeout.default")
        default (Any): Default value if key is not found

    Returns:
        Any: Retrieved value or default

    Example:
        >>> config = {"db": {"timeout": {"default": 30}}}
        >>> get_nested_value(config, "db.timeout.default")
        30
        >>> get_nested_value(config, "db.missing", "fallback")
        "fallback"
    """
    keys = key_path.split(".")
    current = config

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default
