"""
Shortcut manager for the Luna Gaming Tool.

This module provides functionality for creating Luna-branded desktop shortcuts
with custom icons and cross-platform support, as well as migrating legacy shortcuts.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from rich.console import Console

from luna.managers.display_managers import ProgressDisplayManager, ErrorDisplayManager
from luna.models.models import LunaShortcutConfig, LunaResults

# Type checking imports
if TYPE_CHECKING:
    from luna.models.models import LunaConfig


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
        """Create Luna-branded desktop shortcuts with custom icons.
        
        Args:
            shortcuts: List of Luna shortcut configurations
            results: Optional Luna setup results to update
            
        Returns:
            List of booleans indicating success/failure for each shortcut
        """
        if not shortcuts:
            return []
            
        with self.progress_manager.create_progress_bar(
            "Creating Luna desktop shortcuts...", 
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
                            f"Creating Luna shortcut for {shortcut.display_name}",
                            "Ensure the Luna component is installed correctly"
                        )
                        success_results.append(False)
                        progress.update(1, f"Failed: {shortcut.display_name} (target not found)")
                        continue
                    
                    # Create platform-specific Luna shortcut
                    if os.name == 'nt':  # Windows
                        success = await self._create_windows_shortcut(shortcut)
                    else:  # Unix-like systems
                        success = await self._create_unix_shortcut(shortcut)
                    
                    success_results.append(success)
                    
                    if success:
                        progress.update(1, f"Created Luna shortcut: {shortcut.display_name}")
                        if results:
                            results.shortcuts_created.append((shortcut.display_name, True))
                    else:
                        progress.update(1, f"Failed to create Luna shortcut: {shortcut.display_name}")
                        if results:
                            results.shortcuts_created.append((shortcut.display_name, False))
                    
                    # Small delay for visual feedback
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    error_msg = f"Failed to create Luna shortcut {shortcut.display_name}: {str(e)}"
                    if results:
                        results.add_error(error_msg)
                        results.shortcuts_created.append((shortcut.display_name, False))
                    self.error_manager.display_error(e, f"Creating Luna shortcut for {shortcut.display_name}")
                    success_results.append(False)
                    progress.update(1)
            
            return success_results
    
    async def _create_windows_shortcut(self, config: LunaShortcutConfig) -> bool:
        """Create Windows .lnk shortcut file using COM interface with Luna branding.
        
        Args:
            config: Luna shortcut configuration
            
        Returns:
            True if Luna shortcut creation was successful, False otherwise
        """
        try:
            # Import Windows-specific modules
            import pythoncom
            from win32com.client import Dispatch
            
            pythoncom.CoInitialize()
            
            # Create shell object
            shell = Dispatch("WScript.Shell")
            
            # Create Luna shortcut object
            desktop_path = config.desktop_path
            shortcut = shell.CreateShortcut(str(desktop_path))
            
            # Set Luna shortcut properties
            shortcut.TargetPath = str(config.target_path)
            shortcut.WorkingDirectory = str(config.working_directory)
            
            # Use Luna-branded description
            shortcut.Description = config.luna_description
                
            if config.arguments:
                shortcut.Arguments = config.arguments
                
            if config.icon_path and config.icon_path.exists():
                shortcut.IconLocation = str(config.icon_path)
            
            # Save the Luna shortcut
            shortcut.Save()
            
            # Verify Luna shortcut was created
            if desktop_path.exists():
                return True
            return False
            
        except ImportError:
            # Handle missing Windows COM libraries
            self.error_manager.display_warning(
                "Windows COM libraries not available. Using alternative method for Luna shortcut.",
                "Install pywin32 for better Luna shortcut creation support."
            )
            return await self._create_windows_shortcut_alternative(config)
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                f"Creating Windows Luna shortcut for {config.display_name}",
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
        """Alternative method to create Windows shortcuts using VBScript with Luna branding.
        
        Args:
            config: Luna shortcut configuration
            
        Returns:
            True if Luna shortcut creation was successful, False otherwise
        """
        try:
            # Create temporary VBScript file
            with tempfile.NamedTemporaryFile(suffix='.vbs', delete=False, mode='w') as vbs_file:
                vbs_path = Path(vbs_file.name)
                
                # Write VBScript to create Luna shortcut
                vbs_script = f"""
                Set oWS = WScript.CreateObject("WScript.Shell")
                sLinkFile = "{config.desktop_path}"
                Set oLink = oWS.CreateShortcut(sLinkFile)
                oLink.TargetPath = "{config.target_path}"
                oLink.WorkingDirectory = "{config.working_directory}"
                """
                
                # Use Luna-branded description
                vbs_script += f'oLink.Description = "{config.luna_description}"\n'
                    
                if config.arguments:
                    vbs_script += f'oLink.Arguments = "{config.arguments}"\n'
                    
                if config.icon_path and config.icon_path.exists():
                    vbs_script += f'oLink.IconLocation = "{config.icon_path}"\n'
                    
                vbs_script += "oLink.Save"
                
                vbs_file.write(vbs_script)
            
            # Execute VBScript to create Luna shortcut
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
            
            # Verify Luna shortcut was created
            if config.desktop_path.exists():
                return True
            return False
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                f"Creating Windows Luna shortcut (alternative method) for {config.display_name}"
            )
            return False
    
    async def _create_unix_shortcut(self, config: LunaShortcutConfig) -> bool:
        """Create Unix desktop entry file with Luna branding.
        
        Args:
            config: Luna shortcut configuration
            
        Returns:
            True if Luna shortcut creation was successful, False otherwise
        """
        try:
            # Create Luna desktop entry file
            desktop_path = config.desktop_path
            
            # Ensure desktop directory exists
            desktop_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create Luna desktop entry content
            desktop_entry = [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={config.display_name}",
                f"Exec={config.target_path} {config.arguments or ''}",
                f"Path={config.working_directory}",
                "Terminal=false",
            ]
            
            # Use Luna-branded description
            desktop_entry.append(f"Comment={config.luna_description}")
                
            if config.icon_path and config.icon_path.exists():
                desktop_entry.append(f"Icon={config.icon_path}")
            
            # Write Luna desktop entry file
            with open(desktop_path, 'w') as file:
                file.write('\n'.join(desktop_entry))
            
            # Make executable
            desktop_path.chmod(desktop_path.stat().st_mode | 0o755)
            
            return True
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                f"Creating Unix Luna desktop shortcut for {config.display_name}"
            )
            return False
    
    async def validate_shortcut(self, shortcut_path: Path) -> bool:
        """Validate that a Luna shortcut exists and points to the correct target.
        
        Args:
            shortcut_path: Path to the Luna shortcut file
            
        Returns:
            True if Luna shortcut is valid, False otherwise
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
                    
                    # Open Luna shortcut
                    shell = Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortcut(str(shortcut_path))
                    
                    # Check if Luna target exists
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
                # Check if Luna desktop entry file exists and is executable
                return shortcut_path.exists() and os.access(shortcut_path, os.X_OK)
                
        except Exception:
            return False
            
    async def detect_legacy_shortcuts(self, legacy_patterns: List[str] = None) -> List[Path]:
        """Detect legacy GreenLuma and Koalageddon shortcuts on the desktop.
        
        Args:
            legacy_patterns: List of patterns to match legacy shortcuts (defaults to common patterns)
            
        Returns:
            List of paths to detected legacy shortcuts
        """
        if legacy_patterns is None:
            legacy_patterns = [
                "GreenLuma*", 
                "Koalageddon*", 
                "DLLInjector*", 
                "AppList*",
                "Gaming Setup Tool*"
            ]
            
        desktop_path = Path.home() / "Desktop"
        legacy_shortcuts = []
        
        try:
            # Get extension based on platform
            extension = ".lnk" if os.name == 'nt' else ".desktop"
            
            # Search for legacy shortcuts
            for pattern in legacy_patterns:
                if os.name == 'nt':
                    # Windows: Use glob to find matching shortcuts
                    for shortcut in desktop_path.glob(f"{pattern}{extension}"):
                        legacy_shortcuts.append(shortcut)
                else:
                    # Unix: Check .desktop files for matching names
                    for shortcut in desktop_path.glob(f"*{extension}"):
                        try:
                            with open(shortcut, 'r') as f:
                                content = f.read()
                                # Check if the desktop entry contains the legacy pattern
                                if any(pattern.replace('*', '') in line for line in content.splitlines() if line.startswith("Name=")):
                                    legacy_shortcuts.append(shortcut)
                        except:
                            pass
                            
            return legacy_shortcuts
            
        except Exception as e:
            self.error_manager.display_error(
                e,
                "Detecting legacy shortcuts",
                "Legacy shortcuts will not be migrated automatically"
            )
            return []
            
    async def update_legacy_shortcuts(self, 
                                    legacy_shortcuts: List[Path], 
                                    luna_config: 'LunaConfig',
                                    results: Optional[LunaResults] = None) -> List[bool]:
        """Update legacy shortcuts to point to Luna components.
        
        Args:
            legacy_shortcuts: List of paths to legacy shortcuts
            luna_config: Luna configuration with paths to Luna components
            results: Optional Luna setup results to update
            
        Returns:
            List of booleans indicating success/failure for each shortcut update
        """
        if not legacy_shortcuts:
            return []
            
        with self.progress_manager.create_progress_bar(
            "Migrating legacy shortcuts to Luna...", 
            total=len(legacy_shortcuts)
        ) as progress:
            
            success_results = []
            
            # Create backup directory
            backup_dir = luna_config.temp_dir / "shortcut_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            for shortcut_path in legacy_shortcuts:
                try:
                    # Create backup of legacy shortcut
                    backup_path = backup_dir / shortcut_path.name
                    
                    try:
                        import shutil
                        shutil.copy2(shortcut_path, backup_path)
                    except Exception as e:
                        self.error_manager.display_warning(
                            f"Failed to backup shortcut {shortcut_path.name}: {str(e)}",
                            "Proceeding without backup"
                        )
                    
                    # Get shortcut info
                    shortcut_info = await self._get_shortcut_info(shortcut_path)
                    
                    if not shortcut_info:
                        progress.update(1, f"Failed to read legacy shortcut: {shortcut_path.name}")
                        success_results.append(False)
                        if results:
                            results.luna_shortcuts_updated.append((shortcut_path.name, False))
                        continue
                    
                    # Determine Luna component based on legacy shortcut
                    component, luna_target = self._map_legacy_to_luna_component(shortcut_info, luna_config)
                    
                    if not luna_target or not luna_target.exists():
                        progress.update(1, f"No matching Luna component for: {shortcut_path.name}")
                        success_results.append(False)
                        if results:
                            results.luna_shortcuts_updated.append((shortcut_path.name, False))
                        continue
                    
                    # Create Luna shortcut config
                    luna_shortcut = LunaShortcutConfig(
                        name=self._get_luna_name_from_legacy(shortcut_path.name),
                        component=component,
                        target_path=luna_target,
                        working_directory=luna_target.parent,
                        icon_path=shortcut_info.get('icon_path'),
                        arguments=shortcut_info.get('arguments'),
                        luna_branding=True
                    )
                    
                    # Delete legacy shortcut
                    try:
                        shortcut_path.unlink()
                    except Exception as e:
                        self.error_manager.display_warning(
                            f"Failed to remove legacy shortcut {shortcut_path.name}: {str(e)}",
                            "Will attempt to overwrite instead"
                        )
                    
                    # Create Luna shortcut
                    if os.name == 'nt':  # Windows
                        success = await self._create_windows_shortcut(luna_shortcut)
                    else:  # Unix-like systems
                        success = await self._create_unix_shortcut(luna_shortcut)
                    
                    success_results.append(success)
                    
                    if success:
                        progress.update(1, f"Migrated: {shortcut_path.name} → {luna_shortcut.display_name}")
                        if results:
                            results.luna_shortcuts_updated.append((luna_shortcut.display_name, True))
                    else:
                        progress.update(1, f"Failed to migrate: {shortcut_path.name}")
                        if results:
                            results.luna_shortcuts_updated.append((shortcut_path.name, False))
                    
                    # Small delay for visual feedback
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    error_msg = f"Failed to migrate shortcut {shortcut_path.name}: {str(e)}"
                    if results:
                        results.add_error(error_msg)
                        results.luna_shortcuts_updated.append((shortcut_path.name, False))
                    self.error_manager.display_error(e, f"Migrating legacy shortcut {shortcut_path.name}")
                    success_results.append(False)
                    progress.update(1)
            
            return success_results
            
    async def _get_shortcut_info(self, shortcut_path: Path) -> Dict[str, Any]:
        """Get information about a shortcut file.
        
        Args:
            shortcut_path: Path to the shortcut file
            
        Returns:
            Dictionary with shortcut information or empty dict if failed
        """
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
                    
                    # Extract shortcut info
                    info = {
                        'target_path': Path(shortcut.TargetPath),
                        'working_directory': Path(shortcut.WorkingDirectory) if shortcut.WorkingDirectory else None,
                        'description': shortcut.Description,
                        'arguments': shortcut.Arguments,
                        'icon_path': Path(shortcut.IconLocation.split(',')[0]) if shortcut.IconLocation else None
                    }
                    
                    return info
                    
                except ImportError:
                    # Can't read without COM libraries
                    return {'target_path': None, 'name': shortcut_path.stem}
                    
                finally:
                    try:
                        pythoncom.CoUninitialize()
                    except:
                        pass
                        
            else:  # Unix-like systems
                # Read desktop entry file
                info = {'name': shortcut_path.stem, 'target_path': None}
                
                try:
                    with open(shortcut_path, 'r') as f:
                        for line in f:
                            if line.startswith('Exec='):
                                parts = line[5:].strip().split()
                                if parts:
                                    info['target_path'] = Path(parts[0])
                                    if len(parts) > 1:
                                        info['arguments'] = ' '.join(parts[1:])
                            elif line.startswith('Path='):
                                info['working_directory'] = Path(line[5:].strip())
                            elif line.startswith('Comment='):
                                info['description'] = line[8:].strip()
                            elif line.startswith('Icon='):
                                info['icon_path'] = Path(line[5:].strip())
                            elif line.startswith('Name='):
                                info['name'] = line[5:].strip()
                except:
                    pass
                
                return info
                
        except Exception:
            return {}
            
    def _map_legacy_to_luna_component(self, shortcut_info: Dict[str, Any], luna_config: 'LunaConfig') -> Tuple[str, Optional[Path]]:
        """Map legacy shortcut to Luna component.
        
        Args:
            shortcut_info: Dictionary with legacy shortcut information
            luna_config: Luna configuration with paths to Luna components
            
        Returns:
            Tuple of (component_type, target_path) or (None, None) if no match
        """
        target_path = shortcut_info.get('target_path')
        if not target_path:
            return None, None
            
        target_name = target_path.name.lower()
        description = (shortcut_info.get('description') or '').lower()
        name = (shortcut_info.get('name') or '').lower()
        
        # Map to Luna injector
        if any(x in target_name for x in ['greenluma', 'dllinjector', 'injector']):
            return 'injector', luna_config.luna_core_path / "core" / "injector" / "luna_injector.exe"
            
        # Map to Luna settings
        if any(x in target_name for x in ['settings', 'config']):
            return 'settings', luna_config.luna_core_path / "core" / "injector" / "luna_settings.exe"
            
        # Map to Luna unlocker
        if any(x in target_name for x in ['koalageddon', 'unlocker', 'unlock']):
            return 'unlocker', luna_config.luna_core_path / "core" / "unlocker" / "luna_unlocker.dll"
            
        # Map to Luna wizard
        if any(x in target_name for x in ['wizard', 'setup']):
            return 'wizard', luna_config.luna_core_path / "core" / "unlocker" / "luna_wizard.exe"
            
        # Check description and name for hints
        if description or name:
            text = f"{description} {name}".lower()
            
            if any(x in text for x in ['greenluma', 'injector', 'dll']):
                return 'injector', luna_config.luna_core_path / "core" / "injector" / "luna_injector.exe"
                
            if any(x in text for x in ['koalageddon', 'unlocker', 'dlc']):
                return 'unlocker', luna_config.luna_core_path / "core" / "unlocker" / "luna_unlocker.dll"
                
            if any(x in text for x in ['settings', 'config']):
                return 'settings', luna_config.luna_core_path / "core" / "injector" / "luna_settings.exe"
                
            if any(x in text for x in ['wizard', 'setup']):
                return 'wizard', luna_config.luna_core_path / "core" / "unlocker" / "luna_wizard.exe"
        
        # Default to Luna manager
        return 'manager', luna_config.luna_core_path / "luna-gui.exe"
            
    def _get_luna_name_from_legacy(self, legacy_name: str) -> str:
        """Convert legacy shortcut name to Luna-compatible name.
        
        Args:
            legacy_name: Legacy shortcut name
            
        Returns:
            Luna-compatible name
        """
        # Remove extension
        name = Path(legacy_name).stem
        
        # Remove common prefixes
        for prefix in ['GreenLuma', 'Koalageddon', 'DLLInjector', 'Gaming Setup Tool']:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                
        # Clean up remaining text
        name = name.strip(' -_')
        
        # Map common names
        name_map = {
            '': 'Manager',
            'settings': 'Settings',
            'config': 'Settings',
            'injector': 'Injector',
            'unlocker': 'Unlocker',
            'wizard': 'Wizard',
            'setup': 'Setup',
            'dlc': 'DLC Unlocker',
            'applist': 'App Manager'
        }
        
        # Check for exact matches in name map
        if name.lower() in name_map:
            return name_map[name.lower()]
            
        # Check for partial matches
        for key, value in name_map.items():
            if key and key in name.lower():
                return value
                
        # If no match, use the cleaned name or default to "Manager"
        return name if name else "Manager"