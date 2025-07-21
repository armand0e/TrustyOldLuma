"""
Security Configuration Manager for Luna Gaming Tool.

This module handles Windows Defender exclusions and security settings for Luna components,
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

from luna.managers.display_managers import ProgressDisplayManager, ErrorDisplayManager
from luna.models.models import LunaResults
from luna.core.config import MAX_RETRY_ATTEMPTS, RETRY_DELAY


class SecurityConfigManager:
    """Manages Windows Defender exclusions and security settings for Luna components."""
    
    def __init__(self, console: Console):
        """Initialize the Luna security configuration manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.logger = logging.getLogger(__name__)
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
        self._is_windows = os.name == 'nt'
        
    async def add_defender_exclusions(self, paths: List[Path], results: LunaResults) -> None:
        """Add Windows Defender exclusions for Luna component paths.
        
        Args:
            paths: List of Luna paths to exclude from Windows Defender scanning
            results: Luna setup results to update
        """
        if not self._is_windows:
            self.logger.info("Windows Defender exclusions are only applicable on Windows")
            self.console.print("[yellow]⚠️  Windows Defender exclusions are only applicable on Windows[/yellow]")
            return
            
        if not paths:
            return
            
        with self.progress_manager.create_progress_bar(
            "Adding Luna security exclusions...", 
            total=len(paths)
        ) as progress:
            
            for path in paths:
                try:
                    # Attempt to add Luna exclusion with retry logic
                    success = False
                    error_message = ""
                    
                    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
                        progress.update(0, f"Adding Luna exclusion for {path.name} (attempt {attempt}/{MAX_RETRY_ATTEMPTS})")
                        
                        success, output = await self._add_defender_exclusion(path)
                        if success:
                            progress.update(1, f"Added Luna exclusion for {path.name}")
                            break
                        else:
                            error_message = output
                            if attempt < MAX_RETRY_ATTEMPTS:
                                # Show retry prompt
                                if self.error_manager.display_retry_prompt(
                                    f"Add Luna security exclusion for {path.name}", attempt, MAX_RETRY_ATTEMPTS
                                ):
                                    await asyncio.sleep(RETRY_DELAY * attempt)  # Exponential backoff
                                    continue
                                else:
                                    break  # User chose not to retry
                    
                    # Record result
                    results.exclusions_added.append((path, success))
                    
                    # If failed after all attempts, show manual instructions
                    if not success:
                        warning_msg = f"Failed to add Luna security exclusion for {path}: {error_message}"
                        results.add_warning(warning_msg)
                        self.error_manager.display_warning(
                            warning_msg,
                            "You may need to add this Luna exclusion manually"
                        )
                        progress.update(1, f"Failed to add Luna exclusion for {path.name}")
                        
                except Exception as e:
                    error_msg = f"Error adding Luna security exclusion for {path}: {str(e)}"
                    results.add_error(error_msg)
                    self.error_manager.display_error(
                        e,
                        "Luna security exclusion configuration",
                        "You may need to add Luna security exclusions manually"
                    )
                    progress.update(1, f"Error adding Luna exclusion for {path.name}")
    
    async def _add_defender_exclusion(self, path: Path) -> Tuple[bool, str]:
        """Add a Windows Defender exclusion for a specific Luna path.
        
        Args:
            path: Luna path to exclude from Windows Defender scanning
            
        Returns:
            Tuple of (success, output_or_error_message)
        """
        if not self._is_windows:
            return False, "Windows Defender exclusions are only applicable on Windows"
            
        # Ensure Luna path exists before adding exclusion
        if not path.exists():
            try:
                # Create Luna directory if it doesn't exist
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Failed to create Luna directory for exclusion: {str(e)}"
        
        # PowerShell command to add Luna exclusion
        ps_command = f'Add-MpPreference -ExclusionPath "{path}"'
        
        try:
            success, output = self._execute_powershell_command(ps_command)
            if success:
                self.logger.info(f"Added Windows Defender exclusion for Luna path: {path}")
                return True, "Luna exclusion added successfully"
            else:
                self.logger.warning(f"Failed to add Windows Defender exclusion for Luna path {path}: {output}")
                return False, output
        except Exception as e:
            self.logger.error(f"Error adding Windows Defender exclusion for Luna: {str(e)}")
            return False, str(e)
    
    async def verify_antivirus_protection(self, luna_paths: Dict[str, Path], results: LunaResults) -> bool:
        """Review Luna component folders to ensure antivirus didn't remove files.
        
        Args:
            luna_paths: Dictionary of Luna component paths (injector, unlocker, etc.)
            results: Luna setup results to update
            
        Returns:
            True if files are intact, False if files were removed
        """
        all_files_intact = True
        
        # Define critical files for each Luna component
        luna_critical_files = {
            'injector': [
                "luna_injector.exe",  # Renamed from DLLInjector.exe
                "luna_injector.ini",  # Renamed from DLLInjector.ini
                "luna_core_x86.dll",  # Renamed from GreenLuma_2020_x86.dll
                "luna_core_x64.dll"   # Renamed from GreenLuma_2020_x64.dll
            ],
            'unlocker': [
                "luna_unlocker.dll",
                "luna_integration.dll",
                "luna_wizard.exe",
                "luna_common.dll"
            ]
        }
        
        total_files = sum(len(files) for files in luna_critical_files.values())
        
        with self.progress_manager.create_progress_bar(
            "Verifying Luna antivirus protection...", 
            total=total_files
        ) as progress:
            
            for component, component_path in luna_paths.items():
                if not component_path.exists():
                    results.add_warning(f"Luna {component} folder not found at {component_path}")
                    all_files_intact = False
                    # Skip files for this component but update progress
                    if component in luna_critical_files:
                        for _ in luna_critical_files[component]:
                            progress.update(1, f"Missing Luna {component} folder")
                    continue
                
                # Check critical files for this component
                if component in luna_critical_files:
                    missing_files = []
                    
                    for file_name in luna_critical_files[component]:
                        file_path = component_path / file_name
                        if not file_path.exists():
                            missing_files.append(file_name)
                            progress.update(1, f"Missing Luna {component} file: {file_name}")
                        else:
                            progress.update(1, f"Verified Luna {component} file: {file_name}")
                        
                        # Small delay for visual feedback
                        await asyncio.sleep(0.1)
                    
                    if missing_files:
                        warning_msg = f"Antivirus may have removed {len(missing_files)} Luna {component} files: {', '.join(missing_files)}"
                        results.add_warning(warning_msg)
                        self.error_manager.display_warning(
                            warning_msg,
                            f"You need to configure Luna security exclusions and extract {component} files again"
                        )
                        all_files_intact = False
            
            return all_files_intact
    
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
    
    async def add_luna_security_exclusions(self, luna_core_path: Path, results: LunaResults) -> None:
        """Add Luna-specific security exclusions for all components.
        
        Args:
            luna_core_path: Base Luna installation path
            results: Luna setup results to update
        """
        # Define Luna component paths that need exclusions
        luna_exclusion_paths = [
            luna_core_path,  # Main Luna directory
            luna_core_path / "injector",  # Luna injector component
            luna_core_path / "unlocker",  # Luna unlocker component
            luna_core_path / "config",    # Luna configuration directory
            luna_core_path / "temp"       # Luna temporary files
        ]
        
        await self.add_defender_exclusions(luna_exclusion_paths, results)
    
    def provide_manual_exclusion_instructions(self, paths: List[Path]) -> None:
        """Display manual instructions for adding Luna security exclusions.
        
        Args:
            paths: List of Luna paths that need exclusions
        """
        if not paths:
            return
            
        # Create markdown instructions
        instructions = """
## Manual Luna Security Exclusion Instructions

Your antivirus software may be blocking Luna components. Follow these steps to add exclusions:

1. **Open Windows Security**
   - Click Start > Settings > Update & Security > Windows Security
   - Click on "Virus & threat protection"

2. **Add Luna Exclusions**
   - Under "Virus & threat protection settings", click "Manage settings"
   - Scroll down to "Exclusions" and click "Add or remove exclusions"
   - Click "Add an exclusion" and select "Folder"
   - Add each of these Luna folders:
"""

        # Add each path to the instructions
        for path in paths:
            instructions += f"     - `{path}`\n"
            
        instructions += """
3. **Restart Luna Setup**
   - After adding exclusions, run Luna setup tool again

> **Note:** Adding these exclusions will prevent Windows Defender from scanning Luna folders.
> This is necessary for Luna Gaming Tool components to function properly.
"""

        # Display instructions in a panel
        md = Markdown(instructions)
        panel = Panel(
            md,
            title="🛡️  Manual Luna Security Configuration",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()