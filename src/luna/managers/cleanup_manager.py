"""
Cleanup manager for the Gaming Setup Tool.

This module provides comprehensive cleanup operations and temporary file management
with proper resource management using context managers, cleanup validation,
and error reporting.
"""

import asyncio
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from rich.console import Console

from luna.managers.display_managers import ProgressDisplayManager, ErrorDisplayManager
from luna.models.models import LunaResults
from luna.models.exceptions import FileOperationError, GamingSetupError
from luna.managers.error_manager import with_retry


@dataclass
class CleanupOperation:
    """Represents a cleanup operation with metadata."""
    
    path: Path
    operation_type: str  # 'file', 'directory', 'temp_file'
    description: str
    critical: bool = False  # Whether failure should stop cleanup
    created_by: Optional[str] = None  # Which component created this item
    
    def __post_init__(self):
        """Validate cleanup operation after initialization."""
        if not self.operation_type:
            raise ValueError("Operation type cannot be empty")
        if not self.description:
            raise ValueError("Description cannot be empty")


@dataclass
class CleanupResults:
    """Results of cleanup operations."""
    
    operations_attempted: int = 0
    operations_successful: int = 0
    operations_failed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cleaned_paths: List[Path] = field(default_factory=list)
    failed_paths: List[Path] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate cleanup success rate."""
        if self.operations_attempted == 0:
            return 1.0
        return self.operations_successful / self.operations_attempted
    
    def add_success(self, path: Path) -> None:
        """Record a successful cleanup operation."""
        self.operations_successful += 1
        self.cleaned_paths.append(path)
    
    def add_failure(self, path: Path, error: str) -> None:
        """Record a failed cleanup operation."""
        self.operations_failed += 1
        self.failed_paths.append(path)
        self.errors.append(f"Failed to clean {path}: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


class CleanupManager:
    """Manages cleanup operations and temporary file removal with comprehensive tracking."""
    
    def __init__(self, console: Console):
        """Initialize the cleanup manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
        self.logger = logging.getLogger(__name__)
        
        # Tracking sets for different types of cleanup items
        self._temp_files: Set[Path] = set()
        self._temp_directories: Set[Path] = set()
        self._created_files: Set[Path] = set()
        self._created_directories: Set[Path] = set()
        self._cleanup_operations: List[CleanupOperation] = []
        
        # Metadata for tracking what created each item
        self._creation_metadata: Dict[Path, str] = {}
    
    def register_temp_file(self, file_path: Path, created_by: Optional[str] = None) -> None:
        """Register a temporary file for cleanup.
        
        Args:
            file_path: Path to the temporary file
            created_by: Optional identifier of what created this file
        """
        self._temp_files.add(file_path)
        if created_by:
            self._creation_metadata[file_path] = created_by
        
        self.logger.debug(f"Registered temporary file: {file_path}")
    
    def register_temp_directory(self, dir_path: Path, created_by: Optional[str] = None) -> None:
        """Register a temporary directory for cleanup.
        
        Args:
            dir_path: Path to the temporary directory
            created_by: Optional identifier of what created this directory
        """
        self._temp_directories.add(dir_path)
        if created_by:
            self._creation_metadata[dir_path] = created_by
        
        self.logger.debug(f"Registered temporary directory: {dir_path}")
    
    def register_created_file(self, file_path: Path, created_by: Optional[str] = None) -> None:
        """Register a file that was created during setup (for rollback).
        
        Args:
            file_path: Path to the created file
            created_by: Optional identifier of what created this file
        """
        self._created_files.add(file_path)
        if created_by:
            self._creation_metadata[file_path] = created_by
        
        self.logger.debug(f"Registered created file: {file_path}")
    
    def register_created_directory(self, dir_path: Path, created_by: Optional[str] = None) -> None:
        """Register a directory that was created during setup (for rollback).
        
        Args:
            dir_path: Path to the created directory
            created_by: Optional identifier of what created this directory
        """
        self._created_directories.add(dir_path)
        if created_by:
            self._creation_metadata[dir_path] = created_by
        
        self.logger.debug(f"Registered created directory: {dir_path}")
    
    def add_cleanup_operation(self, operation: CleanupOperation) -> None:
        """Add a custom cleanup operation.
        
        Args:
            operation: CleanupOperation to add
        """
        self._cleanup_operations.append(operation)
        self.logger.debug(f"Added cleanup operation: {operation.description}")
    
    @with_retry(
        max_attempts=2,
        base_delay=0.5,
        retry_exceptions=(PermissionError, FileOperationError),
        operation_name="Temporary file cleanup"
    )
    async def cleanup_temp_files(self, additional_files: Optional[List[Path]] = None) -> CleanupResults:
        """Clean up temporary files with progress tracking and validation.
        
        Args:
            additional_files: Optional additional files to clean up
            
        Returns:
            CleanupResults with operation details
        """
        results = CleanupResults()
        
        # Combine registered temp files with additional files
        all_temp_files = set(self._temp_files)
        if additional_files:
            all_temp_files.update(additional_files)
        
        if not all_temp_files:
            self.logger.info("No temporary files to clean up")
            return results
        
        self.logger.info(f"Cleaning up {len(all_temp_files)} temporary files")
        
        with self.progress_manager.create_progress_bar(
            "Cleaning up temporary files...",
            total=len(all_temp_files)
        ) as progress:
            
            for temp_file in all_temp_files:
                results.operations_attempted += 1
                
                try:
                    if await self._cleanup_single_file(temp_file, progress):
                        results.add_success(temp_file)
                    else:
                        results.add_failure(temp_file, "File not found or already removed")
                        
                except Exception as e:
                    error_msg = str(e)
                    results.add_failure(temp_file, error_msg)
                    self.logger.warning(f"Failed to remove temporary file {temp_file}: {error_msg}")
                
                # Small delay for visual feedback
                await asyncio.sleep(0.02)
        
        # Clear the registered temp files after cleanup
        self._temp_files.clear()
        
        return results
    
    @with_retry(
        max_attempts=2,
        base_delay=0.5,
        retry_exceptions=(PermissionError, FileOperationError),
        operation_name="Temporary directory cleanup"
    )
    async def cleanup_temp_directories(self, additional_dirs: Optional[List[Path]] = None) -> CleanupResults:
        """Clean up temporary directories with progress tracking.
        
        Args:
            additional_dirs: Optional additional directories to clean up
            
        Returns:
            CleanupResults with operation details
        """
        results = CleanupResults()
        
        # Combine registered temp directories with additional directories
        all_temp_dirs = set(self._temp_directories)
        if additional_dirs:
            all_temp_dirs.update(additional_dirs)
        
        if not all_temp_dirs:
            self.logger.info("No temporary directories to clean up")
            return results
        
        self.logger.info(f"Cleaning up {len(all_temp_dirs)} temporary directories")
        
        with self.progress_manager.create_progress_bar(
            "Cleaning up temporary directories...",
            total=len(all_temp_dirs)
        ) as progress:
            
            for temp_dir in all_temp_dirs:
                results.operations_attempted += 1
                
                try:
                    if await self._cleanup_single_directory(temp_dir, progress):
                        results.add_success(temp_dir)
                    else:
                        results.add_failure(temp_dir, "Directory not found or already removed")
                        
                except Exception as e:
                    error_msg = str(e)
                    results.add_failure(temp_dir, error_msg)
                    self.logger.warning(f"Failed to remove temporary directory {temp_dir}: {error_msg}")
                
                # Small delay for visual feedback
                await asyncio.sleep(0.02)
        
        # Clear the registered temp directories after cleanup
        self._temp_directories.clear()
        
        return results
    
    async def cleanup_failed_installation(self, setup_results: LunaResults) -> CleanupResults:
        """Clean up after failed installation attempts.
        
        Args:
            setup_results: Setup results to determine what needs cleanup
            
        Returns:
            CleanupResults with cleanup operation details
        """
        results = CleanupResults()
        
        self.logger.info("Performing failed installation cleanup")
        
        # Collect items to clean up based on what was created
        cleanup_items = []
        
        # Add created directories (in reverse order for proper cleanup)
        for directory in reversed(setup_results.directories_created):
            cleanup_items.append(CleanupOperation(
                path=directory,
                operation_type="directory",
                description=f"Remove created directory: {directory.name}",
                critical=False,
                created_by="setup_process"
            ))
        
        # Add any files that were downloaded but installation failed
        for url, success in setup_results.files_downloaded:
            if success:
                # Try to determine the file path from the URL
                filename = Path(url).name or "downloaded_file"
                # This is a best guess - in practice, the download manager should track this
                temp_file = Path("temp") / filename
                if temp_file.exists():
                    cleanup_items.append(CleanupOperation(
                        path=temp_file,
                        operation_type="file",
                        description=f"Remove downloaded file: {filename}",
                        critical=False,
                        created_by="download_manager"
                    ))
        
        # Add registered temporary files and directories
        for temp_file in self._temp_files:
            cleanup_items.append(CleanupOperation(
                path=temp_file,
                operation_type="temp_file",
                description=f"Remove temporary file: {temp_file.name}",
                critical=False,
                created_by=self._creation_metadata.get(temp_file, "unknown")
            ))
        
        for temp_dir in self._temp_directories:
            cleanup_items.append(CleanupOperation(
                path=temp_dir,
                operation_type="directory",
                description=f"Remove temporary directory: {temp_dir.name}",
                critical=False,
                created_by=self._creation_metadata.get(temp_dir, "unknown")
            ))
        
        # Add custom cleanup operations
        cleanup_items.extend(self._cleanup_operations)
        
        if not cleanup_items:
            self.logger.info("No items to clean up after failed installation")
            return results
        
        # Perform cleanup operations
        with self.progress_manager.create_progress_bar(
            "Cleaning up failed installation...",
            total=len(cleanup_items)
        ) as progress:
            
            for operation in cleanup_items:
                results.operations_attempted += 1
                
                try:
                    success = await self._perform_cleanup_operation(operation, progress)
                    if success:
                        results.add_success(operation.path)
                    else:
                        results.add_failure(operation.path, "Operation failed")
                        
                except Exception as e:
                    error_msg = str(e)
                    results.add_failure(operation.path, error_msg)
                    
                    if operation.critical:
                        self.logger.error(f"Critical cleanup operation failed: {error_msg}")
                        raise FileOperationError(f"Critical cleanup failed: {error_msg}")
                    else:
                        self.logger.warning(f"Non-critical cleanup operation failed: {error_msg}")
                
                await asyncio.sleep(0.02)
        
        # Clear all registered items after cleanup
        self._temp_files.clear()
        self._temp_directories.clear()
        self._created_files.clear()
        self._created_directories.clear()
        self._cleanup_operations.clear()
        self._creation_metadata.clear()
        
        return results
    
    async def validate_cleanup(self, results: CleanupResults) -> bool:
        """Validate that cleanup operations were successful.
        
        Args:
            results: CleanupResults to validate
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        validation_failed = False
        
        with self.progress_manager.show_spinner("Validating cleanup operations..."):
            # Check that cleaned paths no longer exist
            for path in results.cleaned_paths:
                if path.exists():
                    results.add_warning(f"Path still exists after cleanup: {path}")
                    validation_failed = True
            
            # Check that failed paths still exist (if they should)
            for path in results.failed_paths:
                if not path.exists():
                    # This is actually good - the path was cleaned up despite the "failure"
                    results.add_warning(f"Path was actually cleaned despite reported failure: {path}")
        
        if validation_failed:
            self.logger.warning("Cleanup validation found issues")
            return False
        
        self.logger.info("Cleanup validation passed")
        return True
    
    @asynccontextmanager
    async def temp_file_context(self, temp_dir: Path, 
                               auto_cleanup: bool = True) -> AsyncGenerator[List[Path], None]:
        """Context manager for temporary file tracking and automatic cleanup.
        
        Args:
            temp_dir: Directory for temporary files
            auto_cleanup: Whether to automatically clean up on exit
            
        Yields:
            List to track temporary files (append files to this list)
        """
        temp_files: List[Path] = []
        
        try:
            # Ensure temp directory exists
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.register_temp_directory(temp_dir, "temp_file_context")
            
            yield temp_files
            
        finally:
            if auto_cleanup:
                # Register all tracked files for cleanup
                for temp_file in temp_files:
                    self.register_temp_file(temp_file, "temp_file_context")
                
                # Clean up tracked files
                await self.cleanup_temp_files()
                
                # Clean up the temp directory if it's empty
                try:
                    if temp_dir.exists() and not any(temp_dir.iterdir()):
                        temp_dir.rmdir()
                        self.logger.debug(f"Removed empty temp directory: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")
    
    @asynccontextmanager
    async def installation_context(self, setup_results: LunaResults) -> AsyncGenerator[None, None]:
        """Context manager for installation with automatic cleanup on failure.
        
        Args:
            setup_results: Setup results to track for potential cleanup
            
        Yields:
            None
        """
        try:
            yield
        except Exception as e:
            self.logger.error(f"Installation failed, performing cleanup: {e}")
            
            # Perform cleanup of failed installation
            cleanup_results = await self.cleanup_failed_installation(setup_results)
            
            # Log cleanup results
            if cleanup_results.operations_attempted > 0:
                success_rate = cleanup_results.success_rate * 100
                self.logger.info(
                    f"Cleanup completed: {cleanup_results.operations_successful}/"
                    f"{cleanup_results.operations_attempted} operations successful "
                    f"({success_rate:.1f}%)"
                )
                
                if cleanup_results.errors:
                    self.logger.warning(f"Cleanup errors: {len(cleanup_results.errors)}")
                    for error in cleanup_results.errors[:5]:  # Log first 5 errors
                        self.logger.warning(f"  - {error}")
            
            # Re-raise the original exception
            raise
    
    async def _cleanup_single_file(self, file_path: Path, progress) -> bool:
        """Clean up a single file.
        
        Args:
            file_path: Path to the file to clean up
            progress: Progress context for updates
            
        Returns:
            True if cleanup was successful, False if file didn't exist
        """
        try:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                    progress.update(1, f"Removed file: {file_path.name}")
                    self.logger.debug(f"Removed file: {file_path}")
                    return True
                else:
                    progress.update(1, f"Not a file: {file_path.name}")
                    return False
            else:
                progress.update(1, f"Already removed: {file_path.name}")
                return False
                
        except PermissionError as e:
            progress.update(1, f"Permission denied: {file_path.name}")
            raise PermissionError(f"Permission denied removing {file_path}") from e
        except Exception as e:
            progress.update(1, f"Error: {file_path.name}")
            raise FileOperationError(f"Failed to remove {file_path}: {str(e)}") from e
    
    async def _cleanup_single_directory(self, dir_path: Path, progress) -> bool:
        """Clean up a single directory.
        
        Args:
            dir_path: Path to the directory to clean up
            progress: Progress context for updates
            
        Returns:
            True if cleanup was successful, False if directory didn't exist
        """
        try:
            if dir_path.exists():
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    progress.update(1, f"Removed directory: {dir_path.name}")
                    self.logger.debug(f"Removed directory: {dir_path}")
                    return True
                else:
                    progress.update(1, f"Not a directory: {dir_path.name}")
                    return False
            else:
                progress.update(1, f"Already removed: {dir_path.name}")
                return False
                
        except PermissionError as e:
            progress.update(1, f"Permission denied: {dir_path.name}")
            raise PermissionError(f"Permission denied removing {dir_path}") from e
        except Exception as e:
            progress.update(1, f"Error: {dir_path.name}")
            raise FileOperationError(f"Failed to remove {dir_path}: {str(e)}") from e
    
    async def _perform_cleanup_operation(self, operation: CleanupOperation, progress) -> bool:
        """Perform a single cleanup operation.
        
        Args:
            operation: CleanupOperation to perform
            progress: Progress context for updates
            
        Returns:
            True if operation was successful, False otherwise
        """
        try:
            if operation.operation_type in ("file", "temp_file"):
                return await self._cleanup_single_file(operation.path, progress)
            elif operation.operation_type == "directory":
                return await self._cleanup_single_directory(operation.path, progress)
            else:
                progress.update(1, f"Unknown operation: {operation.operation_type}")
                return False
                
        except Exception as e:
            progress.update(1, f"Failed: {operation.path.name}")
            raise e
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get a summary of registered cleanup items.
        
        Returns:
            Dictionary containing cleanup summary information
        """
        return {
            'temp_files': len(self._temp_files),
            'temp_directories': len(self._temp_directories),
            'created_files': len(self._created_files),
            'created_directories': len(self._created_directories),
            'custom_operations': len(self._cleanup_operations),
            'total_items': (
                len(self._temp_files) + len(self._temp_directories) + 
                len(self._created_files) + len(self._created_directories) + 
                len(self._cleanup_operations)
            )
        }