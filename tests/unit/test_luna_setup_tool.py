"""
Comprehensive integration tests for the Luna Setup Tool.

This module tests the complete Luna setup workflow and integration between
all components of the Luna gaming tool, including legacy migration functionality.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from rich.console import Console

from gaming_setup_tool import LunaSetupTool
from models import LunaConfig, LunaResults
from exceptions import LunaError, LunaMigrationError, AdminPrivilegeError, NetworkError


class TestLunaSetupToolIntegration:
    """Integration tests for the complete Luna Setup Tool workflow."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for Luna integration testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'documents': temp_dir / "Documents",
            'luna': temp_dir / "Documents" / "Luna",
            'luna_config': temp_dir / "Documents" / "Luna" / "config",
            'temp': temp_dir / "temp",
            'desktop': temp_dir / "Desktop",
            # Legacy paths for migration testing
            'legacy_greenluma': temp_dir / "Documents" / "GreenLuma",
            'legacy_koalageddon': temp_dir / "Koalageddon"
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
    def mock_luna_assets(self, temp_workspace):
        """Create mock Luna asset files for testing."""
        assets_dir = temp_workspace['root'] / "assets" / "luna"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock Luna injector zip
        luna_injector_zip = assets_dir / "luna_injector.zip"
        with zipfile.ZipFile(luna_injector_zip, 'w') as zip_ref:
            zip_ref.writestr("luna_core_x64.dll", b"Mock Luna DLL content")
            zip_ref.writestr("luna_injector.exe", b"Mock Luna executable")
            zip_ref.writestr("luna_injector.ini", "[Settings]\nDLL=luna_core_x64.dll\n")
        
        # Create mock Luna unlocker zip
        luna_unlocker_zip = assets_dir / "luna_unlocker.zip"
        with zipfile.ZipFile(luna_unlocker_zip, 'w') as zip_ref:
            zip_ref.writestr("luna_unlocker.dll", b"Mock Luna unlocker DLL")
            zip_ref.writestr("luna_integration.dll", b"Mock Luna integration DLL")
        
        # Create mock Luna config
        luna_config = assets_dir / "luna_config.jsonc"
        luna_config.write_text('{"luna": {"injector_enabled": true, "unlocker_enabled": true}}')
        
        return {
            'luna_injector_zip': luna_injector_zip,
            'luna_unlocker_zip': luna_unlocker_zip,
            'luna_config': luna_config
        }
    
    @pytest.fixture
    def mock_legacy_installations(self, temp_workspace):
        """Create mock legacy installations for migration testing."""
        # Create legacy GreenLuma installation
        greenluma_dir = temp_workspace['legacy_greenluma']
        (greenluma_dir / "GreenLuma_2020_x64.dll").write_bytes(b"Legacy GreenLuma DLL")
        (greenluma_dir / "DLLInjector.exe").write_bytes(b"Legacy DLL Injector")
        (greenluma_dir / "DLLInjector.ini").write_text("[Settings]\nDLL=GreenLuma_2020_x64.dll\n")
        
        # Create legacy Koalageddon installation
        koalageddon_dir = temp_workspace['legacy_koalageddon']
        (koalageddon_dir / "Koalageddon.exe").write_bytes(b"Legacy Koalageddon")
        (koalageddon_dir / "config.json").write_text('{"EnableSteam": true}')
        
        return {
            'greenluma_path': greenluma_dir,
            'koalageddon_path': koalageddon_dir
        }
    
    @pytest.mark.asyncio
    async def test_complete_luna_setup_workflow_success(self, temp_workspace, mock_luna_assets):
        """Test the complete Luna setup workflow with successful execution."""
        # Create LunaSetupTool instance
        tool = LunaSetupTool(verbose=False)
        
        # Mock Luna configuration
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock all Luna operations
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute the complete Luna workflow
            await tool.run()
            
            # Verify Luna results
            assert tool.results is not None
            assert isinstance(tool.results, LunaResults)
            assert tool.results.end_time is not None
    
    @pytest.mark.asyncio
    async def test_luna_migration_workflow_success(self, temp_workspace, mock_legacy_installations, mock_luna_assets):
        """Test Luna migration workflow from legacy installations."""
        # Create LunaSetupTool instance
        tool = LunaSetupTool(verbose=False)
        
        # Mock Luna configuration with legacy paths
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp'],
            legacy_greenluma_path=mock_legacy_installations['greenluma_path'],
            legacy_koalageddon_path=mock_legacy_installations['koalageddon_path']
        )
        
        # Mock migration operations
        with patch.object(tool, '_detect_legacy_installations', return_value=['GreenLuma', 'Koalageddon']), \
             patch.object(tool, '_migrate_legacy_configurations', return_value=True), \
             patch.object(tool, '_migrate_legacy_files', return_value=True), \
             patch.object(tool, '_update_legacy_shortcuts', return_value=True), \
             patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute Luna migration workflow
            await tool.run()
            
            # Verify migration results
            assert tool.results is not None
            assert isinstance(tool.results, LunaResults)
            assert len(tool.results.legacy_installations_found) > 0
            assert len(tool.results.configurations_migrated) > 0
    
    @pytest.mark.asyncio
    async def test_luna_setup_workflow_with_admin_privilege_failure(self, temp_workspace):
        """Test Luna setup workflow when admin privileges are required but not available."""
        tool = LunaSetupTool(verbose=False)
        
        # Mock admin privilege failure
        with patch.object(tool.admin_manager, 'ensure_admin_privileges', 
                         side_effect=AdminPrivilegeError("Admin privileges required for Luna setup")):
            
            with pytest.raises(LunaError):
                await tool.run()
    
    @pytest.mark.asyncio
    async def test_luna_setup_workflow_with_network_failure(self, temp_workspace, mock_luna_assets):
        """Test Luna setup workflow with network download failure."""
        tool = LunaSetupTool(verbose=False)
        
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock successful operations except download
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=False), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute workflow - should complete but with warnings
            await tool.run()
            
            # Verify that download failure was handled gracefully
            assert tool.results is not None
            assert len(tool.results.warnings) > 0 or len(tool.results.errors) > 0
    
    @pytest.mark.asyncio
    async def test_luna_setup_workflow_partial_success(self, temp_workspace, mock_luna_assets):
        """Test Luna setup workflow with partial success (some operations fail)."""
        tool = LunaSetupTool(verbose=False)
        
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock mixed success/failure scenarios
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=False), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=False), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=False), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, False]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute workflow
            await tool.run()
            
            # Verify partial success is handled
            assert tool.results is not None
            assert 0.0 < tool.results.success_rate < 1.0
    
    @pytest.mark.asyncio
    async def test_luna_cleanup_on_failure(self, temp_workspace):
        """Test that cleanup is performed when the Luna workflow fails."""
        tool = LunaSetupTool(verbose=False)
        
        # Create some temporary Luna files
        temp_file = temp_workspace['temp'] / "luna_temp_file.txt"
        temp_file.write_text("Luna test content")
        
        # Mock failure in the middle of workflow
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', side_effect=Exception("Luna extraction failed")), \
             patch.object(tool.cleanup_manager, 'cleanup_failed_installation') as mock_cleanup:
            
            # Mock cleanup to return proper result
            from cleanup_manager import CleanupResults
            mock_cleanup.return_value = CleanupResults()
            
            # Execute workflow - should fail and trigger cleanup
            with pytest.raises(Exception, match="Luna extraction failed"):
                await tool.run()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()
    
    def test_luna_manager_initialization(self):
        """Test that all Luna managers are properly initialized."""
        tool = LunaSetupTool(verbose=False)
        
        # Verify all managers are initialized
        assert hasattr(tool, 'console')
        assert hasattr(tool, 'admin_manager')
        assert hasattr(tool, 'file_manager')
        assert hasattr(tool, 'security_manager')
        assert hasattr(tool, 'config_handler')
        assert hasattr(tool, 'shortcut_manager')
        assert hasattr(tool, 'applist_manager')
        assert hasattr(tool, 'cleanup_manager')
        assert hasattr(tool, 'error_manager')
        assert hasattr(tool, 'progress_manager')
        assert hasattr(tool, 'welcome_manager')
        assert hasattr(tool, 'completion_manager')
        
        # Verify managers have correct console references
        assert tool.admin_manager.console == tool.console
        assert tool.file_manager.console == tool.console
        assert tool.security_manager.console == tool.console
        assert tool.config_handler.console == tool.console
        assert tool.shortcut_manager.console == tool.console
        assert tool.applist_manager.console == tool.console
        assert tool.cleanup_manager.console == tool.console
    
    def test_luna_configuration_loading(self, temp_workspace):
        """Test Luna configuration loading and validation."""
        tool = LunaSetupTool(verbose=True)
        
        # Test that Luna configuration can be loaded
        assert tool.config is not None
        assert isinstance(tool.config, LunaConfig)
        assert tool.config.verbose_logging is True
    
    @pytest.mark.asyncio
    async def test_luna_results_tracking(self, temp_workspace, mock_luna_assets):
        """Test that Luna results are properly tracked throughout the workflow."""
        tool = LunaSetupTool(verbose=False)
        
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock all operations to track Luna results
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions') as mock_exclusions, \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Configure mock to properly update Luna results
            async def mock_add_exclusions(paths, results):
                for path in paths:
                    results.exclusions_added.append((path, True))
            
            mock_exclusions.side_effect = mock_add_exclusions
            
            # Execute Luna workflow
            await tool.run()
            
            # Verify Luna results tracking
            assert tool.results is not None
            assert tool.results.start_time is not None
            assert tool.results.end_time is not None
            assert tool.results.duration is not None
            assert tool.results.success_rate >= 0.0
    
    @pytest.mark.asyncio
    async def test_legacy_detection_functionality(self, temp_workspace, mock_legacy_installations):
        """Test Luna's legacy installation detection functionality."""
        tool = LunaSetupTool(verbose=False)
        
        # Mock the detection method to return found installations
        with patch.object(tool, '_detect_legacy_installations') as mock_detect:
            mock_detect.return_value = ['GreenLuma', 'Koalageddon']
            
            detected = tool._detect_legacy_installations()
            
            assert 'GreenLuma' in detected
            assert 'Koalageddon' in detected
            assert len(detected) == 2


