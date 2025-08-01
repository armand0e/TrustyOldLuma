"""Admin Handler module for Windows privilege management."""

import ctypes
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional

from .data_models import OperationResult


class AdminHandler:
    """Handles Windows privilege management and admin-only operations."""
    
    def __init__(self):
        """Initialize AdminHandler."""
        pass
    
    def is_admin(self) -> bool:
        """
        Check if the current process has administrator privileges.
        
        Uses ctypes to call Windows API shell32.IsUserAnAdmin().
        
        Returns:
            bool: True if running with admin privileges, False otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            # If we can't determine admin status, assume we're not admin
            return False
    
    def run_elevated_command(self, command: str, timeout: int = 30) -> OperationResult:
        """
        Run a single command with elevation using PowerShell Start-Process.
        
        This shows the UAC prompt but doesn't restart the entire application.
        
        Args:
            command: PowerShell command to run with elevation
            timeout: Timeout in seconds for the command
        
        Returns:
            OperationResult: Result of the elevated command execution.
        """
        try:
            # Construct PowerShell command for elevation
            # We use a temporary script block to run the command elevated
            powershell_cmd = [
                "powershell.exe",
                "-Command",
                f"Start-Process powershell -ArgumentList '-Command', '{command}' -Verb RunAs -Wait -WindowStyle Hidden"
            ]
            
            # Execute the elevation request
            result = subprocess.run(
                powershell_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return OperationResult(
                    success=True,
                    message="Successfully executed elevated command",
                    details=f"Command executed: {command}"
                )
            else:
                return OperationResult(
                    success=False,
                    message="Failed to execute elevated command",
                    details=f"PowerShell returned code {result.returncode}: {result.stderr}",
                    suggestions=[
                        "Make sure you clicked 'Yes' in the UAC prompt",
                        "Check if your user account has admin privileges",
                        "Verify the command syntax is correct"
                    ]
                )
                
        except subprocess.TimeoutExpired:
            return OperationResult(
                success=False,
                message="Elevated command timed out",
                details=f"Command did not complete within {timeout} seconds",
                suggestions=[
                    "Try running the command again",
                    "Check if UAC is configured properly on your system",
                    "Increase the timeout if the command takes longer to execute"
                ]
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message="Failed to execute elevated command",
                details=f"Unexpected error: {str(e)}",
                suggestions=[
                    "Check if PowerShell is available on your system",
                    "Verify the command is valid",
                    "Try running the setup as administrator manually"
                ]
            )
    
    def add_security_exclusions(self, paths: List[str]) -> OperationResult:
        """
        Add Windows Security exclusions using elevated PowerShell commands.
        
        This method will prompt for UAC elevation for each exclusion command
        but keeps the main application running in the same window.
        
        Args:
            paths: List of paths to add as exclusions.
        
        Returns:
            OperationResult: Result of adding security exclusions.
        """
        failed_paths = []
        success_count = 0
        
        for path in paths:
            try:
                # Normalize the path and escape single quotes
                normalized_path = str(Path(path).resolve()).replace("'", "''")
                
                # PowerShell command to add exclusion
                exclusion_command = f"Add-MpPreference -ExclusionPath '{normalized_path}'"
                
                # Run the command with elevation
                result = self.run_elevated_command(exclusion_command, timeout=15)
                
                if result.success:
                    success_count += 1
                else:
                    failed_paths.append((path, result.details))
                    
            except Exception as e:
                failed_paths.append((path, str(e)))
        
        if success_count == len(paths):
            return OperationResult(
                success=True,
                message=f"Successfully added {success_count} security exclusions",
                details=f"Added exclusions for: {', '.join(paths)}"
            )
        elif success_count > 0:
            return OperationResult(
                success=False,
                message=f"Partially successful: {success_count}/{len(paths)} exclusions added",
                details=f"Failed paths: {', '.join([path for path, _ in failed_paths])}",
                suggestions=[
                    "Check if Windows Defender is running",
                    "Try adding the remaining exclusions manually in Windows Security",
                    "Some paths might already be excluded"
                ]
            )
        else:
            return OperationResult(
                success=False,
                message="Failed to add any security exclusions",
                details=f"All paths failed: {'; '.join([f'{path}: {error}' for path, error in failed_paths])}",
                suggestions=[
                    "Check if Windows Defender is running and accessible",
                    "Try adding exclusions manually in Windows Security settings",
                    "Verify that the paths exist and are accessible",
                    "Check if another antivirus software is interfering"
                ]
            )
    
    def create_directories_as_admin(self, paths: List[str]) -> OperationResult:
        """
        Create directories with admin privileges using elevated commands when needed.
        
        First tries to create directories normally, then uses elevation for failed ones.
        
        Args:
            paths: List of directory paths to create.
        
        Returns:
            OperationResult: Result of directory creation.
        """
        created_paths = []
        failed_paths = []
        
        for path_str in paths:
            try:
                path = Path(path_str)
                
                # Check if directory already exists
                if path.exists():
                    if path.is_dir():
                        created_paths.append(str(path))
                        continue
                    else:
                        failed_paths.append((str(path), "Path exists but is not a directory"))
                        continue
                
                # Try to create directory normally first
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    created_paths.append(str(path))
                    continue
                except PermissionError:
                    # If permission denied, try with elevation
                    normalized_path = str(path.resolve()).replace("'", "''")
                    mkdir_command = f"New-Item -ItemType Directory -Path '{normalized_path}' -Force"
                    
                    result = self.run_elevated_command(mkdir_command, timeout=10)
                    
                    if result.success:
                        created_paths.append(str(path))
                    else:
                        failed_paths.append((path_str, f"Elevated creation failed: {result.details}"))
                    
            except OSError as e:
                failed_paths.append((path_str, f"OS error: {str(e)}"))
            except Exception as e:
                failed_paths.append((path_str, f"Unexpected error: {str(e)}"))
        
        if len(created_paths) == len(paths):
            return OperationResult(
                success=True,
                message=f"Successfully created {len(created_paths)} directories",
                details=f"Created: {', '.join(created_paths)}"
            )
        elif len(created_paths) > 0:
            return OperationResult(
                success=False,
                message=f"Partially successful: {len(created_paths)}/{len(paths)} directories created",
                details=f"Failed: {', '.join([path for path, _ in failed_paths])}",
                suggestions=[
                    "Check if the parent directories exist and are writable",
                    "Verify that the paths are valid",
                    "Try creating the failed directories manually"
                ]
            )
        else:
            return OperationResult(
                success=False,
                message="Failed to create any directories",
                details=f"All paths failed: {'; '.join([f'{path}: {error}' for path, error in failed_paths])}",
                suggestions=[
                    "Check if the paths are valid and accessible",
                    "Verify that you have write permissions to the parent directories",
                    "Try creating the directories manually",
                    "Check if the disk has sufficient space"
                ]
            )
    
    def get_common_exclusion_paths(self) -> List[str]:
        """
        Get common paths that should be excluded from Windows Security.
        
        Returns:
            List[str]: List of common exclusion paths.
        """
        user_profile = os.environ.get('USERPROFILE', '')
        documents = os.path.join(user_profile, 'Documents')
        appdata_local = os.environ.get('LOCALAPPDATA', '')
        
        return [
            os.path.join(documents, 'GreenLuma'),
            os.path.join(appdata_local, 'Programs', 'Koalageddon'),
            os.path.join(user_profile, 'Desktop', 'GreenLuma'),
        ]
    
    def get_common_admin_directories(self) -> List[str]:
        """
        Get common directories that require admin privileges to create.
        
        Returns:
            List[str]: List of common admin directories.
        """
        user_profile = os.environ.get('USERPROFILE', '')
        documents = os.path.join(user_profile, 'Documents')
        appdata_local = os.environ.get('LOCALAPPDATA', '')
        
        return [
            os.path.join(documents, 'GreenLuma'),
            os.path.join(documents, 'GreenLuma', 'AppList'),
            os.path.join(appdata_local, 'Programs'),
            os.path.join(appdata_local, 'Programs', 'Koalageddon'),
        ]