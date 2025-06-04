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


def escape_toml_value(value: str) -> str:
    """
    Properly escape a string value for TOML with security considerations.

    Args:
        value: String value to escape

    Returns:
        Properly escaped TOML string
    """
    # Check if we need multi-line literal string
    if "\n" in value or "\r" in value:
        # Use multi-line literal string (no escaping needed)
        # But check for ''' to avoid breaking out of literal string
        if "'''" in value:
            # Fall back to basic string with escaping
            escaped = value.replace("\\", "\\\\")  # Backslash first
            escaped = escaped.replace('"', '\\"')  # Quotes
            escaped = escaped.replace("\t", "\\t")  # Tab
            escaped = escaped.replace("\r", "\\r")  # Carriage return
            escaped = escaped.replace("\n", "\\n")  # Newline
            return f'"{escaped}"'
        else:
            return f"'''\n{value}'''"

    # Check if we need basic string with escaping
    needs_escape = any(c in value for c in ['"', "\\", "\t", "\r", "\n"])

    if needs_escape:
        # Escape special characters
        escaped = value.replace("\\", "\\\\")  # Backslash first
        escaped = escaped.replace('"', '\\"')  # Quotes
        escaped = escaped.replace("\t", "\\t")  # Tab
        escaped = escaped.replace("\r", "\\r")  # Carriage return
        escaped = escaped.replace(
            "\n", "\\n"
        )  # Newline (shouldn't happen due to check above)
        return f'"{escaped}"'

    # Simple string
    return f'"{value}"'


def save_config_securely(config_path: str, groups) -> None:
    """
    Save configuration to TOML file with proper escaping.

    Args:
        config_path: Path to save config file
        groups: List of GroupData objects to save
    """
    from pathlib import Path

    # Ensure directory exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)

    # Try to use proper TOML library if available
    try:
        import tomli_w

        data = {}
        for group in groups:
            group_data = {}
            # Always include the sections, even if empty
            group_data["aliases"] = group.aliases if group.aliases else {}
            group_data["env_vars"] = group.env_vars if group.env_vars else {}
            group_data["functions"] = group.functions if group.functions else {}
            data[group.name] = group_data

        with open(config_path, "wb") as f:
            tomli_w.dump(data, f)

    except ImportError:
        # Enhanced fallback that writes proper nested TOML structure
        with open(config_path, "w") as f:
            # Write each group
            for group in groups:
                # Write main group header
                f.write(f"[{group.name}]\n")

                # Write aliases section
                f.write(f"[{group.name}.aliases]\n")
                for key in sorted(group.aliases.keys()):
                    value = group.aliases[key]
                    escaped_value = escape_toml_value(value)
                    f.write(f"{key} = {escaped_value}\n")

                # Write env_vars section
                f.write(f"\n[{group.name}.env_vars]\n")
                for key in sorted(group.env_vars.keys()):
                    value = group.env_vars[key]
                    escaped_value = escape_toml_value(value)
                    f.write(f"{key} = {escaped_value}\n")

                # Write functions section
                f.write(f"\n[{group.name}.functions]\n")
                for key in sorted(group.functions.keys()):
                    value = group.functions[key]
                    escaped_value = escape_toml_value(value)
                    f.write(f"{key} = {escaped_value}\n")

                f.write("\n")  # Empty line between groups


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

    # Class variables for caching
    _detected_shell = None
    _active_groups_cache = None
    _active_groups_mtime = None
    _active_groups_file_path = None

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

    @classmethod
    def clear_all_caches(cls):
        """Clear all caches (useful for testing or forced refresh)"""
        cls._detected_shell = None
        cls._active_groups_cache = None
        cls._active_groups_mtime = None
        cls._active_groups_file_path = None

    def load_active_groups(self) -> List[str]:
        """Load list of currently active groups with caching"""
        active_file = self.get_active_groups_file()

        # Check if we need to reload from disk
        if os.path.exists(active_file):
            current_mtime = os.path.getmtime(active_file)
            if (
                self._active_groups_cache is None
                or self._active_groups_file_path != active_file
                or self._active_groups_mtime != current_mtime
            ):

                logger.debug(f"Reloading active groups from {active_file}")
                with open(active_file, "r") as f:
                    self._active_groups_cache = [
                        line.strip() for line in f if line.strip()
                    ]
                self._active_groups_mtime = current_mtime
                self._active_groups_file_path = active_file
            else:
                logger.debug("Using cached active groups")
        else:
            # File doesn't exist, return empty list
            self._active_groups_cache = []
            self._active_groups_mtime = None

        return (
            self._active_groups_cache.copy()
        )  # Return a copy to prevent external modification

    def save_active_groups(self, active_groups: List[str]) -> None:
        """Save list of active groups to state file"""
        self.ensure_config_dir()
        active_file = self.get_active_groups_file()

        with open(active_file, "w") as f:
            for group in active_groups:
                f.write(f"{group}\n")

        # Invalidate cache by updating mtime
        self._active_groups_cache = active_groups.copy()
        self._active_groups_mtime = os.path.getmtime(active_file)
        self._active_groups_file_path = active_file

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

            # Create GroupData object (allow empty groups)
            new_group = GroupData(
                name=group_name,
                aliases=group_data["aliases"],
                env_vars=group_data["env_vars"],
                functions=group_data["functions"],
            )

            # Always add the group, even if empty
            self.groups.append(new_group)

            if new_group.total_items > 0:
                logger.debug(
                    f"Created group '{group_name}' with {len(group_data['aliases'])} aliases, "
                    f"{len(group_data['env_vars'])} env_vars, {len(group_data['functions'])} functions"
                )
            else:
                logger.debug(f"Created empty group '{group_name}'")

        logger.debug(
            f"Final groups loaded: {[g.name for g in self.groups]} (total: {len(self.groups)})"
        )

    def save(self) -> None:
        """Save the current configuration back to TOML file with secure escaping"""
        # Check if we should backup
        from .settings import Settings

        settings = Settings()

        if settings.behavior.backup_on_save and os.path.exists(self.config_path):
            # Create automatic backup
            from datetime import datetime

            backup_dir = os.path.join(os.path.dirname(self.config_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"config_auto_{timestamp}.toml")

            import shutil

            shutil.copy2(self.config_path, backup_path)
            logger.debug(f"Created automatic backup: {backup_path}")

            # Clean up old auto backups (keep last 10)
            auto_backups = sorted(
                [
                    f
                    for f in os.listdir(backup_dir)
                    if f.startswith("config_auto_") and f.endswith(".toml")
                ]
            )
            if len(auto_backups) > 10:
                for old_backup in auto_backups[:-10]:
                    os.remove(os.path.join(backup_dir, old_backup))

        # Save normally
        save_config_securely(self.config_path, self.groups)

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
        from .settings import Settings

        settings = Settings()

        # If shells are explicitly set in settings, use those
        if settings.generation.shells:
            logger.debug(f"Using shells from settings: {settings.generation.shells}")
            return settings.generation.shells

        # Otherwise auto-detect based on current shell
        current_shell = self.get_current_shell()
        if not current_shell:
            logger.debug("No current shell detected, using defaults")
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
        logger.debug(
            f"Auto-detected shells based on current shell '{current_shell}': {shells}"
        )
        return list(set(shells))  # Remove duplicates
