"""File Operations Manager module for handling file operations with progress tracking."""

import json
import shutil
import tempfile
import zipfile
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import os

from rich.progress import Progress, TaskID

from .ui_manager import UIManager


class FileOperationsManager:
    """Handles file operations with Rich progress bar integration."""
    
    def __init__(self, ui_manager: UIManager):
        """Initialize File Operations Manager with UI Manager."""
        self.ui = ui_manager
        
    def extract_archive(self, archive_path: str, destination: str) -> bool:
        """
        Extract ZIP archive with Rich progress bar integration.
        
        Args:
            archive_path: Path to the ZIP archive
            destination: Destination directory for extraction
            
        Returns:
            bool: True if extraction successful, False otherwise
        """
        try:
            archive_path = Path(archive_path)
            destination = Path(destination)
            
            if not archive_path.exists():
                self.ui.display_error(
                    f"Archive not found: {archive_path}",
                    ["Check if the archive file exists", "Verify the file path is correct"]
                )
                return False
                
            if not archive_path.suffix.lower() == '.zip':
                self.ui.display_error(
                    f"Unsupported archive format: {archive_path.suffix}",
                    ["Only ZIP archives are supported", "Convert archive to ZIP format"]
                )
                return False
                
            # Create destination directory if it doesn't exist
            destination.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Get list of files to extract
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                if total_files == 0:
                    self.ui.display_warning("Archive is empty")
                    return True
                
                # Create cancellable progress bar
                extraction_cancelled = False
                
                def cancel_extraction():
                    nonlocal extraction_cancelled
                    extraction_cancelled = True
                    self.ui.display_warning("File extraction cancelled by user")
                
                with self.ui.show_progress_with_cancel(
                    f"Extracting {archive_path.name}", 
                    total_files, 
                    cancel_extraction
                ) as progress:
                    task = progress.add_task("Extracting files...", total=total_files)
                    
                    for i, file_info in enumerate(zip_ref.infolist()):
                        # Check if extraction was cancelled
                        if extraction_cancelled or self.ui.was_interrupted():
                            self.ui.display_warning("Extraction cancelled, cleaning up...")
                            # Clean up partially extracted files
                            try:
                                if destination.exists():
                                    shutil.rmtree(destination)
                            except Exception:
                                pass  # Don't fail cleanup
                            return False
                            
                        try:
                            # Extract individual file
                            zip_ref.extract(file_info, destination)
                            progress.update(task, advance=1)
                            
                        except Exception as e:
                            self.ui.display_error(
                                f"Failed to extract {file_info.filename}: {str(e)}",
                                ["Check file permissions", "Ensure sufficient disk space"]
                            )
                            return False
                            
            self.ui.display_success(f"Successfully extracted {total_files} files to {destination}")
            return True
            
        except zipfile.BadZipFile:
            self.ui.display_error(
                f"Invalid or corrupted ZIP file: {archive_path}",
                ["Download the archive again", "Check if the file is corrupted"]
            )
            return False
            
        except PermissionError:
            self.ui.display_error(
                f"Permission denied accessing: {archive_path}",
                ["Run as administrator", "Check file permissions"]
            )
            return False
            
        except Exception as e:
            self.ui.display_error(
                f"Unexpected error during extraction: {str(e)}",
                ["Check available disk space", "Verify file paths are valid"]
            )
            return False
            
    def create_directory_structure(self, base_path: str, directories: Optional[List[str]] = None) -> bool:
        """
        Create directory structure with proper path handling using pathlib.
        
        Args:
            base_path: Base directory path
            directories: Optional list of subdirectories to create
            
        Returns:
            bool: True if directory creation successful, False otherwise
        """
        try:
            base_path = Path(base_path)
            
            # Create base directory
            base_path.mkdir(parents=True, exist_ok=True)
            
            if directories:
                total_dirs = len(directories)
                
                with self.ui.show_progress_bar(f"Creating directory structure", total_dirs) as progress:
                    task = progress.add_task("Creating directories...", total=total_dirs)
                    
                    for directory in directories:
                        try:
                            dir_path = base_path / directory
                            dir_path.mkdir(parents=True, exist_ok=True)
                            progress.update(task, advance=1)
                            
                        except Exception as e:
                            self.ui.display_error(
                                f"Failed to create directory {directory}: {str(e)}",
                                ["Check permissions", "Verify path is valid"]
                            )
                            return False
                            
                self.ui.display_success(f"Successfully created {total_dirs} directories under {base_path}")
            else:
                self.ui.display_success(f"Successfully created base directory: {base_path}")
                
            return True
            
        except PermissionError:
            self.ui.display_error(
                f"Permission denied creating directory: {base_path}",
                ["Run as administrator", "Check parent directory permissions"]
            )
            return False
            
        except Exception as e:
            self.ui.display_error(
                f"Unexpected error creating directories: {str(e)}",
                ["Check available disk space", "Verify path is valid"]
            )
            return False
            
    def copy_files(self, source: str, destination: str, files: Optional[List[str]] = None) -> bool:
        """
        Copy files with progress feedback and atomic operations.
        
        Args:
            source: Source directory or file path
            destination: Destination directory or file path
            files: Optional list of specific files to copy (relative to source)
            
        Returns:
            bool: True if copy operation successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                self.ui.display_error(
                    f"Source path not found: {source_path}",
                    ["Check if the source path exists", "Verify the path is correct"]
                )
                return False
                
            # Handle single file copy
            if source_path.is_file():
                return self._copy_single_file(source_path, dest_path)
                
            # Handle directory copy
            if files:
                return self._copy_specific_files(source_path, dest_path, files)
            else:
                return self._copy_directory(source_path, dest_path)
                
        except Exception as e:
            self.ui.display_error(
                f"Unexpected error during copy operation: {str(e)}",
                ["Check available disk space", "Verify file permissions"]
            )
            return False
            
    def _copy_single_file(self, source: Path, destination: Path) -> bool:
        """Copy a single file with atomic operation."""
        try:
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Use temporary file for atomic operation
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=destination.parent, 
                    delete=False, 
                    suffix=destination.suffix
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    
                # Copy file with progress tracking
                file_size = source.stat().st_size
                
                with self.ui.show_progress_bar(f"Copying {source.name}", file_size) as progress:
                    task = progress.add_task("Copying file...", total=file_size)
                    
                    with open(source, 'rb') as src, open(temp_path, 'wb') as dst:
                        chunk_size = 64 * 1024  # 64KB chunks
                        while True:
                            chunk = src.read(chunk_size)
                            if not chunk:
                                break
                            dst.write(chunk)
                            progress.update(task, advance=len(chunk))
                            
                # Atomic move to final destination
                temp_path.replace(destination)
            except Exception:
                # Clean up temporary file if it exists
                if temp_path and temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                raise
                
            self.ui.display_success(f"Successfully copied {source.name} to {destination}")
            return True
            
        except Exception as e:
            # Clean up temporary file if it exists
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink(missing_ok=True)
                
            self.ui.display_error(
                f"Failed to copy {source.name}: {str(e)}",
                ["Check available disk space", "Verify file permissions"]
            )
            return False
            
    def _copy_specific_files(self, source: Path, destination: Path, files: List[str]) -> bool:
        """Copy specific files from source to destination."""
        try:
            destination.mkdir(parents=True, exist_ok=True)
            
            total_files = len(files)
            
            with self.ui.show_progress_bar(f"Copying {total_files} files", total_files) as progress:
                task = progress.add_task("Copying files...", total=total_files)
                
                for file_name in files:
                    source_file = source / file_name
                    dest_file = destination / file_name
                    
                    if not source_file.exists():
                        self.ui.display_warning(f"File not found: {file_name}")
                        progress.update(task, advance=1)
                        continue
                        
                    # Create destination subdirectory if needed
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(source_file, dest_file)
                    progress.update(task, advance=1)
                    
            self.ui.display_success(f"Successfully copied {total_files} files to {destination}")
            return True
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to copy files: {str(e)}",
                ["Check available disk space", "Verify file permissions"]
            )
            return False
            
    def _copy_directory(self, source: Path, destination: Path) -> bool:
        """Copy entire directory with progress tracking."""
        try:
            # Count total files for progress tracking
            all_files = list(source.rglob('*'))
            file_count = len([f for f in all_files if f.is_file()])
            
            if file_count == 0:
                self.ui.display_warning(f"No files found in {source}")
                return True
                
            with self.ui.show_progress_bar(f"Copying directory {source.name}", file_count) as progress:
                task = progress.add_task("Copying directory...", total=file_count)
                
                def copy_progress(src, dst):
                    """Progress callback for shutil.copytree."""
                    progress.update(task, advance=1)
                    
                # Use shutil.copytree with progress callback
                shutil.copytree(
                    source, 
                    destination, 
                    dirs_exist_ok=True,
                    copy_function=lambda src, dst: (shutil.copy2(src, dst), copy_progress(src, dst))[0]
                )
                
            self.ui.display_success(f"Successfully copied directory {source.name} to {destination}")
            return True
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to copy directory: {str(e)}",
                ["Check available disk space", "Verify directory permissions"]
            )
            return False
            
    def update_config_file(self, config_path: str, updates: Dict[str, Any], 
                          config_type: str = "auto") -> bool:
        """
        Update configuration file (JSON or INI) with new values.
        
        Args:
            config_path: Path to configuration file
            updates: Dictionary of updates to apply
            config_type: Type of config file ("json", "ini", or "auto" to detect)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            config_path = Path(config_path)
            
            # Auto-detect config type if not specified
            if config_type == "auto":
                if config_path.suffix.lower() == '.json':
                    config_type = "json"
                elif config_path.suffix.lower() in ['.ini', '.cfg', '.conf']:
                    config_type = "ini"
                else:
                    self.ui.display_error(
                        f"Cannot determine config file type for: {config_path}",
                        ["Specify config_type parameter", "Use .json or .ini file extension"]
                    )
                    return False
                    
            if config_type == "json":
                return self._update_json_config(config_path, updates)
            elif config_type == "ini":
                return self._update_ini_config(config_path, updates)
            else:
                self.ui.display_error(
                    f"Unsupported config type: {config_type}",
                    ["Use 'json' or 'ini' config type"]
                )
                return False
                
        except Exception as e:
            self.ui.display_error(
                f"Unexpected error updating config file: {str(e)}",
                ["Check file permissions", "Verify file format is valid"]
            )
            return False
            
    def _update_json_config(self, config_path: Path, updates: Dict[str, Any]) -> bool:
        """Update JSON configuration file."""
        try:
            # Create backup for atomic operation
            backup_path = config_path.with_suffix(config_path.suffix + '.backup')
            
            # Load existing config or create new one
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                # Create backup
                shutil.copy2(config_path, backup_path)
            else:
                config_data = {}
                # Create parent directory if needed
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Apply updates
            self._deep_update(config_data, updates)
            
            # Write updated config to temporary file first (atomic operation)
            temp_path = config_path.with_suffix(config_path.suffix + '.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            # Atomic move to final location
            temp_path.replace(config_path)
            
            # Remove backup on success
            if backup_path.exists():
                backup_path.unlink()
                
            self.ui.display_success(f"Successfully updated JSON config: {config_path.name}")
            return True
            
        except json.JSONDecodeError as e:
            self.ui.display_error(
                f"Invalid JSON format in {config_path.name}: {str(e)}",
                ["Check JSON syntax", "Restore from backup if available"]
            )
            return False
            
        except Exception as e:
            # Restore from backup if available
            if 'backup_path' in locals() and backup_path.exists():
                backup_path.replace(config_path)
                
            # Clean up temporary file
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink(missing_ok=True)
                
            self.ui.display_error(
                f"Failed to update JSON config: {str(e)}",
                ["Check file permissions", "Verify JSON format is valid"]
            )
            return False
            
    def _update_ini_config(self, config_path: Path, updates: Dict[str, Any]) -> bool:
        """Update INI configuration file."""
        try:
            # Create backup for atomic operation
            backup_path = config_path.with_suffix(config_path.suffix + '.backup')
            
            config = ConfigParser()
            
            # Load existing config or create new one
            if config_path.exists():
                config.read(config_path, encoding='utf-8')
                # Create backup
                shutil.copy2(config_path, backup_path)
            else:
                # Create parent directory if needed
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Apply updates
            for key, value in updates.items():
                if isinstance(value, dict):
                    # Handle section updates
                    if not config.has_section(key):
                        config.add_section(key)
                    for sub_key, sub_value in value.items():
                        config.set(key, sub_key, str(sub_value))
                else:
                    # Handle direct key-value updates (assume DEFAULT section)
                    config.set('DEFAULT', key, str(value))
                    
            # Write updated config to temporary file first (atomic operation)
            temp_path = config_path.with_suffix(config_path.suffix + '.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                config.write(f)
                
            # Atomic move to final location
            temp_path.replace(config_path)
            
            # Remove backup on success
            if backup_path.exists():
                backup_path.unlink()
                
            self.ui.display_success(f"Successfully updated INI config: {config_path.name}")
            return True
            
        except Exception as e:
            # Restore from backup if available
            if 'backup_path' in locals() and backup_path.exists():
                backup_path.replace(config_path)
                
            # Clean up temporary file
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink(missing_ok=True)
                
            self.ui.display_error(
                f"Failed to update INI config: {str(e)}",
                ["Check file permissions", "Verify INI format is valid"]
            )
            return False
            
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """
        Deep update dictionary with nested values.
        
        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates to apply
        """
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            int: File size in bytes, or 0 if file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except (OSError, FileNotFoundError):
            return 0
            
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return Path(file_path).exists()
        
    def create_file(self, file_path: str, content: str = "") -> bool:
        """
        Create a new file with optional content.
        
        Args:
            file_path: Path to file to create
            content: Optional content to write to file
            
        Returns:
            bool: True if file creation successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.ui.display_success(f"Successfully created file: {file_path.name}")
            return True
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to create file {file_path}: {str(e)}",
                ["Check file permissions", "Verify directory exists"]
            )
            return False