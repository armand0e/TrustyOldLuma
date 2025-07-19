"""
Unit tests for the FileOperationsManager class.

This module contains comprehensive tests for file operations including
directory creation, archive extraction, and download functionality.
"""

import pytest
import asyncio
import zipfile
import tempfile
import aiohttp
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from rich.console import Console

from file_operations_manager import FileOperationsManager
from models import LunaResults


class TestFileOperationsManager:
    """Test suite for FileOperationsManager."""
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = Mock(spec=Console)
        console.get_time = Mock(return_value=0.0)
        console.is_jupyter = False
        console.set_live = Mock()
        console.show_cursor = Mock()
        console.push_render_hook = Mock()
        console.clear_live = Mock()
        console.input = Mock(return_value="n")  # Default to "no" for retry prompts
        console.__enter__ = Mock(return_value=console)
        console.__exit__ = Mock(return_value=None)
        return console
    
    @pytest.fixture
    def file_manager(self, mock_console):
        """Create FileOperationsManager instance with mocked console."""
        return FileOperationsManager(mock_console)
    
    @pytest.fixture
    def setup_results(self):
        """Create a LunaResults instance for testing."""
        return LunaResults()
    
    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_create_directories_success(self, file_manager, setup_results, temp_directory):
        """Test successful directory creation."""
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
        assert all(dir_path in setup_results.directories_created for dir_path in test_dirs)
        assert len(setup_results.errors) == 0
    
    @pytest.mark.asyncio
    async def test_create_directories_already_exists(self, file_manager, setup_results, temp_directory):
        """Test directory creation when directories already exist."""
        # Arrange
        existing_dir = temp_directory / "existing_dir"
        existing_dir.mkdir()
        test_dirs = [existing_dir, temp_directory / "new_dir"]
        
        # Act
        await file_manager.create_directories(test_dirs, setup_results)
        
        # Assert
        assert len(setup_results.directories_created) == 2
        assert len(setup_results.errors) == 0
    
    @pytest.mark.asyncio
    async def test_create_directories_file_exists(self, file_manager, setup_results, temp_directory):
        """Test directory creation when a file exists with the same name."""
        # Arrange
        file_path = temp_directory / "test_file"
        file_path.touch()  # Create a file
        test_dirs = [file_path]
        
        # Act
        await file_manager.create_directories(test_dirs, setup_results)
        
        # Assert
        assert len(setup_results.directories_created) == 0
        assert len(setup_results.errors) == 1
        assert "not a directory" in setup_results.errors[0]
    
    @pytest.mark.asyncio
    async def test_extract_archive_success_flattened(self, file_manager, setup_results, temp_directory):
        """Test successful archive extraction with flattened structure."""
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
        
        # Ensure no nested directories
        assert not (extract_dir / "folder1").exists()
        assert not (extract_dir / "folder2").exists()
    
    @pytest.mark.asyncio
    async def test_extract_archive_success_normal(self, file_manager, setup_results, temp_directory):
        """Test successful archive extraction with normal structure."""
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
    
    @pytest.mark.asyncio
    async def test_extract_archive_file_not_found(self, file_manager, setup_results, temp_directory):
        """Test archive extraction when archive file doesn't exist."""
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
    async def test_extract_archive_bad_zip(self, file_manager, setup_results, temp_directory):
        """Test archive extraction with corrupted zip file."""
        # Arrange
        archive_path = temp_directory / "bad.zip"
        extract_dir = temp_directory / "extracted"
        
        # Create a file that's not a valid zip
        with open(archive_path, 'w') as f:
            f.write("This is not a zip file")
        
        # Act
        result = await file_manager.extract_archive(
            archive_path, extract_dir, results=setup_results
        )
        
        # Assert
        assert result is False
        assert len(setup_results.errors) == 1
        assert "corrupted" in setup_results.errors[0]
    
    @pytest.mark.asyncio
    async def test_download_file_success(self, file_manager, setup_results, temp_directory):
        """Test successful file download."""
        # Arrange
        url = "https://example.com/test.exe"
        filename = "test.exe"
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'content-length': '1024'}
        
        # Create async iterator for chunks
        async def async_iter_chunked(size):
            yield b'test_data_chunk'
        
        mock_response.content.iter_chunked = async_iter_chunked
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Mock aiofiles
            with patch('aiofiles.open', create=True) as mock_aiofiles:
                mock_file = AsyncMock()
                mock_aiofiles.return_value.__aenter__.return_value = mock_file
                
                # Act
                result = await file_manager.download_file(
                    url, temp_directory, filename, setup_results
                )
        
        # Assert
        assert result is True
        assert len(setup_results.files_downloaded) == 1
        assert setup_results.files_downloaded[0] == (url, True)
    
    @pytest.mark.asyncio
    async def test_download_file_http_error(self, file_manager, setup_results, temp_directory):
        """Test file download with HTTP error."""
        # Arrange
        url = "https://example.com/notfound.exe"
        
        # Mock aiohttp response with 404 error
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.request_info = Mock()
        mock_response.history = []
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Mock the retry prompt to return False (don't retry)
            with patch.object(file_manager.error_manager, 'display_retry_prompt', return_value=False):
                # Act
                result = await file_manager.download_file(
                    url, temp_directory, results=setup_results
                )
        
        # Assert
        assert result is False
        assert len(setup_results.files_downloaded) == 1
        assert setup_results.files_downloaded[0] == (url, False)
        assert len(setup_results.errors) == 1
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_success(self, file_manager, temp_directory):
        """Test file integrity verification for valid file."""
        # Arrange
        test_file = temp_directory / "test.txt"
        test_content = b"test content"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # Act
        result = await file_manager.verify_file_integrity(
            test_file, expected_size=len(test_content)
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_missing_file(self, file_manager, temp_directory):
        """Test file integrity verification for missing file."""
        # Arrange
        missing_file = temp_directory / "missing.txt"
        
        # Act
        result = await file_manager.verify_file_integrity(missing_file)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_empty_file(self, file_manager, temp_directory):
        """Test file integrity verification for empty file."""
        # Arrange
        empty_file = temp_directory / "empty.txt"
        empty_file.touch()
        
        # Act
        result = await file_manager.verify_file_integrity(empty_file)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_zip_file(self, file_manager, temp_directory):
        """Test file integrity verification for zip file."""
        # Arrange
        zip_file = temp_directory / "test.zip"
        
        with zipfile.ZipFile(zip_file, 'w') as zip_ref:
            zip_ref.writestr("test.txt", "content")
        
        # Act
        result = await file_manager.verify_file_integrity(zip_file)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_file_integrity_bad_zip(self, file_manager, temp_directory):
        """Test file integrity verification for corrupted zip file."""
        # Arrange
        bad_zip = temp_directory / "bad.zip"
        
        with open(bad_zip, 'w') as f:
            f.write("not a zip file")
        
        # Act
        result = await file_manager.verify_file_integrity(bad_zip)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, file_manager, temp_directory):
        """Test temporary file cleanup."""
        # Arrange
        temp_files = [
            temp_directory / "temp1.txt",
            temp_directory / "temp2.txt",
            temp_directory / "temp_dir"
        ]
        
        # Create test files and directory
        temp_files[0].touch()
        temp_files[1].touch()
        temp_files[2].mkdir()
        (temp_files[2] / "nested.txt").touch()
        
        # Act
        await file_manager.cleanup_temp_files(temp_files)
        
        # Assert
        for temp_file in temp_files:
            assert not temp_file.exists()
    
    @pytest.mark.asyncio
    async def test_temp_file_manager_context(self, file_manager, temp_directory):
        """Test temporary file manager context."""
        # Arrange
        temp_dir = temp_directory / "temp"
        
        # Act
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
    
    @pytest.mark.asyncio
    async def test_create_directories_empty_list(self, file_manager, setup_results):
        """Test directory creation with empty list."""
        # Act
        await file_manager.create_directories([], setup_results)
        
        # Assert
        assert len(setup_results.directories_created) == 0
        assert len(setup_results.errors) == 0
    
    @pytest.mark.asyncio
    async def test_download_file_filename_from_url(self, file_manager, setup_results, temp_directory):
        """Test download file with filename extracted from URL."""
        # Arrange
        url = "https://example.com/path/to/file.exe"
        
        # Mock successful download
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'content-length': '100'}
        
        # Create async iterator for chunks
        async def async_iter_chunked(size):
            yield b'data'
        
        mock_response.content.iter_chunked = async_iter_chunked
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            with patch('aiofiles.open', create=True) as mock_aiofiles:
                mock_file = AsyncMock()
                mock_aiofiles.return_value.__aenter__.return_value = mock_file
                
                # Act
                result = await file_manager.download_file(
                    url, temp_directory, results=setup_results
                )
        
        # Assert
        assert result is True
        # Verify the filename was extracted correctly
        expected_path = temp_directory / "file.exe"
        mock_aiofiles.assert_called_with(expected_path, 'wb')


if __name__ == "__main__":
    pytest.main([__file__])