"""
Admin Privilege Manager for the Gaming Setup Tool.

This module handles administrator privilege detection and elevation on Windows,
with graceful degradation for other platforms.
"""

import ctypes
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console

from luna.models.exceptions import GamingSetupError


class AdminPrivilegeManager:
    """Handles administrator privilege detection and elevation."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the admin privilege manager.
        
        Args:
            console: Rich console for user interaction (optional)
        """
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        self._is_windows = os.name == 'nt'
        
    @staticmethod
    def is_admin() -> bool:
        """Check if running with administrator privileges.
        
        Returns:
            True if running with admin privileges, False otherwise
        """
        if os.name == 'nt':  # Windows
            try:
                # Use Windows API to check for admin privileges
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                # If we can't determine admin status, assume we don't have it
                return False
        else:
            # On Unix-like systems, check if running as root
            return os.geteuid() == 0
    
    @staticmethod
    def elevate_privileges() -> bool:
        """Attempt to restart the application with elevated privileges.
        
        Returns:
            True if elevation was attempted, False if not possible
            
        Note:
            This method will not return if elevation is successful,
            as the current process will be replaced.
        """
        if os.name == 'nt':  # Windows
            try:
                # Get the current script path and arguments
                script_path = sys.argv[0]
                args = sys.argv[1:]
                
                # Use ShellExecuteW to restart with elevated privileges
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",  # Verb for "Run as administrator"
                    sys.executable,  # Python executable
                    f'"{script_path}" {" ".join(args)}',  # Script and arguments
                    None,  # Working directory (None = current)
                    1  # Show window
                )
                return True
            except Exception:
                return False
        else:
            # On Unix-like systems, we could use sudo, but for this gaming tool
            # it's not typically needed, so we'll just return False
            return False
    
    def ensure_admin_privileges(self) -> None:
        """Ensure admin privileges are available or handle gracefully.
        
        Raises:
            GamingSetupError: If admin privileges are required but cannot be obtained
        """
        if not self.is_admin():
            if self._is_windows:
                self._handle_windows_privilege_elevation()
            else:
                self._handle_non_windows_privileges()
    
    def _handle_windows_privilege_elevation(self) -> None:
        """Handle Windows privilege elevation process."""
        self.logger.info("Administrator privileges required for Windows operations")
        
        # Display privilege requirement message
        self.console.print("\n[yellow]⚠️  Administrator Privileges Required[/yellow]")
        self.console.print(
            "This tool needs administrator privileges to:\n"
            "• Create security exclusions in Windows Defender\n"
            "• Access system directories\n"
            "• Configure system settings\n"
        )
        
        # Prompt user for elevation
        try:
            response = self.console.input(
                "\n[cyan]Would you like to restart with administrator privileges? (y/N): [/cyan]"
            ).strip().lower()
            
            if response in ('y', 'yes'):
                self.console.print("[cyan]🔄 Restarting with administrator privileges...[/cyan]")
                
                if self.elevate_privileges():
                    # If we reach here, elevation failed
                    self.logger.error("Failed to elevate privileges")
                    raise GamingSetupError(
                        "Failed to restart with administrator privileges. "
                        "Please run the application as administrator manually."
                    )
                else:
                    raise GamingSetupError(
                        "Privilege elevation is not available on this system. "
                        "Please run the application as administrator manually."
                    )
            else:
                self.console.print("[yellow]⚠️  Continuing without administrator privileges[/yellow]")
                self.console.print(
                    "[dim]Some features may not work correctly:\n"
                    "• Windows Defender exclusions will be skipped\n"
                    "• Some file operations may fail\n"
                    "• Manual configuration may be required[/dim]\n"
                )
                
                # Ask for confirmation to continue
                confirm = self.console.input(
                    "[yellow]Continue anyway? (y/N): [/yellow]"
                ).strip().lower()
                
                if confirm not in ('y', 'yes'):
                    raise GamingSetupError("Setup cancelled by user")
                
                self.logger.warning("Continuing without administrator privileges")
                
        except KeyboardInterrupt:
            raise GamingSetupError("Setup cancelled by user")
        except EOFError:
            raise GamingSetupError("Setup cancelled - no input available")
    
    def _handle_non_windows_privileges(self) -> None:
        """Handle privilege requirements on non-Windows systems."""
        self.logger.info("Running on non-Windows system - admin privileges not required")
        
        # On non-Windows systems, most operations don't require root privileges
        # We'll just log this and continue
        self.console.print(
            "[dim]ℹ️  Running on non-Windows system. "
            "Administrator privileges are not required for most operations.[/dim]\n"
        )
    
    def check_privilege_requirements(self, operation: str) -> bool:
        """Check if admin privileges are required for a specific operation.
        
        Args:
            operation: Name of the operation to check
            
        Returns:
            True if admin privileges are required, False otherwise
        """
        # Operations that require admin privileges on Windows
        admin_required_operations = {
            'security_exclusions',
            'system_configuration',
            'registry_modifications',
            'service_management'
        }
        
        if self._is_windows and operation in admin_required_operations:
            return True
        
        return False
    
    def get_privilege_status(self) -> Tuple[bool, str]:
        """Get current privilege status and description.
        
        Returns:
            Tuple of (has_admin_privileges, status_description)
        """
        has_admin = self.is_admin()
        
        if self._is_windows:
            if has_admin:
                status = "Running with administrator privileges"
            else:
                status = "Running with standard user privileges"
        else:
            if has_admin:
                status = "Running as root user"
            else:
                status = "Running as standard user"
        
        return has_admin, status
    
    def log_privilege_status(self) -> None:
        """Log the current privilege status."""
        has_admin, status = self.get_privilege_status()
        
        if has_admin:
            self.logger.info(f"✅ {status}")
        else:
            self.logger.info(f"ℹ️  {status}")
    
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows.
        
        Returns:
            True if running on Windows, False otherwise
        """
        return self._is_windows
    
    @property
    def platform_name(self) -> str:
        """Get the platform name.
        
        Returns:
            Platform name string
        """
        if self._is_windows:
            return "Windows"
        elif sys.platform.startswith('linux'):
            return "Linux"
        elif sys.platform == 'darwin':
            return "macOS"
        else:
            return sys.platform