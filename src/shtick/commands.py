"""
Command implementations for shtick CLI - FIXED WITH CONSISTENT RETURN STATUSES
"""

import os
import sys
import subprocess
import logging
from typing import Optional, List

from shtick.shtick import ShtickManager
from shtick.config import Config
from shtick.security import validate_assignment, validate_config_path

logger = logging.getLogger("shtick")


class ShtickCommands:
    """Central command handler for shtick operations - with consistent return codes"""

    def __init__(self, debug: bool = False):
        # Set up logging based on debug flag
        if debug:
            logging.basicConfig(
                level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
            )
        else:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

        self.manager = ShtickManager(debug=debug)

    def _exit_error(self, message: str, code: int = 1):
        """Print error message and exit with given code"""
        print(f"Error: {message}")
        sys.exit(code)

    def _exit_success(self, message: str = None, code: int = 0):
        """Print optional success message and exit with code"""
        if message:
            print(message)
        sys.exit(code)

    def get_current_shell(self) -> Optional[str]:
        """Use cached shell detection from Config"""
        return Config.get_current_shell()

    def validate_assignment(self, assignment: str) -> tuple[str, str]:
        """Use secure validation from security module"""
        return validate_assignment(assignment)

    def offer_auto_source(self):
        """Offer to source shtick in current shell session"""
        # Check settings first
        from shtick.settings import Settings

        settings = Settings()
        if not settings.behavior.auto_source_prompt:
            return

        current_shell = self.get_current_shell()
        if not current_shell or current_shell not in ["bash", "zsh", "fish"]:
            return

        loader_path = os.path.expanduser(
            f"~/.config/shtick/load_active.{current_shell}"
        )
        if not os.path.exists(loader_path):
            print("Loader file not found. Run 'shtick generate' first.")
            return

        try:
            response = (
                input(f"\nSource shtick in current {current_shell} session? [Y/n]: ")
                .strip()
                .lower()
            )
            if response in ["", "y", "yes"]:
                self._show_source_instructions(current_shell)
        except (KeyboardInterrupt, EOFError):
            print()

    def _show_source_instructions(self, shell: str):
        """Show instructions for sourcing"""
        print(f"\n🎯 Copy and paste this command to load changes immediately:")
        if shell == "fish":
            print(f"eval (shtick source)")
        else:
            print(f'eval "$(shtick source)"')

        print(f"\nOr run directly:")
        print(f"source ~/.config/shtick/load_active.{shell}")

        print("\n✨ Changes will be available in new shell sessions automatically.")
        self._show_eval_hint(shell)

    def _show_eval_hint(self, shell: str):
        """Show eval hint for easier future use"""
        print(f"\n💡 To automatically source shtick when making changes, use:")
        print(f'eval "$(shtick source)"')
        print(f"\nOr add this alias to your shell config:")
        if shell in ["bash", "zsh"]:
            print(f"alias ss='eval \"$(shtick source)\"'")
        elif shell == "fish":
            print(f"alias ss 'eval (shtick source)'")
        print(f"Then just run 'ss' after adding aliases!")

    def check_shell_integration(self):
        """Check if shtick is properly integrated with shell config"""
        current_shell = self.get_current_shell()
        if not current_shell:
            return

        shell_configs = {
            "bash": ["~/.bashrc", "~/.bash_profile"],
            "zsh": ["~/.zshrc", "~/.zprofile"],
            "fish": ["~/.config/fish/config.fish"],
        }

        if current_shell not in shell_configs:
            return

        loader_line = f"source ~/.config/shtick/load_active.{current_shell}"

        # Check if already integrated
        for config_file in shell_configs[current_shell]:
            expanded_path = os.path.expanduser(config_file)
            if os.path.exists(expanded_path):
                try:
                    with open(expanded_path, "r") as f:
                        content = f.read()
                        if "shtick" in content or loader_line in content:
                            return  # Already integrated
                except:
                    continue

        # Not integrated, offer to add
        try:
            print(
                f"\n🔧 Shtick is not integrated with your {current_shell} configuration."
            )
            print("This means your aliases won't be available in new shell sessions.")
            response = (
                input("Add shtick to your shell config automatically? [Y/n]: ")
                .strip()
                .lower()
            )
            if response in ["", "y", "yes"]:
                if self._add_shell_integration(
                    current_shell, shell_configs[current_shell]
                ):
                    print(
                        "\n✓ Integration complete! Your aliases will be available in new shell sessions."
                    )
                    print("To use them immediately in this session, run:")
                    print(f"  source ~/.config/shtick/load_active.{current_shell}")
            else:
                print(
                    f"\nTo manually integrate later, add this line to your {current_shell} config:"
                )
                print(f"  {loader_line}")
        except (KeyboardInterrupt, EOFError):
            print()

    def _add_shell_integration(self, shell: str, config_files: List[str]) -> bool:
        """Add shtick integration to shell config"""
        loader_line = f"source ~/.config/shtick/load_active.{shell}"

        # Try to find the best config file to modify
        for config_file in config_files:
            expanded_path = os.path.expanduser(config_file)
            if os.path.exists(expanded_path):
                try:
                    with open(expanded_path, "a") as f:
                        f.write(f"\n# Shtick shell configuration manager\n")
                        f.write(f"{loader_line}\n")
                    print(f"✓ Added shtick integration to {config_file}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to modify {config_file}: {e}")
                    continue

        # If no existing config file found, create the primary one
        primary_config = config_files[0]
        expanded_path = os.path.expanduser(primary_config)
        try:
            os.makedirs(os.path.dirname(expanded_path), exist_ok=True)
            with open(expanded_path, "w") as f:
                f.write(f"# Shtick shell configuration manager\n")
                f.write(f"{loader_line}\n")
            print(f"✓ Created {primary_config} with shtick integration")
            return True
        except Exception as e:
            logger.error(f"Failed to create {primary_config}: {e}")
            return False

    # Command implementations - now with consistent return statuses
    def generate(self, config_path: str = None, terse: bool = False):
        """Generate shell files from config"""
        try:
            if config_path:
                # Validate path for security with relaxed rules for generate
                validated_path = validate_config_path(config_path, for_generate=True)

                # Warn about custom config behavior
                if not terse:
                    print("Note: Generating from custom config file")
                    print("This will overwrite files but won't affect active groups")

                # Create a new manager with custom config path
                manager = ShtickManager(config_path=validated_path)
            else:
                manager = self.manager

            success = manager.generate_shell_files()
            if success:
                if not terse:
                    self.check_shell_integration()
                self._exit_success()  # Explicit success
            else:
                self._exit_error("Failed to generate shell files")

        except FileNotFoundError as e:
            self._exit_error(f"{e}\nCreate a config file first")
        except Exception as e:
            self._exit_error(str(e))

    def add_item(self, item_type: str, group: str, assignment: str):
        """Add an item to a specific group"""
        try:
            key, value = self.validate_assignment(assignment)
        except ValueError as e:
            self._exit_error(str(e))

        # Dispatch to appropriate manager method
        if item_type == "alias":
            success = self.manager.add_alias(key, value, group)
        elif item_type == "env":
            success = self.manager.add_env(key, value, group)
        elif item_type == "function":
            success = self.manager.add_function(key, value, group)
        else:
            self._exit_error(f"Unknown item type '{item_type}'")

        if success:
            print(f"✓ Added {item_type} '{key}' = '{value}' to group '{group}'")
            # Check if group is active and offer to source
            if (
                self.manager.get_active_groups()
                and group in self.manager.get_active_groups()
            ):
                self.offer_auto_source()
            self._exit_success()  # Explicit success
        else:
            self._exit_error(f"Failed to add {item_type}")

    def add_persistent(self, item_type: str, assignment: str):
        """Add an item to the persistent group"""
        try:
            key, value = self.validate_assignment(assignment)
        except ValueError as e:
            self._exit_error(str(e))

        is_first_time = not os.path.exists(Config.get_default_config_path())

        # Dispatch to appropriate manager method
        if item_type == "alias":
            success = self.manager.add_persistent_alias(key, value)
        elif item_type == "env":
            success = self.manager.add_persistent_env(key, value)
        elif item_type == "function":
            success = self.manager.add_persistent_function(key, value)
        else:
            self._exit_error(f"Unknown item type '{item_type}'")

        if success:
            print(
                f"✓ Added {item_type} '{key}' = '{value}' to persistent group (always active)"
            )
            self.offer_auto_source()

            # First-time setup experience
            if is_first_time:
                print("\n🎉 Welcome to shtick!")
                self.check_shell_integration()

            self._exit_success()  # Explicit success
        else:
            self._exit_error(f"Failed to add {item_type}")

    def remove_item(self, item_type: str, group: str, search: str):
        """Remove an item from a group"""
        try:
            # Use manager's list_items to find matches
            all_items = self.manager.list_items(group)
            matches = [
                item["key"]
                for item in all_items
                if item["type"] == item_type and search.lower() in item["key"].lower()
            ]

            if not matches:
                print(
                    f"No {item_type} items matching '{search}' found in group '{group}'"
                )
                self._exit_success()  # Not an error - nothing to remove

            # Handle single vs multiple matches
            item_to_remove = self._select_item_to_remove(matches)
            if not item_to_remove:
                self._exit_success()  # User cancelled - not an error

            # Dispatch to appropriate manager method
            if item_type == "alias":
                success = self.manager.remove_alias(item_to_remove, group)
            elif item_type == "env":
                success = self.manager.remove_env(item_to_remove, group)
            elif item_type == "function":
                success = self.manager.remove_function(item_to_remove, group)
            else:
                self._exit_error(f"Unknown item type '{item_type}'")

            if success:
                print(f"✓ Removed {item_type} '{item_to_remove}' from group '{group}'")
                # Offer to source if group is active
                if group == "persistent" or group in self.manager.get_active_groups():
                    self.offer_auto_source()
                self._exit_success()  # Explicit success
            else:
                self._exit_error(f"Failed to remove {item_type} '{item_to_remove}'")

        except Exception as e:
            self._exit_error(str(e))

    def _select_item_to_remove(self, matches: List[str]) -> Optional[str]:
        """Handle selection of item to remove from matches"""
        if len(matches) == 1:
            return matches[0]

        # Multiple matches, ask for confirmation
        print(f"Found {len(matches)} matches:")
        for i, item in enumerate(matches, 1):
            print(f"  {i}. {item}")

        try:
            choice = input("Enter number to remove (or 'q' to quit): ").strip()
            if choice.lower() == "q":
                print("Cancelled")
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                return matches[idx]
            else:
                print("Invalid choice")
                return None
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled")
            return None

    def activate_group(self, group_name: str):
        """Activate a group"""
        if group_name == "persistent":
            self._exit_error(
                "'persistent' group is always active and cannot be manually activated"
            )

        success = self.manager.activate_group(group_name)
        if success:
            print(f"✓ Activated group '{group_name}'")
            print("Changes are now active in new shell sessions")
            self.offer_auto_source()
            self._exit_success()  # Explicit success
        else:
            available = self.manager.get_groups()
            if available:
                self._exit_error(
                    f"Group '{group_name}' not found. Available groups: {', '.join(available)}"
                )
            else:
                self._exit_error(f"Group '{group_name}' not found in configuration")

    def deactivate_group(self, group_name: str):
        """Deactivate a group"""
        if group_name == "persistent":
            self._exit_error("'persistent' group cannot be deactivated")

        success = self.manager.deactivate_group(group_name)
        if success:
            print(f"✓ Deactivated group '{group_name}'")
            print("Changes will take effect in new shell sessions")
            self.offer_auto_source()
        else:
            print(f"Group '{group_name}' was not active")
            # Not an error - deactivating inactive group is idempotent

        self._exit_success()  # Always exit success for idempotent operation

    def source_command(self, shell: str = None):
        """Output source command for eval"""
        current_shell = shell or self.get_current_shell()

        if not current_shell:
            print("Could not detect shell. Use --shell to specify.", file=sys.stderr)
            sys.exit(1)

        loader_path = os.path.expanduser(
            f"~/.config/shtick/load_active.{current_shell}"
        )
        if not os.path.exists(loader_path):
            print(f"Loader file not found: {loader_path}", file=sys.stderr)
            print("Run 'shtick generate' first.", file=sys.stderr)
            sys.exit(1)

        # Output the source command that can be eval'd
        print(f"source {loader_path}")
        self._exit_success()  # Explicit success

    # Settings commands
    def settings_init(self):
        """Initialize settings file with defaults"""
        from shtick.settings import Settings

        settings = Settings()

        if os.path.exists(settings._settings_path):
            try:
                response = (
                    input("Settings file already exists. Overwrite? [y/N]: ")
                    .strip()
                    .lower()
                )
                if response not in ["y", "yes"]:
                    print("Cancelled")
                    self._exit_success()  # User cancelled - not an error
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled")
                self._exit_error("Operation cancelled by user", code=2)

        settings.create_default_settings_file()
        print(f"✓ Created settings file at {settings._settings_path}")
        print("\nYou can now customize your shtick behavior by editing this file.")
        self._exit_success()  # Explicit success

    def settings_show(self):
        """Show current settings"""
        from shtick.settings import Settings

        settings = Settings()

        print("Shtick Settings")
        print("=" * 50)

        print("\n[generation]")
        print(f"  shells = {settings.generation.shells or '[] (auto-detect)'}")
        print(f"  parallel = {settings.generation.parallel}")
        print(f"  consolidate_files = {settings.generation.consolidate_files}")

        print("\n[behavior]")
        print(f"  auto_source_prompt = {settings.behavior.auto_source_prompt}")
        print(f"  check_conflicts = {settings.behavior.check_conflicts}")
        print(f"  backup_on_save = {settings.behavior.backup_on_save}")
        print(f"  interactive_mode = {settings.behavior.interactive_mode}")

        print("\n[performance]")
        print(f"  cache_ttl = {settings.performance.cache_ttl}")
        print(f"  lazy_load = {settings.performance.lazy_load}")
        print(f"  batch_operations = {settings.performance.batch_operations}")

        print(f"\nSettings file: {settings._settings_path}")
        if not os.path.exists(settings._settings_path):
            print("(No settings file found - using defaults)")
            print("Run 'shtick settings init' to create one")

        self._exit_success()  # Explicit success

    def settings_set(self, key: str, value: str):
        """Set a specific setting value"""
        from shtick.settings import Settings

        settings = Settings()

        # Parse the key (e.g., "generation.shells")
        parts = key.split(".")
        if len(parts) != 2:
            self._exit_error(
                "Invalid key format. Use 'section.key' (e.g., 'generation.shells')"
            )

        section, setting_key = parts

        # Validate section
        if section not in ["generation", "behavior", "performance"]:
            self._exit_error(
                f"Invalid section '{section}'. Must be one of: generation, behavior, performance"
            )

        # Get the section object
        section_obj = getattr(settings, section)

        # Check if key exists
        if not hasattr(section_obj, setting_key):
            print(f"Error: Invalid key '{setting_key}' for section '{section}'")
            print(f"Valid keys: {', '.join(vars(section_obj).keys())}")
            self._exit_error(f"Invalid key '{setting_key}'")

        # Parse the value based on type
        current_value = getattr(section_obj, setting_key)
        try:
            if isinstance(current_value, bool):
                # Parse boolean
                if value.lower() in ["true", "1", "yes", "on"]:
                    parsed_value = True
                elif value.lower() in ["false", "0", "no", "off"]:
                    parsed_value = False
                else:
                    raise ValueError(f"Invalid boolean value: {value}")
            elif isinstance(current_value, int):
                # Parse integer
                parsed_value = int(value)
            elif isinstance(current_value, list):
                # Parse list (simple eval for now - could be improved)
                if value == "[]":
                    parsed_value = []
                elif value.startswith("[") and value.endswith("]"):
                    # Simple parsing - just split by comma
                    parsed_value = [
                        s.strip().strip("\"'")
                        for s in value[1:-1].split(",")
                        if s.strip()
                    ]
                else:
                    # Single value becomes a list
                    parsed_value = [value]
            else:
                # String value
                parsed_value = value
        except Exception as e:
            self._exit_error(f"Error parsing value: {e}")

        # Set the value
        setattr(section_obj, setting_key, parsed_value)

        # Save settings
        try:
            settings.save()
            print(f"✓ Set {key} = {parsed_value}")
            print(f"Settings saved to {settings._settings_path}")
            self._exit_success()  # Explicit success
        except Exception as e:
            self._exit_error(f"Failed to save settings: {e}")

    # Group management commands
    def group_create(self, name: str, description: str = None):
        """Create a new group"""
        try:
            # Check if group already exists
            if self.manager.get_groups() and name in self.manager.get_groups():
                self._exit_error(f"Group '{name}' already exists")

            # Actually create the empty group
            from shtick.config import Config, GroupData

            config = self.manager._get_config()

            # Add the new empty group
            new_group = GroupData(name=name, aliases={}, env_vars={}, functions={})
            config.groups.append(new_group)

            # Save the config with the new empty group
            config.save()

            print(f"✓ Created group '{name}'")
            print(f"\nAdd items to this group with:")
            print(f"  shtick add alias {name} ll='ls -la'")
            print(f"  shtick add env {name} DEBUG=1")
            print(f"\nActivate with:")
            print(f"  shtick activate {name}")

            self._exit_success()
        except Exception as e:
            self._exit_error(str(e))

    def group_rename(self, old_name: str, new_name: str):
        """Rename a group"""
        # This would require refactoring the config to support renaming
        # For now, just indicate it's not implemented
        self._exit_error("Group rename is not yet implemented")

    def group_remove(self, name: str, force: bool = False):
        """Remove a group"""
        # This would require refactoring the config to support group removal
        # For now, just indicate it's not implemented
        self._exit_error("Group removal is not yet implemented")

    # Backup commands
    def backup_create(self, name: str = None):
        """Create a backup"""
        try:
            backup_path = self.manager.backup_config(name)
            print(f"✓ Created backup: {backup_path}")
            self._exit_success()
        except Exception as e:
            self._exit_error(f"Failed to create backup: {e}")

    def backup_list(self):
        """List available backups"""
        try:
            backups = self.manager.list_backups()
            if not backups:
                print("No backups found")
            else:
                print("Available backups:")
                for backup in backups:
                    from datetime import datetime

                    mtime = datetime.fromtimestamp(backup["modified"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    size_kb = backup["size"] / 1024
                    print(f"  {backup['name']} ({size_kb:.1f} KB, modified: {mtime})")
            self._exit_success()
        except Exception as e:
            self._exit_error(f"Failed to list backups: {e}")

    def backup_restore(self, name: str):
        """Restore from backup"""
        try:
            if self.manager.restore_backup(name):
                print(f"✓ Restored from backup: {name}")
                print("Run 'shtick generate' to regenerate shell files")
                self._exit_success()
            else:
                self._exit_error(f"Backup '{name}' not found")
        except Exception as e:
            self._exit_error(f"Failed to restore backup: {e}")


# Return code conventions:
# 0 - Success
# 1 - General error (invalid arguments, missing files, etc.)
# 2 - User cancelled operation
# 3 - Permission denied (currently not used, but reserved)
# 4 - Resource not found when it should exist (currently not used, but reserved)
