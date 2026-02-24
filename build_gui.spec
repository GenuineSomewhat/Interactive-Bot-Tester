# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for GUI version

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Collect all customtkinter files
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')

a = Analysis(
    ['src/interactive_gui.py'],
    pathex=[],
    binaries=ctk_binaries,
    datas=ctk_datas + [('icon.ico', '.')],  # Include icon.ico in root of executable
    hiddenimports=[
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.widgets',
        'PIL',
        'PIL._tkinter_finder',
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
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ] + ctk_hiddenimports,
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
    icon='icon.ico',  # Use icon.ico file
)
