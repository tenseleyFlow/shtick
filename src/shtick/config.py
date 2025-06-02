"""
Configuration parsing for shtick - REFACTORED
"""

import os
import tomllib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

logger = logging.getLogger("shtick")


@dataclass
class GroupData:
    """Holds parsed data for a single group"""

    name: str
    aliases: Dict[str, str]
    env_vars: Dict[str, str]
    functions: Dict[str, str]

    def get_items(self, item_type: str) -> Dict[str, str]:
        """Get items dictionary for the specified type"""
        type_map = {"alias": "aliases", "env": "env_vars", "function": "functions"}
        attr_name = type_map.get(item_type)
        if not attr_name:
            raise ValueError(f"Unknown item type: {item_type}")
        return getattr(self, attr_name)

    def set_item(self, item_type: str, key: str, value: str) -> None:
        """Set an item in the appropriate dictionary"""
        items = self.get_items(item_type)
        items[key] = value

    def remove_item(self, item_type: str, key: str) -> bool:
        """Remove an item if it exists"""
        items = self.get_items(item_type)
        if key in items:
            del items[key]
            return True
        return False

    def has_item(self, item_type: str, key: str) -> bool:
        """Check if an item exists"""
        items = self.get_items(item_type)
        return key in items

    def get_item_value(self, item_type: str, key: str) -> Optional[str]:
        """Get the value of an item"""
        items = self.get_items(item_type)
        return items.get(key)

    @property
    def total_items(self) -> int:
        """Get total number of items in this group"""
        return len(self.aliases) + len(self.env_vars) + len(self.functions)


