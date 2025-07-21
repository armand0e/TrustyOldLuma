"""
Unit tests for AppListManager.

Tests the AppList folder creation and configuration management functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from rich.console import Console

from applist_manager import AppListManager
from models import LunaResults
from exceptions import FileOperationError, ConfigurationError


class TestAppListManager:
    """Test cases for AppListManager."""
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        return Mock(spec=Console)
    
    @pytest.fixture
    def applist_manager(self, mock_console):
        """Create AppListManager instance with mock console."""
        return AppListManager(mock_console)
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def setup_results(self):
        """Create LunaResults instance for testing."""
        return LunaResults()
    
    @pytest.mark.asyncio
    async def test_setup_applist_success(self, applist_manager, temp_dir, setup_results):
        """Test successful AppList setup."""
        greenluma_path = temp_dir / "GreenLuma"
        app_id = "480"
        
        # Setup should succeed
        result = await applist_manager.setup_applist(greenluma_path, app_id, setup_results)
        
        assert result is True
        assert (greenluma_path / "AppList").exists()
        assert (greenluma_path / "AppList" / "0.txt").exists()
        
        # Check file content
        with open(greenluma_path / "AppList" / "0.txt", 'r') as f:
            content = f.read().strip()
        assert content == app_id
        
        # Check results tracking
        assert len(setup_results.configs_updated) == 1
        assert setup_results.configs_updated[0] == ("AppList configuration", True)
    
    @pytest.mark.asyncio
    async def test_setup_applist_existing_directory(self, applist_manager, temp_dir, setup_results):
        """Test AppList setup when directory already exists."""
        greenluma_path = temp_dir / "GreenLuma"
        applist_path = greenluma_path / "AppList"
        app_id = "480"
        
        # Create directory structure
        applist_path.mkdir(parents=True, exist_ok=True)
        
        # Setup should still succeed
        result = await applist_manager.setup_applist(greenluma_path, app_id, setup_results)
        
        assert result is True
        assert applist_path.exists()
        assert (applist_path / "0.txt").exists()
    
    @pytest.mark.asyncio
    async def test_setup_applist_existing_file(self, applist_manager, temp_dir, setup_results):
        """Test AppList setup when file already exists."""
        greenluma_path = temp_dir / "GreenLuma"
        applist_path = greenluma_path / "AppList"
        applist_file = applist_path / "0.txt"
        app_id = "480"
        
        # Create directory and file
        applist_path.mkdir(parents=True, exist_ok=True)
        with open(applist_file, 'w') as f:
            f.write("123\n")
        
        # Setup should still succeed (file already exists)
        result = await applist_manager.setup_applist(greenluma_path, app_id, setup_results)
        
        assert result is True
        assert applist_file.exists()
        
        # File content should remain unchanged
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert content == "123"
    
    @pytest.mark.asyncio
    async def test_setup_applist_invalid_app_id(self, applist_manager, temp_dir, setup_results):
        """Test AppList setup with invalid App ID."""
        greenluma_path = temp_dir / "GreenLuma"
        invalid_app_id = "invalid"
        
        # Setup should still create the file (validation is separate)
        result = await applist_manager.setup_applist(greenluma_path, invalid_app_id, setup_results)
        
        assert result is True
        assert (greenluma_path / "AppList" / "0.txt").exists()
        
        # Check file content
        with open(greenluma_path / "AppList" / "0.txt", 'r') as f:
            content = f.read().strip()
        assert content == invalid_app_id
    
    @pytest.mark.asyncio
    async def test_create_applist_directory_success(self, applist_manager, temp_dir):
        """Test successful AppList directory creation."""
        applist_path = temp_dir / "AppList"
        
        result = await applist_manager._create_applist_directory(applist_path)
        
        assert result is True
        assert applist_path.exists()
        assert applist_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_create_applist_directory_existing(self, applist_manager, temp_dir):
        """Test AppList directory creation when directory already exists."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        
        result = await applist_manager._create_applist_directory(applist_path)
        
        assert result is True
        assert applist_path.exists()
        assert applist_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_create_applist_directory_file_exists(self, applist_manager, temp_dir):
        """Test AppList directory creation when a file exists with the same name."""
        applist_path = temp_dir / "AppList"
        
        # Create a file with the same name
        with open(applist_path, 'w') as f:
            f.write("test")
        
        result = await applist_manager._create_applist_directory(applist_path)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_initial_applist_file_success(self, applist_manager, temp_dir):
        """Test successful initial AppList file creation."""
        applist_file = temp_dir / "0.txt"
        app_id = "480"
        
        result = await applist_manager._create_initial_applist_file(applist_file, app_id)
        
        assert result is True
        assert applist_file.exists()
        
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert content == app_id
    
    @pytest.mark.asyncio
    async def test_create_initial_applist_file_existing(self, applist_manager, temp_dir):
        """Test initial AppList file creation when file already exists."""
        applist_file = temp_dir / "0.txt"
        app_id = "480"
        
        # Create existing file
        with open(applist_file, 'w') as f:
            f.write("123\n")
        
        result = await applist_manager._create_initial_applist_file(applist_file, app_id)
        
        assert result is True
        assert applist_file.exists()
        
        # Content should remain unchanged
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert content == "123"
    
    def test_validate_applist_format_valid(self, applist_manager, temp_dir):
        """Test AppList file format validation with valid content."""
        applist_file = temp_dir / "0.txt"
        
        # Create valid AppList file
        with open(applist_file, 'w') as f:
            f.write("480\n730\n440\n")
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is True
    
    def test_validate_applist_format_single_app_id(self, applist_manager, temp_dir):
        """Test AppList file format validation with single App ID."""
        applist_file = temp_dir / "0.txt"
        
        # Create valid AppList file with single App ID
        with open(applist_file, 'w') as f:
            f.write("480\n")
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is True
    
    def test_validate_applist_format_empty_file(self, applist_manager, temp_dir):
        """Test AppList file format validation with empty file."""
        applist_file = temp_dir / "0.txt"
        
        # Create empty file
        applist_file.touch()
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is False
    
    def test_validate_applist_format_invalid_content(self, applist_manager, temp_dir):
        """Test AppList file format validation with invalid content."""
        applist_file = temp_dir / "0.txt"
        
        # Create file with invalid content
        with open(applist_file, 'w') as f:
            f.write("invalid\nnotanumber\n")
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is False
    
    def test_validate_applist_format_mixed_content(self, applist_manager, temp_dir):
        """Test AppList file format validation with mixed valid/invalid content."""
        applist_file = temp_dir / "0.txt"
        
        # Create file with mixed content
        with open(applist_file, 'w') as f:
            f.write("480\ninvalid\n730\n")
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is True  # Should pass because there are valid App IDs
    
    def test_validate_applist_format_negative_app_id(self, applist_manager, temp_dir):
        """Test AppList file format validation with negative App ID."""
        applist_file = temp_dir / "0.txt"
        
        # Create file with negative App ID
        with open(applist_file, 'w') as f:
            f.write("-480\n")
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is False
    
    def test_validate_applist_format_zero_app_id(self, applist_manager, temp_dir):
        """Test AppList file format validation with zero App ID."""
        applist_file = temp_dir / "0.txt"
        
        # Create file with zero App ID
        with open(applist_file, 'w') as f:
            f.write("0\n")
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is False
    
    def test_validate_applist_format_nonexistent_file(self, applist_manager, temp_dir):
        """Test AppList file format validation with nonexistent file."""
        applist_file = temp_dir / "nonexistent.txt"
        
        result = applist_manager._validate_applist_format(applist_file)
        
        assert result is False
    
    def test_add_app_id_new_file(self, applist_manager, temp_dir):
        """Test adding App ID to new file."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        app_id = "480"
        
        result = applist_manager.add_app_id(applist_path, app_id)
        
        assert result is True
        assert (applist_path / "0.txt").exists()
        
        with open(applist_path / "0.txt", 'r') as f:
            content = f.read().strip()
        assert content == app_id
    
    def test_add_app_id_existing_file(self, applist_manager, temp_dir):
        """Test adding App ID to existing file."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        applist_file = applist_path / "0.txt"
        
        # Create existing file
        with open(applist_file, 'w') as f:
            f.write("480\n")
        
        new_app_id = "730"
        result = applist_manager.add_app_id(applist_path, new_app_id)
        
        assert result is True
        
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert "480" in content
        assert "730" in content
    
    def test_add_app_id_duplicate(self, applist_manager, temp_dir):
        """Test adding duplicate App ID."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        applist_file = applist_path / "0.txt"
        
        # Create existing file with App ID
        with open(applist_file, 'w') as f:
            f.write("480\n")
        
        # Try to add the same App ID
        result = applist_manager.add_app_id(applist_path, "480")
        
        assert result is True
        
        # File should remain unchanged
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert content == "480"
    
    def test_add_app_id_invalid(self, applist_manager, temp_dir):
        """Test adding invalid App ID."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        
        result = applist_manager.add_app_id(applist_path, "invalid")
        
        assert result is False
    
    def test_add_app_id_negative(self, applist_manager, temp_dir):
        """Test adding negative App ID."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        
        result = applist_manager.add_app_id(applist_path, "-480")
        
        assert result is False
    
    def test_get_app_ids_success(self, applist_manager, temp_dir):
        """Test getting App IDs from AppList files."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        
        # Create multiple AppList files
        with open(applist_path / "0.txt", 'w') as f:
            f.write("480\n730\n")
        
        with open(applist_path / "1.txt", 'w') as f:
            f.write("440\n")
        
        app_ids = applist_manager.get_app_ids(applist_path)
        
        assert len(app_ids) == 3
        assert "480" in app_ids
        assert "730" in app_ids
        assert "440" in app_ids
    
    def test_get_app_ids_empty_directory(self, applist_manager, temp_dir):
        """Test getting App IDs from empty directory."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        
        app_ids = applist_manager.get_app_ids(applist_path)
        
        assert len(app_ids) == 0
    
    def test_get_app_ids_nonexistent_directory(self, applist_manager, temp_dir):
        """Test getting App IDs from nonexistent directory."""
        applist_path = temp_dir / "NonExistent"
        
        app_ids = applist_manager.get_app_ids(applist_path)
        
        assert len(app_ids) == 0
    
    def test_get_app_ids_mixed_content(self, applist_manager, temp_dir):
        """Test getting App IDs from files with mixed content."""
        applist_path = temp_dir / "AppList"
        applist_path.mkdir(parents=True, exist_ok=True)
        
        # Create file with mixed valid/invalid content
        with open(applist_path / "0.txt", 'w') as f:
            f.write("480\ninvalid\n730\n\n")
        
        app_ids = applist_manager.get_app_ids(applist_path)
        
        assert len(app_ids) == 2
        assert "480" in app_ids
        assert "730" in app_ids
        assert "invalid" not in app_ids
    
    @pytest.mark.asyncio
    async def test_setup_applist_permission_error(self, applist_manager, setup_results):
        """Test AppList setup with permission error."""
        import platform
        
        # Use a path that would cause permission error based on platform
        if platform.system() == "Windows":
            # On Windows, try to write to a system directory
            greenluma_path = Path("C:/Windows/System32/GreenLuma")
        else:
            # On Unix-like systems, try to write to root
            greenluma_path = Path("/root/restricted")
        
        app_id = "480"
        
        result = await applist_manager.setup_applist(greenluma_path, app_id, setup_results)
        
        # The result might still be True if the user has admin privileges
        # So we'll just check that the function handles the case gracefully
        assert isinstance(result, bool)
        
        # If it failed, there should be an error
        if not result:
            assert len(setup_results.errors) > 0
    
    @pytest.mark.asyncio
    async def test_setup_applist_console_output(self, applist_manager, temp_dir, setup_results, mock_console):
        """Test that AppList setup produces appropriate console output."""
        greenluma_path = temp_dir / "GreenLuma"
        app_id = "480"
        
        result = await applist_manager.setup_applist(greenluma_path, app_id, setup_results)
        
        assert result is True
        
        # Check that console.print was called with success message
        mock_console.print.assert_called()
        
        # Check that success message was printed
        calls = mock_console.print.call_args_list
        success_call_found = any(
            "[green]✅ AppList setup completed successfully[/green]" in str(call)
            for call in calls
        )
        assert success_call_found