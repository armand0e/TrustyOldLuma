"""
Tests for Configuration Manager.

Tests cover:
- Koalageddon configuration file updates with JSON parsing and writing
- DLLInjector.ini path configuration methods with proper string replacement
- Desktop shortcut creation using Windows COM objects and VBScript generation
- AppList folder and file creation with proper App ID handling
"""

import json
import os
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

from src.configuration_manager import ConfigurationManager
from src.ui_manager import UIManager


class TestConfigurationManager(unittest.TestCase):
    """Test cases for Configuration Manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ui_manager = Mock(spec=UIManager)
        self.config_manager = ConfigurationManager(self.ui_manager)
    
    def test_init(self):
        """Test Configuration Manager initialization."""
        assert self.config_manager.ui is self.ui_manager
        assert self.config_manager.default_app_id == "252950"
    
    def test_update_koalageddon_config_success(self):
        """Test successful Koalageddon config update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source config file
            source_config = Path(temp_dir) / "source_config.jsonc"
            source_config.write_text('{"test": "config"}')
            
            # Create target directory
            target_dir = Path(temp_dir) / "koala_config"
            target_dir.mkdir()
            
            # Test the update
            result = self.config_manager.update_koalageddon_config(
                str(source_config), str(target_dir)
            )
            
            assert result is True
            
            # Verify file was copied
            target_file = target_dir / "Config.jsonc"
            assert target_file.exists()
            assert target_file.read_text() == '{"test": "config"}'
            
            # Verify UI feedback
            self.ui_manager.display_success.assert_called_once_with(
                "Replaced Koalageddon config with repository version"
            )
    
    def test_update_koalageddon_config_source_not_found(self):
        """Test Koalageddon config update with missing source file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_config = Path(temp_dir) / "nonexistent.jsonc"
            target_dir = Path(temp_dir) / "koala_config"
            target_dir.mkdir()
            
            result = self.config_manager.update_koalageddon_config(
                str(source_config), str(target_dir)
            )
            
            assert result is False
            self.ui_manager.display_error.assert_called_once()
            error_call = self.ui_manager.display_error.call_args
            assert "Source config file not found" in error_call[0][0]
    
    def test_update_koalageddon_config_target_dir_not_found(self):
        """Test Koalageddon config update with missing target directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_config = Path(temp_dir) / "source_config.jsonc"
            source_config.write_text('{"test": "config"}')
            
            target_dir = Path(temp_dir) / "nonexistent_dir"
            
            result = self.config_manager.update_koalageddon_config(
                str(source_config), str(target_dir)
            )
            
            assert result is False
            self.ui_manager.display_warning.assert_called_once()
            warning_call = self.ui_manager.display_warning.call_args
            assert "Koalageddon config directory not found" in warning_call[0][0]
    
    @patch('shutil.copy2')
    @patch('time.sleep')
    def test_update_koalageddon_config_retry_logic(self, mock_sleep, mock_copy):
        """Test retry logic for file in use scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_config = Path(temp_dir) / "source_config.jsonc"
            source_config.write_text('{"test": "config"}')
            
            target_dir = Path(temp_dir) / "koala_config"
            target_dir.mkdir()
            
            # Mock copy to fail twice then succeed
            mock_copy.side_effect = [
                PermissionError("File in use"),
                PermissionError("File in use"),
                None  # Success on third attempt
            ]
            
            result = self.config_manager.update_koalageddon_config(
                str(source_config), str(target_dir)
            )
            
            assert result is True
            assert mock_copy.call_count == 3
            assert mock_sleep.call_count == 2  # Sleep before retry attempts
            self.ui_manager.display_success.assert_called_once()
    
    def test_update_dll_injector_ini_success(self):
        """Test successful DLLInjector.ini update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_dir = Path(temp_dir)
            
            # Create DLL file
            dll_file = greenluma_dir / "GreenLuma_2020_x86.dll"
            dll_file.write_text("dummy dll content")
            
            # Create INI file with placeholder path
            ini_file = greenluma_dir / "DLLInjector.ini"
            ini_content = '''[Settings]
Dll = "C:\\old\\path\\GreenLuma_2020_x86.dll"
OtherSetting = value
'''
            ini_file.write_text(ini_content)
            
            result = self.config_manager.update_dll_injector_ini(str(greenluma_dir))
            
            assert result is True
            
            # Verify INI file was updated
            updated_content = ini_file.read_text()
            expected_dll_path = str(dll_file)
            assert f'Dll = "{expected_dll_path}"' in updated_content
            assert 'OtherSetting = value' in updated_content  # Other content preserved
            
            self.ui_manager.display_success.assert_called_once()
            success_call = self.ui_manager.display_success.call_args
            assert "Updated DLLInjector.ini with path" in success_call[0][0]
    
    def test_update_dll_injector_ini_dll_not_found(self):
        """Test DLLInjector.ini update with missing DLL file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_dir = Path(temp_dir)
            
            # Create INI file but no DLL
            ini_file = greenluma_dir / "DLLInjector.ini"
            ini_file.write_text('[Settings]\nDll = "old_path"')
            
            result = self.config_manager.update_dll_injector_ini(str(greenluma_dir))
            
            assert result is False
            self.ui_manager.display_warning.assert_called_once()
            warning_call = self.ui_manager.display_warning.call_args
            assert "GreenLuma DLL not found" in warning_call[0][0]
    
    def test_update_dll_injector_ini_file_not_found(self):
        """Test DLLInjector.ini update with missing INI file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_dir = Path(temp_dir)
            
            # Create DLL file but no INI
            dll_file = greenluma_dir / "GreenLuma_2020_x86.dll"
            dll_file.write_text("dummy dll content")
            
            result = self.config_manager.update_dll_injector_ini(str(greenluma_dir))
            
            assert result is False
            self.ui_manager.display_error.assert_called_once()
            error_call = self.ui_manager.display_error.call_args
            assert "DLLInjector.ini not found" in error_call[0][0]
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_create_desktop_shortcut_success(self, mock_unlink, mock_tempfile, mock_subprocess):
        """Test successful desktop shortcut creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock desktop path
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                # Mock temporary file
                mock_file = MagicMock()
                mock_file.name = str(Path(temp_dir) / "temp.vbs")
                mock_tempfile.return_value.__enter__.return_value = mock_file
                
                # Mock successful subprocess
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_subprocess.return_value = mock_result
                
                result = self.config_manager.create_desktop_shortcut(
                    "C:\\target\\app.exe",
                    "TestApp",
                    "C:\\target",
                    "C:\\target\\icon.ico"
                )
                
                assert result is True
                
                # Verify VBScript was written
                mock_file.write.assert_called_once()
                vbs_content = mock_file.write.call_args[0][0]
                assert 'Set oWS = WScript.CreateObject("WScript.Shell")' in vbs_content
                assert 'TestApp.lnk' in vbs_content
                assert 'C:\\target\\app.exe' in vbs_content
                assert 'C:\\target\\icon.ico' in vbs_content
                
                # Verify subprocess was called
                mock_subprocess.assert_called_once()
                subprocess_args = mock_subprocess.call_args[0][0]
                assert subprocess_args[0] == 'cscript'
                assert subprocess_args[1] == '//nologo'
                
                # Verify cleanup
                mock_unlink.assert_called_once()
                
                self.ui_manager.display_success.assert_called_once()
    
    def test_create_desktop_shortcut_no_desktop(self):
        """Test desktop shortcut creation with no desktop directory."""
        with patch.object(self.config_manager, '_get_desktop_path', return_value=None):
            result = self.config_manager.create_desktop_shortcut(
                "C:\\target\\app.exe", "TestApp", "C:\\target"
            )
            
            assert result is False
            self.ui_manager.display_warning.assert_called_once()
            warning_call = self.ui_manager.display_warning.call_args
            assert "Could not find desktop directory" in warning_call[0][0]
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_create_desktop_shortcut_vbscript_failure(self, mock_tempfile, mock_subprocess):
        """Test desktop shortcut creation with VBScript execution failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                # Mock temporary file
                mock_file = MagicMock()
                mock_file.name = str(Path(temp_dir) / "temp.vbs")
                mock_tempfile.return_value.__enter__.return_value = mock_file
                
                # Mock failed subprocess
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stderr = "VBScript error"
                mock_subprocess.return_value = mock_result
                
                result = self.config_manager.create_desktop_shortcut(
                    "C:\\target\\app.exe", "TestApp", "C:\\target"
                )
                
                assert result is False
                self.ui_manager.display_error.assert_called_once()
                error_call = self.ui_manager.display_error.call_args
                assert "Failed to create desktop shortcut" in error_call[0][0]
    
    @patch('shutil.copy2')
    def test_copy_koalageddon_shortcut_success(self, mock_copy):
        """Test successful Koalageddon shortcut copy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create desktop directory and shortcut
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            source_shortcut = desktop_path / "Koalageddon.lnk"
            source_shortcut.write_text("shortcut content")
            
            greenluma_path = Path(temp_dir) / "GreenLuma"
            greenluma_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                result = self.config_manager.copy_koalageddon_shortcut(str(greenluma_path))
                
                assert result is True
                
                # Verify copy was called
                mock_copy.assert_called_once()
                copy_args = mock_copy.call_args[0]
                assert str(source_shortcut) == str(copy_args[0])
                assert str(greenluma_path / "Koalageddon.lnk") == str(copy_args[1])
                
                self.ui_manager.display_success.assert_called_once()
    
    def test_copy_koalageddon_shortcut_not_found(self):
        """Test Koalageddon shortcut copy with missing source shortcut."""
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            # Don't create the shortcut file
            
            greenluma_path = Path(temp_dir) / "GreenLuma"
            greenluma_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                result = self.config_manager.copy_koalageddon_shortcut(str(greenluma_path))
                
                assert result is False
                self.ui_manager.display_warning.assert_called_once()
                warning_call = self.ui_manager.display_warning.call_args
                assert "Koalageddon desktop shortcut not found" in warning_call[0][0]
    
    def test_create_applist_structure_success(self):
        """Test successful AppList structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_path = Path(temp_dir)
            
            result = self.config_manager.create_applist_structure(str(greenluma_path))
            
            assert result is True
            
            # Verify AppList directory was created
            applist_dir = greenluma_path / "AppList"
            assert applist_dir.exists()
            assert applist_dir.is_dir()
            
            # Verify initial app list file was created
            applist_file = applist_dir / "0.txt"
            assert applist_file.exists()
            content = applist_file.read_text().strip()
            assert content == "252950"  # Default app ID
            
            # Verify UI feedback
            assert self.ui_manager.display_success.call_count == 2
            success_calls = [call[0][0] for call in self.ui_manager.display_success.call_args_list]
            assert "Created AppList folder" in success_calls
            assert "Created initial AppList file with App ID: 252950" in success_calls
    
    def test_create_applist_structure_custom_app_id(self):
        """Test AppList structure creation with custom App ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_path = Path(temp_dir)
            custom_app_id = "123456"
            
            result = self.config_manager.create_applist_structure(
                str(greenluma_path), custom_app_id
            )
            
            assert result is True
            
            # Verify custom app ID was used
            applist_file = greenluma_path / "AppList" / "0.txt"
            content = applist_file.read_text().strip()
            assert content == custom_app_id
            
            # Verify UI feedback includes custom app ID
            success_calls = [call[0][0] for call in self.ui_manager.display_success.call_args_list]
            assert f"Created initial AppList file with App ID: {custom_app_id}" in success_calls
    
    def test_get_desktop_path_standard(self):
        """Test desktop path detection for standard desktop."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create standard desktop
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                result = self.config_manager._get_desktop_path()
                assert result == desktop_path
    
    def test_get_desktop_path_onedrive(self):
        """Test desktop path detection for OneDrive desktop."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OneDrive desktop (no standard desktop)
            onedrive_desktop = Path(temp_dir) / "OneDrive" / "Desktop"
            onedrive_desktop.mkdir(parents=True)
            
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                result = self.config_manager._get_desktop_path()
                assert result == onedrive_desktop
    
    def test_get_desktop_path_none_found(self):
        """Test desktop path detection when no desktop exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create any desktop directories
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                result = self.config_manager._get_desktop_path()
                assert result is None
    
    def test_generate_vbscript_with_icon(self):
        """Test VBScript generation with icon."""
        vbs_content = self.config_manager._generate_vbscript(
            "C:\\Desktop\\Test.lnk",
            "C:\\target\\app.exe",
            "C:\\target",
            "C:\\target\\icon.ico"
        )
        
        expected_lines = [
            'Set oWS = WScript.CreateObject("WScript.Shell")',
            'sLinkFile = "C:\\Desktop\\Test.lnk"',
            'Set oLink = oWS.CreateShortcut(sLinkFile)',
            'oLink.TargetPath = "C:\\target\\app.exe"',
            'oLink.WorkingDirectory = "C:\\target"',
            'oLink.IconLocation = "C:\\target\\icon.ico"',
            'oLink.Save'
        ]
        
        for line in expected_lines:
            assert line in vbs_content
    
    def test_generate_vbscript_without_icon(self):
        """Test VBScript generation without icon."""
        vbs_content = self.config_manager._generate_vbscript(
            "C:\\Desktop\\Test.lnk",
            "C:\\target\\app.exe",
            "C:\\target"
        )
        
        # Should not contain icon line
        assert 'oLink.IconLocation' not in vbs_content
        
        # Should contain other required lines
        assert 'Set oWS = WScript.CreateObject("WScript.Shell")' in vbs_content
        assert 'oLink.TargetPath = "C:\\target\\app.exe"' in vbs_content
        assert 'oLink.Save' in vbs_content
    
    @patch('shutil.copy2')
    def test_update_koalageddon_config_max_retries_exceeded(self, mock_copy):
        """Test Koalageddon config update when max retries exceeded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_config = Path(temp_dir) / "source_config.jsonc"
            source_config.write_text('{"test": "config"}')
            
            target_dir = Path(temp_dir) / "koala_config"
            target_dir.mkdir()
            
            # Mock copy to always fail
            mock_copy.side_effect = PermissionError("File permanently in use")
            
            result = self.config_manager.update_koalageddon_config(
                str(source_config), str(target_dir)
            )
            
            assert result is False
            assert mock_copy.call_count == 3  # Should retry 3 times
            self.ui_manager.display_warning.assert_called_once()
    
    def test_update_dll_injector_ini_multiple_dll_files(self):
        """Test DLLInjector.ini update with multiple DLL files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_dir = Path(temp_dir)
            
            # Create multiple DLL files
            dll_x86 = greenluma_dir / "GreenLuma_2020_x86.dll"
            dll_x64 = greenluma_dir / "GreenLuma_2020_x64.dll"
            dll_x86.write_text("x86 dll content")
            dll_x64.write_text("x64 dll content")
            
            # Create INI file
            ini_file = greenluma_dir / "DLLInjector.ini"
            ini_content = '[Settings]\nDll = "old_path"'
            ini_file.write_text(ini_content)
            
            result = self.config_manager.update_dll_injector_ini(str(greenluma_dir))
            
            assert result is True
            
            # Should use x86 version (first found)
            updated_content = ini_file.read_text()
            assert str(dll_x86) in updated_content
    
    def test_update_dll_injector_ini_read_only_file(self):
        """Test DLLInjector.ini update with read-only INI file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_dir = Path(temp_dir)
            
            # Create DLL file
            dll_file = greenluma_dir / "GreenLuma_2020_x86.dll"
            dll_file.write_text("dll content")
            
            # Create INI file
            ini_file = greenluma_dir / "DLLInjector.ini"
            ini_file.write_text('[Settings]\nDll = "old_path"')
            
            # Mock Path.write_text to raise PermissionError
            with patch('pathlib.Path.write_text', side_effect=PermissionError("Read-only file")):
                result = self.config_manager.update_dll_injector_ini(str(greenluma_dir))
                
                assert result is False
                self.ui_manager.display_error.assert_called_once()
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_create_desktop_shortcut_vbscript_timeout(self, mock_tempfile, mock_subprocess):
        """Test desktop shortcut creation with VBScript timeout."""
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                # Mock temporary file
                mock_file = MagicMock()
                mock_file.name = str(Path(temp_dir) / "temp.vbs")
                mock_tempfile.return_value.__enter__.return_value = mock_file
                
                # Mock subprocess timeout
                mock_subprocess.side_effect = subprocess.TimeoutExpired("cscript", 30)
                
                result = self.config_manager.create_desktop_shortcut(
                    "C:\\target\\app.exe", "TestApp", "C:\\target"
                )
                
                assert result is False
                self.ui_manager.display_error.assert_called_once()
    
    def test_copy_koalageddon_shortcut_permission_error(self):
        """Test Koalageddon shortcut copy with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            source_shortcut = desktop_path / "Koalageddon.lnk"
            source_shortcut.write_text("shortcut content")
            
            greenluma_path = Path(temp_dir) / "GreenLuma"
            greenluma_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                with patch('shutil.copy2', side_effect=PermissionError("Access denied")):
                    result = self.config_manager.copy_koalageddon_shortcut(str(greenluma_path))
                    
                    assert result is False
                    self.ui_manager.display_warning.assert_called_once()
    
    def test_create_applist_structure_permission_error(self):
        """Test AppList structure creation with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_path = Path(temp_dir)
            
            # Mock Path.mkdir to raise PermissionError
            with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
                result = self.config_manager.create_applist_structure(str(greenluma_path))
                
                assert result is False
                self.ui_manager.display_error.assert_called_once()
    
    def test_create_applist_structure_file_write_error(self):
        """Test AppList structure creation with file write error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_path = Path(temp_dir)
            
            # Mock Path.write_text to raise PermissionError for file creation
            with patch('pathlib.Path.write_text', side_effect=PermissionError("Cannot write file")):
                result = self.config_manager.create_applist_structure(str(greenluma_path))
                
                assert result is False
                self.ui_manager.display_error.assert_called()
    
    def test_get_desktop_path_both_exist_prefer_standard(self):
        """Test desktop path detection when both standard and OneDrive exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create both desktop directories
            standard_desktop = Path(temp_dir) / "Desktop"
            onedrive_desktop = Path(temp_dir) / "OneDrive" / "Desktop"
            standard_desktop.mkdir()
            onedrive_desktop.mkdir(parents=True)
            
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                result = self.config_manager._get_desktop_path()
                # Should prefer standard desktop
                assert result == standard_desktop
    
    def test_create_desktop_shortcut_with_special_characters(self):
        """Test desktop shortcut creation with special characters in paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_path = Path(temp_dir) / "Desktop"
            desktop_path.mkdir()
            
            with patch.object(self.config_manager, '_get_desktop_path', return_value=desktop_path):
                with patch('subprocess.run') as mock_subprocess:
                    with patch('tempfile.NamedTemporaryFile') as mock_tempfile:
                        # Mock successful execution
                        mock_result = MagicMock()
                        mock_result.returncode = 0
                        mock_subprocess.return_value = mock_result
                        
                        mock_file = MagicMock()
                        mock_file.name = str(Path(temp_dir) / "temp.vbs")
                        mock_tempfile.return_value.__enter__.return_value = mock_file
                        
                        # Test with special characters
                        result = self.config_manager.create_desktop_shortcut(
                            "C:\\Program Files (x86)\\App\\app.exe",
                            "Test App & More",
                            "C:\\Program Files (x86)\\App",
                            "C:\\Program Files (x86)\\App\\icon.ico"
                        )
                        
                        assert result is True
                        # Verify VBScript was written with escaped characters
                        mock_file.write.assert_called_once()
    
    def test_configuration_manager_default_app_id(self):
        """Test configuration manager default app ID."""
        assert self.config_manager.default_app_id == "252950"
        
        # Test with custom app ID
        custom_ui = Mock(spec=UIManager)
        custom_manager = ConfigurationManager(custom_ui)
        custom_manager.default_app_id = "123456"
        
        assert custom_manager.default_app_id == "123456"


if __name__ == '__main__':
    unittest.main()