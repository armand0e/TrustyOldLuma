"""
Integration test for AppList functionality.

Tests the AppList setup process in the context of the main application.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from rich.console import Console

from gaming_setup_tool import GamingSetupTool
from models import SetupConfig, SetupResults
from applist_manager import AppListManager


class TestAppListIntegration:
    """Integration tests for AppList functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        return Mock(spec=Console)
    
    @pytest.fixture
    def setup_config(self, temp_dir):
        """Create test setup configuration."""
        return SetupConfig(
            greenluma_path=temp_dir / "GreenLuma",
            koalageddon_path=temp_dir / "Koalageddon",
            koalageddon_config_path=temp_dir / "Koalageddon" / "config",
            download_url="https://example.com/test.exe",
            app_id="480",
            verbose_logging=False,
            documents_path=temp_dir / "Documents",
            temp_dir=temp_dir / "temp"
        )
    
    @pytest.mark.asyncio
    async def test_applist_setup_integration(self, temp_dir, setup_config):
        """Test AppList setup integration with main application."""
        # Create AppListManager
        console = Console()
        applist_manager = AppListManager(console)
        results = SetupResults()
        
        # Test the setup process
        success = await applist_manager.setup_applist(
            setup_config.greenluma_path,
            setup_config.app_id,
            results
        )
        
        assert success is True
        
        # Verify directory structure was created
        applist_path = setup_config.greenluma_path / "AppList"
        assert applist_path.exists()
        assert applist_path.is_dir()
        
        # Verify initial configuration file was created
        applist_file = applist_path / "0.txt"
        assert applist_file.exists()
        
        # Verify file content
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert content == setup_config.app_id
        
        # Verify results tracking
        assert len(results.configs_updated) == 1
        assert results.configs_updated[0] == ("AppList configuration", True)
        assert len(results.errors) == 0
    
    @pytest.mark.asyncio
    async def test_applist_manager_in_gaming_setup_tool(self, temp_dir):
        """Test that AppListManager is properly integrated in GamingSetupTool."""
        # Create a GamingSetupTool instance
        tool = GamingSetupTool(verbose=False)
        
        # Verify that AppListManager is initialized
        assert hasattr(tool, 'applist_manager')
        assert isinstance(tool.applist_manager, AppListManager)
        
        # Verify that the manager has the correct console reference
        assert tool.applist_manager.console is tool.console
    
    @pytest.mark.asyncio
    async def test_applist_setup_with_custom_app_id(self, temp_dir):
        """Test AppList setup with custom App ID."""
        console = Console()
        applist_manager = AppListManager(console)
        results = SetupResults()
        
        greenluma_path = temp_dir / "GreenLuma"
        custom_app_id = "730"  # Counter-Strike: Global Offensive
        
        # Test the setup process with custom App ID
        success = await applist_manager.setup_applist(
            greenluma_path,
            custom_app_id,
            results
        )
        
        assert success is True
        
        # Verify file content has the custom App ID
        applist_file = greenluma_path / "AppList" / "0.txt"
        with open(applist_file, 'r') as f:
            content = f.read().strip()
        assert content == custom_app_id
    
    @pytest.mark.asyncio
    async def test_applist_validation_after_setup(self, temp_dir):
        """Test that AppList validation works after setup."""
        console = Console()
        applist_manager = AppListManager(console)
        results = SetupResults()
        
        greenluma_path = temp_dir / "GreenLuma"
        app_id = "480"
        
        # Setup AppList
        success = await applist_manager.setup_applist(greenluma_path, app_id, results)
        assert success is True
        
        # Test validation
        applist_file = greenluma_path / "AppList" / "0.txt"
        is_valid = applist_manager._validate_applist_format(applist_file)
        assert is_valid is True
        
        # Test getting App IDs
        app_ids = applist_manager.get_app_ids(greenluma_path / "AppList")
        assert len(app_ids) == 1
        assert app_ids[0] == app_id
    
    @pytest.mark.asyncio
    async def test_applist_add_additional_app_id(self, temp_dir):
        """Test adding additional App IDs after initial setup."""
        console = Console()
        applist_manager = AppListManager(console)
        results = SetupResults()
        
        greenluma_path = temp_dir / "GreenLuma"
        initial_app_id = "480"
        additional_app_id = "730"
        
        # Initial setup
        success = await applist_manager.setup_applist(greenluma_path, initial_app_id, results)
        assert success is True
        
        # Add additional App ID
        applist_path = greenluma_path / "AppList"
        success = applist_manager.add_app_id(applist_path, additional_app_id)
        assert success is True
        
        # Verify both App IDs are present
        app_ids = applist_manager.get_app_ids(applist_path)
        assert len(app_ids) == 2
        assert initial_app_id in app_ids
        assert additional_app_id in app_ids
    
    def test_applist_manager_console_integration(self):
        """Test that AppListManager properly uses Rich console for output."""
        mock_console = Mock(spec=Console)
        applist_manager = AppListManager(mock_console)
        
        # Verify console is stored
        assert applist_manager.console is mock_console
        
        # The console should be used for output in the actual methods
        # This is tested in the unit tests where we verify console.print calls
    
    @pytest.mark.asyncio
    async def test_applist_setup_error_handling(self, temp_dir):
        """Test AppList setup error handling and results tracking."""
        console = Console()
        applist_manager = AppListManager(console)
        results = SetupResults()
        
        # Create a scenario that might cause issues (file instead of directory)
        greenluma_path = temp_dir / "GreenLuma"
        greenluma_path.mkdir(parents=True, exist_ok=True)
        
        # Create a file where AppList directory should be
        applist_file_path = greenluma_path / "AppList"
        with open(applist_file_path, 'w') as f:
            f.write("blocking file")
        
        app_id = "480"
        
        # This should fail because AppList exists as a file, not directory
        success = await applist_manager.setup_applist(greenluma_path, app_id, results)
        
        assert success is False
        assert len(results.errors) > 0
        
        # Verify error message contains relevant information
        error_found = any("AppList" in error for error in results.errors)
        assert error_found