#!/usr/bin/env python3
"""
shtick - Shell alias manager
Generates shell configuration files from TOML config
"""

import sys
import argparse
from shtick.commands import ShtickCommands
from shtick.display import DisplayCommands
from shtick.logger import setup_logging


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

    # Add group management commands
    group_parser = subparsers.add_parser("group", help="Group management commands")
    group_subparsers = group_parser.add_subparsers(
        dest="group_command", help="Group commands"
    )

    # Create group
    create_parser = group_subparsers.add_parser("create", help="Create a new group")
    create_parser.add_argument("name", help="Group name")
    create_parser.add_argument("-d", "--description", help="Group description")

    # Remove group
    remove_parser = group_subparsers.add_parser("remove", help="Remove a group")
    remove_parser.add_argument("name", help="Group name")
    remove_parser.add_argument(
        "-f", "--force", action="store_true", help="Force removal without confirmation"
    )

    # Rename group
    rename_parser = group_subparsers.add_parser("rename", help="Rename a group")
    rename_parser.add_argument("old_name", help="Current group name")
    rename_parser.add_argument("new_name", help="New group name")

    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Backup management commands")
    backup_subparsers = backup_parser.add_subparsers(
        dest="backup_command", help="Backup commands"
    )

    # Create backup
    backup_create_parser = backup_subparsers.add_parser(
        "create", help="Create a backup"
    )
    backup_create_parser.add_argument(
        "-n", "--name", help="Backup name (timestamp used if not provided)"
    )

    # List backups
    backup_list_parser = backup_subparsers.add_parser(
        "list", help="List available backups"
    )

    # Restore backup
    backup_restore_parser = backup_subparsers.add_parser(
        "restore", help="Restore from backup"
    )
    backup_restore_parser.add_argument("name", help="Backup name or filename")

    # Source command (for eval)
    source_parser = subparsers.add_parser(
        "source", help="Output source command for eval (for immediate loading)"
    )
    source_parser.add_argument(
        "--shell", help="Specify shell type (auto-detected if not provided)"
    )

    # Settings command
    settings_parser = subparsers.add_parser("settings", help="Manage shtick settings")
    settings_subparsers = settings_parser.add_subparsers(
        dest="settings_command", help="Settings commands"
    )

    # Settings subcommands
    settings_init_parser = settings_subparsers.add_parser(
        "init", help="Create default settings file"
    )

    settings_show_parser = settings_subparsers.add_parser(
        "show", help="Show current settings"
    )

    settings_set_parser = settings_subparsers.add_parser(
        "set", help="Set a setting value"
    )
    settings_set_parser.add_argument(
        "key", help="Setting key (e.g., generation.shells)"
    )
    settings_set_parser.add_argument("value", help="Setting value")

    args = parser.parse_args()

    # Set up logging first
    logger = setup_logging(debug=args.debug)

    if not args.command:
        # Show helpful getting started message
        parser.print_help()
        print("\nQuick start:")
        print("  shtick alias ll='ls -la'      # Add a persistent alias")
        print("  shtick status                 # Show current configuration")
        print("  shtick list                   # List all items")
        sys.exit(1)

    # Initialize command handlers with debug flag
    commands = ShtickCommands(debug=args.debug)
    display = DisplayCommands(debug=args.debug)

    # Route commands
    try:
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
        elif args.command == "settings":
            if args.settings_command == "init":
                commands.settings_init()
            elif args.settings_command == "show":
                commands.settings_show()
            elif args.settings_command == "set":
                commands.settings_set(args.key, args.value)
            else:
                settings_parser.print_help()
        elif args.command == "group":
            if args.group_command == "create":
                commands.group_create(args.name, args.description)
            elif args.group_command == "rename":
                commands.group_rename(args.old_name, args.new_name)
            elif args.group_command == "remove":
                commands.group_remove(args.name, args.force)
            else:
                group_parser.print_help()
        elif args.command == "backup":
            if args.backup_command == "create":
                commands.backup_create(args.name)
            elif args.backup_command == "list":
                commands.backup_list()
            elif args.backup_command == "restore":
                commands.backup_restore(args.name)
            else:
                backup_parser.print_help()

    except KeyboardInterrupt:
        logger.debug("Operation cancelled by user")
        print("\nCancelled")
        sys.exit(2)  # Use exit code 2 for user cancellation
    except Exception as e:
        if args.debug:
            logger.exception("Unhandled exception")
        else:
            logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
