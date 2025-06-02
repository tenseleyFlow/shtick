"""
Settings management for shtick
"""

import os
import tomllib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger("shtick")


@dataclass
class GenerationSettings:
    """Settings for file generation"""

    shells: List[str] = field(default_factory=list)  # Empty = auto-detect
    parallel: bool = False  # Threading not implemented yet
    consolidate_files: bool = True


@dataclass
class BehaviorSettings:
    """Settings for shtick behavior"""

    auto_source_prompt: bool = True
    check_conflicts: bool = True
    backup_on_save: bool = False
    interactive_mode: bool = True


@dataclass
class PerformanceSettings:
    """Settings for performance optimization"""

    cache_ttl: int = 300  # 5 minutes
    lazy_load: bool = False  # Not implemented yet
    batch_operations: bool = True


class Settings:
    """Manages shtick settings and preferences"""

    # Singleton instance
    _instance = None
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._loaded:
            self.generation = GenerationSettings()
            self.behavior = BehaviorSettings()
            self.performance = PerformanceSettings()
            self._settings_path = self.get_settings_path()
            self._load()
            Settings._loaded = True

    @staticmethod
    def get_settings_path() -> str:
        """Get the settings file path"""
        return os.path.expanduser("~/.config/shtick/settings.toml")

    def _load(self) -> None:
        """Load settings from file if it exists"""
        if not os.path.exists(self._settings_path):
            logger.debug("No settings file found, using defaults")
            return

        try:
            logger.debug(f"Loading settings from {self._settings_path}")
            with open(self._settings_path, "rb") as f:
                data = tomllib.load(f)

            # Load generation settings
            if "generation" in data:
                gen_data = data["generation"]
                self.generation.shells = gen_data.get("shells", [])
                self.generation.parallel = gen_data.get("parallel", False)
                self.generation.consolidate_files = gen_data.get(
                    "consolidate_files", True
                )

            # Load behavior settings
            if "behavior" in data:
                beh_data = data["behavior"]
                self.behavior.auto_source_prompt = beh_data.get(
                    "auto_source_prompt", True
                )
                self.behavior.check_conflicts = beh_data.get("check_conflicts", True)
                self.behavior.backup_on_save = beh_data.get("backup_on_save", False)
                self.behavior.interactive_mode = beh_data.get("interactive_mode", True)

            # Load performance settings
            if "performance" in data:
                perf_data = data["performance"]
                self.performance.cache_ttl = perf_data.get("cache_ttl", 300)
                self.performance.lazy_load = perf_data.get("lazy_load", False)
                self.performance.batch_operations = perf_data.get(
                    "batch_operations", True
                )

            logger.debug("Settings loaded successfully")

        except Exception as e:
            logger.warning(f"Failed to load settings: {e}, using defaults")

    def save(self) -> None:
        """Save current settings to file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self._settings_path), exist_ok=True)

        # Build settings dictionary
        settings_dict = {
            "generation": {
                "shells": self.generation.shells,
                "parallel": self.generation.parallel,
                "consolidate_files": self.generation.consolidate_files,
            },
            "behavior": {
                "auto_source_prompt": self.behavior.auto_source_prompt,
                "check_conflicts": self.behavior.check_conflicts,
                "backup_on_save": self.behavior.backup_on_save,
                "interactive_mode": self.behavior.interactive_mode,
            },
            "performance": {
                "cache_ttl": self.performance.cache_ttl,
                "lazy_load": self.performance.lazy_load,
                "batch_operations": self.performance.batch_operations,
            },
        }

        # Write TOML file
        with open(self._settings_path, "w") as f:
            f.write("# Shtick settings file\n")
            f.write("# Generated automatically - edit as needed\n\n")

            for section, values in settings_dict.items():
                f.write(f"[{section}]\n")
                for key, value in values.items():
                    if isinstance(value, bool):
                        f.write(f"{key} = {str(value).lower()}\n")
                    elif isinstance(value, list):
                        if value:  # Non-empty list
                            f.write(f"{key} = {repr(value)}\n")
                        else:
                            f.write(f"{key} = []  # Empty = auto-detect\n")
                    else:
                        f.write(f"{key} = {value}\n")
                f.write("\n")

    def create_default_settings_file(self) -> None:
        """Create a default settings file with comments"""
        os.makedirs(os.path.dirname(self._settings_path), exist_ok=True)

        content = """# Shtick settings file
# This file controls various shtick behaviors and optimizations

[generation]
# Shells to generate files for. Empty list = auto-detect based on current shell
shells = []
# Enable parallel generation (not implemented yet)
parallel = false
# Consolidate all items into single files per shell
consolidate_files = true

[behavior]
# Prompt to source changes after modifications
auto_source_prompt = true
# Check for conflicts when adding items
check_conflicts = true
# Create backups before saving config
backup_on_save = false
# Enable interactive prompts
interactive_mode = true

[performance]
# Cache time-to-live in seconds
cache_ttl = 300
# Enable lazy loading (not implemented yet)
lazy_load = false
# Enable batch operations for better performance
batch_operations = true
"""

        with open(self._settings_path, "w") as f:
            f.write(content)

        logger.info(f"Created default settings file at {self._settings_path}")

    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
        cls._loaded = False
