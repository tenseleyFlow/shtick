"""
Display commands for shtick CLI - handles listing, status, and informational output
"""

import os
import sys
import logging
from shtick.config import Config
from shtick.shells import get_supported_shells
from shtick.shtick import ShtickManager

logger = logging.getLogger("shtick")


class DisplayCommands:
    """Handles all display/listing commands for shtick"""

    def __init__(self, debug: bool = False):
        # Set up logging
        if debug:
            logging.basicConfig(
                level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
            )
        else:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

        self.manager = ShtickManager(debug=debug)

    def get_current_shell(self):
        """Use cached shell detection from Config"""
        return Config.get_current_shell()

    def status(self):
        """Show status of groups and active state"""
        status = self.manager.get_status()

        if "error" in status:
            print(f"Error loading configuration: {status['error']}")
            print("\nGet started with:")
            print("  shtick alias ll='ls -la'")
            return

        print("Shtick Status")
        print("=" * 40)

        # Show current shell integration status
        if status["current_shell"]:
            print(f"Current shell: {status['current_shell']}")
            if status["loader_exists"]:
                print(f"Loader file: ✓ exists")
            else:
                print(f"Loader file: ✗ missing (run 'shtick generate')")
        print()

        # Show persistent group
        if status["persistent_items"] > 0:
            print(f"Persistent (always active): {status['persistent_items']} items")
        else:
            print("Persistent: No items")

        print()

        # Show regular groups
        if status["available_groups"]:
            print("Available Groups:")
            active_set = set(status["active_groups"])
            for group_name in status["available_groups"]:
                # Get item count for this group
                items = self.manager.list_items(group_name)
                item_count = len(items)
                status_str = "ACTIVE" if group_name in active_set else "inactive"
                print(f"  {group_name}: {item_count} items ({status_str})")
        else:
            print("No regular groups configured")

        print()

        # Show summary
        if status["active_groups"]:
            print(f"Currently active: {', '.join(status['active_groups'])}")
        else:
            print("No groups currently active")

        print()
        print("Quick commands:")
        print("  shtick alias ll='ls -la'              # Add persistent alias")
        print("  shtick activate <group>               # Activate group")
        print('  eval "$(shtick source)"               # Load changes now')

    def list_config(self, long_format: bool = False):
        """List current configuration"""
        items = self.manager.list_items()

        if not items:
            print("No items configured")
            print("\nGet started with:")
            print("  shtick alias ll='ls -la'              # Add persistent alias")
            print("  shtick add alias work ll='ls -la'     # Add to 'work' group")
            print("  shtick activate work                  # Activate 'work' group")
            return

        # Group items by group name
        groups_data = {}
        for item in items:
            group_name = item["group"]
            if group_name not in groups_data:
                groups_data[group_name] = {
                    "aliases": {},
                    "env_vars": {},
                    "functions": {},
                    "active": item["active"],
                }

            if item["type"] == "alias":
                groups_data[group_name]["aliases"][item["key"]] = item["value"]
            elif item["type"] == "env":
                groups_data[group_name]["env_vars"][item["key"]] = item["value"]
            elif item["type"] == "function":
                groups_data[group_name]["functions"][item["key"]] = item["value"]

        # Display based on format
        if long_format:
            self._print_detailed_list(groups_data)
        else:
            self._print_tabular_list(items)

    def _print_detailed_list(self, groups_data):
        """Print detailed line-by-line list format"""
        # Show persistent group first if it exists
        if "persistent" in groups_data:
            print("Group: persistent (always active)")
            self._print_group_items_detailed(groups_data["persistent"])
            print()
            del groups_data["persistent"]

        # Show regular groups
        for group_name, group_data in sorted(groups_data.items()):
            status = " (ACTIVE)" if group_data["active"] else " (inactive)"
            print(f"Group: {group_name}{status}")
            self._print_group_items_detailed(group_data)
            print()

    def _print_group_items_detailed(self, group_data):
        """Print items for a single group in detailed format"""
        if group_data["aliases"]:
            print(f"  Aliases ({len(group_data['aliases'])}):")
            for key, value in group_data["aliases"].items():
                print(f"    {key} = {value}")
        if group_data["env_vars"]:
            print(f"  Environment Variables ({len(group_data['env_vars'])}):")
            for key, value in group_data["env_vars"].items():
                print(f"    {key} = {value}")
        if group_data["functions"]:
            print(f"  Functions ({len(group_data['functions'])}):")
            for key, value in group_data["functions"].items():
                print(f"    {key} = {value}")

    def _print_tabular_list(self, items):
        """Print compact tabular list format"""
        if not items:
            return

        # Calculate column widths
        max_group = max(max(len(item["group"]) for item in items), 5)  # "Group"
        max_type = max(max(len(item["type"]) for item in items), 4)  # "Type"
        max_key = max(max(len(item["key"]) for item in items), 3)  # "Key"
        max_value = max(
            max(min(len(item["value"]), 50) for item in items), 5
        )  # "Value" (limited)
        max_status = max(
            max(len("ACTIVE" if item["active"] else "inactive") for item in items), 6
        )  # "Status"

        # Print header
        header = f"{'Group':<{max_group}} {'Type':<{max_type}} {'Key':<{max_key}} {'Value':<{max_value}} {'Status':<{max_status}}"
        print(header)
        print("-" * len(header))

        # Sort items for better display (persistent first, then by group, then by type)
        def sort_key(item):
            group_order = 0 if item["group"] == "persistent" else 1
            return (group_order, item["group"], item["type"], item["key"])

        sorted_items = sorted(items, key=sort_key)

        # Print items
        for item in sorted_items:
            # Truncate long values with ellipsis
            value = item["value"]
            display_value = (
                value if len(value) <= max_value else value[: max_value - 3] + "..."
            )
            status = "ACTIVE" if item["active"] else "inactive"
            print(
                f"{item['group']:<{max_group}} {item['type']:<{max_type}} "
                f"{item['key']:<{max_key}} {display_value:<{max_value}} {status:<{max_status}}"
            )

        # Print summary
        self._print_summary(items)

    def _print_summary(self, items):
        """Print summary information"""
        print()
        total_items = len(items)
        active_items = len([item for item in items if item["active"]])
        print(f"Total: {total_items} items ({active_items} active)")

        # Show available commands
        print()
        print("Use 'shtick list -l' for detailed view")

        # Get inactive groups
        inactive_groups = set()
        for item in items:
            if not item["active"] and item["group"] != "persistent":
                inactive_groups.add(item["group"])

        if inactive_groups:
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
