# AI Agent Integration Guide

This guide explains how to integrate the bot tester into your AI agent system.

## Overview

The interactive bot tester can now be used in three ways:

1. **CLI (Command Line)** - `python src/cli_tester.py`
   - Best for scripts, CI/CD pipelines, and shell integration
   - Returns JSON for easy parsing
   
2. **Python API** - `from agent_tester import AIAgentBotTester`
   - Best for Python-based AI agents
   - Simple, high-level API
   
3. **Direct Import** - `from interactive_test import InteractiveTester`
   - Direct access to tester internals
   - Maximum flexibility

## Quick Integration

### Option 1: CLI-based Integration

```bash
#!/bin/bash

# Test a message
python src/cli_tester.py --bot . --message "!help" --output json

# Parse the JSON response
RESPONSE=$(python src/cli_tester.py --bot . --message "!help" --output json)
BOT_SAID=$(echo $RESPONSE | jq -r '.data[0].text')

echo "Bot said: $BOT_SAID"
```

### Option 2: Python Agent Integration

```python
from agent_tester import AIAgentBotTester

# Initialize
tester = AIAgentBotTester("./bot")

# Test commands
response = tester.test_admin("!help")

# Test conversations
response = tester.test_conversation(
    "!play",
    "yes",
    "2",
    "left"
)
```

### Option 3: Direct Python Import

```python
from interactive_test import InteractiveTester

# Load bot
tester = InteractiveTester("./bot")

# Send message
responses = tester.test_message("!help", user_role="admin")

# Access responses
for response in responses:
    print(response["text"])
```

## For AI Agents

### LangChain Integration Example

```python
from langchain.tools import tool
from agent_tester import AIAgentBotTester

@tool
def test_bot_command(command: str, user_role: str = "admin") -> str:
    """Test a bot command and return the response."""
    tester = AIAgentBotTester(".")
    
    try:
        responses = tester.test(command, user_role=user_role)
        return "\n".join(r.get("text", "") for r in responses)
    except Exception as e:
        return f"Error: {e}"

# Agent can now use this tool
tools = [test_bot_command]
```

### Custom Agent Loop

```python
from agent_tester import AIAgentBotTester

class BotTestingAgent:
    def __init__(self, bot_path=".", model=None):
        self.tester = AIAgentBotTester(bot_path)
        self.model = model  # e.g., OpenAI, Anthropic, etc.
    
    def test_hypothesis(self, hypothesis: str) -> bool:
        """Test if a hypothesis about bot behavior is true."""
        
        # Convert hypothesis to testable commands
        commands = self._parse_hypothesis(hypothesis)
        
        # Test each command
        for cmd in commands:
            try:
                response = self.tester.test_admin(cmd)
                
                # Verify against hypothesis
                if self._verify(hypothesis, response):
                    return True
            except Exception as e:
                print(f"Test failed: {e}")
                return False
        
        return False
    
    def _parse_hypothesis(self, hypothesis: str) -> list:
        """Use LLM to convert hypothesis to test commands."""
        # This would call your LLM to generate test commands
        return ["!help"]  # Placeholder
    
    def _verify(self, hypothesis: str, response: list) -> bool:
        """Use LLM to verify if response matches hypothesis."""
        # This would call your LLM to check
        return True  # Placeholder
```

### Automated Test Generation

```python
from agent_tester import AIAgentBotTester

class AutomatedTestGenerator:
    def __init__(self, bot_path="."):
        self.tester = AIAgentBotTester(bot_path)
    
    def generate_and_run_tests(self, command_spec: dict) -> dict:
        """
        Generate and run tests based on command specification.
        
        Args:
            command_spec: {
                "command": "!play",
                "test_cases": [
                    {"input": "!play", "expected_response": "game started"},
                    {"input": "yes", "expected_response": "difficulty"},
                ]
            }
        
        Returns:
            Test results
        """
        results = {
            "passed": [],
            "failed": [],
            "errors": []
        }
        
        for test_case in command_spec.get("test_cases", []):
            try:
                response = self.tester.test_admin(test_case["input"])
                response_text = " ".join(r.get("text", "") for r in response)
                
                if test_case["expected_response"].lower() in response_text.lower():
                    results["passed"].append(test_case)
                else:
                    results["failed"].append({
                        "test": test_case,
                        "got": response_text
                    })
            except Exception as e:
                results["errors"].append({
                    "test": test_case,
                    "error": str(e)
                })
        
        return results
```

## API Reference for Agents

### AIAgentBotTester Methods

