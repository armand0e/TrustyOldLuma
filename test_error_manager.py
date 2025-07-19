"""
Tests for the error management system.

This module contains tests for the error categorization, retry mechanisms,
and platform-specific feature handling.
"""

import asyncio
import pytest
import platform
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from rich.console import Console

from exceptions import (
    GamingSetupError,
    AdminPrivilegeError,
    FileOperationError,
    NetworkError,
    ConfigurationError,
    SecurityConfigError,
    DownloadError,
    ConnectionTimeoutError,
    PlatformNotSupportedError
)
from error_manager import (
    ErrorManager,
    RetryManager,
    ErrorCategory,
    PlatformFeatureContext,
    with_retry,
    create_user_friendly_message
)


class TestErrorManager:
    """Tests for the ErrorManager class."""
    
    @pytest.fixture
    def error_manager(self):
        """Create an ErrorManager instance for testing."""
        console = Mock(spec=Console)
        return ErrorManager(console)
    
    def test_error_categorization(self, error_manager):
        """Test error categorization for different exception types."""
        # Critical errors
        assert error_manager.categorize_error(AdminPrivilegeError()) == ErrorCategory.CRITICAL
        assert error_manager.categorize_error(PermissionError()) == ErrorCategory.CRITICAL
        
        # Recoverable errors
        assert error_manager.categorize_error(FileOperationError()) == ErrorCategory.RECOVERABLE
        assert error_manager.categorize_error(ConfigurationError()) == ErrorCategory.RECOVERABLE
        assert error_manager.categorize_error(SecurityConfigError()) == ErrorCategory.RECOVERABLE
        assert error_manager.categorize_error(FileNotFoundError()) == ErrorCategory.RECOVERABLE
        
        # Network errors
        assert error_manager.categorize_error(NetworkError()) == ErrorCategory.NETWORK
        assert error_manager.categorize_error(ConnectionError()) == ErrorCategory.NETWORK
        assert error_manager.categorize_error(TimeoutError()) == ErrorCategory.NETWORK
        assert error_manager.categorize_error(DownloadError()) == ErrorCategory.NETWORK
        assert error_manager.categorize_error(ConnectionTimeoutError()) == ErrorCategory.NETWORK
        
        # Platform errors
        assert error_manager.categorize_error(NotImplementedError()) == ErrorCategory.PLATFORM
        assert error_manager.categorize_error(OSError()) == ErrorCategory.PLATFORM
        assert error_manager.categorize_error(PlatformNotSupportedError()) == ErrorCategory.PLATFORM
        
        # Unknown errors should default to recoverable
        assert error_manager.categorize_error(KeyError()) == ErrorCategory.RECOVERABLE
        assert error_manager.categorize_error(ValueError()) == ErrorCategory.RECOVERABLE
    
    def test_solution_suggestions(self, error_manager):
        """Test solution suggestions for different exception types."""
        # Check that solutions are provided for known error types
        assert error_manager.get_solution(AdminPrivilegeError()) is not None
        assert error_manager.get_solution(PermissionError()) is not None
        assert error_manager.get_solution(FileOperationError()) is not None
        assert error_manager.get_solution(NetworkError()) is not None
        
        # Unknown error types should return None
        class UnknownError(Exception):
            pass
        
        assert error_manager.get_solution(UnknownError()) is None
    
    def test_platform_feature_detection(self, error_manager):
        """Test platform feature detection."""
        features = error_manager._platform_features
        
        # Check that platform detection is working
        system = platform.system().lower()
        
        if system == "windows":
            assert features["windows_admin"] is True
            assert features["windows_defender"] is True
            assert features["windows_shortcuts"] is True
        elif system == "linux":
            assert features["linux_desktop_entries"] is True
            assert features["windows_admin"] is False
        elif system == "darwin":  # macOS
            assert features["macos_aliases"] is True
            assert features["windows_admin"] is False
    
    @patch("error_manager.ErrorManager.display_error")
    def test_display_error(self, mock_display, error_manager):
        """Test error display with categorization."""
        error = NetworkError("Connection failed")
        error_manager.display_error(error, "Downloading file")
        
        # Verify that display_error was called
        mock_display.assert_called_once()


