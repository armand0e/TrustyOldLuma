# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TrustyOldLuma Setup
Configures packaging of the Python setup application into a standalone executable.
"""

import os
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Define data files to include
datas = [
    # Configuration file
    ('Config.jsonc', '.'),
    # Icon file
    ('assets/icon.ico', 'assets'),
    # Include any additional config files if they exist
]

# Include embedded Koalageddon binaries if they exist
koalageddon_binaries_dir = current_dir / 'koalageddon_binaries'
if koalageddon_binaries_dir.exists():
    # Add all files from the koalageddon_binaries directory
    for binary_file in koalageddon_binaries_dir.rglob('*'):
        if binary_file.is_file() and binary_file.name != 'README.md':
            # Calculate relative path for inclusion
            rel_path = binary_file.relative_to(koalageddon_binaries_dir)
            datas.append((str(binary_file), f'koalageddon_binaries/{rel_path.parent}' if rel_path.parent != Path('.') else 'koalageddon_binaries'))

# Check for additional data files that might exist
additional_files = [
    'example_config.jsonc',
    'README.md',
]

for file in additional_files:
    if (current_dir / file).exists():
        datas.append((file, '.'))

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    # Rich library components
    'rich',
    'rich.console',
    'rich.panel',
    'rich.progress',
    'rich.status',
    'rich.text',
    'rich.align',
    'rich.prompt',
    'rich.pager',
    'rich.live',
    'rich.logging',
    'rich.traceback',
    'rich.table',
    'rich.columns',
    'rich.layout',
    'rich.spinner',
    'rich.style',
    'rich.color',
    'rich.theme',
    'rich.highlighter',
    'rich.markup',
    'rich.measure',
    'rich.segment',
    'rich.cells',
    'rich.control',
    'rich.filesize',
    'rich.tree',
    'rich.syntax',
    
    # Standard library modules that might need explicit inclusion
    'ctypes',
    'ctypes.wintypes',
    'subprocess',
    'urllib.request',
    'urllib.error',
    'urllib.parse',
    'zipfile',
    'json',
    'configparser',
    'pathlib',
    'tempfile',
    'shutil',
    'logging',
    'traceback',
    'threading',
    'signal',
    'time',
    'datetime',
    'enum',
    'dataclasses',
    're',
    
    # Windows-specific modules
    'winreg',
    'msvcrt',
]

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TrustyOldLuma-Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)