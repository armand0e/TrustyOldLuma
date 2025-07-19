"""
Unit tests for the AdminPrivilegeManager class.

Tests cover Windows API integration, privilege detection, elevation functionality,
and cross-platform graceful degradation.
"""

import ctypes
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

import pytest
from rich.console import Console

from admin_manager import AdminPrivilegeManager
from exceptions import GamingSetupError


class TestAdminPrivilegeManager(unittest.TestCase):
    """Test cases for AdminPrivilegeManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console(file=StringIO(), width=80)
        self.manager = AdminPrivilegeManager(console=self.console)
    
    def test_init_with_console(self):
        """Test initialization with provided console."""
        manager = AdminPrivilegeManager(console=self.console)
        self.assertEqual(manager.console, self.console)
        self.assertEqual(manager._is_windows, os.name == 'nt')
    
    def test_init_without_console(self):
        """Test initialization without provided console."""
        manager = AdminPrivilegeManager()
        self.assertIsInstance(manager.console, Console)
        self.assertEqual(manager._is_windows, os.name == 'nt')
    
    @patch('os.name', 'nt')
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_is_admin_windows_true(self, mock_is_admin):
        """Test admin detection on Windows when user is admin."""
        mock_is_admin.return_value = 1
        self.assertTrue(AdminPrivilegeManager.is_admin())
        mock_is_admin.assert_called_once()
    
    @patch('os.name', 'nt')
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_is_admin_windows_false(self, mock_is_admin):
        """Test admin detection on Windows when user is not admin."""
        mock_is_admin.return_value = 0
        self.assertFalse(AdminPrivilegeManager.is_admin())
        mock_is_admin.assert_called_once()
    
    @patch('os.name', 'nt')
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    def test_is_admin_windows_exception(self, mock_is_admin):
        """Test admin detection on Windows when API call fails."""
        mock_is_admin.side_effect = Exception("API Error")
        self.assertFalse(AdminPrivilegeManager.is_admin())
    
    @patch('os.name', 'posix')
    def test_is_admin_unix_root(self):
        """Test admin detection on Unix when running as root."""
        with patch('os.geteuid', return_value=0, create=True):
            self.assertTrue(AdminPrivilegeManager.is_admin())
    
    @patch('os.name', 'posix')
    def test_is_admin_unix_user(self):
        """Test admin detection on Unix when running as regular user."""
        with patch('os.geteuid', return_value=1000, create=True):
            self.assertFalse(AdminPrivilegeManager.is_admin())
    
    @patch('os.name', 'nt')
    @patch('sys.argv', ['script.py', '--verbose'])
    @patch('sys.executable', 'python.exe')
    @patch('ctypes.windll.shell32.ShellExecuteW')
    def test_elevate_privileges_windows_success(self, mock_shell_execute):
        """Test privilege elevation on Windows when successful."""
        mock_shell_execute.return_value = 42  # Success
        result = AdminPrivilegeManager.elevate_privileges()
        
        self.assertTrue(result)
        mock_shell_execute.assert_called_once_with(
            None,
            "runas",
            "python.exe",
            '"script.py" --verbose',
            None,
            1
        )
    
    @patch('os.name', 'nt')
    @patch('ctypes.windll.shell32.ShellExecuteW')
    def test_elevate_privileges_windows_failure(self, mock_shell_execute):
        """Test privilege elevation on Windows when it fails."""
        mock_shell_execute.side_effect = Exception("Elevation failed")
        result = AdminPrivilegeManager.elevate_privileges()
        
        self.assertFalse(result)
    
    @patch('os.name', 'posix')
    def test_elevate_privileges_unix(self):
        """Test privilege elevation on Unix systems."""
        result = AdminPrivilegeManager.elevate_privileges()
        self.assertFalse(result)
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    def test_ensure_admin_privileges_already_admin(self, mock_is_admin):
        """Test ensure_admin_privileges when already admin."""
        mock_is_admin.return_value = True
        
        # Should not raise any exception
        self.manager.ensure_admin_privileges()
        mock_is_admin.assert_called_once()
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    @patch('os.name', 'nt')
    def test_ensure_admin_privileges_windows_elevation_accepted(self, mock_is_admin):
        """Test ensure_admin_privileges on Windows when user accepts elevation."""
        mock_is_admin.return_value = False
        
        with patch.object(self.manager, '_handle_windows_privilege_elevation') as mock_handle:
            self.manager.ensure_admin_privileges()
            mock_handle.assert_called_once()
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    def test_ensure_admin_privileges_non_windows(self, mock_is_admin):
        """Test ensure_admin_privileges on non-Windows systems."""
        mock_is_admin.return_value = False
        
        # Create a manager with non-Windows platform
        with patch('os.name', 'posix'):
            manager = AdminPrivilegeManager(console=self.console)
            with patch.object(manager, '_handle_non_windows_privileges') as mock_handle:
                manager.ensure_admin_privileges()
                mock_handle.assert_called_once()
    
    @patch.object(AdminPrivilegeManager, 'elevate_privileges')
    def test_handle_windows_privilege_elevation_yes_success(self, mock_elevate):
        """Test Windows privilege elevation when user says yes and elevation succeeds."""
        mock_elevate.return_value = True
        
        with patch.object(self.manager.console, 'input', side_effect=['y', 'y']):
            with self.assertRaises(GamingSetupError) as context:
                self.manager._handle_windows_privilege_elevation()
            
            self.assertIn("Failed to restart with administrator privileges", str(context.exception))
    
    @patch.object(AdminPrivilegeManager, 'elevate_privileges')
    def test_handle_windows_privilege_elevation_yes_failure(self, mock_elevate):
        """Test Windows privilege elevation when user says yes but elevation fails."""
        mock_elevate.return_value = False
        
        with patch.object(self.manager.console, 'input', return_value='y'):
            with self.assertRaises(GamingSetupError) as context:
                self.manager._handle_windows_privilege_elevation()
            
            self.assertIn("Privilege elevation is not available", str(context.exception))
    
    def test_handle_windows_privilege_elevation_no_continue(self):
        """Test Windows privilege elevation when user says no but continues."""
        with patch.object(self.manager.console, 'input', side_effect=['n', 'y']):
            # Should not raise exception
            self.manager._handle_windows_privilege_elevation()
    
    def test_handle_windows_privilege_elevation_no_cancel(self):
        """Test Windows privilege elevation when user says no and cancels."""
        with patch.object(self.manager.console, 'input', side_effect=['n', 'n']):
            with self.assertRaises(GamingSetupError) as context:
                self.manager._handle_windows_privilege_elevation()
            
            self.assertIn("Setup cancelled by user", str(context.exception))
    
    def test_handle_windows_privilege_elevation_keyboard_interrupt(self):
        """Test Windows privilege elevation when user presses Ctrl+C."""
        with patch.object(self.manager.console, 'input', side_effect=KeyboardInterrupt()):
            with self.assertRaises(GamingSetupError) as context:
                self.manager._handle_windows_privilege_elevation()
            
            self.assertIn("Setup cancelled by user", str(context.exception))
    
    def test_handle_windows_privilege_elevation_eof_error(self):
        """Test Windows privilege elevation when input is not available."""
        with patch.object(self.manager.console, 'input', side_effect=EOFError()):
            with self.assertRaises(GamingSetupError) as context:
                self.manager._handle_windows_privilege_elevation()
            
            self.assertIn("Setup cancelled - no input available", str(context.exception))
    
    def test_handle_non_windows_privileges(self):
        """Test handling privileges on non-Windows systems."""
        # Should not raise any exception
        self.manager._handle_non_windows_privileges()
    
    @patch('os.name', 'nt')
    def test_check_privilege_requirements_windows_required(self):
        """Test privilege requirement check on Windows for operations that need admin."""
        manager = AdminPrivilegeManager()
        
        self.assertTrue(manager.check_privilege_requirements('security_exclusions'))
        self.assertTrue(manager.check_privilege_requirements('system_configuration'))
        self.assertTrue(manager.check_privilege_requirements('registry_modifications'))
        self.assertTrue(manager.check_privilege_requirements('service_management'))
        self.assertFalse(manager.check_privilege_requirements('file_operations'))
    
    @patch('os.name', 'posix')
    def test_check_privilege_requirements_non_windows(self):
        """Test privilege requirement check on non-Windows systems."""
        manager = AdminPrivilegeManager()
        
        self.assertFalse(manager.check_privilege_requirements('security_exclusions'))
        self.assertFalse(manager.check_privilege_requirements('system_configuration'))
        self.assertFalse(manager.check_privilege_requirements('file_operations'))
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    @patch('os.name', 'nt')
    def test_get_privilege_status_windows_admin(self, mock_is_admin):
        """Test privilege status on Windows with admin privileges."""
        mock_is_admin.return_value = True
        manager = AdminPrivilegeManager()
        
        has_admin, status = manager.get_privilege_status()
        
        self.assertTrue(has_admin)
        self.assertEqual(status, "Running with administrator privileges")
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    @patch('os.name', 'nt')
    def test_get_privilege_status_windows_user(self, mock_is_admin):
        """Test privilege status on Windows without admin privileges."""
        mock_is_admin.return_value = False
        manager = AdminPrivilegeManager()
        
        has_admin, status = manager.get_privilege_status()
        
        self.assertFalse(has_admin)
        self.assertEqual(status, "Running with standard user privileges")
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    @patch('os.name', 'posix')
    def test_get_privilege_status_unix_root(self, mock_is_admin):
        """Test privilege status on Unix as root."""
        mock_is_admin.return_value = True
        manager = AdminPrivilegeManager()
        
        has_admin, status = manager.get_privilege_status()
        
        self.assertTrue(has_admin)
        self.assertEqual(status, "Running as root user")
    
    @patch.object(AdminPrivilegeManager, 'is_admin')
    @patch('os.name', 'posix')
    def test_get_privilege_status_unix_user(self, mock_is_admin):
        """Test privilege status on Unix as regular user."""
        mock_is_admin.return_value = False
        manager = AdminPrivilegeManager()
        
        has_admin, status = manager.get_privilege_status()
        
        self.assertFalse(has_admin)
        self.assertEqual(status, "Running as standard user")
    
    @patch.object(AdminPrivilegeManager, 'get_privilege_status')
    def test_log_privilege_status_admin(self, mock_get_status):
        """Test logging privilege status when admin."""
        mock_get_status.return_value = (True, "Running with administrator privileges")
        
        with patch.object(self.manager.logger, 'info') as mock_log:
            self.manager.log_privilege_status()
            mock_log.assert_called_once_with("✅ Running with administrator privileges")
    
    @patch.object(AdminPrivilegeManager, 'get_privilege_status')
    def test_log_privilege_status_user(self, mock_get_status):
        """Test logging privilege status when not admin."""
        mock_get_status.return_value = (False, "Running with standard user privileges")
        
        with patch.object(self.manager.logger, 'info') as mock_log:
            self.manager.log_privilege_status()
            mock_log.assert_called_once_with("ℹ️  Running with standard user privileges")
    
    @patch('os.name', 'nt')
    def test_is_windows_property_true(self):
        """Test is_windows property on Windows."""
        manager = AdminPrivilegeManager()
        self.assertTrue(manager.is_windows)
    
    @patch('os.name', 'posix')
    def test_is_windows_property_false(self):
        """Test is_windows property on non-Windows."""
        manager = AdminPrivilegeManager()
        self.assertFalse(manager.is_windows)
    
    @patch('os.name', 'nt')
    def test_platform_name_windows(self):
        """Test platform name on Windows."""
        manager = AdminPrivilegeManager()
        self.assertEqual(manager.platform_name, "Windows")
    
    @patch('os.name', 'posix')
    @patch('sys.platform', 'linux')
    def test_platform_name_linux(self):
        """Test platform name on Linux."""
        manager = AdminPrivilegeManager()
        self.assertEqual(manager.platform_name, "Linux")
    
    @patch('os.name', 'posix')
    @patch('sys.platform', 'darwin')
    def test_platform_name_macos(self):
        """Test platform name on macOS."""
        manager = AdminPrivilegeManager()
        self.assertEqual(manager.platform_name, "macOS")
    
    @patch('os.name', 'posix')
    @patch('sys.platform', 'freebsd')
    def test_platform_name_other(self):
        """Test platform name on other systems."""
        manager = AdminPrivilegeManager()
        self.assertEqual(manager.platform_name, "freebsd")


if __name__ == '__main__':
    unittest.main()