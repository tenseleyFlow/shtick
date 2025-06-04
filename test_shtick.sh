#!/bin/bash
# test_shtick_fixed.sh - Test suite for shtick commands with proper PATH handling

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test config directory
TEST_DIR="/tmp/shtick_test_$$"
export HOME="$TEST_DIR"
CONFIG_DIR="$TEST_DIR/.config/shtick"

# Find shtick command - try multiple approaches
find_shtick() {
    # Method 1: Check if shtick is in PATH
    if command -v shtick >/dev/null 2>&1; then
        SHTICK_CMD="shtick"
        echo "Found shtick in PATH: $(command -v shtick)"
        return 0
    fi
    
    # Method 2: Check if we're in development directory with cli.py
    if [ -f "./shtick/cli.py" ]; then
        SHTICK_CMD="python -m shtick.cli"
        echo "Found shtick module in current directory, using: $SHTICK_CMD"
        return 0
    fi
    
    # Method 3: Check parent directory
    if [ -f "../shtick/cli.py" ]; then
        SHTICK_CMD="python -m shtick.cli"
        echo "Found shtick module in parent directory"
        cd ..
        return 0
    fi
    
    # Method 4: Try direct python execution
    if [ -f "cli.py" ]; then
        SHTICK_CMD="python cli.py"
        echo "Found cli.py in current directory, using: $SHTICK_CMD"
        return 0
    fi
    
    echo "ERROR: Cannot find shtick command!"
    echo "Please ensure either:"
    echo "  1. shtick is installed and in your PATH"
    echo "  2. You're running this from the shtick source directory"
    echo "  3. The shtick package is properly installed with 'pip install -e .'"
    exit 1
}

# Clean up function
cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Setup test environment
setup() {
    rm -rf "$TEST_DIR"
    mkdir -p "$CONFIG_DIR"
    cd "$TEST_DIR"
}

# Test function
test_command() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"
    local description="$4"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    echo -n "[$TESTS_RUN] $test_name: $description ... "
    
    # Replace 'shtick' with actual command
    command="${command//shtick/$SHTICK_CMD}"
    
    # Run command and capture status
    set +e
    output=$(eval "$command" 2>&1)
    actual_status=$?
    set -e
    
    if [ $actual_status -eq $expected_status ]; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected status: $expected_status, Got: $actual_status"
        echo "  Command: $command"
        echo "  Output: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Verify shtick is working
verify_shtick() {
    echo "Verifying shtick command..."
    set +e
    output=$($SHTICK_CMD --help 2>&1)
    status=$?
    set -e
    
    if [ $status -ne 0 ]; then
        echo -e "${RED}ERROR: shtick command not working!${NC}"
        echo "Command: $SHTICK_CMD --help"
        echo "Status: $status"
        echo "Output: $output"
        exit 1
    fi
    echo -e "${GREEN}✓ shtick command verified${NC}"
    echo
}

# Header
echo "==================================="
echo "Shtick Command Test Suite"
echo "==================================="
echo

# Find shtick command
find_shtick

# Setup
setup

# Verify shtick works
verify_shtick

# Save original directory to return to later
ORIGINAL_DIR=$(pwd)

# Test 1: Basic commands without config
echo -e "${YELLOW}Testing basic commands without config:${NC}"
test_command "status-no-config" "shtick status" 0 "Status should work without config"
test_command "list-no-config" "shtick list" 0 "List should work without config"
test_command "shells" "shtick shells" 0 "Shells command should always work"

# Test 2: Adding items (creates config)
echo -e "\n${YELLOW}Testing add commands:${NC}"
test_command "add-alias" "shtick alias ll='ls -la'" 0 "Add persistent alias"
test_command "add-env" "shtick env DEBUG=1" 0 "Add persistent env var"
test_command "add-function" "shtick function greet='echo Hello'" 0 "Add persistent function"

# Test 3: Invalid add commands
echo -e "\n${YELLOW}Testing invalid add commands:${NC}"
test_command "add-invalid-key" "shtick alias '123bad=value'" 1 "Invalid key should fail"
test_command "add-no-equals" "shtick alias 'no_equals_sign'" 1 "Missing = should fail"
test_command "add-empty-key" "shtick alias '=value'" 1 "Empty key should fail"
test_command "add-empty-value" "shtick alias 'key='" 1 "Empty value should fail"

