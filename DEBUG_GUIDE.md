# Bot Window Opening Issue - Debugging Guide

## What We've Done

We've added comprehensive logging to help diagnose why new windows are opening when loading a bot. The updated .exe will now log all activity to a debug file.

## How to Check the Debug Log

1. **Run the updated .exe** normally (just double-click it)
2. **Click "Load bot"** and select your bot folder
3. **Observe if new windows open**
4. **Check for the log file** at:
   ```
   C:\Users\miles\tester_debug.log
   ```

## What to Look For in the Log

Open the debug.log file and look for these key indicators:

**Expected output when TESTING_MODE is working:**
```
[IMPORT] TESTING_MODE env var = 1
[BOT STARTUP] TESTING_MODE=True, Will spawn threads: False
[BOT STARTUP] TESTING_MODE active - skipping background threads
```

**If you see this instead, something is wrong:**
```
[BOT IMPORT] TESTING_MODE env var = None
[BOT STARTUP] TESTING_MODE=False, Will spawn threads: True
[BOT STARTUP] Starting background threads...
```

## Next Steps

1. **After loading the bot**, send the entire contents of `C:\Users\miles\tester_debug.log` 
2. Include the exact names and descriptions of any new windows that opened
3. Note how many windows open and in what order

## Workaround for Now

If new windows keep opening, you can:
- Try to close them quickly when they appear
- The bot should still work in the GUI despite the extra windows
- Report what's in the log file so we can identify the cause

## Additional Info

The log file contains timestamps and debug messages from:
- Bot module loading
- Environment variable checks
- Thread creation (or skipping)
- Addon discovery
- Message processing

If the log file doesn't exist after loading a bot, that indicates a different problem - the bot might be crashing before it can even attempt to load.
