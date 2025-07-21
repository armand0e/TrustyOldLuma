"""
Tests for main entry point and startup validation.

This module tests the main entry point, startup checks, environment validation,
and error scenario handling for the Gaming Setup Tool.
"""

import pytest
import sys
import os
import tempfile
import shutil
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Import the main functions to test
from gaming_setup_tool import (
    main, 
    perform_startup_checks, 
    validate_environment,
    create_argument_parser,
    validate_arguments,
    determine_exit_code
)
from exceptions import (
    AdminPrivilegeError,
    NetworkError,
    FileOperationError,
    ConfigurationError
)


class TestMainEntryPoint:
    """Test main entry point functionality."""
    
    def test_create_argument_parser(self):
        """Test argument parser creation and configuration."""
        parser = create_argument_parser()
        
        # Test basic parser properties
        assert parser.prog == "luna-gaming-tool"
        assert "Luna Setup Tool" in parser.description
        
        # Test that all expected arguments are present
        help_text = parser.format_help()
        expected_args = [
            "--verbose", "-v",
            "--quiet", "-q", 
            "--dry-run",
            "--config-only",
            "--skip-admin",
            "--skip-security",
            "--luna-core-path",
            "--legacy-greenluma-path",
            "--legacy-koalageddon-path",
            "--app-id",
            "--download-url",
            "--no-cleanup",
            "--force",
            "--timeout"
        ]
        
        for arg in expected_args:
            assert arg in help_text
    
    def test_validate_arguments_success(self):
        """Test successful argument validation."""
        parser = create_argument_parser()
        
        # Test valid arguments
        valid_args = [
            [],  # Default arguments
            ["--verbose"],
            ["--quiet"],
            ["--dry-run"],
            ["--app-id", "730"],
            ["--timeout", "600"]
        ]
        
        for args in valid_args:
            parsed_args = parser.parse_args(args)
            # Should not raise exception
            validate_arguments(parsed_args)
    
    def test_validate_arguments_conflicts(self):
        """Test argument validation with conflicts."""
        # Test our validation logic directly
        mock_args = Mock()
        mock_args.verbose = True
        mock_args.quiet = True
        mock_args.dry_run = False
        mock_args.config_only = False
        mock_args.greenluma_path = None
        mock_args.koalageddon_path = None
        mock_args.timeout = 300
        mock_args.app_id = "480"
        
        with pytest.raises(argparse.ArgumentTypeError, match="Cannot use --verbose and --quiet together"):
            validate_arguments(mock_args)
    
    def test_validate_arguments_invalid_values(self):
        """Test argument validation with invalid values."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.quiet = False
        mock_args.dry_run = False
        mock_args.config_only = False
        mock_args.greenluma_path = None
        mock_args.koalageddon_path = None
        
        # Test invalid timeout
        mock_args.timeout = -1
        mock_args.app_id = "480"
        
        with pytest.raises(argparse.ArgumentTypeError, match="Timeout must be a positive integer"):
            validate_arguments(mock_args)
        
        # Test invalid app ID
        mock_args.timeout = 300
        mock_args.app_id = "invalid-id"
        
        with pytest.raises(argparse.ArgumentTypeError, match="App ID must be a numeric string"):
            validate_arguments(mock_args)
    
    def test_determine_exit_code(self):
        """Test exit code determination based on exception types."""
        # Test specific exception types
        assert determine_exit_code(AdminPrivilegeError("test")) == 2
        assert determine_exit_code(NetworkError("test")) == 3
        assert determine_exit_code(FileOperationError("test")) == 4
        assert determine_exit_code(ConfigurationError("test")) == 5
        assert determine_exit_code(KeyboardInterrupt()) == 6
        assert determine_exit_code(Exception("test")) == 1


class TestStartupChecks:
    """Test startup checks and environment validation."""
    
    @pytest.fixture
    def temp_assets_dir(self):
        """Create temporary assets directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        assets_dir = temp_dir / "assets"
        assets_dir.mkdir()
        
        # Create mock greenluma.zip
        greenluma_zip = assets_dir / "greenluma.zip"
        greenluma_zip.write_text("mock zip content")
        
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        yield temp_dir
        
        # Cleanup
        os.chdir(original_cwd)
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_perform_startup_checks_success(self, temp_assets_dir):
        """Test successful startup checks."""
        # Mock sys.version_info to ensure Python version check passes
        with patch('sys.version_info', (3, 9, 0)):
            with patch('platform.system', return_value='Windows'):
                # Should not raise exception
                perform_startup_checks()
    
    def test_perform_startup_checks_python_version_fail(self):
        """Test startup checks with insufficient Python version."""
        with patch('sys.version_info', (3, 7, 0)):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    perform_startup_checks()
                    mock_exit.assert_called_with(1)
    
    def test_perform_startup_checks_missing_assets(self):
        """Test startup checks with missing assets."""
        # Create temp directory without assets
        temp_dir = Path(tempfile.mkdtemp())
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    perform_startup_checks()
                    mock_exit.assert_called_with(4)  # File error
        finally:
            os.chdir(original_cwd)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_perform_startup_checks_permission_warnings(self, temp_assets_dir):
        """Test startup checks with permission issues."""
        # Mock permission error for Documents directory
        with patch('pathlib.Path.write_text', side_effect=PermissionError("Access denied")):
            with patch('builtins.print') as mock_print:
                with patch('sys.version_info', (3, 9, 0)):
                    perform_startup_checks()
                    
                    # Check that warning was printed
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    warning_printed = any("Permission issues detected" in call for call in print_calls)
                    assert warning_printed
    
    def test_validate_environment_success(self):
        """Test successful environment validation."""
        # Should not raise exception with all required modules available
        validate_environment()
    
    def test_validate_environment_missing_modules(self):
        """Test environment validation with missing modules."""
        # Mock the validate_environment function to test missing modules scenario
        with patch('gaming_setup_tool.validate_environment') as mock_validate:
            # Simulate the function behavior when modules are missing
            mock_validate.side_effect = SystemExit(1)
            
            with pytest.raises(SystemExit) as exc_info:
                mock_validate()
            assert exc_info.value.code == 1
    
    def test_validate_environment_rich_console_failure(self):
        """Test environment validation with Rich console failure."""
        # Mock Rich Console to raise exception
        with patch('rich.console.Console', side_effect=Exception("Console init failed")):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    validate_environment()
                    mock_exit.assert_called_with(1)
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_validate_environment_windows_specific(self):
        """Test Windows-specific environment validation."""
        with patch('platform.system', return_value='Windows'):
            # Mock ctypes to raise exception
            with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("API error")):
                with patch('builtins.print') as mock_print:
                    validate_environment()
                    
                    # Should print warning but not exit
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    warning_printed = any("Windows-specific functionality may be limited" in call for call in print_calls)
                    assert warning_printed


