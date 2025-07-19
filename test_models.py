"""
Unit tests for the Gaming Setup Tool data models.

This module contains comprehensive tests for all data model classes
including SetupConfig, SetupResults, and ShortcutConfig.
"""

import os
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from models import SetupConfig, SetupResults, ShortcutConfig


class TestSetupConfig:
    """Test cases for SetupConfig dataclass."""
    
    def test_setup_config_initialization(self):
        """Test basic SetupConfig initialization."""
        config = SetupConfig(
            greenluma_path=Path("/test/greenluma").resolve(),
            koalageddon_path=Path("/test/koalageddon").resolve(),
            koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
            download_url="https://example.com/download.exe",
            app_id="480"
        )
        
        assert config.greenluma_path == Path("/test/greenluma").resolve()
        assert config.koalageddon_path == Path("/test/koalageddon").resolve()
        assert config.koalageddon_config_path == Path("/test/koalageddon/config").resolve()
        assert config.download_url == "https://example.com/download.exe"
        assert config.app_id == "480"
        assert config.verbose_logging is False
    
    def test_setup_config_with_optional_params(self):
        """Test SetupConfig initialization with optional parameters."""
        temp_dir = Path("/test/temp").resolve()
        docs_path = Path("/test/docs").resolve()
        
        config = SetupConfig(
            greenluma_path=Path("/test/greenluma").resolve(),
            koalageddon_path=Path("/test/koalageddon").resolve(),
            koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
            download_url="https://example.com/download.exe",
            app_id="480",
            verbose_logging=True,
            documents_path=docs_path,
            temp_dir=temp_dir
        )
        
        assert config.verbose_logging is True
        assert config.documents_path == docs_path
        assert config.temp_dir == temp_dir
    
    def test_setup_config_path_validation(self):
        """Test that SetupConfig validates paths are absolute."""
        with pytest.raises(ValueError, match="GreenLuma path must be absolute"):
            SetupConfig(
                greenluma_path=Path("relative/path"),
                koalageddon_path=Path("/test/koalageddon").resolve(),
                koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
                download_url="https://example.com/download.exe",
                app_id="480"
            )
    
    def test_setup_config_url_validation(self):
        """Test that SetupConfig validates URL format."""
        with pytest.raises(ValueError, match="Invalid download URL format"):
            SetupConfig(
                greenluma_path=Path("/test/greenluma").resolve(),
                koalageddon_path=Path("/test/koalageddon").resolve(),
                koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
                download_url="not-a-valid-url",
                app_id="480"
            )
    
    def test_setup_config_app_id_validation(self):
        """Test that SetupConfig validates app ID format."""
        with pytest.raises(ValueError, match="App ID must be a non-empty numeric string"):
            SetupConfig(
                greenluma_path=Path("/test/greenluma").resolve(),
                koalageddon_path=Path("/test/koalageddon").resolve(),
                koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
                download_url="https://example.com/download.exe",
                app_id="not-numeric"
            )
        
        with pytest.raises(ValueError, match="App ID must be a non-empty numeric string"):
            SetupConfig(
                greenluma_path=Path("/test/greenluma").resolve(),
                koalageddon_path=Path("/test/koalageddon").resolve(),
                koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
                download_url="https://example.com/download.exe",
                app_id=""
            )
    
    @patch.dict(os.environ, {'HOME': str(Path.cwd())}, clear=True)
    def test_from_environment_defaults(self):
        """Test SetupConfig.from_environment with default values."""
        with patch('pathlib.Path.home', return_value=Path.cwd()):
            config = SetupConfig.from_environment()
            
            # Check that paths are set to expected defaults
            assert config.greenluma_path == Path.cwd() / "Documents" / "GreenLuma"
            assert config.app_id == "480"
            assert config.download_url == "https://github.com/acidicoala/Koalageddon/releases/latest/download/Koalageddon.exe"
            assert config.verbose_logging is False
    
    @patch.dict(os.environ, {
        'GREENLUMA_PATH': str(Path.cwd() / 'custom' / 'greenluma'),
        'KOALAGEDDON_PATH': str(Path.cwd() / 'custom' / 'koalageddon'),
        'DOCUMENTS_PATH': str(Path.cwd() / 'custom' / 'documents'),
        'DEFAULT_APP_ID': '123',
        'VERBOSE_LOGGING': 'true',
        'TEMP_DIR': str(Path.cwd() / 'custom' / 'temp')
    })
    def test_from_environment_with_env_vars(self):
        """Test SetupConfig.from_environment with environment variables."""
        config = SetupConfig.from_environment()
        
        assert config.greenluma_path == Path.cwd() / 'custom' / 'greenluma'
        assert config.koalageddon_path == Path.cwd() / 'custom' / 'koalageddon'
        assert config.documents_path == Path.cwd() / 'custom' / 'documents'
        assert config.app_id == "123"
        assert config.verbose_logging is True
        assert config.temp_dir == Path.cwd() / 'custom' / 'temp'
    
    def test_from_environment_with_overrides(self):
        """Test SetupConfig.from_environment with parameter overrides."""
        config = SetupConfig.from_environment(
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
            config = SetupConfig(
                greenluma_path=base_path / "absolute" / "greenluma",
                koalageddon_path=base_path / "relative" / "koalageddon", 
                koalageddon_config_path=base_path / "relative" / "config",
                download_url="https://example.com/download.exe",
                app_id="480",
                temp_dir=base_path / "relative" / "temp"
            )
            
            # Manually set some paths to relative for testing
            config.koalageddon_path = Path("relative/koalageddon")
            config.koalageddon_config_path = Path("relative/config")
            config.temp_dir = Path("relative/temp")
            
            config.resolve_relative_paths(base_path)
            
            # Absolute path should remain unchanged
            assert config.greenluma_path == base_path / "absolute" / "greenluma"
            
            # Relative paths should be resolved
            assert config.koalageddon_path == (base_path / "relative/koalageddon").resolve()
            assert config.koalageddon_config_path == (base_path / "relative/config").resolve()
            assert config.temp_dir == (base_path / "relative/temp").resolve()
    
    def test_get_security_exclusion_paths(self):
        """Test getting security exclusion paths."""
        config = SetupConfig(
            greenluma_path=Path("/test/greenluma").resolve(),
            koalageddon_path=Path("/test/koalageddon").resolve(),
            koalageddon_config_path=Path("/test/koalageddon/config").resolve(),
            download_url="https://example.com/download.exe",
            app_id="480",
            temp_dir=Path("/test/temp").resolve()
        )
        
        exclusion_paths = config.get_security_exclusion_paths()
        
        assert len(exclusion_paths) == 3
        assert config.greenluma_path in exclusion_paths
        assert config.koalageddon_path in exclusion_paths
        assert config.temp_dir in exclusion_paths


class TestSetupResults:
    """Test cases for SetupResults dataclass."""
    
    def test_setup_results_initialization(self):
        """Test basic SetupResults initialization."""
        results = SetupResults()
        
        assert results.directories_created == []
        assert results.exclusions_added == []
        assert results.files_extracted is False
        assert results.files_downloaded == []
        assert results.configs_updated == []
        assert results.shortcuts_created == []
        assert results.errors == []
        assert results.warnings == []
        assert results.start_time is None
        assert results.end_time is None
    
    def test_success_rate_no_operations(self):
        """Test success rate calculation with no operations."""
        results = SetupResults()
        assert results.success_rate == 1.0
    
    def test_success_rate_all_successful(self):
        """Test success rate calculation with all successful operations."""
        results = SetupResults(
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
                ("Shortcut1", True)
            ]
        )
        results.files_extracted = True
        results.mark_extraction_attempted()
        
        assert results.success_rate == 1.0
    
    def test_success_rate_partial_success(self):
        """Test success rate calculation with partial success."""
        results = SetupResults(
            directories_created=[Path("/test1")],  # 1 successful
            exclusions_added=[
                (Path("/test1"), True),   # 1 successful
                (Path("/test2"), False)   # 1 failed
            ],
            files_downloaded=[
                ("file1.exe", True),      # 1 successful
                ("file2.exe", False)      # 1 failed
            ]
        )
        
        # Total: 5 operations, 3 successful
        # Success rate: 3/5 = 0.6
        assert abs(results.success_rate - 0.6) < 0.001
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        results = SetupResults()
        
        # No timing recorded
        assert results.duration is None
        
        # With timing
        results.start_time = 100.0
        results.end_time = 105.5
        assert results.duration == 5.5
    
    def test_has_errors_and_warnings(self):
        """Test error and warning detection."""
        results = SetupResults()
        
        assert results.has_errors is False
        assert results.has_warnings is False
        
        results.add_error("Test error")
        assert results.has_errors is True
        
        results.add_warning("Test warning")
        assert results.has_warnings is True
        
        assert len(results.errors) == 1
        assert len(results.warnings) == 1
        assert "Test error" in results.errors
        assert "Test warning" in results.warnings
    
    def test_get_summary(self):
        """Test getting setup results summary."""
        results = SetupResults(
            directories_created=[Path("/test1"), Path("/test2")],
            exclusions_added=[
                (Path("/test1"), True),
                (Path("/test2"), False)
            ],
            files_downloaded=[("file1.exe", True)],
            configs_updated=[("config1.ini", True)],
            shortcuts_created=[("Shortcut1", False)],
            errors=["Error 1"],
            warnings=["Warning 1", "Warning 2"]
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
        assert abs(summary['success_rate'] - (6/8)) < 0.001


class TestShortcutConfig:
    """Test cases for ShortcutConfig dataclass."""
    
    def test_shortcut_config_initialization(self):
        """Test basic ShortcutConfig initialization."""
        config = ShortcutConfig(
            name="Test Shortcut",
            target_path=Path("/test/target.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        
        assert config.name == "Test Shortcut"
        assert config.target_path == Path("/test/target.exe").resolve()
        assert config.working_directory == Path("/test").resolve()
        assert config.icon_path is None
        assert config.description is None
        assert config.arguments is None
    
    def test_shortcut_config_with_optional_params(self):
        """Test ShortcutConfig initialization with optional parameters."""
        config = ShortcutConfig(
            name="Test Shortcut",
            target_path=Path("/test/target.exe").resolve(),
            working_directory=Path("/test").resolve(),
            icon_path=Path("/test/icon.ico").resolve(),
            description="Test description",
            arguments="--test-arg"
        )
        
        assert config.icon_path == Path("/test/icon.ico").resolve()
        assert config.description == "Test description"
        assert config.arguments == "--test-arg"
    
    def test_shortcut_config_name_validation(self):
        """Test that ShortcutConfig validates shortcut names."""
        with pytest.raises(ValueError, match="Shortcut name cannot be empty"):
            ShortcutConfig(
                name="",
                target_path=Path("/test/target.exe").resolve(),
                working_directory=Path("/test").resolve()
            )
        
        with pytest.raises(ValueError, match="Shortcut name contains invalid characters"):
            ShortcutConfig(
                name="Test<>Shortcut",
                target_path=Path("/test/target.exe").resolve(),
                working_directory=Path("/test").resolve()
            )
    
    def test_shortcut_config_path_validation(self):
        """Test that ShortcutConfig validates paths are absolute."""
        with pytest.raises(ValueError, match="Target path must be absolute"):
            ShortcutConfig(
                name="Test Shortcut",
                target_path=Path("relative/target.exe"),
                working_directory=Path("/test").resolve()
            )
        
        with pytest.raises(ValueError, match="Working directory must be absolute"):
            ShortcutConfig(
                name="Test Shortcut",
                target_path=Path("/test/target.exe").resolve(),
                working_directory=Path("relative/dir")
            )
        
        with pytest.raises(ValueError, match="Icon path must be absolute"):
            ShortcutConfig(
                name="Test Shortcut",
                target_path=Path("/test/target.exe").resolve(),
                working_directory=Path("/test").resolve(),
                icon_path=Path("relative/icon.ico")
            )
    
    def test_desktop_path_property(self):
        """Test desktop path property."""
        config = ShortcutConfig(
            name="Test Shortcut",
            target_path=Path("/test/target.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        
        desktop_path = config.desktop_path
        assert desktop_path.parent == Path.home() / "Desktop"
        
        if os.name == 'nt':  # Windows
            assert desktop_path.name == "Test Shortcut.lnk"
        else:  # Unix-like systems
            assert desktop_path.name == "Test Shortcut.desktop"
    
    def test_resolve_relative_paths(self):
        """Test resolving relative paths to absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Create config with absolute paths first, then modify to test resolution
            config = ShortcutConfig(
                name="Test Shortcut",
                target_path=base_path / "absolute" / "target.exe",
                working_directory=base_path / "relative" / "dir",
                icon_path=base_path / "relative" / "icon.ico"
            )
            
            # Manually set some paths to relative for testing
            config.working_directory = Path("relative/dir")
            config.icon_path = Path("relative/icon.ico")
            
            config.resolve_relative_paths(base_path)
            
            # Absolute path should remain unchanged
            assert config.target_path == base_path / "absolute" / "target.exe"
            
            # Relative paths should be resolved
            assert config.working_directory == (base_path / "relative/dir").resolve()
            assert config.icon_path == (base_path / "relative/icon.ico").resolve()
    
    def test_to_dict_and_from_dict(self):
        """Test converting shortcut config to/from dictionary."""
        original_config = ShortcutConfig(
            name="Test Shortcut",
            target_path=Path("/test/target.exe").resolve(),
            working_directory=Path("/test").resolve(),
            icon_path=Path("/test/icon.ico").resolve(),
            description="Test description",
            arguments="--test-arg"
        )
        
        # Convert to dict
        config_dict = original_config.to_dict()
        
        assert config_dict['name'] == "Test Shortcut"
        assert config_dict['target_path'] == str(Path("/test/target.exe").resolve())
        assert config_dict['working_directory'] == str(Path("/test").resolve())
        assert config_dict['icon_path'] == str(Path("/test/icon.ico").resolve())
        assert config_dict['description'] == "Test description"
        assert config_dict['arguments'] == "--test-arg"
        assert 'desktop_path' in config_dict
        
        # Convert back from dict
        restored_config = ShortcutConfig.from_dict(config_dict)
        
        assert restored_config.name == original_config.name
        assert restored_config.target_path == original_config.target_path
        assert restored_config.working_directory == original_config.working_directory
        assert restored_config.icon_path == original_config.icon_path
        assert restored_config.description == original_config.description
        assert restored_config.arguments == original_config.arguments
    
    def test_to_dict_with_none_values(self):
        """Test converting shortcut config to dict with None values."""
        config = ShortcutConfig(
            name="Test Shortcut",
            target_path=Path("/test/target.exe").resolve(),
            working_directory=Path("/test").resolve()
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['icon_path'] is None
        assert config_dict['description'] is None
        assert config_dict['arguments'] is None
        
        # Test from_dict with None values
        restored_config = ShortcutConfig.from_dict(config_dict)
        assert restored_config.icon_path is None
        assert restored_config.description is None
        assert restored_config.arguments is None


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])