class Config:
    """Main configuration handler"""

    # Class variable for shell detection caching
    _detected_shell = None

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.get_default_config_path()
        self.groups: List[GroupData] = []

    @staticmethod
    def get_default_config_path() -> str:
        """Get the default config file location"""
        return os.path.expanduser("~/.config/shtick/config.toml")

    @staticmethod
    def get_output_dir() -> str:
        """Get the output directory for generated shell files"""
        return os.path.expanduser("~/.config/shtick")

    @staticmethod
    def get_active_groups_file() -> str:
        """Get the active groups state file path"""
        return os.path.expanduser("~/.config/shtick/active_groups")

    @classmethod
    def get_current_shell(cls) -> Optional[str]:
        """Detect the current shell with caching"""
        if cls._detected_shell is None:
            shell_path = os.environ.get("SHELL", "")
            cls._detected_shell = os.path.basename(shell_path) if shell_path else ""
        return cls._detected_shell if cls._detected_shell else None

    @classmethod
    def clear_shell_cache(cls):
        """Clear the cached shell detection (useful for testing)"""
        cls._detected_shell = None

    def load_active_groups(self) -> List[str]:
        """Load list of currently active groups"""
        active_file = self.get_active_groups_file()
        if not os.path.exists(active_file):
            return []

        with open(active_file, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def save_active_groups(self, active_groups: List[str]) -> None:
        """Save list of active groups to state file"""
        self.ensure_config_dir()
        active_file = self.get_active_groups_file()

        with open(active_file, "w") as f:
            for group in active_groups:
                f.write(f"{group}\n")

    def activate_group(self, group_name: str) -> bool:
        """Activate a group. Returns True if successful."""
        # Check if group exists
        if not self.get_group(group_name):
            return False

        active_groups = self.load_active_groups()
        if group_name not in active_groups:
            active_groups.append(group_name)
            self.save_active_groups(active_groups)

        return True

    def deactivate_group(self, group_name: str) -> bool:
        """Deactivate a group. Returns True if was active."""
        active_groups = self.load_active_groups()
        if group_name in active_groups:
            active_groups.remove(group_name)
            self.save_active_groups(active_groups)
            return True
        return False

    def is_group_active(self, group_name: str) -> bool:
        """Check if a group is currently active"""
        return group_name in self.load_active_groups()

    def get_persistent_group(self) -> Optional[GroupData]:
        """Get the special 'persistent' group if it exists"""
        return self.get_group("persistent")

    def get_regular_groups(self) -> List[GroupData]:
        """Get all groups except 'persistent'"""
        return [group for group in self.groups if group.name != "persistent"]

    def ensure_config_dir(self) -> None:
        """Ensure the config directory exists"""
        config_dir = os.path.dirname(self.config_path)
        Path(config_dir).mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Load and parse the TOML configuration file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        logger.debug(f"Loading config from: {self.config_path}")

        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)

        logger.debug(f"Raw TOML data keys: {list(data.keys())}")

        self.groups = []

        # Parse groups from nested TOML structure
        for group_name, group_config in data.items():
            if not isinstance(group_config, dict):
                logger.debug(f"Skipping non-dict value for key '{group_name}'")
                continue

            # Initialize group data
            group_data = {"aliases": {}, "env_vars": {}, "functions": {}}

            # Extract each section from the group
            for section_name, section_data in group_config.items():
                if section_name == "aliases" and isinstance(section_data, dict):
                    group_data["aliases"] = section_data
                    logger.debug(f"Added {len(section_data)} aliases to '{group_name}'")
                elif section_name == "env_vars" and isinstance(section_data, dict):
                    group_data["env_vars"] = section_data
                    logger.debug(
                        f"Added {len(section_data)} env_vars to '{group_name}'"
                    )
                elif section_name == "functions" and isinstance(section_data, dict):
                    group_data["functions"] = section_data
                    logger.debug(
                        f"Added {len(section_data)} functions to '{group_name}'"
                    )
                else:
                    logger.debug(
                        f"Unknown or invalid section '{section_name}' in group '{group_name}'"
                    )

            # Create GroupData object if group has any items
            new_group = GroupData(
                name=group_name,
                aliases=group_data["aliases"],
                env_vars=group_data["env_vars"],
                functions=group_data["functions"],
            )

            if new_group.total_items > 0:
                self.groups.append(new_group)
                logger.debug(
                    f"Created group '{group_name}' with {len(group_data['aliases'])} aliases, "
                    f"{len(group_data['env_vars'])} env_vars, {len(group_data['functions'])} functions"
                )
            else:
                logger.warning(f"Group '{group_name}' has no items, skipping")

        logger.debug(
            f"Final groups loaded: {[g.name for g in self.groups]} (total: {len(self.groups)})"
        )

    def save(self) -> None:
        """Save the current configuration back to TOML file"""
        self.ensure_config_dir()

        # Convert groups back to TOML structure
        data = {}
        for group in self.groups:
            if group.aliases:
                data[f"{group.name}.aliases"] = group.aliases
            if group.env_vars:
                data[f"{group.name}.env_vars"] = group.env_vars
            if group.functions:
                data[f"{group.name}.functions"] = group.functions

        # Write TOML manually since tomllib is read-only
        with open(self.config_path, "w") as f:
            for section, items in data.items():
                f.write(f"[{section}]\n")
                for key, value in items.items():
                    # Escape quotes in values
                    escaped_value = value.replace('"', '\\"')
                    f.write(f'{key} = "{escaped_value}"\n')
                f.write("\n")

    def get_group(self, group_name: str) -> Optional[GroupData]:
        """Get a specific group by name"""
        for group in self.groups:
            if group.name == group_name:
                return group
        return None

    def add_group(self, group_name: str) -> GroupData:
        """Add a new group or return existing one"""
        existing = self.get_group(group_name)
        if existing:
            return existing

        new_group = GroupData(name=group_name, aliases={}, env_vars={}, functions={})
        self.groups.append(new_group)
        return new_group

    def add_item(self, item_type: str, group_name: str, key: str, value: str) -> None:
        """Add an alias, env var, or function to a group"""
        group = self.add_group(group_name)
        group.set_item(item_type, key, value)

    def remove_item(self, item_type: str, group_name: str, key: str) -> bool:
        """Remove an item from a group. Returns True if found and removed."""
        group = self.get_group(group_name)
        if not group:
            return False
        return group.remove_item(item_type, key)

    def find_items(
        self, item_type: str, group_name: str, search_term: str
    ) -> List[str]:
        """Find items matching a search term (for fuzzy removal)"""
        group = self.get_group(group_name)
        if not group:
            return []

        items = group.get_items(item_type)
        # Simple fuzzy matching - contains search term
        return [item for item in items.keys() if search_term.lower() in item.lower()]

    def get_all_shells_to_generate(self) -> List[str]:
        """Get list of shells to generate files for based on user settings"""
        # For now, just detect current shell and common ones
        # Later this can read from settings.toml
        current_shell = self.get_current_shell()
        if not current_shell:
            return ["bash", "zsh", "fish"]  # Common defaults

        # Include current shell and close relatives
        shell_families = {
            "bash": ["bash", "sh"],
            "zsh": ["zsh", "bash"],
            "fish": ["fish"],
            "ksh": ["ksh", "bash"],
            "dash": ["dash", "sh"],
        }

        shells = shell_families.get(current_shell, [current_shell])
        return list(set(shells))  # Remove duplicates
