# Interactive Tester - Auto-Discovery Mode

The interactive tester now includes **automatic bot discovery** - it can find and load Flask bots without any configuration!

## Quick Start

```bash
# Navigate to your bot directory
cd /path/to/your/bot

# Just run it!
python interactive_test.py
```

That's it! The tester will:
1. Scan for Flask bot files
2. Load the bot automatically
3. Start interactive testing

## Scenarios

### Single Bot (Automatic Load)
```bash
$ cd my-bot-repo
$ python interactive_test.py

[AUTO] Single bot found: app.py
[INFO] Loaded bot from: /path/to/app.py
[INFO] Using webhook route: /webhook

[TestUser]> 5!
Bot responses:
  [1] 5! = 120
```

### Multiple Bots (Menu Selection)
```bash
$ cd project-with-multiple-bots
$ python interactive_test.py

======================================================================
AVAILABLE BOTS FOUND
======================================================================
  1. main_bot.py                (15,234 bytes)
  2. utility_bot.py             (8,456 bytes)

Select bot to test (number or 'q' to cancel): 1
[INFO] Loaded bot from: /path/to/main_bot.py
```

### Explicit Path (Override Auto-Discovery)
```bash
# Still supports explicit path argument
python interactive_test.py /path/to/specific_bot.py
```

## How It Works

### 1. **Bot Discovery**
Scans the current directory for Python files that look like Flask bots by checking for:
- `from flask import Flask` or similar imports
- `app = Flask(...)` declarations
- `@app.route()` or `@app.post()` route definitions

### 2. **Exclusion Filter**
Automatically excludes:
- Test files (files starting with `test_`, containing `test`)
- Demo files (files starting with `demo_`)
- The tester script itself (`interactive_test.py`)
- Special/hidden files

### 3. **Auto-Load Logic**
- **0 bots found**: Shows error and usage instructions
- **1 bot found**: Loads it automatically
- **2+ bots found**: Displays an interactive menu
- **Explicit path given**: Uses specified path (no discovery)

### 4. **State Auto-Discovery**
Once loaded, automatically discovers:
- Bot's Flask app instance
- Webhook route (`/webhook`, `/`, etc.)
- All mutable state variables (COMMANDS, MUTED, etc.)

## Usage Examples

### Example 1: Test Sigma Bot
```bash
cd lkh-sigma
python interactive_test.py

[AUTO] Single bot found: app.py
[INFO] Found state attributes: COMMANDS, MUTED, VIOLATION_COUNTS
[INFO] Using webhook route: /

[TestUser]> sigma online
Bot responses:
  [1] ∑ is online.

[TestUser]> !leaderboard
Bot responses:
  [1] Daily Message Leaderboard...
```

### Example 2: Test ClankerBot
```bash
cd bot-test
python interactive_test.py

[AUTO] Single bot found: app.py
[INFO] Found state attributes: ADMIN_IDS, INSTANT_BAN_WORDS
[INFO] Using webhook route: /webhook

[TestUser]> 5!
Bot responses:
  [1] 5! = 120

[TestUser]> 100!
Bot responses:
  [1] 100! ≈ 9.3326e+157
```

### Example 3: Multiple Bots with Menu
```
$ python interactive_test.py

======================================================================
AVAILABLE BOTS FOUND
======================================================================
  1. bot_v1.py                  (12,345 bytes)
  2. bot_v2.py                  (15,678 bytes)
  3. experimental_bot.py        (8,901 bytes)

Select bot to test (number or 'q' to cancel): 2
[INFO] Loaded bot from: bot_v2.py
```

## Command-Line Options

```bash
# Auto-discover and load
python interactive_test.py

# Use specific bot (skip discovery)
python interactive_test.py app.py
python interactive_test.py /full/path/to/bot.py

# Combining with relative paths
python interactive_test.py ../other-project/bot.py
```

## Interactive Mode Commands

Once running, you can:

```
[TestUser]> help              # Show command help
[TestUser]> state             # Display bot state
[TestUser]> cmds              # List bot commands
[TestUser]> user:Alice        # Switch user
[TestUser]> dummy add Bob 999 # Add test user
[TestUser]> dummy use Bob     # Switch to test user
[TestUser]> say Alice:message # Send as specific user
[TestUser]> reset             # Clear bot memory
[TestUser]> quit              # Exit tester
```

## Files Included

```
interactive_test.py       ← Main script (now with auto-discovery)
test_autodiscovery.py     ← Test suite for discovery feature
```

## Key Features

✅ **Zero Configuration** - Just run it in any bot directory
✅ **Smart Filtering** - Ignores test files and itself
✅ **Multiple Bot Support** - Shows menu if multiple bots found
✅ **Backward Compatible** - Still supports explicit path argument
✅ **Auto-Detection** - Discovers routes and state automatically
✅ **Easy to Use** - Single command: `python interactive_test.py`

## Error Handling

If something goes wrong:

```bash
# No Flask bots found
[ERROR] No Flask bot files found in current directory
Please provide a bot file path as argument:
  python interactive_test.py /path/to/bot.py

# Invalid bot file
[ERROR] Failed to load bot: No Flask app instance found in app.py

# Wrong directory
[ERROR] No Flask bot files found in current directory
```

## Tips & Tricks

1. **Copy the tester to your bot repo**
   ```bash
   cp interactive_test.py /path/to/your/bot/
   ```

2. **Use relative paths**
   ```bash
   python interactive_test.py ../sibling-bot/app.py
   ```

3. **Run multiple testers in parallel**
   Open two terminals and test different bots simultaneously

4. **Script it**
   ```python
   from interactive_test import InteractiveTester
   tester = InteractiveTester()  # Auto-discovers
   tester.test_message('your command')
   ```

## Architecture

```
┌─────────────────────────────────────┐
│  Run: python interactive_test.py    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  discover_bots() - Scan directory   │
│  Returns: list of Flask bot files   │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
  None        1 bot      2+ bots
   │           │          │
   ▼           ▼          ▼
 Error      Auto-load   Menu
            │
            ▼
    InteractiveTester()
            │
            ▼
    load_bot_module()
            │
    ┌───────┼────────┐
    ▼       ▼        ▼
   App   Routes   State
            │
            ▼
    Interactive Mode
```

## Future Ideas

- Config file support (specify multiple bots)
- Remember last selected bot
- Bot comparison mode (test multiple bots side-by-side)
- Batch testing mode (load test scripts)
- Performance profiling
- Integration with CI/CD

## Troubleshooting

**Q: The tester finds my test files as bots**
A: Add them to a separate directory or rename them with `test_` prefix

**Q: Can't find my bot even though it's in the directory**
A: Make sure it has a Flask `app = Flask(...)` and a route definition

**Q: Want to skip discovery?**
A: Just provide an explicit path: `python interactive_test.py mybot.py`

**Q: Multiple bots but the menu doesn't appear**
A: Check that all files are valid Flask apps with @app.route decorators
