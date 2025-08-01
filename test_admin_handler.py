"""Unit tests for AdminHandler module."""

import pytest
import ctypes
import subprocess
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.admin_handler import AdminHandler
from src.data_models import OperationResult


class TestAdminHandler:
    """Test cases for AdminHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.admin_handler = AdminHandler()
    
    def test_init(self):
        """Test AdminHandler initialization."""
        handler = AdminHandler()
        assert handler is not None
    
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_is_admin_true(self, mock_is_admin):
        """Test is_admin returns True when user has admin privileges."""
        mock_is_admin.return_value = True
        
        result = self.admin_handler.is_admin()
        
        assert result is True
        mock_is_admin.assert_called_once()
    
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_is_admin_false(self, mock_is_admin):
        """Test is_admin returns False when user doesn't have admin privileges."""
        mock_is_admin.return_value = False
        
        result = self.admin_handler.is_admin()
        
        assert result is False
        mock_is_admin.assert_called_once()
    
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_is_admin_exception(self, mock_is_admin):
        """Test is_admin returns False when exception occurs."""
        mock_is_admin.side_effect = Exception("API call failed")
        
        result = self.admin_handler.is_admin()
        
        assert result is False
        mock_is_admin.assert_called_once()
    
    @patch('subprocess.run')
    @patch('sys.executable', 'python.exe')
    @patch('sys.argv', ['setup.py', '--test'])
    def test_request_elevation_success(self, mock_run):
        """Test successful elevation request."""
        mock_run.return_value = Mock(returncode=0, stderr="")
        
        result = self.admin_handler.request_elevation()
        
        assert result.success is True
        assert "Successfully requested elevation" in result.message
        mock_run.assert_called_once()
        
        # Verify PowerShell command structure
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "powershell.exe"
        assert call_args[1] == "-Command"
        assert "Start-Process" in call_args[2]
        assert "-Verb RunAs" in call_args[2]
    
    @patch('subprocess.run')
    def test_request_elevation_failure(self, mock_run):
        """Test failed elevation request."""
        mock_run.return_value = Mock(returncode=1, stderr="Access denied")
        
        result = self.admin_handler.request_elevation()
        
        assert result.success is False
        assert "Failed to request elevation" in result.message
        assert "Access denied" in result.details
        assert len(result.suggestions) > 0
    
    @patch('subprocess.run')
    def test_request_elevation_timeout(self, mock_run):
        """Test elevation request timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("powershell.exe", 30)
        
        result = self.admin_handler.request_elevation()
        
        assert result.success is False
        assert "timed out" in result.message
        assert "30 seconds" in result.details
        assert len(result.suggestions) > 0
    
    @patch('subprocess.run')
    def test_request_elevation_exception(self, mock_run):
        """Test elevation request with unexpected exception."""
        mock_run.side_effect = Exception("Unexpected error")
        
        result = self.admin_handler.request_elevation()
        
        assert result.success is False
        assert "Failed to request elevation" in result.message
        assert "Unexpected error" in result.details
        assert len(result.suggestions) > 0
    
    @patch('subprocess.run')
    def test_request_elevation_custom_script(self, mock_run):
        """Test elevation request with custom script path."""
        mock_run.return_value = Mock(returncode=0, stderr="")
        custom_script = "custom_setup.py"
        
        result = self.admin_handler.request_elevation(custom_script)
        
        assert result.success is True
        mock_run.assert_called_once()
        
        # Verify custom script path is used
        call_args = mock_run.call_args[0][0]
        assert custom_script in call_args[2]
    
    @patch.object(AdminHandler, 'is_admin')
    def test_add_security_exclusions_no_admin(self, mock_is_admin):
        """Test add_security_exclusions without admin privileges."""
        mock_is_admin.return_value = False
        
        result = self.admin_handler.add_security_exclusions(["/test/path"])
        
        assert result.success is False
        assert "Administrator privileges required" in result.message
        assert len(result.suggestions) > 0
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('subprocess.run')
    def test_add_security_exclusions_success(self, mock_run, mock_is_admin):
        """Test successful security exclusions addition."""
        mock_is_admin.return_value = True
        mock_run.return_value = Mock(returncode=0, stderr="")
        
        paths = ["/test/path1", "/test/path2"]
        result = self.admin_handler.add_security_exclusions(paths)
        
        assert result.success is True
        assert "Successfully added 2 security exclusions" in result.message
        assert mock_run.call_count == 2
        
        # Verify PowerShell commands
        for call in mock_run.call_args_list:
            call_args = call[0][0]
            assert call_args[0] == "powershell.exe"
            assert "Add-MpPreference" in call_args[2]
            assert "-ExclusionPath" in call_args[2]
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('subprocess.run')
    def test_add_security_exclusions_partial_failure(self, mock_run, mock_is_admin):
        """Test partial failure in security exclusions addition."""
        mock_is_admin.return_value = True
        
        # First call succeeds, second fails
        mock_run.side_effect = [
            Mock(returncode=0, stderr=""),
            Mock(returncode=1, stderr="Access denied")
        ]
        
        paths = ["/test/path1", "/test/path2"]
        result = self.admin_handler.add_security_exclusions(paths)
        
        assert result.success is False
        assert "Partially successful: 1/2" in result.message
        assert "/test/path2" in result.details
        assert len(result.suggestions) > 0
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('subprocess.run')
    def test_add_security_exclusions_all_fail(self, mock_run, mock_is_admin):
        """Test complete failure in security exclusions addition."""
        mock_is_admin.return_value = True
        mock_run.return_value = Mock(returncode=1, stderr="Command failed")
        
        paths = ["/test/path1", "/test/path2"]
        result = self.admin_handler.add_security_exclusions(paths)
        
        assert result.success is False
        assert "Failed to add any security exclusions" in result.message
        assert "Command failed" in result.details
        assert len(result.suggestions) > 0
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('subprocess.run')
    def test_add_security_exclusions_timeout(self, mock_run, mock_is_admin):
        """Test timeout in security exclusions addition."""
        mock_is_admin.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("powershell.exe", 10)
        
        result = self.admin_handler.add_security_exclusions(["/test/path"])
        
        assert result.success is False
        assert "Failed to add any security exclusions" in result.message
        assert "Command timed out" in result.details
    
    @patch.object(AdminHandler, 'is_admin')
    def test_create_directories_no_admin(self, mock_is_admin):
        """Test create_directories_as_admin without admin privileges."""
        mock_is_admin.return_value = False
        
        result = self.admin_handler.create_directories_as_admin(["/test/path"])
        
        assert result.success is False
        assert "Administrator privileges required" in result.message
        assert len(result.suggestions) > 0
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    def test_create_directories_success(self, mock_is_dir, mock_exists, mock_mkdir, mock_is_admin):
        """Test successful directory creation."""
        mock_is_admin.return_value = True
        
        # Both directories don't exist initially
        mock_exists.return_value = False
        mock_is_dir.return_value = True
        
        paths = ["/test/path1", "/test/path2"]
        result = self.admin_handler.create_directories_as_admin(paths)
        
        assert result.success is True
        assert "Successfully created 2 directories" in result.message
        assert mock_mkdir.call_count == 2
        
        # Verify mkdir was called with correct parameters
        for call in mock_mkdir.call_args_list:
            assert call[1]['parents'] is True
            assert call[1]['exist_ok'] is True
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    def test_create_directories_already_exists(self, mock_is_dir, mock_exists, mock_is_admin):
        """Test directory creation when directories already exist."""
        mock_is_admin.return_value = True
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        paths = ["/test/existing_path"]
        result = self.admin_handler.create_directories_as_admin(paths)
        
        assert result.success is True
        assert "Successfully created 1 directories" in result.message
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    def test_create_directories_path_is_file(self, mock_is_dir, mock_exists, mock_is_admin):
        """Test directory creation when path exists but is a file."""
        mock_is_admin.return_value = True
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        
        paths = ["/test/file_path"]
        result = self.admin_handler.create_directories_as_admin(paths)
        
        assert result.success is False
        assert "Failed to create any directories" in result.message
        assert "not a directory" in result.details
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_create_directories_permission_error(self, mock_exists, mock_mkdir, mock_is_admin):
        """Test directory creation with permission error."""
        mock_is_admin.return_value = True
        mock_exists.return_value = False
        mock_mkdir.side_effect = PermissionError("Access denied")
        
        paths = ["/test/protected_path"]
        result = self.admin_handler.create_directories_as_admin(paths)
        
        assert result.success is False
        assert "Failed to create any directories" in result.message
        assert "Permission denied" in result.details
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_create_directories_os_error(self, mock_exists, mock_mkdir, mock_is_admin):
        """Test directory creation with OS error."""
        mock_is_admin.return_value = True
        mock_exists.return_value = False
        mock_mkdir.side_effect = OSError("Disk full")
        
        paths = ["/test/path"]
        result = self.admin_handler.create_directories_as_admin(paths)
        
        assert result.success is False
        assert "Failed to create any directories" in result.message
        assert "OS error" in result.details
    
    @patch.object(AdminHandler, 'is_admin')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_create_directories_partial_success(self, mock_exists, mock_mkdir, mock_is_admin):
        """Test partial success in directory creation."""
        mock_is_admin.return_value = True
        
        # First directory succeeds, second fails
        mock_exists.return_value = False  # Both directories don't exist
        mock_mkdir.side_effect = [None, PermissionError("Access denied")]
        
        paths = ["/test/path1", "/test/path2"]
        result = self.admin_handler.create_directories_as_admin(paths)
        
        assert result.success is False
        assert "Partially successful: 1/2" in result.message
        assert "path2" in result.details
    
    @patch('os.environ.get')
    def test_get_common_exclusion_paths(self, mock_env_get):
        """Test getting common exclusion paths."""
        mock_env_get.side_effect = lambda key, default='': {
            'USERPROFILE': 'C:\\Users\\TestUser',
            'LOCALAPPDATA': 'C:\\Users\\TestUser\\AppData\\Local'
        }.get(key, default)
        
        paths = self.admin_handler.get_common_exclusion_paths()
        
        assert len(paths) == 3
        assert 'C:\\Users\\TestUser\\Documents\\GreenLuma' in paths
        assert 'C:\\Users\\TestUser\\AppData\\Local\\Programs\\Koalageddon' in paths
        assert 'C:\\Users\\TestUser\\Desktop\\GreenLuma' in paths
    
    @patch('os.environ.get')
    def test_get_common_admin_directories(self, mock_env_get):
        """Test getting common admin directories."""
        mock_env_get.side_effect = lambda key, default='': {
            'USERPROFILE': 'C:\\Users\\TestUser',
            'LOCALAPPDATA': 'C:\\Users\\TestUser\\AppData\\Local'
        }.get(key, default)
        
        paths = self.admin_handler.get_common_admin_directories()
        
        assert len(paths) == 4
        assert 'C:\\Users\\TestUser\\Documents\\GreenLuma' in paths
        assert 'C:\\Users\\TestUser\\Documents\\GreenLuma\\AppList' in paths
        assert 'C:\\Users\\TestUser\\AppData\\Local\\Programs' in paths
        assert 'C:\\Users\\TestUser\\AppData\\Local\\Programs\\Koalageddon' in paths


class TestOperationResult:
    """Test cases for OperationResult dataclass."""
    
    def test_operation_result_basic(self):
        """Test basic OperationResult creation."""
        result = OperationResult(success=True, message="Test message")
        
        assert result.success is True
        assert result.message == "Test message"
        assert result.details is None
        assert result.suggestions == []
    
    def test_operation_result_with_details(self):
        """Test OperationResult with details."""
        result = OperationResult(
            success=False,
            message="Test message",
            details="Test details"
        )
        
        assert result.success is False
        assert result.message == "Test message"
        assert result.details == "Test details"
        assert result.suggestions == []
    
    def test_operation_result_with_suggestions(self):
        """Test OperationResult with suggestions."""
        suggestions = ["Suggestion 1", "Suggestion 2"]
        result = OperationResult(
            success=False,
            message="Test message",
            suggestions=suggestions
        )
        
        assert result.success is False
        assert result.message == "Test message"
        assert result.suggestions == suggestions
    
    def test_operation_result_post_init(self):
        """Test OperationResult __post_init__ method."""
        result = OperationResult(success=True, message="Test", suggestions=None)
        
        # __post_init__ should set suggestions to empty list if None
        assert result.suggestions == []


if __name__ == "__main__":
    pytest.main([__file__])