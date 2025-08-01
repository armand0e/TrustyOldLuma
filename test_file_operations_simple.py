"""Simple tests for File Operations Manager to verify core functionality."""

import json
import tempfile
import zipfile
from configparser import ConfigParser
from pathlib import Path
from unittest.mock import Mock
import pytest

from src.file_operations import FileOperationsManager
from src.ui_manager import UIManager


class TestFileOperationsManagerSimple:
    """Simple test cases for FileOperationsManager core functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ui = Mock(spec=UIManager)
        # Mock the progress bar to return a simple context manager
        self.mock_ui.show_progress_bar.return_value.__enter__ = Mock(return_value=Mock())
        self.mock_ui.show_progress_bar.return_value.__exit__ = Mock(return_value=None)
        self.file_ops = FileOperationsManager(self.mock_ui)
        
    def test_extract_archive_success(self):
        """Test successful ZIP archive extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test ZIP file
            zip_path = temp_path / "test.zip"
            extract_path = temp_path / "extracted"
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file1.txt", "content1")
                zf.writestr("subdir/file2.txt", "content2")
                
            # Test extraction
            result = self.file_ops.extract_archive(str(zip_path), str(extract_path))
            
            assert result is True
            assert (extract_path / "file1.txt").exists()
            assert (extract_path / "subdir" / "file2.txt").exists()
            assert (extract_path / "file1.txt").read_text() == "content1"
            assert (extract_path / "subdir" / "file2.txt").read_text() == "content2"
            
    def test_extract_archive_file_not_found(self):
        """Test extraction with non-existent archive."""
        result = self.file_ops.extract_archive("nonexistent.zip", "/tmp/extract")
        
        assert result is False
        self.mock_ui.display_error.assert_called_once()
        
    def test_create_directory_structure_success(self):
        """Test successful directory structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            directories = ["dir1", "dir2/subdir", "dir3"]
            
            result = self.file_ops.create_directory_structure(str(base_path), directories)
            
            assert result is True
            assert base_path.exists()
            assert (base_path / "dir1").exists()
            assert (base_path / "dir2" / "subdir").exists()
            assert (base_path / "dir3").exists()
            
    def test_create_directory_structure_base_only(self):
        """Test creating only base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            
            result = self.file_ops.create_directory_structure(str(base_path))
            
            assert result is True
            assert base_path.exists()
            
    def test_copy_single_file_success(self):
        """Test successful single file copy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")
            
            dest_file = temp_path / "dest.txt"
            
            result = self.file_ops.copy_files(str(source_file), str(dest_file))
            
            assert result is True
            assert dest_file.exists()
            assert dest_file.read_text() == "test content"
            
    def test_copy_specific_files_success(self):
        """Test copying specific files from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source directory with files
            source_dir = temp_path / "source"
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "file2.txt").write_text("content2")
            (source_dir / "file3.txt").write_text("content3")
            
            dest_dir = temp_path / "dest"
            files_to_copy = ["file1.txt", "file3.txt"]
            
            result = self.file_ops.copy_files(str(source_dir), str(dest_dir), files_to_copy)
            
            assert result is True
            assert (dest_dir / "file1.txt").exists()
            assert (dest_dir / "file3.txt").exists()
            assert not (dest_dir / "file2.txt").exists()
            assert (dest_dir / "file1.txt").read_text() == "content1"
            assert (dest_dir / "file3.txt").read_text() == "content3"
            
    def test_update_json_config_success(self):
        """Test successful JSON config update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create initial config
            initial_config = {"key1": "value1", "nested": {"key2": "value2"}}
            config_path.write_text(json.dumps(initial_config))
            
            updates = {"key1": "updated_value1", "nested": {"key3": "value3"}, "new_key": "new_value"}
            
            result = self.file_ops.update_config_file(str(config_path), updates)
            
            assert result is True
            
            # Verify updates
            updated_config = json.loads(config_path.read_text())
            assert updated_config["key1"] == "updated_value1"
            assert updated_config["nested"]["key2"] == "value2"  # Preserved
            assert updated_config["nested"]["key3"] == "value3"  # Added
            assert updated_config["new_key"] == "new_value"  # Added
            
    def test_update_ini_config_success(self):
        """Test successful INI config update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            
            # Create initial config
            config = ConfigParser()
            config['DEFAULT'] = {'key1': 'value1'}
            config['section1'] = {'key2': 'value2'}
            
            with open(config_path, 'w') as f:
                config.write(f)
                
            updates = {
                'key1': 'updated_value1',
                'section1': {'key2': 'updated_value2', 'key3': 'value3'},
                'section2': {'key4': 'value4'}
            }
            
            result = self.file_ops.update_config_file(str(config_path), updates, "ini")
            
            assert result is True
            
            # Verify updates
            updated_config = ConfigParser()
            updated_config.read(config_path)
            
            assert updated_config['DEFAULT']['key1'] == 'updated_value1'
            assert updated_config['section1']['key2'] == 'updated_value2'
            assert updated_config['section1']['key3'] == 'value3'
            assert updated_config['section2']['key4'] == 'value4'
            
    def test_update_config_auto_detect_json(self):
        """Test auto-detection of JSON config type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text('{"key": "value"}')
            
            updates = {"key": "updated_value"}
            
            result = self.file_ops.update_config_file(str(config_path), updates)
            
            assert result is True
            updated_config = json.loads(config_path.read_text())
            assert updated_config["key"] == "updated_value"
            
    def test_update_config_auto_detect_ini(self):
        """Test auto-detection of INI config type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            config_path.write_text('[DEFAULT]\nkey = value\n')
            
            updates = {"key": "updated_value"}
            
            result = self.file_ops.update_config_file(str(config_path), updates)
            
            assert result is True
            
            updated_config = ConfigParser()
            updated_config.read(config_path)
            assert updated_config['DEFAULT']['key'] == 'updated_value'
            
    def test_get_file_size(self):
        """Test getting file size."""
        with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            
            size = self.file_ops.get_file_size(temp_file.name)
            assert size > 0
            
        # Test non-existent file
        size = self.file_ops.get_file_size("nonexistent.txt")
        assert size == 0
        
    def test_file_exists(self):
        """Test file existence check."""
        with tempfile.NamedTemporaryFile() as temp_file:
            assert self.file_ops.file_exists(temp_file.name) is True
            
        assert self.file_ops.file_exists("nonexistent.txt") is False
        
    def test_create_file_success(self):
        """Test successful file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "subdir" / "newfile.txt"
            content = "test content"
            
            result = self.file_ops.create_file(str(file_path), content)
            
            assert result is True
            assert file_path.exists()
            assert file_path.read_text() == content


if __name__ == "__main__":
    pytest.main([__file__])