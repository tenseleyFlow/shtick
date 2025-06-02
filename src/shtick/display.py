"""
Display commands for shtick CLI - handles listing, status, and informational output
"""

import os
import sys
from shtick.config import Config
from shtick.shells import get_supported_shells


class DisplayCommands:
    """Handles all display/listing commands for shtick"""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def get_current_shell(self):
        """Detect the current shell"""
        shell_path = os.environ.get("SHELL", "")
        return os.path.basename(shell_path) if shell_path else None

    def status(self):
        """Show status of groups and active state"""
        config_path = Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            config.load()

            persistent_group = config.get_persistent_group()
            regular_groups = config.get_regular_groups()
            active_groups = config.load_active_groups()

            print("Shtick Status")
            print("=" * 40)

            # Show current shell integration status
            current_shell = self.get_current_shell()
            if current_shell:
                print(f"Current shell: {current_shell}")
                loader_path = os.path.expanduser(
                    f"~/.config/shtick/load_active.{current_shell}"
                )
                if os.path.exists(loader_path):
                    print(f"Loader file: ✓ exists")
                else:
                    print(f"Loader file: ✗ missing (run 'shtick generate')")
            print()

            # Show persistent group
            if persistent_group:
                total_persistent = (
                    len(persistent_group.aliases)
                    + len(persistent_group.env_vars)
                    + len(persistent_group.functions)
                )
                print(f"Persistent (always active): {total_persistent} items")
            else:
                print("Persistent: No items")

            print()

            # Show regular groups
            if regular_groups:
                print("Available Groups:")
                for group in regular_groups:
                    status = "ACTIVE" if group.name in active_groups else "inactive"
                    total_items = (
                        len(group.aliases) + len(group.env_vars) + len(group.functions)
                    )
                    print(f"  {group.name}: {total_items} items ({status})")
            else:
                print("No regular groups configured")

            print()

            # Show summary
            if active_groups:
                print(f"Currently active: {', '.join(active_groups)}")
            else:
                print("No groups currently active")

            print()
            print("Quick commands:")
            print("  shtick alias ll='ls -la'              # Add persistent alias")
            print("  shtick activate <group>               # Activate group")
            print('  eval "$(shtick source)"               # Load changes now')

        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            print("No configuration exists yet")
            print("\nGet started with:")
            print("  shtick alias ll='ls -la'")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def list_config(self, long_format: bool = False):
        """List current configuration"""
        config_path = Config.get_default_config_path()

        try:
            config = Config(config_path, debug=self.debug)
            config.load()

            if not config.groups:
                print("No groups configured")
                print("\nGet started with:")
                print("  shtick alias ll='ls -la'              # Add persistent alias")
                print("  shtick add alias work ll='ls -la'     # Add to 'work' group")
                print("  shtick activate work                  # Activate 'work' group")
                return

            persistent_group = config.get_persistent_group()
            regular_groups = config.get_regular_groups()
            active_groups = config.load_active_groups()

            if long_format:
                self._print_detailed_list(
                    persistent_group, regular_groups, active_groups
                )
            else:
                self._print_tabular_list(
                    persistent_group, regular_groups, active_groups
                )

        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            print("Use 'shtick alias <key>=<value>' to create your first alias")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def _print_detailed_list(self, persistent_group, regular_groups, active_groups):
        """Print detailed line-by-line list format"""
        # Show persistent group first
        if persistent_group:
            print("Group: persistent (always active)")
            self._print_group_items(persistent_group)
            print()

        # Show regular groups
        for group in regular_groups:
            status = " (ACTIVE)" if group.name in active_groups else " (inactive)"
            print(f"Group: {group.name}{status}")
            self._print_group_items(group)
            print()

    def _print_group_items(self, group):
        """Print items for a single group"""
        if group.aliases:
            print(f"  Aliases ({len(group.aliases)}):")
            for key, value in group.aliases.items():
                print(f"    {key} = {value}")
        if group.env_vars:
            print(f"  Environment Variables ({len(group.env_vars)}):")
            for key, value in group.env_vars.items():
                print(f"    {key} = {value}")
        if group.functions:
            print(f"  Functions ({len(group.functions)}):")
            for key, value in group.functions.items():
                print(f"    {key} = {value}")

    def _print_tabular_list(self, persistent_group, regular_groups, active_groups):
        """Print compact tabular list format"""
        # Collect all items for tabular display
        items = []

        # Add persistent items
        if persistent_group:
            items.extend(self._collect_group_items(persistent_group, "PERSISTENT"))

        # Add regular group items
        for group in regular_groups:
            status = "ACTIVE" if group.name in active_groups else "inactive"
            items.extend(self._collect_group_items(group, status))

        if not items:
            print("No items configured")
            return

        self._print_table(items)
        self._print_summary(items, active_groups)

    def _collect_group_items(self, group, status):
        """Collect items from a group for tabular display"""
        items = []
        for key, value in group.aliases.items():
            items.append((group.name, "alias", key, value, status))
        for key, value in group.env_vars.items():
            items.append((group.name, "env", key, value, status))
        for key, value in group.functions.items():
            items.append((group.name, "function", key, value, status))
        return items

    def _print_table(self, items):
        """Print items in tabular format"""
        # Calculate column widths
        max_group = max(max(len(item[0]) for item in items), 5)  # "Group"
        max_type = max(max(len(item[1]) for item in items), 4)  # "Type"
        max_key = max(max(len(item[2]) for item in items), 3)  # "Key"
        max_value = max(
            max(min(len(item[3]), 50) for item in items), 5
        )  # "Value" (limited)
        max_status = max(max(len(item[4]) for item in items), 6)  # "Status"

        # Print header
        header = f"{'Group':<{max_group}} {'Type':<{max_type}} {'Key':<{max_key}} {'Value':<{max_value}} {'Status':<{max_status}}"
        print(header)
        print("-" * len(header))

        # Print items
        for group, item_type, key, value, status in items:
            # Truncate long values with ellipsis
            display_value = (
                value if len(value) <= max_value else value[: max_value - 3] + "..."
            )
            print(
                f"{group:<{max_group}} {item_type:<{max_type}} {key:<{max_key}} {display_value:<{max_value}} {status:<{max_status}}"
            )

    def _print_summary(self, items, active_groups):
        """Print summary information"""
        print()
        total_items = len(items)
        active_items = len(
            [item for item in items if item[4] in ["ACTIVE", "PERSISTENT"]]
        )
        print(f"Total: {total_items} items ({active_items} active)")

        # Show available commands
        print()
        print("Use 'shtick list -l' for detailed view")
        if any(item[4] == "inactive" for item in items):
            inactive_groups = set(item[0] for item in items if item[4] == "inactive")
            print(f"Activate groups with: shtick activate <group>")
            print(f"Inactive groups: {', '.join(sorted(inactive_groups))}")

    def shells(self, long_format: bool = False):
        """List supported shells"""
        shells = sorted(get_supported_shells())

        if long_format:
            print("Supported shells:")
            for shell in shells:
                print(f"  {shell}")
        else:
            self._print_shells_columns(shells)

    def _print_shells_columns(self, shells):
        """Print shells in columns like ls output"""
        if not shells:
            print("No shells configured")
            return

        # Try to get terminal width, fallback to 80
        try:
            import shutil

            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80

        # Find the longest shell name
        max_shell_length = max(len(shell) for shell in shells)
        column_width = max_shell_length + 2

        # Calculate how many columns we can fit
        columns = max(1, terminal_width // column_width)
        rows = (len(shells) + columns - 1) // columns

        print(f"Supported shells ({len(shells)} total):")
        print()

        # Print shells in columns
        for row in range(rows):
            line = ""
            for col in range(columns):
                index = row + col * rows
                if index < len(shells):
                    shell = shells[index]
                    line += f"{shell:<{column_width}}"
            print(line.rstrip())
