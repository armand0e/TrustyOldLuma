#!/usr/bin/env python3
"""
Luna Integration Test Runner

This script runs the Luna component and workflow integration tests.
"""

import sys
import os
import subprocess
from pathlib import Path


def setup_environment():
    """Set up the environment for testing."""
    # Add the project root to Python path to help with imports
    project_root = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(project_root))
    
    # Add src directory to Python path if it exists
    src_dir = project_root / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
    
    # Print environment info
    print(f"Python version: {sys.version}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")


def run_tests():
    """Run Luna integration tests."""
    print("\n" + "="*60)
    print("Running Luna Integration Tests")
    print("="*60)
    
    # Set up environment
    setup_environment()
    
    # Get the test files
    test_files = [
        "tests/integration/test_luna_component_integration.py",
        "tests/integration/test_luna_workflow_integration.py"
    ]
    
    # Build the command
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--no-header",  # No pytest header
        "--tb=native",  # Native traceback format
    ]
    
    # Add test files
    cmd.extend(test_files)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Luna integration tests completed successfully")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Luna integration tests failed with exit code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(run_tests())