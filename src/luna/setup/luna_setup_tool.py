#!/usr/bin/env python3
"""
Luna Setup Tool - Unified gaming tool combining injection and DLC unlocking.

This tool sets up Luna (unified GreenLuma and Koalageddon) with a rich text interface,
progress indicators, comprehensive error handling, and legacy migration support.
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, Type

from rich.console import Console
from rich.logging import RichHandler

from luna.models.exceptions import (
    GamingSetupError, 
    NetworkError, 
    ConfigurationError,
    AdminPrivilegeError,
    FileOperationError,
    SecurityConfigError,
    PlatformNotSupportedError,
    WindowsSpecificError,
    DownloadError,
    ConnectionTimeoutError
)
from luna.core.config import APP_NAME, LOG_FORMAT, LOG_DATE_FORMAT
from luna.managers.display_managers import (
    ProgressDisplayManager,
    ErrorDisplayManager,
    WelcomeScreenManager,
    CompletionScreenManager
)
from luna.models.models import LunaConfig, LunaResults, LunaShortcutConfig
from luna.managers.admin_manager import AdminPrivilegeManager
from luna.managers.file_operations_manager import FileOperationsManager
from luna.managers.security_config_manager import SecurityConfigManager
from luna.setup.configuration_handler import ConfigurationHandler
from luna.managers.shortcut_manager import ShortcutManager
from luna.managers.applist_manager import AppListManager
from luna.managers.cleanup_manager import CleanupManager
from luna.managers.error_manager import ErrorManager, RetryManager, PlatformFeatureContext, with_retry


class LunaSetupTool:
    """Main Luna application controller orchestrating the unified setup process."""
    
    def __init__(self, verbose: bool = False, quiet: bool = False, dry_run: bool = False,
                 config_only: bool = False, skip_admin: bool = False, skip_security: bool = False,
                 no_cleanup: bool = False, force: bool = False, timeout: int = 300,
                 luna_core_path: Optional[Path] = None, legacy_greenluma_path: Optional[Path] = None,
                 legacy_koalageddon_path: Optional[Path] = None, app_id: str = "480", 
                 download_url: Optional[str] = None):
        """Initialize the Luna setup tool.
        
        Args:
            verbose: Enable verbose logging mode
            quiet: Suppress non-essential output
            dry_run: Show what would be done without making changes
            config_only: Only update configuration files
            skip_admin: Skip administrator privilege checks
            skip_security: Skip Windows Defender exclusion setup
            no_cleanup: Skip cleanup of temporary files
            force: Force setup even if files already exist
            timeout: Network timeout in seconds
            luna_core_path: Custom path for Luna core installation
            legacy_greenluma_path: Path to existing GreenLuma installation for migration
            legacy_koalageddon_path: Path to existing Koalageddon installation for migration
            app_id: Steam App ID for Luna AppList
            download_url: Custom download URL for Luna installer
        """
        self.console = Console()
        self.verbose = verbose
        self.quiet = quiet
        self.dry_run = dry_run
        self.config_only = config_only
        self.skip_admin = skip_admin
        self.skip_security = skip_security
        self.no_cleanup = no_cleanup
        self.force = force
        self.timeout = timeout
        self.custom_luna_core_path = luna_core_path
        self.legacy_greenluma_path = legacy_greenluma_path
        self.legacy_koalageddon_path = legacy_koalageddon_path
        self.custom_app_id = app_id
        self.custom_download_url = download_url
        
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize display managers
        self.progress_manager = ProgressDisplayManager(self.console)
        self.error_display_manager = ErrorDisplayManager(self.console)
        self.welcome_manager = WelcomeScreenManager(self.console)
        self.completion_manager = CompletionScreenManager(self.console)
        
        # Initialize error handling system
        self.error_manager = ErrorManager(self.console)
        self.retry_manager = RetryManager(self.console)
        
        # Initialize managers and handlers
        self.admin_manager = AdminPrivilegeManager(self.console)
        self.file_manager = FileOperationsManager(self.console)
        self.security_manager = SecurityConfigManager(self.console)
        self.config_handler = ConfigurationHandler(self.console)
        self.shortcut_manager = ShortcutManager(self.console)
        self.applist_manager = AppListManager(self.console)
        self.cleanup_manager = CleanupManager(self.console)
        
        # Setup Luna configuration and results
        self.config = None
        self.results = LunaResults()
        
    def _setup_logging(self) -> None:
        """Configure logging with Rich handler."""
        # Set logging level based on flags
        if self.quiet:
            log_level = logging.WARNING
        elif self.verbose:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
            handlers=[RichHandler(console=self.console, rich_tracebacks=True)]
        )
        
        # Reduce noise from external libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        
    async def run(self) -> None:
        """Main entry point for the setup process."""
        try:
            self.logger.info("Starting Luna Setup Tool")
            self.results.start_time = time.time()
            
            # Display welcome screen
            self.welcome_manager.display_welcome()
            
            # Check and handle admin privileges (unless skipped)
            if not self.skip_admin:
                self.admin_manager.log_privilege_status()
                if not self.dry_run:
                    self.admin_manager.ensure_admin_privileges()
                else:
                    self.logger.info("DRY RUN: Would check admin privileges")
            else:
                self.logger.warning("Skipping admin privilege checks (may cause setup failures)")
            
            # Initialize configuration
            await self._initialize_configuration()
            
            # Execute setup workflow
            await self._execute_setup_workflow()
            
            # Record completion time
            self.results.end_time = time.time()
            
            # Show completion screen
            self.completion_manager.display_completion(self.results)
            
        except KeyboardInterrupt:
            self.logger.info("Setup cancelled by user")
            self.console.print("\n[yellow]Setup cancelled by user[/yellow]")
            sys.exit(1)
        except GamingSetupError as e:
            # Use our error categorization system
            category = self.error_manager.categorize_error(e)
            solution = self.error_manager.get_solution(e)
            
            # Log with appropriate level based on category
            self.logger.error(f"Setup error ({category.value}): {e}")
            
            # Display error with category-appropriate styling
            self.error_manager.display_error(e, "Setup process")
            
            # Exit with appropriate code based on error category
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error during setup: {e}", exc_info=True)
            self.error_manager.display_error(e, "Main setup process")
            sys.exit(1)
    
    async def _initialize_configuration(self) -> None:
        """Initialize and validate Luna configuration."""
        try:
            with self.progress_manager.show_spinner("Initializing Luna configuration..."):
                # Create Luna configuration from environment with custom overrides
                if self.legacy_greenluma_path or self.legacy_koalageddon_path:
                    # Use legacy migration configuration
                    self.config = LunaConfig.from_legacy_configs(
                        greenluma_path=self.legacy_greenluma_path,
                        koalageddon_path=self.legacy_koalageddon_path,
                        verbose_logging=self.verbose,
                        app_id=self.custom_app_id,
                        download_url=self.custom_download_url,
                        timeout=self.timeout
                    )
                else:
                    # Use standard Luna configuration
                    self.config = LunaConfig.from_environment(
                        verbose_logging=self.verbose,
                        luna_core_path=self.custom_luna_core_path,
                        app_id=self.custom_app_id,
                        download_url=self.custom_download_url,
                        timeout=self.timeout
                    )
                
                # Resolve any relative paths
                self.config.resolve_relative_paths()
                
                self.logger.info("Luna configuration initialized successfully")
                self.logger.debug(f"Luna core path: {self.config.luna_core_path}")
                self.logger.debug(f"Luna config path: {self.config.luna_config_path}")
                self.logger.debug(f"Legacy GreenLuma path: {self.config.legacy_greenluma_path}")
                self.logger.debug(f"Legacy Koalageddon path: {self.config.legacy_koalageddon_path}")
                self.logger.debug(f"Download URL: {self.config.download_url}")
                self.logger.debug(f"App ID: {self.config.app_id}")
                self.logger.debug(f"Timeout: {self.config.timeout}")
                
                if self.dry_run:
                    self.logger.info("DRY RUN MODE: No actual changes will be made")
                if self.config_only:
                    self.logger.info("CONFIG ONLY MODE: Skipping downloads and installations")
                    
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Luna configuration: {str(e)}")
    
    async def _execute_setup_workflow(self) -> None:
        """Execute the main Luna setup workflow with proper error handling and cleanup."""
        # Use installation context for automatic cleanup on failure
        async with self.cleanup_manager.installation_context(self.results):
            # Register temp directory for cleanup
            self.cleanup_manager.register_temp_directory(self.config.temp_dir, "luna_setup_workflow")
            
            # Detect and migrate legacy installations if present
            await self._detect_legacy_installations()
            
            # Create required Luna directories
            await self._create_directories()
            
            # Add Luna security exclusions
            await self._configure_security_exclusions()
            
            # Migrate legacy configurations and files
            await self._migrate_legacy_configurations()
            await self._migrate_legacy_files()
            
            # Extract Luna injector files
            await self._extract_luna_injector()
            
            # Verify antivirus didn't remove files
            await self._verify_antivirus_protection()
            
            # Update Luna injector configuration
            await self._update_luna_injector_config()
            
            # Setup AppList folder and configuration
            await self._setup_applist()
            
            # Download and install Luna unlocker
            await self._download_luna_unlocker()
            
            # Update Luna unlocker configuration
            await self._update_luna_unlocker_config()
            
            # Create Luna desktop shortcuts
            await self._create_shortcuts()
            
            # Update legacy shortcuts to Luna
            await self._update_legacy_shortcuts()
            
            # Clean up temporary files
            await self._cleanup_temp_files()
    
    async def _create_directories(self) -> None:
        """Create required directories for the setup."""
        self.logger.info("Creating required directories")
        
        # List of Luna directories to create
        directories = [
            self.config.luna_core_path,
            self.config.luna_config_path,
            self.config.temp_dir
        ]
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would create directories:")
            for directory in directories:
                self.logger.info(f"  - {directory}")
            return
        
        # Create directories with progress tracking
        await self.file_manager.create_directories(directories, self.results)
        
        # Register created directories with cleanup manager for potential rollback
        for directory in directories:
            if directory.exists():
                self.cleanup_manager.register_created_directory(directory, "directory_creation")
    
    async def _configure_security_exclusions(self) -> None:
        """Configure Windows Defender security exclusions."""
        if self.skip_security:
            self.logger.info("Skipping security exclusions (--skip-security flag)")
            return
            
        self.logger.info("Configuring security exclusions")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would configure Windows Defender exclusions")
            return
        
        # Get Luna paths that need security exclusions
        exclusion_paths = self.config.get_luna_security_exclusion_paths()
        
        # Use platform feature context for Windows-specific operation
        with PlatformFeatureContext(
            self.error_manager, 
            "windows_defender", 
            "configuring security exclusions",
            fallback_func=lambda: self.results.add_warning(
                "Windows Defender exclusions are not available on this platform. "
                "You may need to manually configure your antivirus software."
            )
        ) as feature_available:
            if feature_available:
                # Add security exclusions with progress tracking
                await self.security_manager.add_defender_exclusions(exclusion_paths, self.results)
            else:
                self.logger.info("Skipping Windows Defender exclusions on non-Windows platform")
    
    async def _extract_luna_injector(self) -> None:
        """Extract Luna injector files from archive."""
        if self.config_only:
            self.logger.info("Skipping Luna injector extraction (--config-only mode)")
            return
            
        self.logger.info("Extracting Luna injector files")
        
        # Path to Luna injector archive (legacy GreenLuma archive)
        luna_injector_archive = Path("assets/greenluma.zip")
        
        if not luna_injector_archive.exists():
            error_msg = f"Luna injector archive not found at {luna_injector_archive}"
            self.results.add_luna_error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would extract {luna_injector_archive} to {self.config.luna_core_path}/injector")
            return
        
        # Create injector subdirectory within Luna core
        injector_path = self.config.luna_core_path / "injector"
        injector_path.mkdir(parents=True, exist_ok=True)
        
        # Mark extraction as attempted for success rate calculation
        self.results.mark_luna_extraction_attempted()
        
        # Extract archive with flattened structure
        success = await self.file_manager.extract_archive(
            luna_injector_archive,
            injector_path,
            flatten=True,
            results=self.results
        )
        
        if success:
            self.results.files_extracted = True
            self.results.luna_components_installed.append(("Luna Injector", True))
        else:
            self.results.luna_components_installed.append(("Luna Injector", False))
            raise GamingSetupError("Failed to extract Luna injector files")
    
    async def _verify_antivirus_protection(self) -> None:
        """Verify that antivirus didn't remove any Luna files after extraction."""
        self.logger.info("Verifying Luna antivirus protection")
        
        # Check if Luna injector files are intact
        injector_path = self.config.luna_core_path / "injector"
        await self.security_manager.verify_antivirus_protection(
            injector_path,
            self.results
        )
    
    async def _update_luna_injector_config(self) -> None:
        """Update Luna injector configuration files."""
        self.logger.info("Updating Luna injector configuration")
        
        # Path to Luna injector configuration
        injector_path = self.config.luna_core_path / "injector"
        config_path = injector_path / "DLLInjector.ini"
        
        # Path to Luna DLL file (use x64 by default)
        dll_path = injector_path / "GreenLuma_2020_x64.dll"
        
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would update {config_path} with Luna DLL path {dll_path}")
            return
        
        # Mark injector configuration as attempted
        self.results.mark_luna_injector_attempted()
        
        # Update Luna injector configuration
        success = await self.config_handler.update_dll_injector_config(
            dll_path,
            config_path,
            self.results
        )
        
        if success:
            self.results.luna_injector_configured = True
            self.results.configs_updated.append(("Luna Injector Config", True))
        else:
            self.results.configs_updated.append(("Luna Injector Config", False))
            self.results.add_luna_warning("Failed to update Luna injector configuration")
    
    async def _setup_applist(self) -> None:
        """Setup Luna AppList folder and initial configuration."""
        self.logger.info("Setting up Luna AppList folder and configuration")
        
        # Setup Luna AppList with the configured App ID
        injector_path = self.config.luna_core_path / "injector"
        success = await self.applist_manager.setup_applist(
            injector_path,
            self.config.app_id,
            self.results
        )
        
        if success:
            self.results.configs_updated.append(("Luna AppList Config", True))
        else:
            self.results.configs_updated.append(("Luna AppList Config", False))
            self.results.add_luna_warning("Failed to setup Luna AppList configuration")
    
    async def _download_luna_unlocker(self) -> None:
        """Download and install Luna unlocker."""
        if self.config_only:
            self.logger.info("Skipping Luna unlocker download (--config-only mode)")
            return
            
        self.logger.info("Downloading Luna unlocker")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would download Luna unlocker installer")
            return
        
        # Download Luna unlocker installer
        luna_unlocker_installer = self.config.temp_dir / "LunaUnlocker.exe"
        
        success = await self.file_manager.download_file(
            self.config.download_url,
            self.config.temp_dir,
            filename="LunaUnlocker.exe",
            results=self.results
        )
        
        if success:
            self.results.files_downloaded.append(("Luna Unlocker", True))
            self.results.luna_components_installed.append(("Luna Unlocker", True))
        else:
            self.results.files_downloaded.append(("Luna Unlocker", False))
            self.results.luna_components_installed.append(("Luna Unlocker", False))
            raise NetworkError("Failed to download Luna unlocker installer")
        
        # TODO: Implement installer execution in a future task
        # For now, just log that we would run the installer
        self.logger.info("Luna unlocker installer downloaded successfully")
        self.logger.info("Luna unlocker installer execution will be implemented in a future task")
    
    async def _update_luna_unlocker_config(self) -> None:
        """Update Luna unlocker configuration files."""
        self.logger.info("Updating Luna unlocker configuration")
        
        # Check if we have a custom Luna unlocker config to use
        custom_config = Path("assets/luna_unlocker_config.json")
        legacy_config = Path("assets/koalageddon_config.json")  # Fallback to legacy config
        
        # Mark unlocker configuration as attempted
        self.results.mark_luna_unlocker_attempted()
        
        # Path to Luna unlocker configuration
        unlocker_config_path = self.config.luna_core_path / "unlocker" / "config.json"
        
        if custom_config.exists():
            # Replace Luna unlocker config with custom version
            success = await self.config_handler.replace_koalageddon_config(
                custom_config,
                unlocker_config_path,
                self.results
            )
        elif legacy_config.exists():
            # Use legacy Koalageddon config as fallback
            success = await self.config_handler.replace_koalageddon_config(
                legacy_config,
                unlocker_config_path,
                self.results
            )
        else:
            self.logger.info("No custom Luna unlocker config found, skipping configuration update")
            success = True  # Not an error if no custom config exists
        
        if success:
            self.results.luna_unlocker_configured = True
            self.results.configs_updated.append(("Luna Unlocker Config", True))
        else:
            self.results.configs_updated.append(("Luna Unlocker Config", False))
            self.results.add_luna_warning("Failed to update Luna unlocker configuration")
    
    async def _create_shortcuts(self) -> None:
        """Create desktop shortcuts for Luna components."""
        self.logger.info("Creating Luna desktop shortcuts")
        
        # Define Luna shortcuts to create
        injector_path = self.config.luna_core_path / "injector"
        unlocker_path = self.config.luna_core_path / "unlocker"
        
        shortcuts = [
            LunaShortcutConfig(
                name="Injector",
                component="injector",
                target_path=injector_path / "DLLInjector.exe",
                working_directory=injector_path,
                icon_path=injector_path / "DLLInjector.exe",
                description="Luna DLL Injector"
            ),
            LunaShortcutConfig(
                name="Unlocker",
                component="unlocker",
                target_path=unlocker_path / "Koalageddon.exe",
                working_directory=unlocker_path,
                description="Luna DLC Unlocker"
            ),
            LunaShortcutConfig(
                name="Manager",
                component="manager",
                target_path=self.config.luna_core_path / "luna.exe",
                working_directory=self.config.luna_core_path,
                description="Luna Gaming Tool Manager"
            )
        ]
        
        # Use platform feature context for Luna shortcut creation
        system = platform.system().lower()
        if system == "windows":
            feature_name = "windows_shortcuts"
        elif system == "linux":
            feature_name = "linux_desktop_entries"
        elif system == "darwin":  # macOS
            feature_name = "macos_aliases"
        else:
            feature_name = "unknown_platform_shortcuts"
            
        with PlatformFeatureContext(
            self.error_manager,
            feature_name,
            "creating Luna desktop shortcuts",
            fallback_func=lambda: self.results.add_luna_warning(
                f"Luna desktop shortcut creation is not fully supported on {system.capitalize()}. "
                "You may need to create Luna shortcuts manually."
            )
        ) as feature_available:
            if feature_available:
                # Create Luna shortcuts with progress tracking
                await self.shortcut_manager.create_shortcuts(shortcuts, self.results)
            else:
                self.logger.info(f"Skipping Luna shortcut creation on {system} platform")
    
    async def _cleanup_temp_files(self) -> None:
        """Clean up temporary files after setup using the comprehensive cleanup manager."""
        if self.no_cleanup:
            self.logger.info("Skipping cleanup (--no-cleanup flag)")
            return
            
        if self.dry_run:
            self.logger.info("DRY RUN: Would clean up temporary files")
            return
            
        self.logger.info("Cleaning up temporary files")
        
        # Register specific temporary files for cleanup
        koalageddon_installer = self.config.temp_dir / "Koalageddon.exe"
        if koalageddon_installer.exists():
            self.cleanup_manager.register_temp_file(koalageddon_installer, "koalageddon_download")
        
        # Perform comprehensive cleanup of temporary files
        temp_file_results = await self.cleanup_manager.cleanup_temp_files()
        
        # Perform cleanup of temporary directories
        temp_dir_results = await self.cleanup_manager.cleanup_temp_directories()
        
        # Validate cleanup operations
        temp_files_valid = await self.cleanup_manager.validate_cleanup(temp_file_results)
        temp_dirs_valid = await self.cleanup_manager.validate_cleanup(temp_dir_results)
        
        # Log cleanup results
        if temp_file_results.operations_attempted > 0:
            success_rate = temp_file_results.success_rate * 100
            self.logger.info(
                f"Temporary file cleanup: {temp_file_results.operations_successful}/"
                f"{temp_file_results.operations_attempted} operations successful "
                f"({success_rate:.1f}%)"
            )
            
            # Add any cleanup errors to results
            for error in temp_file_results.errors:
                self.results.add_warning(f"Cleanup error: {error}")
        
        if temp_dir_results.operations_attempted > 0:
            success_rate = temp_dir_results.success_rate * 100
            self.logger.info(
                f"Temporary directory cleanup: {temp_dir_results.operations_successful}/"
                f"{temp_dir_results.operations_attempted} operations successful "
                f"({success_rate:.1f}%)"
            )
            
            # Add any cleanup errors to results
            for error in temp_dir_results.errors:
                self.results.add_warning(f"Cleanup error: {error}")
        
        # Report validation results
        if not temp_files_valid or not temp_dirs_valid:
            self.results.add_luna_warning("Some cleanup operations may not have completed successfully")
        else:
            self.logger.info("All cleanup operations validated successfully")
    
    async def _detect_legacy_installations(self) -> None:
        """Detect existing GreenLuma and Koalageddon installations for migration."""
        self.logger.info("Detecting legacy installations")
        
        # Common installation paths to check
        documents_path = Path.home() / "Documents"
        common_paths = [
            documents_path / "GreenLuma",
            documents_path / "Koalageddon",
            Path("C:/GreenLuma"),
            Path("C:/Koalageddon"),
            Path("C:/Program Files/GreenLuma"),
            Path("C:/Program Files/Koalageddon"),
            Path("C:/Program Files (x86)/GreenLuma"),
            Path("C:/Program Files (x86)/Koalageddon")
        ]
        
        # Check for GreenLuma installations
        for path in common_paths:
            if path.name == "GreenLuma" and path.exists():
                # Look for GreenLuma-specific files
                if (path / "DLLInjector.exe").exists() or (path / "GreenLuma_2020_x64.dll").exists():
                    self.logger.info(f"Found GreenLuma installation at: {path}")
                    self.results.legacy_installations_found.append(f"GreenLuma: {path}")
                    if self.config.legacy_greenluma_path is None:
                        self.config.legacy_greenluma_path = path
        
        # Check for Koalageddon installations
        for path in common_paths:
            if path.name == "Koalageddon" and path.exists():
                # Look for Koalageddon-specific files
                if (path / "Koalageddon.exe").exists() or (path / "config.json").exists():
                    self.logger.info(f"Found Koalageddon installation at: {path}")
                    self.results.legacy_installations_found.append(f"Koalageddon: {path}")
                    if self.config.legacy_koalageddon_path is None:
                        self.config.legacy_koalageddon_path = path
        
        if self.results.legacy_installations_found:
            self.logger.info(f"Found {len(self.results.legacy_installations_found)} legacy installations")
        else:
            self.logger.info("No legacy installations detected")
    
    async def _migrate_legacy_configurations(self) -> None:
        """Convert old GreenLuma and Koalageddon configurations to Luna format."""
        self.logger.info("Migrating legacy configurations")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would migrate legacy configurations")
            return
        
        # Migrate GreenLuma configuration
        if self.config.legacy_greenluma_path and self.config.legacy_greenluma_path.exists():
            success = await self._migrate_greenluma_config()
            self.results.configurations_migrated.append(("GreenLuma Config", success))
        
        # Migrate Koalageddon configuration
        if self.config.legacy_koalageddon_path and self.config.legacy_koalageddon_path.exists():
            success = await self._migrate_koalageddon_config()
            self.results.configurations_migrated.append(("Koalageddon Config", success))
        
        # Create unified Luna configuration
        await self._create_unified_luna_config()
    
    async def _migrate_greenluma_config(self) -> bool:
        """Migrate GreenLuma configuration to Luna format."""
        try:
            self.logger.info("Migrating GreenLuma configuration")
            
            # Source configuration files
            dll_injector_ini = self.config.legacy_greenluma_path / "DLLInjector.ini"
            applist_folder = self.config.legacy_greenluma_path / "AppList"
            
            # Target Luna injector configuration
            luna_injector_path = self.config.luna_core_path / "injector"
            luna_injector_path.mkdir(parents=True, exist_ok=True)
            
            # Copy DLLInjector.ini if it exists
            if dll_injector_ini.exists():
                target_ini = luna_injector_path / "DLLInjector.ini"
                await self.file_manager.copy_file(dll_injector_ini, target_ini)
                self.logger.info("Migrated DLLInjector.ini to Luna")
            
            # Copy AppList folder if it exists
            if applist_folder.exists():
                target_applist = luna_injector_path / "AppList"
                await self.file_manager.copy_directory(applist_folder, target_applist)
                self.logger.info("Migrated AppList folder to Luna")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate GreenLuma configuration: {e}")
            self.results.add_luna_error(f"GreenLuma config migration failed: {e}")
            return False
    
    async def _migrate_koalageddon_config(self) -> bool:
        """Migrate Koalageddon configuration to Luna format."""
        try:
            self.logger.info("Migrating Koalageddon configuration")
            
            # Source configuration files
            koala_config = self.config.legacy_koalageddon_path / "config.json"
            
            # Target Luna unlocker configuration
            luna_unlocker_path = self.config.luna_core_path / "unlocker"
            luna_unlocker_path.mkdir(parents=True, exist_ok=True)
            
            # Copy config.json if it exists
            if koala_config.exists():
                target_config = luna_unlocker_path / "config.json"
                await self.file_manager.copy_file(koala_config, target_config)
                self.logger.info("Migrated Koalageddon config.json to Luna")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate Koalageddon configuration: {e}")
            self.results.add_luna_error(f"Koalageddon config migration failed: {e}")
            return False
    
    async def _create_unified_luna_config(self) -> None:
        """Create unified Luna configuration file."""
        try:
            self.logger.info("Creating unified Luna configuration")
            
            # Create Luna configuration directory
            self.config.luna_config_path.mkdir(parents=True, exist_ok=True)
            
            # Create unified configuration
            luna_config = {
                "luna": {
                    "version": "1.0.0",
                    "core": {
                        "injector_enabled": True,
                        "unlocker_enabled": True,
                        "auto_start": False,
                        "stealth_mode": True
                    },
                    "paths": {
                        "core_directory": str(self.config.luna_core_path),
                        "config_directory": str(self.config.luna_config_path),
                        "temp_directory": str(self.config.temp_dir)
                    },
                    "migration": {
                        "legacy_greenluma_path": str(self.config.legacy_greenluma_path) if self.config.legacy_greenluma_path else None,
                        "legacy_koalageddon_path": str(self.config.legacy_koalageddon_path) if self.config.legacy_koalageddon_path else None,
                        "migration_completed": True
                    }
                }
            }
            
            # Write unified configuration
            config_file = self.config.luna_config_path / "luna_config.json"
            import json
            with open(config_file, 'w') as f:
                json.dump(luna_config, f, indent=2)
            
            self.logger.info("Created unified Luna configuration")
            self.results.configs_updated.append(("Unified Luna Config", True))
            
        except Exception as e:
            self.logger.error(f"Failed to create unified Luna configuration: {e}")
            self.results.add_luna_error(f"Unified config creation failed: {e}")
            self.results.configs_updated.append(("Unified Luna Config", False))
    
    async def _migrate_legacy_files(self) -> None:
        """Move or copy existing GreenLuma and Koalageddon files to Luna structure."""
        self.logger.info("Migrating legacy files")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would migrate legacy files")
            return
        
        # Migrate GreenLuma files
        if self.config.legacy_greenluma_path and self.config.legacy_greenluma_path.exists():
            await self._migrate_greenluma_files()
        
        # Migrate Koalageddon files
        if self.config.legacy_koalageddon_path and self.config.legacy_koalageddon_path.exists():
            await self._migrate_koalageddon_files()
    
    async def _migrate_greenluma_files(self) -> None:
        """Migrate GreenLuma executable files to Luna injector directory."""
        try:
            self.logger.info("Migrating GreenLuma files")
            
            source_path = self.config.legacy_greenluma_path
            target_path = self.config.luna_core_path / "injector"
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Files to migrate
            files_to_migrate = [
                "DLLInjector.exe",
                "GreenLuma_2020_x64.dll",
                "GreenLuma_2020_x86.dll",
                "GreenLumaSettings_2023.exe"
            ]
            
            for filename in files_to_migrate:
                source_file = source_path / filename
                if source_file.exists():
                    target_file = target_path / filename
                    await self.file_manager.copy_file(source_file, target_file)
                    self.logger.info(f"Migrated {filename} to Luna injector")
            
            self.results.luna_components_installed.append(("Legacy GreenLuma Files", True))
            
        except Exception as e:
            self.logger.error(f"Failed to migrate GreenLuma files: {e}")
            self.results.add_luna_error(f"GreenLuma file migration failed: {e}")
            self.results.luna_components_installed.append(("Legacy GreenLuma Files", False))
    
    async def _migrate_koalageddon_files(self) -> None:
        """Migrate Koalageddon executable files to Luna unlocker directory."""
        try:
            self.logger.info("Migrating Koalageddon files")
            
            source_path = self.config.legacy_koalageddon_path
            target_path = self.config.luna_core_path / "unlocker"
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Files to migrate
            files_to_migrate = [
                "Koalageddon.exe",
                "Koalageddon.dll",
                "IntegrationWizard.exe",
                "CommonLibrary.dll"
            ]
            
            for filename in files_to_migrate:
                source_file = source_path / filename
                if source_file.exists():
                    target_file = target_path / filename
                    await self.file_manager.copy_file(source_file, target_file)
                    self.logger.info(f"Migrated {filename} to Luna unlocker")
            
            self.results.luna_components_installed.append(("Legacy Koalageddon Files", True))
            
        except Exception as e:
            self.logger.error(f"Failed to migrate Koalageddon files: {e}")
            self.results.add_luna_error(f"Koalageddon file migration failed: {e}")
            self.results.luna_components_installed.append(("Legacy Koalageddon Files", False))
    
    async def _update_legacy_shortcuts(self) -> None:
        """Update old GreenLuma and Koalageddon shortcuts to point to Luna."""
        self.logger.info("Updating legacy shortcuts to Luna")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would update legacy shortcuts")
            return
        
        # Desktop path
        desktop = Path.home() / "Desktop"
        
        # Legacy shortcuts to update
        legacy_shortcuts = [
            "GreenLuma.lnk",
            "Koalageddon.lnk",
            "DLLInjector.lnk",
            "GreenLuma DLL Injector.lnk"
        ]
        
        for shortcut_name in legacy_shortcuts:
            shortcut_path = desktop / shortcut_name
            if shortcut_path.exists():
                try:
                    # Remove old shortcut
                    shortcut_path.unlink()
                    self.logger.info(f"Removed legacy shortcut: {shortcut_name}")
                    self.results.luna_shortcuts_updated.append((shortcut_name, True))
                except Exception as e:
                    self.logger.warning(f"Failed to remove legacy shortcut {shortcut_name}: {e}")
                    self.results.luna_shortcuts_updated.append((shortcut_name, False))
        
        # Create note about Luna shortcuts
        try:
            note_path = desktop / "Luna_Migration_Note.txt"
            with open(note_path, 'w') as f:
                f.write("Luna Gaming Tool Migration\n")
                f.write("=" * 30 + "\n\n")
                f.write("Your GreenLuma and Koalageddon installations have been migrated to Luna.\n")
                f.write("New Luna shortcuts have been created on your desktop.\n\n")
                f.write("Luna combines both tools into a unified gaming solution.\n")
                f.write("You can safely delete this note after reading.\n")
            
            self.logger.info("Created Luna migration note on desktop")
            
        except Exception as e:
            self.logger.warning(f"Failed to create migration note: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="luna-gaming-tool",
        description="Luna Setup Tool - Unified gaming tool combining injection and DLC unlocking",
        epilog="""
Examples:
  %(prog)s                    Run Luna setup with default settings
  %(prog)s --verbose          Run Luna setup with detailed logging
  %(prog)s --dry-run          Show what would be done without making changes
  %(prog)s --skip-admin       Skip admin privilege checks (not recommended)
  %(prog)s --config-only      Only update Luna configuration files
  %(prog)s --legacy-greenluma-path ~/Documents/GreenLuma    Migrate from existing GreenLuma
  %(prog)s --legacy-koalageddon-path ~/Documents/Koalageddon  Migrate from existing Koalageddon
  
Exit Codes:
  0   Success - Luna setup completed successfully
  1   General Error - Luna setup failed due to an error
  2   Admin Required - Administrator privileges are required
  3   Network Error - Failed to download required Luna files
  4   File Error - File operation failed (missing files, permissions)
  5   Config Error - Luna configuration error or invalid settings
  6   User Cancelled - Luna setup was cancelled by the user
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Logging options
    logging_group = parser.add_argument_group("Logging Options")
    logging_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging output with debug information"
    )
    logging_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress non-essential output (errors and warnings only)"
    )
    
    # Setup mode options
    mode_group = parser.add_argument_group("Setup Mode Options")
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any actual changes"
    )
    mode_group.add_argument(
        "--config-only",
        action="store_true",
        help="Only update configuration files, skip downloads and installations"
    )
    mode_group.add_argument(
        "--skip-admin",
        action="store_true",
        help="Skip administrator privilege checks (may cause setup to fail)"
    )
    mode_group.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip Windows Defender exclusion setup"
    )
    
    # Configuration options
    config_group = parser.add_argument_group("Configuration Options")
    config_group.add_argument(
        "--luna-core-path",
        type=Path,
        help="Custom path for Luna core installation (default: ~/Documents/Luna)"
    )
    config_group.add_argument(
        "--legacy-greenluma-path",
        type=Path,
        help="Path to existing GreenLuma installation for migration"
    )
    config_group.add_argument(
        "--legacy-koalageddon-path",
        type=Path,
        help="Path to existing Koalageddon installation for migration"
    )
    config_group.add_argument(
        "--app-id",
        type=str,
        default="480",
        help="Steam App ID for Luna AppList (default: 480 for Spacewar)"
    )
    config_group.add_argument(
        "--download-url",
        type=str,
        help="Custom download URL for Luna unlocker installer"
    )
    
    # Advanced options
    advanced_group = parser.add_argument_group("Advanced Options")
    advanced_group.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of temporary files (useful for debugging)"
    )
    advanced_group.add_argument(
        "--force",
        action="store_true",
        help="Force setup even if files already exist"
    )
    advanced_group.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Network timeout in seconds (default: 300)"
    )
    
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command-line arguments and check for conflicts."""
    # Check for conflicting options
    if args.verbose and args.quiet:
        raise argparse.ArgumentTypeError("Cannot use --verbose and --quiet together")
    
    if args.dry_run and args.config_only:
        raise argparse.ArgumentTypeError("Cannot use --dry-run and --config-only together")
    
    # Validate Luna paths if provided
    if args.luna_core_path and not args.luna_core_path.parent.exists():
        raise argparse.ArgumentTypeError(f"Parent directory does not exist: {args.luna_core_path.parent}")
    
    if args.legacy_greenluma_path and not args.legacy_greenluma_path.exists():
        raise argparse.ArgumentTypeError(f"Legacy GreenLuma path does not exist: {args.legacy_greenluma_path}")
    
    if args.legacy_koalageddon_path and not args.legacy_koalageddon_path.exists():
        raise argparse.ArgumentTypeError(f"Legacy Koalageddon path does not exist: {args.legacy_koalageddon_path}")
    
    # Validate timeout
    if args.timeout <= 0:
        raise argparse.ArgumentTypeError("Timeout must be a positive integer")
    
    # Validate App ID
    if args.app_id and not args.app_id.isdigit():
        raise argparse.ArgumentTypeError("App ID must be a numeric string")


def determine_exit_code(exception: Exception) -> int:
    """Determine appropriate exit code based on exception type."""
    if isinstance(exception, AdminPrivilegeError):
        return 2  # Admin required
    elif isinstance(exception, (NetworkError, DownloadError, ConnectionTimeoutError)):
        return 3  # Network error
    elif isinstance(exception, FileOperationError):
        return 4  # File error
    elif isinstance(exception, ConfigurationError):
        return 5  # Config error
    elif isinstance(exception, KeyboardInterrupt):
        return 6  # User cancelled
    else:
        return 1  # General error


def perform_startup_checks() -> None:
    """Perform comprehensive startup checks and environment validation."""
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required", file=sys.stderr)
        print(f"Current version: {sys.version}", file=sys.stderr)
        sys.exit(1)
    
    # Check platform compatibility
    supported_platforms = ['Windows', 'Linux', 'Darwin']
    current_platform = platform.system()
    if current_platform not in supported_platforms:
        print(f"Warning: Platform '{current_platform}' is not fully supported", file=sys.stderr)
        print("Some features may not work correctly", file=sys.stderr)
    
    # Check for required assets
    required_assets = [
        Path("assets/greenluma.zip"),
        Path("assets")  # Assets directory should exist
    ]
    
    missing_assets = []
    for asset in required_assets:
        if not asset.exists():
            missing_assets.append(str(asset))
    
    if missing_assets:
        print("Error: Required assets are missing:", file=sys.stderr)
        for asset in missing_assets:
            print(f"  - {asset}", file=sys.stderr)
        print("\nPlease ensure all required assets are present before running the setup.", file=sys.stderr)
        sys.exit(4)  # File error
    
    # Check write permissions for default paths
    test_paths = [
        Path.home() / "Documents",
        Path.home() / "Desktop" if (Path.home() / "Desktop").exists() else None
    ]
    
    permission_issues = []
    for test_path in test_paths:
        if test_path and test_path.exists():
            try:
                # Test write permission by creating a temporary file
                test_file = test_path / f".gaming_setup_test_{os.getpid()}"
                test_file.write_text("test")
                test_file.unlink()
            except (PermissionError, OSError) as e:
                permission_issues.append(f"{test_path}: {e}")
    
    if permission_issues:
        print("Warning: Permission issues detected:", file=sys.stderr)
        for issue in permission_issues:
            print(f"  - {issue}", file=sys.stderr)
        print("You may need to run with administrator privileges or choose different paths.", file=sys.stderr)
    
    # Check available disk space (at least 100MB)
    try:
        import shutil
        free_space = shutil.disk_usage(Path.home()).free
        required_space = 100 * 1024 * 1024  # 100MB
        
        if free_space < required_space:
            print(f"Warning: Low disk space detected", file=sys.stderr)
            print(f"Available: {free_space // (1024*1024)}MB, Recommended: {required_space // (1024*1024)}MB", file=sys.stderr)
    except Exception:
        # Disk space check is not critical
        pass


def validate_environment() -> None:
    """Validate the runtime environment and dependencies."""
    # Check for required Python modules
    required_modules = [
        'rich',
        'pathlib',
        'asyncio',
        'zipfile',
        'argparse'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Error: Required Python modules are missing:", file=sys.stderr)
        for module in missing_modules:
            print(f"  - {module}", file=sys.stderr)
        print("\nPlease install required dependencies using: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    
    # Validate Rich console functionality
    try:
        from rich.console import Console
        test_console = Console()
        # Test basic Rich functionality
        test_console.print("", end="")  # Silent test
    except Exception as e:
        print(f"Error: Rich console initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Check for Windows-specific dependencies on Windows
    if platform.system() == 'Windows':
        try:
            import ctypes
            import subprocess
            # Test basic Windows API access
            ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            print(f"Warning: Windows-specific functionality may be limited: {e}", file=sys.stderr)


def main() -> None:
    """Main entry point with comprehensive startup checks, argument parsing and error handling."""
    exit_code = 0
    
    try:
        # Perform startup checks and environment validation
        perform_startup_checks()
        validate_environment()
        
        # Create and parse arguments
        parser = create_argument_parser()
        
        try:
            args = parser.parse_args()
            validate_arguments(args)
        except argparse.ArgumentTypeError as e:
            print(f"Error: {e}", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        except SystemExit:
            # argparse calls sys.exit() for --help, --version, etc.
            raise
        
        # Configure logging level based on arguments
        if args.quiet:
            log_level = logging.WARNING
        elif args.verbose:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        
        # Create Luna setup configuration from arguments
        luna_setup_config = {
            'verbose': args.verbose,
            'quiet': args.quiet,
            'dry_run': args.dry_run,
            'config_only': args.config_only,
            'skip_admin': args.skip_admin,
            'skip_security': args.skip_security,
            'no_cleanup': args.no_cleanup,
            'force': args.force,
            'timeout': args.timeout,
            'luna_core_path': args.luna_core_path,
            'legacy_greenluma_path': args.legacy_greenluma_path,
            'legacy_koalageddon_path': args.legacy_koalageddon_path,
            'app_id': args.app_id,
            'download_url': args.download_url
        }
        
        # Create and run the Luna setup tool
        tool = LunaSetupTool(**luna_setup_config)
        asyncio.run(tool.run())
        
        # Success - exit with code 0
        exit_code = 0
        
    except KeyboardInterrupt:
        if not (len(sys.argv) > 1 and '--quiet' in sys.argv):
            print("\n[yellow]Setup cancelled by user[/yellow]")
        exit_code = 6
        
    except SystemExit as e:
        # Preserve the original exit code from SystemExit
        exit_code = e.code if e.code is not None else 0
        
    except Exception as e:
        # Determine appropriate exit code
        exit_code = determine_exit_code(e)
        
        # Log error if not in quiet mode
        quiet_mode = len(sys.argv) > 1 and '--quiet' in sys.argv
        if not quiet_mode:
            verbose_mode = len(sys.argv) > 1 and ('--verbose' in sys.argv or '-v' in sys.argv)
            if verbose_mode:
                # Show full traceback in verbose mode
                import traceback
                print(f"Fatal error: {e}", file=sys.stderr)
                traceback.print_exc()
            else:
                print(f"Fatal error: {e}", file=sys.stderr)
                print("Use --verbose for detailed error information", file=sys.stderr)
    
    finally:
        # Exit with appropriate code
        sys.exit(exit_code)


if __name__ == "__main__":
    main()