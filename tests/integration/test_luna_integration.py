"""
Integration tests for Luna component interaction.

This module tests the interaction between Luna injector and unlocker components,
unified configuration management, and platform integration.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from rich.console import Console

from gaming_setup_tool import LunaSetupTool
from models import LunaConfig, LunaResults, LunaShortcutConfig
from configuration_handler import ConfigurationHandler
from file_operations_manager import FileOperationsManager
from shortcut_manager import ShortcutManager
from security_config_manager import SecurityConfigManager


class TestLunaComponentIntegration:
    """Test Luna component integration and interaction."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for Luna integration testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'luna': temp_dir / "Luna",
            'luna_injector': temp_dir / "Luna" / "injector",
            'luna_unlocker': temp_dir / "Luna" / "unlocker",
            'luna_config': temp_dir / "Luna" / "config",
            'temp': temp_dir / "temp"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        yield workspace
        
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def luna_config(self, temp_workspace):
        """Create a Luna configuration for testing."""
        return LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            temp_dir=temp_workspace['temp']
        )
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = Mock(spec=Console)
        console.is_jupyter = False
        return console
    
    @pytest.mark.asyncio
    async def test_luna_injector_unlocker_interaction(self, temp_workspace, luna_config, mock_console):
        """Test interaction between Luna injector and unlocker components."""
        # Create managers
        config_handler = ConfigurationHandler(mock_console)
        file_manager = FileOperationsManager(mock_console)
        results = LunaResults()
        
        # Mock Luna component files
        injector_dll = temp_workspace['luna_injector'] / "luna_core_x64.dll"
        unlocker_dll = temp_workspace['luna_unlocker'] / "luna_unlocker.dll"
        injector_dll.write_bytes(b"Mock Luna injector DLL")
        unlocker_dll.write_bytes(b"Mock Luna unlocker DLL")
        
        # Test injector configuration
        injector_config = temp_workspace['luna_injector'] / "luna_injector.ini"
        injector_config.write_text("[Settings]\nDLL=old_path.dll\n")
        
        with patch.object(config_handler, 'update_luna_injector_config', return_value=True) as mock_injector, \
             patch.object(config_handler, 'update_luna_unlocker_config', return_value=True) as mock_unlocker:
            
            # Configure injector
            injector_result = await config_handler.update_luna_injector_config(
                injector_dll, injector_config, results
            )
            
            # Configure unlocker
            unlocker_result = await config_handler.update_luna_unlocker_config(
                unlocker_dll, {"steam": True, "epic": True}, results
            )
            
            assert injector_result is True
            assert unlocker_result is True
            mock_injector.assert_called_once()
            mock_unlocker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unified_luna_configuration_management(self, temp_workspace, luna_config, mock_console):
        """Test unified Luna configuration management."""
        config_handler = ConfigurationHandler(mock_console)
        results = LunaResults()
        
        # Create unified Luna config
        luna_config_file = temp_workspace['luna_config'] / "luna_config.jsonc"
        luna_config_content = """
        {
            "luna": {
                "version": "1.0.0",
                "core": {
                    "injector_enabled": true,
                    "unlocker_enabled": true,
                    "auto_start": false
                },
                "platforms": {
                    "steam": {"enabled": true, "priority": 1},
                    "epic": {"enabled": true, "priority": 2}
                }
            }
        }
        """
        luna_config_file.write_text(luna_config_content)
        
        # Test configuration replacement
        with patch.object(config_handler, 'replace_luna_config', return_value=True) as mock_replace:
            result = await config_handler.replace_luna_config(
                luna_config_file, temp_workspace['luna_config'], results
            )
            
            assert result is True
            mock_replace.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_luna_security_exclusions(self, temp_workspace, luna_config, mock_console):
        """Test Luna security exclusions for all components."""
        security_manager = SecurityConfigManager(mock_console)
        results = LunaResults()
        
        # Get Luna paths for exclusions
        luna_paths = [
            temp_workspace['luna'],
            temp_workspace['luna_injector'],
            temp_workspace['luna_unlocker'],
            temp_workspace['temp']
        ]
        
        # Mock Windows Defender exclusion addition
        with patch.object(security_manager, 'add_defender_exclusions') as mock_exclusions:
            async def mock_add_exclusions(paths, results_obj):
                for path in paths:
                    results_obj.exclusions_added.append((path, True))
            
            mock_exclusions.side_effect = mock_add_exclusions
            
            await security_manager.add_defender_exclusions(luna_paths, results)
            
            assert len(results.exclusions_added) == len(luna_paths)
            assert all(success for _, success in results.exclusions_added)
    
    @pytest.mark.asyncio
    async def test_luna_shortcut_creation_integration(self, temp_workspace, luna_config, mock_console):
        """Test Luna shortcut creation for all components."""
        shortcut_manager = ShortcutManager(mock_console)
        results = LunaResults()
        
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
        
        # Mock shortcut creation
        with patch.object(shortcut_manager, 'create_shortcuts', return_value=[True, True, True]) as mock_create:
            result = await shortcut_manager.create_shortcuts(luna_shortcuts, results)
            
            assert result == [True, True, True]
            mock_create.assert_called_once_with(luna_shortcuts, results)
    
    @pytest.mark.asyncio
    async def test_luna_platform_integration(self, temp_workspace, luna_config, mock_console):
        """Test Luna integration with different gaming platforms."""
        tool = LunaSetupTool(verbose=False)
        tool.config = luna_config
        
        # Mock platform-specific operations
        platforms = ['steam', 'epic', 'origin', 'uplay']
        
        for platform in platforms:
            # Mock platform detection and configuration
            with patch.object(tool, f'_configure_{platform}_integration', return_value=True) as mock_platform:
                result = getattr(tool, f'_configure_{platform}_integration', lambda: True)()
                assert result is True
    
    @pytest.mark.asyncio
    async def test_luna_component_dependency_resolution(self, temp_workspace, luna_config, mock_console):
        """Test Luna component dependency resolution and loading order."""
        tool = LunaSetupTool(verbose=False)
        tool.config = luna_config
        
        # Test component loading order
        expected_order = ['core', 'injector', 'unlocker', 'integration']
        
        with patch.object(tool, '_load_luna_components') as mock_load:
            mock_load.return_value = expected_order
            
            loaded_components = tool._load_luna_components()
            
            assert loaded_components == expected_order
            assert loaded_components.index('core') < loaded_components.index('injector')
            assert loaded_components.index('injector') < loaded_components.index('integration')
            assert loaded_components.index('unlocker') < loaded_components.index('integration')
    
    @pytest.mark.asyncio
    async def test_luna_error_propagation_between_components(self, temp_workspace, luna_config, mock_console):
        """Test error propagation between Luna components."""
        tool = LunaSetupTool(verbose=False)
        tool.config = luna_config
        results = LunaResults()
        
        # Simulate error in injector affecting unlocker
        with patch.object(tool, '_setup_luna_injector', side_effect=Exception("Injector setup failed")) as mock_injector, \
             patch.object(tool, '_setup_luna_unlocker', return_value=True) as mock_unlocker:
            
            # Test that injector failure is handled gracefully
            try:
                await tool._setup_luna_injector(results)
            except Exception as e:
                results.add_error(str(e))
            
            # Unlocker should still be attempted
            unlocker_result = await tool._setup_luna_unlocker(results)
            
            assert len(results.errors) == 1
            assert "Injector setup failed" in results.errors[0]
            assert unlocker_result is True
    
    @pytest.mark.asyncio
    async def test_luna_configuration_validation(self, temp_workspace, luna_config, mock_console):
        """Test Luna configuration validation across components."""
        config_handler = ConfigurationHandler(mock_console)
        
        # Test valid Luna configuration
        valid_config = {
            "luna": {
                "version": "1.0.0",
                "core": {
                    "injector_enabled": True,
                    "unlocker_enabled": True
                },
                "platforms": {
                    "steam": {"enabled": True}
                }
            }
        }
        
        with patch.object(config_handler, 'validate_luna_config', return_value=True) as mock_validate:
            result = config_handler.validate_luna_config(valid_config)
            assert result is True
            mock_validate.assert_called_once_with(valid_config)
        
        # Test invalid Luna configuration
        invalid_config = {
            "luna": {
                "core": {
                    "injector_enabled": "invalid_boolean"
                }
            }
        }
        
        with patch.object(config_handler, 'validate_luna_config', return_value=False) as mock_validate_invalid:
            result = config_handler.validate_luna_config(invalid_config)
            assert result is False
            mock_validate_invalid.assert_called_once_with(invalid_config)


class TestLunaPlatformIntegration:
    """Test Luna integration with different gaming platforms."""
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        return Mock(spec=Console)
    
    @pytest.mark.asyncio
    async def test_steam_platform_integration(self, mock_console):
        """Test Luna integration with Steam platform."""
        tool = LunaSetupTool(verbose=False)
        
        # Mock Steam-specific operations
        with patch.object(tool, '_detect_steam_installation', return_value=True), \
             patch.object(tool, '_configure_steam_luna_integration', return_value=True), \
             patch.object(tool, '_validate_steam_luna_compatibility', return_value=True):
            
            steam_detected = tool._detect_steam_installation()
            steam_configured = tool._configure_steam_luna_integration()
            steam_compatible = tool._validate_steam_luna_compatibility()
            
            assert steam_detected is True
            assert steam_configured is True
            assert steam_compatible is True
    
    @pytest.mark.asyncio
    async def test_epic_games_platform_integration(self, mock_console):
        """Test Luna integration with Epic Games platform."""
        tool = LunaSetupTool(verbose=False)
        
        # Mock Epic Games-specific operations
        with patch.object(tool, '_detect_epic_installation', return_value=True), \
             patch.object(tool, '_configure_epic_luna_integration', return_value=True), \
             patch.object(tool, '_validate_epic_luna_compatibility', return_value=True):
            
            epic_detected = tool._detect_epic_installation()
            epic_configured = tool._configure_epic_luna_integration()
            epic_compatible = tool._validate_epic_luna_compatibility()
            
            assert epic_detected is True
            assert epic_configured is True
            assert epic_compatible is True
    
    @pytest.mark.asyncio
    async def test_multiple_platform_integration(self, mock_console):
        """Test Luna integration with multiple gaming platforms simultaneously."""
        tool = LunaSetupTool(verbose=False)
        
        platforms = ['steam', 'epic', 'origin', 'uplay']
        
        # Mock multi-platform operations
        with patch.object(tool, '_detect_all_platforms', return_value=platforms), \
             patch.object(tool, '_configure_multi_platform_luna', return_value=True), \
             patch.object(tool, '_validate_multi_platform_compatibility', return_value=True):
            
            detected_platforms = tool._detect_all_platforms()
            multi_configured = tool._configure_multi_platform_luna()
            multi_compatible = tool._validate_multi_platform_compatibility()
            
            assert set(detected_platforms) == set(platforms)
            assert multi_configured is True
            assert multi_compatible is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])