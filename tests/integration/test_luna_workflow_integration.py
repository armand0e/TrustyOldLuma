"""
End-to-end integration tests for Luna workflows.

This module tests complete Luna workflows including installation, migration,
desktop integration, and platform functionality.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
import json
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from rich.console import Console

try:
    from src.luna.core.luna_core import LunaCore
    from src.luna.models.models import LunaConfig, LunaResults, LunaShortcutConfig
    from src.luna.managers.configuration_handler import ConfigurationHandler
    from src.luna.managers.file_operations_manager import FileOperationsManager
    from src.luna.managers.shortcut_manager import ShortcutManager
    from src.luna.managers.security_config_manager import SecurityConfigManager
    from src.luna.setup.setup_tool import LunaSetupTool
except ImportError:
    # Fallback for different import structure
    from luna.core.luna_core import LunaCore
    from models import LunaConfig, LunaResults, LunaShortcutConfig
    from configuration_handler import ConfigurationHandler
    from file_operations_manager import FileOperationsManager
    from shortcut_manager import ShortcutManager
    from security_config_manager import SecurityConfigManager
    from gaming_setup_tool import LunaSetupTool  # Might still be named this way


class TestLunaWorkflowIntegration:
    """Test end-to-end Luna workflows."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for workflow testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'luna': temp_dir / "Luna",
            'luna_injector': temp_dir / "Luna" / "injector",
            'luna_unlocker': temp_dir / "Luna" / "unlocker",
            'luna_config': temp_dir / "Luna" / "config",
            'assets': temp_dir / "assets",
            'desktop': temp_dir / "Desktop",
            'documents': temp_dir / "Documents",
            'temp': temp_dir / "temp"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        # Create mock asset files
        injector_zip = workspace['assets'] / "luna_injector.zip"
        unlocker_zip = workspace['assets'] / "luna_unlocker.zip"
        
        # Create mock injector zip
        with zipfile.ZipFile(injector_zip, 'w') as zf:
            zf.writestr("luna_injector.exe", b"mock executable")
            zf.writestr("luna_core_x64.dll", b"mock dll")
            zf.writestr("luna_injector.ini", b"[Settings]\nDLL=luna_core_x64.dll\n")
        
        # Create mock unlocker zip
        with zipfile.ZipFile(unlocker_zip, 'w') as zf:
            zf.writestr("luna_unlocker.exe", b"mock executable")
            zf.writestr("luna_unlocker.dll", b"mock dll")
            zf.writestr("luna_unlocker.json", b"{\"EnableSteam\": true}")
        
        yield workspace
        
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def luna_config_file(self, temp_workspace):
        """Create a Luna configuration file for testing."""
        config_file = temp_workspace['luna_config'] / "luna_config.jsonc"
        config_content = {
            "luna": {
                "version": "1.0.0",
                "core": {
                    "injector_enabled": True,
                    "unlocker_enabled": True,
                    "auto_start": False,
                    "stealth_mode": True
                },
                "platforms": {
                    "steam": {"enabled": True, "priority": 1},
                    "epic": {"enabled": True, "priority": 2},
                    "origin": {"enabled": False, "priority": 3},
                    "uplay": {"enabled": False, "priority": 4}
                },
                "paths": {
                    "core_directory": str(temp_workspace['luna']),
                    "config_directory": str(temp_workspace['luna_config']),
                    "temp_directory": str(temp_workspace['temp'])
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_content, f, indent=2)
        
        return config_file
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = Mock(spec=Console)
        console.is_jupyter = False
        return console
    
    @pytest.fixture
    def setup_config(self, temp_workspace):
        """Create a test LunaConfig instance."""
        return LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            verbose_logging=False,
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp'],
            desktop_path=temp_workspace['desktop']
        )
    
    @pytest.mark.asyncio
    async def test_complete_luna_installation(self, temp_workspace, setup_config, mock_console):
        """Test complete Luna installation from scratch."""
        # Create setup tool
        setup_tool = LunaSetupTool(verbose=False)
        setup_tool.config = setup_config
        setup_tool.console = mock_console
        
        # Mock file operations
        file_manager = FileOperationsManager(mock_console)
        
        # Mock extract_archive method
        async def mock_extract_archive(archive_path, extract_path, results):
            # Create mock files
            (extract_path / "luna_injector.exe").write_bytes(b"mock executable")
            (extract_path / "luna_core_x64.dll").write_bytes(b"mock dll")
            (extract_path / "luna_injector.ini").write_text("[Settings]\nDLL=luna_core_x64.dll\n")
            return True
        
        # Mock download_file method
        async def mock_download_file(url, target_path, results):
            # Copy mock zip file
            shutil.copy(
                temp_workspace['assets'] / "luna_injector.zip",
                target_path
            )
            return True
        
        # Apply mocks
        with patch.object(file_manager, 'extract_archive', side_effect=mock_extract_archive) as mock_extract, \
             patch.object(file_manager, 'download_file', side_effect=mock_download_file) as mock_download, \
             patch.object(setup_tool, '_setup_luna_injector') as mock_injector_setup, \
             patch.object(setup_tool, '_setup_luna_unlocker') as mock_unlocker_setup, \
             patch.object(setup_tool, '_create_luna_shortcuts') as mock_shortcuts, \
             patch.object(setup_tool, '_setup_security_exclusions') as mock_security:
            
            # Set up mock returns
            mock_injector_setup.return_value = True
            mock_unlocker_setup.return_value = True
            mock_shortcuts.return_value = True
            mock_security.return_value = True
            
            # Run setup
            results = LunaResults()
            await setup_tool.run(results)
            
            # Verify setup was successful
            assert len(results.errors) == 0
            
            # Verify component setup was called
            mock_injector_setup.assert_called_once()
            mock_unlocker_setup.assert_called_once()
            mock_shortcuts.assert_called_once()
            mock_security.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_luna_migration_workflow(self, temp_workspace, setup_config, mock_console):
        """Test migration workflow from existing GreenLuma/Koalageddon installations."""
        # Create legacy installations
        greenluma_dir = temp_workspace['documents'] / "GreenLuma"
        koalageddon_dir = temp_workspace['documents'] / "Koalageddon"
        
        greenluma_dir.mkdir(exist_ok=True)
        koalageddon_dir.mkdir(exist_ok=True)
        
        # Create legacy GreenLuma files
        (greenluma_dir / "DLLInjector.exe").write_bytes(b"mock executable")
        (greenluma_dir / "GreenLuma_2020_x64.dll").write_bytes(b"mock dll")
        (greenluma_dir / "DLLInjector.ini").write_text("[Settings]\nDLL=GreenLuma_2020_x64.dll\n")
        
        # Create AppList directory and files
        applist_dir = greenluma_dir / "AppList"
        applist_dir.mkdir(exist_ok=True)
        (applist_dir / "0.txt").write_text("480")  # Spacewar
        (applist_dir / "1.txt").write_text("570")  # Dota 2
        
        # Create legacy Koalageddon files
        (koalageddon_dir / "Koalageddon.exe").write_bytes(b"mock executable")
        (koalageddon_dir / "Koalageddon.dll").write_bytes(b"mock dll")
        (koalageddon_dir / "Config.jsonc").write_text(
            '{\n'
            '  "EnableSteam": true,\n'
            '  "EnableEpic": true,\n'
            '  "EnableOrigin": false,\n'
            '  "EnableUplay": false,\n'
            '  "LogLevel": "Info"\n'
            '}\n'
        )
        
        # Create legacy shortcuts
        (temp_workspace['desktop'] / "GreenLuma DLLInjector.lnk").write_bytes(b"mock shortcut")
        (temp_workspace['desktop'] / "Koalageddon.lnk").write_bytes(b"mock shortcut")
        
        # Update config with legacy paths
        setup_config.legacy_greenluma_path = greenluma_dir
        setup_config.legacy_koalageddon_path = koalageddon_dir
        
        # Create setup tool
        setup_tool = LunaSetupTool(verbose=False)
        setup_tool.config = setup_config
        setup_tool.console = mock_console
        
        # Mock migration methods
        with patch.object(setup_tool, '_detect_legacy_installations') as mock_detect, \
             patch.object(setup_tool, '_migrate_legacy_configurations') as mock_migrate_config, \
             patch.object(setup_tool, '_migrate_legacy_files') as mock_migrate_files, \
             patch.object(setup_tool, '_update_legacy_shortcuts') as mock_update_shortcuts, \
             patch.object(setup_tool, '_setup_luna_injector') as mock_injector_setup, \
             patch.object(setup_tool, '_setup_luna_unlocker') as mock_unlocker_setup:
            
            # Set up mock returns
            mock_detect.return_value = {
                "greenluma": greenluma_dir,
                "koalageddon": koalageddon_dir
            }
            mock_migrate_config.return_value = True
            mock_migrate_files.return_value = True
            mock_update_shortcuts.return_value = True
            mock_injector_setup.return_value = True
            mock_unlocker_setup.return_value = True
            
            # Run migration
            results = LunaResults()
            await setup_tool.run(results)
            
            # Verify migration was successful
            assert len(results.errors) == 0
            
            # Verify migration methods were called
            mock_detect.assert_called_once()
            mock_migrate_config.assert_called_once()
            mock_migrate_files.assert_called_once()
            mock_update_shortcuts.assert_called_once()
            mock_injector_setup.assert_called_once()
            mock_unlocker_setup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_luna_shortcuts_desktop_integration(self, temp_workspace, mock_console):
        """Test Luna shortcuts and desktop integration."""
        # Create shortcut manager
        shortcut_manager = ShortcutManager(mock_console)
        
        # Create Luna shortcut configurations
        luna_shortcuts = [
            LunaShortcutConfig(
                name="Injector",
                component="injector",
                target_path=temp_workspace['luna_injector'] / "luna_injector.exe",
                working_directory=temp_workspace['luna_injector'],
                description="Luna DLL Injector",
                luna_branding=True
            ),
            LunaShortcutConfig(
                name="Unlocker",
                component="unlocker",
                target_path=temp_workspace['luna_unlocker'] / "luna_unlocker.exe",
                working_directory=temp_workspace['luna_unlocker'],
                description="Luna DLC Unlocker",
                luna_branding=True
            ),
            LunaShortcutConfig(
                name="Manager",
                component="manager",
                target_path=temp_workspace['luna'] / "luna_manager.exe",
                working_directory=temp_workspace['luna'],
                description="Luna Manager",
                luna_branding=True
            )
        ]
        
        # Mock create_shortcut method
        def mock_create_shortcut(shortcut_config, desktop_path):
            # Create mock shortcut file
            shortcut_path = desktop_path / f"{shortcut_config.display_name}.lnk"
            shortcut_path.write_bytes(b"mock shortcut")
            return True
        
        # Apply mock
        with patch.object(shortcut_manager, 'create_shortcut', side_effect=mock_create_shortcut) as mock_create:
            # Create shortcuts
            results = LunaResults()
            success = await shortcut_manager.create_shortcuts(luna_shortcuts, temp_workspace['desktop'], results)
            
            # Verify shortcuts were created successfully
            assert success is True
            assert len(results.errors) == 0
            
            # Verify create_shortcut was called for each shortcut
            assert mock_create.call_count == len(luna_shortcuts)
            
            # Verify shortcut files were created
            for shortcut in luna_shortcuts:
                shortcut_path = temp_workspace['desktop'] / f"{shortcut.display_name}.lnk"
                assert shortcut_path.exists()
    
    @pytest.mark.asyncio
    async def test_luna_platform_functionality(self, temp_workspace, luna_config_file):
        """Test Luna functionality across different gaming platforms."""
        # Create Luna core
        luna_core = LunaCore(luna_config_file)
        
        # Initialize Luna core
        await luna_core.initialize()
        
        # Configure platforms
        platform_config = {
            "platforms": {
                "steam": {"enabled": True, "priority": 1},
                "epic": {"enabled": True, "priority": 2},
                "origin": {"enabled": True, "priority": 3},
                "uplay": {"enabled": False, "priority": 4}
            }
        }
        
        # Update configuration
        update_result = await luna_core.update_config(platform_config)
        
        # Verify update was successful
        assert update_result["success"] is True
        
        # Start injector with platform-specific configuration
        injector_result = await luna_core.start_injector({
            "injector_enabled": True,
            "app_list": ["480", "570", "730"]  # Example Steam App IDs
        })
        
        # Verify injector was started successfully
        assert injector_result["success"] is True
        assert luna_core.injector_running is True
        
        # Start unlocker with platform-specific configuration
        unlocker_result = await luna_core.start_unlocker({
            "unlocker_enabled": True,
            "unlock_dlc": True,
            "platforms": {
                "steam": {"enabled": True},
                "epic": {"enabled": True},
                "origin": {"enabled": True},
                "uplay": {"enabled": False}
            }
        })
        
        # Verify unlocker was started successfully
        assert unlocker_result["success"] is True
        assert luna_core.unlocker_running is True
        
        # Shutdown Luna core
        await luna_core.shutdown()
        
        # Verify components are stopped
        assert luna_core.injector_running is False
        assert luna_core.unlocker_running is False
    
    @pytest.mark.asyncio
    async def test_luna_error_handling_recovery(self, temp_workspace, luna_config_file):
        """Test Luna error handling and recovery scenarios."""
        # Create Luna core
        luna_core = LunaCore(luna_config_file)
        
        # Initialize Luna core
        await luna_core.initialize()
        
        # Test error handling for injector start
        with patch.object(luna_core, 'start_injector', wraps=luna_core.start_injector) as mock_start_injector:
            # Make the first call fail, then succeed
            mock_start_injector.side_effect = [
                {"success": False, "message": "Injector failed to start"},
                {"success": True, "message": "Injector started successfully"}
            ]
            
            # First attempt - should fail
            result1 = await luna_core.start_injector()
            assert result1["success"] is False
            assert "Injector failed to start" in result1["message"]
            
            # Second attempt - should succeed
            result2 = await luna_core.start_injector()
            assert result2["success"] is True
            assert luna_core.injector_running is True
        
        # Test error handling for unlocker start
        with patch.object(luna_core, 'start_unlocker', wraps=luna_core.start_unlocker) as mock_start_unlocker:
            # Make the first call fail, then succeed
            mock_start_unlocker.side_effect = [
                {"success": False, "message": "Unlocker failed to start"},
                {"success": True, "message": "Unlocker started successfully"}
            ]
            
            # First attempt - should fail
            result1 = await luna_core.start_unlocker()
            assert result1["success"] is False
            assert "Unlocker failed to start" in result1["message"]
            
            # Second attempt - should succeed
            result2 = await luna_core.start_unlocker()
            assert result2["success"] is True
            assert luna_core.unlocker_running is True
        
        # Test graceful shutdown even with errors
        with patch.object(luna_core, 'stop_injector') as mock_stop_injector:
            # Make stop_injector raise an exception
            mock_stop_injector.side_effect = Exception("Failed to stop injector")
            
            # Shutdown should complete without raising exceptions
            await luna_core.shutdown()
            
            # Verify stop_injector was called
            mock_stop_injector.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])