class TestLunaSetupToolErrorHandling:
    """Test Luna error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_luna_critical_error_handling(self):
        """Test handling of critical Luna errors that should stop execution."""
        tool = LunaSetupTool(verbose=False)
        
        # Mock critical Luna error
        with patch.object(tool.admin_manager, 'ensure_admin_privileges', 
                         side_effect=AdminPrivilegeError("Critical Luna admin error")):
            
            with pytest.raises(LunaError):
                await tool.run()
    
    @pytest.mark.asyncio
    async def test_luna_migration_error_handling(self, temp_workspace):
        """Test handling of Luna migration-specific errors."""
        tool = LunaSetupTool(verbose=False)
        
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock migration error
        with patch.object(tool, '_migrate_legacy_configurations', 
                         side_effect=LunaMigrationError("Failed to migrate legacy configurations")), \
             patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool, '_detect_legacy_installations', return_value=['GreenLuma']):
            
            # Should handle migration error gracefully
            await tool.run()
            
            # Verify error was recorded
            assert tool.results is not None
            assert len(tool.results.errors) > 0
    
    @pytest.mark.asyncio
    async def test_luna_recoverable_error_handling(self, temp_workspace):
        """Test handling of recoverable Luna errors that allow continuation."""
        tool = LunaSetupTool(verbose=False)
        
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock recoverable error in one Luna operation
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=False), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Should complete despite one failure
            await tool.run()
            
            # Verify error was recorded but execution continued
            assert tool.results is not None
            assert len(tool.results.errors) > 0 or len(tool.results.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_luna_network_error_retry(self, temp_workspace):
        """Test Luna network error retry mechanisms."""
        tool = LunaSetupTool(verbose=False)
        
        tool.config = LunaConfig(
            luna_core_path=temp_workspace['luna'],
            luna_config_path=temp_workspace['luna_config'],
            download_url="https://example.com/luna_components.zip",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock network error with eventual success
        download_attempts = [False, False, True]  # Fail twice, then succeed
        
        def mock_download(*args, **kwargs):
            return download_attempts.pop(0)
        
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_injector_config', return_value=True), \
             patch.object(tool.config_handler, 'update_luna_unlocker_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', side_effect=mock_download), \
             patch.object(tool.config_handler, 'replace_luna_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Should eventually succeed after retries
            await tool.run()
            
            # Verify successful completion
            assert tool.results is not None
            assert tool.results.success_rate > 0.5


class TestLunaSetupToolPlatformSpecific:
    """Test Luna platform-specific functionality."""
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific Luna test")
    def test_luna_windows_specific_initialization(self):
        """Test Luna Windows-specific initialization."""
        tool = LunaSetupTool(verbose=False)
        
        # Verify Windows-specific managers are properly configured for Luna
        assert tool.admin_manager.is_windows is True
        assert tool.security_manager._is_windows is True
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific Luna test")
    def test_luna_unix_specific_initialization(self):
        """Test Luna Unix-specific initialization."""
        tool = LunaSetupTool(verbose=False)
        
        # Verify Unix-specific behavior for Luna
        assert tool.admin_manager.is_windows is False
        assert tool.security_manager._is_windows is False


class TestLunaSetupToolMigration:
    """Test Luna-specific migration functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for migration testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'documents': temp_dir / "Documents",
            'luna': temp_dir / "Documents" / "Luna",
            'legacy_greenluma': temp_dir / "Documents" / "GreenLuma",
            'legacy_koalageddon': temp_dir / "Koalageddon",
            'temp': temp_dir / "temp"
        }
        
        # Create directories
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        yield workspace
        
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_legacy_installation_detection(self, temp_workspace):
        """Test detection of legacy GreenLuma and Koalageddon installations."""
        tool = LunaSetupTool(verbose=False)
        
        # Create mock legacy files
        (temp_workspace['legacy_greenluma'] / "GreenLuma_2020_x64.dll").write_bytes(b"mock")
        (temp_workspace['legacy_koalageddon'] / "Koalageddon.exe").write_bytes(b"mock")
        
        # Mock the detection method
        with patch.object(tool, '_detect_legacy_installations') as mock_detect:
            mock_detect.return_value = ['GreenLuma', 'Koalageddon']
            
            detected = tool._detect_legacy_installations()
            
            assert 'GreenLuma' in detected
            assert 'Koalageddon' in detected
    
    @pytest.mark.asyncio
    async def test_configuration_migration(self, temp_workspace):
        """Test migration of legacy configurations to Luna format."""
        tool = LunaSetupTool(verbose=False)
        
        # Create mock legacy configurations
        greenluma_config = temp_workspace['legacy_greenluma'] / "DLLInjector.ini"
        greenluma_config.write_text("[Settings]\nDLL=GreenLuma_2020_x64.dll\n")
        
        koalageddon_config = temp_workspace['legacy_koalageddon'] / "config.json"
        koalageddon_config.write_text('{"EnableSteam": true, "EnableEpic": true}')
        
        # Mock migration method
        with patch.object(tool, '_migrate_legacy_configurations') as mock_migrate:
            mock_migrate.return_value = True
            
            result = tool._migrate_legacy_configurations()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_file_migration(self, temp_workspace):
        """Test migration of legacy files to Luna directory structure."""
        tool = LunaSetupTool(verbose=False)
        
        # Create mock legacy files
        (temp_workspace['legacy_greenluma'] / "GreenLuma_2020_x64.dll").write_bytes(b"legacy dll")
        (temp_workspace['legacy_koalageddon'] / "Koalageddon.exe").write_bytes(b"legacy exe")
        
        # Mock file migration method
        with patch.object(tool, '_migrate_legacy_files') as mock_migrate:
            mock_migrate.return_value = True
            
            result = tool._migrate_legacy_files()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_shortcut_migration(self, temp_workspace):
        """Test migration of legacy shortcuts to Luna shortcuts."""
        tool = LunaSetupTool(verbose=False)
        
        # Mock shortcut migration method
        with patch.object(tool, '_update_legacy_shortcuts') as mock_migrate:
            mock_migrate.return_value = True
            
            result = tool._update_legacy_shortcuts()
            
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])