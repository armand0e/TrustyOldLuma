"""
Integration tests for cleanup functionality in the Gaming Setup Tool.

This module tests the integration between the CleanupManager and other components
of the gaming setup tool to ensure proper cleanup behavior.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from rich.console import Console

from gaming_setup_tool import GamingSetupTool
from cleanup_manager import CleanupManager
from models import SetupConfig, SetupResults


class TestCleanupIntegration:
    """Test cleanup integration with the main application."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup after test
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a mock configuration for testing."""
        config = Mock(spec=SetupConfig)
        config.greenluma_path = temp_dir / "GreenLuma"
        config.koalageddon_path = temp_dir / "Koalageddon"
        config.temp_dir = temp_dir / "temp"
        config.get_security_exclusion_paths.return_value = [
            config.greenluma_path,
            config.koalageddon_path,
            config.temp_dir
        ]
        return config
    
    def test_cleanup_manager_initialization_in_main_app(self):
        """Test that CleanupManager is properly initialized in the main application."""
        tool = GamingSetupTool()
        
        assert hasattr(tool, 'cleanup_manager')
        assert isinstance(tool.cleanup_manager, CleanupManager)
        assert tool.cleanup_manager.console == tool.console
    
    @pytest.mark.asyncio
    async def test_temp_directory_registration(self, temp_dir):
        """Test that temporary directories are properly registered for cleanup."""
        tool = GamingSetupTool()
        tool.config = Mock()
        tool.config.temp_dir = temp_dir / "temp"
        tool.results = SetupResults()
        
        # Create the temp directory
        tool.config.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the other workflow methods to focus on cleanup registration
        with patch.object(tool, '_create_directories') as mock_create, \
             patch.object(tool, '_configure_security_exclusions') as mock_security, \
             patch.object(tool, '_extract_greenluma') as mock_extract, \
             patch.object(tool, '_verify_antivirus_protection') as mock_verify, \
             patch.object(tool, '_update_greenluma_config') as mock_update_gl, \
             patch.object(tool, '_setup_applist') as mock_applist, \
             patch.object(tool, '_download_koalageddon') as mock_download, \
             patch.object(tool, '_update_koalageddon_config') as mock_update_koa, \
             patch.object(tool, '_create_shortcuts') as mock_shortcuts, \
             patch.object(tool, '_cleanup_temp_files') as mock_cleanup:
            
            # Execute the workflow
            await tool._execute_setup_workflow()
            
            # Verify that temp directory was registered
            assert tool.config.temp_dir in tool.cleanup_manager._temp_directories
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_on_workflow_failure(self, temp_dir):
        """Test that cleanup is performed when the workflow fails."""
        tool = GamingSetupTool()
        tool.config = Mock()
        tool.config.temp_dir = temp_dir / "temp"
        tool.results = SetupResults()
        
        # Create some test files that should be cleaned up
        tool.config.temp_dir.mkdir(parents=True, exist_ok=True)
        test_file = tool.config.temp_dir / "test_file.txt"
        test_file.write_text("test content")
        
        # Register the file for cleanup
        tool.cleanup_manager.register_temp_file(test_file, "test")
        
        # Mock a method to raise an exception
        with patch.object(tool, '_create_directories', side_effect=Exception("Test failure")), \
             patch.object(tool.cleanup_manager, 'cleanup_failed_installation') as mock_cleanup:
            
            # Return a proper CleanupResults object
            from cleanup_manager import CleanupResults
            mock_cleanup.return_value = CleanupResults()
            
            # Execute the workflow - should fail and trigger cleanup
            with pytest.raises(Exception, match="Test failure"):
                await tool._execute_setup_workflow()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once_with(tool.results)
    
    @pytest.mark.asyncio
    async def test_comprehensive_cleanup_workflow(self, temp_dir):
        """Test the complete cleanup workflow with real file operations."""
        # Create a real cleanup manager with a real console
        console = Console(file=Mock())  # Mock the file to avoid actual output
        cleanup_manager = CleanupManager(console)
        
        # Create test files and directories
        test_file1 = temp_dir / "temp_file1.txt"
        test_file2 = temp_dir / "temp_file2.txt"
        test_dir = temp_dir / "temp_dir"
        
        test_file1.write_text("test content 1")
        test_file2.write_text("test content 2")
        test_dir.mkdir()
        (test_dir / "nested_file.txt").write_text("nested content")
        
        # Register items for cleanup
        cleanup_manager.register_temp_file(test_file1, "test_component")
        cleanup_manager.register_temp_file(test_file2, "test_component")
        cleanup_manager.register_temp_directory(test_dir, "test_component")
        
        # Verify files exist before cleanup
        assert test_file1.exists()
        assert test_file2.exists()
        assert test_dir.exists()
        
        # Mock the progress manager to avoid Rich console issues
        with patch.object(cleanup_manager.progress_manager, 'create_progress_bar') as mock_progress:
            mock_context = Mock()
            mock_progress.return_value.__enter__ = Mock(return_value=mock_context)
            mock_progress.return_value.__exit__ = Mock(return_value=None)
            
            # Perform cleanup
            file_results = await cleanup_manager.cleanup_temp_files()
            dir_results = await cleanup_manager.cleanup_temp_directories()
        
        # Verify cleanup results
        assert file_results.operations_attempted == 2
        assert file_results.operations_successful == 2
        assert dir_results.operations_attempted == 1
        assert dir_results.operations_successful == 1
        
        # Verify files were actually removed
        assert not test_file1.exists()
        assert not test_file2.exists()
        assert not test_dir.exists()
        
        # Verify tracking was cleared
        assert len(cleanup_manager._temp_files) == 0
        assert len(cleanup_manager._temp_directories) == 0
    
    def test_cleanup_summary_integration(self):
        """Test that cleanup summary provides accurate information."""
        tool = GamingSetupTool()
        
        # Register various items
        tool.cleanup_manager.register_temp_file(Path("/temp/file1.txt"), "component1")
        tool.cleanup_manager.register_temp_file(Path("/temp/file2.txt"), "component2")
        tool.cleanup_manager.register_temp_directory(Path("/temp/dir1"), "component1")
        tool.cleanup_manager.register_created_file(Path("/created/file.txt"), "setup")
        
        # Get summary
        summary = tool.cleanup_manager.get_cleanup_summary()
        
        # Verify summary accuracy
        assert summary['temp_files'] == 2
        assert summary['temp_directories'] == 1
        assert summary['created_files'] == 1
        assert summary['created_directories'] == 0
        assert summary['custom_operations'] == 0
        assert summary['total_items'] == 4
    
    @pytest.mark.asyncio
    async def test_context_manager_integration(self, temp_dir):
        """Test that context managers work properly in integration scenarios."""
        tool = GamingSetupTool()
        
        # Mock the cleanup method to avoid Rich console issues
        with patch.object(tool.cleanup_manager, 'cleanup_temp_files') as mock_cleanup:
            mock_cleanup.return_value = AsyncMock()
            
            # Use the temp file context manager
            async with tool.cleanup_manager.temp_file_context(temp_dir) as temp_files:
                # Create a test file
                test_file = temp_dir / "context_test.txt"
                test_file.write_text("test content")
                temp_files.append(test_file)
                
                # Verify file exists during context
                assert test_file.exists()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])