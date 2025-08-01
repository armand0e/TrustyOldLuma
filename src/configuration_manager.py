"""
Configuration Manager for application setup operations.

This module handles:
- Koalageddon configuration file updates with JSON parsing and writing
- DLLInjector.ini path configuration methods with proper string replacement
- Desktop shortcut creation using Windows COM objects and VBScript generation
- AppList folder and file creation with proper App ID handling
"""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import re

from .ui_manager import UIManager


class ConfigurationManager:
    """Manages unified application configuration operations for both GreenLuma and Koalageddon."""
    
    def __init__(self, ui_manager: UIManager):
        """Initialize the Configuration Manager.
        
        Args:
            ui_manager: UI manager instance for user feedback
        """
        self.ui = ui_manager
        self.default_app_id = "252950"  # Default Steam App ID
        
        # Configuration paths for unified management
        self.unified_config_cache = {}  # Cache for parsed configurations
    
    def update_koalageddon_config(self, source_config_path: str, target_config_dir: str) -> bool:
        """Update Koalageddon configuration file with repository version.
        
        Args:
            source_config_path: Path to the source Config.jsonc file
            target_config_dir: Directory where Koalageddon config should be placed
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source_path = Path(source_config_path)
            target_dir = Path(target_config_dir)
            target_file = target_dir / "Config.jsonc"
            
            if not source_path.exists():
                self.ui.display_error(
                    f"Source config file not found: {source_path}",
                    ["Check that Config.jsonc exists in the script directory"]
                )
                return False
            
            if not target_dir.exists():
                self.ui.display_warning(
                    f"Koalageddon config directory not found: {target_dir}"
                )
                return False
            
            # Attempt to copy with retry logic for file in use scenarios
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Small delay to handle file locks
                    if attempt > 0:
                        import time
                        time.sleep(0.5)
                    
                    # Copy the configuration file
                    import shutil
                    shutil.copy2(source_path, target_file)
                    
                    self.ui.display_success(
                        f"Replaced Koalageddon config with repository version"
                    )
                    return True
                    
                except (PermissionError, OSError) as e:
                    if attempt == max_attempts - 1:
                        self.ui.display_warning(
                            f"Could not replace Koalageddon config file: {e}"
                        )
                        return False
                    continue
            
            return False
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to update Koalageddon config: {e}",
                ["Check file permissions", "Ensure Koalageddon is not running"]
            )
            return False
    
    def update_dll_injector_ini(self, greenluma_path: str) -> bool:
        """Update DLLInjector.ini with the correct DLL path.
        
        Args:
            greenluma_path: Path to the GreenLuma directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            greenluma_dir = Path(greenluma_path)
            ini_file = greenluma_dir / "DLLInjector.ini"
            dll_file = greenluma_dir / "GreenLuma_2020_x86.dll"
            
            if not dll_file.exists():
                self.ui.display_warning(
                    f"GreenLuma DLL not found at {dll_file}"
                )
                return False
            
            if not ini_file.exists():
                self.ui.display_error(
                    f"DLLInjector.ini not found at {ini_file}",
                    ["Check that GreenLuma files were extracted correctly"]
                )
                return False
            
            # Read the current content
            content = ini_file.read_text(encoding='utf-8')
            
            # Replace the DLL path using regex (same pattern as batch script)
            dll_path_str = str(dll_file).replace('\\', '\\\\')  # Escape backslashes for regex replacement
            new_content = re.sub(
                r'(?m)^Dll = ".*"',
                f'Dll = "{dll_path_str}"',
                content
            )
            
            # Write back the updated content
            ini_file.write_text(new_content, encoding='utf-8')
            
            self.ui.display_success(
                f"Updated DLLInjector.ini with path: {dll_file}"
            )
            return True
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to update DLLInjector.ini: {e}",
                ["Check file permissions", "Ensure the file is not in use"]
            )
            return False
    
    def create_desktop_shortcut(self, target_path: str, shortcut_name: str, 
                              working_dir: str, icon_path: Optional[str] = None) -> bool:
        """Create a desktop shortcut using VBScript generation.
        
        Args:
            target_path: Path to the executable to launch
            shortcut_name: Name of the shortcut (without .lnk extension)
            working_dir: Working directory for the shortcut
            icon_path: Optional path to icon file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find desktop directory (handle OneDrive desktop)
            desktop_path = self._get_desktop_path()
            if not desktop_path:
                self.ui.display_warning(
                    "Could not find desktop directory, skipping shortcut creation"
                )
                return False
            
            shortcut_file = desktop_path / f"{shortcut_name}.lnk"
            
            # Create VBScript content
            vbs_content = self._generate_vbscript(
                str(shortcut_file), target_path, working_dir, icon_path
            )
            
            # Write VBScript to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as vbs_file:
                vbs_file.write(vbs_content)
                vbs_temp_path = vbs_file.name
            
            try:
                # Execute VBScript
                result = subprocess.run(
                    ['cscript', '//nologo', vbs_temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.ui.display_success(
                        f"Created {shortcut_name} desktop shortcut"
                    )
                    return True
                else:
                    self.ui.display_error(
                        f"Failed to create desktop shortcut: {result.stderr}",
                        ["Check that cscript is available", "Verify file permissions"]
                    )
                    return False
                    
            finally:
                # Clean up temporary VBScript file
                try:
                    os.unlink(vbs_temp_path)
                except OSError:
                    pass
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to create desktop shortcut: {e}",
                ["Check desktop permissions", "Ensure target executable exists"]
            )
            return False
    
    def copy_koalageddon_shortcut(self, greenluma_path: str) -> bool:
        """Copy Koalageddon shortcut from desktop to GreenLuma folder.
        
        Args:
            greenluma_path: Path to the GreenLuma directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            desktop_path = self._get_desktop_path()
            if not desktop_path:
                return False
            
            source_shortcut = desktop_path / "Koalageddon.lnk"
            target_shortcut = Path(greenluma_path) / "Koalageddon.lnk"
            
            if not source_shortcut.exists():
                self.ui.display_warning(
                    "Koalageddon desktop shortcut not found, skipping copy"
                )
                return False
            
            import shutil
            shutil.copy2(source_shortcut, target_shortcut)
            
            self.ui.display_success(
                "Copied Koalageddon shortcut to GreenLuma folder"
            )
            return True
            
        except Exception as e:
            self.ui.display_warning(
                f"Could not copy Koalageddon shortcut: {e}"
            )
            return False
    
    def create_applist_structure(self, greenluma_path: str, app_id: Optional[str] = None) -> bool:
        """Create AppList folder and initial file with App ID.
        
        Args:
            greenluma_path: Path to the GreenLuma directory
            app_id: Steam App ID to use (defaults to 252950)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            applist_dir = Path(greenluma_path) / "AppList"
            app_id = app_id or self.default_app_id
            
            # Create AppList directory
            applist_dir.mkdir(exist_ok=True)
            self.ui.display_success("Created AppList folder")
            
            # Create initial app list file
            applist_file = applist_dir / "0.txt"
            applist_file.write_text(f"{app_id}\n", encoding='utf-8')
            
            self.ui.display_success(
                f"Created initial AppList file with App ID: {app_id}"
            )
            return True
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to create AppList structure: {e}",
                ["Check directory permissions", "Ensure GreenLuma path exists"]
            )
            return False
    
    def _get_desktop_path(self) -> Optional[Path]:
        """Get the desktop directory path, handling OneDrive desktop.
        
        Returns:
            Path to desktop directory or None if not found
        """
        # Try standard desktop first
        desktop_path = Path.home() / "Desktop"
        if desktop_path.exists():
            return desktop_path
        
        # Try OneDrive desktop
        onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
        if onedrive_desktop.exists():
            return onedrive_desktop
        
        return None
    
    def _generate_vbscript(self, shortcut_file: str, target_path: str, 
                          working_dir: str, icon_path: Optional[str] = None) -> str:
        """Generate VBScript content for shortcut creation.
        
        Args:
            shortcut_file: Full path to the shortcut file to create
            target_path: Path to the target executable
            working_dir: Working directory for the shortcut
            icon_path: Optional path to icon file
            
        Returns:
            VBScript content as string
        """
        vbs_lines = [
            'Set oWS = WScript.CreateObject("WScript.Shell")',
            f'sLinkFile = "{shortcut_file}"',
            'Set oLink = oWS.CreateShortcut(sLinkFile)',
            f'oLink.TargetPath = "{target_path}"',
            f'oLink.WorkingDirectory = "{working_dir}"'
        ]
        
        if icon_path:
            vbs_lines.append(f'oLink.IconLocation = "{icon_path}"')
        
        vbs_lines.append('oLink.Save')
        
        return '\n'.join(vbs_lines)
    
    def load_unified_configuration(self, config_path: str) -> Optional[Dict]:
        """Load and parse unified configuration file with caching.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Parsed configuration dictionary or None if failed
        """
        try:
            config_file = Path(config_path)
            
            # Check cache first
            if str(config_file) in self.unified_config_cache:
                return self.unified_config_cache[str(config_file)]
                
            if not config_file.exists():
                self.ui.display_warning(f"Configuration file not found: {config_file}")
                return None
                
            # Parse JSONC (JSON with comments)
            content = config_file.read_text(encoding='utf-8')
            
            # Remove comments for JSON parsing (simple approach)
            lines = []
            for line in content.split('\n'):
                # Remove line comments
                if '//' in line:
                    line = line.split('//')[0]
                lines.append(line)
            
            cleaned_content = '\n'.join(lines)
            config_data = json.loads(cleaned_content)
            
            # Cache the result
            self.unified_config_cache[str(config_file)] = config_data
            
            return config_data
            
        except json.JSONDecodeError as e:
            self.ui.display_error(
                f"Invalid JSON in configuration file: {e}",
                ["Check configuration file syntax", "Verify JSON format"]
            )
            return None
        except Exception as e:
            self.ui.display_error(
                f"Failed to load configuration: {e}",
                ["Check file permissions", "Verify file exists"]
            )
            return None
    
    def validate_unified_setup(self, greenluma_path: str, koalageddon_path: str) -> Dict[str, bool]:
        """Validate unified setup configuration for both tools.
        
        Args:
            greenluma_path: Path to GreenLuma installation
            koalageddon_path: Path to Koalageddon installation
            
        Returns:
            Dictionary with validation results for each component
        """
        results = {
            "greenluma_installed": False,
            "koalageddon_installed": False,
            "greenluma_configured": False,
            "koalageddon_configured": False,
            "shortcuts_created": False
        }
        
        try:
            # Validate GreenLuma installation
            greenluma_dir = Path(greenluma_path)
            if greenluma_dir.exists():
                required_files = ["DLLInjector.exe", "DLLInjector.ini", "GreenLuma_2020_x86.dll"]
                if all((greenluma_dir / f).exists() for f in required_files):
                    results["greenluma_installed"] = True
                    
                    # Check if configured (AppList exists)
                    if (greenluma_dir / "AppList").exists():
                        results["greenluma_configured"] = True
            
            # Validate Koalageddon installation
            koalageddon_dir = Path(koalageddon_path)
            if koalageddon_dir.exists():
                if (koalageddon_dir / "Koalageddon.exe").exists():
                    results["koalageddon_installed"] = True
                    
                    # Check if configured (config file exists)
                    config_path = Path(os.environ.get('PROGRAMDATA', '')) / "acidicoala" / "Koalageddon" / "Config.jsonc"
                    if config_path.exists():
                        results["koalageddon_configured"] = True
            
            # Check for desktop shortcuts
            desktop_path = self._get_desktop_path()
            if desktop_path:
                shortcuts = ["GreenLuma.lnk", "Koalageddon.lnk"]
                if any((desktop_path / shortcut).exists() for shortcut in shortcuts):
                    results["shortcuts_created"] = True
            
            return results
            
        except Exception as e:
            self.ui.display_error(f"Error during unified validation: {e}")
            return results
    
    def create_unified_shortcuts(self, greenluma_path: str, koalageddon_path: str) -> int:
        """Create desktop shortcuts for both gaming tools.
        
        Args:
            greenluma_path: Path to GreenLuma installation
            koalageddon_path: Path to Koalageddon installation
            
        Returns:
            Number of shortcuts successfully created
        """
        shortcuts_created = 0
        
        try:
            # Create GreenLuma shortcut
            greenluma_exe = Path(greenluma_path) / "DLLInjector.exe"
            if greenluma_exe.exists():
                if self.create_desktop_shortcut(
                    str(greenluma_exe),
                    "GreenLuma",
                    str(greenluma_path)
                ):
                    shortcuts_created += 1
                    self.ui.display_success("Created GreenLuma shortcut")
            
            # Create Koalageddon shortcut
            koalageddon_exe = Path(koalageddon_path) / "Koalageddon.exe"
            if koalageddon_exe.exists():
                if self.create_desktop_shortcut(
                    str(koalageddon_exe),
                    "Koalageddon",
                    str(koalageddon_path)
                ):
                    shortcuts_created += 1
                    self.ui.display_success("Created Koalageddon shortcut")
            
            return shortcuts_created
            
        except Exception as e:
            self.ui.display_error(f"Error creating unified shortcuts: {e}")
            return shortcuts_created
    
    def export_unified_summary(self, output_path: str, validation_results: Dict[str, bool]) -> bool:
        """Export a summary of the unified installation.
        
        Args:
            output_path: Path to save the summary file
            validation_results: Results from validate_unified_setup
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            summary_data = {
                "installation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "TrustyOldLuma Unified v1.0",
                "components": {
                    "GreenLuma": {
                        "installed": validation_results.get("greenluma_installed", False),
                        "configured": validation_results.get("greenluma_configured", False)
                    },
                    "Koalageddon": {
                        "installed": validation_results.get("koalageddon_installed", False),
                        "configured": validation_results.get("koalageddon_configured", False)
                    }
                },
                "shortcuts_created": validation_results.get("shortcuts_created", False)
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            self.ui.display_success(f"Installation summary exported to: {output_file}")
            return True
            
        except Exception as e:
            self.ui.display_error(f"Failed to export installation summary: {e}")
            return False