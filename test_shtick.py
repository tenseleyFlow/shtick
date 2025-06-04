#!/usr/bin/env python3
"""
test_shtick_enhanced.py - Comprehensive test suite for shtick commands
Enhanced with backup and group management tests
"""

import subprocess
import tempfile
import shutil
import os
import sys
from pathlib import Path

# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


class ShtickTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_dir = None
        self.original_home = os.environ.get("HOME")
        self.shtick_cmd = self._find_shtick_command()

    def _find_shtick_command(self):
        """Find the shtick command to use"""
        # Method 1: Check if shtick is in PATH
        if shutil.which("shtick"):
            print(f"Found shtick in PATH: {shutil.which('shtick')}")
            return ["shtick"]

        # Method 2: Try running as module from current directory
        if Path("shtick/cli.py").exists():
            print("Found shtick module in current directory")
            return [sys.executable, "-m", "shtick.cli"]

        # Method 3: Try parent directory
        if Path("../shtick/cli.py").exists():
            print("Found shtick module in parent directory")
            os.chdir("..")
            return [sys.executable, "-m", "shtick.cli"]

        # Method 4: Direct cli.py execution
        if Path("cli.py").exists():
            print("Found cli.py in current directory")
            return [sys.executable, "cli.py"]

        raise RuntimeError(
            "Cannot find shtick command! Please ensure shtick is installed or run from source directory."
        )

    def setup(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="shtick_test_")
        os.environ["HOME"] = self.test_dir
        os.environ["SHTICK_ORIGINAL_HOME"] = (
            self.original_home
        )  # For security.py to work
        os.makedirs(os.path.join(self.test_dir, ".config", "shtick"), exist_ok=True)

        # Create a settings file that disables auto_source_prompt to avoid timeouts
        settings_path = os.path.join(
            self.test_dir, ".config", "shtick", "settings.toml"
        )
        with open(settings_path, "w") as f:
            f.write(
                """# Test settings
[behavior]
auto_source_prompt = false
check_conflicts = true
backup_on_save = false
interactive_mode = false
"""
            )

        print(f"Test directory: {self.test_dir}")
        print(f"Created settings to disable interactive prompts")

    def cleanup(self):
        """Clean up test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if self.original_home:
            os.environ["HOME"] = self.original_home
        else:
            os.environ.pop("HOME", None)
        os.environ.pop("SHTICK_ORIGINAL_HOME", None)

    def run_command(self, args, input_text=None, env_override=None):
        """Run a shtick command and return (output, return_code)"""
        cmd = self.shtick_cmd + args

        env = os.environ.copy()
        if env_override:
            env.update(env_override)

        # Always ensure we're using our test HOME
        env["HOME"] = self.test_dir
        env["SHTICK_ORIGINAL_HOME"] = self.original_home  # For security.py

        try:
            # For commands that might prompt, always provide 'n' as input
            # to avoid hanging on interactive prompts
            if input_text is None and any(
                x in args for x in ["alias", "env", "function", "add", "remove"]
            ):
                input_text = "n\n"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=input_text,
                env=env,
                timeout=5,  # Reduced timeout since we're handling prompts
            )
            return result.stdout + result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "Command timed out", -1
        except Exception as e:
            return f"Error running command: {e}", -1

    def test_command(
        self,
        test_name,
        args,
        expected_status,
        description,
        input_text=None,
        env_override=None,
        check_output=None,
        check_not_output=None,
    ):
        """Run a test and check the result"""
        self.tests_run += 1

        print(f"[{self.tests_run}] {test_name}: {description} ... ", end="", flush=True)

        output, actual_status = self.run_command(args, input_text, env_override)

        # Check status code
        status_ok = actual_status == expected_status

        # Check output if requested
        output_ok = True
        if check_output is not None:
            output_ok = check_output in output
        if check_not_output is not None and output_ok:
            output_ok = check_not_output not in output

        if status_ok and output_ok:
            print(f"{GREEN}PASS{NC}")
            self.tests_passed += 1
        else:
            print(f"{RED}FAIL{NC}")
            if not status_ok:
                print(f"  Expected status: {expected_status}, Got: {actual_status}")
            if not output_ok:
                if check_output is not None:
                    print(f"  Expected output to contain: {check_output}")
                if check_not_output is not None:
                    print(f"  Expected output NOT to contain: {check_not_output}")
            print(f"  Command: {' '.join(self.shtick_cmd + args)}")
            print(f"  Output: {output[:500]}...")  # Truncate long output
            self.tests_failed += 1

    def verify_shtick(self):
        """Verify shtick command is working"""
        print("Verifying shtick command...")
        output, status = self.run_command(["--help"])

        if status != 0:
            print(f"{RED}ERROR: shtick command not working!{NC}")
            print(f"Status: {status}")
            print(f"Output: {output}")
            sys.exit(1)

        print(f"{GREEN}✓ shtick command verified{NC}\n")

    def run_all_tests(self):
        """Run all tests"""
        print("===================================")
        print("Shtick Command Test Suite (Enhanced)")
        print("===================================\n")

        self.setup()
        self.verify_shtick()

        try:
            # Test 1: Basic commands without config
            print(f"{YELLOW}Testing basic commands without config:{NC}")
            self.test_command(
                "status-no-config", ["status"], 0, "Status should work without config"
            )
            self.test_command(
                "list-no-config", ["list"], 0, "List should work without config"
            )
            self.test_command(
                "shells", ["shells"], 0, "Shells command should always work"
            )

            # Test 2: Adding items - use proper quoting
            print(f"\n{YELLOW}Testing add commands:{NC}")
            self.test_command(
                "add-alias", ["alias", "ll=ls -la"], 0, "Add persistent alias"
            )
            self.test_command(
                "add-env", ["env", "DEBUG=1"], 0, "Add persistent env var"
            )
            self.test_command(
                "add-function",
                ["function", "greet=echo Hello"],
                0,
                "Add persistent function",
            )

            # Test 3: Invalid add commands
            print(f"\n{YELLOW}Testing invalid add commands:{NC}")
            self.test_command(
                "add-invalid-key",
                ["alias", "123bad=value"],
                1,
                "Invalid key should fail",
            )
            self.test_command(
                "add-no-equals", ["alias", "no_equals_sign"], 1, "Missing = should fail"
            )
            self.test_command(
                "add-empty-key", ["alias", "=value"], 1, "Empty key should fail"
            )
            self.test_command(
                "add-empty-value", ["alias", "key="], 1, "Empty value should fail"
            )

            # Test 4: Group operations
            print(f"\n{YELLOW}Testing group operations:{NC}")
            self.test_command(
                "add-to-group",
                ["add", "alias", "work", "ll=ls -la"],
                0,
                "Add to specific group",
            )
            self.test_command(
                "activate-group", ["activate", "work"], 0, "Activate existing group"
            )
            self.test_command(
                "activate-nonexistent",
                ["activate", "nonexistent"],
                1,
                "Activate non-existent group should fail",
            )
            self.test_command(
                "deactivate-group", ["deactivate", "work"], 0, "Deactivate active group"
            )
            self.test_command(
                "deactivate-inactive",
                ["deactivate", "work"],
                0,
                "Deactivate already inactive group (idempotent)",
            )

            # Test 5: Remove operations - provide input for selection
            print(f"\n{YELLOW}Testing remove operations:{NC}")
            self.test_command(
                "remove-existing",
                ["remove-persistent", "alias", "ll"],
                0,
                "Remove existing alias",
                input_text="1\n",
            )
            self.test_command(
                "remove-nonexistent",
                ["remove-persistent", "alias", "nonexistent"],
                0,
                "Remove non-existent item (no-op)",
            )

            # Re-add for next test
            self.run_command(["add", "alias", "work", "ll=ls -la"])
            self.test_command(
                "remove-fuzzy",
                ["remove", "alias", "work", "ll"],
                0,
                "Remove with fuzzy match",
                input_text="1\n",
            )

            # Test 6: Generate command
            print(f"\n{YELLOW}Testing generate command:{NC}")
            self.test_command(
                "generate-default",
                ["generate", "--terse"],
                0,
                "Generate with default config",
            )
            config_path = os.path.join(
                self.test_dir, ".config", "shtick", "config.toml"
            )
            self.test_command(
                "generate-custom",
                ["generate", config_path, "--terse"],
                0,
                "Generate with custom config path",
            )
            self.test_command(
                "generate-nonexistent",
                ["generate", "/tmp/nonexistent.toml"],
                1,
                "Generate with non-existent config should fail",
            )

            # Test 7: Source command
            print(f"\n{YELLOW}Testing source command:{NC}")
            self.test_command(
                "source-bash",
                ["source"],
                0,
                "Source command for bash",
                env_override={"SHELL": "/bin/bash"},
            )
            self.test_command(
                "source-no-shell",
                ["source"],
                1,
                "Source without shell should fail",
                env_override={"SHELL": ""},
            )

            # Test 8: Settings commands
            print(f"\n{YELLOW}Testing settings commands:{NC}")
            self.test_command("settings-show", ["settings", "show"], 0, "Show settings")
            # Don't re-init since we already have settings
            self.test_command(
                "settings-set-bool",
                ["settings", "set", "behavior.backup_on_save", "true"],
                0,
                "Set boolean setting",
            )
            self.test_command(
                "settings-set-invalid",
                ["settings", "set", "invalid.key", "value"],
                1,
                "Set invalid setting should fail",
            )

            # Test 9: Edge cases
            print(f"\n{YELLOW}Testing edge cases:{NC}")
            self.test_command(
                "persistent-activate",
                ["activate", "persistent"],
                1,
                "Cannot activate persistent group",
            )
            self.test_command(
                "persistent-deactivate",
                ["deactivate", "persistent"],
                1,
                "Cannot deactivate persistent group",
            )
            long_key = "a" * 65
            self.test_command(
                "very-long-key",
                ["alias", f"{long_key}=value"],
                1,
                "Key over 64 chars should fail",
            )

            # Test 10: Special characters
            print(f"\n{YELLOW}Testing special characters:{NC}")
            self.test_command(
                "alias-with-quotes",
                ["alias", 'msg=echo "Hello World"'],
                0,
                "Alias with quotes",
            )
            self.test_command(
                "alias-with-dollar",
                ["alias", "home=cd $HOME"],
                0,
                "Alias with dollar sign",
            )
            self.test_command(
                "multiline-function",
                ["function", "hello=echo line1\necho line2"],
                0,
                "Multiline function",
            )

            # Test 11: List and status with content
            print(f"\n{YELLOW}Testing list and status with content:{NC}")
            self.test_command("list-with-content", ["list"], 0, "List with items")
            self.test_command(
                "list-long-format", ["list", "-l"], 0, "List in long format"
            )
            self.test_command(
                "status-with-content", ["status"], 0, "Status with configuration"
            )

            # Test 12: Conflict handling
            print(f"\n{YELLOW}Testing conflict handling:{NC}")
            # First create an alias in persistent
            self.run_command(["alias", "mytest=echo test1"])
            # Then add conflicting alias to different group
            self.test_command(
                "add-conflict-alias",
                ["add", "alias", "temp", "mytest=echo test2"],
                0,
                "Add conflicting alias to different group",
            )

            # Check if warning appears when adding duplicate
            output, status = self.run_command(["alias", "mytest=echo test3"])
            if "exists in groups" in output and status == 0:
                print(
                    f"[{self.tests_run + 1}] check-conflict-warning: Should warn about conflicts ... {GREEN}PASS{NC}"
                )
                self.tests_passed += 1
            else:
                print(
                    f"[{self.tests_run + 1}] check-conflict-warning: Should warn about conflicts ... {RED}FAIL{NC}"
                )
                print(f"  Expected warning about existing item, but got: {output}")
                print(f"  Status: {status}")
                self.tests_failed += 1
            self.tests_run += 1

            # Test 13: Backup functionality
            print(f"\n{YELLOW}Testing backup functionality:{NC}")
            # Add some content first
            self.run_command(["alias", "backup_test=echo backup"])
            self.test_command("backup-create", ["backup", "create"], 0, "Create backup")
            self.test_command(
                "backup-create-named",
                ["backup", "create", "-n", "test_backup"],
                0,
                "Create named backup",
            )
            self.test_command("backup-list", ["backup", "list"], 0, "List backups")

            # Modify config
            self.run_command(["alias", "after_backup=echo after"])

            # Restore and verify
            self.test_command(
                "backup-restore",
                ["backup", "restore", "test_backup"],
                0,
                "Restore from backup",
            )

            # Verify restore worked by checking if the new alias is gone
            output, _ = self.run_command(["list"])
            if "after_backup" not in output:
                print(
                    f"[{self.tests_run + 1}] verify-restore: Backup restore worked correctly ... {GREEN}PASS{NC}"
                )
                self.tests_passed += 1
            else:
                print(
                    f"[{self.tests_run + 1}] verify-restore: Backup restore failed ... {RED}FAIL{NC}"
                )
                self.tests_failed += 1
            self.tests_run += 1

            # Test 14: Group management - NOW WITH REAL FUNCTIONALITY!
            print(f"\n{YELLOW}Testing group management (enhanced):{NC}")

            # Test creating a new group
            self.test_command(
                "group-create",
                ["group", "create", "testgroup"],
                0,
                "Create new group",
                check_output="✓ Created group 'testgroup'",
                check_not_output="will be created when you add",
            )

            # Verify the group exists in status
            output, _ = self.run_command(["status"])
            if "testgroup: 0 items" in output:
                print(
                    f"[{self.tests_run + 1}] verify-group-exists: Created group shows in status ... {GREEN}PASS{NC}"
                )
                self.tests_passed += 1
            else:
                print(
                    f"[{self.tests_run + 1}] verify-group-exists: Created group should show in status ... {RED}FAIL{NC}"
                )
                print(f"  Status output: {output}")
                self.tests_failed += 1
            self.tests_run += 1

            # Verify we can activate the empty group
            self.test_command(
                "activate-empty-group",
                ["activate", "testgroup"],
                0,
                "Activate empty group",
            )

            # Verify the group shows as active
            output, _ = self.run_command(["status"])
            if "testgroup: 0 items (ACTIVE)" in output:
                print(
                    f"[{self.tests_run + 1}] verify-group-active: Empty group shows as active ... {GREEN}PASS{NC}"
                )
                self.tests_passed += 1
            else:
                print(
                    f"[{self.tests_run + 1}] verify-group-active: Empty group should show as active ... {RED}FAIL{NC}"
                )
                print(f"  Status output: {output}")
                self.tests_failed += 1
            self.tests_run += 1

            # Test adding to the newly created group
            self.test_command(
                "add-to-created-group",
                ["add", "alias", "testgroup", "tg=echo testgroup"],
                0,
                "Add item to newly created group",
            )

            # Verify the group now has 1 item
            output, _ = self.run_command(["status"])
            if "testgroup: 1 items (ACTIVE)" in output:
                print(
                    f"[{self.tests_run + 1}] verify-group-has-item: Group shows 1 item after add ... {GREEN}PASS{NC}"
                )
                self.tests_passed += 1
            else:
                print(
                    f"[{self.tests_run + 1}] verify-group-has-item: Group should show 1 item ... {RED}FAIL{NC}"
                )
                print(f"  Status output: {output}")
                self.tests_failed += 1
            self.tests_run += 1

            # Test creating duplicate group
            self.test_command(
                "group-create-duplicate",
                ["group", "create", "testgroup"],
                1,
                "Cannot create duplicate group",
                check_output="already exists",
            )

            # Check the TOML file contains empty sections
            config_path = os.path.join(
                self.test_dir, ".config", "shtick", "config.toml"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    toml_content = f.read()
                    # Check for either nested format (with tomli_w) or flat format (fallback)
                    has_nested = (
                        "[testgroup]" in toml_content
                        and "[testgroup.aliases]" in toml_content
                    )
                    has_flat = "[testgroup.aliases]" in toml_content
                    if has_nested or has_flat:
                        print(
                            f"[{self.tests_run + 1}] verify-toml-structure: TOML has proper empty group structure ... {GREEN}PASS{NC}"
                        )
                        self.tests_passed += 1
                    else:
                        print(
                            f"[{self.tests_run + 1}] verify-toml-structure: TOML should have empty group sections ... {RED}FAIL{NC}"
                        )
                        print(f"  TOML content:\n{toml_content[:500]}")
                        self.tests_failed += 1
                    self.tests_run += 1

            # Still test unimplemented features
            self.test_command(
                "group-rename",
                ["group", "rename", "testgroup", "newgroup"],
                1,
                "Rename group (not implemented)",
                check_output="not yet implemented",
            )
            self.test_command(
                "group-remove",
                ["group", "remove", "testgroup", "-f"],
                1,
                "Remove group (not implemented)",
                check_output="not yet implemented",
            )

            # Test 15: Exit code consistency
            print(f"\n{YELLOW}Testing exit code consistency:{NC}")
            # Test that user cancellation uses exit code 2
            output, status = self.run_command(
                ["settings", "init"], input_text="\x03"
            )  # Ctrl+C
            if status == 2 or "Cancelled" in output:
                print(
                    f"[{self.tests_run + 1}] user-cancel-exit-code: User cancellation returns code 2 ... {GREEN}PASS{NC}"
                )
                self.tests_passed += 1
            else:
                print(
                    f"[{self.tests_run + 1}] user-cancel-exit-code: User cancellation should return code 2 ... {RED}FAIL{NC}"
                )
                print(f"  Got status: {status}, output: {output}")
                self.tests_failed += 1
            self.tests_run += 1

            # Test 16: No-output commands should still exit properly
            print(f"\n{YELLOW}Testing commands with no output still exit properly:{NC}")
            # Create an empty config scenario
            empty_dir = tempfile.mkdtemp()
            self.test_command(
                "list-empty-explicit-exit",
                ["list"],
                0,
                "List with empty config exits 0",
                env_override={"HOME": empty_dir},
            )
            shutil.rmtree(empty_dir)

        finally:
            self.cleanup()

        # Summary
        print("\n===================================")
        print("Test Summary")
        print("===================================")
        print(f"Tests run:    {self.tests_run}")
        print(f"Tests passed: {GREEN}{self.tests_passed}{NC}")
        print(f"Tests failed: {RED}{self.tests_failed}{NC}")

        if self.tests_failed == 0:
            print(f"\n{GREEN}All tests passed!{NC}")
            return 0
        else:
            print(f"\n{RED}Some tests failed!{NC}")
            return 1


def main():
    """Run the test suite"""
    # Check if we should run in non-interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: test_shtick_enhanced.py")
        print("Run comprehensive tests for shtick command line tool")
        return 0

    tester = ShtickTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
