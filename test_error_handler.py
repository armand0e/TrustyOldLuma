"""
Unit tests for the Error Handler module.

Tests error categorization, display functionality, logging, and user guidance features.
"""

import pytest
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from rich.console import Console

from src.error_handler import (
    ErrorHandler, ErrorCategory, ErrorInfo,
    create_permission_error, create_network_error, create_filesystem_error
)


class TestErrorHandler:
    """Test cases for the ErrorHandler class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create a mock console for testing
        self.mock_console = Mock(spec=Console)
        
        # Create temporary log file
        self.temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.temp_log_path = Path(self.temp_log.name)
        self.temp_log.close()
        
        # Create error handler instance
        self.error_handler = ErrorHandler(
            console=self.mock_console,
            log_file=self.temp_log_path
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Close any open file handlers to release the file
        if hasattr(self.error_handler, 'logger'):
            for handler in self.error_handler.logger.handlers[:]:
                handler.close()
                self.error_handler.logger.removeHandler(handler)
        
        # Clean up temporary log file
        if self.temp_log_path.exists():
            try:
                self.temp_log_path.unlink()
            except PermissionError:
                # File might still be in use, skip cleanup
                pass
    
    def test_error_categorization_permission_errors(self):
        """Test categorization of permission-related errors."""
        # Test PermissionError
        perm_error = PermissionError("Access denied")
        category = self.error_handler.categorize_error(perm_error)
        assert category == ErrorCategory.PERMISSION
        
        # Test OSError with permission message
        os_error = OSError("Operation not permitted")
        category = self.error_handler.categorize_error(os_error)
        assert category == ErrorCategory.PERMISSION
    
    def test_error_categorization_network_errors(self):
        """Test categorization of network-related errors."""
        # Test with network context
        connection_error = ConnectionError("Network unreachable")
        category = self.error_handler.categorize_error(connection_error, "download")
        assert category == ErrorCategory.NETWORK
        
        # Test timeout error
        timeout_error = TimeoutError("Connection timed out")
        category = self.error_handler.categorize_error(timeout_error)
        assert category == ErrorCategory.NETWORK
    
    def test_error_categorization_filesystem_errors(self):
        """Test categorization of filesystem-related errors."""
        # Test FileNotFoundError
        file_error = FileNotFoundError("No such file or directory")
        category = self.error_handler.categorize_error(file_error)
        assert category == ErrorCategory.FILESYSTEM
        
        # Test directory error
        dir_error = IsADirectoryError("Is a directory")
        category = self.error_handler.categorize_error(dir_error)
        assert category == ErrorCategory.FILESYSTEM
    
    def test_error_categorization_configuration_errors(self):
        """Test categorization of configuration-related errors."""
        # Test ValueError in config context
        value_error = ValueError("Invalid configuration value")
        category = self.error_handler.categorize_error(value_error, "config update")
        assert category == ErrorCategory.CONFIGURATION
        
        # Test JSON decode error
        json_error = ValueError("Invalid JSON format")
        category = self.error_handler.categorize_error(json_error)
        assert category == ErrorCategory.CONFIGURATION  # ValueError with json in message gets categorized as CONFIGURATION
    
    def test_error_categorization_admin_errors(self):
        """Test categorization of admin-related errors."""
        # Test with admin context
        runtime_error = RuntimeError("Elevation failed")
        category = self.error_handler.categorize_error(runtime_error, "admin elevation")
        assert category == ErrorCategory.ADMIN
        
        # Test with privilege message
        privilege_error = OSError("Insufficient privileges")
        category = self.error_handler.categorize_error(privilege_error)
        assert category == ErrorCategory.ADMIN
    
    def test_error_categorization_unknown_errors(self):
        """Test categorization of unknown errors."""
        # Test generic exception
        generic_error = Exception("Something went wrong")
        category = self.error_handler.categorize_error(generic_error)
        assert category == ErrorCategory.UNKNOWN
    
    def test_handle_error_basic(self):
        """Test basic error handling functionality."""
        test_exception = ValueError("Test error message")
        
        error_info = self.error_handler.handle_error(
            test_exception,
            context="test context"
        )
        
        # Verify error info
        assert error_info.message == "Test error message"
        assert error_info.details == "test context"
        assert error_info.category in [ErrorCategory.CONFIGURATION, ErrorCategory.UNKNOWN]
        assert len(error_info.suggestions) > 0
        
        # Verify error was stored in history
        assert len(self.error_handler.error_history) == 1
        assert self.error_handler.error_history[0] == error_info
        
        # Verify display was called
        self.mock_console.print.assert_called()
    
    def test_handle_error_with_custom_suggestions(self):
        """Test error handling with custom suggestions."""
        test_exception = RuntimeError("Custom error")
        custom_suggestions = ["Try this", "Or try that"]
        
        error_info = self.error_handler.handle_error(
            test_exception,
            custom_suggestions=custom_suggestions
        )
        
        assert error_info.suggestions == custom_suggestions
    
    def test_handle_error_with_traceback(self):
        """Test error handling with traceback information."""
        test_exception = ValueError("Error with traceback")
        
        error_info = self.error_handler.handle_error(
            test_exception,
            show_traceback=True
        )
        
        assert error_info.traceback_info is not None
        assert "ValueError" in error_info.traceback_info
    
    def test_display_error(self):
        """Test error display functionality."""
        error_info = ErrorInfo(
            category=ErrorCategory.PERMISSION,
            message="Test permission error",
            details="Test context",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )
        
        self.error_handler.display_error(error_info)
        
        # Verify console.print was called multiple times (for spacing and panel)
        assert self.mock_console.print.call_count >= 3
    
    def test_display_warning(self):
        """Test warning display functionality."""
        self.error_handler.display_warning(
            "Test warning message",
            suggestions=["Warning suggestion"]
        )
        
        # Verify console.print was called for warning display
        assert self.mock_console.print.call_count >= 3
    
    def test_display_critical_error(self):
        """Test critical error display functionality."""
        self.error_handler.display_critical_error(
            "Critical system failure",
            suggestions=["Critical suggestion"]
        )
        
        # Verify console.print was called for critical error display
        assert self.mock_console.print.call_count >= 3
    
    def test_error_logging(self):
        """Test error logging functionality."""
        test_exception = PermissionError("Permission denied")
        
        self.error_handler.handle_error(test_exception, context="test logging")
        
        # Check that log file was created and contains error
        assert self.temp_log_path.exists()
        
        with open(self.temp_log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
            assert "Permission denied" in log_content
            assert "test logging" in log_content
    
    def test_get_error_summary_empty(self):
        """Test error summary with no errors."""
        summary = self.error_handler.get_error_summary()
        
        assert summary["total_errors"] == 0
        assert summary["categories"] == {}
        assert summary["recent_errors"] == []
    
    def test_get_error_summary_with_errors(self):
        """Test error summary with multiple errors."""
        # Add some test errors
        self.error_handler.handle_error(PermissionError("Error 1"))
        self.error_handler.handle_error(ConnectionError("Error 2"))
        self.error_handler.handle_error(PermissionError("Error 3"))
        
        summary = self.error_handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert "Permission Error" in summary["categories"]
        assert "Network Error" in summary["categories"]
        assert len(summary["recent_errors"]) == 3
    
    def test_display_error_summary(self):
        """Test error summary display."""
        # Add a test error
        self.error_handler.handle_error(ValueError("Test error"))
        
        # Reset mock to clear previous calls
        self.mock_console.reset_mock()
        
        self.error_handler.display_error_summary()
        
        # Verify console.print was called for summary display
        assert self.mock_console.print.call_count >= 3
    
    def test_clear_error_history(self):
        """Test clearing error history."""
        # Add some errors
        self.error_handler.handle_error(ValueError("Error 1"))
        self.error_handler.handle_error(RuntimeError("Error 2"))
        
        assert len(self.error_handler.error_history) == 2
        
        # Clear history
        self.error_handler.clear_error_history()
        
        assert len(self.error_handler.error_history) == 0
    
    def test_export_error_log(self):
        """Test error log export functionality."""
        # Add some test errors
        self.error_handler.handle_error(PermissionError("Export test error"))
        
        # Export to temporary file
        export_path = Path(tempfile.mktemp(suffix='.log'))
        
        try:
            result_path = self.error_handler.export_error_log(export_path)
            
            assert result_path == export_path
            assert export_path.exists()
            
            # Check export content
            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Setup Error Report" in content
                assert "Export test error" in content
                assert "Permission Error" in content
        
        finally:
            # Clean up export file
            if export_path.exists():
                export_path.unlink()


class TestConvenienceFunctions:
    """Test cases for convenience error creation functions."""
    
    def test_create_permission_error(self):
        """Test permission error creation function."""
        error_info = create_permission_error("Access denied", "/test/path")
        
        assert error_info.category == ErrorCategory.PERMISSION
        assert error_info.message == "Access denied"
        assert "Path: /test/path" in error_info.details
        assert len(error_info.suggestions) > 0
        assert any("Administrator" in suggestion for suggestion in error_info.suggestions)
    
    def test_create_network_error(self):
        """Test network error creation function."""
        error_info = create_network_error("Connection failed", "https://example.com")
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.message == "Connection failed"
        assert "URL: https://example.com" in error_info.details
        assert len(error_info.suggestions) > 0
        assert any("internet connection" in suggestion for suggestion in error_info.suggestions)
    
    def test_create_filesystem_error(self):
        """Test filesystem error creation function."""
        error_info = create_filesystem_error("File not found", "/missing/file")
        
        assert error_info.category == ErrorCategory.FILESYSTEM
        assert error_info.message == "File not found"
        assert "Path: /missing/file" in error_info.details
        assert len(error_info.suggestions) > 0
        assert any("disk space" in suggestion for suggestion in error_info.suggestions)


class TestErrorHandlerIntegration:
    """Integration tests for error handler with real Rich console."""
    
    def test_real_console_display(self):
        """Test error display with real Rich console."""
        # Create a real console with string output
        string_output = StringIO()
        real_console = Console(file=string_output, width=80)
        
        # Create error handler with real console
        error_handler = ErrorHandler(console=real_console)
        
        # Handle an error
        test_exception = PermissionError("Real console test")
        error_handler.handle_error(test_exception, context="integration test")
        
        # Check output
        output = string_output.getvalue()
        assert "Permission Error" in output
        assert "Real console test" in output
        assert "Troubleshooting Suggestions" in output
    
    def test_logging_integration(self):
        """Test logging integration with real file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_log:
            temp_log_path = Path(temp_log.name)
        
        try:
            # Create error handler with real logging
            error_handler = ErrorHandler(log_file=temp_log_path)
            
            # Handle multiple errors
            error_handler.handle_error(PermissionError("Log test 1"))
            error_handler.handle_error(ConnectionError("Log test 2"))
            
            # Verify log file content
            assert temp_log_path.exists()
            
            with open(temp_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
                assert "Log test 1" in log_content
                assert "Log test 2" in log_content
                assert "Permission Error" in log_content
                assert "Network Error" in log_content
        
        finally:
            # Close handlers to release file
            if 'error_handler' in locals():
                for handler in error_handler.logger.handlers[:]:
                    handler.close()
                    error_handler.logger.removeHandler(handler)
            
            # Clean up
            if temp_log_path.exists():
                try:
                    temp_log_path.unlink()
                except PermissionError:
                    pass  # File might still be in use


if __name__ == "__main__":
    pytest.main([__file__])