# Building Executables

This guide explains how to build standalone executables of the Bot Interactive Tester for Windows, macOS, and Linux.

## Quick Start

### Windows
```powershell
.\build.ps1
```

### macOS / Linux
```bash
chmod +x build.sh
./build.sh
```

Executables will be in the `dist/` folder.

---

## Prerequisites

1. **Python 3.8+** installed
2. **Virtual environment** activated
3. **All dependencies** installed:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

---

## Build Options

### Option 1: Automated Build (Recommended)

Use the provided build scripts:

**Windows:**
```powershell
.\build.ps1
```

**macOS/Linux:**
```bash
chmod +x build.sh
./build.sh
```

This builds both GUI and CLI versions automatically.

### Option 2: Manual Build

**GUI Version:**
```bash
pyinstaller build_gui.spec --clean
```

**CLI Version:**
```bash
pyinstaller build_cli.spec --clean
```

### Option 3: Command-Line Build

**GUI (without spec file):**
```bash
pyinstaller --onefile --windowed --name "BotTester" \
  --hidden-import=customtkinter \
  --hidden-import=PIL \
  --hidden-import=flask \
  src/interactive_gui.py
```

**CLI (without spec file):**
```bash
pyinstaller --onefile --name "BotTesterCLI" \
  --hidden-import=flask \
  --hidden-import=importlib.util \
  src/interactive_test.py
```

---

## Output

After building, you'll find:

```
dist/
├── BotTester.exe       (GUI version - Windows)
├── BotTester           (GUI version - macOS/Linux)
├── BotTesterCLI.exe    (CLI version - Windows)
└── BotTesterCLI        (CLI version - macOS/Linux)
```

These executables are **standalone** and can be distributed without Python.

---

## Platform-Specific Notes

### Windows
- `.exe` files are created
- May trigger Windows Defender (false positive) - click "More info" → "Run anyway"
- To add an icon: `--icon=icon.ico` in the spec file

### macOS
- Creates Unix executable
- May need to allow in System Preferences → Security & Privacy
- For `.app` bundle: Use `--windowed` and rename to `BotTester.app`
- Code signing recommended for distribution

### Linux
- Creates Unix executable
- May need to make executable: `chmod +x dist/BotTester`
- Different distros may need different builds

---

## Troubleshooting

### "Module not found" errors
Add missing modules to `hiddenimports` in the spec files:
```python
hiddenimports=[
    'your_missing_module',
],
```

### Large executable size
- Normal: 50-100 MB (includes Python + dependencies)
- To reduce: Use `--exclude-module` for unused packages
- Alternative: Use directory mode instead of `--onefile`

### Import errors at runtime
- Check `hiddenimports` in spec file
- Use `--debug all` for detailed logs
- Test in a clean environment

### GUI doesn't show
- Ensure `console=False` in GUI spec
- On macOS: May need `--windowed-darwin` flag

---

## File Structure

```
interactive-tester/
├── src/
│   ├── interactive_gui.py    # GUI source
│   └── interactive_test.py   # CLI source
├── docs/                      # Documentation (included in build)
├── build_gui.spec             # PyInstaller config for GUI
├── build_cli.spec             # PyInstaller config for CLI
├── build.ps1                  # Windows build script
├── build.sh                   # macOS/Linux build script
├── build/                     # Temporary build files (auto-generated)
└── dist/                      # Final executables (auto-generated)
```

---

## Distribution

The executables in `dist/` can be:
- Copied to other computers (same OS)
- Shared without requiring Python installation
- Run directly by double-clicking (GUI) or from terminal (CLI)

**Note:** Executables are OS-specific:
- Build on Windows → works on Windows
- Build on macOS → works on macOS
- Build on Linux → works on Linux

---

## Advanced Configuration

### Custom Icon (Windows)
1. Get an `.ico` file
2. Edit spec file:
   ```python
   exe = EXE(
       ...,
       icon='path/to/icon.ico',
   )
   ```

### Include Additional Files
Edit spec file `datas` section:
```python
datas=[
    ('docs', 'docs'),
    ('config.json', '.'),
    ('images', 'images'),
],
```

### Reduce Size
Edit spec file:
```python
excludes=[
    'matplotlib',
    'numpy',
    'scipy',
],
```

---

## Testing the Build

1. **Test locally:**
   ```bash
   dist/BotTester.exe     # Windows GUI
   dist/BotTesterCLI.exe  # Windows CLI
   ```

2. **Test on clean system:**
   - Copy to computer without Python
   - Try loading a bot
   - Test all features

3. **Check dependencies:**
   ```bash
   # Windows
   dumpbin /dependents dist/BotTester.exe
   
   # Linux/macOS
   ldd dist/BotTester
   otool -L dist/BotTester
   ```

---

## Support

For issues:
1. Check error messages in console
2. Try `--debug all` flag
3. Verify all imports work in Python first
4. Check PyInstaller documentation: https://pyinstaller.org
