"""
Integration tests for Configuration Manager with UI Manager.

Tests the Configuration Manager working with a real UI Manager instance
to ensure proper integration and user feedback.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.configuration_manager import ConfigurationManager
from src.ui_manager import UIManager


class TestConfigurationManagerIntegration(unittest.TestCase):
    """Integration test cases for Configuration Manager with UI Manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ui_manager = UIManager()
        self.config_manager = ConfigurationManager(self.ui_manager)
    
    def test_integration_with_ui_manager(self):
        """Test Configuration Manager integration with real UI Manager."""
        # Test that the Configuration Manager can be initialized with a real UI Manager
        assert self.config_manager.ui is self.ui_manager
        assert isinstance(self.config_manager.ui, UIManager)
    
    def test_dll_injector_update_integration(self):
        """Test DLL injector update with real UI Manager feedback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_dir = Path(temp_dir)
            
            # Create DLL file
            dll_file = greenluma_dir / "GreenLuma_2020_x86.dll"
            dll_file.write_text("dummy dll content")
            
            # Create INI file
            ini_file = greenluma_dir / "DLLInjector.ini"
            ini_content = '''[Settings]
Dll = "C:\\old\\path\\GreenLuma_2020_x86.dll"
OtherSetting = value
'''
            ini_file.write_text(ini_content)
            
            # Test the update - should work without exceptions
            result = self.config_manager.update_dll_injector_ini(str(greenluma_dir))
            
            # Should succeed
            assert result is True
            
            # Verify file was updated
            updated_content = ini_file.read_text()
            assert str(dll_file) in updated_content
            assert 'OtherSetting = value' in updated_content
    
    def test_applist_creation_integration(self):
        """Test AppList creation with real UI Manager feedback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            greenluma_path = Path(temp_dir)
            
            # Test AppList creation - should work without exceptions
            result = self.config_manager.create_applist_structure(str(greenluma_path))
            
            # Should succeed
            assert result is True
            
            # Verify structure was created
            applist_dir = greenluma_path / "AppList"
            assert applist_dir.exists()
            assert applist_dir.is_dir()
            
            applist_file = applist_dir / "0.txt"
            assert applist_file.exists()
            content = applist_file.read_text().strip()
            assert content == "252950"
    
    def test_koalageddon_config_update_integration(self):
        """Test Koalageddon config update with real UI Manager feedback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source config
            source_config = Path(temp_dir) / "source_config.jsonc"
            source_config.write_text('{"test": "config", "version": 1}')
            
            # Create target directory
            target_dir = Path(temp_dir) / "koala_config"
            target_dir.mkdir()
            
            # Test the update - should work without exceptions
            result = self.config_manager.update_koalageddon_config(
                str(source_config), str(target_dir)
            )
            
            # Should succeed
            assert result is True
            
            # Verify file was copied
            target_file = target_dir / "Config.jsonc"
            assert target_file.exists()
            assert target_file.read_text() == '{"test": "config", "version": 1}'


if __name__ == '__main__':
    unittest.main()