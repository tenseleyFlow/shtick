"""
High-level API for shtick - provides a clean programmatic interface
"""

import os
from typing import List, Dict, Optional, Union
from .config import Config, GroupData
from .generator import Generator
from .commands import ShtickCommands


class ShtickManager:
    """
    High-level interface for managing shtick configurations programmatically.

    This class provides a clean Python API for all shtick operations without
    needing to use the CLI. Perfect for integration into other tools, scripts,
    or applications.

    Example:
        >>> from shtick import ShtickManager
        >>> manager = ShtickManager()
        >>> manager.add_persistent_alias('ll', 'ls -la')
        True
        >>> manager.activate_group('work')
        True
        >>> status = manager.get_status()
        >>> print(status['active_groups'])
        ['work']
    """

    def __init__(self, config_path: Optional[str] = None, debug: bool = False):
        """
        Initialize the ShtickManager.

        Args:
            config_path: Path to config file (uses default if None)
            debug: Enable debug output
        """
        self.config_path = config_path or Config.get_default_config_path()
        self.debug = debug
        self._config = None
        self._commands = ShtickCommands(debug=debug)

    def _load_config(self, create_if_missing: bool = True) -> Config:
        """Load or reload the configuration"""
        try:
            config = Config(self.config_path, debug=self.debug)
            config.load()
            self._config = config
            return config
        except FileNotFoundError:
            if create_if_missing:
                # Create empty config
                config = Config(self.config_path, debug=self.debug)
                config.ensure_config_dir()
                config.save()
                self._config = config
                return config
            else:
                raise

    def _get_config(self) -> Config:
        """Get current config, loading if necessary"""
        if self._config is None:
            return self._load_config()
        return self._config

    def _save_and_regenerate(self) -> None:
        """Save config and regenerate shell files"""
        config = self._get_config()
        config.save()

        # Regenerate shell files
        generator = Generator()
        for group in config.groups:
            generator.generate_for_group(group)
        generator.generate_loader(config)

    # Alias management
    def add_persistent_alias(self, key: str, value: str) -> bool:
        """
        Add a persistent alias (always active).

        Args:
            key: Alias name
            value: Alias command

        Returns:
            True if successful

        Example:
            >>> manager.add_persistent_alias('ll', 'ls -la')
            True
        """
        try:
            config = self._get_config()
            config.add_item("alias", "persistent", key, value)
            self._save_and_regenerate()
            return True
        except Exception as e:
            if self.debug:
                print(f"Error adding persistent alias: {e}")
            return False

    def add_alias(self, key: str, value: str, group: str) -> bool:
        """
        Add an alias to a specific group.

        Args:
            key: Alias name
            value: Alias command
            group: Group name

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            config.add_item("alias", group, key, value)
            self._save_and_regenerate()
            return True
        except Exception as e:
            if self.debug:
                print(f"Error adding alias: {e}")
            return False

    def remove_alias(self, key: str, group: str = "persistent") -> bool:
        """
        Remove an alias from a group.

        Args:
            key: Alias name to remove
            group: Group name (defaults to persistent)

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            success = config.remove_item("alias", group, key)
            if success:
                self._save_and_regenerate()
            return success
        except Exception as e:
            if self.debug:
                print(f"Error removing alias: {e}")
            return False

    # Environment variable management
    def add_persistent_env(self, key: str, value: str) -> bool:
        """
        Add a persistent environment variable (always active).

        Args:
            key: Variable name
            value: Variable value

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            config.add_item("env", "persistent", key, value)
            self._save_and_regenerate()
            return True
        except Exception as e:
            if self.debug:
                print(f"Error adding persistent env var: {e}")
            return False

    def add_env(self, key: str, value: str, group: str) -> bool:
        """
        Add an environment variable to a specific group.

        Args:
            key: Variable name
            value: Variable value
            group: Group name

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            config.add_item("env", group, key, value)
            self._save_and_regenerate()
            return True
        except Exception as e:
            if self.debug:
                print(f"Error adding env var: {e}")
            return False

    def remove_env(self, key: str, group: str = "persistent") -> bool:
        """
        Remove an environment variable from a group.

        Args:
            key: Variable name to remove
            group: Group name (defaults to persistent)

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            success = config.remove_item("env", group, key)
            if success:
                self._save_and_regenerate()
            return success
        except Exception as e:
            if self.debug:
                print(f"Error removing env var: {e}")
            return False

    # Function management
    def add_persistent_function(self, key: str, value: str) -> bool:
        """
        Add a persistent function (always active).

        Args:
            key: Function name
            value: Function body

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            config.add_item("function", "persistent", key, value)
            self._save_and_regenerate()
            return True
        except Exception as e:
            if self.debug:
                print(f"Error adding persistent function: {e}")
            return False

    def add_function(self, key: str, value: str, group: str) -> bool:
        """
        Add a function to a specific group.

        Args:
            key: Function name
            value: Function body
            group: Group name

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            config.add_item("function", group, key, value)
            self._save_and_regenerate()
            return True
        except Exception as e:
            if self.debug:
                print(f"Error adding function: {e}")
            return False

    def remove_function(self, key: str, group: str = "persistent") -> bool:
        """
        Remove a function from a group.

        Args:
            key: Function name to remove
            group: Group name (defaults to persistent)

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            success = config.remove_item("function", group, key)
            if success:
                self._save_and_regenerate()
            return success
        except Exception as e:
            if self.debug:
                print(f"Error removing function: {e}")
            return False

    # Group management
    def activate_group(self, group: str) -> bool:
        """
        Activate a group.

        Args:
            group: Group name to activate

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            success = config.activate_group(group)
            if success:
                generator = Generator()
                generator.generate_loader(config)
            return success
        except Exception as e:
            if self.debug:
                print(f"Error activating group: {e}")
            return False

    def deactivate_group(self, group: str) -> bool:
        """
        Deactivate a group.

        Args:
            group: Group name to deactivate

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            success = config.deactivate_group(group)
            if success:
                generator = Generator()
                generator.generate_loader(config)
            return success
        except Exception as e:
            if self.debug:
                print(f"Error deactivating group: {e}")
            return False

    def get_active_groups(self) -> List[str]:
        """
        Get list of currently active groups.

        Returns:
            List of active group names
        """
        try:
            config = self._get_config()
            return config.load_active_groups()
        except Exception:
            return []

    def get_groups(self) -> List[str]:
        """
        Get list of all available groups.

        Returns:
            List of all group names
        """
        try:
            config = self._get_config()
            return [group.name for group in config.groups]
        except Exception:
            return []

    # Information and status
    def get_status(self) -> Dict[str, Union[str, int, List[str], bool]]:
        """
        Get current shtick status.

        Returns:
            Dictionary with status information
        """
        try:
            config = self._get_config()
            persistent_group = config.get_persistent_group()
            regular_groups = config.get_regular_groups()
            active_groups = config.load_active_groups()

            current_shell = os.path.basename(os.environ.get("SHELL", ""))
            loader_exists = False
            if current_shell:
                loader_path = os.path.expanduser(
                    f"~/.config/shtick/load_active.{current_shell}"
                )
                loader_exists = os.path.exists(loader_path)

            persistent_count = 0
            if persistent_group:
                persistent_count = (
                    len(persistent_group.aliases)
                    + len(persistent_group.env_vars)
                    + len(persistent_group.functions)
                )

            return {
                "current_shell": current_shell,
                "loader_exists": loader_exists,
                "persistent_items": persistent_count,
                "total_groups": len(regular_groups),
                "active_groups": active_groups,
                "available_groups": [g.name for g in regular_groups],
                "config_path": self.config_path,
            }
        except Exception as e:
            return {
                "error": str(e),
                "current_shell": "",
                "loader_exists": False,
                "persistent_items": 0,
                "total_groups": 0,
                "active_groups": [],
                "available_groups": [],
                "config_path": self.config_path,
            }

    def list_items(self, group: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all items, optionally filtered by group.

        Args:
            group: Optional group name to filter by

        Returns:
            List of dictionaries with item information
        """
        try:
            config = self._get_config()
            items = []

            groups_to_check = [config.get_group(group)] if group else config.groups
            groups_to_check = [g for g in groups_to_check if g is not None]

            for g in groups_to_check:
                # Add aliases
                for key, value in g.aliases.items():
                    items.append(
                        {
                            "group": g.name,
                            "type": "alias",
                            "key": key,
                            "value": value,
                            "active": config.is_group_active(g.name)
                            or g.name == "persistent",
                        }
                    )

                # Add env vars
                for key, value in g.env_vars.items():
                    items.append(
                        {
                            "group": g.name,
                            "type": "env",
                            "key": key,
                            "value": value,
                            "active": config.is_group_active(g.name)
                            or g.name == "persistent",
                        }
                    )

                # Add functions
                for key, value in g.functions.items():
                    items.append(
                        {
                            "group": g.name,
                            "type": "function",
                            "key": key,
                            "value": value,
                            "active": config.is_group_active(g.name)
                            or g.name == "persistent",
                        }
                    )

            return items
        except Exception as e:
            if self.debug:
                print(f"Error listing items: {e}")
            return []

    def generate_shell_files(self) -> bool:
        """
        Regenerate all shell files.

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            generator = Generator()
            for group in config.groups:
                generator.generate_for_group(group)
            generator.generate_loader(config)
            return True
        except Exception as e:
            if self.debug:
                print(f"Error generating shell files: {e}")
            return False

    def get_source_command(self, shell: Optional[str] = None) -> Optional[str]:
        """
        Get the source command for loading shtick in current session.

        Args:
            shell: Shell type (auto-detected if None)

        Returns:
            Source command string or None if not available
        """
        try:
            current_shell = shell or os.path.basename(os.environ.get("SHELL", ""))
            if not current_shell:
                return None

            loader_path = os.path.expanduser(
                f"~/.config/shtick/load_active.{current_shell}"
            )
            if os.path.exists(loader_path):
                return f"source {loader_path}"
            else:
                return None
        except Exception:
            return None
