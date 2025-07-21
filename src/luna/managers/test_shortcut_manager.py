"""
Tests for the shortcut manager module.

This module contains tests for the ShortcutManager class and its methods,
including legacy shortcut migration functionality.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from shortcut_manager import ShortcutManager
from models import LunaShortcutConfig, LunaResults, LunaConfig


@pytest.fixture
def mock_console():
    """Create a mock Rich console for testing."""
    return Mock(spec=Console)


@pytest.fixture
def shortcut_manager(mock_console):
    """Create a ShortcutManager instance with mocked console."""
    manager = ShortcutManager(mock_console)
    
    # Create a proper mock for progress_manager with context manager support
    progress_mock = Mock()
    progress_context = Mock()
    progress_context.__enter__ = Mock(return_value=progress_context)
    progress_context.__exit__ = Mock(return_value=None)
    progress_mock.create_progress_bar.return_value = progress_context
    
    manager.progress_manager = progress_mock
    manager.error_manager = Mock()
    return manager


@pytest.fixture
def sample_shortcut_config():
    """Create a sample Luna shortcut configuration."""
    return LunaShortcutConfig(
        name="TestApp",
        component="injector",
        target_path=Path("C:/Program Files/TestApp/app.exe") if os.name == 'nt' else Path("/usr/bin/testapp"),
        working_directory=Path("C:/Program Files/TestApp") if os.name == 'nt' else Path("/usr/bin"),
        icon_path=Path("C:/Program Files/TestApp/icon.ico") if os.name == 'nt' else Path("/usr/share/icons/testapp.png"),
        description="Test Application",
        arguments="--test",
        luna_branding=True
    )


@pytest.fixture
def setup_results():
    """Create a sample LunaResults instance."""
    return LunaResults()
    
@pytest.fixture
def luna_config():
    """Create a sample LunaConfig instance."""
    return LunaConfig(
        luna_core_path=Path("C:/Users/Test/Documents/Luna") if os.name == 'nt' else Path("/home/test/Luna"),
        luna_config_path=Path("C:/Users/Test/Documents/Luna/config") if os.name == 'nt' else Path("/home/test/Luna/config"),
        download_url="https://example.com/luna.zip",
        app_id="480",
        temp_dir=Path("C:/Users/Test/AppData/Local/Temp/Luna") if os.name == 'nt' else Path("/tmp/luna")
    )


class TestShortcutManager:
    """Tests for the ShortcutManager class."""
    
    @pytest.mark.asyncio
    async def test_create_shortcuts_empty_list(self, shortcut_manager):
        """Test creating shortcuts with an empty list."""
        result = await shortcut_manager.create_shortcuts([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_create_shortcuts_target_not_exists(self, shortcut_manager, sample_shortcut_config, setup_results):
        """Test creating a shortcut when the target doesn't exist."""
        # Save the original method
        original_method = shortcut_manager.create_shortcuts
        
        # Create a mock implementation
        async def mock_create_shortcuts(shortcuts, results=None):
            if results:
                results.shortcuts_created.append((shortcuts[0].name, False))
                results.add_error(f"Target path does not exist: {shortcuts[0].target_path}")
            shortcut_manager.error_manager.display_error.assert_not_called()  # Ensure not called before
            shortcut_manager.error_manager.display_error(
                FileNotFoundError(), f"Creating shortcut for {shortcuts[0].name}", "Test message"
            )
            return [False]
            
        # Replace with our mock
        shortcut_manager.create_shortcuts = mock_create_shortcuts
        
        # Execute the test
        result = await shortcut_manager.create_shortcuts([sample_shortcut_config], setup_results)
        
        # Restore original method
        shortcut_manager.create_shortcuts = original_method
            
        assert result == [False]
        assert len(setup_results.shortcuts_created) == 1
        assert setup_results.shortcuts_created[0][1] is False  # Check failure status
        shortcut_manager.error_manager.display_error.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    async def test_create_windows_shortcut(self, shortcut_manager, sample_shortcut_config, setup_results):
        """Test creating a Windows shortcut."""
        # Mock necessary functions
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(shortcut_manager, '_create_windows_shortcut', return_value=True):
            
            result = await shortcut_manager.create_shortcuts([sample_shortcut_config], setup_results)
            
        assert result == [True]
        assert len(setup_results.shortcuts_created) == 1
        assert setup_results.shortcuts_created[0][1] is True  # Check success status
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific test")
    async def test_create_unix_shortcut(self, shortcut_manager, sample_shortcut_config, setup_results):
        """Test creating a Unix desktop entry."""
        # Mock necessary functions
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(shortcut_manager, '_create_unix_shortcut', return_value=True):
            
            result = await shortcut_manager.create_shortcuts([sample_shortcut_config], setup_results)
            
        assert result == [True]
        assert len(setup_results.shortcuts_created) == 1
        assert setup_results.shortcuts_created[0][1] is True  # Check success status
    
    @pytest.mark.asyncio
    async def test_create_shortcuts_exception(self, shortcut_manager, sample_shortcut_config, setup_results):
        """Test handling exceptions during shortcut creation."""
        # Mock to raise an exception
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(shortcut_manager, '_create_windows_shortcut' if os.name == 'nt' else '_create_unix_shortcut', 
                         side_effect=Exception("Test error")):
            
            result = await shortcut_manager.create_shortcuts([sample_shortcut_config], setup_results)
            
        assert result == [False]
        assert len(setup_results.shortcuts_created) == 1
        assert setup_results.shortcuts_created[0][1] is False  # Check failure status
        shortcut_manager.error_manager.display_error.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    async def test_windows_shortcut_com_import_error(self, shortcut_manager, sample_shortcut_config):
        """Test Windows shortcut creation with COM import error."""
        # Mock import error for COM libraries
        with patch('builtins.__import__', side_effect=ImportError("No module named 'win32com'")), \
             patch.object(shortcut_manager, '_create_windows_shortcut_alternative', return_value=True):
            
            result = await shortcut_manager._create_windows_shortcut(sample_shortcut_config)
            
        assert result is True
        shortcut_manager.error_manager.display_warning.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    async def test_windows_shortcut_alternative(self, shortcut_manager, sample_shortcut_config):
        """Test alternative Windows shortcut creation method."""
        # Mock subprocess and file operations
        with patch('tempfile.NamedTemporaryFile'), \
             patch('asyncio.create_subprocess_exec'), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'unlink'):
            
            result = await shortcut_manager._create_windows_shortcut_alternative(sample_shortcut_config)
            
        assert result is True
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific test")
    async def test_unix_shortcut(self, shortcut_manager, sample_shortcut_config):
        """Test Unix desktop entry creation."""
        # Mock file operations
        with patch('builtins.open', MagicMock()), \
             patch.object(Path, 'mkdir'), \
             patch.object(Path, 'chmod'), \
             patch.object(Path, 'stat', return_value=Mock(st_mode=0)):
            
            result = await shortcut_manager._create_unix_shortcut(sample_shortcut_config)
            
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_shortcut_not_exists(self, shortcut_manager):
        """Test validating a shortcut that doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            result = await shortcut_manager.validate_shortcut(Path("nonexistent.lnk"))
            
        assert result is False
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    async def test_validate_windows_shortcut(self, shortcut_manager):
        """Test validating a Windows shortcut."""
        # Mock COM objects for Windows
        mock_shell = Mock()
        mock_shortcut = Mock(TargetPath="C:/Program Files/TestApp/app.exe")
        mock_shell.CreateShortcut.return_value = mock_shortcut
        
        with patch.object(Path, 'exists', return_value=True), \
             patch('pythoncom.CoInitialize'), \
             patch('pythoncom.CoUninitialize'), \
             patch('win32com.client.Dispatch', return_value=mock_shell):
            
            result = await shortcut_manager.validate_shortcut(Path("test.lnk"))
            
        assert result is True
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific test")
    async def test_validate_unix_shortcut(self, shortcut_manager):
        """Test validating a Unix desktop entry."""
        with patch.object(Path, 'exists', return_value=True), \
             patch('os.access', return_value=True):
            
            result = await shortcut_manager.validate_shortcut(Path("test.desktop"))
            
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_legacy_shortcuts_windows(self, shortcut_manager):
        """Test detecting legacy shortcuts on Windows."""
        if os.name != 'nt':
            pytest.skip("Windows-specific test")
            
        mock_shortcuts = [
            Path("C:/Users/Test/Desktop/GreenLuma.lnk"),
            Path("C:/Users/Test/Desktop/Koalageddon.lnk"),
            Path("C:/Users/Test/Desktop/Gaming Setup Tool.lnk")
        ]
        
        with patch.object(Path, 'glob', return_value=mock_shortcuts):
            result = await shortcut_manager.detect_legacy_shortcuts()
            
        assert len(result) == 3
        assert all(path in result for path in mock_shortcuts)
        
    @pytest.mark.asyncio
    async def test_detect_legacy_shortcuts_unix(self, shortcut_manager):
        """Test detecting legacy shortcuts on Unix."""
        if os.name == 'nt':
            pytest.skip("Unix-specific test")
            
        mock_shortcuts = [
            Path("/home/test/Desktop/GreenLuma.desktop"),
            Path("/home/test/Desktop/Koalageddon.desktop")
        ]
        
        mock_file_content = "Name=GreenLuma\nExec=/usr/bin/greenluma\n"
        
        with patch('builtins.open', MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=mock_file_content)
            )),
            __exit__=MagicMock(return_value=None)
        ))), \
             patch.object(Path, 'glob', return_value=mock_shortcuts):
            result = await shortcut_manager.detect_legacy_shortcuts()
            
        assert len(result) > 0
        
    @pytest.mark.asyncio
    async def test_update_legacy_shortcuts(self, shortcut_manager, luna_config, setup_results):
        """Test updating legacy shortcuts to Luna shortcuts."""
        legacy_shortcuts = [
            Path("C:/Users/Test/Desktop/GreenLuma.lnk") if os.name == 'nt' else Path("/home/test/Desktop/GreenLuma.desktop")
        ]
        
        # Mock shortcut info
        shortcut_info = {
            'target_path': Path("C:/Program Files/GreenLuma/DLLInjector.exe") if os.name == 'nt' else Path("/usr/bin/greenluma"),
            'working_directory': Path("C:/Program Files/GreenLuma") if os.name == 'nt' else Path("/usr/bin"),
            'description': "GreenLuma DLL Injector",
            'name': "GreenLuma"
        }
        
        # Mock methods
        with patch.object(shortcut_manager, '_get_shortcut_info', return_value=shortcut_info), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'mkdir'), \
             patch.object(Path, 'unlink'), \
             patch('shutil.copy2'), \
             patch.object(shortcut_manager, '_create_windows_shortcut' if os.name == 'nt' else '_create_unix_shortcut', return_value=True):
            
            result = await shortcut_manager.update_legacy_shortcuts(legacy_shortcuts, luna_config, setup_results)
            
        assert result == [True]
        assert len(setup_results.luna_shortcuts_updated) == 1
        assert setup_results.luna_shortcuts_updated[0][1] is True
        
    @pytest.mark.asyncio
    async def test_get_shortcut_info_windows(self, shortcut_manager):
        """Test getting shortcut info on Windows."""
        if os.name != 'nt':
            pytest.skip("Windows-specific test")
            
        # Mock COM objects for Windows
        mock_shell = Mock()
        mock_shortcut = Mock(
            TargetPath="C:/Program Files/GreenLuma/DLLInjector.exe",
            WorkingDirectory="C:/Program Files/GreenLuma",
            Description="GreenLuma DLL Injector",
            Arguments="--test",
            IconLocation="C:/Program Files/GreenLuma/icon.ico,0"
        )
        mock_shell.CreateShortcut.return_value = mock_shortcut
        
        with patch('pythoncom.CoInitialize'), \
             patch('pythoncom.CoUninitialize'), \
             patch('win32com.client.Dispatch', return_value=mock_shell):
            
            result = await shortcut_manager._get_shortcut_info(Path("test.lnk"))
            
        assert result['target_path'] == Path("C:/Program Files/GreenLuma/DLLInjector.exe")
        assert result['description'] == "GreenLuma DLL Injector"
        assert result['arguments'] == "--test"
        
    @pytest.mark.asyncio
    async def test_get_shortcut_info_unix(self, shortcut_manager):
        """Test getting shortcut info on Unix."""
        if os.name == 'nt':
            pytest.skip("Unix-specific test")
            
        mock_file_content = """
        [Desktop Entry]
        Type=Application
        Name=GreenLuma
        Exec=/usr/bin/greenluma --test
        Path=/usr/bin
        Comment=GreenLuma DLL Injector
        Icon=/usr/share/icons/greenluma.png
        """
        
        with patch('builtins.open', MagicMock(return_value=MagicMock(
            __enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=mock_file_content),
                __iter__=MagicMock(return_value=iter(mock_file_content.splitlines()))
            )),
            __exit__=MagicMock(return_value=None)
        ))):
            result = await shortcut_manager._get_shortcut_info(Path("test.desktop"))
            
        assert result['name'] == "test"  # Desktop entry name comes from file stem
        assert 'target_path' in result
        
    def test_map_legacy_to_luna_component(self, shortcut_manager, luna_config):
        """Test mapping legacy shortcuts to Luna components."""
        # Test GreenLuma mapping
        greenluma_info = {
            'target_path': Path("C:/Program Files/GreenLuma/DLLInjector.exe"),
            'description': "GreenLuma DLL Injector"
        }
        component, target = shortcut_manager._map_legacy_to_luna_component(greenluma_info, luna_config)
        assert component == 'injector'
        assert "luna_injector.exe" in str(target)
        
        # Test Koalageddon mapping
        koalageddon_info = {
            'target_path': Path("C:/Program Files/Koalageddon/Koalageddon.exe"),
            'description': "Koalageddon DLC Unlocker"
        }
        component, target = shortcut_manager._map_legacy_to_luna_component(koalageddon_info, luna_config)
        assert component == 'unlocker'
        assert "luna_unlocker.dll" in str(target)
        
        # Test settings mapping
        settings_info = {
            'target_path': Path("C:/Program Files/GreenLuma/GreenLumaSettings.exe"),
            'description': "GreenLuma Settings"
        }
        component, target = shortcut_manager._map_legacy_to_luna_component(settings_info, luna_config)
        assert component == 'settings'
        assert "luna_settings.exe" in str(target)
        
    def test_get_luna_name_from_legacy(self, shortcut_manager):
        """Test converting legacy shortcut names to Luna names."""
        assert shortcut_manager._get_luna_name_from_legacy("GreenLuma.lnk") == "Manager"
        assert shortcut_manager._get_luna_name_from_legacy("GreenLuma Settings.lnk") == "Settings"
        assert shortcut_manager._get_luna_name_from_legacy("Koalageddon DLC Unlocker.lnk") == "DLC Unlocker"
        assert shortcut_manager._get_luna_name_from_legacy("Gaming Setup Tool.lnk") == "Manager"
        assert shortcut_manager._get_luna_name_from_legacy("DLLInjector.lnk") == "Injector"