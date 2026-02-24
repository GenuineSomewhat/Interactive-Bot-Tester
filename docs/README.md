# Bot Interactive Tester

A powerful testing tool for GroupMe bots with both GUI and CLI interfaces. Test your bot's responses, simulate messages, manage state, and debug commands without deploying to a live group.

## Features

- 🎨 **GUI & CLI Modes** - Choose your preferred interface
- 🤖 **Auto-Discovery** - Automatically finds Flask and polling bots
- 📝 **Manifest Support** - Load bot metadata from `manifest.json`
- 👥 **Multi-User Testing** - Simulate different users
- 🖼️ **Image Support** - Send messages with attachments
- 🔄 **State Management** - View and reset bot state
- 📊 **Response Tracking** - See all bot messages and actions
- 🎯 **Direct Mode** - Test commands directly without mocking

## Quick Start

### GUI Version
```bash
python src/interactive_gui.py
```

### CLI Version
```bash
python src/interactive_test.py
```

### Using Batch Files (Windows)
```bash
run_gui.bat
```

## Installation

1. **Clone or download** this repository
2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```
3. **Activate virtual environment:**
   - Windows: `.venv\Scripts\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Building Executables

Want to distribute without Python? Build standalone executables:

```bash
# Windows
.\build.ps1

# macOS/Linux
./build.sh
```

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed instructions.

## Bot Manifest

Add a `manifest.json` to your bot directory for better integration:

```json
{
  "name": "Your Bot Name",
  "type": "Flask",
  "author": "Your Name"
}
```

The tester will automatically:
- Display the bot name instead of filename
- Show author information
- Use the specified type (Flask/Polling)

Without a manifest, the tester auto-detects the bot type from code.

## Documentation

- [Generic Tester Guide](GENERIC_TESTER_GUIDE.md) - Detailed usage instructions
- [Auto-Discovery Guide](AUTODISCOVERY_GUIDE.md) - How bot discovery works
- [Build Guide](BUILD_GUIDE.md) - Creating executables

## Supported Bot Types

### Flask Bots
- Webhook-based bots using Flask
- POST route detection
- Request mocking

### Polling Bots
- Event loop-based bots
- Message fetching simulation
- API call mocking

## Requirements

- Python 3.8+
- Flask 2.3+
- CustomTkinter 5.2+ (GUI only)
- Pillow 10.0+ (for image support)

See `requirements.txt` for full list.

## License

Free to use and modify.
