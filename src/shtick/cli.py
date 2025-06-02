#!/usr/bin/env python3
"""
shtick - Shell alias manager
Generates shell configuration files from TOML config
"""

import sys
import argparse
import os
from typing import Optional

# Package imports
from shtick.config import Config
from shtick.generator import Generator
from shtick.shells import get_supported_shells


def cmd_generate(args) -> None:
    """Generate shell files from config"""
    config_path = args.config or Config.get_default_config_path()

    try:
        config = Config(config_path, debug=args.debug)
        config.load()

        generator = Generator()
        generator.generate_all(config, interactive=args.interactive)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Create a config file at {config_path} first")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_add(args) -> None:
    """Add an item to the config"""
    if "=" not in args.assignment:
        print("Error: Assignment must be in format key=value")
        sys.exit(1)

    key, value = args.assignment.split("=", 1)
    key = key.strip()
    value = value.strip()

    if not key or not value:
        print("Error: Both key and value must be non-empty")
        sys.exit(1)

    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path, debug=getattr(args, "debug", False))
        # Try to load existing config, create empty if doesn't exist
        try:
            config.load()
        except FileNotFoundError:
            print(f"Creating new config file at {config_path}")

        config.add_item(args.type, args.group, key, value)
        config.save()

        print(f"Added {args.type} '{key}' = '{value}' to group '{args.group}'")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_remove(args) -> None:
    """Remove an item from the config"""
    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path, debug=getattr(args, "debug", False))
        config.load()

        # Find matching items
        matches = config.find_items(args.type, args.group, args.search)

        if not matches:
            print(
                f"No {args.type} items matching '{args.search}' found in group '{args.group}'"
            )
            return

        if len(matches) == 1:
            # Exact match, remove it
            item = matches[0]
            if config.remove_item(args.type, args.group, item):
                config.save()
                print(f"Removed {args.type} '{item}' from group '{args.group}'")
            else:
                print(f"Failed to remove {args.type} '{item}'")
        else:
            # Multiple matches, ask for confirmation
            print(f"Found {len(matches)} matches:")
            for i, item in enumerate(matches, 1):
                print(f"  {i}. {item}")

            try:
                choice = input("Enter number to remove (or 'q' to quit): ").strip()
                if choice.lower() == "q":
                    print("Cancelled")
                    return

                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    item = matches[idx]
                    if config.remove_item(args.type, args.group, item):
                        config.save()
                        print(f"Removed {args.type} '{item}' from group '{args.group}'")
                    else:
                        print(f"Failed to remove {args.type} '{item}'")
                else:
                    print("Invalid choice")
            except (ValueError, KeyboardInterrupt):
                print("\nCancelled")

    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_activate(args) -> None:
    """Activate a group"""
    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path, debug=getattr(args, "debug", False))
        config.load()

        if args.group == "persistent":
            print(
                "Error: 'persistent' group is always active and cannot be manually activated"
            )
            return

        if config.activate_group(args.group):
            # Regenerate all files to ensure they exist and are up to date
            from shtick.generator import Generator

            generator = Generator()
            # Generate shell files for all groups (not just the activated one)
            for group in config.groups:
                generator.generate_for_group(group)
            # Then regenerate the loader to include newly activated group
            generator.generate_loader(config)

            print(f"Activated group '{args.group}'")
            print("Changes are now active in new shell sessions")
        else:
            print(f"Error: Group '{args.group}' not found in configuration")
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


