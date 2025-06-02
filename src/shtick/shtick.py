"""
High-level API for shtick - provides a clean programmatic interface
"""

import os
import logging
from typing import List, Dict, Optional, Union, Tuple
from .config import Config, GroupData
from .generator import Generator

logger = logging.getLogger("shtick")


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

        # Set up logging
        if debug:
            logging.basicConfig(
                level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
            )
        else:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

        self._config = None
        self._generator = Generator()

    def _load_config(self, create_if_missing: bool = True) -> Config:
        """Load or reload the configuration"""
        try:
            config = Config(self.config_path)
            config.load()
            self._config = config
            return config
        except FileNotFoundError:
            if create_if_missing:
                logger.debug("Creating new config file")
                # Create empty config
                config = Config(self.config_path)
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

    def _save_and_regenerate(self, affected_groups: Optional[List[str]] = None) -> None:
        """Save config and regenerate shell files"""
        config = self._get_config()
        config.save()

        # Regenerate shell files for affected groups
        if affected_groups:
            for group_name in affected_groups:
                group = config.get_group(group_name)
                if group:
                    self._generator.generate_for_group(group)
        else:
            # Regenerate all
            for group in config.groups:
                self._generator.generate_for_group(group)

        # Always regenerate loader
        self._generator.generate_loader(config)

    def check_conflicts(
        self, item_type: str, key: str, group_name: str
    ) -> List[Tuple[str, str]]:
        """
        Check for conflicts across all groups.

        Returns:
            List of tuples (group_name, existing_value) for conflicts
        """
        config = self._get_config()
        conflicts = []

        for group in config.groups:
            if group.has_item(item_type, key):
                existing_value = group.get_item_value(item_type, key)
                conflicts.append((group.name, existing_value))

        return conflicts

    # Alias management
    def add_persistent_alias(
        self, key: str, value: str, check_conflicts: bool = True
    ) -> bool:
        """
        Add a persistent alias (always active).

        Args:
            key: Alias name
            value: Alias command
            check_conflicts: Whether to check for conflicts

        Returns:
            True if successful
        """
        return self._add_item("alias", "persistent", key, value, check_conflicts)

    def add_alias(
        self, key: str, value: str, group: str, check_conflicts: bool = True
    ) -> bool:
        """
        Add an alias to a specific group.

        Args:
            key: Alias name
            value: Alias command
            group: Group name
            check_conflicts: Whether to check for conflicts

        Returns:
            True if successful
        """
        return self._add_item("alias", group, key, value, check_conflicts)

    def remove_alias(self, key: str, group: str = "persistent") -> bool:
        """
        Remove an alias from a group.

        Args:
            key: Alias name to remove
            group: Group name (defaults to persistent)

        Returns:
            True if successful
        """
        return self._remove_item("alias", group, key)

    # Environment variable management
    def add_persistent_env(
        self, key: str, value: str, check_conflicts: bool = True
    ) -> bool:
        """
        Add a persistent environment variable (always active).

        Args:
            key: Variable name
            value: Variable value
            check_conflicts: Whether to check for conflicts

        Returns:
            True if successful
        """
        return self._add_item("env", "persistent", key, value, check_conflicts)

    def add_env(
        self, key: str, value: str, group: str, check_conflicts: bool = True
    ) -> bool:
        """
        Add an environment variable to a specific group.

        Args:
            key: Variable name
            value: Variable value
            group: Group name
            check_conflicts: Whether to check for conflicts

        Returns:
            True if successful
        """
        return self._add_item("env", group, key, value, check_conflicts)

    def remove_env(self, key: str, group: str = "persistent") -> bool:
        """
        Remove an environment variable from a group.

        Args:
            key: Variable name to remove
            group: Group name (defaults to persistent)

        Returns:
            True if successful
        """
        return self._remove_item("env", group, key)

    # Function management
    def add_persistent_function(
        self, key: str, value: str, check_conflicts: bool = True
    ) -> bool:
        """
        Add a persistent function (always active).

        Args:
            key: Function name
            value: Function body
            check_conflicts: Whether to check for conflicts

        Returns:
            True if successful
        """
        return self._add_item("function", "persistent", key, value, check_conflicts)

    def add_function(
        self, key: str, value: str, group: str, check_conflicts: bool = True
    ) -> bool:
        """
        Add a function to a specific group.

        Args:
            key: Function name
            value: Function body
            group: Group name
            check_conflicts: Whether to check for conflicts

        Returns:
            True if successful
        """
        return self._add_item("function", group, key, value, check_conflicts)

    def remove_function(self, key: str, group: str = "persistent") -> bool:
        """
        Remove a function from a group.

        Args:
            key: Function name to remove
            group: Group name (defaults to persistent)

        Returns:
            True if successful
        """
        return self._remove_item("function", group, key)

    # Generic item management
    def _add_item(
        self,
        item_type: str,
        group_name: str,
        key: str,
        value: str,
        check_conflicts: bool,
    ) -> bool:
        """Generic method to add any item type"""
        try:
            config = self._get_config()

            # Check for conflicts if requested
            if check_conflicts:
                conflicts = self.check_conflicts(item_type, key, group_name)
                if conflicts:
                    logger.warning(
                        f"Item '{key}' exists in groups: {[c[0] for c in conflicts]}"
                    )
                    # Still proceed but warn

            config.add_item(item_type, group_name, key, value)

            # Only regenerate files for affected group if it's active
            affected_groups = []
            if group_name == "persistent" or config.is_group_active(group_name):
                affected_groups.append(group_name)

            self._save_and_regenerate(affected_groups)
            return True

        except Exception as e:
            logger.error(f"Error adding {item_type}: {e}")
            return False

    def _remove_item(self, item_type: str, group_name: str, key: str) -> bool:
        """Generic method to remove any item type"""
        try:
            config = self._get_config()
            success = config.remove_item(item_type, group_name, key)

            if success:
                # Only regenerate if group is active
                affected_groups = []
                if group_name == "persistent" or config.is_group_active(group_name):
                    affected_groups.append(group_name)

                self._save_and_regenerate(affected_groups)

            return success

        except Exception as e:
            logger.error(f"Error removing {item_type}: {e}")
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
                self._generator.generate_loader(config)
            return success
        except Exception as e:
            logger.error(f"Error activating group: {e}")
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
                self._generator.generate_loader(config)
            return success
        except Exception as e:
            logger.error(f"Error deactivating group: {e}")
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

            current_shell = Config.get_current_shell() or ""
            loader_exists = False
            if current_shell:
                loader_path = os.path.expanduser(
                    f"~/.config/shtick/load_active.{current_shell}"
                )
                loader_exists = os.path.exists(loader_path)

            persistent_count = persistent_group.total_items if persistent_group else 0

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
                # Process each item type
                for item_type in ["alias", "env", "function"]:
                    item_dict = g.get_items(item_type)
                    for key, value in item_dict.items():
                        items.append(
                            {
                                "group": g.name,
                                "type": item_type,
                                "key": key,
                                "value": value,
                                "active": config.is_group_active(g.name)
                                or g.name == "persistent",
                            }
                        )

            return items
        except Exception as e:
            logger.error(f"Error listing items: {e}")
            return []

    def generate_shell_files(self) -> bool:
        """
        Regenerate all shell files.

        Returns:
            True if successful
        """
        try:
            config = self._get_config()
            self._generator.generate_all(config, interactive=False)
            return True
        except Exception as e:
            logger.error(f"Error generating shell files: {e}")
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
            current_shell = shell or Config.get_current_shell()
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
