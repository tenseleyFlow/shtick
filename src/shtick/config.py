"""
Configuration parsing for shtick
"""

import os
import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GroupData:
    """Holds parsed data for a single group"""

    name: str
    aliases: Dict[str, str]
    env_vars: Dict[str, str]
    functions: Dict[str, str]


class Config:
    """Main configuration handler"""

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

        print(f"Debug: Loading config from: {self.config_path}")

        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)

        print(f"Debug: Raw TOML data keys: {list(data.keys())}")
        print(f"Debug: Raw TOML data structure: {data}")

        self.groups = []

        # Parse groups from nested TOML structure
        for group_name, group_config in data.items():
            print(f"Debug: Processing group '{group_name}' with config: {group_config}")

            if not isinstance(group_config, dict):
                print(f"Debug: Skipping non-dict value for key '{group_name}'")
                continue

            # Initialize group data
            group_data = {"aliases": {}, "env_vars": {}, "functions": {}}

            # Extract each section from the group
            for section_name, section_data in group_config.items():
                print(
                    f"Debug: Processing section '{section_name}' in group '{group_name}': {section_data}"
                )

                if section_name == "aliases" and isinstance(section_data, dict):
                    group_data["aliases"] = section_data
                    print(f"Debug: Added {len(section_data)} aliases to '{group_name}'")
                elif section_name == "env_vars" and isinstance(section_data, dict):
                    group_data["env_vars"] = section_data
                    print(
                        f"Debug: Added {len(section_data)} env_vars to '{group_name}'"
                    )
                elif section_name == "functions" and isinstance(section_data, dict):
                    group_data["functions"] = section_data
                    print(
                        f"Debug: Added {len(section_data)} functions to '{group_name}'"
                    )
                else:
                    print(
                        f"Debug: Unknown or invalid section '{section_name}' in group '{group_name}'"
                    )

            # Create GroupData object if group has any items
            total_items = (
                len(group_data["aliases"])
                + len(group_data["env_vars"])
                + len(group_data["functions"])
            )
            print(f"Debug: Group '{group_name}' has {total_items} total items")

            if total_items > 0:
                new_group = GroupData(
                    name=group_name,
                    aliases=group_data["aliases"],
                    env_vars=group_data["env_vars"],
                    functions=group_data["functions"],
                )
                self.groups.append(new_group)
                print(
                    f"Debug: Created group '{group_name}' with {len(group_data['aliases'])} aliases, {len(group_data['env_vars'])} env_vars, {len(group_data['functions'])} functions"
                )
            else:
                print(f"Warning: Group '{group_name}' has no items, skipping")

        print(
            f"Debug: Final groups loaded: {[g.name for g in self.groups]} (total: {len(self.groups)})"
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

        if item_type == "alias":
            group.aliases[key] = value
        elif item_type == "env":
            group.env_vars[key] = value
        elif item_type == "function":
            group.functions[key] = value
        else:
            raise ValueError(f"Unknown item type: {item_type}")

    def remove_item(self, item_type: str, group_name: str, key: str) -> bool:
        """Remove an item from a group. Returns True if found and removed."""
        group = self.get_group(group_name)
        if not group:
            return False

        if item_type == "alias" and key in group.aliases:
            del group.aliases[key]
            return True
        elif item_type == "env" and key in group.env_vars:
            del group.env_vars[key]
            return True
        elif item_type == "function" and key in group.functions:
            del group.functions[key]
            return True

        return False

    def find_items(
        self, item_type: str, group_name: str, search_term: str
    ) -> List[str]:
        """Find items matching a search term (for fuzzy removal)"""
        group = self.get_group(group_name)
        if not group:
            return []

        if item_type == "alias":
            items = group.aliases.keys()
        elif item_type == "env":
            items = group.env_vars.keys()
        elif item_type == "function":
            items = group.functions.keys()
        else:
            return []

        # Simple fuzzy matching - contains search term
        return [item for item in items if search_term.lower() in item.lower()]
