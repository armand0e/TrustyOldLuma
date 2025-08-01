"""Setup Controller module for orchestrating the entire setup process."""

import os
import sys
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional

from .ui_manager import UIManager
from .admin_handler import AdminHandler
from .file_operations import FileOperationsManager
from .download_manager import DownloadManager
from .configuration_manager import ConfigurationManager
from .embedded_koalageddon_manager import EmbeddedKoalageddonManager
from .error_handler import ErrorHandler, ErrorCategory
from .data_models import SetupConfig, OperationResult, load_default_configuration


class SetupController:
    """Main setup flow controller that coordinates all manager classes."""
    
    def __init__(self):
        """Initialize the setup controller with all manager components."""
        self.ui = UIManager()
        self.error_handler = ErrorHandler(console=self.ui.console)
        self.admin_handler = AdminHandler()
        self.file_ops = FileOperationsManager(self.ui)
        self.downloader = DownloadManager(self.ui)
        self.config_manager = ConfigurationManager(self.ui)
        self.koalageddon_manager = EmbeddedKoalageddonManager(self.ui)
        
        # Setup configuration
        self.config = load_default_configuration()
        
        # Track completed operations for rollback and summary
        self.completed_operations: List[str] = []
        self.setup_successful = False
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def graceful_shutdown():
            self.ui.display_warning("Setup interrupted by user (Ctrl+C)")
            self.ui.display_info("Performing graceful shutdown...")
            self._cleanup_on_exit()
            sys.exit(1)
            
        # Set the UI manager's interrupt handler
        self.ui.set_interrupt_handler(graceful_shutdown)
        
    def run_setup(self) -> int:
        """
        Run the complete setup process with phase-by-phase execution.
        
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Show welcome screen
            self.ui.show_welcome_screen()
            
            # Show setup options menu
            setup_choice = self._show_setup_options_menu()
            if setup_choice is None:
                self.ui.display_info("Setup cancelled by user")
                return 0
            elif setup_choice == "help":
                self.ui.show_help_text(
                    "This setup will guide you through each phase with clear prompts.\n\n"
                    "The unified setup process includes:\n"
                    "1. Prerequisites check\n"
                    "2. Administrator setup\n"
                    "3. Gaming tools extraction (GreenLuma + Koalageddon)\n"
                    "4. Platform detection and integration\n"
                    "5. Unified configuration management\n"
                    "6. Shortcut creation\n"
                    "7. Cleanup and finalization"
                )
                # Ask if user wants to continue after help
                if not self.ui.prompt_confirmation("Continue with setup?", default=True):
                    return 0
            
            # Phase 1: Prerequisites check
            self.ui.prompt_continue("Press Enter to start prerequisites check...")
            if not self.check_prerequisites():
                self.error_handler.display_critical_error(
                    "Prerequisites check failed",
                    ["Ensure all required files are present", "Check system requirements"]
                )
                return 1
            
            # Phase 2: Admin privileges and security setup
            self.ui.display_phase_transition("Prerequisites Check", "Administrator Setup")
            if not self.handle_admin_phase():
                self.error_handler.display_critical_error(
                    "Administrator setup failed",
                    ["Run the setup as Administrator", "Check UAC settings"]
                )
                return 1
            
            # Phase 3: Unified gaming tools extraction (GreenLuma + Koalageddon)
            self.ui.display_phase_transition("Administrator Setup", "Gaming Tools Extraction")
            if not self.perform_unified_extraction():
                self.error_handler.display_critical_error(
                    "Gaming tools extraction failed",
                    ["Check available disk space", "Verify file permissions", "Ensure embedded binaries are present"]
                )
                return 1
            
            # Phase 4: Platform detection and integration
            self.ui.display_phase_transition("Gaming Tools Extraction", "Platform Detection & Integration")
            if not self.perform_platform_integrations():
                self.error_handler.display_critical_error(
                    "Platform integration failed",
                    ["Check gaming platform installations", "Try running setup as Administrator", "Restart gaming platforms if running"]
                )
                return 1
            
            # Phase 5: Unified configuration management
            self.ui.display_phase_transition("Platform Detection & Integration", "Unified Configuration")
            if not self.configure_unified_applications():
                self.error_handler.display_critical_error(
                    "Unified configuration failed",
                    ["Check file permissions", "Verify configuration files", "Ensure both tools are installed"]
                )
                return 1
            
            # Phase 6: Create shortcuts
            self.ui.display_phase_transition("Unified Configuration", "Shortcut Creation")
            if not self.create_shortcuts():
                # Ask user if they want to continue without shortcuts
                continue_without_shortcuts = self.ui.prompt_confirmation(
                    "Shortcut creation failed. Continue setup without shortcuts?", 
                    default=True
                )
                if not continue_without_shortcuts:
                    return 1
                self.ui.display_warning("Continuing setup without shortcuts")
            
            # Phase 7: Cleanup and finalize
            self.ui.display_phase_transition("Shortcut Creation", "Cleanup and Finalization")
            if not self.cleanup_and_finalize():
                self.ui.display_warning("Cleanup had some issues, but setup completed")
            
            # Mark setup as successful
            self.setup_successful = True
            
            # Show completion summary
            self._show_completion_summary()
            
            return 0
            
        except KeyboardInterrupt:
            self.ui.display_warning("Setup cancelled by user")
            self._cleanup_on_exit()
            return 1
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                "Unexpected error during setup process",
                show_traceback=True
            )
            self._cleanup_on_exit()
            return 1
        
    def check_prerequisites(self) -> bool:
        """
        Check prerequisite requirements before starting setup operations.
        
        Returns:
            bool: True if all prerequisites are met, False otherwise
        """
        try:
            self.ui.display_info("Checking prerequisites...")
            
            prerequisites_met = True
            
            # Check if greenluma.zip exists
            greenluma_zip = Path("greenluma.zip")
            if not greenluma_zip.exists():
                self.error_handler.display_error(
                    self.error_handler.ErrorInfo(
                        category=ErrorCategory.FILESYSTEM,
                        message="greenluma.zip not found in current directory",
                        suggestions=[
                            "Ensure greenluma.zip is in the same folder as the setup",
                            "Download the complete setup package",
                            "Check if the file was moved or deleted"
                        ]
                    )
                )
                prerequisites_met = False
            
            # Check if Config.jsonc exists
            config_file = Path("Config.jsonc")
            if not config_file.exists():
                self.error_handler.display_error(
                    self.error_handler.ErrorInfo(
                        category=ErrorCategory.CONFIGURATION,
                        message="Config.jsonc not found in current directory",
                        suggestions=[
                            "Ensure Config.jsonc is in the same folder as the setup",
                            "Download the complete setup package",
                            "Check if the file was moved or deleted"
                        ]
                    )
                )
                prerequisites_met = False
            
            # Check available disk space (at least 500MB)
            try:
                import shutil
                free_space = shutil.disk_usage(Path.cwd()).free
                required_space = 500 * 1024 * 1024  # 500MB in bytes
                
                if free_space < required_space:
                    self.error_handler.display_error(
                        self.error_handler.ErrorInfo(
                            category=ErrorCategory.FILESYSTEM,
                            message=f"Insufficient disk space. Available: {free_space // (1024*1024)}MB, Required: 500MB",
                            suggestions=[
                                "Free up disk space",
                                "Run the setup from a drive with more space",
                                "Clean up temporary files"
                            ]
                        )
                    )
                    prerequisites_met = False
                    
            except Exception as e:
                self.ui.display_warning(f"Could not check disk space: {e}")
            
            # Check Windows version (basic check)
            if sys.platform != "win32":
                self.error_handler.display_error(
                    self.error_handler.ErrorInfo(
                        category=ErrorCategory.CONFIGURATION,
                        message="This setup is designed for Windows systems only",
                        suggestions=[
                            "Run this setup on a Windows system",
                            "Use Windows Subsystem for Linux if on Linux"
                        ]
                    )
                )
                prerequisites_met = False
            
            if prerequisites_met:
                self.ui.display_success("All prerequisites met")
                self.completed_operations.append("Prerequisites check")
                
            return prerequisites_met
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during prerequisites check")
            return False
        
    def handle_admin_phase(self) -> bool:
        """
        Handle admin privilege phase with individual command elevation.
        
        This approach runs individual admin commands with UAC prompts
        while keeping the main setup UI in the same window.
        
        Returns:
            bool: True if admin phase completed successfully, False otherwise
        """
        try:
            admin_status_messages = ["🔐 Administrator Setup", ""]
            
            # Show initial admin phase panel
            self.ui.show_admin_phase_panel(admin_status_messages)
            
            # Add security exclusions (will prompt for UAC per command)
            admin_status_messages.append("⏳ Adding Windows Security exclusions...")
            admin_status_messages.append("   (You may see UAC prompts for each exclusion)")
            self.ui.show_admin_phase_panel(admin_status_messages)
            
            exclusions_result = self.admin_handler.add_security_exclusions(self.config.required_exclusions)
            if exclusions_result.success:
                admin_status_messages.append("✅ Windows Security exclusions added")
                self.completed_operations.append("Windows Security exclusions")
            else:
                admin_status_messages.append("⚠️  Some security exclusions failed")
                self.ui.display_warning(
                    f"Security exclusions partially failed: {exclusions_result.message}"
                )
                # Continue with setup even if some exclusions failed
            
            admin_status_messages.append("⏳ Creating required directories...")
            admin_status_messages.append("   (May prompt for UAC if elevated access needed)")
            self.ui.show_admin_phase_panel(admin_status_messages)
            
            # Create admin directories (will try normal creation first, then elevation if needed)
            admin_dirs = self.admin_handler.get_common_admin_directories()
            dirs_result = self.admin_handler.create_directories_as_admin(admin_dirs)
            if dirs_result.success:
                admin_status_messages.append("✅ Required directories created")
                self.completed_operations.append("Directory structure creation")
            else:
                self.error_handler.display_error(
                    self.error_handler.ErrorInfo(
                        category=ErrorCategory.ADMIN,
                        message=dirs_result.message,
                        details=dirs_result.details,
                        suggestions=dirs_result.suggestions
                    )
                )
                return False
            
            admin_status_messages.append("✅ Administrator setup complete")
            self.ui.show_admin_phase_panel(admin_status_messages)
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during admin phase")
            return False
        
    def perform_unified_extraction(self) -> bool:
        """
        Perform unified extraction of both GreenLuma and Koalageddon with progress tracking.
        
        Returns:
            bool: True if extraction completed successfully, False otherwise
        """
        try:
            self.ui.display_info("Starting unified gaming tools extraction...")
            
            # Phase 3a: Extract GreenLuma archive
            self.ui.display_info("Extracting GreenLuma files...")
            greenluma_zip = Path("greenluma.zip")
            if not self.file_ops.extract_archive(str(greenluma_zip), str(self.config.greenluma_path)):
                return False
            
            self.completed_operations.append("GreenLuma files extracted")
            
            # Phase 3b: Install embedded Koalageddon
            self.ui.display_info("Installing embedded Koalageddon...")
            if not self.koalageddon_manager.install_koalageddon_embedded():
                self.ui.display_warning("Koalageddon installation failed, but continuing with GreenLuma setup")
                # Don't return False here - allow setup to continue with just GreenLuma
            else:
                self.completed_operations.append("Embedded Koalageddon installed")
            
            # Phase 3c: Create AppList structure for GreenLuma
            if not self.config_manager.create_applist_structure(str(self.config.greenluma_path), self.config.app_id):
                return False
            
            self.completed_operations.append("AppList structure created")
            
            # Phase 3d: Update DLLInjector.ini with correct paths
            if not self.config_manager.update_dll_injector_ini(str(self.config.greenluma_path)):
                return False
            
            self.completed_operations.append("DLLInjector.ini configured")
            
            self.ui.display_success("Unified gaming tools extraction completed successfully")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during unified extraction")
            return False
        
    def perform_platform_integrations(self) -> bool:
        """
        Detect gaming platforms and perform automatic integrations.
        
        Returns:
            bool: True if platform integration successful, False otherwise
        """
        try:
            self.ui.display_info("Starting platform detection and integration...")
            
            # Phase 4a: Detect installed gaming platforms
            detected_platforms = self.koalageddon_manager.detect_gaming_platforms()
            
            if not detected_platforms:
                self.ui.display_warning("No gaming platforms detected, skipping integrations")
                return True
            
            # Phase 4b: Perform platform integrations
            if self.koalageddon_manager.perform_platform_integrations(detected_platforms):
                platform_count = sum(detected_platforms.values())
                self.completed_operations.append(f"Platform integrations completed for {platform_count} platforms")
                self.ui.display_success("Platform detection and integration completed successfully")
                return True
            else:
                self.ui.display_warning("Platform integrations failed, but setup can continue")
                # Don't fail the entire setup if integrations fail
                return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during platform integrations")
            # Don't fail the entire setup if platform integration fails
            self.ui.display_warning("Platform integration encountered errors, but setup continues")
            return True
        
    def configure_unified_applications(self) -> bool:
        """
        Configure both GreenLuma and Koalageddon with unified settings management.
        
        Returns:
            bool: True if configuration completed successfully, False otherwise
        """
        try:
            self.ui.display_info("Configuring unified gaming applications...")
            
            # Phase 5a: Configure Koalageddon if installed
            config_source = Path("Config.jsonc")
            if config_source.exists():
                if self.koalageddon_manager.configure_koalageddon(str(config_source)):
                    self.completed_operations.append("Koalageddon configuration updated")
                else:
                    self.ui.display_warning("Koalageddon config update failed, using default")
            else:
                self.ui.display_warning("Config.jsonc not found, Koalageddon will use default settings")
            
            # Phase 5b: Validate installations
            greenluma_valid = self._validate_greenluma_installation()
            koalageddon_valid = self.koalageddon_manager.validate_installation()
            
            if greenluma_valid:
                self.completed_operations.append("GreenLuma installation validated")
            
            if koalageddon_valid:
                self.completed_operations.append("Koalageddon installation validated")
            
            # At least one tool should be working
            if greenluma_valid or koalageddon_valid:
                self.ui.display_success("Unified gaming applications configuration completed")
                return True
            else:
                self.ui.display_warning("Neither gaming tool validated successfully")
                return False
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during unified application configuration")
            return False
        
    def create_shortcuts(self) -> bool:
        """
        Create desktop shortcuts with proper error handling.
        
        Returns:
            bool: True if shortcuts created successfully, False otherwise
        """
        try:
            self.ui.display_info("Creating desktop shortcuts...")
            
            shortcuts_created = 0
            
            # Create GreenLuma shortcut
            greenluma_exe = self.config.greenluma_path / "DLLInjector.exe"
            if greenluma_exe.exists():
                if self.config_manager.create_desktop_shortcut(
                    str(greenluma_exe),
                    "GreenLuma",
                    str(self.config.greenluma_path)
                ):
                    shortcuts_created += 1
            
            # Create Koalageddon shortcut (from embedded installation)
            koalageddon_exe = self.koalageddon_manager.koalageddon_install_path / "Koalageddon.exe"
            if koalageddon_exe.exists():
                if self.config_manager.create_desktop_shortcut(
                    str(koalageddon_exe),
                    "Koalageddon",
                    str(self.koalageddon_manager.koalageddon_install_path)
                ):
                    shortcuts_created += 1
            
            # Copy Koalageddon shortcut to GreenLuma folder
            self.config_manager.copy_koalageddon_shortcut(str(self.config.greenluma_path))
            
            if shortcuts_created > 0:
                self.completed_operations.append(f"{shortcuts_created} desktop shortcuts created")
                self.ui.display_success(f"Created {shortcuts_created} desktop shortcuts")
                return True
            else:
                self.ui.display_warning("No shortcuts could be created")
                return False
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during shortcut creation")
            return False
        
    def cleanup_and_finalize(self) -> bool:
        """
        Cleanup temporary files and finalize setup process.
        
        Returns:
            bool: True if cleanup completed successfully, False otherwise
        """
        try:
            self.ui.display_info("Finalizing setup...")
            
            # Clean up any temporary files
            temp_files = [
                Path.cwd() / "koalageddon_temp.zip",
                Path.cwd() / "setup_temp",
            ]
            
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        if temp_file.is_file():
                            temp_file.unlink()
                        else:
                            import shutil
                            shutil.rmtree(temp_file)
                except Exception:
                    pass  # Don't fail setup for cleanup issues
            
            self.completed_operations.append("Temporary files cleaned up")
            
            # Validate final setup state
            validation_passed = self._validate_setup_completion()
            
            if validation_passed:
                self.ui.display_success("Setup finalization completed")
                return True
            else:
                self.ui.display_warning("Setup completed with some validation warnings")
                return True  # Don't fail for validation warnings
            
        except Exception as e:
            self.error_handler.handle_error(e, "Error during cleanup and finalization")
            return False
        
    def _validate_greenluma_installation(self) -> bool:
        """
        Validate that GreenLuma installation is complete and functional.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        try:
            if not self.config.greenluma_path.exists():
                return False
                
            required_files = ["DLLInjector.exe", "DLLInjector.ini", "GreenLuma_2020_x86.dll"]
            for file_name in required_files:
                if not (self.config.greenluma_path / file_name).exists():
                    return False
                    
            # Check AppList directory
            applist_dir = self.config.greenluma_path / "AppList"
            if not applist_dir.exists():
                return False
                
            return True
            
        except Exception:
            return False
        
    def _validate_setup_completion(self) -> bool:
        """
        Validate that the setup completed correctly.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        validation_passed = True
        
        # Check if GreenLuma directory exists and has required files
        if not self.config.greenluma_path.exists():
            self.ui.display_warning("GreenLuma directory not found")
            validation_passed = False
        else:
            required_files = ["DLLInjector.exe", "DLLInjector.ini", "GreenLuma_2020_x86.dll"]
            for file_name in required_files:
                if not (self.config.greenluma_path / file_name).exists():
                    self.ui.display_warning(f"Required file missing: {file_name}")
                    validation_passed = False
        
        # Check if Koalageddon directory exists
        if not self.config.koalageddon_config_path.exists():
            self.ui.display_warning("Koalageddon directory not found")
            validation_passed = False
        
        return validation_passed
        
    def _show_completion_summary(self) -> None:
        """Show completion summary with operation status and next steps."""
        if self.setup_successful:
            self.ui.show_completion_summary(self.completed_operations)
        else:
            # Show error summary if setup failed
            self.error_handler.display_error_summary()
            
    def _cleanup_on_exit(self) -> None:
        """Perform cleanup operations when exiting."""
        if not self.setup_successful:
            self.ui.display_info("Performing cleanup due to setup failure...")
            
            # Show what was completed before failure
            if self.completed_operations:
                self.ui.display_info("Operations completed before failure:")
                for operation in self.completed_operations:
                    self.ui.print(f"  ✅ {operation}")
            
            # Show error summary
            self.error_handler.display_error_summary()
        
        # Export error log if there were errors
        if self.error_handler.error_history:
            try:
                log_path = self.error_handler.export_error_log()
                self.ui.display_info(f"Error log exported to: {log_path}")
            except Exception:
                pass  # Don't fail cleanup for logging issues
                
    def _show_setup_options_menu(self) -> Optional[str]:
        """
        Show setup options menu with keyboard navigation.
        
        Returns:
            str: Selected option, None if cancelled
        """
        options = {
            "start": "Start setup process",
            "help": "Show detailed help and keyboard shortcuts",
            "exit": "Exit setup"
        }
        
        choice = self.ui.show_menu("Setup Options", options, allow_cancel=True)
        
        if choice == "exit" or choice is None:
            return None
        elif choice == "help":
            return "help"
        else:
            return "start"