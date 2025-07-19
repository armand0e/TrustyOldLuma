"""
Configuration module for the Luna Setup Tool.

This module contains configuration constants and settings used throughout
the Luna application.
"""

from pathlib import Path
from typing import Dict, Any

# Application metadata
APP_NAME = "Luna Gaming Tool"
APP_VERSION = "1.0.0"

# Logging configuration
LOG_FORMAT = "%(message)s"
LOG_DATE_FORMAT = "[%X]"

# Rich UI styling
PANEL_STYLES: Dict[str, Dict[str, Any]] = {
    'welcome': {
        'border_style': 'cyan',
        'padding': (1, 2)
    },
    'error': {
        'border_style': 'red',
        'title_align': 'left'
    },
    'success': {
        'border_style': 'green',
        'title_align': 'left'
    },
    'warning': {
        'border_style': 'yellow',
        'title_align': 'left'
    },
    'completion': {
        'border_style': 'cyan',
        'subtitle_align': 'center'
    }
}

# Default Luna paths (will be configured based on environment)
DEFAULT_DOCUMENTS_PATH = Path.home() / "Documents"
DEFAULT_LUNA_PATH = DEFAULT_DOCUMENTS_PATH / "Luna"
DEFAULT_LUNA_CONFIG_PATH = DEFAULT_LUNA_PATH / "config"

# Legacy paths for migration
LEGACY_GREENLUMA_PATH = DEFAULT_DOCUMENTS_PATH / "GreenLuma"
LEGACY_KOALAGEDDON_PATH = Path.home() / "AppData" / "Roaming" / "Koalageddon"

# Network configuration
DOWNLOAD_TIMEOUT = 30  # seconds
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0  # seconds

# Error handling configuration
ERROR_CATEGORIES = {
    'CRITICAL': 'critical',
    'RECOVERABLE': 'recoverable',
    'NETWORK': 'network',
    'PLATFORM': 'platform'
}

# Platform-specific feature flags
PLATFORM_FEATURES = {
    'windows_admin': True,
    'windows_defender': True,
    'windows_shortcuts': True,
    'powershell': True,
    'linux_desktop_entries': False,
    'macos_aliases': False
}