"""
Command implementations for shtick CLI
"""

import os
import sys
import subprocess
from typing import Optional, List

from shtick.config import Config
from shtick.generator import Generator
from shtick.shells import get_supported_shells


class ShtickCommands:
    """Central command handler for shtick operations"""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def get_current_shell(self) -> Optional[str]:
        """Detect the current shell"""
        shell_path = os.environ.get("SHELL", "")
        return os.path.basename(shell_path) if shell_path else None

    def validate_assignment(self, assignment: str) -> tuple[str, str]:
        """Validate key=value assignment format and return key, value"""
        if "=" not in assignment:
            raise ValueError("Assignment must be in format key=value")

        key, value = assignment.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key or not value:
            raise ValueError("Both key and value must be non-empty")

        # Validate key format (basic shell identifier rules)
        if not key.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Key must contain only letters, numbers, underscores, and hyphens"
            )

        return key, value

    def check_conflicts(
        self, config: Config, item_type: str, group_name: str, key: str
    ) -> List[str]:
        """Check for potential conflicts and warn user"""
        warnings = []

        # Check if item already exists in same group
        group = config.get_group(group_name)
        if group:
            existing_value = None
            if item_type == "alias" and key in group.aliases:
                existing_value = group.aliases[key]
            elif item_type == "env" and key in group.env_vars:
                existing_value = group.env_vars[key]
            elif item_type == "function" and key in group.functions:
                existing_value = group.functions[key]

            if existing_value:
                warnings.append(
                    f"Will overwrite existing {item_type} '{key}' = '{existing_value}' in group '{group_name}'"
                )

        # Check if item exists in other groups
        for other_group in config.groups:
            if other_group.name == group_name:
                continue

            if item_type == "alias" and key in other_group.aliases:
                warnings.append(
                    f"Alias '{key}' also exists in group '{other_group.name}' = '{other_group.aliases[key]}'"
                )
            elif item_type == "env" and key in other_group.env_vars:
                warnings.append(
                    f"Environment variable '{key}' also exists in group '{other_group.name}' = '{other_group.env_vars[key]}'"
                )
            elif item_type == "function" and key in other_group.functions:
                warnings.append(
                    f"Function '{key}' also exists in group '{other_group.name}' = '{other_group.functions[key]}'"
                )

        return warnings

    def handle_warnings(self, warnings: List[str]) -> bool:
        """Handle conflict warnings and return True if user wants to continue"""
        if not warnings:
            return True

        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        try:
            response = input("Continue anyway? [y/N]: ").strip().lower()
            return response in ["y", "yes"]
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled")
            return False

    def regenerate_and_offer_source(self, config: Config, group_name: str = None):
        """Regenerate shell files and offer auto-sourcing"""
        try:
            generator = Generator()

            if group_name:
                group = config.get_group(group_name)
                if group:
                    generator.generate_for_group(group)
            else:
                # Regenerate all groups
                for group in config.groups:
                    generator.generate_for_group(group)

            generator.generate_loader(config)
            print("✓ Regenerated shell files")
            self.offer_auto_source()
        except Exception as e:
            print(f"Warning: Failed to regenerate files: {e}")
            print("Run 'shtick generate' to update shell files")

    def offer_auto_source(self):
        """Offer to source shtick in current shell session"""
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
                # Test syntax first
                if self._test_loader_syntax(current_shell, loader_path):
                    self._show_source_instructions(current_shell)
        except (KeyboardInterrupt, EOFError):
            print()

    def _test_loader_syntax(self, shell: str, loader_path: str) -> bool:
        """Test loader file syntax and return True if valid"""
        try:
            test_response = (
                input("Test the loader file for syntax errors? [Y/n]: ").strip().lower()
            )
            if test_response not in ["", "y", "yes"]:
                return True

            result = subprocess.run(
                [shell, "-c", f'source "{loader_path}"'],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print("✓ Loader file syntax is valid")
                return True
            else:
                print("✗ Loader file has syntax errors:")
                print(result.stderr)
                print("Please fix the errors before sourcing.")
                return False
        except subprocess.TimeoutExpired:
            print("✓ Loader file appears to work (test timed out, which is normal)")
            return True
        except Exception as e:
            print(f"Could not test loader file: {e}")
            return True

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
                    print(f"✗ Failed to modify {config_file}: {e}")
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
            print(f"✗ Failed to create {primary_config}: {e}")
            return False

    # Command implementations
    def generate(self, config_path: str = None, terse: bool = False):
        """Generate shell files from config"""
        config_path = config_path or Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            config.load()

            generator = Generator()
            generator.generate_all(config, interactive=not terse)

            if not terse:
                self.check_shell_integration()

        except FileNotFoundError as e:
            print(f"Error: {e}")
            print(f"Create a config file at {config_path} first")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def add_item(self, item_type: str, group: str, assignment: str):
        """Add an item to a specific group"""
        try:
            key, value = self.validate_assignment(assignment)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        config_path = Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            try:
                config.load()
            except FileNotFoundError:
                print(f"Creating new config file at {config_path}")

            # Check for conflicts and get user confirmation
            warnings = self.check_conflicts(config, item_type, group, key)
            if not self.handle_warnings(warnings):
                return

            config.add_item(item_type, group, key, value)
            config.save()

            print(f"✓ Added {item_type} '{key}' = '{value}' to group '{group}'")

            # Auto-regenerate if group is active
            if config.is_group_active(group) or group == "persistent":
                self.regenerate_and_offer_source(config, group)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def add_persistent(self, item_type: str, assignment: str):
        """Add an item to the persistent group"""
        try:
            key, value = self.validate_assignment(assignment)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        config_path = Config.get_default_config_path()
        is_first_time = not os.path.exists(config_path)

        try:
            config = Config(config_path, debug=self.debug)
            try:
                config.load()
            except FileNotFoundError:
                print(f"Creating new config file at {config_path}")

            # Check for conflicts
            warnings = self.check_conflicts(config, item_type, "persistent", key)
            if not self.handle_warnings(warnings):
                return

            config.add_item(item_type, "persistent", key, value)
            config.save()

            print(
                f"✓ Added {item_type} '{key}' = '{value}' to persistent group (always active)"
            )

            # Auto-regenerate files
            self.regenerate_and_offer_source(config, "persistent")

            # First-time setup experience
            if is_first_time:
                print("\n🎉 Welcome to shtick!")
                self.check_shell_integration()

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def remove_item(self, item_type: str, group: str, search: str):
        """Remove an item from a group"""
        config_path = Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            config.load()

            # Find matching items
            matches = config.find_items(item_type, group, search)

            if not matches:
                print(
                    f"No {item_type} items matching '{search}' found in group '{group}'"
                )
                return

            # Handle single vs multiple matches
            item_to_remove = self._select_item_to_remove(matches)
            if not item_to_remove:
                return

            if config.remove_item(item_type, group, item_to_remove):
                config.save()
                print(f"✓ Removed {item_type} '{item_to_remove}' from group '{group}'")

                # Auto-regenerate if group is active
                if config.is_group_active(group) or group == "persistent":
                    self.regenerate_and_offer_source(config, group)
            else:
                print(f"Failed to remove {item_type} '{item_to_remove}'")

        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

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
        config_path = Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            config.load()

            if group_name == "persistent":
                print(
                    "Error: 'persistent' group is always active and cannot be manually activated"
                )
                return

            if config.activate_group(group_name):
                self.regenerate_and_offer_source(config)
                print(f"✓ Activated group '{group_name}'")
                print("Changes are now active in new shell sessions")
            else:
                print(f"Error: Group '{group_name}' not found in configuration")
                available = [g.name for g in config.get_regular_groups()]
                if available:
                    print(f"Available groups: {', '.join(available)}")

        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            print("Run 'shtick generate' first or add some items with 'shtick add'")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def deactivate_group(self, group_name: str):
        """Deactivate a group"""
        config_path = Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            config.load()

            if group_name == "persistent":
                print("Error: 'persistent' group cannot be deactivated")
                return

            if config.deactivate_group(group_name):
                # Only need to regenerate loader for deactivation
                try:
                    generator = Generator()
                    generator.generate_loader(config)
                    print("✓ Regenerated shell files")
                except Exception as e:
                    print(f"Warning: Failed to regenerate files: {e}")

                print(f"✓ Deactivated group '{group_name}'")
                print("Changes will take effect in new shell sessions")
                self.offer_auto_source()
            else:
                print(f"Group '{group_name}' was not active")

        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

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
