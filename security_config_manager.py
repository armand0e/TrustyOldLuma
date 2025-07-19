"""
Security Configuration Manager for the Gaming Setup Tool.

This module handles Windows Defender exclusions and security settings,
with PowerShell command execution and error handling.
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from display_managers import ProgressDisplayManager, ErrorDisplayManager
from models import LunaResults
from config import MAX_RETRY_ATTEMPTS, RETRY_DELAY


class SecurityConfigManager:
    """Manages Windows Defender exclusions and security settings."""
    
    def __init__(self, console: Console):
        """Initialize the security configuration manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.logger = logging.getLogger(__name__)
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
        self._is_windows = os.name == 'nt'
        
    async def add_defender_exclusions(self, paths: List[Path], results: LunaResults) -> None:
        """Add Windows Defender exclusions for specified paths.
        
        Args:
            paths: List of paths to exclude from Windows Defender scanning
            results: Setup results to update
        """
        if not self._is_windows:
            self.logger.info("Windows Defender exclusions are only applicable on Windows")
            self.console.print("[yellow]⚠️  Windows Defender exclusions are only applicable on Windows[/yellow]")
            return
            
        if not paths:
            return
            
        with self.progress_manager.create_progress_bar(
            "Adding security exclusions...", 
            total=len(paths)
        ) as progress:
            
            for path in paths:
                try:
                    # Attempt to add exclusion with retry logic
                    success = False
                    error_message = ""
                    
                    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
                        progress.update(0, f"Adding exclusion for {path.name} (attempt {attempt}/{MAX_RETRY_ATTEMPTS})")
                        
                        success, output = await self._add_defender_exclusion(path)
                        if success:
                            progress.update(1, f"Added exclusion for {path.name}")
                            break
                        else:
                            error_message = output
                            if attempt < MAX_RETRY_ATTEMPTS:
                                # Show retry prompt
                                if self.error_manager.display_retry_prompt(
                                    f"Add security exclusion for {path.name}", attempt, MAX_RETRY_ATTEMPTS
                                ):
                                    await asyncio.sleep(RETRY_DELAY * attempt)  # Exponential backoff
                                    continue
                                else:
                                    break  # User chose not to retry
                    
                    # Record result
                    results.exclusions_added.append((path, success))
                    
                    # If failed after all attempts, show manual instructions
                    if not success:
                        warning_msg = f"Failed to add security exclusion for {path}: {error_message}"
                        results.add_warning(warning_msg)
                        self.error_manager.display_warning(
                            warning_msg,
                            "You may need to add this exclusion manually"
                        )
                        progress.update(1, f"Failed to add exclusion for {path.name}")
                        
                except Exception as e:
                    error_msg = f"Error adding security exclusion for {path}: {str(e)}"
                    results.add_error(error_msg)
                    self.error_manager.display_error(
                        e,
                        "Security exclusion configuration",
                        "You may need to add security exclusions manually"
                    )
                    progress.update(1, f"Error adding exclusion for {path.name}")
    
    async def _add_defender_exclusion(self, path: Path) -> Tuple[bool, str]:
        """Add a Windows Defender exclusion for a specific path.
        
        Args:
            path: Path to exclude from Windows Defender scanning
            
        Returns:
            Tuple of (success, output_or_error_message)
        """
        if not self._is_windows:
            return False, "Windows Defender exclusions are only applicable on Windows"
            
        # Ensure path exists before adding exclusion
        if not path.exists():
            try:
                # Create directory if it doesn't exist
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Failed to create directory for exclusion: {str(e)}"
        
        # PowerShell command to add exclusion
        ps_command = f'Add-MpPreference -ExclusionPath "{path}"'
        
        try:
            success, output = self._execute_powershell_command(ps_command)
            if success:
                self.logger.info(f"Added Windows Defender exclusion for {path}")
                return True, "Exclusion added successfully"
            else:
                self.logger.warning(f"Failed to add Windows Defender exclusion for {path}: {output}")
                return False, output
        except Exception as e:
            self.logger.error(f"Error adding Windows Defender exclusion: {str(e)}")
            return False, str(e)
    
    async def verify_antivirus_protection(self, greenluma_path: Path, results: LunaResults) -> bool:
        """Review GreenLuma folder contents to ensure antivirus didn't remove files.
        
        Args:
            greenluma_path: Path to GreenLuma folder
            results: Setup results to update
            
        Returns:
            True if files are intact, False if files were removed
        """
        if not greenluma_path.exists():
            results.add_warning(f"GreenLuma folder not found at {greenluma_path}")
            return False
            
        # Critical files that should exist in GreenLuma folder
        critical_files = [
            "DLLInjector.exe",
            "DLLInjector.ini",
            "GreenLuma_2020_x86.dll",
            "GreenLuma_2020_x64.dll"
        ]
        
        with self.progress_manager.create_progress_bar(
            "Verifying antivirus protection...", 
            total=len(critical_files)
        ) as progress:
            
            missing_files = []
            
            for file_name in critical_files:
                file_path = greenluma_path / file_name
                if not file_path.exists():
                    missing_files.append(file_name)
                    progress.update(1, f"Missing file: {file_name}")
                else:
                    progress.update(1, f"Verified file: {file_name}")
                
                # Small delay for visual feedback
                await asyncio.sleep(0.1)
            
            if missing_files:
                warning_msg = f"Antivirus may have removed {len(missing_files)} files: {', '.join(missing_files)}"
                results.add_warning(warning_msg)
                self.error_manager.display_warning(
                    warning_msg,
                    "You need to configure security exclusions and extract files again"
                )
                return False
            
            return True
    
    def _execute_powershell_command(self, command: str) -> Tuple[bool, str]:
        """Execute PowerShell command and return result.
        
        Args:
            command: PowerShell command to execute
            
        Returns:
            Tuple of (success, output_or_error_message)
        """
        if not self._is_windows:
            return False, "PowerShell commands are only applicable on Windows"
            
        try:
            # Construct full PowerShell command
            full_command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", command
            ]
            
            # Execute command and capture output
            process = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit code
            )
            
            # Check if command was successful
            if process.returncode == 0:
                return True, process.stdout.strip()
            else:
                error_output = process.stderr.strip() or process.stdout.strip() or f"Exit code: {process.returncode}"
                return False, error_output
                
        except Exception as e:
            return False, str(e)
    
    def provide_manual_exclusion_instructions(self, paths: List[Path]) -> None:
        """Display manual instructions for adding security exclusions.
        
        Args:
            paths: List of paths that need exclusions
        """
        if not paths:
            return
            
        # Create markdown instructions
        instructions = """
## Manual Windows Defender Exclusion Instructions

Your antivirus software may be blocking some files. Follow these steps to add exclusions:

1. **Open Windows Security**
   - Click Start > Settings > Update & Security > Windows Security
   - Click on "Virus & threat protection"

2. **Add Exclusions**
   - Under "Virus & threat protection settings", click "Manage settings"
   - Scroll down to "Exclusions" and click "Add or remove exclusions"
   - Click "Add an exclusion" and select "Folder"
   - Add each of these folders:
"""

        # Add each path to the instructions
        for path in paths:
            instructions += f"     - `{path}`\n"
            
        instructions += """
3. **Restart Setup**
   - After adding exclusions, run this setup tool again

> **Note:** Adding these exclusions will prevent Windows Defender from scanning these folders.
> This is necessary for GreenLuma and Koalageddon to function properly.
"""

        # Display instructions in a panel
        md = Markdown(instructions)
        panel = Panel(
            md,
            title="🛡️  Manual Security Configuration",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()