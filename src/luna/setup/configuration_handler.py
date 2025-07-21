"""
Configuration Handler for Luna Gaming Tool.

This module handles Luna configuration file updates and management, including
Luna injector configuration, Luna unlocker configuration, and unified
configuration management with legacy migration support.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from rich.console import Console

from luna.managers.display_managers import ProgressDisplayManager, ErrorDisplayManager
from luna.models.models import LunaResults
from luna.core.config import MAX_RETRY_ATTEMPTS, RETRY_DELAY


class ConfigurationHandler:
    """Handles Luna configuration file updates and management."""
    
    def __init__(self, console: Console):
        """Initialize the Luna configuration handler.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.logger = logging.getLogger(__name__)
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
    
    async def update_dll_injector_config(self, dll_path: Path, config_path: Path, 
                                       results: LunaResults) -> bool:
        """Update Luna injector configuration with correct DLL path.
        
        Args:
            dll_path: Path to the Luna core DLL file
            config_path: Path to the luna_injector.ini file
            results: Luna setup results to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not config_path.exists():
            error_msg = f"Luna injector config not found at {config_path}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                FileNotFoundError(error_msg),
                "Luna configuration update",
                "Ensure Luna injector was extracted correctly"
            )
            return False
        
        if not dll_path.exists():
            error_msg = f"Luna core DLL file not found at {dll_path}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                FileNotFoundError(error_msg),
                "Luna configuration update",
                "Ensure Luna injector was extracted correctly"
            )
            return False
        
        # Create backup of original config
        backup_path = await self._create_backup(config_path)
        if not backup_path:
            warning_msg = f"Failed to create backup of {config_path.name}"
            results.add_warning(warning_msg)
            self.error_manager.display_warning(warning_msg)
        
        try:
            with self.progress_manager.show_spinner(f"Updating Luna injector config: {config_path.name}"):
                # Read the current config
                config_content = await self._read_file(config_path)
                if config_content is None:
                    error_msg = f"Failed to read Luna injector config: {config_path}"
                    results.add_error(error_msg)
                    return False
                
                # Update the DLL path in the config
                updated_content = self._update_dll_path_in_config(config_content, dll_path)
                
                # Write the updated config
                success = await self._write_file(config_path, updated_content)
                if success:
                    self.logger.info(f"Updated Luna injector DLL path in {config_path}")
                    results.configs_updated.append((str(config_path), True))
                    return True
                else:
                    error_msg = f"Failed to write updated Luna injector config to {config_path}"
                    results.add_error(error_msg)
                    
                    # Try to restore backup
                    if backup_path and backup_path.exists():
                        await self._restore_backup(backup_path, config_path)
                    
                    return False
                    
        except Exception as e:
            error_msg = f"Error updating Luna injector configuration: {str(e)}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                e,
                "Luna configuration update",
                "You may need to manually update Luna injector configuration"
            )
            
            # Try to restore backup
            if backup_path and backup_path.exists():
                await self._restore_backup(backup_path, config_path)
                
            return False
    
    def _update_dll_path_in_config(self, config_content: str, dll_path: Path) -> str:
        """Update the Luna DLL path in the config content.
        
        Args:
            config_content: Current Luna config file content
            dll_path: Path to the Luna core DLL file
            
        Returns:
            Updated Luna config content
        """
        lines = config_content.splitlines()
        updated_lines = []
        
        for line in lines:
            if line.strip().startswith("DLL="):
                # Replace Luna DLL path line
                updated_lines.append(f"DLL={dll_path}")
            else:
                updated_lines.append(line)
        
        return "\n".join(updated_lines)
    
    async def update_luna_unlocker_config(self, source_path: Path, destination_path: Path, 
                                        results: LunaResults) -> bool:
        """Update Luna unlocker configuration with repository version.
        
        Args:
            source_path: Path to the source Luna unlocker config file
            destination_path: Path to the destination Luna config directory
            results: Luna setup results to update
            
        Returns:
            True if replacement was successful, False otherwise
        """
        if not source_path.exists():
            error_msg = f"Source Luna unlocker config file not found at {source_path}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                FileNotFoundError(error_msg),
                "Luna unlocker configuration update",
                "Ensure the Luna unlocker config file exists"
            )
            return False
        
        # Ensure Luna destination directory exists
        if not destination_path.exists():
            try:
                destination_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created Luna config directory: {destination_path}")
            except Exception as e:
                error_msg = f"Failed to create Luna config directory {destination_path}: {str(e)}"
                results.add_error(error_msg)
                self.error_manager.display_error(
                    e,
                    "Luna unlocker configuration update",
                    "You may need to manually create the Luna config directory"
                )
                return False
        
        # Determine target file path
        target_path = destination_path / source_path.name
        
        # Create backup if target exists
        backup_path = None
        if target_path.exists():
            backup_path = await self._create_backup(target_path)
            if not backup_path:
                warning_msg = f"Failed to create backup of Luna config: {target_path.name}"
                results.add_warning(warning_msg)
                self.error_manager.display_warning(warning_msg)
        
        # Attempt to replace Luna config with retry logic
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                with self.progress_manager.show_spinner(
                    f"Updating Luna unlocker config: {target_path.name} (attempt {attempt}/{MAX_RETRY_ATTEMPTS})"
                ):
                    # Copy the Luna config file
                    shutil.copy2(source_path, target_path)
                    
                    # Verify the copy was successful
                    if await self._verify_file_copy(source_path, target_path):
                        self.logger.info(f"Updated Luna unlocker config file: {target_path}")
                        results.configs_updated.append((str(target_path), True))
                        return True
                    else:
                        raise IOError(f"Luna config file verification failed for {target_path}")
                        
            except Exception as e:
                error_msg = f"Failed to update Luna unlocker config (attempt {attempt}): {str(e)}"
                self.logger.warning(error_msg)
                
                if attempt < MAX_RETRY_ATTEMPTS:
                    # Show retry prompt
                    if self.error_manager.display_retry_prompt(
                        f"Update Luna unlocker config {target_path.name}", attempt, MAX_RETRY_ATTEMPTS
                    ):
                        await asyncio.sleep(RETRY_DELAY * attempt)  # Exponential backoff
                        continue
                    else:
                        break  # User chose not to retry
                        
        # All attempts failed
        error_msg = f"Failed to update Luna unlocker config after {MAX_RETRY_ATTEMPTS} attempts"
        results.add_error(error_msg)
        results.configs_updated.append((str(target_path), False))
        self.error_manager.display_error(
            IOError(error_msg),
            "Luna unlocker configuration update",
            "You may need to manually copy the Luna unlocker config file"
        )
        
        # Try to restore backup
        if backup_path and backup_path.exists():
            await self._restore_backup(backup_path, target_path)
            
        return False
    
    async def replace_luna_config(self, luna_config_data: Dict[str, Any], config_path: Path,
                                results: LunaResults) -> bool:
        """Replace Luna unified configuration with new settings.
        
        Args:
            luna_config_data: Dictionary containing Luna configuration data
            config_path: Path to the Luna configuration file
            results: Luna setup results to update
            
        Returns:
            True if replacement was successful, False otherwise
        """
        import json
        
        # Create backup of existing config
        backup_path = None
        if config_path.exists():
            backup_path = await self._create_backup(config_path)
            if not backup_path:
                warning_msg = f"Failed to create backup of Luna config: {config_path.name}"
                results.add_warning(warning_msg)
                self.error_manager.display_warning(warning_msg)
        
        # Ensure Luna config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with self.progress_manager.show_spinner(f"Updating Luna unified config: {config_path.name}"):
                # Write Luna configuration as JSON
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(luna_config_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Updated Luna unified configuration: {config_path}")
                results.configs_updated.append((str(config_path), True))
                return True
                
        except Exception as e:
            error_msg = f"Error updating Luna unified configuration: {str(e)}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                e,
                "Luna unified configuration update",
                "You may need to manually update Luna configuration"
            )
            
            # Try to restore backup
            if backup_path and backup_path.exists():
                await self._restore_backup(backup_path, config_path)
                
            return False
    
    async def migrate_legacy_greenluma_config(self, legacy_config_path: Path, 
                                            luna_config_path: Path,
                                            results: LunaResults) -> Optional[Dict[str, Any]]:
        """Migrate legacy GreenLuma configuration to Luna format.
        
        Args:
            legacy_config_path: Path to legacy GreenLuma config file
            luna_config_path: Path to Luna configuration file
            results: Luna setup results to update
            
        Returns:
            Dictionary containing migrated configuration, or None if migration failed
        """
        if not legacy_config_path.exists():
            self.logger.info(f"Legacy GreenLuma config not found at {legacy_config_path}")
            return None
        
        try:
            with self.progress_manager.show_spinner("Migrating legacy GreenLuma configuration to Luna"):
                # Read legacy config
                legacy_content = await self._read_file(legacy_config_path)
                if legacy_content is None:
                    error_msg = f"Failed to read legacy GreenLuma config: {legacy_config_path}"
                    results.add_error(error_msg)
                    return None
                
                # Parse legacy config and convert to Luna format
                luna_config = self._convert_greenluma_to_luna_config(legacy_content)
                
                # Add migration metadata
                luna_config['migration'] = {
                    'from': 'greenluma',
                    'legacy_path': str(legacy_config_path),
                    'migrated_at': asyncio.get_event_loop().time()
                }
                
                self.logger.info("Successfully migrated GreenLuma configuration to Luna format")
                return luna_config
                
        except Exception as e:
            error_msg = f"Error migrating legacy GreenLuma configuration: {str(e)}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                e,
                "Legacy configuration migration",
                "You may need to manually configure Luna"
            )
            return None
    
    async def migrate_legacy_koalageddon_config(self, legacy_config_path: Path,
                                              luna_config_path: Path,
                                              results: LunaResults) -> Optional[Dict[str, Any]]:
        """Migrate legacy Koalageddon configuration to Luna format.
        
        Args:
            legacy_config_path: Path to legacy Koalageddon config file
            luna_config_path: Path to Luna configuration file
            results: Luna setup results to update
            
        Returns:
            Dictionary containing migrated configuration, or None if migration failed
        """
        if not legacy_config_path.exists():
            self.logger.info(f"Legacy Koalageddon config not found at {legacy_config_path}")
            return None
        
        try:
            with self.progress_manager.show_spinner("Migrating legacy Koalageddon configuration to Luna"):
                import json
                
                # Read legacy Koalageddon config (JSON format)
                with open(legacy_config_path, 'r', encoding='utf-8') as f:
                    legacy_config = json.load(f)
                
                # Convert to Luna format
                luna_config = self._convert_koalageddon_to_luna_config(legacy_config)
                
                # Add migration metadata
                luna_config['migration'] = {
                    'from': 'koalageddon',
                    'legacy_path': str(legacy_config_path),
                    'migrated_at': asyncio.get_event_loop().time()
                }
                
                self.logger.info("Successfully migrated Koalageddon configuration to Luna format")
                return luna_config
                
        except Exception as e:
            error_msg = f"Error migrating legacy Koalageddon configuration: {str(e)}"
            results.add_error(error_msg)
            self.error_manager.display_error(
                e,
                "Legacy configuration migration",
                "You may need to manually configure Luna"
            )
            return None
    
    def _convert_greenluma_to_luna_config(self, greenluma_content: str) -> Dict[str, Any]:
        """Convert GreenLuma configuration content to Luna format.
        
        Args:
            greenluma_content: Content of GreenLuma configuration file
            
        Returns:
            Dictionary containing Luna configuration
        """
        luna_config = {
            'luna': {
                'version': '1.0.0',
                'injector': {
                    'enabled': True,
                    'dll_path': '',
                    'auto_inject': True
                },
                'platforms': {
                    'steam': {'enabled': True, 'priority': 1}
                }
            }
        }
        
        # Parse GreenLuma config lines
        lines = greenluma_content.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith('DLL='):
                # Extract DLL path and convert to Luna naming
                dll_path = line[4:].strip()
                if 'GreenLuma' in dll_path:
                    dll_path = dll_path.replace('GreenLuma_2020', 'luna_core')
                luna_config['luna']['injector']['dll_path'] = dll_path
        
        return luna_config
    
    def _convert_koalageddon_to_luna_config(self, koalageddon_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Koalageddon configuration to Luna format.
        
        Args:
            koalageddon_config: Koalageddon configuration dictionary
            
        Returns:
            Dictionary containing Luna configuration
        """
        luna_config = {
            'luna': {
                'version': '1.0.0',
                'unlocker': {
                    'enabled': True,
                    'unlock_dlc': True,
                    'unlock_shared_library': True
                },
                'platforms': {}
            }
        }
        
        # Convert platform settings
        if 'platforms' in koalageddon_config:
            for platform, settings in koalageddon_config['platforms'].items():
                luna_config['luna']['platforms'][platform] = {
                    'enabled': settings.get('enabled', True),
                    'priority': settings.get('priority', 1),
                    'unlock_dlc': settings.get('unlock_dlc', True)
                }
        
        # Convert blacklists
        if 'blacklists' in koalageddon_config:
            luna_config['luna']['unlocker']['app_blacklist'] = koalageddon_config['blacklists'].get('apps', [])
            luna_config['luna']['unlocker']['process_blacklist'] = koalageddon_config['blacklists'].get('processes', [])
        
        return luna_config
    
    async def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a Luna configuration file.
        
        Args:
            file_path: Path to the Luna file to backup
            
        Returns:
            Path to the backup file, or None if backup failed
        """
        if not file_path.exists():
            return None
            
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created Luna config backup: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.warning(f"Failed to create Luna config backup of {file_path}: {str(e)}")
            return None
    
    async def _restore_backup(self, backup_path: Path, original_path: Path) -> bool:
        """Restore a Luna configuration file from backup.
        
        Args:
            backup_path: Path to the backup file
            original_path: Path to restore to
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, original_path)
                self.logger.info(f"Restored Luna config {original_path} from backup")
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Failed to restore Luna config backup: {str(e)}")
            return False
    
    async def _read_file(self, file_path: Path) -> Optional[str]:
        """Read a Luna configuration file asynchronously.
        
        Args:
            file_path: Path to the Luna file to read
            
        Returns:
            File content as string, or None if read failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to read Luna config file {file_path}: {str(e)}")
            return None
    
    async def _write_file(self, file_path: Path, content: str) -> bool:
        """Write content to a Luna configuration file asynchronously.
        
        Args:
            file_path: Path to the Luna file to write
            content: Content to write
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to write to Luna config file {file_path}: {str(e)}")
            return False
    
    async def _verify_file_copy(self, source_path: Path, target_path: Path) -> bool:
        """Verify that a Luna configuration file was copied correctly.
        
        Args:
            source_path: Path to the source Luna file
            target_path: Path to the target Luna file
            
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
            self.logger.warning(f"Luna config file verification failed: {str(e)}")
            return False