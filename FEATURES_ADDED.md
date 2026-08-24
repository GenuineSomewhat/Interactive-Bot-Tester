# Bot Tester QOL Features

## Three new quality-of-life features have been added:

### 1. **Tabs for Multiple Bot Tests**
- The GUI now supports multiple tabs for testing different bots simultaneously
- Each tab has its own independent chat display, input field, and bot instance
- Use **"New Tab"** button to create a new test tab
- Use **"Close Tab"** button to close the current tab (at least one tab must remain open)
- Switch between tabs by clicking on them
- The tab title automatically updates to show the loaded bot name

### 2. **Clear Text Area on Bot Load**
- When you load a new bot, the chat display is automatically cleared
- This gives you a clean slate for each bot test
- Prevents clutter from previous test runs

### 3. **Drag-and-Drop Bot Folder Support**
- You can now drag a bot folder directly onto `run_gui.bat` (Windows) or `run_gui.sh` (Linux/Mac)
- The bot will automatically load when the GUI starts
- This works because the launcher scripts now accept command-line arguments:
  - `run_gui.bat` and `run_gui.sh` pass any dragged path to the Python script
  - The GUI detects and loads the bot automatically on startup

## How to Use:

### Loading Multiple Bots:
1. Click **"Load Bot"** to load a bot in the current tab
2. Click **"New Tab"** to create another tab
3. Click **"Load Bot"** in the new tab to load a different bot
4. Switch between tabs to test different bots

### Drag-and-Drop (Drag Bot Folder onto Launcher):
1. Open your file explorer and navigate to a bot folder
2. Drag the bot folder onto `run_gui.bat` (Windows) or `run_gui.sh` (Linux/Mac)
3. The GUI will launch and automatically load that bot

### Resetting Bot State:
- Use the **"Reset State"** button to clear the internal state of the current bot
- This clears any dictionaries in the bot module

## Files Modified:
- `src/interactive_gui.py` - Complete rewrite with tab support and class-based tab management
- `run_gui.bat` - Updated to accept command-line arguments
- `run_gui.sh` - Updated to accept command-line arguments
