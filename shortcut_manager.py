"""
Shortcut manager for the Gaming Setup Tool.

This module provides functionality for creating desktop shortcuts
with custom icons and cross-platform support.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from rich.console import Console

from display_managers import ProgressDisplayManager, ErrorDisplayManager
from models import LunaShortcutConfig, LunaResults


class ShortcutManager:
    """Manages desktop shortcut creation with platform-specific implementations."""
    
    def __init__(self, console: Console):
        """Initialize the shortcut manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.progress_manager = ProgressDisplayManager(console)
        self.error_manager = ErrorDisplayManager(console)
    
    async def create_shortcuts(self, shortcuts: List[LunaShortcutConfig], 
                             results: Optional[LunaResults] = None) -> List[bool]:
        """Create desktop shortcuts with custom icons.
        
        Args:
            shortcuts: List of shortcut configurations
            results: Optional setup results to update
            
        Returns:
            List of booleans indicating success/failure for each shortcut
        """
        if not shortcuts:
            return []
            
        with self.progress_manager.create_progress_bar(
            "Creating desktop shortcuts...", 
            total=len(shortcuts)
        ) as progress:
            
            success_results = []
            
            for shortcut in shortcuts:
                try:
                    # Validate target path exists
                    if not shortcut.target_path.exists():
                        error_msg = f"Target path does not exist: {shortcut.target_path}"
                        if results:
                            results.add_error(error_msg)
                        self.error_manager.display_error(
                            FileNotFoundError(error_msg),
                            f"Creating shortcut for {shortcut.name}",
                            "Ensure the target application is installed correctly"
                        )
                        success_results.append(False)
                        progress.update(1, f"Failed: {shortcut.name} (target not found)")
                        continue
                    
                    # Create platform-specific shortcut
                    if os.name == 'nt':  # Windows
                        success = await self._create_windows_shortcut(shortcut)
                    else:  # Unix-like systems
                        success = await self._create_unix_shortcut(shortcut)
                    
                    success_results.append(success)
                    
                    if success:
                        progress.update(1, f"Created shortcut: {shortcut.name}")
                        if results:
                            results.shortcuts_created.append((shortcut.name, True))
                    else:
                        progress.update(1, f"Failed to create shortcut: {shortcut.name}")
                        if results:
                            results.shortcuts_created.append((shortcut.name, False))
                    
                    # Small delay for visual feedback
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    error_msg = f"Failed to create shortcut {shortcut.name}: {str(e)}"
                    if results:
                        results.add_error(error_msg)
                        results.shortcuts_created.append((shortcut.name, False))
                    self.error_manager.display_error(e, f"Creating shortcut for {shortcut.name}")
                    success_results.append(False)
                    progress.update(1)
            
            return success_results
    
    async def _create_windows_shortcut(self, config: LunaShortcutConfig) -> bool:
        """Create Windows .lnk shortcut file using COM interface.
        
        Args:
            config: Shortcut configuration
            
        Returns:
            True if shortcut creation was successful, False otherwise
        """
        try:
            # Import Windows-specific modules
            import pythoncom
            from win32com.client import Dispatch
            
            pythoncom.CoInitialize()
            
            # Create shell object
            shell = Dispatch("WScript.Shell")
            
            # Create shortcut object
            desktop_path = config.desktop_path
            shortcut = shell.CreateShortcut(str(desktop_path))
            
            # Set shortcut properties
            shortcut.TargetPath = str(config.target_path)
            shortcut.WorkingDirectory = str(config.working_directory)
            
            if config.description:
                shortcut.Description = config.description
                
            if config.arguments:
                shortcut.Arguments = config.arguments
                
            if config.icon_path and config.icon_path.exists():
                shortcut.IconLocation = str(config.icon_path)
            
            # Save the shortcut
            shortcut.Save()
            
            # Verify shortcut was created
            if desktop_path.exists():
                return True
            return False
            
        except ImportError:
            # Handle missing Windows COM libraries
            self.error_manager.display_warning(
                "Windows COM libraries not available. Using alternative method.",
                "Install pywin32 for better shortcut creation support."
            )
            return await self._create_windows_shortcut_alternative(config)
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                f"Creating Windows shortcut for {config.name}",
                "Check permissions or try running as administrator"
            )
            return False
            
        finally:
            # Clean up COM objects
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    async def _create_windows_shortcut_alternative(self, config: LunaShortcutConfig) -> bool:
        """Alternative method to create Windows shortcuts using VBScript.
        
        Args:
            config: Shortcut configuration
            
        Returns:
            True if shortcut creation was successful, False otherwise
        """
        try:
            # Create temporary VBScript file
            with tempfile.NamedTemporaryFile(suffix='.vbs', delete=False, mode='w') as vbs_file:
                vbs_path = Path(vbs_file.name)
                
                # Write VBScript to create shortcut
                vbs_script = f"""
                Set oWS = WScript.CreateObject("WScript.Shell")
                sLinkFile = "{config.desktop_path}"
                Set oLink = oWS.CreateShortcut(sLinkFile)
                oLink.TargetPath = "{config.target_path}"
                oLink.WorkingDirectory = "{config.working_directory}"
                """
                
                if config.description:
                    vbs_script += f'oLink.Description = "{config.description}"\n'
                    
                if config.arguments:
                    vbs_script += f'oLink.Arguments = "{config.arguments}"\n'
                    
                if config.icon_path and config.icon_path.exists():
                    vbs_script += f'oLink.IconLocation = "{config.icon_path}"\n'
                    
                vbs_script += "oLink.Save"
                
                vbs_file.write(vbs_script)
            
            # Execute VBScript
            process = await asyncio.create_subprocess_exec(
                'cscript', 
                str(vbs_path), 
                '/nologo',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            # Clean up temporary file
            try:
                vbs_path.unlink()
            except:
                pass
            
            # Verify shortcut was created
            if config.desktop_path.exists():
                return True
            return False
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                f"Creating Windows shortcut (alternative method) for {config.name}"
            )
            return False
    
    async def _create_unix_shortcut(self, config: LunaShortcutConfig) -> bool:
        """Create Unix desktop entry file.
        
        Args:
            config: Shortcut configuration
            
        Returns:
            True if shortcut creation was successful, False otherwise
        """
        try:
            # Create desktop entry file
            desktop_path = config.desktop_path
            
            # Ensure desktop directory exists
            desktop_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create desktop entry content
            desktop_entry = [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={config.name}",
                f"Exec={config.target_path} {config.arguments or ''}",
                f"Path={config.working_directory}",
                "Terminal=false",
            ]
            
            if config.description:
                desktop_entry.append(f"Comment={config.description}")
                
            if config.icon_path and config.icon_path.exists():
                desktop_entry.append(f"Icon={config.icon_path}")
            
            # Write desktop entry file
            with open(desktop_path, 'w') as file:
                file.write('\n'.join(desktop_entry))
            
            # Make executable
            desktop_path.chmod(desktop_path.stat().st_mode | 0o755)
            
            return True
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                f"Creating Unix desktop shortcut for {config.name}"
            )
            return False
    
    async def validate_shortcut(self, shortcut_path: Path) -> bool:
        """Validate that a shortcut exists and points to the correct target.
        
        Args:
            shortcut_path: Path to the shortcut file
            
        Returns:
            True if shortcut is valid, False otherwise
        """
        if not shortcut_path.exists():
            return False
            
        try:
            if os.name == 'nt':  # Windows
                # Import Windows-specific modules
                try:
                    import pythoncom
                    from win32com.client import Dispatch
                    
                    pythoncom.CoInitialize()
                    
                    # Open shortcut
                    shell = Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortcut(str(shortcut_path))
                    
                    # Check if target exists
                    target_path = Path(shortcut.TargetPath)
                    return target_path.exists()
                    
                except ImportError:
                    # Can't validate without COM libraries
                    return shortcut_path.exists()
                    
                finally:
                    try:
                        pythoncom.CoUninitialize()
                    except:
                        pass
                        
            else:  # Unix-like systems
                # Check if desktop entry file exists and is executable
                return shortcut_path.exists() and os.access(shortcut_path, os.X_OK)
                
        except Exception:
            return False