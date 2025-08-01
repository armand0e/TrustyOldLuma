"""
Embedded Koalageddon Manager for integrating Koalageddon DLC unlocker.

This module handles the embedded installation and configuration of Koalageddon
without requiring external downloads or user interaction, providing a seamless
one-click installation experience.
"""

import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import time

from .ui_manager import UIManager
from .error_handler import ErrorHandler, ErrorCategory


class EmbeddedKoalageddonManager:
    """Manages embedded Koalageddon installation and platform integration."""
    
    def __init__(self, ui_manager: UIManager):
        """Initialize the Embedded Koalageddon Manager.
        
        Args:
            ui_manager: UI manager instance for user feedback
        """
        self.ui = ui_manager
        self.error_handler = ErrorHandler(console=self.ui.console)
        
        # Installation paths
        self.koalageddon_install_path = Path.home() / "AppData" / "Local" / "Programs" / "Koalageddon"
        self.koalageddon_config_path = Path(os.environ.get('PROGRAMDATA', '')) / "acidicoala" / "Koalageddon"
        
        # Embedded binaries path (will be bundled in installer)
        self.embedded_binaries_path = Path("koalageddon_binaries")
        
        # Platform detection mapping
        self.platform_executables = {
            "Steam": ["steam.exe"],
            "EpicGames": ["EpicGamesLauncher.exe"],
            "Origin": ["Origin.exe"],
            "EADesktop": ["EADesktop.exe"],
            "UplayR1": ["upc.exe", "UbisoftConnect.exe"]
        }
        
    def is_koalageddon_available(self) -> bool:
        """Check if embedded Koalageddon binaries are available.
        
        Returns:
            bool: True if binaries are available, False otherwise
        """
        try:
            # Check if embedded binaries directory exists
            if not self.embedded_binaries_path.exists():
                self.ui.display_warning("Embedded Koalageddon binaries not found")
                return False
                
            # Check for required files
            required_files = [
                "Koalageddon.exe",
                "IntegrationWizard.exe", 
                "Injector.exe",
                "version.dll"
            ]
            
            for file_name in required_files:
                if not (self.embedded_binaries_path / file_name).exists():
                    self.ui.display_warning(f"Missing Koalageddon binary: {file_name}")
                    return False
                    
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error checking Koalageddon availability")
            return False
    
    def install_koalageddon_embedded(self) -> bool:
        """Install Koalageddon from embedded binaries.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            self.ui.display_info("Installing Koalageddon from embedded binaries...")
            
            if not self.is_koalageddon_available():
                return False
                
            # Create installation directory
            self.koalageddon_install_path.mkdir(parents=True, exist_ok=True)
            self.ui.display_success(f"Created Koalageddon directory: {self.koalageddon_install_path}")
            
            # Create config directory
            self.koalageddon_config_path.mkdir(parents=True, exist_ok=True)
            self.ui.display_success(f"Created config directory: {self.koalageddon_config_path}")
            
            # Copy embedded binaries to installation directory
            if not self._copy_embedded_binaries():
                return False
                
            # Create desktop shortcut
            if not self._create_koalageddon_shortcut():
                self.ui.display_warning("Failed to create Koalageddon shortcut, but installation continues")
                
            self.ui.display_success("Koalageddon installation completed successfully")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during embedded Koalageddon installation")
            return False
    
    def configure_koalageddon(self, config_source_path: str) -> bool:
        """Configure Koalageddon with provided configuration.
        
        Args:
            config_source_path: Path to the source configuration file
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            self.ui.display_info("Configuring Koalageddon...")
            
            source_config = Path(config_source_path)
            target_config = self.koalageddon_config_path / "Config.jsonc"
            
            if not source_config.exists():
                self.ui.display_error(
                    f"Source config file not found: {source_config}",
                    ["Check that Config.jsonc exists in the script directory"]
                )
                return False
            
            # Copy configuration file
            import shutil
            shutil.copy2(source_config, target_config)
            
            self.ui.display_success("Koalageddon configuration updated")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error configuring Koalageddon")
            return False
    
    def detect_gaming_platforms(self) -> Dict[str, bool]:
        """Detect installed gaming platforms.
        
        Returns:
            Dictionary mapping platform names to installation status
        """
        detected_platforms = {}
        
        try:
            self.ui.display_info("Detecting installed gaming platforms...")
            
            for platform, executables in self.platform_executables.items():
                detected = False
                
                for exe_name in executables:
                    if self._is_process_available(exe_name):
                        detected = True
                        break
                        
                detected_platforms[platform] = detected
                
                if detected:
                    self.ui.display_success(f"✓ {platform} detected")
                else:
                    self.ui.display_info(f"○ {platform} not detected")
            
            # Summary
            detected_count = sum(detected_platforms.values())
            self.ui.display_info(f"Detected {detected_count} gaming platform(s)")
            
            return detected_platforms
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error detecting gaming platforms")
            return {}
    
    def perform_platform_integrations(self, detected_platforms: Dict[str, bool]) -> bool:
        """Perform automatic platform integrations for detected platforms.
        
        Args:
            detected_platforms: Dictionary of platform detection results
            
        Returns:
            bool: True if integrations successful, False otherwise
        """
        try:
            self.ui.display_info("Performing platform integrations...")
            
            # Filter to only detected platforms
            platforms_to_integrate = [
                platform for platform, detected in detected_platforms.items() 
                if detected
            ]
            
            if not platforms_to_integrate:
                self.ui.display_warning("No gaming platforms detected, skipping integrations")
                return True
            
            integration_wizard = self.koalageddon_install_path / "IntegrationWizard.exe"
            if not integration_wizard.exists():
                self.ui.display_error(
                    "IntegrationWizard.exe not found",
                    ["Ensure Koalageddon installation completed successfully"]
                )
                return False
            
            # Perform integrations for each detected platform
            successful_integrations = 0
            
            for platform in platforms_to_integrate:
                if self._integrate_platform(platform, integration_wizard):
                    successful_integrations += 1
                    self.ui.display_success(f"✓ {platform} integration completed")
                else:
                    self.ui.display_warning(f"⚠ {platform} integration failed")
            
            if successful_integrations > 0:
                self.ui.display_success(
                    f"Completed {successful_integrations}/{len(platforms_to_integrate)} platform integrations"
                )
                return True
            else:
                self.ui.display_warning("No platform integrations were successful")
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, "Error during platform integrations")
            return False
    
    def _copy_embedded_binaries(self) -> bool:
        """Copy embedded binaries to installation directory.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import shutil
            
            # Copy all files from embedded binaries directory
            for file_path in self.embedded_binaries_path.iterdir():
                if file_path.is_file():
                    target_path = self.koalageddon_install_path / file_path.name
                    shutil.copy2(file_path, target_path)
                    self.ui.display_info(f"Copied {file_path.name}")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error copying embedded binaries")
            return False
    
    def _create_koalageddon_shortcut(self) -> bool:
        """Create desktop shortcut for Koalageddon.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from .configuration_manager import ConfigurationManager
            config_manager = ConfigurationManager(self.ui)
            
            koalageddon_exe = self.koalageddon_install_path / "Koalageddon.exe"
            if not koalageddon_exe.exists():
                return False
                
            return config_manager.create_desktop_shortcut(
                str(koalageddon_exe),
                "Koalageddon",
                str(self.koalageddon_install_path)
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error creating Koalageddon shortcut")
            return False
    
    def _is_process_available(self, process_name: str) -> bool:
        """Check if a process/executable is available on the system.
        
        Args:
            process_name: Name of the process/executable to check
            
        Returns:
            bool: True if available, False otherwise
        """
        try:
            # Check common installation directories
            common_dirs = [
                Path(os.environ.get('PROGRAMFILES', '')),
                Path(os.environ.get('PROGRAMFILES(X86)', '')),
                Path(os.environ.get('LOCALAPPDATA', '')) / "Programs",
                Path(os.environ.get('APPDATA', '')) / "Local" / "Programs"
            ]
            
            for base_dir in common_dirs:
                if not base_dir.exists():
                    continue
                    
                # Search recursively for the executable
                for exe_path in base_dir.rglob(process_name):
                    if exe_path.is_file():
                        return True
            
            # Also check if process is currently running
            try:
                result = subprocess.run(
                    ['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return process_name.lower() in result.stdout.lower()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
                
            return False
            
        except Exception:
            return False
    
    def _integrate_platform(self, platform: str, integration_wizard_path: Path) -> bool:
        """Integrate a specific platform using the Integration Wizard.
        
        Args:
            platform: Platform name to integrate
            integration_wizard_path: Path to IntegrationWizard.exe
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Run integration wizard with platform-specific parameters
            # This is a simplified version - actual implementation would need
            # to handle the Integration Wizard's command line interface
            
            cmd = [
                str(integration_wizard_path),
                "--silent",  # Assuming silent mode exists
                "--platform", platform.lower()
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(integration_wizard_path.parent)
            )
            
            if result.returncode == 0:
                return True
            else:
                self.ui.display_warning(
                    f"Integration wizard returned code {result.returncode} for {platform}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.ui.display_warning(f"Integration timeout for {platform}")
            return False
        except Exception as e:
            self.ui.display_warning(f"Integration error for {platform}: {e}")
            return False
    
    def cleanup_installation(self) -> bool:
        """Clean up temporary files from installation.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clean up any temporary files created during installation
            temp_files = [
                self.koalageddon_install_path / "temp",
                self.koalageddon_config_path / "temp"
            ]
            
            for temp_path in temp_files:
                if temp_path.exists():
                    if temp_path.is_dir():
                        import shutil
                        shutil.rmtree(temp_path)
                    else:
                        temp_path.unlink()
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during cleanup")
            return False
    
    def validate_installation(self) -> bool:
        """Validate that Koalageddon installation is complete and functional.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        try:
            validation_passed = True
            
            # Check installation directory exists and has required files
            if not self.koalageddon_install_path.exists():
                self.ui.display_warning("Koalageddon installation directory not found")
                validation_passed = False
            else:
                required_files = ["Koalageddon.exe", "IntegrationWizard.exe"]
                for file_name in required_files:
                    if not (self.koalageddon_install_path / file_name).exists():
                        self.ui.display_warning(f"Required Koalageddon file missing: {file_name}")
                        validation_passed = False
            
            # Check configuration directory
            if not self.koalageddon_config_path.exists():
                self.ui.display_warning("Koalageddon configuration directory not found")
                validation_passed = False
            else:
                config_file = self.koalageddon_config_path / "Config.jsonc"
                if not config_file.exists():
                    self.ui.display_warning("Koalageddon configuration file missing")
                    validation_passed = False
            
            if validation_passed:
                self.ui.display_success("Koalageddon installation validation passed")
            
            return validation_passed
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during installation validation")
            return False