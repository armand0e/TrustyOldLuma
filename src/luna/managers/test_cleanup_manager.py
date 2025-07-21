"""
Unit tests for the CleanupManager class.

This module contains comprehensive tests for cleanup operations, temporary file management,
resource management with context managers, and error handling.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, call
from rich.console import Console

from cleanup_manager import CleanupManager, CleanupOperation, CleanupResults
from models import LunaResults
from exceptions import FileOperationError, GamingSetupError


class TestCleanupOperation:
    """Test the CleanupOperation dataclass."""
    
    def test_cleanup_operation_creation(self):
        """Test creating a cleanup operation."""
        operation = CleanupOperation(
            path=Path("/test/path"),
            operation_type="file",
            description="Test cleanup operation"
        )
        
        assert operation.path == Path("/test/path")
        assert operation.operation_type == "file"
        assert operation.description == "Test cleanup operation"
        assert operation.critical is False
        assert operation.created_by is None
    
    def test_cleanup_operation_with_metadata(self):
        """Test creating a cleanup operation with metadata."""
        operation = CleanupOperation(
            path=Path("/test/path"),
            operation_type="directory",
            description="Test cleanup operation",
            critical=True,
            created_by="test_component"
        )
        
        assert operation.critical is True
        assert operation.created_by == "test_component"
    
    def test_cleanup_operation_validation(self):
        """Test cleanup operation validation."""
        # Test empty operation type
        with pytest.raises(ValueError, match="Operation type cannot be empty"):
            CleanupOperation(
                path=Path("/test"),
                operation_type="",
                description="Test"
            )
        
        # Test empty description
        with pytest.raises(ValueError, match="Description cannot be empty"):
            CleanupOperation(
                path=Path("/test"),
                operation_type="file",
                description=""
            )


class TestCleanupResults:
    """Test the CleanupResults dataclass."""
    
    def test_cleanup_results_creation(self):
        """Test creating cleanup results."""
        results = CleanupResults()
        
        assert results.operations_attempted == 0
        assert results.operations_successful == 0
        assert results.operations_failed == 0
        assert results.errors == []
        assert results.warnings == []
        assert results.cleaned_paths == []
        assert results.failed_paths == []
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        results = CleanupResults()
        
        # No operations - should be 100%
        assert results.success_rate == 1.0
        
        # Add some operations
        results.operations_attempted = 10
        results.operations_successful = 8
        results.operations_failed = 2
        
        assert results.success_rate == 0.8
    
    def test_add_success(self):
        """Test adding successful operations."""
        results = CleanupResults()
        path = Path("/test/path")
        
        results.add_success(path)
        
        assert results.operations_successful == 1
        assert path in results.cleaned_paths
    
    def test_add_failure(self):
        """Test adding failed operations."""
        results = CleanupResults()
        path = Path("/test/path")
        error = "Test error"
        
        results.add_failure(path, error)
        
        assert results.operations_failed == 1
        assert path in results.failed_paths
        assert f"Failed to clean {path}: {error}" in results.errors
    
    def test_add_warning(self):
        """Test adding warnings."""
        results = CleanupResults()
        warning = "Test warning"
        
        results.add_warning(warning)
        
        assert warning in results.warnings


class TestCleanupManager:
    """Test the CleanupManager class."""
    
    @pytest.fixture
    def console(self):
        """Create a mock console for testing."""
        mock_console = Mock(spec=Console)
        mock_console.get_time = Mock(return_value=0.0)
        mock_console.is_jupyter = False
        mock_console.set_live = Mock()
        mock_console.clear_live = Mock()
        mock_console.show_cursor = Mock()
        mock_console.push_render_hook = Mock()
        mock_console.__enter__ = Mock(return_value=mock_console)
        mock_console.__exit__ = Mock(return_value=None)
        return mock_console
    
    @pytest.fixture
    def cleanup_manager(self, console):
        """Create a CleanupManager instance for testing."""
        return CleanupManager(console)
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup after test
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    def test_cleanup_manager_initialization(self, cleanup_manager, console):
        """Test CleanupManager initialization."""
        assert cleanup_manager.console == console
        assert cleanup_manager.progress_manager is not None
        assert cleanup_manager.error_manager is not None
        assert cleanup_manager.logger is not None
        assert len(cleanup_manager._temp_files) == 0
        assert len(cleanup_manager._temp_directories) == 0
    
    def test_register_temp_file(self, cleanup_manager):
        """Test registering temporary files."""
        file_path = Path("/test/temp_file.txt")
        
        cleanup_manager.register_temp_file(file_path, "test_component")
        
        assert file_path in cleanup_manager._temp_files
        assert cleanup_manager._creation_metadata[file_path] == "test_component"
    
    def test_register_temp_directory(self, cleanup_manager):
        """Test registering temporary directories."""
        dir_path = Path("/test/temp_dir")
        
        cleanup_manager.register_temp_directory(dir_path, "test_component")
        
        assert dir_path in cleanup_manager._temp_directories
        assert cleanup_manager._creation_metadata[dir_path] == "test_component"
    
    def test_register_created_file(self, cleanup_manager):
        """Test registering created files."""
        file_path = Path("/test/created_file.txt")
        
        cleanup_manager.register_created_file(file_path, "test_component")
        
        assert file_path in cleanup_manager._created_files
        assert cleanup_manager._creation_metadata[file_path] == "test_component"
    
    def test_register_created_directory(self, cleanup_manager):
        """Test registering created directories."""
        dir_path = Path("/test/created_dir")
        
        cleanup_manager.register_created_directory(dir_path, "test_component")
        
        assert dir_path in cleanup_manager._created_directories
        assert cleanup_manager._creation_metadata[dir_path] == "test_component"
    
    def test_add_cleanup_operation(self, cleanup_manager):
        """Test adding custom cleanup operations."""
        operation = CleanupOperation(
            path=Path("/test/path"),
            operation_type="file",
            description="Test operation"
        )
        
        cleanup_manager.add_cleanup_operation(operation)
        
        assert operation in cleanup_manager._cleanup_operations
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files_success(self, cleanup_manager, temp_dir):
        """Test successful temporary file cleanup."""
        # Create test files
        test_file1 = temp_dir / "test1.txt"
        test_file2 = temp_dir / "test2.txt"
        test_file1.write_text("test content")
        test_file2.write_text("test content")
        
        # Register files for cleanup
        cleanup_manager.register_temp_file(test_file1)
        cleanup_manager.register_temp_file(test_file2)
        
        # Mock progress manager
        with patch.object(cleanup_manager.progress_manager, 'create_progress_bar') as mock_progress:
            mock_context = Mock()
            mock_progress.return_value.__enter__ = Mock(return_value=mock_context)
            mock_progress.return_value.__exit__ = Mock(return_value=None)
            
            # Perform cleanup
            results = await cleanup_manager.cleanup_temp_files()
        
        # Verify results
        assert results.operations_attempted == 2
        assert results.operations_successful == 2
        assert results.operations_failed == 0
        assert not test_file1.exists()
        assert not test_file2.exists()
        assert len(cleanup_manager._temp_files) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files_with_additional(self, cleanup_manager, temp_dir):
        """Test cleanup with additional files."""
        # Create test files
        registered_file = temp_dir / "registered.txt"
        additional_file = temp_dir / "additional.txt"
        registered_file.write_text("test")
        additional_file.write_text("test")
        
        # Register one file
        cleanup_manager.register_temp_file(registered_file)
        
        # Mock progress manager
        with patch.object(cleanup_manager.progress_manager, 'create_progress_bar') as mock_progress:
            mock_context = Mock()
            mock_progress.return_value.__enter__ = Mock(return_value=mock_context)
            mock_progress.return_value.__exit__ = Mock(return_value=None)
            
            # Cleanup with additional file
            results = await cleanup_manager.cleanup_temp_files([additional_file])
        
        # Verify both files were cleaned
        assert results.operations_attempted == 2
        assert results.operations_successful == 2
        assert not registered_file.exists()
        assert not additional_file.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files_nonexistent(self, cleanup_manager):
        """Test cleanup of non-existent files."""
        nonexistent_file = Path("/nonexistent/file.txt")
        cleanup_manager.register_temp_file(nonexistent_file)
        
        with patch.object(cleanup_manager.progress_manager, 'create_progress_bar') as mock_progress:
            mock_context = Mock()
            mock_progress.return_value.__enter__ = Mock(return_value=mock_context)
            mock_progress.return_value.__exit__ = Mock(return_value=None)
            
            results = await cleanup_manager.cleanup_temp_files()
        
        # Should handle gracefully
        assert results.operations_attempted == 1
        assert results.operations_successful == 0
        assert results.operations_failed == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_directories_success(self, cleanup_manager, temp_dir):
        """Test successful temporary directory cleanup."""
        # Create test directories
        test_dir1 = temp_dir / "test_dir1"
        test_dir2 = temp_dir / "test_dir2"
        test_dir1.mkdir()
        test_dir2.mkdir()
        
        # Add some files to directories
        (test_dir1 / "file.txt").write_text("test")
        (test_dir2 / "file.txt").write_text("test")
        
        # Register directories for cleanup
        cleanup_manager.register_temp_directory(test_dir1)
        cleanup_manager.register_temp_directory(test_dir2)
        
        with patch.object(cleanup_manager.progress_manager, 'create_progress_bar') as mock_progress:
            mock_context = Mock()
            mock_progress.return_value.__enter__ = Mock(return_value=mock_context)
            mock_progress.return_value.__exit__ = Mock(return_value=None)
            
            results = await cleanup_manager.cleanup_temp_directories()
        
        # Verify results
        assert results.operations_attempted == 2
        assert results.operations_successful == 2
        assert results.operations_failed == 0
        assert not test_dir1.exists()
        assert not test_dir2.exists()
        assert len(cleanup_manager._temp_directories) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_failed_installation(self, cleanup_manager, temp_dir):
        """Test cleanup after failed installation."""
        # Create setup results with some operations
        setup_results = LunaResults()
        
        # Add some directories that were created
        created_dir = temp_dir / "created_dir"
        created_dir.mkdir()
        setup_results.directories_created.append(created_dir)
        
        # Add some download results
        setup_results.files_downloaded.append(("http://example.com/file.exe", True))
        
        # Register some temp files
        temp_file = temp_dir / "temp_file.txt"
        temp_file.write_text("test")
        cleanup_manager.register_temp_file(temp_file)
        
        with patch.object(cleanup_manager.progress_manager, 'create_progress_bar') as mock_progress:
            mock_context = Mock()
            mock_progress.return_value.__enter__ = Mock(return_value=mock_context)
            mock_progress.return_value.__exit__ = Mock(return_value=None)
            
            results = await cleanup_manager.cleanup_failed_installation(setup_results)
        
        # Verify cleanup was attempted
        assert results.operations_attempted >= 2  # At least temp file and created directory
        assert not created_dir.exists()
        assert not temp_file.exists()
        
        # Verify tracking was cleared
        assert len(cleanup_manager._temp_files) == 0
        assert len(cleanup_manager._temp_directories) == 0
        assert len(cleanup_manager._created_files) == 0
        assert len(cleanup_manager._created_directories) == 0
    
    @pytest.mark.asyncio
    async def test_validate_cleanup_success(self, cleanup_manager):
        """Test cleanup validation with successful cleanup."""
        results = CleanupResults()
        
        # Add some cleaned paths that don't exist
        results.cleaned_paths = [Path("/nonexistent1"), Path("/nonexistent2")]
        
        with patch.object(cleanup_manager.progress_manager, 'show_spinner') as mock_spinner:
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            
            is_valid = await cleanup_manager.validate_cleanup(results)
        
        assert is_valid is True
        assert len(results.warnings) == 0
    
    @pytest.mark.asyncio
    async def test_validate_cleanup_failure(self, cleanup_manager, temp_dir):
        """Test cleanup validation with failed cleanup."""
        results = CleanupResults()
        
        # Create a file that should have been cleaned
        existing_file = temp_dir / "should_be_cleaned.txt"
        existing_file.write_text("test")
        results.cleaned_paths = [existing_file]
        
        with patch.object(cleanup_manager.progress_manager, 'show_spinner') as mock_spinner:
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            
            is_valid = await cleanup_manager.validate_cleanup(results)
        
        assert is_valid is False
        assert len(results.warnings) > 0
        assert "still exists after cleanup" in results.warnings[0]
    
    @pytest.mark.asyncio
    async def test_temp_file_context_manager(self, cleanup_manager, temp_dir):
        """Test the temporary file context manager."""
        test_file = temp_dir / "context_test.txt"
        
        # Mock the cleanup_temp_files method to avoid Rich console issues
        with patch.object(cleanup_manager, 'cleanup_temp_files') as mock_cleanup:
            mock_cleanup.return_value = CleanupResults()
            
            # Use context manager
            async with cleanup_manager.temp_file_context(temp_dir) as temp_files:
                # Create a file and add it to tracking
                test_file.write_text("test content")
                temp_files.append(test_file)
                
                # File should exist during context
                assert test_file.exists()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()
        
        # Since we mocked cleanup, file should still exist
        assert test_file.exists()
        
        # Clean up manually for test
        test_file.unlink()
    
    @pytest.mark.asyncio
    async def test_temp_file_context_no_auto_cleanup(self, cleanup_manager, temp_dir):
        """Test the temporary file context manager without auto cleanup."""
        test_file = temp_dir / "context_test.txt"
        
        # Use context manager with auto_cleanup=False
        async with cleanup_manager.temp_file_context(temp_dir, auto_cleanup=False) as temp_files:
            test_file.write_text("test content")
            temp_files.append(test_file)
        
        # File should still exist after context
        assert test_file.exists()
    
    @pytest.mark.asyncio
    async def test_installation_context_success(self, cleanup_manager):
        """Test installation context manager with successful installation."""
        setup_results = LunaResults()
        
        # Should not raise any exceptions
        async with cleanup_manager.installation_context(setup_results):
            # Simulate successful installation
            pass
    
    @pytest.mark.asyncio
    async def test_installation_context_failure(self, cleanup_manager, temp_dir):
        """Test installation context manager with failed installation."""
        setup_results = LunaResults()
        
        # Create some items that would need cleanup
        created_dir = temp_dir / "created_dir"
        created_dir.mkdir()
        setup_results.directories_created.append(created_dir)
        
        temp_file = temp_dir / "temp_file.txt"
        temp_file.write_text("test")
        cleanup_manager.register_temp_file(temp_file)
        
        # Mock the cleanup method to avoid actual cleanup during test
        with patch.object(cleanup_manager, 'cleanup_failed_installation') as mock_cleanup:
            mock_cleanup.return_value = CleanupResults()
            
            # Should catch exception and perform cleanup
            with pytest.raises(ValueError):
                async with cleanup_manager.installation_context(setup_results):
                    raise ValueError("Installation failed")
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once_with(setup_results)
    
    def test_get_cleanup_summary(self, cleanup_manager):
        """Test getting cleanup summary."""
        # Register various items
        cleanup_manager.register_temp_file(Path("/temp/file1.txt"))
        cleanup_manager.register_temp_file(Path("/temp/file2.txt"))
        cleanup_manager.register_temp_directory(Path("/temp/dir1"))
        cleanup_manager.register_created_file(Path("/created/file.txt"))
        cleanup_manager.register_created_directory(Path("/created/dir"))
        
        operation = CleanupOperation(
            path=Path("/custom/path"),
            operation_type="file",
            description="Custom operation"
        )
        cleanup_manager.add_cleanup_operation(operation)
        
        summary = cleanup_manager.get_cleanup_summary()
        
        assert summary['temp_files'] == 2
        assert summary['temp_directories'] == 1
        assert summary['created_files'] == 1
        assert summary['created_directories'] == 1
        assert summary['custom_operations'] == 1
        assert summary['total_items'] == 6
    
    @pytest.mark.asyncio
    async def test_cleanup_single_file_permission_error(self, cleanup_manager, temp_dir):
        """Test cleanup with permission errors."""
        test_file = temp_dir / "permission_test.txt"
        test_file.write_text("test")
        
        # Mock permission error
        with patch('pathlib.Path.unlink', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                await cleanup_manager._cleanup_single_file(test_file, Mock())
    
    @pytest.mark.asyncio
    async def test_cleanup_single_directory_permission_error(self, cleanup_manager, temp_dir):
        """Test directory cleanup with permission errors."""
        test_dir = temp_dir / "permission_test_dir"
        test_dir.mkdir()
        
        # Mock permission error
        with patch('shutil.rmtree', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                await cleanup_manager._cleanup_single_directory(test_dir, Mock())
    
    @pytest.mark.asyncio
    async def test_perform_cleanup_operation_unknown_type(self, cleanup_manager):
        """Test cleanup operation with unknown operation type."""
        operation = CleanupOperation(
            path=Path("/test/path"),
            operation_type="unknown_type",
            description="Unknown operation"
        )
        
        result = await cleanup_manager._perform_cleanup_operation(operation, Mock())
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])