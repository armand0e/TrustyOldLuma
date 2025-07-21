"""
Unit tests for the Luna Gaming Tool data models.

This module contains comprehensive tests for all Luna data model classes
including LunaConfig, LunaResults, and LunaShortcutConfig.
"""

import os
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from luna.models.models import LunaConfig, LunaResults, LunaShortcutConfig


class TestLunaConfig:
    """Test cases for LunaConfig dataclass."""
    
    def test_luna_config_initialization(self):
        """Test basic LunaConfig initialization."""
        config = LunaConfig(
            luna_core_path=Path("/test/luna").resolve(),
            luna_config_path=Path("/test/luna/config").resolve(),
            download_url="https://example.com/download.exe",
            app_id="480"
        )
        
        assert config.luna_core_path == Path("/test/luna").resolve()
        assert config.luna_config_path == Path("/test/luna/config").resolve()
        assert config.download_url == "https://example.com/download.exe"
        assert config.app_id == "480"
        assert config.verbose_logging is False
    
    def test_luna_config_with_optional_params(self):
        """Test LunaConfig initialization with optional parameters."""
        temp_dir = Path("/test/temp").resolve()
        docs_path = Path("/test/docs").resolve()
        
        config = LunaConfig(
            luna_core_path=Path("/test/luna").resolve(),
            luna_config_path=Path("/test/luna/config").resolve(),
            download_url="https://example.com/download.exe",
            app_id="480",
            verbose_logging=True,
            documents_path=docs_path,
            temp_dir=temp_dir,
            legacy_greenluma_path=Path("/test/legacy/greenluma").resolve(),
            legacy_koalageddon_path=Path("/test/legacy/koalageddon").resolve()
        )
        
        assert config.verbose_logging is True
        assert config.documents_path == docs_path
        assert config.temp_dir == temp_dir
        assert config.legacy_greenluma_path == Path("/test/legacy/greenluma").resolve()
        assert config.legacy_koalageddon_path == Path("/test/legacy/koalageddon").resolve()
    
    def test_luna_config_path_validation(self):
        """Test that LunaConfig validates paths are absolute."""
        with pytest.raises(ValueError, match="Luna core path must be absolute"):
            LunaConfig(
                luna_core_path=Path("relative/path"),
                luna_config_path=Path("/test/luna/config").resolve(),
                download_url="https://example.com/download.exe",
                app_id="480"
            )
    
    def test_luna_config_url_validation(self):
        """Test that LunaConfig validates URL format."""
        with pytest.raises(ValueError, match="Invalid download URL format"):
            LunaConfig(
                luna_core_path=Path("/test/luna").resolve(),
                luna_config_path=Path("/test/luna/config").resolve(),
                download_url="not-a-valid-url",
                app_id="480"
            )
    
    def test_luna_config_app_id_validation(self):
        """Test that LunaConfig validates app ID format."""
        with pytest.raises(ValueError, match="App ID must be a non-empty numeric string"):
            LunaConfig(
                luna_core_path=Path("/test/luna").resolve(),
                luna_config_path=Path("/test/luna/config").resolve(),
                download_url="https://example.com/download.exe",
                app_id="not-numeric"
            )
        
        with pytest.raises(ValueError, match="App ID must be a non-empty numeric string"):
            LunaConfig(
                luna_core_path=Path("/test/luna").resolve(),
                luna_config_path=Path("/test/luna/config").resolve(),
                download_url="https://example.com/download.exe",
                app_id=""
            )
    
    @patch.dict(os.environ, {'HOME': str(Path.cwd())}, clear=True)
    def test_from_environment_defaults(self):
        """Test LunaConfig.from_environment with default values."""
        with patch('pathlib.Path.home', return_value=Path.cwd()):
            config = LunaConfig.from_environment()
            
            # Check that paths are set to expected defaults
            assert config.luna_core_path == Path.cwd() / "Documents" / "Luna"
            assert config.app_id == "480"
            assert config.download_url == "https://github.com/acidicoala/Koalageddon/releases/latest/download/Koalageddon.exe"
            assert config.verbose_logging is False
    
    @patch.dict(os.environ, {
        'LUNA_CORE_PATH': str(Path.cwd() / 'custom' / 'luna'),
        'LUNA_CONFIG_PATH': str(Path.cwd() / 'custom' / 'luna' / 'config'),
        'DOCUMENTS_PATH': str(Path.cwd() / 'custom' / 'documents'),
        'DEFAULT_APP_ID': '123',
        'VERBOSE_LOGGING': 'true',
        'TEMP_DIR': str(Path.cwd() / 'custom' / 'temp')
    })
    def test_from_environment_with_env_vars(self):
        """Test LunaConfig.from_environment with environment variables."""
        config = LunaConfig.from_environment()
        
        assert config.luna_core_path == Path.cwd() / 'custom' / 'luna'
        assert config.luna_config_path == Path.cwd() / 'custom' / 'luna' / 'config'
        assert config.documents_path == Path.cwd() / 'custom' / 'documents'
        assert config.app_id == "123"
        assert config.verbose_logging is True
        assert config.temp_dir == Path.cwd() / 'custom' / 'temp'
    
    def test_from_environment_with_overrides(self):
        """Test LunaConfig.from_environment with parameter overrides."""
        config = LunaConfig.from_environment(
            app_id="999",
            verbose_logging=True
        )
        
        assert config.app_id == "999"
        assert config.verbose_logging is True
    
    def test_resolve_relative_paths(self):
        """Test resolving relative paths to absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create a config with absolute paths first, then modify to test resolution
            config = LunaConfig(
                luna_core_path=base_path / "absolute" / "luna",
                luna_config_path=base_path / "relative" / "config",
                download_url="https://example.com/download.exe",
                app_id="480",
                temp_dir=base_path / "relative" / "temp"
            )
            
            # Manually set some paths to relative for testing
            config.luna_config_path = Path("relative/config")
            config.temp_dir = Path("relative/temp")
            
            config.resolve_relative_paths(base_path)
            
            # Absolute path should remain unchanged
            assert config.luna_core_path == base_path / "absolute" / "luna"
            
            # Relative paths should be resolved
            assert config.luna_config_path == (base_path / "relative/config").resolve()
            assert config.temp_dir == (base_path / "relative/temp").resolve()
    
    def test_get_security_exclusion_paths(self):
        """Test getting security exclusion paths."""
        config = LunaConfig(
            luna_core_path=Path("/test/luna").resolve(),
            luna_config_path=Path("/test/luna/config").resolve(),
            download_url="https://example.com/download.exe",
            app_id="480",
            temp_dir=Path("/test/temp").resolve()
        )
        
        exclusion_paths = config.get_security_exclusion_paths()
        
        assert len(exclusion_paths) >= 2
        assert config.luna_core_path in exclusion_paths
        assert config.temp_dir in exclusion_paths
    
    def test_from_legacy_configs(self):
        """Test creating LunaConfig from legacy configurations."""
        greenluma_path = Path("/test/legacy/greenluma").resolve()
        koalageddon_path = Path("/test/legacy/koalageddon").resolve()
        
        config = LunaConfig.from_legacy_configs(
            greenluma_path=greenluma_path,
            koalageddon_path=koalageddon_path,
            app_id="480"
        )
        
        assert config.legacy_greenluma_path == greenluma_path
        assert config.legacy_koalageddon_path == koalageddon_path
        assert config.luna_core_path == Path.home() / "Documents" / "Luna"
        assert config.app_id == "480"


class TestLunaResults:
    """Test cases for LunaResults dataclass."""
    
    def test_luna_results_initialization(self):
        """Test basic LunaResults initialization."""
        results = LunaResults()
        
        assert results.directories_created == []
        assert results.exclusions_added == []
        assert results.files_extracted is False
        assert results.files_downloaded == []
        assert results.configs_updated == []
        assert results.shortcuts_created == []
        assert results.legacy_installations_found == []
        assert results.configurations_migrated == []
        assert results.shortcuts_updated == []
        assert results.components_installed == []
        assert results.luna_shortcuts_created == []
        assert results.errors == []
        assert results.warnings == []
        assert results.start_time is None
        assert results.end_time is None
    
    def test_success_rate_no_operations(self):
        """Test success rate calculation with no operations."""
        results = LunaResults()
        assert results.success_rate == 1.0
    
    def test_success_rate_all_successful(self):
        """Test success rate calculation with all successful operations."""
        results = LunaResults(
            directories_created=[Path("/test1"), Path("/test2")],
            exclusions_added=[
                (Path("/test1"), True),
                (Path("/test2"), True)
            ],
            files_downloaded=[
                ("file1.exe", True),
                ("file2.exe", True)
            ],
            configs_updated=[
                ("config1.ini", True)
            ],
            shortcuts_created=[
                ("Luna Shortcut1", True)
            ],
            configurations_migrated=[
                ("greenluma_config", True),
                ("koalageddon_config", True)
            ],
            components_installed=[
                ("luna_injector", True),
                ("luna_unlocker", True)
            ]
        )
        results.files_extracted = True
        results.mark_extraction_attempted()
        
        assert results.success_rate == 1.0
    
    def test_success_rate_partial_success(self):
        """Test success rate calculation with partial success."""
        results = LunaResults(
            directories_created=[Path("/test1")],  # 1 successful
            exclusions_added=[
                (Path("/test1"), True),   # 1 successful
                (Path("/test2"), False)   # 1 failed
            ],
            files_downloaded=[
                ("file1.exe", True),      # 1 successful
                ("file2.exe", False)      # 1 failed
            ],
            configurations_migrated=[
                ("greenluma_config", True),   # 1 successful
                ("koalageddon_config", False) # 1 failed
            ]
        )
        
        # Total: 7 operations, 4 successful
        # Success rate: 4/7 ≈ 0.571
        assert abs(results.success_rate - (4/7)) < 0.001
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        results = LunaResults()
        
        # No timing recorded
        assert results.duration is None
        
        # With timing
        results.start_time = 100.0
        results.end_time = 105.5
        assert results.duration == 5.5
    
    def test_has_errors_and_warnings(self):
        """Test error and warning detection."""
        results = LunaResults()
        
        assert results.has_errors is False
        assert results.has_warnings is False
        
        results.add_error("Luna test error")
        assert results.has_errors is True
        
        results.add_warning("Luna test warning")
        assert results.has_warnings is True
        
        assert len(results.errors) == 1
        assert len(results.warnings) == 1
        assert "Luna test error" in results.errors
        assert "Luna test warning" in results.warnings
    
    def test_get_summary(self):
        """Test getting Luna results summary."""
        results = LunaResults(
            directories_created=[Path("/test1"), Path("/test2")],
            exclusions_added=[
                (Path("/test1"), True),
                (Path("/test2"), False)
            ],
            files_downloaded=[("luna_file.exe", True)],
            configs_updated=[("luna_config.jsonc", True)],
            shortcuts_created=[("Luna Shortcut1", False)],
            configurations_migrated=[("greenluma_config", True)],
            components_installed=[("luna_injector", True), ("luna_unlocker", False)],
            errors=["Luna Error 1"],
            warnings=["Luna Warning 1", "Luna Warning 2"]
        )
        results.files_extracted = True
        results.mark_extraction_attempted()
        results.start_time = 100.0
        results.end_time = 105.0
        
        summary = results.get_summary()
        
        assert summary['directories_created'] == 2
        assert summary['exclusions_successful'] == 1
        assert summary['exclusions_total'] == 2
        assert summary['files_extracted'] is True
        assert summary['downloads_successful'] == 1
        assert summary['downloads_total'] == 1
        assert summary['configs_successful'] == 1
        assert summary['configs_total'] == 1
        assert summary['shortcuts_successful'] == 0
        assert summary['shortcuts_total'] == 1
        assert summary['error_count'] == 1
        assert summary['warning_count'] == 2
        assert summary['duration'] == 5.0
        # Updated calculation includes migration and component operations
        expected_success_rate = (2 + 1 + 1 + 1 + 1 + 0 + 1 + 1) / (2 + 2 + 1 + 1 + 1 + 1 + 1 + 2)
        assert abs(summary['success_rate'] - expected_success_rate) < 0.001
    
    def test_migration_tracking(self):
        """Test Luna migration-specific result tracking."""
        results = LunaResults()
        
        # Test legacy installation tracking
        results.legacy_installations_found = ["GreenLuma", "Koalageddon"]
        assert len(results.legacy_installations_found) == 2
        assert "GreenLuma" in results.legacy_installations_found
        assert "Koalageddon" in results.legacy_installations_found
        
        # Test configuration migration tracking
        results.configurations_migrated = [
            ("greenluma_config", True),
            ("koalageddon_config", True),
            ("steam_config", False)
        ]
        assert len(results.configurations_migrated) == 3
        
        # Test shortcut update tracking
        results.shortcuts_updated = [
            ("GreenLuma Shortcut", True),
            ("Koalageddon Shortcut", False)
        ]
        assert len(results.shortcuts_updated) == 2
        
        # Test Luna component installation tracking
        results.components_installed = [
            ("luna_injector", True),
            ("luna_unlocker", True),
            ("luna_integration", True)
        ]
        assert len(results.components_installed) == 3


class TestLunaShortcutConfig:
    """Test cases for LunaShortcutConfig dataclass."""
    
    def test_luna_shortcut_config_initialization(self):
        """Test basic LunaShortcutConfig initialization."""
        config = LunaShortcutConfig(
            name="Injector",
            component="injector",
            target_path=Path("/test/luna_injector.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        
        assert config.name == "Injector"
        assert config.component == "injector"
        assert config.target_path == Path("/test/luna_injector.exe").resolve()
        assert config.working_directory == Path("/test").resolve()
        assert config.icon_path is None
        assert config.description is None
        assert config.luna_branding is True
    
    def test_luna_shortcut_config_with_optional_params(self):
        """Test LunaShortcutConfig initialization with optional parameters."""
        config = LunaShortcutConfig(
            name="Unlocker",
            component="unlocker",
            target_path=Path("/test/luna_unlocker.exe").resolve(),
            working_directory=Path("/test").resolve(),
            icon_path=Path("/test/luna_icon.ico").resolve(),
            description="Luna DLC Unlocker",
            luna_branding=False
        )
        
        assert config.icon_path == Path("/test/luna_icon.ico").resolve()
        assert config.description == "Luna DLC Unlocker"
        assert config.luna_branding is False
    
    def test_luna_shortcut_config_name_validation(self):
        """Test that LunaShortcutConfig validates shortcut names."""
        with pytest.raises(ValueError, match="Shortcut name cannot be empty"):
            LunaShortcutConfig(
                name="",
                component="injector",
                target_path=Path("/test/luna_target.exe").resolve(),
                working_directory=Path("/test").resolve()
            )
        
        with pytest.raises(ValueError, match="Shortcut name contains invalid characters"):
            LunaShortcutConfig(
                name="Luna<>Shortcut",
                component="injector",
                target_path=Path("/test/luna_target.exe").resolve(),
                working_directory=Path("/test").resolve()
            )
    
    def test_luna_shortcut_config_path_validation(self):
        """Test that LunaShortcutConfig validates paths are absolute."""
        with pytest.raises(ValueError, match="Target path must be absolute"):
            LunaShortcutConfig(
                name="Luna Shortcut",
                component="injector",
                target_path=Path("relative/luna_target.exe"),
                working_directory=Path("/test").resolve()
            )
        
        with pytest.raises(ValueError, match="Working directory must be absolute"):
            LunaShortcutConfig(
                name="Luna Shortcut",
                component="injector",
                target_path=Path("/test/luna_target.exe").resolve(),
                working_directory=Path("relative/dir")
            )
        
        with pytest.raises(ValueError, match="Icon path must be absolute"):
            LunaShortcutConfig(
                name="Luna Shortcut",
                component="injector",
                target_path=Path("/test/luna_target.exe").resolve(),
                working_directory=Path("/test").resolve(),
                icon_path=Path("relative/luna_icon.ico")
            )
    
    def test_desktop_path_property(self):
        """Test desktop path property with Luna branding."""
        config = LunaShortcutConfig(
            name="Injector",
            component="injector",
            target_path=Path("/test/luna_injector.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        
        desktop_path = config.desktop_path
        assert desktop_path.parent == Path.home() / "Desktop"
        
        if os.name == 'nt':  # Windows
            assert desktop_path.name == "Luna Injector.lnk"
        else:  # Unix-like systems
            assert desktop_path.name == "Luna Injector.desktop"
    
    def test_resolve_relative_paths(self):
        """Test resolving relative paths to absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create config with absolute paths first, then modify to test resolution
            config = LunaShortcutConfig(
                name="Manager",
                component="manager",
                target_path=base_path / "absolute" / "luna_manager.exe",
                working_directory=base_path / "relative" / "dir",
                icon_path=base_path / "relative" / "luna_icon.ico"
            )
            
            # Manually set some paths to relative for testing
            config.working_directory = Path("relative/dir")
            config.icon_path = Path("relative/luna_icon.ico")
            
            config.resolve_relative_paths(base_path)
            
            # Absolute path should remain unchanged
            assert config.target_path == base_path / "absolute" / "luna_manager.exe"
            
            # Relative paths should be resolved
            assert config.working_directory == (base_path / "relative/dir").resolve()
            assert config.icon_path == (base_path / "relative/luna_icon.ico").resolve()
    
    def test_to_dict_and_from_dict(self):
        """Test converting Luna shortcut config to/from dictionary."""
        original_config = LunaShortcutConfig(
            name="Settings",
            component="settings",
            target_path=Path("/test/luna_settings.exe").resolve(),
            working_directory=Path("/test").resolve(),
            icon_path=Path("/test/luna_icon.ico").resolve(),
            description="Luna Settings Manager"
        )
        
        # Convert to dict
        config_dict = original_config.to_dict()
        
        assert config_dict['name'] == "Settings"
        assert config_dict['component'] == "settings"
        assert config_dict['target_path'] == str(Path("/test/luna_settings.exe").resolve())
        assert config_dict['working_directory'] == str(Path("/test").resolve())
        assert config_dict['icon_path'] == str(Path("/test/luna_icon.ico").resolve())
        assert config_dict['description'] == "Luna Settings Manager"
        assert config_dict['luna_branding'] is True
        assert 'desktop_path' in config_dict
        
        # Convert back from dict
        restored_config = LunaShortcutConfig.from_dict(config_dict)
        
        assert restored_config.name == original_config.name
        assert restored_config.component == original_config.component
        assert restored_config.target_path == original_config.target_path
        assert restored_config.working_directory == original_config.working_directory
        assert restored_config.icon_path == original_config.icon_path
        assert restored_config.description == original_config.description
        assert restored_config.luna_branding == original_config.luna_branding
    
    def test_to_dict_with_none_values(self):
        """Test converting Luna shortcut config to dict with None values."""
        config = LunaShortcutConfig(
            name="Basic",
            component="basic",
            target_path=Path("/test/luna_basic.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['icon_path'] is None
        assert config_dict['description'] is None
        assert config_dict['component'] == "basic"
        assert config_dict['luna_branding'] is True
        
        # Test from_dict with None values
        restored_config = LunaShortcutConfig.from_dict(config_dict)
        assert restored_config.icon_path is None
        assert restored_config.description is None
        assert restored_config.component == "basic"
        assert restored_config.luna_branding is True
    
    def test_display_name_property(self):
        """Test display name property with Luna branding."""
        # Test with Luna branding enabled
        config_with_branding = LunaShortcutConfig(
            name="Injector",
            component="injector",
            target_path=Path("/test/luna_injector.exe").resolve(),
            working_directory=Path("/test").resolve(),
            luna_branding=True
        )
        assert config_with_branding.display_name == "Luna Injector"
        
        # Test with Luna branding disabled
        config_without_branding = LunaShortcutConfig(
            name="Injector",
            component="injector",
            target_path=Path("/test/luna_injector.exe").resolve(),
            working_directory=Path("/test").resolve(),
            luna_branding=False
        )
        assert config_without_branding.display_name == "Injector"
    
    def test_luna_description_property(self):
        """Test Luna description property."""
        config = LunaShortcutConfig(
            name="Unlocker",
            component="unlocker",
            target_path=Path("/test/luna_unlocker.exe").resolve(),
            working_directory=Path("/test").resolve(),
            description="DLC Unlocker"
        )
        assert config.luna_description == "DLC Unlocker - Unified Gaming Tool"
        
        # Test with no description
        config_no_desc = LunaShortcutConfig(
            name="Manager",
            component="manager",
            target_path=Path("/test/luna_manager.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        assert config_no_desc.luna_description == "Luna Manager - Unified Gaming Tool"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])