"""
Configuration Handler for the Gaming Setup Tool.

This module handles configuration file updates and management, including
DLLInjector.ini updates and Koalageddon config file replacement.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from rich.console import Console

from display_managers import ProgressDisplayManager, ErrorDisplayManager
from models import LunaResults
from config import MAX_RETRY_ATTEMPTS, RETRY_DELAY


class ConfigurationHandler:
    """Handles configuration file updates and management."""
    
    def __init__(self, console: Console):
        """Initialize the configuration handler.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.logger = logging.getLogger(__name__)
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
    
    async def update_dll_injector_config(self, dll_path: Path, config_path: Path, 
                                       results: LunaResults) -> bool:
        """Update DLLInjector.ini with correct DLL path.
        
        Args:
            dll_path: Path to the DLL file
            config_path: Path to the DLLInjector.ini file
            results: Setup results to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not config_path.exists():
            error_msg = f"DLLInjector.ini not found at {config_path}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                FileNotFoundError(error_msg),
                "Configuration update",
                "Ensure GreenLuma was extracted correctly"
            )
            return False
        
        if not dll_path.exists():
            error_msg = f"DLL file not found at {dll_path}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                FileNotFoundError(error_msg),
                "Configuration update",
                "Ensure GreenLuma was extracted correctly"
            )
            return False
        
        # Create backup of original config
        backup_path = await self._create_backup(config_path)
        if not backup_path:
            warning_msg = f"Failed to create backup of {config_path.name}"
            results.add_warning(warning_msg)
            self.error_manager.display_warning(warning_msg)
        
        try:
            with self.progress_manager.show_spinner(f"Updating {config_path.name}"):
                # Read the current config
                config_content = await self._read_file(config_path)
                if config_content is None:
                    error_msg = f"Failed to read {config_path}"
                    results.add_error(error_msg)
                    return False
                
                # Update the DLL path in the config
                updated_content = self._update_dll_path_in_config(config_content, dll_path)
                
                # Write the updated config
                success = await self._write_file(config_path, updated_content)
                if success:
                    self.logger.info(f"Updated DLL path in {config_path}")
                    results.configs_updated.append((str(config_path), True))
                    return True
                else:
                    error_msg = f"Failed to write updated config to {config_path}"
                    results.add_error(error_msg)
                    
                    # Try to restore backup
                    if backup_path and backup_path.exists():
                        await self._restore_backup(backup_path, config_path)
                    
                    return False
                    
        except Exception as e:
            error_msg = f"Error updating DLLInjector.ini: {str(e)}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                e,
                "Configuration update",
                "You may need to manually update DLLInjector.ini"
            )
            
            # Try to restore backup
            if backup_path and backup_path.exists():
                await self._restore_backup(backup_path, config_path)
                
            return False
    
    def _update_dll_path_in_config(self, config_content: str, dll_path: Path) -> str:
        """Update the DLL path in the config content.
        
        Args:
            config_content: Current config file content
            dll_path: Path to the DLL file
            
        Returns:
            Updated config content
        """
        lines = config_content.splitlines()
        updated_lines = []
        
        for line in lines:
            if line.strip().startswith("DLL="):
                # Replace DLL path line
                updated_lines.append(f"DLL={dll_path}")
            else:
                updated_lines.append(line)
        
        return "\n".join(updated_lines)
    
    async def replace_koalageddon_config(self, source_path: Path, destination_path: Path, 
                                       results: LunaResults) -> bool:
        """Replace Koalageddon config with repository version.
        
        Args:
            source_path: Path to the source config file
            destination_path: Path to the destination config directory
            results: Setup results to update
            
        Returns:
            True if replacement was successful, False otherwise
        """
        if not source_path.exists():
            error_msg = f"Source config file not found at {source_path}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                FileNotFoundError(error_msg),
                "Configuration replacement",
                "Ensure the repository config file exists"
            )
            return False
        
        # Ensure destination directory exists
        if not destination_path.exists():
            try:
                destination_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created config directory: {destination_path}")
            except Exception as e:
                error_msg = f"Failed to create config directory {destination_path}: {str(e)}"
                results.add_error(error_msg)
                self.error_manager.display_error(
                    e,
                    "Configuration replacement",
                    "You may need to manually create the config directory"
                )
                return False
        
        # Determine target file path
        target_path = destination_path / source_path.name
        
        # Create backup if target exists
        backup_path = None
        if target_path.exists():
            backup_path = await self._create_backup(target_path)
            if not backup_path:
                warning_msg = f"Failed to create backup of {target_path.name}"
                results.add_warning(warning_msg)
                self.error_manager.display_warning(warning_msg)
        
        # Attempt to replace config with retry logic
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                with self.progress_manager.show_spinner(
                    f"Replacing {target_path.name} (attempt {attempt}/{MAX_RETRY_ATTEMPTS})"
                ):
                    # Copy the config file
                    shutil.copy2(source_path, target_path)
                    
                    # Verify the copy was successful
                    if await self._verify_file_copy(source_path, target_path):
                        self.logger.info(f"Replaced config file: {target_path}")
                        results.configs_updated.append((str(target_path), True))
                        return True
                    else:
                        raise IOError(f"File verification failed for {target_path}")
                        
            except Exception as e:
                error_msg = f"Failed to replace config file (attempt {attempt}): {str(e)}"
                self.logger.warning(error_msg)
                
                if attempt < MAX_RETRY_ATTEMPTS:
                    # Show retry prompt
                    if self.error_manager.display_retry_prompt(
                        f"Replace config file {target_path.name}", attempt, MAX_RETRY_ATTEMPTS
                    ):
                        await asyncio.sleep(RETRY_DELAY * attempt)  # Exponential backoff
                        continue
                    else:
                        break  # User chose not to retry
                        
        # All attempts failed
        error_msg = f"Failed to replace config file after {MAX_RETRY_ATTEMPTS} attempts"
        results.add_error(error_msg)
        results.configs_updated.append((str(target_path), False))
        self.error_manager.display_error(
            IOError(error_msg),
            "Configuration replacement",
            "You may need to manually copy the config file"
        )
        
        # Try to restore backup
        if backup_path and backup_path.exists():
            await self._restore_backup(backup_path, target_path)
            
        return False
    
    async def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file, or None if backup failed
        """
        if not file_path.exists():
            return None
            
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.warning(f"Failed to create backup of {file_path}: {str(e)}")
            return None
    
    async def _restore_backup(self, backup_path: Path, original_path: Path) -> bool:
        """Restore a file from backup.
        
        Args:
            backup_path: Path to the backup file
            original_path: Path to restore to
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, original_path)
                self.logger.info(f"Restored {original_path} from backup")
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Failed to restore backup: {str(e)}")
            return False
    
    async def _read_file(self, file_path: Path) -> Optional[str]:
        """Read a file asynchronously.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string, or None if read failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to read {file_path}: {str(e)}")
            return None
    
    async def _write_file(self, file_path: Path, content: str) -> bool:
        """Write content to a file asynchronously.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to write to {file_path}: {str(e)}")
            return False
    
    async def _verify_file_copy(self, source_path: Path, target_path: Path) -> bool:
        """Verify that a file was copied correctly.
        
        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            
        Returns:
            True if files match, False otherwise
        """
        if not source_path.exists() or not target_path.exists():
            return False
            
        try:
            # Compare file sizes
            if source_path.stat().st_size != target_path.stat().st_size:
                return False
                
            # Compare file content (for small files)
            if source_path.stat().st_size < 10 * 1024 * 1024:  # 10 MB
                with open(source_path, 'rb') as src, open(target_path, 'rb') as tgt:
                    return src.read() == tgt.read()
                    
            # For larger files, just check size
            return True
            
        except Exception as e:
            self.logger.warning(f"File verification failed: {str(e)}")
            return False