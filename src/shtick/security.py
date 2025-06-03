"""
Security validation functions for shtick
"""

import os
import re
from pathlib import Path
from typing import Tuple

# Pre-compiled regex for key validation - used frequently
KEY_VALIDATION_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")

# System directories that should be blocked
FORBIDDEN_SYSTEM_PATHS = (
    "/etc",
    "/sys",
    "/proc",
    "/dev",
    "/boot",
    "/usr",
    "/bin",
    "/sbin",
)


def validate_key(key: str) -> None:
    """
    Validate key format for security.

    Args:
        key: The key to validate

    Raises:
        ValueError: If key format is invalid
    """
    if not KEY_VALIDATION_PATTERN.match(key):
        raise ValueError(
            f"Invalid key '{key}': must start with letter/underscore and contain only alphanumeric, underscore, hyphen"
        )

    # Additional length check to prevent abuse
    if len(key) > 64:
        raise ValueError(f"Key '{key}' too long: maximum 64 characters")


def validate_value(value: str, max_length: int = 4096) -> None:
    """
    Validate value for security.

    Args:
        value: The value to validate
        max_length: Maximum allowed length

    Raises:
        ValueError: If value is invalid
    """
    if len(value) > max_length:
        raise ValueError(f"Value too long: maximum {max_length} characters")


def validate_config_path(path: str) -> str:
    """
    Validate and sanitize config path for security.

    Args:
        path: Path to validate

    Returns:
        Validated absolute path

    Raises:
        ValueError: If path is invalid or unsafe
    """
    if not path:
        from shtick.config import Config

        return Config.get_default_config_path()

    try:
        # Resolve to absolute path
        resolved = Path(path).resolve()
        resolved_str = str(resolved)

        # Check for directory traversal attempts
        if ".." in path:
            raise ValueError("Directory traversal detected")

        # Block system directories
        if any(
            resolved_str.startswith(forbidden) for forbidden in FORBIDDEN_SYSTEM_PATHS
        ):
            raise ValueError(f"Access to system directories is forbidden")

        # Ensure it's under user's home or current directory
        home = Path.home()
        cwd = Path.cwd()

        if not (resolved.is_relative_to(home) or resolved.is_relative_to(cwd)):
            raise ValueError("Config path must be under home or current directory")

        # Ensure .toml extension
        if resolved.suffix != ".toml":
            raise ValueError("Config file must have .toml extension")

        return resolved_str

    except Exception as e:
        raise ValueError(f"Invalid config path: {e}")


def validate_assignment(assignment: str) -> Tuple[str, str]:
    """
    Validate key=value assignment format and return validated key, value.

    Args:
        assignment: Assignment string in format "key=value"

    Returns:
        Tuple of (validated_key, validated_value)

    Raises:
        ValueError: If assignment format or content is invalid
    """
    if "=" not in assignment:
        raise ValueError("Assignment must be in format key=value")

    key, value = assignment.split("=", 1)
    key = key.strip()
    value = value.strip()

    if not key or not value:
        raise ValueError("Both key and value must be non-empty")

    # Validate key and value
    validate_key(key)
    validate_value(value)

    return key, value
