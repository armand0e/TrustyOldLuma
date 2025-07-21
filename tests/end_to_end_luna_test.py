#!/usr/bin/env python3
"""
End-to-End Luna Workflow Test

This script performs a comprehensive end-to-end test of the Luna Gaming Tool,
including installation, migration, configuration, and operation.

Usage:
    python tests/end_to_end_luna_test.py [--verbose] [--no-cleanup]

Options:
    --verbose       Enable verbose output
    --no-cleanup    Don't clean up test files after running
"""

import os
import sys
import asyncio
import argparse
import tempfile
import shutil
import json
import zipfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Rich library not found. Please install it with: pip install rich")
    sys.exit(1)

try:
    # Try importing from src.luna structure
    from src.luna.core.luna_core import LunaCore
    from src.luna.models.models import LunaConfig, LunaResults, LunaShortcutConfig
    from src.luna.setup.setup_tool import LunaSetupTool
except ImportError:
    try:
        # Fallback to flat structure
        from luna.core.luna_core import LunaCore
        from models import LunaConfig, LunaResults, LunaShortcutConfig
        from gaming_setup_tool import LunaSetupTool
    except ImportError:
        print("Luna modules not found. Make sure you're running from the project root.")
        sys.exit(1)


class EndToEndTest:
    """End-to-end test for Luna Gaming Tool."""
    
    def __init__(self, verbose: bool = False, cleanup: bool = True):
        """Initialize the end-to-end test.
        
        Args:
            verbose: Enable verbose output
            cleanup: Clean up test files after running
        """
        self.verbose = verbose
        self.cleanup = cleanup
        self.console = Console()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace = self._create_workspace()
        self.results = LunaResults()
    
    def _create_workspace(self) -> Dict[str, Path]:
        """Create a temporary workspace for testing.
        
        Returns:
            Dict[str, Path]: Workspace directories
        """
        workspace = {
            'root': self.temp_dir,
            'luna': self.temp_dir / "Luna",
            'luna_injector': self.temp_dir / "Luna" / "injector",
            'luna_unlocker': self.temp_dir / "Luna" / "unlocker",
            'luna_config': self.temp_dir / "Luna" / "config",
            'assets': self.temp_dir / "assets",
            'desktop': self.temp_dir / "Desktop",
            'documents': self.temp_dir / "Documents",
            'greenluma': self.temp_dir / "Documents" / "GreenLuma",
            'koalageddon': self.temp_dir / "Documents" / "Koalageddon",
            'temp': self.temp_dir / "temp"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        return workspace
    
    def _create_mock_assets(self):
        """Create mock asset files for testing."""
        # Create mock injector zip
        injector_zip = self.workspace['assets'] / "luna_injector.zip"
        with zipfile.ZipFile(injector_zip, 'w') as zf:
            zf.writestr("luna_injector.exe", b"mock executable")
            zf.writestr("luna_core_x64.dll", b"mock dll")
            zf.writestr("luna_injector.ini", b"[Settings]\nDLL=luna_core_x64.dll\n")
        
        # Create mock unlocker zip
        unlocker_zip = self.workspace['assets'] / "luna_unlocker.zip"
        with zipfile.ZipFile(unlocker_zip, 'w') as zf:
            zf.writestr("luna_unlocker.exe", b"mock executable")
            zf.writestr("luna_unlocker.dll", b"mock dll")
            zf.writestr("luna_unlocker.json", b"{\"EnableSteam\": true}")
        
        # Create legacy GreenLuma files
        (self.workspace['greenluma'] / "DLLInjector.exe").write_bytes(b"mock executable")
        (self.workspace['greenluma'] / "GreenLuma_2020_x64.dll").write_bytes(b"mock dll")
        (self.workspace['greenluma'] / "DLLInjector.ini").write_text("[Settings]\nDLL=GreenLuma_2020_x64.dll\n")
        
        # Create AppList directory and files
        applist_dir = self.workspace['greenluma'] / "AppList"
        applist_dir.mkdir(exist_ok=True)
        (applist_dir / "0.txt").write_text("480")  # Spacewar
        (applist_dir / "1.txt").write_text("570")  # Dota 2
        
        # Create legacy Koalageddon files
        (self.workspace['koalageddon'] / "Koalageddon.exe").write_bytes(b"mock executable")
        (self.workspace['koalageddon'] / "Koalageddon.dll").write_bytes(b"mock dll")
        (self.workspace['koalageddon'] / "Config.jsonc").write_text(
            '{\n'
            '  "EnableSteam": true,\n'
            '  "EnableEpic": true,\n'
            '  "EnableOrigin": false,\n'
            '  "EnableUplay": false,\n'
            '  "LogLevel": "Info"\n'
            '}\n'
        )
        
        # Create legacy shortcuts
        (self.workspace['desktop'] / "GreenLuma DLLInjector.lnk").write_bytes(b"mock shortcut")
        (self.workspace['desktop'] / "Koalageddon.lnk").write_bytes(b"mock shortcut")
    
    def _create_luna_config(self) -> Path:
        """Create a Luna configuration file for testing.
        
        Returns:
            Path: Path to the configuration file
        """
        config_file = self.workspace['luna_config'] / "luna_config.jsonc"
        config_content = {
            "luna": {
                "version": "1.0.0",
                "core": {
                    "injector_enabled": True,
                    "unlocker_enabled": True,
                    "auto_start": False,
                    "stealth_mode": True
                },
                "platforms": {
                    "steam": {"enabled": True, "priority": 1},
                    "epic": {"enabled": True, "priority": 2},
                    "origin": {"enabled": False, "priority": 3},
                    "uplay": {"enabled": False, "priority": 4}
                },
                "paths": {
                    "core_directory": str(self.workspace['luna']),
                    "config_directory": str(self.workspace['luna_config']),
                    "temp_directory": str(self.workspace['temp'])
                },
                "migration": {
                    "auto_detect_legacy": True,
                    "migrate_greenluma": True,
                    "migrate_koalageddon": True,
                    "preserve_legacy": False,
                    "backup_before_migration": True,
                    "legacy_paths": {
                        "greenluma_default": str(self.workspace['greenluma']),
                        "koalageddon_default": str(self.workspace['koalageddon'])
                    }
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_content, f, indent=2)
        
        return config_file
    
    def _create_setup_config(self) -> LunaConfig:
        """Create a test LunaConfig instance.
        
        Returns:
            LunaConfig: Test configuration
        """
        return LunaConfig(
            luna_core_path=self.workspace['luna'],
            luna_config_path=self.workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            verbose_logging=self.verbose,
            documents_path=self.workspace['documents'],
            temp_dir=self.workspace['temp'],
            desktop_path=self.workspace['desktop'],
            legacy_greenluma_path=self.workspace['greenluma'],
            legacy_koalageddon_path=self.workspace['koalageddon']
        )
    
    def cleanup_workspace(self):
        """Clean up the temporary workspace."""
        if self.cleanup and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.console.print("[green]Cleaned up temporary workspace[/green]")
    
    async def run_test(self):
        """Run the end-to-end test."""
        try:
            # Create mock assets
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                # Setup phase
                setup_task = progress.add_task("[cyan]Setting up test environment...", total=3)
                
                # Create mock assets
                self._create_mock_assets()
                progress.update(setup_task, advance=1)
                
                # Create Luna configuration
                config_file = self._create_luna_config()
                progress.update(setup_task, advance=1)
                
                # Create setup configuration
                setup_config = self._create_setup_config()
                progress.update(setup_task, advance=1, completed=True)
                
                # Test phases
                test_task = progress.add_task("[cyan]Running end-to-end tests...", total=5)
                
                # Phase 1: Test Luna core initialization
                self.console.print("\n[bold cyan]Phase 1: Testing Luna Core Initialization[/bold cyan]")
                await self._test_luna_core_initialization(config_file)
                progress.update(test_task, advance=1)
                
                # Phase 2: Test Luna migration
                self.console.print("\n[bold cyan]Phase 2: Testing Luna Migration[/bold cyan]")
                await self._test_luna_migration(setup_config)
                progress.update(test_task, advance=1)
                
                # Phase 3: Test Luna configuration
                self.console.print("\n[bold cyan]Phase 3: Testing Luna Configuration[/bold cyan]")
                await self._test_luna_configuration(config_file)
                progress.update(test_task, advance=1)
                
                # Phase 4: Test Luna component interaction
                self.console.print("\n[bold cyan]Phase 4: Testing Luna Component Interaction[/bold cyan]")
                await self._test_luna_component_interaction(config_file)
                progress.update(test_task, advance=1)
                
                # Phase 5: Test Luna platform integration
                self.console.print("\n[bold cyan]Phase 5: Testing Luna Platform Integration[/bold cyan]")
                await self._test_luna_platform_integration(config_file)
                progress.update(test_task, advance=1, completed=True)
            
            # Display test results
            self._display_test_results()
            
        except Exception as e:
            self.console.print(f"[bold red]Error during end-to-end test: {str(e)}[/bold red]")
            if self.verbose:
                self.console.print_exception()
            return False
        finally:
            # Clean up
            if self.cleanup:
                self.cleanup_workspace()
        
        return len(self.results.errors) == 0
    
    async def _test_luna_core_initialization(self, config_file: Path) -> bool:
        """Test Luna core initialization.
        
        Args:
            config_file: Path to Luna configuration file
            
        Returns:
            bool: Test success
        """
        try:
            # Create Luna core
            luna_core = LunaCore(config_file)
            
            # Initialize Luna core
            self.console.print("  Initializing Luna core...")
            result = await luna_core.initialize()
            
            # Verify initialization was successful
            if result:
                self.console.print("  [green]✓[/green] Luna core initialized successfully")
            else:
                self.console.print("  [red]✗[/red] Luna core initialization failed")
                self.results.errors.append("Luna core initialization failed")
                return False
            
            # Verify configuration was loaded
            config = await luna_core.get_config()
            if config:
                self.console.print("  [green]✓[/green] Luna configuration loaded successfully")
            else:
                self.console.print("  [red]✗[/red] Luna configuration loading failed")
                self.results.errors.append("Luna configuration loading failed")
                return False
            
            # Shutdown Luna core
            await luna_core.shutdown()
            self.console.print("  [green]✓[/green] Luna core shutdown successfully")
            
            return True
        
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Error during Luna core initialization: {str(e)}")
            self.results.errors.append(f"Luna core initialization error: {str(e)}")
            if self.verbose:
                self.console.print_exception()
            return False
    
    async def _test_luna_migration(self, setup_config: LunaConfig) -> bool:
        """Test Luna migration from legacy installations.
        
        Args:
            setup_config: Luna setup configuration
            
        Returns:
            bool: Test success
        """
        try:
            # Create setup tool
            setup_tool = LunaSetupTool(verbose=self.verbose)
            setup_tool.config = setup_config
            
            # Detect legacy installations
            self.console.print("  Detecting legacy installations...")
            legacy_installations = await setup_tool._detect_legacy_installations()
            
            if legacy_installations:
                self.console.print("  [green]✓[/green] Legacy installations detected:")
                for name, path in legacy_installations.items():
                    self.console.print(f"    - {name}: {path}")
            else:
                self.console.print("  [yellow]![/yellow] No legacy installations detected")
                return True
            
            # Migrate legacy configurations
            self.console.print("  Migrating legacy configurations...")
            config_migration = await setup_tool._migrate_legacy_configurations(self.results)
            
            if config_migration:
                self.console.print("  [green]✓[/green] Legacy configurations migrated successfully")
            else:
                self.console.print("  [red]✗[/red] Legacy configuration migration failed")
                self.results.errors.append("Legacy configuration migration failed")
                return False
            
            # Migrate legacy files
            self.console.print("  Migrating legacy files...")
            file_migration = await setup_tool._migrate_legacy_files(self.results)
            
            if file_migration:
                self.console.print("  [green]✓[/green] Legacy files migrated successfully")
            else:
                self.console.print("  [red]✗[/red] Legacy file migration failed")
                self.results.errors.append("Legacy file migration failed")
                return False
            
            # Update legacy shortcuts
            self.console.print("  Updating legacy shortcuts...")
            shortcut_update = await setup_tool._update_legacy_shortcuts(self.results)
            
            if shortcut_update:
                self.console.print("  [green]✓[/green] Legacy shortcuts updated successfully")
            else:
                self.console.print("  [red]✗[/red] Legacy shortcut update failed")
                self.results.errors.append("Legacy shortcut update failed")
                return False
            
            return True
        
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Error during Luna migration: {str(e)}")
            self.results.errors.append(f"Luna migration error: {str(e)}")
            if self.verbose:
                self.console.print_exception()
            return False
    
    async def _test_luna_configuration(self, config_file: Path) -> bool:
        """Test Luna configuration management.
        
        Args:
            config_file: Path to Luna configuration file
            
        Returns:
            bool: Test success
        """
        try:
            # Create Luna core
            luna_core = LunaCore(config_file)
            
            # Initialize Luna core
            await luna_core.initialize()
            
            # Get initial configuration
            self.console.print("  Getting initial configuration...")
            initial_config = await luna_core.get_config()
            
            if initial_config:
                self.console.print("  [green]✓[/green] Initial configuration retrieved successfully")
            else:
                self.console.print("  [red]✗[/red] Failed to retrieve initial configuration")
                self.results.errors.append("Failed to retrieve initial configuration")
                return False
            
            # Update configuration
            self.console.print("  Updating configuration...")
            update_result = await luna_core.update_config({
                "injector_enabled": False,
                "unlocker_enabled": True,
                "platforms": {
                    "steam": {"enabled": False},
                    "epic": {"enabled": True}
                }
            })
            
            if update_result["success"]:
                self.console.print("  [green]✓[/green] Configuration updated successfully")
            else:
                self.console.print(f"  [red]✗[/red] Configuration update failed: {update_result['message']}")
                self.results.errors.append(f"Configuration update failed: {update_result['message']}")
                return False
            
            # Get updated configuration
            self.console.print("  Getting updated configuration...")
            updated_config = await luna_core.get_config()
            
            if updated_config:
                self.console.print("  [green]✓[/green] Updated configuration retrieved successfully")
                
                # Verify configuration changes
                if updated_config["injector_enabled"] is False and \
                   updated_config["unlocker_enabled"] is True and \
                   updated_config["platforms"]["steam"]["enabled"] is False and \
                   updated_config["platforms"]["epic"]["enabled"] is True:
                    self.console.print("  [green]✓[/green] Configuration changes verified")
                else:
                    self.console.print("  [red]✗[/red] Configuration changes not applied correctly")
                    self.results.errors.append("Configuration changes not applied correctly")
                    return False
            else:
                self.console.print("  [red]✗[/red] Failed to retrieve updated configuration")
                self.results.errors.append("Failed to retrieve updated configuration")
                return False
            
            # Shutdown Luna core
            await luna_core.shutdown()
            
            return True
        
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Error during Luna configuration test: {str(e)}")
            self.results.errors.append(f"Luna configuration error: {str(e)}")
            if self.verbose:
                self.console.print_exception()
            return False
    
    async def _test_luna_component_interaction(self, config_file: Path) -> bool:
        """Test Luna component interaction.
        
        Args:
            config_file: Path to Luna configuration file
            
        Returns:
            bool: Test success
        """
        try:
            # Create Luna core
            luna_core = LunaCore(config_file)
            
            # Initialize Luna core
            await luna_core.initialize()
            
            # Start injector
            self.console.print("  Starting Luna injector...")
            injector_result = await luna_core.start_injector()
            
            if injector_result["success"]:
                self.console.print("  [green]✓[/green] Luna injector started successfully")
            else:
                self.console.print(f"  [red]✗[/red] Luna injector start failed: {injector_result['message']}")
                self.results.errors.append(f"Luna injector start failed: {injector_result['message']}")
                return False
            
            # Start unlocker
            self.console.print("  Starting Luna unlocker...")
            unlocker_result = await luna_core.start_unlocker()
            
            if unlocker_result["success"]:
                self.console.print("  [green]✓[/green] Luna unlocker started successfully")
            else:
                self.console.print(f"  [red]✗[/red] Luna unlocker start failed: {unlocker_result['message']}")
                self.results.errors.append(f"Luna unlocker start failed: {unlocker_result['message']}")
                return False
            
            # Verify monitoring task is running
            if luna_core.monitoring_task is not None and not luna_core.monitoring_task.done():
                self.console.print("  [green]✓[/green] Luna monitoring task is running")
            else:
                self.console.print("  [red]✗[/red] Luna monitoring task is not running")
                self.results.errors.append("Luna monitoring task is not running")
                return False
            
            # Stop injector
            self.console.print("  Stopping Luna injector...")
            injector_stop_result = await luna_core.stop_injector()
            
            if injector_stop_result["success"]:
                self.console.print("  [green]✓[/green] Luna injector stopped successfully")
            else:
                self.console.print(f"  [red]✗[/red] Luna injector stop failed: {injector_stop_result['message']}")
                self.results.errors.append(f"Luna injector stop failed: {injector_stop_result['message']}")
                return False
            
            # Stop unlocker
            self.console.print("  Stopping Luna unlocker...")
            unlocker_stop_result = await luna_core.stop_unlocker()
            
            if unlocker_stop_result["success"]:
                self.console.print("  [green]✓[/green] Luna unlocker stopped successfully")
            else:
                self.console.print(f"  [red]✗[/red] Luna unlocker stop failed: {unlocker_stop_result['message']}")
                self.results.errors.append(f"Luna unlocker stop failed: {unlocker_stop_result['message']}")
                return False
            
            # Verify monitoring task is stopped
            await asyncio.sleep(0.1)  # Give time for monitoring task to stop
            if luna_core.monitoring_task is None or luna_core.monitoring_task.done():
                self.console.print("  [green]✓[/green] Luna monitoring task stopped")
            else:
                self.console.print("  [red]✗[/red] Luna monitoring task is still running")
                self.results.errors.append("Luna monitoring task is still running")
                return False
            
            # Shutdown Luna core
            await luna_core.shutdown()
            
            return True
        
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Error during Luna component interaction test: {str(e)}")
            self.results.errors.append(f"Luna component interaction error: {str(e)}")
            if self.verbose:
                self.console.print_exception()
            return False
    
    async def _test_luna_platform_integration(self, config_file: Path) -> bool:
        """Test Luna platform integration.
        
        Args:
            config_file: Path to Luna configuration file
            
        Returns:
            bool: Test success
        """
        try:
            # Create Luna core
            luna_core = LunaCore(config_file)
            
            # Initialize Luna core
            await luna_core.initialize()
            
            # Configure platforms
            self.console.print("  Configuring platforms...")
            platform_config = {
                "platforms": {
                    "steam": {"enabled": True, "priority": 1},
                    "epic": {"enabled": True, "priority": 2},
                    "origin": {"enabled": True, "priority": 3},
                    "uplay": {"enabled": False, "priority": 4}
                }
            }
            
            update_result = await luna_core.update_config(platform_config)
            
            if update_result["success"]:
                self.console.print("  [green]✓[/green] Platform configuration updated successfully")
            else:
                self.console.print(f"  [red]✗[/red] Platform configuration update failed: {update_result['message']}")
                self.results.errors.append(f"Platform configuration update failed: {update_result['message']}")
                return False
            
            # Start injector with platform-specific configuration
            self.console.print("  Starting injector with platform-specific configuration...")
            injector_result = await luna_core.start_injector({
                "injector_enabled": True,
                "app_list": ["480", "570", "730"]  # Example Steam App IDs
            })
            
            if injector_result["success"]:
                self.console.print("  [green]✓[/green] Injector started with platform-specific configuration")
            else:
                self.console.print(f"  [red]✗[/red] Injector start failed: {injector_result['message']}")
                self.results.errors.append(f"Injector start failed: {injector_result['message']}")
                return False
            
            # Start unlocker with platform-specific configuration
            self.console.print("  Starting unlocker with platform-specific configuration...")
            unlocker_result = await luna_core.start_unlocker({
                "unlocker_enabled": True,
                "unlock_dlc": True,
                "platforms": {
                    "steam": {"enabled": True},
                    "epic": {"enabled": True},
                    "origin": {"enabled": True},
                    "uplay": {"enabled": False}
                }
            })
            
            if unlocker_result["success"]:
                self.console.print("  [green]✓[/green] Unlocker started with platform-specific configuration")
            else:
                self.console.print(f"  [red]✗[/red] Unlocker start failed: {unlocker_result['message']}")
                self.results.errors.append(f"Unlocker start failed: {unlocker_result['message']}")
                return False
            
            # Verify configuration was updated
            self.console.print("  Verifying platform configuration...")
            config = await luna_core.get_config()
            
            if config["platforms"]["steam"]["enabled"] is True and \
               config["platforms"]["epic"]["enabled"] is True and \
               config["platforms"]["origin"]["enabled"] is True and \
               config["platforms"]["uplay"]["enabled"] is False:
                self.console.print("  [green]✓[/green] Platform configuration verified")
            else:
                self.console.print("  [red]✗[/red] Platform configuration not applied correctly")
                self.results.errors.append("Platform configuration not applied correctly")
                return False
            
            # Shutdown Luna core
            await luna_core.shutdown()
            
            return True
        
        except Exception as e:
            self.console.print(f"  [red]✗[/red] Error during Luna platform integration test: {str(e)}")
            self.results.errors.append(f"Luna platform integration error: {str(e)}")
            if self.verbose:
                self.console.print_exception()
            return False
    
    def _display_test_results(self):
        """Display test results."""
        self.console.print("\n[bold cyan]End-to-End Test Results[/bold cyan]")
        
        # Create results table
        table = Table(title="Luna End-to-End Test Results")
        table.add_column("Test Phase", style="cyan")
        table.add_column("Status", style="green")
        
        # Add test results
        phases = [
            "Luna Core Initialization",
            "Luna Migration",
            "Luna Configuration",
            "Luna Component Interaction",
            "Luna Platform Integration"
        ]
        
        # Check for errors in each phase
        for i, phase in enumerate(phases):
            phase_errors = [e for e in self.results.errors if phase.lower() in e.lower()]
            status = "[green]✓ Passed[/green]" if not phase_errors else f"[red]✗ Failed ({len(phase_errors)} errors)[/red]"
            table.add_row(phase, status)
        
        # Display table
        self.console.print(table)
        
        # Display errors if any
        if self.results.errors:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for i, error in enumerate(self.results.errors, 1):
                self.console.print(f"  {i}. {error}")
        else:
            self.console.print("\n[bold green]All tests passed successfully![/bold green]")


async def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="End-to-End Luna Workflow Test")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't clean up test files after running")
    args = parser.parse_args()
    
    # Create and run test
    test = EndToEndTest(verbose=args.verbose, cleanup=not args.no_cleanup)
    success = await test.run_test()
    
    # Return exit code
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)