```python
# Initialize
tester = AIAgentBotTester(bot_path)

# Single message
tester.test(message, user_role="admin")
tester.test_admin(message)
tester.test_user(message)

# Multiple messages
tester.test_batch(["msg1", "msg2", ...], user_role="admin")
tester.test_conversation("msg1", "msg2", ...)  # as admin

# With attachments
tester.test_with_image(message, image_url)

# Load testing
tester.test_high_volume(message, count=100, interval=0.1)

# Edge cases
tester.test_duplicate(message)           # Duplicate handling
tester.test_error(message, error_code=409)  # Error simulation

# Bot info
tester.get_info()  # Returns webhook_route, bot_dir, test_users

# Assertions (for testing)
tester.assert_response(
    responses, 
    contains="expected text",
    count=1,
    has_image=False
)
```

### Return Format

All test methods return a list of response dictionaries:

```python
[
    {
        "text": "Response text",
        "attachments": [
            {
                "type": "image",
                "url": "https://...",
                "is_local_file": False
            }
        ]
    }
]
```

## Error Handling

```python
from agent_tester import AIAgentBotTester

tester = AIAgentBotTester(".")

try:
    # Bot might not load
    if not tester.loaded:
        print("Failed to load bot")
        exit(1)
    
    # Test might fail
    responses = tester.test_admin("!help")
    
except RuntimeError as e:
    # Specific test error
    print(f"Test error: {e}")
except Exception as e:
    # General error
    print(f"Unexpected error: {e}")
```

## Testing Best Practices for Agents

### 1. Always Check Bot Loads
```python
tester = AIAgentBotTester(".")
if not tester.loaded:
    # Handle bot not loading
    print("Cannot proceed without bot")
    return
```

### 2. Test Both Admin and User
```python
# Check permissions
admin_response = tester.test_admin("!ban user")
user_response = tester.test_user("!ban user")

# Verify they're different
if len(admin_response) > 0 and len(user_response) == 0:
    print("Permissions working correctly")
```

### 3. Use Batch Testing for Flows
```python
# Test conversation flows as batch
responses = tester.test_conversation(
    "!start",
    "option1",
    "option2"
)

# All responses are captured together
print(f"Full conversation: {len(responses)} responses")
```

### 4. Handle Timeouts
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout

try:
    responses = tester.test_high_volume("msg", count=1000)
except TimeoutError:
    print("Test suite timed out")
finally:
    signal.alarm(0)
```

### 5. Validate Responses
```python
def validate_response(responses, expected_contains=None):
    """Validate bot response meets expectations."""
    
    if not responses:
        raise ValueError("No response from bot")
    
    text = " ".join(r.get("text", "") for r in responses)
    
    if expected_contains:
        for expected in expected_contains:
            if expected not in text:
                raise ValueError(f"Response missing: {expected}")
    
    return True
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Test Bot with CLI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Test bot with CLI tester
        run: |
          python src/cli_tester.py --bot . --message "!help" --output json
          python src/cli_tester.py --bot . --batch examples/test_messages_basic.txt
      
      - name: Run full test suite
        run: bash run_test_suite.sh
```

## Debugging

### Enable Verbose Output
```bash
python src/cli_tester.py --bot . --message "test" --verbose
```

### Check Bot Info
```bash
python src/cli_tester.py --bot . --info
```

### Inspect Raw Responses
```python
tester = AIAgentBotTester(".", auto_load=False)
tester.load()  # See verbose output

responses = tester.test_admin("!help")
print(json.dumps(responses, indent=2))
```

## Performance Considerations

1. **Reuse Tester Instance**: Create once, use many times
   ```python
   tester = AIAgentBotTester(".")  # Create once
   for msg in messages:
       tester.test_admin(msg)  # Reuse
   ```

2. **Batch Testing**: Use `test_batch()` for multiple messages
   ```python
   responses = tester.test_batch(messages)  # More efficient
   ```

3. **Timeout Management**: High volume tests can take time
   ```python
   # Reduce count for faster tests
   responses = tester.test_high_volume("msg", count=10)
   ```

4. **Parallel Testing**: Run multiple tester instances if needed
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   testers = [AIAgentBotTester(".") for _ in range(4)]
   
   with ThreadPoolExecutor() as executor:
       results = executor.map(lambda t: t.test_admin("!help"), testers)
   ```

## Examples Directory

See `examples/` for complete working examples:
- `ai_agent_testing.py` - Full test suite example
- `test_messages_basic.txt` - Example batch messages
