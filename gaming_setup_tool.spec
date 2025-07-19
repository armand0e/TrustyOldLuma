# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Gaming Setup Tool.

This file configures PyInstaller to create a standalone executable
for the Gaming Setup Tool with all required dependencies and assets.

Usage:
    pyinstaller gaming_setup_tool.spec
"""

import os
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Define paths
assets_dir = current_dir / "assets"
readme_file = current_dir / "README.md"
requirements_file = current_dir / "requirements.txt"

# Collect all Python modules
modules = [
    'gaming_setup_tool',
    'admin_manager',
    'applist_manager',
    'cleanup_manager',
    'config',
    'configuration_handler',
    'display_managers',
    'error_manager',
    'exceptions',
    'file_operations_manager',
    'models',
    'security_config_manager',
    'shortcut_manager'
]

# Hidden imports for dependencies that might not be auto-detected
hidden_imports = [
    'rich.console',
    'rich.progress',
    'rich.panel',
    'rich.text',
    'rich.table',
    'rich.logging',
    'rich.traceback',
    'rich.prompt',
    'rich.spinner',
    'rich.status',
    'ctypes.wintypes',
    'win32com.client',
    'pythoncom',
    'pywintypes'
]

# Data files to include
datas = []

# Add assets directory if it exists
if assets_dir.exists():
    datas.append((str(assets_dir), 'assets'))

# Add documentation files
if readme_file.exists():
    datas.append((str(readme_file), '.'))

if requirements_file.exists():
    datas.append((str(requirements_file), '.'))

# Analysis configuration
a = Analysis(
    ['gaming_setup_tool.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx'
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
    name='gaming-setup-tool',
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
    icon=None,  # Add icon file path here if available
    version_file=None,  # Add version file path here if available
)

# Optional: Create a directory distribution instead of a single file
# Uncomment the following lines to create a directory distribution:

# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='gaming-setup-tool'
# )