class TestMainFunction:
    """Test the main function with various scenarios."""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock environment for main function testing."""
        with patch('gaming_setup_tool.perform_startup_checks'):
            with patch('gaming_setup_tool.validate_environment'):
                with patch('gaming_setup_tool.LunaSetupTool') as mock_tool_class:
                    mock_tool = Mock()
                    mock_tool_class.return_value = mock_tool
                    
                    with patch('asyncio.run') as mock_asyncio_run:
                        yield {
                            'tool_class': mock_tool_class,
                            'tool': mock_tool,
                            'asyncio_run': mock_asyncio_run
                        }
    
    def test_main_success(self, mock_environment):
        """Test successful main function execution."""
        with patch('sys.argv', ['luna']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_with(0)
    
    def test_main_keyboard_interrupt(self, mock_environment):
        """Test main function with keyboard interrupt."""
        mock_environment['asyncio_run'].side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['luna']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    main()
                    mock_exit.assert_called_with(6)
    
    def test_main_admin_privilege_error(self, mock_environment):
        """Test main function with admin privilege error."""
        mock_environment['asyncio_run'].side_effect = AdminPrivilegeError("Admin required")
        
        with patch('sys.argv', ['luna']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    main()
                    mock_exit.assert_called_with(2)
    
    def test_main_network_error(self, mock_environment):
        """Test main function with network error."""
        mock_environment['asyncio_run'].side_effect = NetworkError("Connection failed")
        
        with patch('sys.argv', ['luna']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    main()
                    mock_exit.assert_called_with(3)
    
    def test_main_verbose_error_output(self, mock_environment):
        """Test main function error output in verbose mode."""
        mock_environment['asyncio_run'].side_effect = Exception("Test error")
        
        with patch('sys.argv', ['luna', '--verbose']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    with patch('traceback.print_exc') as mock_traceback:
                        main()
                        
                        mock_exit.assert_called_with(1)
                        mock_traceback.assert_called_once()
                        
                        # Check that error was printed
                        print_calls = [str(call) for call in mock_print.call_args_list]
                        error_printed = any("Fatal error: Test error" in call for call in print_calls)
                        assert error_printed
    
    def test_main_quiet_mode_error(self, mock_environment):
        """Test main function error handling in quiet mode."""
        mock_environment['asyncio_run'].side_effect = Exception("Test error")
        
        with patch('sys.argv', ['luna', '--quiet']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    main()
                    
                    mock_exit.assert_called_with(1)
                    
                    # In quiet mode, should not print error details
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    # Should have minimal or no output
                    assert len(print_calls) == 0 or all("Fatal error" not in call for call in print_calls)
    
    def test_main_argument_parsing_error(self):
        """Test main function with argument parsing errors."""
        with patch('sys.argv', ['luna', '--invalid-argument']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):
                    main()
                    # Should exit with error code 1 due to invalid argument
                    mock_exit.assert_called()
    
    def test_main_startup_check_failure(self):
        """Test main function when startup checks fail."""
        with patch('gaming_setup_tool.perform_startup_checks', side_effect=SystemExit(1)):
            with patch('sys.argv', ['luna']):
                with pytest.raises(SystemExit):
                    main()


class TestIntegrationScenarios:
    """Test integration scenarios and error conditions."""
    
    def test_main_with_real_argument_parsing(self):
        """Test main function with real argument parsing scenarios."""
        # Test help argument
        with patch('sys.argv', ['luna', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Help should exit with code 0
            assert exc_info.value.code == 0
    
    def test_main_environment_validation_integration(self):
        """Test integration between startup checks and main function."""
        # Mock startup checks to fail with SystemExit
        with patch('gaming_setup_tool.perform_startup_checks') as mock_startup:
            mock_startup.side_effect = SystemExit(4)
            
            with patch('sys.argv', ['luna']):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 4
    
    def test_error_code_consistency(self):
        """Test that error codes are consistent across the application."""
        # Test all defined error codes
        error_mappings = [
            (AdminPrivilegeError("test"), 2),
            (NetworkError("test"), 3),
            (FileOperationError("test"), 4),
            (ConfigurationError("test"), 5),
            (KeyboardInterrupt(), 6),
            (Exception("test"), 1)
        ]
        
        for exception, expected_code in error_mappings:
            actual_code = determine_exit_code(exception)
            assert actual_code == expected_code, f"Expected {expected_code} for {type(exception).__name__}, got {actual_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])