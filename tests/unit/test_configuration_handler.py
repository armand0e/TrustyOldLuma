"""
Tests for the Luna Configuration Handler module.

This module contains tests for the ConfigurationHandler class, including
Luna injector configuration updates and Luna unlocker config file management.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from rich.console import Console
from configuration_handler import ConfigurationHandler
from models import LunaResults


@pytest.fixture
def mock_console():
    """Create a mock Rich console for testing."""
    console = MagicMock(spec=Console)
    console.is_jupyter = False
    return console


@pytest.fixture
def config_handler(mock_console):
    """Create a ConfigurationHandler instance for testing."""
    handler = ConfigurationHandler(mock_console)
    
    # Mock progress_manager and error_manager
    handler.progress_manager = MagicMock()
    handler.progress_manager.show_spinner = MagicMock()
    handler.progress_manager.show_spinner.return_value.__enter__ = MagicMock()
    handler.progress_manager.show_spinner.return_value.__exit__ = MagicMock()
    
    handler.error_manager = MagicMock()
    handler.error_manager.display_error = MagicMock()
    handler.error_manager.display_warning = MagicMock()
    handler.error_manager.display_retry_prompt = MagicMock(return_value=False)  # Don't retry by default
    
    return handler


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def luna_results():
    """Create a LunaResults instance for testing."""
    return LunaResults()


@pytest.fixture
def sample_luna_injector_config(temp_dir):
    """Create a sample luna_injector.ini file."""
    config_path = temp_dir / "luna_injector.ini"
    with open(config_path, 'w') as f:
        f.write("[Settings]\n")
        f.write("DLL=C:\\OldPath\\luna_core_x64.dll\n")
        f.write("Timeout=30\n")
    return config_path


@pytest.fixture
def sample_luna_dll_file(temp_dir):
    """Create a sample Luna DLL file."""
    dll_path = temp_dir / "luna_core_x64.dll"
    with open(dll_path, 'wb') as f:
        f.write(b"Mock Luna DLL content")
    return dll_path


@pytest.fixture
def sample_luna_config(temp_dir):
    """Create a sample Luna config file."""
    config_path = temp_dir / "luna_config.jsonc"
    with open(config_path, 'w') as f:
        f.write("{\n")
        f.write('  "luna": {\n')
        f.write('    "injector_enabled": true,\n')
        f.write('    "unlocker_enabled": true,\n')
        f.write('    "platforms": {\n')
        f.write('      "steam": {"enabled": true},\n')
        f.write('      "epic": {"enabled": true}\n')
        f.write('    }\n')
        f.write('  }\n')
        f.write("}\n")
    return config_path


@pytest.mark.asyncio
async def test_update_luna_injector_config_success(config_handler, sample_luna_injector_config, 
                                                sample_luna_dll_file, luna_results):
    """Test successful Luna injector configuration update."""
    # Act
    result = await config_handler.update_luna_injector_config(
        sample_luna_dll_file, sample_luna_injector_config, luna_results
    )
    
    # Assert
    assert result is True
    assert len(luna_results.configs_updated) == 1
    assert luna_results.configs_updated[0][1] is True  # Success flag
    
    # Verify file content was updated
    with open(sample_luna_injector_config, 'r') as f:
        content = f.read()
        assert f"DLL={sample_luna_dll_file}" in content


@pytest.mark.asyncio
async def test_update_luna_injector_config_missing_file(config_handler, temp_dir, luna_results):
    """Test Luna injector configuration update with missing config file."""
    # Arrange
    nonexistent_config = temp_dir / "nonexistent.ini"
    dll_path = temp_dir / "luna_core_x64.dll"
    with open(dll_path, 'wb') as f:
        f.write(b"Mock Luna DLL content")
    
    # Act
    result = await config_handler.update_luna_injector_config(
        dll_path, nonexistent_config, luna_results
    )
    
    # Assert
    assert result is False
    assert len(luna_results.errors) == 1


@pytest.mark.asyncio
async def test_update_luna_injector_config_missing_dll(config_handler, sample_luna_injector_config, 
                                                   temp_dir, luna_results):
    """Test Luna injector configuration update with missing DLL file."""
    # Arrange
    nonexistent_dll = temp_dir / "nonexistent.dll"
    
    # Act
    result = await config_handler.update_luna_injector_config(
        nonexistent_dll, sample_luna_injector_config, luna_results
    )
    
    # Assert
    assert result is False
    assert len(luna_results.errors) == 1


@pytest.mark.asyncio
async def test_replace_luna_config_success(config_handler, sample_luna_config, 
                                               temp_dir, luna_results):
    """Test successful Luna config replacement."""
    # Arrange
    dest_dir = temp_dir / "luna_config"
    dest_dir.mkdir()
    
    # Act
    result = await config_handler.replace_luna_config(
        sample_luna_config, dest_dir, luna_results
    )
    
    # Assert
    assert result is True
    assert len(luna_results.configs_updated) == 1
    assert luna_results.configs_updated[0][1] is True  # Success flag
    
    # Verify file was copied
    dest_file = dest_dir / sample_luna_config.name
    assert dest_file.exists()
    with open(dest_file, 'r') as f:
        content = f.read()
        assert "injector_enabled" in content


@pytest.mark.asyncio
async def test_replace_luna_config_missing_source(config_handler, temp_dir, luna_results):
    """Test Luna config replacement with missing source file."""
    # Arrange
    nonexistent_config = temp_dir / "nonexistent.jsonc"
    dest_dir = temp_dir / "luna_config"
    dest_dir.mkdir()
    
    # Act
    result = await config_handler.replace_luna_config(
        nonexistent_config, dest_dir, luna_results
    )
    
    # Assert
    assert result is False
    assert len(luna_results.errors) == 1


@pytest.mark.asyncio
async def test_replace_luna_config_creates_dest_dir(config_handler, sample_luna_config, 
                                                        temp_dir, luna_results):
    """Test Luna config replacement creates destination directory if needed."""
    # Arrange
    dest_dir = temp_dir / "nonexistent_dir"
    
    # Act
    result = await config_handler.replace_luna_config(
        sample_luna_config, dest_dir, luna_results
    )
    
    # Assert
    assert result is True
    assert dest_dir.exists()
    assert dest_dir.is_dir()
    
    # Verify file was copied
    dest_file = dest_dir / sample_luna_config.name
    assert dest_file.exists()


@pytest.mark.asyncio
async def test_backup_and_restore(config_handler, sample_luna_injector_config):
    """Test backup and restore functionality for Luna configurations."""
    # Arrange
    original_content = sample_luna_injector_config.read_text()
    
    # Act - Create backup
    backup_path = await config_handler._create_backup(sample_luna_injector_config)
    
    # Assert backup was created
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.read_text() == original_content
    
    # Modify original file
    with open(sample_luna_injector_config, 'w') as f:
        f.write("Modified Luna content")
    
    # Act - Restore backup
    restore_result = await config_handler._restore_backup(backup_path, sample_luna_injector_config)
    
    # Assert restore was successful
    assert restore_result is True
    assert sample_luna_injector_config.read_text() == original_content


@pytest.mark.asyncio
async def test_verify_file_copy(config_handler, temp_dir):
    """Test file copy verification."""
    # Arrange
    source_file = temp_dir / "source.txt"
    target_file = temp_dir / "target.txt"
    
    with open(source_file, 'w') as f:
        f.write("Test content")
    
    # Act - Copy with matching content
    shutil.copy2(source_file, target_file)
    match_result = await config_handler._verify_file_copy(source_file, target_file)
    
    # Assert
    assert match_result is True
    
    # Act - Copy with different content
    with open(target_file, 'w') as f:
        f.write("Different content")
    mismatch_result = await config_handler._verify_file_copy(source_file, target_file)
    
    # Assert
    assert mismatch_result is False


@pytest.mark.asyncio
async def test_update_luna_unlocker_config_success(config_handler, temp_dir, luna_results):
    """Test successful Luna unlocker configuration update."""
    # Arrange
    unlocker_config_path = temp_dir / "luna_unlocker.json"
    with open(unlocker_config_path, 'w') as f:
        f.write('{"platforms": {"steam": false, "epic": false}}')
    
    # Act
    result = await config_handler.update_luna_unlocker_config(
        unlocker_config_path, {"steam": True, "epic": True}, luna_results
    )
    
    # Assert
    assert result is True
    assert len(luna_results.configs_updated) == 1
    assert luna_results.configs_updated[0][1] is True  # Success flag
    
    # Verify file content was updated
    with open(unlocker_config_path, 'r') as f:
        content = f.read()
        assert '"steam": true' in content.lower()
        assert '"epic": true' in content.lower()


@pytest.mark.asyncio
async def test_migration_config_merge(config_handler, temp_dir, luna_results):
    """Test merging legacy configurations into Luna format."""
    # Arrange - Create legacy config files
    greenluma_config = temp_dir / "DLLInjector.ini"
    with open(greenluma_config, 'w') as f:
        f.write("[Settings]\nDLL=GreenLuma_2020_x64.dll\nTimeout=30\n")
    
    koalageddon_config = temp_dir / "config.json"
    with open(koalageddon_config, 'w') as f:
        f.write('{"EnableSteam": true, "EnableEpic": false}')
    
    luna_config_path = temp_dir / "luna_config.jsonc"
    
    # Act
    result = await config_handler.merge_legacy_configs(
        greenluma_config, koalageddon_config, luna_config_path, luna_results
    )
    
    # Assert
    assert result is True
    assert luna_config_path.exists()
    
    # Verify merged configuration
    with open(luna_config_path, 'r') as f:
        content = f.read()
        assert "injector_enabled" in content
        assert "unlocker_enabled" in content