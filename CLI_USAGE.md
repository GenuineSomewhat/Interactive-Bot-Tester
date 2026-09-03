# CLI Bot Tester

Terminal-based bot tester that AI agents can use to test your bot without a GUI. Perfect for CI/CD pipelines, automation, and integration testing.

## Quick Start

### Single Message Test
```bash
python src/cli_tester.py --bot . --message "!help"
```

### Multiple Messages
```bash
python src/cli_tester.py --bot . --batch test_messages.txt
```

### High Volume Test
```bash
python src/cli_tester.py --bot . --high-volume "test" --count 50 --interval 0.1
```

## Command Reference

### Basic Usage
```bash
python src/cli_tester.py --bot <bot_path> <test_mode> [options]
```

**Bot Path:**
- `--bot .` - Current directory (where bot runs)
- `--bot ../bot` - Path to bot directory
- `--bot /path/to/app.py` - Direct path to Flask app file

### Test Modes (pick one)

#### Single Message
```bash
--message "hello world"
```
Test one message and capture bot responses.

#### Batch Messages
```bash
--batch messages.txt
```
Test multiple messages from a file (one message per line):
```
!help
!play
!score
```

#### High Volume
```bash
--high-volume "test message" --count 100 --interval 0.1
```
Send 100 messages with 0.1 second delay between each.

#### Duplicate Detection
```bash
--duplicate "test message"
```
Test bot's handling of duplicate messages (GroupMe API simulation).

#### Error Handling
```bash
--error "test message" --error-code 409
```
Test bot response to API errors (409 Conflict, 404 Not Found, 503 Service Unavailable, etc).

#### Bot Information
```bash
--info
```
Get webhook route, test users, and bot configuration.

### Options

**User Role:**
```bash
--user-role admin        # Send as admin (default)
--user-role user         # Send as regular user
```

**Attachments:**
```bash
# With image
--image-url https://example.com/image.jpg

# With location
--location "Coffee Shop" 40.7128 -74.0060
```

**Output Format:**
```bash
--output json    # JSON output (default)
--output text    # Plain text output
```

**Other Options:**
```bash
--verbose        # Print debug output
--count 50       # Number of messages for high-volume test
--interval 0.1   # Delay between messages (seconds)
--error-code 503 # HTTP error code to simulate
```

## Examples

### Example 1: Test Basic Functionality
```bash
# Test single command
python src/cli_tester.py --bot . --message "!help"

# Output:
# {
#   "success": true,
#   "data": [
#     {"text": "Available commands: ..."},
#     ...
#   ]
# }
```

### Example 2: Batch Testing a Conversation
```bash
# Create messages.txt
cat > messages.txt << EOF
!play
yes
2
left
EOF

# Run batch test
python src/cli_tester.py --bot . --batch messages.txt
```

### Example 3: Admin vs User Permissions
```bash
# Admin can access command
python src/cli_tester.py --bot . --message "!ban user123" --user-role admin

# User gets denied
python src/cli_tester.py --bot . --message "!ban user123" --user-role user
```

### Example 4: AI Agent Test Suite (Bash)
```bash
#!/bin/bash

# Define test suite
run_tests() {
    local bot_path=$1
    
    echo "=== Testing Bot: $bot_path ==="
    
    # Test 1: Basic commands
    echo "Test 1: Help command"
    python src/cli_tester.py --bot "$bot_path" --message "!help" --output text
    
    # Test 2: Admin commands
    echo "Test 2: Admin functionality"
    python src/cli_tester.py --bot "$bot_path" --message "!status" --user-role admin --output text
    
    # Test 3: User permissions
    echo "Test 3: User permissions"
    python src/cli_tester.py --bot "$bot_path" --message "!admin" --user-role user --output text
    
    # Test 4: Conversation flow
    echo "Test 4: Game flow"
    python src/cli_tester.py --bot "$bot_path" --batch game_flow.txt --output text
    
    # Test 5: High volume
    echo "Test 5: High volume (10 messages)"
    python src/cli_tester.py --bot "$bot_path" --high-volume "spam" --count 10 --interval 0.2 --output text
}

run_tests "."
```

### Example 5: Python Integration (AI Agent)
```python
import subprocess
import json

def test_bot_message(bot_path, message, user_role="admin"):
    """Test a bot message and return responses."""
    cmd = [
        "python", "src/cli_tester.py",
        "--bot", bot_path,
        "--message", message,
        "--user-role", user_role,
        "--output", "json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# Use it
response = test_bot_message(".", "!help")
if response["success"]:
    for message in response["data"]:
        print(f"Bot: {message.get('text', '')}")
else:
    print(f"Error: {response['data']['message']}")
```

## JSON Output Format

```json
{
  "success": true,
  "data": [
    {
      "text": "Bot response text",
      "attachments": [
        {
          "type": "image",
          "url": "https://i.groupme.com/...",
          "is_local_file": false
        }
      ]
    }
  ]
}
```

Error response:
```json
{
  "error": true,
  "message": "Error description"
}
```

## Use Cases

### 1. Automated Testing in CI/CD
```bash
# .github/workflows/test.yml
- name: Test Bot
  run: |
    python src/cli_tester.py --bot . --message "!health" --output json
```

### 2. AI Agent Testing
```python
# Agent can test commands before executing
def test_command(command):
    result = run_cli_tester(command)
    return result["success"]
```

### 3. Regression Testing
```bash
# Test that all commands still work
for cmd in "!help" "!status" "!play" "!score"; do
    python src/cli_tester.py --bot . --message "$cmd"
done
```

### 4. Load Testing
```bash
# Test bot under high load
python src/cli_tester.py --bot . --high-volume "message" --count 1000 --interval 0.01
```

### 5. Integration Testing
```bash
# Test message flow with attachments
python src/cli_tester.py --bot . --message "show image" --image-url test_image.jpg
```

## Troubleshooting

### Bot fails to load
```bash
# Use verbose mode to see what's wrong
python src/cli_tester.py --bot . --message "test" --verbose
```

### Messages not getting responses
- Check that bot path is correct (`--bot .` or full path)
- Verify bot uses Flask
- Check requirements are installed (cli_tester installs them automatically)

### JSON parsing errors
- Make sure `--output json` is used for machine parsing
- Check bot responses don't include non-JSON characters

### Slow tests
- Reduce `--count` for high volume tests
- Increase `--interval` to reduce CPU usage
- Use `--user-role user` if admin commands are slow

## API for AI Agents

AI agents can integrate the tester programmatically:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli_tester import CLIBotTester

# Load bot
tester = CLIBotTester("./", output_format="json", verbose=True)
tester.load_bot()

# Test messages
responses = tester.test_single_message("!help", user_role="admin")
print(responses)

# Test batch
messages = ["!play", "yes", "2", "left"]
responses = tester.test_batch_messages(messages)
print(responses)
```

## Tips for AI Agents

1. **Check bot info first:** `--info` to see webhook route and test users
2. **Use batch testing** for conversation flows instead of single messages
3. **Catch errors:** Check for empty response lists which indicate failures
4. **JSON output:** Always use `--output json` for programmatic parsing
5. **Verbose mode:** Use `--verbose` during debugging
6. **User roles:** Test both `admin` and `user` roles for permission testing
