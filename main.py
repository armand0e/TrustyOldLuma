#!/usr/bin/env python3
"""
TrustyOldLuma Setup - Python Edition

Main entry point for the Python-based setup application with Rich UI.
Transforms the existing batch script setup into a sophisticated Python-based 
setup application with colorful terminal interface and progress tracking.

This application provides:
- Rich terminal UI with colors and progress bars
- Admin privilege management and Windows Security exclusions
- File extraction and configuration management
- Download management with progress tracking
- Comprehensive error handling and user guidance
"""

import sys
import os
from pathlib import Path

# Ensure we can import from src directory
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import after path setup
try:
    from src.setup_controller import SetupController
    from src.error_handler import ErrorHandler, ErrorCategory
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def main() -> int:
    """
    Main entry point for the setup application.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Initialize and run the setup controller
        controller = SetupController()
        return controller.run_setup()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled by user.")
        return 130  # Standard exit code for Ctrl+C
        
    except ImportError as e:
        print(f"\n❌ Missing dependencies: {e}")
        print("Please install required packages: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"\n💥 Unexpected error occurred: {e}")
        print("Please check the error details above and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())