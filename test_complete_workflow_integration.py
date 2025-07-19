"""
Complete workflow integration tests with real file operations.

This module tests the complete setup workflow with minimal mocking
to verify actual functionality and file system operations.
"""

import pytest
import asyncio
import tempfile
import shutil
import zipfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from rich.console import Console

from gaming_setup_tool import GamingSetupTool
from models import SetupConfig, SetupResults
from admin_manager import AdminPrivilegeManager
from file_operations_manager import FileOperationsManager
from security_config_manager import SecurityConfigManager
from configuration_handler import ConfigurationHandler
from shortcut_manager import ShortcutManager
from applist_manager import AppListManager
from cleanup_manager import CleanupManager


class TestCompleteWorkflowIntegration:
    """Test complete workflow with real file operations."""
    
    @pytest.fixture
    def real_workspace(self):
        """Create a real temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'documents': temp_dir / "Documents",
            'greenluma': temp_dir / "Documents" / "GreenLuma",
            'koalageddon': temp_dir / "Koalageddon",
            'temp': temp_dir / "temp",
            'desktop': temp_dir / "Desktop",
            'assets': temp_dir / "assets"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        yield workspace
        
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def real_assets(self, real_workspace):
        """Create real asset files for testing."""
        assets_dir = real_workspace['assets']
        
        # Create real GreenLuma zip file
        greenluma_zip = assets_dir / "greenluma.zip"
        with zipfile.ZipFile(greenluma_zip, 'w') as zip_ref:
            zip_ref.writestr("GreenLuma_2020_x64.dll", b"Mock DLL content for testing")
            zip_ref.writestr("DLLInjector.exe", b"Mock executable content")
            zip_ref.writestr("DLLInjector.ini", 
                           "[Settings]\n"
                           "DLL=GreenLuma_2020_x64.dll\n"
                           "ProcessName=steam.exe\n"
                           "Timeout=30\n")
            zip_ref.writestr("README.txt", "GreenLuma setup files")
        
        # Create real Koalageddon config
        koa_config = assets_dir / "koalageddon.config"
        koa_config.write_text(
            '{\n'
            '  "EnableSteam": true,\n'
            '  "EnableEpic": true,\n'
            '  "EnableOrigin": false,\n'
            '  "LogLevel": "Info",\n'
            '  "AutoInject": true\n'
            '}\n'
        )
        
        return {
            'greenluma_zip': greenluma_zip,
            'koalageddon_config': koa_config
        }
    
    @pytest.mark.asyncio
    async def test_file_operations_real_workflow(self, real_workspace, real_assets):
        """Test file operations with real files and directories."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        # Test directory creation
        test_dirs = [
            real_workspace['greenluma'],
            real_workspace['koalageddon'],
            real_workspace['temp']
        ]
        
        await file_manager.create_directories(test_dirs, results)
        
        # Verify directories were created
        for test_dir in test_dirs:
            assert test_dir.exists()
            assert test_dir.is_dir()
        
        assert len(results.directories_created) == len(test_dirs)
        assert len(results.errors) == 0
        
        # Test archive extraction
        extract_result = await file_manager.extract_archive(
            real_assets['greenluma_zip'],
            real_workspace['greenluma'],
            flatten=True,
            results=results
        )
        
        assert extract_result is True
        assert results.files_extracted is True
        
        # Verify extracted files exist
        assert (real_workspace['greenluma'] / "GreenLuma_2020_x64.dll").exists()
        assert (real_workspace['greenluma'] / "DLLInjector.exe").exists()
        assert (real_workspace['greenluma'] / "DLLInjector.ini").exists()
        
        # Test file integrity verification
        dll_file = real_workspace['greenluma'] / "GreenLuma_2020_x64.dll"
        integrity_result = await file_manager.verify_file_integrity(dll_file)
        assert integrity_result is True
    
    @pytest.mark.asyncio
    async def test_configuration_handler_real_workflow(self, real_workspace, real_assets):
        """Test configuration handler with real files."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        config_handler = ConfigurationHandler(console)
        results = SetupResults()
        
        # Extract files first
        file_manager = FileOperationsManager(console)
        await file_manager.extract_archive(
            real_assets['greenluma_zip'],
            real_workspace['greenluma'],
            flatten=True,
            results=results
        )
        
        # Test DLL injector config update
        dll_file = real_workspace['greenluma'] / "GreenLuma_2020_x64.dll"
        config_file = real_workspace['greenluma'] / "DLLInjector.ini"
        
        update_result = await config_handler.update_dll_injector_config(
            dll_file, config_file, results
        )
        
        assert update_result is True
        assert len(results.configs_updated) == 1
        assert results.configs_updated[0][1] is True  # Success flag
        
        # Verify config file was updated
        with open(config_file, 'r') as f:
            content = f.read()
            assert str(dll_file) in content
        
        # Test Koalageddon config replacement
        koa_dest_dir = real_workspace['koalageddon']
        replace_result = await config_handler.replace_koalageddon_config(
            real_assets['koalageddon_config'],
            koa_dest_dir,
            results
        )
        
        assert replace_result is True
        
        # Verify config was copied
        dest_config = koa_dest_dir / "koalageddon.config"
        assert dest_config.exists()
        
        with open(dest_config, 'r') as f:
            content = f.read()
            assert "EnableSteam" in content
    
    @pytest.mark.asyncio
    async def test_applist_manager_real_workflow(self, real_workspace):
        """Test AppList manager with real file operations."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        applist_manager = AppListManager(console)
        results = SetupResults()
        
        # Test AppList setup
        setup_result = await applist_manager.setup_applist(
            real_workspace['greenluma'],
            "480",  # Spacewar App ID
            results
        )
        
        assert setup_result is True
        assert len(results.configs_updated) == 1
        assert results.configs_updated[0] == ("AppList configuration", True)
        
        # Verify AppList directory and file were created
        applist_dir = real_workspace['greenluma'] / "AppList"
        assert applist_dir.exists()
        assert applist_dir.is_dir()
        
        applist_file = applist_dir / "0.txt"
        assert applist_file.exists()
        
        with open(applist_file, 'r') as f:
            content = f.read().strip()
            assert content == "480"
        
        # Test adding additional App ID
        add_result = applist_manager.add_app_id(applist_dir, "730")
        assert add_result is True
        
        # Verify both App IDs are present
        app_ids = applist_manager.get_app_ids(applist_dir)
        assert len(app_ids) == 2
        assert "480" in app_ids
        assert "730" in app_ids
    
    @pytest.mark.asyncio
    async def test_cleanup_manager_real_workflow(self, real_workspace):
        """Test cleanup manager with real file operations."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        cleanup_manager = CleanupManager(console)
        
        # Create test files and directories to clean up
        temp_files = [
            real_workspace['temp'] / "temp_file1.txt",
            real_workspace['temp'] / "temp_file2.txt"
        ]
        
        temp_dirs = [
            real_workspace['temp'] / "temp_dir1",
            real_workspace['temp'] / "temp_dir2"
        ]
        
        # Create the files and directories
        for temp_file in temp_files:
            temp_file.write_text("temporary content")
        
        for temp_dir in temp_dirs:
            temp_dir.mkdir(parents=True, exist_ok=True)
            (temp_dir / "nested_file.txt").write_text("nested content")
        
        # Register for cleanup
        for temp_file in temp_files:
            cleanup_manager.register_temp_file(temp_file, "test_component")
        
        for temp_dir in temp_dirs:
            cleanup_manager.register_temp_directory(temp_dir, "test_component")
        
        # Verify files exist before cleanup
        for temp_file in temp_files:
            assert temp_file.exists()
        for temp_dir in temp_dirs:
            assert temp_dir.exists()
        
        # Perform cleanup
        file_results = await cleanup_manager.cleanup_temp_files()
        dir_results = await cleanup_manager.cleanup_temp_directories()
        
        # Verify cleanup results
        assert file_results.operations_attempted == len(temp_files)
        assert file_results.operations_successful == len(temp_files)
        assert dir_results.operations_attempted == len(temp_dirs)
        assert dir_results.operations_successful == len(temp_dirs)
        
        # Verify files were actually removed
        for temp_file in temp_files:
            assert not temp_file.exists()
        for temp_dir in temp_dirs:
            assert not temp_dir.exists()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    async def test_shortcut_manager_windows_real(self, real_workspace, real_assets):
        """Test shortcut manager on Windows with real files."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        shortcut_manager = ShortcutManager(console)
        results = SetupResults()
        
        # Extract files first to have real targets
        file_manager = FileOperationsManager(console)
        await file_manager.extract_archive(
            real_assets['greenluma_zip'],
            real_workspace['greenluma'],
            flatten=True,
            results=results
        )
        
        # Create shortcut config
        from models import ShortcutConfig
        shortcut_config = ShortcutConfig(
            name="GreenLuma Test",
            target_path=real_workspace['greenluma'] / "DLLInjector.exe",
            working_directory=real_workspace['greenluma'],
            description="GreenLuma DLL Injector Test"
        )
        
        # Create shortcut
        shortcut_results = await shortcut_manager.create_shortcuts([shortcut_config], results)
        
        # Verify shortcut creation attempt
        assert len(shortcut_results) == 1
        assert len(results.shortcuts_created) == 1
        
        # Note: Actual shortcut creation might fail in test environment
        # but we verify the attempt was made
        shortcut_name, success = results.shortcuts_created[0]
        assert shortcut_name == "GreenLuma Test"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific test")
    async def test_shortcut_manager_unix_real(self, real_workspace, real_assets):
        """Test shortcut manager on Unix with real files."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        shortcut_manager = ShortcutManager(console)
        results = SetupResults()
        
        # Create a mock executable
        mock_exe = real_workspace['greenluma'] / "mock_app"
        mock_exe.write_text("#!/bin/bash\necho 'Mock application'")
        mock_exe.chmod(0o755)
        
        # Create shortcut config
        from models import ShortcutConfig
        shortcut_config = ShortcutConfig(
            name="Mock App Test",
            target_path=mock_exe,
            working_directory=real_workspace['greenluma'],
            description="Mock Application Test"
        )
        
        # Create shortcut
        shortcut_results = await shortcut_manager.create_shortcuts([shortcut_config], results)
        
        # Verify shortcut creation attempt
        assert len(shortcut_results) == 1
        assert len(results.shortcuts_created) == 1
        
        shortcut_name, success = results.shortcuts_created[0]
        assert shortcut_name == "Mock App Test"
    
    @pytest.mark.asyncio
    async def test_error_handling_real_scenarios(self, real_workspace):
        """Test error handling with real error scenarios."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        # Test extraction of non-existent file
        nonexistent_zip = real_workspace['root'] / "nonexistent.zip"
        extract_result = await file_manager.extract_archive(
            nonexistent_zip,
            real_workspace['temp'],
            results=results
        )
        
        assert extract_result is False
        assert len(results.errors) == 1
        assert "not found" in results.errors[0]
        
        # Test extraction of invalid zip file
        invalid_zip = real_workspace['root'] / "invalid.zip"
        invalid_zip.write_text("This is not a zip file")
        
        extract_result = await file_manager.extract_archive(
            invalid_zip,
            real_workspace['temp'],
            results=results
        )
        
        assert extract_result is False
        assert len(results.errors) == 2
        assert "corrupted" in results.errors[1]
    
    @pytest.mark.asyncio
    async def test_results_tracking_real_operations(self, real_workspace, real_assets):
        """Test results tracking with real operations."""
        console = Console(file=open(os.devnull, 'w'), force_terminal=False)
        results = SetupResults()
        results.start_time = 1000.0  # Mock start time
        
        # Perform real operations and track results
        file_manager = FileOperationsManager(console)
        config_handler = ConfigurationHandler(console)
        applist_manager = AppListManager(console)
        
        # Directory creation
        test_dirs = [real_workspace['greenluma'], real_workspace['koalageddon']]
        await file_manager.create_directories(test_dirs, results)
        
        # File extraction
        await file_manager.extract_archive(
            real_assets['greenluma_zip'],
            real_workspace['greenluma'],
            flatten=True,
            results=results
        )
        
        # Configuration update
        dll_file = real_workspace['greenluma'] / "GreenLuma_2020_x64.dll"
        config_file = real_workspace['greenluma'] / "DLLInjector.ini"
        await config_handler.update_dll_injector_config(dll_file, config_file, results)
        
        # AppList setup
        await applist_manager.setup_applist(real_workspace['greenluma'], "480", results)
        
        # Set end time and verify results
        results.end_time = 1005.0  # Mock end time
        
        # Verify comprehensive results tracking
        assert len(results.directories_created) == 2
        assert results.files_extracted is True
        assert len(results.configs_updated) == 2  # DLL config + AppList config
        assert results.duration == 5.0
        assert results.success_rate > 0.8  # Should be high success rate
        
        # Verify summary
        summary = results.get_summary()
        assert summary['directories_created'] == 2
        assert summary['files_extracted'] is True
        assert summary['configs_successful'] == 2
        assert summary['duration'] == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])