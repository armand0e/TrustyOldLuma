#!/usr/bin/env python3
"""
Test runner script for Gaming Setup Tool.

This script provides various test execution options including
unit tests, integration tests, performance tests, and coverage reports.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('='*60)
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"\n✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {command[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def install_test_dependencies():
    """Install test dependencies."""
    dependencies = [
        "pytest>=6.0.0",
        "pytest-asyncio>=0.18.0",
        "pytest-cov>=3.0.0",
        "pytest-mock>=3.6.0",
        "pytest-timeout>=2.1.0",
        "pytest-xdist>=2.5.0",  # For parallel test execution
        "coverage>=6.0.0"
    ]
    
    print("Installing test dependencies...")
    for dep in dependencies:
        cmd = [sys.executable, "-m", "pip", "install", dep]
        if not run_command(cmd, f"Installing {dep}"):
            return False
    
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add unit test markers
    cmd.extend(["-m", "unit or not integration"])
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add specific unit test files
    unit_test_files = [
        "test_admin_manager.py",
        "test_file_operations_manager.py",
        "test_security_config_manager.py",
        "test_configuration_handler.py",
        "test_shortcut_manager.py",
        "test_applist_manager.py",
        "test_cleanup_manager.py",
        "test_error_manager.py",
        "test_display_managers.py",
        "test_models.py"
    ]
    
    # Only add files that exist
    existing_files = [f for f in unit_test_files if Path(f).exists()]
    cmd.extend(existing_files)
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add integration test markers
    cmd.extend(["-m", "integration"])
    
    if verbose:
        cmd.append("-v")
    
    # Add specific integration test files
    integration_test_files = [
        "test_gaming_setup_integration.py",
        "test_complete_workflow_integration.py",
        "test_applist_integration.py",
        "test_cleanup_integration.py",
        "test_file_operations_integration.py"
    ]
    
    # Only add files that exist
    existing_files = [f for f in integration_test_files if Path(f).exists()]
    if existing_files:
        cmd.extend(existing_files)
    else:
        # Fallback to pattern matching
        cmd.extend(["*integration*.py"])
    
    return run_command(cmd, "Integration Tests")


def run_rich_output_tests(verbose=False):
    """Run Rich console output tests."""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add Rich output test markers
    cmd.extend(["-m", "rich_output"])
    
    if verbose:
        cmd.append("-v")
    
    # Add Rich output test file
    if Path("test_rich_console_output.py").exists():
        cmd.append("test_rich_console_output.py")
    
    return run_command(cmd, "Rich Console Output Tests")


def run_performance_tests(verbose=False):
    """Run performance tests."""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add performance test markers
    cmd.extend(["-m", "slow"])
    
    if verbose:
        cmd.append("-v")
    
    # Add timeout for performance tests
    cmd.extend(["--timeout=300"])
    
    return run_command(cmd, "Performance Tests")


def run_all_tests(verbose=False, coverage=False, parallel=False):
    """Run all tests."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    if parallel:
        cmd.extend(["-n", "auto"])  # Use all available CPUs
    
    # Add timeout
    cmd.extend(["--timeout=300"])
    
    return run_command(cmd, "All Tests")


def run_specific_test(test_pattern, verbose=False):
    """Run specific test by pattern."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["-k", test_pattern])
    
    return run_command(cmd, f"Tests matching '{test_pattern}'")


def generate_coverage_report():
    """Generate detailed coverage report."""
    print("\nGenerating coverage report...")
    
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-exclude=test_*",
        "--cov-exclude=conftest.py",
        "--cov-exclude=run_tests.py"
    ]
    
    if run_command(cmd, "Coverage Analysis"):
        print("\n📊 Coverage reports generated:")
        print("  - HTML report: htmlcov/index.html")
        print("  - XML report: coverage.xml")
        return True
    
    return False


def clean_test_artifacts():
    """Clean test artifacts and cache files."""
    print("Cleaning test artifacts...")
    
    artifacts = [
        ".pytest_cache",
        "__pycache__",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        "*.pyc"
    ]
    
    for pattern in artifacts:
        if pattern.startswith(".") and Path(pattern).exists():
            if Path(pattern).is_dir():
                import shutil
                shutil.rmtree(pattern)
                print(f"Removed directory: {pattern}")
            else:
                Path(pattern).unlink()
                print(f"Removed file: {pattern}")
        elif "*" in pattern:
            import glob
            for file in glob.glob(pattern, recursive=True):
                try:
                    Path(file).unlink()
                    print(f"Removed file: {file}")
                except OSError:
                    pass
    
    print("✅ Test artifacts cleaned")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Gaming Setup Tool Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all                    # Run all tests
  python run_tests.py --unit --coverage        # Run unit tests with coverage
  python run_tests.py --integration -v         # Run integration tests verbosely
  python run_tests.py --rich-output            # Run Rich console output tests
  python run_tests.py --specific "test_admin"  # Run tests matching pattern
  python run_tests.py --install-deps           # Install test dependencies
  python run_tests.py --clean                  # Clean test artifacts
        """
    )
    
    # Test type options
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--rich-output", action="store_true", help="Run Rich console output tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--specific", metavar="PATTERN", help="Run specific tests matching pattern")
    
    # Options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    # Utility options
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--coverage-only", action="store_true", help="Generate coverage report only")
    
    args = parser.parse_args()
    
    # Handle utility commands first
    if args.install_deps:
        return 0 if install_test_dependencies() else 1
    
    if args.clean:
        clean_test_artifacts()
        return 0
    
    if args.coverage_only:
        return 0 if generate_coverage_report() else 1
    
    # Check if pytest is available
    try:
        subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                      check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest is not installed or not working")
        print("Run: python run_tests.py --install-deps")
        return 1
    
    success = True
    
    # Run tests based on arguments
    if args.all:
        success &= run_all_tests(args.verbose, args.coverage, args.parallel)
    elif args.unit:
        success &= run_unit_tests(args.verbose, args.coverage)
    elif args.integration:
        success &= run_integration_tests(args.verbose)
    elif args.rich_output:
        success &= run_rich_output_tests(args.verbose)
    elif args.performance:
        success &= run_performance_tests(args.verbose)
    elif args.specific:
        success &= run_specific_test(args.specific, args.verbose)
    else:
        # Default: run unit tests
        print("No specific test type specified, running unit tests...")
        success &= run_unit_tests(args.verbose, args.coverage)
    
    # Generate coverage report if requested and not already done
    if args.coverage and not args.unit:
        success &= generate_coverage_report()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())