def cmd_deactivate(args) -> None:
    """Deactivate a group"""
    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path, debug=getattr(args, "debug", False))
        config.load()

        if args.group == "persistent":
            print("Error: 'persistent' group cannot be deactivated")
            return

        if config.deactivate_group(args.group):
            # Regenerate loader to exclude deactivated group
            from shtick.generator import Generator

            generator = Generator()
            # Regenerate loader (no need to regenerate all files for deactivation)
            generator.generate_loader(config)

            print(f"Deactivated group '{args.group}'")
            print("Changes will take effect in new shell sessions")
        else:
            print(f"Group '{args.group}' was not active")

    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_list(args) -> None:
    """List current configuration"""
    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path, debug=getattr(args, "debug", False))
        config.load()

        if not config.groups:
            print("No groups configured")
            return

        persistent_group = config.get_persistent_group()
        regular_groups = config.get_regular_groups()
        active_groups = config.load_active_groups()

        if args.long:
            # Long format - detailed line-by-line
            _print_detailed_list(persistent_group, regular_groups, active_groups)
        else:
            # Default tabular format
            _print_tabular_list(persistent_group, regular_groups, active_groups)

    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print(
            "Use 'shtick add' to create entries or 'shtick generate' with a config file"
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def _print_detailed_list(persistent_group, regular_groups, active_groups) -> None:
    """Print detailed line-by-line list format"""
    # Show persistent group first
    if persistent_group:
        print("Group: persistent (always active)")
        if persistent_group.aliases:
            print(f"  Aliases ({len(persistent_group.aliases)}):")
            for key, value in persistent_group.aliases.items():
                print(f"    {key} = {value}")
        if persistent_group.env_vars:
            print(f"  Environment Variables ({len(persistent_group.env_vars)}):")
            for key, value in persistent_group.env_vars.items():
                print(f"    {key} = {value}")
        if persistent_group.functions:
            print(f"  Functions ({len(persistent_group.functions)}):")
            for key, value in persistent_group.functions.items():
                print(f"    {key} = {value}")
        print()

    # Show regular groups
    for group in regular_groups:
        status = " (ACTIVE)" if group.name in active_groups else " (inactive)"
        print(f"Group: {group.name}{status}")

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
        print()


def _print_tabular_list(persistent_group, regular_groups, active_groups) -> None:
    """Print compact tabular list format"""
    # Collect all items for tabular display
    items = []

    # Add persistent items
    if persistent_group:
        for key, value in persistent_group.aliases.items():
            items.append(("persistent", "alias", key, value, "PERSISTENT"))
        for key, value in persistent_group.env_vars.items():
            items.append(("persistent", "env", key, value, "PERSISTENT"))
        for key, value in persistent_group.functions.items():
            items.append(("persistent", "function", key, value, "PERSISTENT"))

    # Add regular group items
    for group in regular_groups:
        status = "ACTIVE" if group.name in active_groups else "inactive"

        for key, value in group.aliases.items():
            items.append((group.name, "alias", key, value, status))
        for key, value in group.env_vars.items():
            items.append((group.name, "env", key, value, status))
        for key, value in group.functions.items():
            items.append((group.name, "function", key, value, status))

    if not items:
        print("No items configured")
        return

    # Calculate column widths
    max_group = max(len(item[0]) for item in items)
    max_type = max(len(item[1]) for item in items)
    max_key = max(len(item[2]) for item in items)
    max_value = max(min(len(item[3]), 50) for item in items)  # Limit value column width
    max_status = max(len(item[4]) for item in items)

    # Ensure minimum widths
    max_group = max(max_group, 5)  # "Group"
    max_type = max(max_type, 4)  # "Type"
    max_key = max(max_key, 3)  # "Key"
    max_value = max(max_value, 5)  # "Value"
    max_status = max(max_status, 6)  # "Status"

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

    # Print summary
    print()
    total_items = len(items)
    active_items = len([item for item in items if item[4] in ["ACTIVE", "PERSISTENT"]])
    print(f"Total: {total_items} items ({active_items} active)")

    # Show available commands
    print()
    print("Use 'shtick list -l' for detailed view")
    if any(item[4] == "inactive" for item in items):
        inactive_groups = set(item[0] for item in items if item[4] == "inactive")
        print(f"Activate groups with: shtick activate <group>")
        print(f"Inactive groups: {', '.join(sorted(inactive_groups))}")


def cmd_shells(args) -> None:
    """List supported shells"""
    shells = sorted(get_supported_shells())

    if args.long:
        # Long format - one per line with descriptions
        print("Supported shells:")
        for shell in shells:
            print(f"  {shell}")
    else:
        # Default columnar format (like ls)
        _print_shells_columns(shells)


def _print_shells_columns(shells) -> None:
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

    # Add some padding
    column_width = max_shell_length + 2

    # Calculate how many columns we can fit
    columns = max(1, terminal_width // column_width)

    # Calculate number of rows needed
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


def cmd_status(args) -> None:
    """Show status of groups and active state"""
    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path, debug=getattr(args, "debug", False))
        config.load()

        persistent_group = config.get_persistent_group()
        regular_groups = config.get_regular_groups()
        active_groups = config.load_active_groups()

        print("Shtick Status")
        print("=" * 40)

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
        print("To activate a group: shtick activate <group>")
        print("To deactivate a group: shtick deactivate <group>")

    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("No configuration exists yet")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="shtick - Generate shell configuration files from TOML"
    )

    # Global flags
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser(
        "generate", help="Generate shell files from config"
    )
    gen_parser.add_argument("config", nargs="?", help="Path to config TOML file")
    gen_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive shell selection for sourcing instructions",
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add an item to config")
    add_parser.add_argument(
        "type", choices=["alias", "env", "function"], help="Type of item to add"
    )
    add_parser.add_argument("group", help="Group name")
    add_parser.add_argument("assignment", help="Assignment in format key=value")

    # Remove command
    rm_parser = subparsers.add_parser("remove", help="Remove an item from config")
    rm_parser.add_argument(
        "type", choices=["alias", "env", "function"], help="Type of item to remove"
    )
    rm_parser.add_argument("group", help="Group name")
    rm_parser.add_argument("search", help="Search term (fuzzy match)")

    # Activate command
    activate_parser = subparsers.add_parser("activate", help="Activate a group")
    activate_parser.add_argument("group", help="Group name to activate")

    # Deactivate command
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate a group")
    deactivate_parser.add_argument("group", help="Group name to deactivate")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show status of groups")

    # List command
    list_parser = subparsers.add_parser("list", help="List current configuration")
    list_parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="Show detailed line-by-line format instead of table",
    )

    # Shells command
    shells_parser = subparsers.add_parser("shells", help="List supported shells")
    shells_parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="Show one shell per line instead of columns",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "remove":
        cmd_remove(args)
    elif args.command == "activate":
        cmd_activate(args)
    elif args.command == "deactivate":
        cmd_deactivate(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "shells":
        cmd_shells(args)


if __name__ == "__main__":
    main()
