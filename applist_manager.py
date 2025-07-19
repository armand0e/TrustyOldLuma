"""
AppList Manager for GreenLuma configuration.

This module handles the creation and management of AppList directories and
configuration files for GreenLuma setup.
"""

import logging
from pathlib import Path
from typing import Optional, List
from rich.console import Console

from models import LunaResults
from exceptions import FileOperationError, ConfigurationError


class AppListManager:
    """Manages AppList folder creation and initial configuration."""
    
    def __init__(self, console: Console):
        """Initialize the AppList manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.logger = logging.getLogger(__name__)
    
    async def setup_applist(self, greenluma_path: Path, app_id: str, results: LunaResults) -> bool:
        """Create AppList directory and initial configuration file.
        
        Args:
            greenluma_path: Path to GreenLuma installation directory
            app_id: Default App ID to include in initial configuration
            results: SetupResults instance to track operation results
            
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            self.logger.info("Setting up AppList directory and configuration")
            
            # Create AppList directory
            applist_path = greenluma_path / "AppList"
            success = await self._create_applist_directory(applist_path)
            
            if not success:
                results.add_error("Failed to create AppList directory")
                return False
            
            # Create initial AppList configuration file
            applist_file = applist_path / "0.txt"
            success = await self._create_initial_applist_file(applist_file, app_id)
            
            if not success:
                results.add_error("Failed to create initial AppList configuration file")
                return False
            
            # Validate the created file
            if not self._validate_applist_format(applist_file):
                results.add_warning("AppList file validation failed, but file was created")
            
            # Add success notification
            self.console.print(f"[green]✅ AppList setup completed successfully[/green]")
            self.console.print(f"[dim]   Directory: {applist_path}[/dim]")
            self.console.print(f"[dim]   Initial App ID: {app_id}[/dim]")
            
            # Track the operation in results
            results.configs_updated.append(("AppList configuration", True))
            
            self.logger.info(f"AppList setup completed: {applist_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to setup AppList: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            results.add_error(error_msg)
            
            # Display error to user
            self.console.print(f"[red]❌ AppList setup failed: {str(e)}[/red]")
            return False
    
    async def _create_applist_directory(self, applist_path: Path) -> bool:
        """Create the AppList directory.
        
        Args:
            applist_path: Path where AppList directory should be created
            
        Returns:
            True if directory was created or already exists, False on failure
        """
        try:
            if applist_path.exists():
                if applist_path.is_dir():
                    self.logger.info(f"AppList directory already exists: {applist_path}")
                    return True
                else:
                    raise FileOperationError(f"AppList path exists but is not a directory: {applist_path}")
            
            # Create the directory
            applist_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created AppList directory: {applist_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create AppList directory {applist_path}: {str(e)}")
            return False
    
    async def _create_initial_applist_file(self, applist_file: Path, app_id: str) -> bool:
        """Create initial AppList configuration file with default App ID.
        
        Args:
            applist_file: Path to the AppList file to create
            app_id: App ID to include in the file
            
        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            # Check if file already exists
            if applist_file.exists():
                self.logger.info(f"AppList file already exists: {applist_file}")
                return True
            
            # Create the initial AppList file with the provided App ID
            with open(applist_file, 'w', encoding='utf-8') as f:
                f.write(f"{app_id}\n")
            
            self.logger.info(f"Created initial AppList file: {applist_file} with App ID: {app_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create AppList file {applist_file}: {str(e)}")
            return False
    
    def _validate_applist_format(self, applist_file: Path) -> bool:
        """Validate AppList file format and content.
        
        Args:
            applist_file: Path to the AppList file to validate
            
        Returns:
            True if file format is valid, False otherwise
        """
        try:
            if not applist_file.exists():
                self.logger.warning(f"AppList file does not exist: {applist_file}")
                return False
            
            # Read and validate file content
            with open(applist_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                self.logger.warning(f"AppList file is empty: {applist_file}")
                return False
            
            # Split into lines and validate each App ID
            lines = content.split('\n')
            valid_lines = 0
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
                
                # Validate that each line contains a numeric App ID
                if not line.isdigit():
                    self.logger.warning(f"Invalid App ID on line {line_num}: '{line}' (not numeric)")
                    continue
                
                # Check for reasonable App ID range (Steam App IDs are typically positive integers)
                app_id_num = int(line)
                if app_id_num <= 0:
                    self.logger.warning(f"Invalid App ID on line {line_num}: {app_id_num} (not positive)")
                    continue
                
                valid_lines += 1
            
            if valid_lines == 0:
                self.logger.warning(f"No valid App IDs found in AppList file: {applist_file}")
                return False
            
            self.logger.info(f"AppList file validation successful: {valid_lines} valid App IDs found")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate AppList file {applist_file}: {str(e)}")
            return False
    
    def add_app_id(self, applist_path: Path, app_id: str) -> bool:
        """Add a new App ID to an existing AppList file.
        
        Args:
            applist_path: Path to the AppList directory
            app_id: App ID to add
            
        Returns:
            True if App ID was added successfully, False otherwise
        """
        try:
            # Validate the App ID
            if not app_id.isdigit() or int(app_id) <= 0:
                raise ValueError(f"Invalid App ID: {app_id}")
            
            # Find the next available AppList file
            file_index = 0
            while True:
                applist_file = applist_path / f"{file_index}.txt"
                if not applist_file.exists():
                    # Create new file
                    with open(applist_file, 'w', encoding='utf-8') as f:
                        f.write(f"{app_id}\n")
                    self.logger.info(f"Created new AppList file {applist_file} with App ID: {app_id}")
                    return True
                
                # Check if this file has space (less than 100 App IDs per file is reasonable)
                with open(applist_file, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                
                if len(lines) < 100:
                    # Check if App ID already exists
                    if app_id in lines:
                        self.logger.info(f"App ID {app_id} already exists in {applist_file}")
                        return True
                    
                    # Add to existing file
                    with open(applist_file, 'a', encoding='utf-8') as f:
                        f.write(f"{app_id}\n")
                    self.logger.info(f"Added App ID {app_id} to existing file: {applist_file}")
                    return True
                
                file_index += 1
                
                # Safety check to prevent infinite loop
                if file_index > 1000:
                    raise FileOperationError("Too many AppList files, cannot add new App ID")
            
        except Exception as e:
            self.logger.error(f"Failed to add App ID {app_id}: {str(e)}")
            return False
    
    def get_app_ids(self, applist_path: Path) -> List[str]:
        """Get all App IDs from AppList files.
        
        Args:
            applist_path: Path to the AppList directory
            
        Returns:
            List of App IDs found in AppList files
        """
        app_ids = []
        
        try:
            if not applist_path.exists() or not applist_path.is_dir():
                self.logger.warning(f"AppList directory does not exist: {applist_path}")
                return app_ids
            
            # Find all AppList files (numbered .txt files)
            applist_files = sorted([f for f in applist_path.glob("*.txt") if f.stem.isdigit()])
            
            for applist_file in applist_files:
                try:
                    with open(applist_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and line.isdigit():
                                app_ids.append(line)
                except Exception as e:
                    self.logger.warning(f"Failed to read AppList file {applist_file}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(app_ids)} App IDs in AppList directory")
            return app_ids
            
        except Exception as e:
            self.logger.error(f"Failed to get App IDs from {applist_path}: {str(e)}")
            return app_ids