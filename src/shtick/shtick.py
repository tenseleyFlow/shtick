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
        config = Config(config_path)
        config.load()

        generator = Generator()
        generator.generate_all(config)

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
        config = Config(config_path)
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
        config = Config(config_path)
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


def cmd_list(args) -> None:
    """List current configuration"""
    config_path = Config.get_default_config_path()

    try:
        config = Config(config_path)
        config.load()

        if not config.groups:
            print("No groups configured")
            return

        for group in config.groups:
            print(f"\nGroup: {group.name}")

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

    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print(
            "Use 'shtick add' to create entries or 'shtick generate' with a config file"
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="shtick - Generate shell configuration files from TOML"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser(
        "generate", help="Generate shell files from config"
    )
    gen_parser.add_argument("config", nargs="?", help="Path to config TOML file")

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

    # List command
    list_parser = subparsers.add_parser("list", help="List current configuration")

    # Shells command (bonus)
    shells_parser = subparsers.add_parser("shells", help="List supported shells")

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
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "shells":
        print("Supported shells:")
        for shell in sorted(get_supported_shells()):
            print(f"  {shell}")


if __name__ == "__main__":
    main()
