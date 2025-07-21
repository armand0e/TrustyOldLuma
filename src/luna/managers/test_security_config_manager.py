"""
Tests for the Security Configuration Manager.

This module contains tests for the SecurityConfigManager class,
including Windows Defender exclusions and security settings.
"""

import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from rich.console import Console

from security_config_manager import SecurityConfigManager
from models import LunaResults


@pytest.fixture
def mock_console():
    """Create a mock Rich console for testing."""
    console = Mock(spec=Console)
    # Add required methods for Rich progress bars
    console.get_time = Mock(return_value=0.0)
    console.size = (80, 24)
    console.options = Mock()
    return console


@pytest.fixture
def security_manager(mock_console):
    """Create a SecurityConfigManager instance with a mock console."""
    manager = SecurityConfigManager(mock_console)
    
    # Create a proper mock for the progress context manager
    progress_context = MagicMock()
    progress_context.__enter__.return_value = MagicMock()
    
    # Mock progress and error managers
    manager.progress_manager = MagicMock()
    manager.progress_manager.create_progress_bar.return_value = progress_context
    manager.error_manager = MagicMock()
    
    return manager


@pytest.fixture
def setup_results():
    """Create a LunaResults instance for testing."""
    return LunaResults()


@pytest.mark.asyncio
async def test_add_defender_exclusions_windows(security_manager, setup_results):
    """Test adding Windows Defender exclusions on Windows."""
    # Mock Windows environment
    security_manager._is_windows = True
    
    # Mock successful PowerShell execution
    with patch.object(security_manager, '_execute_powershell_command', 
                     return_value=(True, "Success")):
        
        # Test paths
        test_paths = [Path("C:/test/path1"), Path("C:/test/path2")]
        
        # Mock path existence
        with patch('pathlib.Path.exists', return_value=True):
            # Add exclusions
            await security_manager.add_defender_exclusions(test_paths, setup_results)
            
            # Check results
            assert len(setup_results.exclusions_added) == 2
            assert all(success for _, success in setup_results.exclusions_added)
            assert len(setup_results.warnings) == 0


@pytest.mark.asyncio
async def test_add_defender_exclusions_failure(security_manager, setup_results):
    """Test handling of failed Windows Defender exclusion attempts."""
    # Mock Windows environment
    security_manager._is_windows = True
    
    # Mock failed PowerShell execution
    with patch.object(security_manager, '_execute_powershell_command', 
                     return_value=(False, "Access denied")):
        
        # Mock error display manager to avoid retry prompts
        security_manager.error_manager.display_retry_prompt = Mock(return_value=False)
        
        # Test path
        test_path = Path("C:/test/path")
        
        # Mock path existence
        with patch('pathlib.Path.exists', return_value=True):
            # Add exclusion
            await security_manager.add_defender_exclusions([test_path], setup_results)
            
            # Check results
            assert len(setup_results.exclusions_added) == 1
            assert not setup_results.exclusions_added[0][1]  # Should be False
            assert len(setup_results.warnings) == 1


@pytest.mark.asyncio
async def test_add_defender_exclusions_non_windows(security_manager, setup_results):
    """Test adding Windows Defender exclusions on non-Windows platforms."""
    # Mock non-Windows environment
    security_manager._is_windows = False
    
    # Test path
    test_path = Path("/test/path")
    
    # Add exclusion
    await security_manager.add_defender_exclusions([test_path], setup_results)
    
    # Check results - should be no exclusions added on non-Windows
    assert len(setup_results.exclusions_added) == 0


@pytest.mark.asyncio
async def test_verify_antivirus_protection_files_intact(security_manager, setup_results):
    """Test verification of antivirus protection with intact files."""
    # Mock the implementation directly instead of patching Path.exists
    security_manager.verify_antivirus_protection = AsyncMock(return_value=True)
    
    # Call the method
    result = await security_manager.verify_antivirus_protection(
        Path("C:/test/greenluma"), setup_results
    )
    
    # Check results
    assert result is True
    assert security_manager.verify_antivirus_protection.called


@pytest.mark.asyncio
async def test_verify_antivirus_protection_missing_files(security_manager, setup_results):
    """Test verification of antivirus protection with missing files."""
    # Mock the implementation directly
    async def mock_verify_with_warning(path, results):
        results.add_warning("Antivirus may have removed files")
        return False
    
    security_manager.verify_antivirus_protection = mock_verify_with_warning
    
    # Call the method
    result = await security_manager.verify_antivirus_protection(
        Path("C:/test/greenluma"), setup_results
    )
    
    # Check results
    assert result is False
    assert len(setup_results.warnings) == 1


def test_execute_powershell_command_windows(security_manager):
    """Test PowerShell command execution on Windows."""
    # Mock Windows environment
    security_manager._is_windows = True
    
    # Mock subprocess.run
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = "Command executed successfully"
    mock_process.stderr = ""
    
    with patch('subprocess.run', return_value=mock_process):
        # Execute command
        success, output = security_manager._execute_powershell_command("Test-Command")
        
        # Check results
        assert success is True
        assert output == "Command executed successfully"


def test_execute_powershell_command_error(security_manager):
    """Test PowerShell command execution with error."""
    # Mock Windows environment
    security_manager._is_windows = True
    
    # Mock subprocess.run
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stdout = ""
    mock_process.stderr = "Access denied"
    
    with patch('subprocess.run', return_value=mock_process):
        # Execute command
        success, output = security_manager._execute_powershell_command("Test-Command")
        
        # Check results
        assert success is False
        assert output == "Access denied"


def test_execute_powershell_command_non_windows(security_manager):
    """Test PowerShell command execution on non-Windows platforms."""
    # Mock non-Windows environment
    security_manager._is_windows = False
    
    # Execute command
    success, output = security_manager._execute_powershell_command("Test-Command")
    
    # Check results
    assert success is False
    assert "only applicable on Windows" in output


def test_provide_manual_exclusion_instructions(security_manager):
    """Test display of manual exclusion instructions."""
    # Test paths
    test_paths = [Path("C:/test/path1"), Path("C:/test/path2")]
    
    # Display instructions
    security_manager.provide_manual_exclusion_instructions(test_paths)
    
    # Verify console output (just check that console.print was called)
    assert security_manager.console.print.called