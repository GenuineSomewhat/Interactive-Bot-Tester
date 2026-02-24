# Interactive Tester - Standalone Tool

This is a **standalone interactive testing tool** for Flask-based bots. It auto-discovers and loads any bot in your directory for interactive testing.

## Quick Start

### Option 1: Test a Bot in Its Own Directory
```bash
# Copy the tester to your bot directory
cp interactive_test.py /path/to/your-bot/

# Run it
cd /path/to/your-bot/
python interactive_test.py
```

### Option 2: Test from Parent Directory
```bash
# Run from parent directory pointing to a specific bot
python interactive_test.py ../path/to/bot-folder/app.py
```

### Option 3: Use Full Path
```bash
python interactive_test.py /full/path/to/bot.py
```

## Files Included

- **interactive_test.py** - Main tester script (standalone, no dependencies except Flask/requests)
- **AUTODISCOVERY_GUIDE.md** - Complete auto-discovery documentation
- **GENERIC_TESTER_GUIDE.md** - Full API and usage guide

## How It Works

1. **Auto-Discovery**
   - Scans directory for Flask bot files
   - Filters out test files
   - Loads bot automatically (or shows menu)

2. **Auto-Detection**
   - Finds Flask app instance
   - Detects webhook route (`/`, `/webhook`, etc.)
   - Discovers bot state variables

3. **Interactive Testing**
   - Send messages to bot
   - Switch users
   - View bot state
   - Track responses

## Tested With

✅ **Sigma Bot** (lkh-sigma/)
- Root route: `/`
- Commands: `sigma online`, `left kidney`, etc.
- State tracking: MUTED, COMMANDS, VIOLATION_COUNTS

✅ **ClankerBot** (bot-test/)
- Custom route: `/webhook`
- Commands: `5!`, `100!`, etc.
- State tracking: ADMIN_IDS, SWEAR_WORDS

## Available Commands

Once running:
```
[TestUser]> sigma online        # Send message
[TestUser]> user:Alice          # Switch user
[TestUser]> dummy add Bob 999   # Add test user
[TestUser]> dummy list          # List users
[TestUser]> state               # Show bot state
[TestUser]> cmds                # List commands
[TestUser]> help                # Show help
[TestUser]> quit                # Exit
```

## Example Usage

### Sigma Bot
```bash
cd ../lkh-sigma
python ../interactive-tester/interactive_test.py

[AUTO] Single bot found: app.py
[INFO] Loaded bot from: /path/to/app.py
[INFO] Using webhook route: /

[TestUser]> sigma online
Bot responses:
  [1] ∑ is online.
```

### ClankerBot
```bash
cd ../bot-test
python ../interactive-tester/interactive_test.py

[AUTO] Single bot found: app.py
[INFO] Loaded bot from: /path/to/app.py
[INFO] Using webhook route: /webhook

[TestUser]> 5!
Bot responses:
  [1] 5! = 120
```

## Installation

Option A: Copy directly
```bash
cp interactive_test.py /path/to/your-bot/
cd /path/to/your-bot/
python interactive_test.py
```

Option B: Use from external location
```bash
python /path/to/interactive-tester/interactive_test.py /path/to/your-bot/app.py
```

Option C: Create symlink (Linux/Mac)
```bash
ln -s /path/to/interactive-tester/interactive_test.py /path/to/your-bot/interactive_test.py
```

## Requirements

- Python 3.7+
- Flask (your bot's dependency)
- requests (your bot's dependency)

## Troubleshooting

**Q: "No Flask bot files found"**
- Make sure your bot has `app = Flask(...)` and `@app.route()` decorators
- Or provide explicit path: `python interactive_test.py app.py`

**Q: "No Flask app instance found"**
- Bot's Flask app must be a module-level variable (usually named `app`)
- Check that your bot.py has proper Flask setup

**Q: Can't find the tester**
- Make sure you're in the bot directory or provide full path
- Run: `python /path/to/interactive-tester/interactive_test.py`

## Documentation

For more details, see:
- **AUTODISCOVERY_GUIDE.md** - Auto-discovery features
- **GENERIC_TESTER_GUIDE.md** - Complete reference guide

## Directory Structure

```
Documents/
├── interactive-tester/          ← YOU ARE HERE
│   ├── interactive_test.py     (main script)
│   ├── README.md               (this file)
│   ├── AUTODISCOVERY_GUIDE.md
│   └── GENERIC_TESTER_GUIDE.md
│
├── lkh-sigma/                   ← Sigma Bot
│   ├── app.py
│   ├── commands.json
│   └── ... (bot files)
│
└── bot-test/                    ← ClankerBot
    ├── app.py
    ├── requirements.txt
    └── ... (bot files)
```

## Usage from Bot Folders

Both bot folders can reference this tester:

```bash
# From lkh-sigma/
python ../interactive-tester/interactive_test.py

# From bot-test/
python ../interactive-tester/interactive_test.py
```

Or copy it locally:
```bash
cp ../interactive-tester/interactive_test.py .
python interactive_test.py
```

## Tips

1. **Test multiple bots simultaneously**
   - Open separate terminals in each bot folder
   - Run tester in each one

2. **Record test sequences**
   - Use shell history to replay commands
   - Create test scripts that use the tester API

3. **Integrate with CI/CD**
   - Use programmatically: `from interactive_test import InteractiveTester`
   - Run automated test suites

4. **Skip discovery**
   - Provide explicit path to bypass auto-discovery
   - Useful if directory has multiple Python files

## License & Credits

Created as a generic testing tool for GroupMe bots.
Works with any Flask-based bot following standard patterns.

## Support

For issues or questions:
1. Check AUTODISCOVERY_GUIDE.md for features
2. Check GENERIC_TESTER_GUIDE.md for API details
3. Ensure bot has Flask setup and routes
