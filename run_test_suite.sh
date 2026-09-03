#!/bin/bash
# Test Suite Runner for Bot Tester
# Run predefined test suites and generate reports

set -e

BOT_PATH="${BOT_PATH:-.}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"
VERBOSE="${VERBOSE:-0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

echo "Bot Tester - Test Suite Runner"
echo "Bot: $BOT_PATH"
echo "================================"
echo ""

# Helper function to run a test
run_test() {
    local test_name=$1
    local test_cmd=$2
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    echo -n "[$TESTS_RUN] $test_name ... "
    
    if eval "$test_cmd" > /tmp/test_output.txt 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        if [ "$VERBOSE" = "1" ]; then
            cat /tmp/test_output.txt
        fi
    fi
}

# Test 1: Bot loads successfully
run_test "Bot initialization" \
    "python src/cli_tester.py --bot $BOT_PATH --info --output json"

# Test 2: Help command
run_test "Help command" \
    "python src/cli_tester.py --bot $BOT_PATH --message '!help' --output json"

# Test 3: Admin permissions
run_test "Admin can execute commands" \
    "python src/cli_tester.py --bot $BOT_PATH --message '!status' --user-role admin --output json"

# Test 4: User permissions
run_test "User gets proper responses" \
    "python src/cli_tester.py --bot $BOT_PATH --message '!status' --user-role user --output json"

# Test 5: High volume handling
run_test "High volume (10 messages)" \
    "python src/cli_tester.py --bot $BOT_PATH --high-volume 'test' --count 10 --interval 0.05 --output json"

# Test 6: Duplicate detection
run_test "Duplicate message handling" \
    "python src/cli_tester.py --bot $BOT_PATH --duplicate 'test' --output json"

# Test 7: Error handling
run_test "Error handling (409)" \
    "python src/cli_tester.py --bot $BOT_PATH --error 'test' --error-code 409 --output json"

# Test 8: Batch messages
run_test "Batch message processing" \
    "echo -e '!help\n!status' | python src/cli_tester.py --bot $BOT_PATH --batch /dev/stdin --output json"

echo ""
echo "================================"
echo -e "Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC} (total: $TESTS_RUN)"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
