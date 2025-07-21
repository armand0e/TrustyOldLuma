"""
File operations manager for Luna Gaming Tool.

This module provides file and directory operations with Rich progress tracking,
including directory creation, archive extraction, download management, and
migration-specific file operations for Luna components.
"""

import asyncio
import aiohttp
import aiofiles
import zipfile
import shutil
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from rich.console import Console

from luna.managers.display_managers import ProgressDisplayManager, ErrorDisplayManager
from luna.models.models import LunaResults
from luna.core.config import DOWNLOAD_TIMEOUT, MAX_RETRY_ATTEMPTS, RETRY_DELAY
from luna.models.exceptions import FileOperationError, NetworkError, DownloadError, ConnectionTimeoutError
from luna.managers.error_manager import ErrorManager, RetryManager, with_retry


class FileOperationsManager:
    """Manages file and directory operations with progress tracking for Luna components."""
    
    def __init__(self, console: Console):
        """Initialize the Luna file operations manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
        
    @with_retry(
        max_attempts=2,
        base_delay=0.5,
        retry_exceptions=(PermissionError, FileOperationError),
        operation_name="Directory creation"
    )
    async def create_directories(self, paths: List[Path], results: LunaResults) -> None:
        """Create required Luna directories with progress indication.
        
        Args:
            paths: List of directory paths to create
            results: Luna setup results to update
        """
        if not paths:
            return
            
        with self.progress_manager.create_progress_bar(
            "Creating Luna directories...", 
            total=len(paths)
        ) as progress:
            
            for path in paths:
                try:
                    # Check if directory already exists
                    if path.exists():
                        if path.is_dir():
                            progress.update(1, f"Luna directory already exists: {path.name}")
                            results.directories_created.append(path)
                        else:
                            error_msg = f"Path exists but is not a directory: {path}"
                            results.add_error(error_msg)
                            raise FileOperationError(error_msg)
                    else:
                        # Create directory with parents
                        path.mkdir(parents=True, exist_ok=True)
                        progress.update(1, f"Created Luna directory: {path.name}")
                        results.directories_created.append(path)
                        
                        # Small delay for visual feedback
                        await asyncio.sleep(0.1)
                        
                except PermissionError as e:
                    error_msg = f"Permission denied creating Luna directory: {path}"
                    results.add_error(error_msg)
                    progress.update(1)
                    raise PermissionError(error_msg) from e
                    
                except Exception as e:
                    error_msg = f"Failed to create Luna directory {path}: {str(e)}"
                    results.add_error(error_msg)
                    progress.update(1)
                    raise FileOperationError(error_msg) from e
    
    @with_retry(
        max_attempts=2,  # Fewer retries for extraction operations
        base_delay=0.5,
        retry_exceptions=(zipfile.BadZipFile, PermissionError, FileOperationError),
        operation_name="Archive extraction"
    )
    async def extract_archive(self, archive_path: Path, destination: Path, 
                            flatten: bool = True, results: Optional[LunaResults] = None,
                            luna_component: Optional[str] = None) -> bool:
        """Extract Luna component archive with progress bar and Luna directory structure.
        
        Args:
            archive_path: Path to the archive file
            destination: Destination directory for extraction
            flatten: Whether to flatten the directory structure
            results: Optional Luna setup results to update
            luna_component: Optional Luna component name (injector, unlocker)
            
        Returns:
            True if extraction was successful, False otherwise
        """
        if results:
            results.mark_extraction_attempted()
            
        if not archive_path.exists():
            error_msg = f"Luna archive file not found: {archive_path}"
            if results:
                results.add_error(error_msg)
            raise FileNotFoundError(error_msg)
            
        try:
            # Ensure Luna destination directory exists
            destination.mkdir(parents=True, exist_ok=True)
            
            # Get archive info for progress tracking
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)
                
            component_desc = f" ({luna_component})" if luna_component else ""
            with self.progress_manager.create_progress_bar(
                f"Extracting Luna {archive_path.name}{component_desc}...",
                total=total_files
            ) as progress:
                
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    for i, file_info in enumerate(file_list):
                        try:
                            if flatten:
                                # Extract with flattened Luna structure
                                await self._extract_file_flattened(
                                    zip_ref, file_info, destination, progress, luna_component
                                )
                            else:
                                # Extract with Luna directory structure
                                await self._extract_file_normal(
                                    zip_ref, file_info, destination, progress, luna_component
                                )
                                
                            # Small delay for visual feedback
                            if i % 10 == 0:  # Update every 10 files
                                await asyncio.sleep(0.01)
                                
                        except Exception as e:
                            warning_msg = f"Failed to extract Luna file {file_info.filename}: {str(e)}"
                            if results:
                                results.add_warning(warning_msg)
                            progress.update(1)
                            continue
                            
            if results:
                results.files_extracted = True
            return True
            
        except zipfile.BadZipFile as e:
            error_msg = f"Invalid or corrupted Luna archive: {archive_path}"
            if results:
                results.add_error(error_msg)
            raise FileOperationError(error_msg) from e
            
        except PermissionError as e:
            error_msg = f"Permission denied extracting Luna components to: {destination}"
            if results:
                results.add_error(error_msg)
            raise PermissionError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Failed to extract Luna archive: {str(e)}"
            if results:
                results.add_error(error_msg)
            raise FileOperationError(error_msg) from e
    
    async def _extract_file_flattened(self, zip_ref: zipfile.ZipFile, 
                                    file_info: zipfile.ZipInfo, 
                                    destination: Path, progress,
                                    luna_component: Optional[str] = None) -> None:
        """Extract a single file with flattened Luna directory structure.
        
        Args:
            zip_ref: ZipFile reference
            file_info: File info from zip
            destination: Luna destination directory
            progress: Progress context for updates
            luna_component: Optional Luna component name
        """
        # Skip directories in flattened mode
        if file_info.is_dir():
            progress.update(1, f"Skipping directory: {file_info.filename}")
            return
            
        # Get just the filename without path
        filename = Path(file_info.filename).name
        if not filename:  # Skip if no filename (shouldn't happen)
            progress.update(1)
            return
            
        target_path = destination / filename
        
        # Extract file data
        with zip_ref.open(file_info) as source:
            async with aiofiles.open(target_path, 'wb') as target:
                # Read and write in chunks for large files
                chunk_size = 8192
                while True:
                    chunk = source.read(chunk_size)
                    if not chunk:
                        break
                    await target.write(chunk)
                    
        component_desc = f" ({luna_component})" if luna_component else ""
        progress.update(1, f"Extracted Luna file: {filename}{component_desc}")
    
    async def _extract_file_normal(self, zip_ref: zipfile.ZipFile,
                                 file_info: zipfile.ZipInfo,
                                 destination: Path, progress,
                                 luna_component: Optional[str] = None) -> None:
        """Extract a single file with Luna directory structure.
        
        Args:
            zip_ref: ZipFile reference
            file_info: File info from zip
            destination: Luna destination directory
            progress: Progress context for updates
            luna_component: Optional Luna component name
        """
        target_path = destination / file_info.filename
        
        if file_info.is_dir():
            # Create Luna directory
            target_path.mkdir(parents=True, exist_ok=True)
            progress.update(1, f"Created Luna directory: {file_info.filename}")
        else:
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract file
            with zip_ref.open(file_info) as source:
                async with aiofiles.open(target_path, 'wb') as target:
                    chunk_size = 8192
                    while True:
                        chunk = source.read(chunk_size)
                        if not chunk:
                            break
                        await target.write(chunk)
                        
            component_desc = f" ({luna_component})" if luna_component else ""
            progress.update(1, f"Extracted Luna file: {file_info.filename}{component_desc}")
    
    @with_retry(
        max_attempts=MAX_RETRY_ATTEMPTS,
        base_delay=RETRY_DELAY,
        retry_exceptions=(aiohttp.ClientError, asyncio.TimeoutError, ConnectionError),
        operation_name="File download"
    )
    async def download_file(self, url: str, destination: Path, 
                          filename: Optional[str] = None,
                          results: Optional[LunaResults] = None) -> bool:
        """Download Luna component file with progress bar and retry logic.
        
        Args:
            url: URL to download from
            destination: Luna destination directory
            filename: Optional custom filename (extracted from URL if not provided)
            results: Optional Luna setup results to update
            
        Returns:
            True if download was successful, False otherwise
        """
        # Determine filename
        if filename is None:
            filename = Path(url).name
            if not filename:
                filename = "downloaded_file"
                
        file_path = destination / filename
        
        # Ensure destination directory exists
        destination.mkdir(parents=True, exist_ok=True)
        
        try:
            # The retry logic is now handled by the decorator
            success = await self._download_with_progress(url, file_path, 1)
            
            if success:
                if results:
                    results.files_downloaded.append((url, True))
                return True
            else:
                if results:
                    error_msg = f"Luna component download failed for {url}"
                    results.add_error(error_msg)
                    results.files_downloaded.append((url, False))
                return False
                
        except aiohttp.ClientResponseError as e:
            # Convert to our custom exception type
            error_msg = f"HTTP error downloading Luna component {e.status}: {e.message}"
            if results:
                results.add_error(error_msg)
                results.files_downloaded.append((url, False))
            raise DownloadError(error_msg) from e
            
        except asyncio.TimeoutError as e:
            error_msg = f"Luna component download timed out for {url}"
            if results:
                results.add_error(error_msg)
                results.files_downloaded.append((url, False))
            raise ConnectionTimeoutError(error_msg) from e
            
        except (aiohttp.ClientError, ConnectionError) as e:
            error_msg = f"Network error while downloading Luna component {url}: {str(e)}"
            if results:
                results.add_error(error_msg)
                results.files_downloaded.append((url, False))
            raise NetworkError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error downloading Luna component {url}: {str(e)}"
            if results:
                results.add_error(error_msg)
                results.files_downloaded.append((url, False))
            raise FileOperationError(error_msg) from e
    
    async def _download_with_progress(self, url: str, file_path: Path, attempt: int) -> bool:
        """Download file with progress tracking.
        
        Args:
            url: URL to download from
            file_path: Path where file should be saved
            attempt: Current attempt number
            
        Returns:
            True if download successful, False otherwise
        """
        timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"HTTP {response.status}"
                    )
                
                # Get file size for progress tracking
                file_size = int(response.headers.get('content-length', 0))
                
                description = f"Downloading Luna component: {file_path.name}"
                if attempt > 1:
                    description += f" (attempt {attempt})"
                    
                with self.progress_manager.create_progress_bar(
                    description,
                    total=file_size if file_size > 0 else 100
                ) as progress:
                    
                    downloaded = 0
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            if file_size > 0:
                                progress.update(len(chunk))
                            else:
                                # Indeterminate progress - just show activity
                                progress.update(1)
                                
                            # Small delay for visual feedback
                            await asyncio.sleep(0.001)
                            
        return True
    
    async def verify_file_integrity(self, file_path: Path, 
                                  expected_size: Optional[int] = None) -> bool:
        """Verify file integrity after download or extraction.
        
        Args:
            file_path: Path to file to verify
            expected_size: Optional expected file size in bytes
            
        Returns:
            True if file appears to be intact, False otherwise
        """
        try:
            if not file_path.exists():
                return False
                
            stat = file_path.stat()
            
            # Check if file is empty
            if stat.st_size == 0:
                return False
                
            # Check expected size if provided
            if expected_size is not None and stat.st_size != expected_size:
                return False
                
            # For zip files, try to open them
            if file_path.suffix.lower() == '.zip':
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        # Test the zip file
                        zip_ref.testzip()
                except zipfile.BadZipFile:
                    return False
                    
            return True
            
        except Exception:
            return False
    
    async def cleanup_temp_files(self, temp_files: List[Path]) -> None:
        """Clean up Luna temporary files with progress indication.
        
        Args:
            temp_files: List of temporary file paths to remove
        """
        if not temp_files:
            return
            
        with self.progress_manager.create_progress_bar(
            "Cleaning up Luna temporary files...",
            total=len(temp_files)
        ) as progress:
            
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        if temp_file.is_file():
                            temp_file.unlink()
                            progress.update(1, f"Removed Luna temp file: {temp_file.name}")
                        elif temp_file.is_dir():
                            shutil.rmtree(temp_file)
                            progress.update(1, f"Removed Luna temp directory: {temp_file.name}")
                    else:
                        progress.update(1, f"Already removed: {temp_file.name}")
                        
                    await asyncio.sleep(0.05)  # Small delay for visual feedback
                    
                except Exception as e:
                    # Log warning but continue cleanup
                    progress.update(1, f"Failed to remove Luna temp file: {temp_file.name}")
                    continue
    
    @asynccontextmanager
    async def temp_file_manager(self, temp_dir: Path) -> AsyncGenerator[List[Path], None]:
        """Context manager for Luna temporary file tracking and cleanup.
        
        Args:
            temp_dir: Directory for Luna temporary files
            
        Yields:
            List to track temporary files (append files to this list)
        """
        temp_files: List[Path] = []
        try:
            # Ensure Luna temp directory exists
            temp_dir.mkdir(parents=True, exist_ok=True)
            yield temp_files
        finally:
            # Clean up all tracked Luna temporary files
            await self.cleanup_temp_files(temp_files)
            
            # Remove Luna temp directory if empty
            try:
                if temp_dir.exists() and not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
            except Exception:
                pass  # Ignore cleanup errors
    
    async def copy_file(self, source: Path, destination: Path, 
                       results: Optional[LunaResults] = None) -> bool:
        """Copy a file for Luna migration with progress tracking.
        
        Args:
            source: Source file path
            destination: Destination file path
            results: Optional Luna results to update
            
        Returns:
            True if copy was successful, False otherwise
        """
        try:
            if not source.exists():
                error_msg = f"Source file not found for Luna migration: {source}"
                if results:
                    results.add_error(error_msg)
                return False
                
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file with progress indication
            with self.progress_manager.create_progress_bar(
                f"Copying Luna file: {source.name}...",
                total=1
            ) as progress:
                shutil.copy2(source, destination)
                progress.update(1, f"Copied to Luna: {destination.name}")
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to copy Luna file {source} to {destination}: {str(e)}"
            if results:
                results.add_error(error_msg)
            return False
    
    async def move_file(self, source: Path, destination: Path,
                       results: Optional[LunaResults] = None) -> bool:
        """Move a file for Luna migration with progress tracking.
        
        Args:
            source: Source file path
            destination: Destination file path
            results: Optional Luna results to update
            
        Returns:
            True if move was successful, False otherwise
        """
        try:
            if not source.exists():
                error_msg = f"Source file not found for Luna migration: {source}"
                if results:
                    results.add_error(error_msg)
                return False
                
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file with progress indication
            with self.progress_manager.create_progress_bar(
                f"Moving Luna file: {source.name}...",
                total=1
            ) as progress:
                shutil.move(str(source), str(destination))
                progress.update(1, f"Moved to Luna: {destination.name}")
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to move Luna file {source} to {destination}: {str(e)}"
            if results:
                results.add_error(error_msg)
            return False
    
    async def backup_file(self, file_path: Path, backup_dir: Path,
                         results: Optional[LunaResults] = None) -> Optional[Path]:
        """Create a backup of a file before Luna migration.
        
        Args:
            file_path: File to backup
            backup_dir: Directory for backup files
            results: Optional Luna results to update
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            if not file_path.exists():
                return None
                
            # Create backup directory
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = int(time.time())
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            # Create backup with progress indication
            with self.progress_manager.create_progress_bar(
                f"Backing up for Luna migration: {file_path.name}...",
                total=1
            ) as progress:
                shutil.copy2(file_path, backup_path)
                progress.update(1, f"Backed up: {backup_name}")
                
            return backup_path
            
        except Exception as e:
            error_msg = f"Failed to backup Luna file {file_path}: {str(e)}"
            if results:
                results.add_error(error_msg)
            return None
    
    async def migrate_directory(self, source_dir: Path, destination_dir: Path,
                               results: Optional[LunaResults] = None) -> bool:
        """Migrate an entire directory for Luna conversion.
        
        Args:
            source_dir: Source directory to migrate
            destination_dir: Luna destination directory
            results: Optional Luna results to update
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            if not source_dir.exists() or not source_dir.is_dir():
                error_msg = f"Source directory not found for Luna migration: {source_dir}"
                if results:
                    results.add_error(error_msg)
                return False
                
            # Get list of files to migrate
            files_to_migrate = list(source_dir.rglob('*'))
            files_to_migrate = [f for f in files_to_migrate if f.is_file()]
            
            if not files_to_migrate:
                return True  # Nothing to migrate
                
            with self.progress_manager.create_progress_bar(
                f"Migrating Luna directory: {source_dir.name}...",
                total=len(files_to_migrate)
            ) as progress:
                
                for file_path in files_to_migrate:
                    try:
                        # Calculate relative path
                        relative_path = file_path.relative_to(source_dir)
                        dest_path = destination_dir / relative_path
                        
                        # Ensure destination directory exists
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(file_path, dest_path)
                        progress.update(1, f"Migrated: {relative_path}")
                        
                        await asyncio.sleep(0.01)  # Small delay for visual feedback
                        
                    except Exception as e:
                        warning_msg = f"Failed to migrate Luna file {file_path}: {str(e)}"
                        if results:
                            results.add_warning(warning_msg)
                        progress.update(1)
                        continue
                        
            return True
            
        except Exception as e:
            error_msg = f"Failed to migrate Luna directory {source_dir}: {str(e)}"
            if results:
                results.add_error(error_msg)
            return False