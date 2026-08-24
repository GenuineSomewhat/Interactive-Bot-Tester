# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Interactive Bot Tester GUI

block_cipher = None

a = Analysis(
    ['src/interactive_gui.py'],
    pathex=['src'],  # Add src to path so it can find modules
    binaries=[],
    datas=[('src/interactive_test.py', 'src'), ('icon.ico', '.')],  # Bundle interactive_test.py and icon
    hiddenimports=[
        'interactive_test',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'flask',
        'flask.json',
        'werkzeug',
        'werkzeug.routing',
        'werkzeug.serving',
        'jinja2',
        'jinja2.ext',
        'click',
        'importlib',
        'importlib.util',
        'importlib.metadata',
        'json',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'urllib',
        'urllib.request',
        'urllib.error',
        'subprocess',
        'threading',
        'pathlib',
        # Bot dependencies
        'fuzzywuzzy',
        'fuzzywuzzy.fuzz',
        'fuzzywuzzy.process',
        'requests',
        'google',
        'google.generativeai',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Interactive Bot Tester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    onefile=True,  # Single executable file
)
