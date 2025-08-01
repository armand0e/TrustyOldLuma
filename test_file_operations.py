"""Tests for File Operations Manager."""

import json
import tempfile
import zipfile
from configparser import ConfigParser
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

from src.file_operations import FileOperationsManager
from src.ui_manager import UIManager


class TestFileOperationsManager:
    """Test cases for FileOperationsManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ui = Mock(spec=UIManager)
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
                
            # Mock progress bar
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.add_task.return_value = mock_task
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_with_cancel.return_value = mock_context_manager
            self.mock_ui.was_interrupted.return_value = False
            
            # Test extraction
            result = self.file_ops.extract_archive(str(zip_path), str(extract_path))
            
            assert result is True
            assert (extract_path / "file1.txt").exists()
            assert (extract_path / "subdir" / "file2.txt").exists()
            self.mock_ui.display_success.assert_called_once()
            
    def test_extract_archive_file_not_found(self):
        """Test extraction with non-existent archive."""
        result = self.file_ops.extract_archive("nonexistent.zip", "/tmp/extract")
        
        assert result is False
        self.mock_ui.display_error.assert_called_once()
        
    def test_extract_archive_invalid_format(self):
        """Test extraction with non-ZIP file."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
            result = self.file_ops.extract_archive(temp_file.name, "/tmp/extract")
            
        assert result is False
        self.mock_ui.display_error.assert_called_once()
        
    def test_create_directory_structure_success(self):
        """Test successful directory structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            directories = ["dir1", "dir2/subdir", "dir3"]
            
            # Mock progress bar
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.add_task.return_value = mock_task
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_bar.return_value = mock_context_manager
            
            result = self.file_ops.create_directory_structure(str(base_path), directories)
            
            assert result is True
            assert base_path.exists()
            assert (base_path / "dir1").exists()
            assert (base_path / "dir2" / "subdir").exists()
            assert (base_path / "dir3").exists()
            self.mock_ui.display_success.assert_called_once()
            
    def test_create_directory_structure_base_only(self):
        """Test creating only base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            
            result = self.file_ops.create_directory_structure(str(base_path))
            
            assert result is True
            assert base_path.exists()
            self.mock_ui.display_success.assert_called_once()
            
    def test_copy_single_file_success(self):
        """Test successful single file copy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")
            
            dest_file = temp_path / "dest.txt"
            
            # Mock progress bar
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.add_task.return_value = mock_task
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_bar.return_value = mock_context_manager
            
            result = self.file_ops.copy_files(str(source_file), str(dest_file))
            
            assert result is True
            assert dest_file.exists()
            assert dest_file.read_text() == "test content"
            self.mock_ui.display_success.assert_called_once()
            
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
            
            # Mock progress bar
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.add_task.return_value = mock_task
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_bar.return_value = mock_context_manager
            
            result = self.file_ops.copy_files(str(source_dir), str(dest_dir), files_to_copy)
            
            assert result is True
            assert (dest_dir / "file1.txt").exists()
            assert (dest_dir / "file3.txt").exists()
            assert not (dest_dir / "file2.txt").exists()
            self.mock_ui.display_success.assert_called_once()
            
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
            
            self.mock_ui.display_success.assert_called_once()
            
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
            
            self.mock_ui.display_success.assert_called_once()
            
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
            self.mock_ui.display_success.assert_called_once()
    
    def test_extract_archive_empty_archive(self):
        """Test extraction of empty ZIP archive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty ZIP file
            zip_path = temp_path / "empty.zip"
            extract_path = temp_path / "extracted"
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                pass  # Create empty archive
                
            # Mock progress bar
            mock_progress = Mock()
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_with_cancel.return_value = mock_context_manager
            self.mock_ui.was_interrupted.return_value = False
            
            result = self.file_ops.extract_archive(str(zip_path), str(extract_path))
            
            assert result is True
            self.mock_ui.display_warning.assert_called_with("Archive is empty")
    
    def test_extract_archive_cancelled_by_user(self):
        """Test extraction cancelled by user."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test ZIP file
            zip_path = temp_path / "test.zip"
            extract_path = temp_path / "extracted"
            
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file1.txt", "content1")
                
            # Mock progress bar and cancellation
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.add_task.return_value = mock_task
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_with_cancel.return_value = mock_context_manager
            self.mock_ui.was_interrupted.return_value = True  # Simulate cancellation
            
            result = self.file_ops.extract_archive(str(zip_path), str(extract_path))
            
            assert result is False
            self.mock_ui.display_warning.assert_called()
    
    def test_extract_archive_bad_zip_file(self):
        """Test extraction with corrupted ZIP file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create corrupted ZIP file
            zip_path = temp_path / "corrupted.zip"
            zip_path.write_text("This is not a valid ZIP file")
            
            result = self.file_ops.extract_archive(str(zip_path), str(temp_path / "extracted"))
            
            assert result is False
            self.mock_ui.display_error.assert_called()
            error_call = self.mock_ui.display_error.call_args
            assert "Invalid or corrupted ZIP file" in error_call[0][0]
    
    def test_extract_archive_permission_error(self):
        """Test extraction with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test ZIP file
            zip_path = temp_path / "test.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr("file1.txt", "content1")
            
            # Mock zipfile.ZipFile to raise PermissionError
            with patch('zipfile.ZipFile', side_effect=PermissionError("Access denied")):
                result = self.file_ops.extract_archive(str(zip_path), str(temp_path / "extracted"))
                
                assert result is False
                self.mock_ui.display_error.assert_called()
                error_call = self.mock_ui.display_error.call_args
                assert "Permission denied" in error_call[0][0]
    
    def test_copy_files_source_not_found(self):
        """Test copying files with non-existent source."""
        result = self.file_ops.copy_files("nonexistent_source", "/tmp/dest")
        
        assert result is False
        self.mock_ui.display_error.assert_called()
    
    def test_copy_files_permission_error(self):
        """Test copying files with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")
            
            dest_file = temp_path / "dest.txt"
            
            # Mock tempfile.NamedTemporaryFile to raise PermissionError
            with patch('tempfile.NamedTemporaryFile', side_effect=PermissionError("Access denied")):
                # Mock progress bar
                mock_progress = Mock()
                mock_task = Mock()
                mock_progress.add_task.return_value = mock_task
                mock_context_manager = MagicMock()
                mock_context_manager.__enter__.return_value = mock_progress
                mock_context_manager.__exit__.return_value = None
                self.mock_ui.show_progress_bar.return_value = mock_context_manager
                
                result = self.file_ops.copy_files(str(source_file), str(dest_file))
                
                assert result is False
                self.mock_ui.display_error.assert_called()
    
    def test_update_config_file_not_found(self):
        """Test config update with non-existent file creates new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "new_config.json"
            
            result = self.file_ops.update_config_file(str(config_path), {"key": "value"})
            
            assert result is True
            assert config_path.exists()
            self.mock_ui.display_success.assert_called_once()
    
    def test_update_config_invalid_json(self):
        """Test config update with invalid JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid.json"
            config_path.write_text("invalid json content")
            
            result = self.file_ops.update_config_file(str(config_path), {"key": "value"})
            
            assert result is False
            self.mock_ui.display_error.assert_called()
    
    def test_update_config_unsupported_format(self):
        """Test config update with unsupported file format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.xml"
            config_path.write_text("<config></config>")
            
            result = self.file_ops.update_config_file(str(config_path), {"key": "value"}, "xml")
            
            assert result is False
            self.mock_ui.display_error.assert_called()
            error_call = self.mock_ui.display_error.call_args
            assert "Unsupported config type" in error_call[0][0]
    
    def test_create_directory_structure_permission_error(self):
        """Test directory creation with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            directories = ["dir1"]
            
            # Mock Path.mkdir to raise PermissionError
            with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
                # Mock progress bar
                mock_progress = Mock()
                mock_task = Mock()
                mock_progress.add_task.return_value = mock_task
                mock_context_manager = MagicMock()
                mock_context_manager.__enter__.return_value = mock_progress
                mock_context_manager.__exit__.return_value = None
                self.mock_ui.show_progress_bar.return_value = mock_context_manager
                
                result = self.file_ops.create_directory_structure(str(base_path), directories)
                
                assert result is False
                self.mock_ui.display_error.assert_called()
    
    def test_create_file_permission_error(self):
        """Test file creation with permission error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "protected_file.txt"
            
            # Mock open to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                result = self.file_ops.create_file(str(file_path), "content")
                
                assert result is False
                self.mock_ui.display_error.assert_called()
    
    def test_copy_directory_recursive(self):
        """Test recursive directory copying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source directory structure
            source_dir = temp_path / "source"
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "subdir").mkdir()
            (source_dir / "subdir" / "file2.txt").write_text("content2")
            
            dest_dir = temp_path / "dest"
            
            # Mock progress bar
            mock_progress = Mock()
            mock_task = Mock()
            mock_progress.add_task.return_value = mock_task
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_progress
            mock_context_manager.__exit__.return_value = None
            self.mock_ui.show_progress_bar.return_value = mock_context_manager
            
            result = self.file_ops.copy_files(str(source_dir), str(dest_dir))
            
            assert result is True
            assert (dest_dir / "file1.txt").exists()
            assert (dest_dir / "subdir" / "file2.txt").exists()
            self.mock_ui.display_success.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])