# Test 4: Group operations
echo -e "\n${YELLOW}Testing group operations:${NC}"
test_command "add-to-group" "shtick add alias work ll='ls -la'" 0 "Add to specific group"
test_command "activate-group" "shtick activate work" 0 "Activate existing group"
test_command "activate-nonexistent" "shtick activate nonexistent" 1 "Activate non-existent group should fail"
test_command "deactivate-group" "shtick deactivate work" 0 "Deactivate active group"
test_command "deactivate-inactive" "shtick deactivate work" 0 "Deactivate already inactive group"

# Test 5: Remove operations
echo -e "\n${YELLOW}Testing remove operations:${NC}"
test_command "remove-existing" "echo 1 | shtick remove-persistent alias ll" 0 "Remove existing alias"
test_command "remove-nonexistent" "shtick remove-persistent alias nonexistent" 0 "Remove non-existent item"
test_command "remove-fuzzy" "echo 1 | shtick remove alias work ll" 0 "Remove with fuzzy match"

# Test 6: Generate command
echo -e "\n${YELLOW}Testing generate command:${NC}"
test_command "generate-default" "shtick generate --terse" 0 "Generate with default config"
test_command "generate-custom" "shtick generate $CONFIG_DIR/config.toml --terse" 0 "Generate with custom config path"
test_command "generate-nonexistent" "shtick generate /tmp/nonexistent.toml" 1 "Generate with non-existent config should fail"

# Test 7: Source command
echo -e "\n${YELLOW}Testing source command:${NC}"
test_command "source-bash" "SHELL=/bin/bash shtick source" 0 "Source command for bash"
test_command "source-no-shell" "SHELL= shtick source" 1 "Source without shell should fail"

# Test 8: Settings commands
echo -e "\n${YELLOW}Testing settings commands:${NC}"
test_command "settings-show" "shtick settings show" 0 "Show settings"
test_command "settings-init" "shtick settings init" 0 "Initialize settings"
test_command "settings-set-bool" "shtick settings set behavior.auto_source_prompt false" 0 "Set boolean setting"
test_command "settings-set-invalid" "shtick settings set invalid.key value" 1 "Set invalid setting should fail"

# Test 9: Edge cases
echo -e "\n${YELLOW}Testing edge cases:${NC}"
test_command "persistent-activate" "shtick activate persistent" 1 "Cannot activate persistent group"
test_command "persistent-deactivate" "shtick deactivate persistent" 1 "Cannot deactivate persistent group"
test_command "very-long-key" "shtick alias $(printf 'a%.0s' {1..65})=value" 1 "Key over 64 chars should fail"

# Test 10: Special characters and escaping
echo -e "\n${YELLOW}Testing special characters:${NC}"
test_command "alias-with-quotes" "shtick alias msg='echo \"Hello World\"'" 0 "Alias with quotes"
test_command "alias-with-dollar" 'shtick alias home="cd \$HOME"' 0 "Alias with dollar sign"
test_command "multiline-function" 'shtick function hello="echo line1
echo line2"' 0 "Multiline function"

# Test 11: List and status with content
echo -e "\n${YELLOW}Testing list and status with content:${NC}"
test_command "list-with-content" "shtick list" 0 "List with items"
test_command "list-long-format" "shtick list -l" 0 "List in long format"
test_command "status-with-content" "shtick status" 0 "Status with configuration"

# Test 12: Conflict handling
echo -e "\n${YELLOW}Testing conflict handling:${NC}"
test_command "add-conflict-alias" "shtick add alias temp ll='ls -lah'" 0 "Add conflicting alias to different group"
test_command "check-conflict-warning" "shtick alias ll='ls -la' 2>&1 | grep -q 'exists in groups'" 0 "Should warn about conflicts"

# Return to original directory
cd "$ORIGINAL_DIR"

# Summary
echo
echo "==================================="
echo "Test Summary"
echo "==================================="
echo "Tests run:    $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi