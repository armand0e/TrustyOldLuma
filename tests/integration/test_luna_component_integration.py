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
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from rich.console import Console

try:
    from src.luna.core.luna_core import LunaCore
except ImportError:
    # Fallback for different import structure
    from luna.core.luna_core import LunaCore
try:
    from src.luna.models.models import LunaConfig, LunaResults, LunaShortcutConfig
except ImportError:
    # Fallback for different import structure
    from models import LunaConfig, LunaResults, LunaShortcutConfig
try:
    from src.luna.managers.configuration_handler import ConfigurationHandler
    from src.luna.managers.file_operations_manager import FileOperationsManager
    from src.luna.managers.shortcut_manager import ShortcutManager
    from src.luna.managers.security_config_manager import SecurityConfigManager
except ImportError:
    # Fallback for different import structure
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
    def luna_core(self, luna_config_file):
        """Create a Luna core instance for testing."""
        core = LunaCore(luna_config_file)
        return core
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = Mock(spec=Console)
        console.is_jupyter = False
        return console
    
    @pytest.mark.asyncio
    async def test_luna_core_initialization(self, luna_core):
        """Test Luna core initialization."""
        # Initialize Luna core
        result = await luna_core.initialize()
        
        # Verify initialization was successful
        assert result is True
        assert luna_core.config is not None
        assert "luna" in luna_core.config
        assert "core" in luna_core.config["luna"]
        assert "platforms" in luna_core.config["luna"]
    
    @pytest.mark.asyncio
    async def test_luna_config_loading(self, luna_core):
        """Test Luna configuration loading."""
        # Load configuration
        config = await luna_core.load_config()
        
        # Verify configuration was loaded correctly
        assert config is not None
        assert "luna" in config
        assert "core" in config["luna"]
        assert "platforms" in config["luna"]
        assert config["luna"]["core"]["injector_enabled"] is True
        assert config["luna"]["core"]["unlocker_enabled"] is True
        assert config["luna"]["platforms"]["steam"]["enabled"] is True
        assert config["luna"]["platforms"]["epic"]["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_luna_config_update(self, luna_core):
        """Test Luna configuration update."""
        # Load initial configuration
        await luna_core.load_config()
        
        # Update configuration
        update_result = await luna_core.update_config({
            "injector_enabled": False,
            "unlocker_enabled": True,
            "platforms": {
                "steam": {"enabled": False, "priority": 1},
                "epic": {"enabled": True, "priority": 2}
            }
        })
        
        # Verify update was successful
        assert update_result["success"] is True
        
        # Reload configuration to verify changes were saved
        await luna_core.load_config()
        
        # Verify configuration was updated correctly
        assert luna_core.config["luna"]["core"]["injector_enabled"] is False
        assert luna_core.config["luna"]["core"]["unlocker_enabled"] is True
        assert luna_core.config["luna"]["platforms"]["steam"]["enabled"] is False
        assert luna_core.config["luna"]["platforms"]["epic"]["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_luna_injector_unlocker_interaction(self, luna_core):
        """Test interaction between Luna injector and unlocker components."""
        # Initialize Luna core
        await luna_core.initialize()
        
        # Start injector
        injector_result = await luna_core.start_injector()
        
        # Verify injector was started successfully
        assert injector_result["success"] is True
        assert luna_core.injector_running is True
        
        # Start unlocker
        unlocker_result = await luna_core.start_unlocker()
        
        # Verify unlocker was started successfully
        assert unlocker_result["success"] is True
        assert luna_core.unlocker_running is True
        
        # Verify monitoring task is running
        assert luna_core.monitoring_task is not None
        assert not luna_core.monitoring_task.done()
        
        # Stop injector
        injector_stop_result = await luna_core.stop_injector()
        
        # Verify injector was stopped successfully
        assert injector_stop_result["success"] is True
        assert luna_core.injector_running is False
        
        # Verify monitoring task is still running (unlocker is still active)
        assert luna_core.monitoring_task is not None
        assert not luna_core.monitoring_task.done()
        
        # Stop unlocker
        unlocker_stop_result = await luna_core.stop_unlocker()
        
        # Verify unlocker was stopped successfully
        assert unlocker_stop_result["success"] is True
        assert luna_core.unlocker_running is False
        
        # Verify monitoring task is stopped (both components are inactive)
        await asyncio.sleep(0.1)  # Give time for monitoring task to stop
        assert luna_core.monitoring_task is None or luna_core.monitoring_task.done()
    
    @pytest.mark.asyncio
    async def test_luna_component_configuration_integration(self, luna_core):
        """Test Luna component configuration integration."""
        # Initialize Luna core
        await luna_core.initialize()
        
        # Configure and start injector with specific configuration
        injector_config = {
            "injector_enabled": True,
            "app_list": ["480", "570", "730"],  # Example Steam App IDs
            "auto_inject": True
        }
        
        injector_result = await luna_core.start_injector(injector_config)
        
        # Verify injector was started successfully with configuration
        assert injector_result["success"] is True
        assert luna_core.injector_running is True
        
        # Get updated configuration
        config = await luna_core.get_config()
        
        # Verify configuration was updated
        assert config["injector_enabled"] is True
        assert "480" in config["app_list"]
        assert "570" in config["app_list"]
        assert "730" in config["app_list"]
        assert config["auto_inject"] is True
        
        # Configure and start unlocker with specific configuration
        unlocker_config = {
            "unlocker_enabled": True,
            "unlock_dlc": True,
            "unlock_shared": True,
            "platforms": {
                "steam": {"enabled": True},
                "epic": {"enabled": True},
                "origin": {"enabled": True},
                "uplay": {"enabled": False}
            }
        }
        
        unlocker_result = await luna_core.start_unlocker(unlocker_config)
        
        # Verify unlocker was started successfully with configuration
        assert unlocker_result["success"] is True
        assert luna_core.unlocker_running is True
        
        # Get updated configuration
        config = await luna_core.get_config()
        
        # Verify configuration was updated
        assert config["unlocker_enabled"] is True
        assert config["unlock_dlc"] is True
        assert config["unlock_shared"] is True
        assert config["platforms"]["steam"]["enabled"] is True
        assert config["platforms"]["epic"]["enabled"] is True
        assert config["platforms"]["origin"]["enabled"] is True
        assert config["platforms"]["uplay"]["enabled"] is False
        
        # Shutdown Luna core
        await luna_core.shutdown()
        
        # Verify components are stopped
        assert luna_core.injector_running is False
        assert luna_core.unlocker_running is False
        assert luna_core.monitoring_task is None or luna_core.monitoring_task.done()


class TestLunaConfigurationMigration:
    """Test Luna configuration migration from legacy installations."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with legacy installations."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'luna': temp_dir / "Luna",
            'luna_config': temp_dir / "Luna" / "config",
            'greenluma': temp_dir / "Documents" / "GreenLuma",
            'koalageddon': temp_dir / "Koalageddon",
            'temp': temp_dir / "temp"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        # Create legacy GreenLuma configuration
        greenluma_config = workspace['greenluma'] / "DLLInjector.ini"
        greenluma_config.write_text(
            "[Settings]\n"
            "DLL=GreenLuma_2020_x64.dll\n"
            "Timeout=30\n"
            "ProcessName=steam.exe\n"
        )
        
        # Create legacy Koalageddon configuration
        koalageddon_config = workspace['koalageddon'] / "Config.jsonc"
        koalageddon_config.write_text(
            '{\n'
            '  "EnableSteam": true,\n'
            '  "EnableEpic": true,\n'
            '  "EnableOrigin": false,\n'
            '  "EnableUplay": false,\n'
            '  "LogLevel": "Info"\n'
            '}\n'
        )
        
        # Create AppList entries
        applist_dir = workspace['greenluma'] / "AppList"
        applist_dir.mkdir(exist_ok=True)
        (applist_dir / "0.txt").write_text("480")  # Spacewar
        (applist_dir / "1.txt").write_text("570")  # Dota 2
        
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
                    "epic": {"enabled": False, "priority": 2},
                    "origin": {"enabled": False, "priority": 3},
                    "uplay": {"enabled": False, "priority": 4}
                },
                "paths": {
                    "core_directory": str(temp_workspace['luna']),
                    "config_directory": str(temp_workspace['luna_config']),
                    "temp_directory": str(temp_workspace['temp'])
                },
                "migration": {
                    "auto_detect_legacy": True,
                    "migrate_greenluma": True,
                    "migrate_koalageddon": True,
                    "preserve_legacy": False,
                    "backup_before_migration": True,
                    "legacy_paths": {
                        "greenluma_default": str(temp_workspace['greenluma']),
                        "koalageddon_default": str(temp_workspace['koalageddon'])
                    }
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_content, f, indent=2)
        
        return config_file
    
    @pytest.fixture
    def luna_core(self, luna_config_file):
        """Create a Luna core instance for testing."""
        core = LunaCore(luna_config_file)
        return core
    
    @pytest.mark.asyncio
    async def test_luna_legacy_migration(self, luna_core, temp_workspace):
        """Test migration from legacy GreenLuma and Koalageddon installations."""
        # Initialize Luna core
        await luna_core.initialize()
        
        # Mock migration process
        with patch.object(luna_core, 'migrate_config', wraps=luna_core.migrate_config) as mock_migrate:
            # Perform migration
            migration_result = await luna_core.migrate_config()
            
            # Verify migration was successful
            assert migration_result["success"] is True
            mock_migrate.assert_called_once()
            
            # Verify configuration was updated with migrated settings
            config = await luna_core.get_config()
            
            # These assertions would be more specific in a real implementation
            # Here we're just checking that the migration function was called
            assert config is not None


class TestLunaPlatformIntegration:
    """Test Luna integration with different gaming platforms."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for platform integration testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'luna': temp_dir / "Luna",
            'luna_config': temp_dir / "Luna" / "config",
            'steam': temp_dir / "Steam",
            'epic': temp_dir / "Epic Games",
            'origin': temp_dir / "Origin",
            'uplay': temp_dir / "Ubisoft",
            'temp': temp_dir / "temp"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        # Create mock platform executables
        (workspace['steam'] / "steam.exe").write_bytes(b"mock executable")
        (workspace['epic'] / "EpicGamesLauncher.exe").write_bytes(b"mock executable")
        (workspace['origin'] / "Origin.exe").write_bytes(b"mock executable")
        (workspace['uplay'] / "upc.exe").write_bytes(b"mock executable")
        
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
                    "steam": {
                        "enabled": True, 
                        "priority": 1,
                        "process": "steam.exe",
                        "path": str(temp_workspace['steam'])
                    },
                    "epic": {
                        "enabled": True, 
                        "priority": 2,
                        "process": "EpicGamesLauncher.exe",
                        "path": str(temp_workspace['epic'])
                    },
                    "origin": {
                        "enabled": True, 
                        "priority": 3,
                        "process": "Origin.exe",
                        "path": str(temp_workspace['origin'])
                    },
                    "uplay": {
                        "enabled": True, 
                        "priority": 4,
                        "process": "upc.exe",
                        "path": str(temp_workspace['uplay'])
                    }
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
    def luna_core(self, luna_config_file):
        """Create a Luna core instance for testing."""
        core = LunaCore(luna_config_file)
        return core
    
    @pytest.mark.asyncio
    async def test_luna_platform_detection(self, luna_core, temp_workspace):
        """Test Luna platform detection."""
        # Initialize Luna core
        await luna_core.initialize()
        
        # Get configuration with platform settings
        config = await luna_core.get_config()
        
        # Verify platform settings were loaded
        assert "platforms" in config
        assert "steam" in config["platforms"]
        assert "epic" in config["platforms"]
        assert "origin" in config["platforms"]
        assert "uplay" in config["platforms"]
        
        # Verify platform settings are correct
        assert config["platforms"]["steam"]["enabled"] is True
        assert config["platforms"]["epic"]["enabled"] is True
        assert config["platforms"]["origin"]["enabled"] is True
        assert config["platforms"]["uplay"]["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_luna_platform_configuration_update(self, luna_core):
        """Test Luna platform configuration update."""
        # Initialize Luna core
        await luna_core.initialize()
        
        # Update platform configuration
        update_result = await luna_core.update_config({
            "platforms": {
                "steam": {"enabled": True, "priority": 1},
                "epic": {"enabled": False, "priority": 2},
                "origin": {"enabled": True, "priority": 3},
                "uplay": {"enabled": False, "priority": 4}
            }
        })
        
        # Verify update was successful
        assert update_result["success"] is True
        
        # Get updated configuration
        config = await luna_core.get_config()
        
        # Verify platform settings were updated
        assert config["platforms"]["steam"]["enabled"] is True
        assert config["platforms"]["epic"]["enabled"] is False
        assert config["platforms"]["origin"]["enabled"] is True
        assert config["platforms"]["uplay"]["enabled"] is False


class TestLunaErrorHandlingAndRecovery:
    """Test Luna error handling and recovery scenarios."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for error handling testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'luna': temp_dir / "Luna",
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
                    "epic": {"enabled": True, "priority": 2}
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
    def luna_core(self, luna_config_file):
        """Create a Luna core instance for testing."""
        core = LunaCore(luna_config_file)
        return core
    
    @pytest.mark.asyncio
    async def test_luna_error_handling_invalid_config(self, temp_workspace):
        """Test Luna error handling with invalid configuration."""
        # Create invalid configuration file
        config_file = temp_workspace['luna_config'] / "invalid_config.jsonc"
        with open(config_file, 'w') as f:
            f.write("This is not valid JSON")
        
        # Create Luna core with invalid configuration
        core = LunaCore(config_file)
        
        # Initialize Luna core
        result = await core.initialize()
        
        # Verify initialization still succeeds with default configuration
        assert result is True
        
        # Verify default configuration was used
        assert core.config is not None
        assert "luna" in core.config
        assert "core" in core.config["luna"]
        assert "platforms" in core.config["luna"]
    
    @pytest.mark.asyncio
    async def test_luna_error_handling_missing_config(self, temp_workspace):
        """Test Luna error handling with missing configuration."""
        # Create Luna core with non-existent configuration file
        core = LunaCore(temp_workspace['luna_config'] / "nonexistent_config.jsonc")
        
        # Initialize Luna core
        result = await core.initialize()
        
        # Verify initialization still succeeds with default configuration
        assert result is True
        
        # Verify default configuration was used
        assert core.config is not None
        assert "luna" in core.config
        assert "core" in core.config["luna"]
        assert "platforms" in core.config["luna"]
    
    @pytest.mark.asyncio
    async def test_luna_component_error_recovery(self, luna_core):
        """Test Luna component error recovery."""
        # Initialize Luna core
        await luna_core.initialize()
        
        # Mock start_injector to fail
        original_start_injector = luna_core.start_injector
        
        async def mock_start_injector_fail(*args, **kwargs):
            return {"success": False, "message": "Injector failed to start"}
        
        luna_core.start_injector = mock_start_injector_fail
        
        # Try to start injector
        injector_result = await luna_core.start_injector()
        
        # Verify injector failed to start
        assert injector_result["success"] is False
        assert "Injector failed to start" in injector_result["message"]
        assert luna_core.injector_running is False
        
        # Restore original method
        luna_core.start_injector = original_start_injector
        
        # Start unlocker
        unlocker_result = await luna_core.start_unlocker()
        
        # Verify unlocker started successfully despite injector failure
        assert unlocker_result["success"] is True
        assert luna_core.unlocker_running is True
        
        # Verify monitoring task is running
        assert luna_core.monitoring_task is not None
        assert not luna_core.monitoring_task.done()
        
        # Shutdown Luna core
        await luna_core.shutdown()
        
        # Verify components are stopped
        assert luna_core.injector_running is False
        assert luna_core.unlocker_running is False
        assert luna_core.monitoring_task is None or luna_core.monitoring_task.done()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])