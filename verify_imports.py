#!/usr/bin/env python3
"""
Import verification script to ensure all dependencies are properly installed
and all modules can be imported successfully.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def verify_imports():
    """Verify that all required modules can be imported."""
    print("🔍 Verifying project imports...")
    
    try:
        # Test Rich library imports
        print("  ✓ Testing Rich library imports...")
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import Progress
        from rich.status import Status
        print("    ✅ Rich library imports successful")
        
        # Test standard library imports
        print("  ✓ Testing standard library imports...")
        import json
        import os
        import sys
        import ctypes
        import subprocess
        import urllib.request
        import zipfile
        import logging
        import tempfile
        import shutil
        from pathlib import Path
        from configparser import ConfigParser
        print("    ✅ Standard library imports successful")
        
        # Test project module imports
        print("  ✓ Testing project module imports...")
        from src.setup_controller import SetupController
        from src.ui_manager import UIManager
        from src.admin_handler import AdminHandler
        from src.file_operations import FileOperationsManager
        from src.download_manager import DownloadManager
        from src.configuration_manager import ConfigurationManager
        from src.error_handler import ErrorHandler, ErrorCategory
        from src.data_models import SetupConfig, OperationResult
        print("    ✅ Project module imports successful")
        
        print("\n🎉 All imports verified successfully!")
        return True
        
    except ImportError as e:
        print(f"    ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"    💥 Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)