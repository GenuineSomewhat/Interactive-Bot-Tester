# Generic Interactive Bot Tester - Complete Implementation

## Summary

The interactive bot tester has been successfully refactored to work with **any bot** that implements the standard bot interface. It's been tested with both the Sigma Bot (lkh-sigma) and ClankerBot (external repo).

## What Was Accomplished

### 1. **Generic Bot Loader**
- Dynamically loads any Python bot module
- Auto-detects Flask app instance
- Discovers webhook routes automatically (`/webhook`, `/`, etc.)
- Finds all mutable state variables in the bot

### 2. **Intelligent Route Detection**
- Scans all POST routes in the Flask app
- Prioritizes common webhook routes (`/webhook`, `/webhooks`, `/message`, `/`)
- Falls back to first available POST route if needed
- Displays detected routes for debugging

### 3. **Cross-Bot Compatibility**
- ✅ **Sigma Bot** (lkh-sigma) - Root route "/"
- ✅ **ClankerBot** (bot-test) - Custom "/webhook" route
- Handles different bot structures and configurations
- Works with different command patterns and responses

### 4. **Multi-User Testing**
- Add/remove/switch test users
- Track actions per user
- Send messages as specific users
- View bot state changes in real-time

### 5. **Enhanced Documentation**
- `BOT_INTERFACE.md` - Bot interface requirements
- `TESTING.md` - Usage guide for external bot
- Demo scripts showing practical usage
- Comprehensive help system within interactive mode

## File Locations

### Sigma Bot (lkh-sigma/)
```
interactive_test.py      ← Generic tester (main)
test_interactive_tester.py  ← Test suite
test_external_bot.py     ← External bot test
BOT_INTERFACE.md         ← Bot interface spec
```

### External Bot (bot-test/)
```
interactive_test.py      ← Copy of generic tester
demo_interactive_tester.py  ← Demo script
TESTING.md               ← Usage guide
```

## Quick Usage

### From Either Directory

```bash
# Test with default bot module (app.py)
python interactive_test.py

# Test with specific bot
python interactive_test.py /path/to/bot.py
```

### Interactive Commands

```
[TestUser]> 5!                    # Send message
[TestUser]> user:Alice            # Switch user
[TestUser]> dummy add Bob 999     # Add test user
[TestUser]> dummy use Bob         # Activate user
[TestUser]> state                 # Show bot state
[TestUser]> cmds                  # List commands
[TestUser]> help                  # Show help
[TestUser]> quit                  # Exit
```

## Test Results

### Sigma Bot
```
✓ Tester initialized
✓ Found state: MUTED, VIOLATION_COUNTS, COMMANDS
✓ Basic commands working
✓ Multiple users supported
✓ Message capture functional
```

### ClankerBot
```
✓ Custom route detected (/webhook)
✓ Bot loaded successfully
✓ Factorial calculations working
✓ Multi-user testing functional
✓ State attributes discovered
```

## How It Works

1. **Module Loading**
   ```python
   spec = importlib.util.spec_from_file_location(name, path)
   module = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(module)
   ```

2. **App Discovery**
   ```python
   # Finds Flask app by checking for test_client() method
   for attr in dir(module):
       if hasattr(attr, 'test_client') and hasattr(attr, 'route'):
           flask_app = attr
   ```

3. **Route Detection**
   ```python
   # Scans Flask app URL map for POST routes
   for rule in app.url_map.iter_rules():
       if 'POST' in rule.methods:
           # Use this route
   ```

4. **Message Injection**
   ```python
   # Creates Flask test client and sends JSON to detected route
   client = app.test_client()
   client.post(webhook_route, json=event_data)
   ```

## Key Features

### Dynamic Patching
- Patches `send_message()` to capture responses
- Patches deletion/ban functions for action tracking
- Uses ExitStack for clean multi-patch management
- Works even if functions don't exist in bot

### State Management
- Automatically discovers all uppercase dict/list variables
- Shows current state with `state` command
- Clears state with `reset` command
- Tracks changes in real-time

### Extensibility
- Works with any Flask bot
- No modifications needed to bot code
- Supports custom routes and configurations
- Handles different message formats

## Error Handling

The tester gracefully handles:
- Missing bot modules
- No Flask app found
- Different route structures
- Missing API functions
- Bot initialization errors
- Message processing failures

## Testing Other Bots

To test your own bot:

1. **Navigate to bot directory**
   ```bash
   cd /path/to/your/bot
   ```

2. **Copy the tester**
   ```bash
   cp /path/to/lkh-sigma/interactive_test.py .
   ```

3. **Run it**
   ```bash
   python interactive_test.py app.py
   # or
   python interactive_test.py
   ```

The tester will automatically:
- Detect your bot structure
- Find the correct webhook route
- Discover state variables
- Start interactive mode

## Limitations

1. **External API Calls**: Mocked/disabled during testing
2. **Authentication**: Uses test tokens or mock auth
3. **Persistence**: State doesn't persist unless explicitly managed
4. **Complex Logic**: Long-running processes/threads may need adjustment

## Future Enhancements

Possible improvements:
- Record/replay test sequences
- Generate test coverage reports
- Compare bot responses across versions
- Batch testing from file
- Performance profiling
- Integration with CI/CD pipeline

## Conclusion

The generic interactive tester successfully bridges the gap between development and testing, allowing developers to:
- ✅ Test bots without deploying
- ✅ Debug command handlers interactively
- ✅ Simulate multiple users
- ✅ Track bot state changes
- ✅ Work with any Flask-based bot

This makes bot testing faster, easier, and more accessible!
