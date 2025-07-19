"""
Integration tests for FileOperationsManager.

These tests verify the actual functionality without complex mocking.
"""

import pytest
import asyncio
import tempfile
import zipfile
from pathlib import Path
from rich.console import Console

from file_operations_manager import FileOperationsManager
from models import SetupResults


class TestFileOperationsIntegration:
    """Integration tests for FileOperationsManager."""
    
    @pytest.fixture
    def console(self):
        """Create a real Rich console for testing."""
        return Console(file=open('nul', 'w') if hasattr(__builtins__, 'open') else None, force_terminal=False)
    
    @pytest.fixture
    def file_manager(self, console):
        """Create FileOperationsManager instance."""
        return FileOperationsManager(console)
    
    @pytest.fixture
    def setup_results(self):
        """Create a SetupResults instance for testing."""
        return SetupResults()
    
    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_create_directories_integration(self, file_manager, setup_results, temp_directory):
        """Test directory creation integration."""
        # Arrange
        test_dirs = [
            temp_directory / "test_dir1",
            temp_directory / "test_dir2" / "subdir",
            temp_directory / "test_dir3"
        ]
        
        # Act
        await file_manager.create_directories(test_dirs, setup_results)
        
        # Assert
        for test_dir in test_dirs:
            assert test_dir.exists()
            assert test_dir.is_dir()
        
        assert len(setup_results.directories_created) == 3
        assert len(setup_results.errors) == 0
    
    @pytest.mark.asyncio
    async def test_extract_archive_flattened_integration(self, file_manager, setup_results, temp_directory):
        """Test archive extraction with flattened structure."""
        # Arrange
        archive_path = temp_directory / "test.zip"
        extract_dir = temp_directory / "extracted"
        
        # Create a test zip file with nested structure
        with zipfile.ZipFile(archive_path, 'w') as zip_ref:
            zip_ref.writestr("folder1/file1.txt", "content1")
            zip_ref.writestr("folder2/subfolder/file2.txt", "content2")
            zip_ref.writestr("file3.txt", "content3")
        
        # Act
        result = await file_manager.extract_archive(
            archive_path, extract_dir, flatten=True, results=setup_results
        )
        
        # Assert
        assert result is True
        assert setup_results.files_extracted is True
        
        # Check flattened structure
        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "file2.txt").exists()
        assert (extract_dir / "file3.txt").exists()
        
        # Verify content
        assert (extract_dir / "file1.txt").read_text() == "content1"
        assert (extract_dir / "file2.txt").read_text() == "content2"
        assert (extract_dir / "file3.txt").read_text() == "content3"
        
        # Ensure no nested directories
        assert not (extract_dir / "folder1").exists()
        assert not (extract_dir / "folder2").exists()
    
    @pytest.mark.asyncio
    async def test_extract_archive_normal_integration(self, file_manager, setup_results, temp_directory):
        """Test archive extraction with normal structure."""
        # Arrange
        archive_path = temp_directory / "test.zip"
        extract_dir = temp_directory / "extracted"
        
        # Create a test zip file with nested structure
        with zipfile.ZipFile(archive_path, 'w') as zip_ref:
            zip_ref.writestr("folder1/file1.txt", "content1")
            zip_ref.writestr("folder2/subfolder/file2.txt", "content2")
        
        # Act
        result = await file_manager.extract_archive(
            archive_path, extract_dir, flatten=False, results=setup_results
        )
        
        # Assert
        assert result is True
        assert setup_results.files_extracted is True
        
        # Check normal structure preserved
        assert (extract_dir / "folder1" / "file1.txt").exists()
        assert (extract_dir / "folder2" / "subfolder" / "file2.txt").exists()
        
        # Verify content
        assert (extract_dir / "folder1" / "file1.txt").read_text() == "content1"
        assert (extract_dir / "folder2" / "subfolder" / "file2.txt").read_text() == "content2"
    
    @pytest.mark.asyncio
    async def test_extract_archive_missing_file(self, file_manager, setup_results, temp_directory):
        """Test archive extraction when file doesn't exist."""
        # Arrange
        archive_path = temp_directory / "nonexistent.zip"
        extract_dir = temp_directory / "extracted"
        
        # Act
        result = await file_manager.extract_archive(
            archive_path, extract_dir, results=setup_results
        )
        
        # Assert
        assert result is False
        assert len(setup_results.errors) == 1
        assert "not found" in setup_results.errors[0]
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_integration(self, file_manager, temp_directory):
        """Test file integrity verification."""
        # Test valid file
        test_file = temp_directory / "test.txt"
        test_content = b"test content"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        result = await file_manager.verify_file_integrity(
            test_file, expected_size=len(test_content)
        )
        assert result is True
        
        # Test missing file
        missing_file = temp_directory / "missing.txt"
        result = await file_manager.verify_file_integrity(missing_file)
        assert result is False
        
        # Test empty file
        empty_file = temp_directory / "empty.txt"
        empty_file.touch()
        result = await file_manager.verify_file_integrity(empty_file)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_zip_file_integrity(self, file_manager, temp_directory):
        """Test zip file integrity verification."""
        # Create valid zip file
        zip_file = temp_directory / "test.zip"
        with zipfile.ZipFile(zip_file, 'w') as zip_ref:
            zip_ref.writestr("test.txt", "content")
        
        result = await file_manager.verify_file_integrity(zip_file)
        assert result is True
        
        # Create invalid zip file
        bad_zip = temp_directory / "bad.zip"
        with open(bad_zip, 'w') as f:
            f.write("not a zip file")
        
        result = await file_manager.verify_file_integrity(bad_zip)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files_integration(self, file_manager, temp_directory):
        """Test temporary file cleanup."""
        # Create test files and directory
        temp_files = [
            temp_directory / "temp1.txt",
            temp_directory / "temp2.txt",
            temp_directory / "temp_dir"
        ]
        
        temp_files[0].touch()
        temp_files[1].touch()
        temp_files[2].mkdir()
        (temp_files[2] / "nested.txt").touch()
        
        # Verify files exist
        for temp_file in temp_files:
            assert temp_file.exists()
        
        # Act
        await file_manager.cleanup_temp_files(temp_files)
        
        # Assert
        for temp_file in temp_files:
            assert not temp_file.exists()
    
    @pytest.mark.asyncio
    async def test_temp_file_manager_context_integration(self, file_manager, temp_directory):
        """Test temporary file manager context."""
        temp_dir = temp_directory / "temp"
        
        async with file_manager.temp_file_manager(temp_dir) as temp_files:
            # Create some temporary files
            temp_file1 = temp_dir / "temp1.txt"
            temp_file2 = temp_dir / "temp2.txt"
            
            temp_file1.touch()
            temp_file2.touch()
            
            # Add to tracking list
            temp_files.extend([temp_file1, temp_file2])
            
            # Verify files exist during context
            assert temp_file1.exists()
            assert temp_file2.exists()
        
        # Assert files are cleaned up after context
        assert not temp_file1.exists()
        assert not temp_file2.exists()


if __name__ == "__main__":
    pytest.main([__file__])