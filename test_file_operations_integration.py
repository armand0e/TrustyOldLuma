"""Integration test for File Operations Manager with UI Manager."""

import json
import tempfile
import zipfile
from pathlib import Path
from io import StringIO

from rich.console import Console

from src.file_operations import FileOperationsManager
from src.ui_manager import UIManager


def test_file_operations_with_real_ui():
    """Test File Operations Manager with real UI Manager."""
    # Create console that captures output
    console_output = StringIO()
    console = Console(file=console_output, width=80)
    
    # Create real UI manager
    ui = UIManager(console=console)
    
    # Create file operations manager
    file_ops = FileOperationsManager(ui)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test 1: Create directory structure
        base_path = temp_path / "test_base"
        directories = ["dir1", "dir2/subdir", "dir3"]
        
        result = file_ops.create_directory_structure(str(base_path), directories)
        assert result is True
        assert (base_path / "dir1").exists()
        assert (base_path / "dir2" / "subdir").exists()
        assert (base_path / "dir3").exists()
        
        # Test 2: Create and extract ZIP archive
        zip_path = temp_path / "test.zip"
        extract_path = temp_path / "extracted"
        
        # Create test ZIP
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("subdir/file2.txt", "content2")
            
        result = file_ops.extract_archive(str(zip_path), str(extract_path))
        assert result is True
        assert (extract_path / "file1.txt").exists()
        assert (extract_path / "subdir" / "file2.txt").exists()
        
        # Test 3: Copy files
        source_file = temp_path / "source.txt"
        source_file.write_text("test content")
        dest_file = temp_path / "dest.txt"
        
        result = file_ops.copy_files(str(source_file), str(dest_file))
        assert result is True
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"
        
        # Test 4: Update JSON config
        config_path = temp_path / "config.json"
        initial_config = {"key1": "value1", "nested": {"key2": "value2"}}
        config_path.write_text(json.dumps(initial_config))
        
        updates = {"key1": "updated_value1", "nested": {"key3": "value3"}}
        result = file_ops.update_config_file(str(config_path), updates)
        assert result is True
        
        updated_config = json.loads(config_path.read_text())
        assert updated_config["key1"] == "updated_value1"
        assert updated_config["nested"]["key3"] == "value3"
        
    # Check that UI output was generated
    output = console_output.getvalue()
    assert "Successfully" in output  # Should have success messages
    
    print("✅ All integration tests passed!")
    print(f"UI Output length: {len(output)} characters")


if __name__ == "__main__":
    test_file_operations_with_real_ui()