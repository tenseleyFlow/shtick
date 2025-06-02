#!/usr/bin/env python3
"""
shtick - Shell alias manager
Generates shell configuration files from TOML config
"""

import sys
import argparse
from shtick.commands import ShtickCommands
from shtick.display import DisplayCommands


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
        "--terse",
        action="store_true",
        help="Skip interactive shell selection and show minimal output",
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add an item to config")
    add_parser.add_argument(
        "type", choices=["alias", "env", "function"], help="Type of item to add"
    )
    add_parser.add_argument("group", help="Group name")
    add_parser.add_argument("assignment", help="Assignment in format key=value")

    # Add-persistent command
    add_persistent_parser = subparsers.add_parser(
        "add-persistent", help="Add an item to the persistent group (always active)"
    )
    add_persistent_parser.add_argument(
        "type", choices=["alias", "env", "function"], help="Type of item to add"
    )
    add_persistent_parser.add_argument(
        "assignment", help="Assignment in format key=value"
    )

    # Shorthand commands for common operations
    alias_parser = subparsers.add_parser(
        "alias", help="Add persistent alias (shorthand for 'add-persistent alias')"
    )
    alias_parser.add_argument("assignment", help="Assignment in format key=value")

    env_parser = subparsers.add_parser(
        "env",
        help="Add persistent environment variable (shorthand for 'add-persistent env')",
    )
    env_parser.add_argument("assignment", help="Assignment in format key=value")

    function_parser = subparsers.add_parser(
        "function",
        help="Add persistent function (shorthand for 'add-persistent function')",
    )
    function_parser.add_argument("assignment", help="Assignment in format key=value")

    # Remove command
    rm_parser = subparsers.add_parser("remove", help="Remove an item from config")
    rm_parser.add_argument(
        "type", choices=["alias", "env", "function"], help="Type of item to remove"
    )
    rm_parser.add_argument("group", help="Group name")
    rm_parser.add_argument("search", help="Search term (fuzzy match)")

    # Remove-persistent command
    rm_persistent_parser = subparsers.add_parser(
        "remove-persistent", help="Remove an item from the persistent group"
    )
    rm_persistent_parser.add_argument(
        "type", choices=["alias", "env", "function"], help="Type of item to remove"
    )
    rm_persistent_parser.add_argument("search", help="Search term (fuzzy match)")

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

    # Source command (for eval)
    source_parser = subparsers.add_parser(
        "source", help="Output source command for eval (for immediate loading)"
    )
    source_parser.add_argument(
        "--shell", help="Specify shell type (auto-detected if not provided)"
    )

    args = parser.parse_args()

    if not args.command:
        # Show helpful getting started message
        parser.print_help()
        print("\nQuick start:")
        print("  shtick alias ll='ls -la'      # Add a persistent alias")
        print("  shtick status                 # Show current configuration")
        print("  shtick list                   # List all items")
        sys.exit(1)

    # Initialize command handlers
    commands = ShtickCommands(debug=args.debug)
    display = DisplayCommands(debug=args.debug)

    # Route commands
    if args.command == "generate":
        commands.generate(args.config, args.terse)
    elif args.command == "add":
        commands.add_item(args.type, args.group, args.assignment)
    elif args.command == "add-persistent":
        commands.add_persistent(args.type, args.assignment)
    elif args.command == "alias":
        commands.add_persistent("alias", args.assignment)
    elif args.command == "env":
        commands.add_persistent("env", args.assignment)
    elif args.command == "function":
        commands.add_persistent("function", args.assignment)
    elif args.command == "remove":
        commands.remove_item(args.type, args.group, args.search)
    elif args.command == "remove-persistent":
        commands.remove_item(args.type, "persistent", args.search)
    elif args.command == "activate":
        commands.activate_group(args.group)
    elif args.command == "deactivate":
        commands.deactivate_group(args.group)
    elif args.command == "status":
        display.status()
    elif args.command == "list":
        display.list_config(args.long)
    elif args.command == "shells":
        display.shells(args.long)
    elif args.command == "source":
        commands.source_command(args.shell)


if __name__ == "__main__":
    main()
