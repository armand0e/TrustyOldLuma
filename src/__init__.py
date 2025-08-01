"""
Python Setup UI Package

This package provides a modern, Rich-based terminal interface for the TrustyOldLuma setup process.
It transforms the existing batch script setup into a sophisticated Python application with
colorful terminal interface, progress tracking, and comprehensive error handling.

Main Components:
- SetupController: Orchestrates the entire setup process
- UIManager: Handles Rich-based terminal interface elements
- AdminHandler: Manages privilege escalation and admin-only operations
- FileOperationsManager: Handles file operations with progress tracking
- DownloadManager: Manages file downloads with progress tracking
- ConfigurationManager: Updates configuration files and creates shortcuts
- ErrorHandler: Provides comprehensive error handling and user guidance
- DataModels: Defines data structures and configuration models
"""

__version__ = "1.0.0"
__author__ = "TrustyOldLuma Team"

# Core modules for external import
from .setup_controller import SetupController
from .ui_manager import UIManager
from .admin_handler import AdminHandler
from .file_operations import FileOperationsManager
from .download_manager import DownloadManager
from .configuration_manager import ConfigurationManager
from .error_handler import ErrorHandler, ErrorCategory
from .data_models import SetupConfig, OperationResult, load_default_configuration

__all__ = [
    "SetupController",
    "UIManager", 
    "AdminHandler",
    "FileOperationsManager",
    "DownloadManager",
    "ConfigurationManager",
    "ErrorHandler",
    "ErrorCategory",
    "SetupConfig",
    "OperationResult",
    "load_default_configuration"
]