"""
Tests for the Configuration Handler module.

This module contains tests for the ConfigurationHandler class, including
DLLInjector.ini updates and Koalageddon config file replacement.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from rich.console import Console
from configuration_handler import ConfigurationHandler
from models import SetupResults


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
def setup_results():
    """Create a SetupResults instance for testing."""
    return SetupResults()


@pytest.fixture
def sample_dll_injector_config(temp_dir):
    """Create a sample DLLInjector.ini file."""
    config_path = temp_dir / "DLLInjector.ini"
    with open(config_path, 'w') as f:
        f.write("[Settings]\n")
        f.write("DLL=C:\\OldPath\\GreenLuma_2020_x64.dll\n")
        f.write("Timeout=30\n")
    return config_path


@pytest.fixture
def sample_dll_file(temp_dir):
    """Create a sample DLL file."""
    dll_path = temp_dir / "GreenLuma_2020_x64.dll"
    with open(dll_path, 'wb') as f:
        f.write(b"Mock DLL content")
    return dll_path


@pytest.fixture
def sample_koalageddon_config(temp_dir):
    """Create a sample Koalageddon config file."""
    config_path = temp_dir / "koalageddon.config"
    with open(config_path, 'w') as f:
        f.write("{\n")
        f.write('  "EnableSteam": true,\n')
        f.write('  "EnableEpic": true,\n')
        f.write('  "EnableOrigin": true\n')
        f.write("}\n")
    return config_path


@pytest.mark.asyncio
async def test_update_dll_injector_config_success(config_handler, sample_dll_injector_config, 
                                                sample_dll_file, setup_results):
    """Test successful DLLInjector.ini update."""
    # Act
    result = await config_handler.update_dll_injector_config(
        sample_dll_file, sample_dll_injector_config, setup_results
    )
    
    # Assert
    assert result is True
    assert len(setup_results.configs_updated) == 1
    assert setup_results.configs_updated[0][1] is True  # Success flag
    
    # Verify file content was updated
    with open(sample_dll_injector_config, 'r') as f:
        content = f.read()
        assert f"DLL={sample_dll_file}" in content


@pytest.mark.asyncio
async def test_update_dll_injector_config_missing_file(config_handler, temp_dir, setup_results):
    """Test DLLInjector.ini update with missing config file."""
    # Arrange
    nonexistent_config = temp_dir / "nonexistent.ini"
    dll_path = temp_dir / "GreenLuma_2020_x64.dll"
    with open(dll_path, 'wb') as f:
        f.write(b"Mock DLL content")
    
    # Act
    result = await config_handler.update_dll_injector_config(
        dll_path, nonexistent_config, setup_results
    )
    
    # Assert
    assert result is False
    assert len(setup_results.errors) == 1


@pytest.mark.asyncio
async def test_update_dll_injector_config_missing_dll(config_handler, sample_dll_injector_config, 
                                                   temp_dir, setup_results):
    """Test DLLInjector.ini update with missing DLL file."""
    # Arrange
    nonexistent_dll = temp_dir / "nonexistent.dll"
    
    # Act
    result = await config_handler.update_dll_injector_config(
        nonexistent_dll, sample_dll_injector_config, setup_results
    )
    
    # Assert
    assert result is False
    assert len(setup_results.errors) == 1


@pytest.mark.asyncio
async def test_replace_koalageddon_config_success(config_handler, sample_koalageddon_config, 
                                               temp_dir, setup_results):
    """Test successful Koalageddon config replacement."""
    # Arrange
    dest_dir = temp_dir / "koalageddon_config"
    dest_dir.mkdir()
    
    # Act
    result = await config_handler.replace_koalageddon_config(
        sample_koalageddon_config, dest_dir, setup_results
    )
    
    # Assert
    assert result is True
    assert len(setup_results.configs_updated) == 1
    assert setup_results.configs_updated[0][1] is True  # Success flag
    
    # Verify file was copied
    dest_file = dest_dir / sample_koalageddon_config.name
    assert dest_file.exists()
    with open(dest_file, 'r') as f:
        content = f.read()
        assert "EnableSteam" in content


@pytest.mark.asyncio
async def test_replace_koalageddon_config_missing_source(config_handler, temp_dir, setup_results):
    """Test Koalageddon config replacement with missing source file."""
    # Arrange
    nonexistent_config = temp_dir / "nonexistent.config"
    dest_dir = temp_dir / "koalageddon_config"
    dest_dir.mkdir()
    
    # Act
    result = await config_handler.replace_koalageddon_config(
        nonexistent_config, dest_dir, setup_results
    )
    
    # Assert
    assert result is False
    assert len(setup_results.errors) == 1


@pytest.mark.asyncio
async def test_replace_koalageddon_config_creates_dest_dir(config_handler, sample_koalageddon_config, 
                                                        temp_dir, setup_results):
    """Test Koalageddon config replacement creates destination directory if needed."""
    # Arrange
    dest_dir = temp_dir / "nonexistent_dir"
    
    # Act
    result = await config_handler.replace_koalageddon_config(
        sample_koalageddon_config, dest_dir, setup_results
    )
    
    # Assert
    assert result is True
    assert dest_dir.exists()
    assert dest_dir.is_dir()
    
    # Verify file was copied
    dest_file = dest_dir / sample_koalageddon_config.name
    assert dest_file.exists()


@pytest.mark.asyncio
async def test_backup_and_restore(config_handler, sample_dll_injector_config):
    """Test backup and restore functionality."""
    # Arrange
    original_content = sample_dll_injector_config.read_text()
    
    # Act - Create backup
    backup_path = await config_handler._create_backup(sample_dll_injector_config)
    
    # Assert backup was created
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.read_text() == original_content
    
    # Modify original file
    with open(sample_dll_injector_config, 'w') as f:
        f.write("Modified content")
    
    # Act - Restore backup
    restore_result = await config_handler._restore_backup(backup_path, sample_dll_injector_config)
    
    # Assert restore was successful
    assert restore_result is True
    assert sample_dll_injector_config.read_text() == original_content


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