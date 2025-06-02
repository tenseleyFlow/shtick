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

    def ensure_config_dir(self) -> None:
        """Ensure the config directory exists"""
        config_dir = os.path.dirname(self.config_path)
        Path(config_dir).mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Load and parse the TOML configuration file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)

        self.groups = []

        # Parse groups from TOML structure like [group1.aliases]
        group_data = {}

        for key, value in data.items():
            if "." in key:
                group_name, data_type = key.split(".", 1)

                if group_name not in group_data:
                    group_data[group_name] = {
                        "aliases": {},
                        "env_vars": {},
                        "functions": {},
                    }

                if data_type == "aliases":
                    group_data[group_name]["aliases"] = value
                elif data_type == "env_vars":
                    group_data[group_name]["env_vars"] = value
                elif data_type == "functions":
                    group_data[group_name]["functions"] = value

        # Convert to GroupData objects
        for group_name, data in group_data.items():
            self.groups.append(
                GroupData(
                    name=group_name,
                    aliases=data["aliases"],
                    env_vars=data["env_vars"],
                    functions=data["functions"],
                )
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