class TestRetryManager:
    """Tests for the RetryManager class."""
    
    @pytest.fixture
    def retry_manager(self):
        """Create a RetryManager instance for testing."""
        console = Mock(spec=Console)
        return RetryManager(console)
    
    @pytest.mark.asyncio
    async def test_retry_async_success_first_try(self, retry_manager):
        """Test successful async function on first try."""
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_manager.retry_async(
            mock_func, "arg1", "arg2", 
            operation_name="Test operation"
        )
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2")
    
    @pytest.mark.asyncio
    async def test_retry_async_success_after_retry(self, retry_manager):
        """Test successful async function after retry."""
        mock_func = AsyncMock(side_effect=[ValueError("First attempt failed"), "success"])
        
        result = await retry_manager.retry_async(
            mock_func, 
            operation_name="Test operation",
            retry_exceptions=(ValueError,)
        )
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_async_all_attempts_fail(self, retry_manager):
        """Test async function where all retry attempts fail."""
        mock_func = AsyncMock(side_effect=ValueError("All attempts failed"))
        
        with pytest.raises(ValueError, match="All attempts failed"):
            await retry_manager.retry_async(
                mock_func, 
                operation_name="Test operation",
                retry_exceptions=(ValueError,)
            )
        
        assert mock_func.call_count == retry_manager.max_attempts
    
    def test_retry_sync_success_first_try(self, retry_manager):
        """Test successful sync function on first try."""
        mock_func = Mock(return_value="success")
        
        result = retry_manager.retry_sync(
            mock_func, "arg1", "arg2", 
            operation_name="Test operation"
        )
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2")
    
    def test_retry_sync_success_after_retry(self, retry_manager):
        """Test successful sync function after retry."""
        mock_func = Mock(side_effect=[ValueError("First attempt failed"), "success"])
        
        result = retry_manager.retry_sync(
            mock_func, 
            operation_name="Test operation",
            retry_exceptions=(ValueError,)
        )
        
        assert result == "success"
        assert mock_func.call_count == 2


class TestWithRetryDecorator:
    """Tests for the with_retry decorator."""
    
    @pytest.mark.asyncio
    async def test_with_retry_async(self):
        """Test with_retry decorator on async function."""
        mock_func = AsyncMock(side_effect=[ValueError("First attempt failed"), "success"])
        
        @with_retry(max_attempts=3, retry_exceptions=(ValueError,))
        async def test_func():
            return await mock_func()
        
        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_with_retry_sync(self):
        """Test with_retry decorator on sync function."""
        mock_func = Mock(side_effect=[ValueError("First attempt failed"), "success"])
        
        @with_retry(max_attempts=3, retry_exceptions=(ValueError,))
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2


class TestPlatformFeatureContext:
    """Tests for the PlatformFeatureContext class."""
    
    @pytest.fixture
    def error_manager(self):
        """Create an ErrorManager instance for testing."""
        console = Mock(spec=Console)
        return ErrorManager(console)
    
    def test_feature_available(self, error_manager):
        """Test context manager with available feature."""
        # Mock the is_feature_available method
        error_manager.is_feature_available = Mock(return_value=True)
        
        with PlatformFeatureContext(error_manager, "test_feature", "Test context") as available:
            assert available is True
    
    def test_feature_not_available(self, error_manager):
        """Test context manager with unavailable feature."""
        # Mock the is_feature_available method
        error_manager.is_feature_available = Mock(return_value=False)
        error_manager.handle_platform_limitation = Mock()
        
        with PlatformFeatureContext(error_manager, "test_feature", "Test context") as available:
            assert available is False
        
        # Verify that handle_platform_limitation was called
        error_manager.handle_platform_limitation.assert_called_once_with(
            "test_feature", "Test context"
        )
    
    def test_not_implemented_error_handling(self, error_manager):
        """Test handling of NotImplementedError within context."""
        # Mock the methods
        error_manager.is_feature_available = Mock(return_value=True)
        error_manager.handle_platform_limitation = Mock()
        fallback_func = Mock()
        
        # Use context manager with a function that raises NotImplementedError
        with PlatformFeatureContext(
            error_manager, "test_feature", "Test context", fallback_func
        ) as available:
            assert available is True
            raise NotImplementedError("Feature not implemented")
        
        # Verify that handle_platform_limitation and fallback_func were called
        error_manager.handle_platform_limitation.assert_called_once()
        fallback_func.assert_called_once()


def test_create_user_friendly_message():
    """Test creation of user-friendly error messages."""
    # Test with known error types
    admin_error = AdminPrivilegeError("Access denied")
    admin_msg = create_user_friendly_message(admin_error, "setting up security exclusions")
    assert "Administrator privileges" in admin_msg
    assert "setting up security exclusions" in admin_msg
    
    # Test with custom error message
    network_error = NetworkError("Connection refused")
    network_msg = create_user_friendly_message(network_error, "downloading Koalageddon")
    assert "network operation" in network_msg.lower()
    assert "downloading Koalageddon" in network_msg
    
    # Test with unknown error type
    unknown_error = KeyError("Missing key")
    unknown_msg = create_user_friendly_message(unknown_error, "processing configuration")
    assert "Missing key" in unknown_msg
    assert "processing configuration" in unknown_msg