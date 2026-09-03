# Terminal Bot Tester - Quick Start

Your interactive bot tester now has a terminal interface! AI agents and scripts can test your bot without using the GUI.

## What's New

✨ **CLI Interface** - Test bot from terminal
✨ **Python API** - Import and use in your agent code  
✨ **JSON Output** - Easy parsing for automation
✨ **No GUI Required** - Perfect for CI/CD and headless systems

## Installation

No additional installation needed! The CLI tester uses the existing `interactive_test.py` module.

## Quick Examples

### Test a single message
```bash
cd interactive-tester
python src/cli_tester.py --bot . --message "!help"
```

### Test as user (not admin)
```bash
python src/cli_tester.py --bot . --message "!command" --user-role user
```

### Test multiple messages
```bash
python src/cli_tester.py --bot . --batch examples/test_messages_basic.txt
```

### High volume test (for load testing)
```bash
python src/cli_tester.py --bot . --high-volume "test message" --count 50
```

### Get JSON output (for parsing)
```bash
python src/cli_tester.py --bot . --message "test" --output json
```

## For Python/AI Agent Integration

```python
from interactive_tester.src.agent_tester import AIAgentBotTester

# Load bot
tester = AIAgentBotTester(".")

# Test messages
response = tester.test_admin("!help")

# Test conversations
response = tester.test_conversation("!play", "yes", "2", "left")

# Parse responses
for msg in response:
    print(msg["text"])
```

## Complete Documentation

- **CLI Usage**: See [CLI_USAGE.md](CLI_USAGE.md)
- **Agent Integration**: See [AGENT_INTEGRATION.md](AGENT_INTEGRATION.md)  
- **Examples**: Check `examples/` folder

## Files Added

```
src/
  ├── cli_tester.py          # CLI interface (use this!)
  └── agent_tester.py        # Python API for agents

examples/
  ├── ai_agent_testing.py    # Example agent test suite
  └── test_messages_basic.txt # Example batch messages

AGENT_INTEGRATION.md          # How to integrate with agents
CLI_USAGE.md                  # Complete CLI documentation
run_test_suite.sh            # Automated test runner (Linux/Mac)
run_test_suite.bat           # Automated test runner (Windows)
```

## Key Features

### 1. Single Message Testing
```bash
python src/cli_tester.py --bot . --message "!help"
```

### 2. Batch Message Testing  
```bash
python src/cli_tester.py --bot . --batch messages.txt
```

### 3. High Volume Testing
```bash
python src/cli_tester.py --bot . --high-volume "spam" --count 100
```

### 4. Permission Testing
```bash
python src/cli_tester.py --bot . --message "!ban user" --user-role admin
python src/cli_tester.py --bot . --message "!ban user" --user-role user
```

### 5. Error Simulation
```bash
python src/cli_tester.py --bot . --error "test" --error-code 409
```

### 6. Duplicate Handling
```bash
python src/cli_tester.py --bot . --duplicate "message"
```

### 7. Bot Information
```bash
python src/cli_tester.py --bot . --info
```

## Output Formats

### JSON (default - for automation)
```bash
python src/cli_tester.py --bot . --message "test" --output json
```

Output:
```json
{
  "success": true,
  "data": [
    {
      "text": "Bot response",
      "attachments": []
    }
  ]
}
```

### Text (human-readable)
```bash
python src/cli_tester.py --bot . --message "test" --output text
```

Output:
```
Bot response
```

## Common Tasks

### Task 1: Test Bot Commands
```bash
python src/cli_tester.py --bot . --message "!help"
python src/cli_tester.py --bot . --message "!status"
python src/cli_tester.py --bot . --message "!play"
```

### Task 2: Verify Permissions Work
```bash
# Admin can access
python src/cli_tester.py --bot . --message "!ban user" --user-role admin

# User cannot access  
python src/cli_tester.py --bot . --message "!ban user" --user-role user
```

### Task 3: Test Game Flow
```bash
python src/cli_tester.py --bot . --batch examples/game_flow.txt
```

### Task 4: Check Bot Responds to Load
```bash
python src/cli_tester.py --bot . --high-volume "msg" --count 50 --interval 0.1
```

### Task 5: Run Full Test Suite
```bash
# Linux/Mac
bash run_test_suite.sh

# Windows
run_test_suite.bat
```

## AI Agent Examples

### Using with an AI Agent (Python)

```python
from src.agent_tester import AIAgentBotTester

agent_tester = AIAgentBotTester(".")

# Agent can test commands before executing
if agent_tester.test_admin("!play"):
    print("Game command works!")

# Agent can test conversations
responses = agent_tester.test_conversation(
    "!play",
    "yes",
    "2",
    "left"
)

# Agent can verify results
for response in responses:
    if "game" in response["text"].lower():
        print("Game flow working correctly")
```

### Using with Shell Script

```bash
#!/bin/bash

# Test that bot responds
if python src/cli_tester.py --bot . --message "!help" --output json | grep -q success; then
    echo "Bot is responding"
else
    echo "Bot is not responding"
fi
```

### Using with CI/CD (GitHub Actions, etc)

```yaml
- name: Test Bot
  run: python src/cli_tester.py --bot . --info
```

## Troubleshooting

### Bot not found
```bash
# Make sure you're in the right directory
cd interactive-tester
python src/cli_tester.py --bot . --message "test"
```

### Permission issues on Linux/Mac
```bash
chmod +x src/cli_tester.py
chmod +x run_test_suite.sh
./run_test_suite.sh
```

### JSON parsing errors
```bash
# Check raw output
python src/cli_tester.py --bot . --message "test" --verbose
```

## Next Steps

1. **Read the full CLI documentation**: See [CLI_USAGE.md](CLI_USAGE.md)
2. **See agent integration examples**: See [AGENT_INTEGRATION.md](AGENT_INTEGRATION.md)
3. **Try the example test suite**: `python examples/ai_agent_testing.py`
4. **Run the test suite**: `bash run_test_suite.sh` (or `.bat` on Windows)

## Help & Support

Get help on any command:
```bash
python src/cli_tester.py --help
```

Run with verbose output to see what's happening:
```bash
python src/cli_tester.py --bot . --message "test" --verbose
```

Check bot configuration:
```bash
python src/cli_tester.py --bot . --info
```

---

That's it! Your bot can now be tested from the terminal. Enjoy! 🎉
