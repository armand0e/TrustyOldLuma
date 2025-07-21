"""
Comprehensive integration tests for the Gaming Setup Tool.

This module tests the complete setup workflow and integration between
all components of the gaming setup tool.
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

from gaming_setup_tool import GamingSetupTool
from models import SetupConfig, SetupResults
from exceptions import GamingSetupError, AdminPrivilegeError, NetworkError


class TestGamingSetupToolIntegration:
    """Integration tests for the complete Gaming Setup Tool workflow."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for integration testing."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'documents': temp_dir / "Documents",
            'greenluma': temp_dir / "Documents" / "GreenLuma",
            'koalageddon': temp_dir / "Koalageddon",
            'temp': temp_dir / "temp",
            'desktop': temp_dir / "Desktop"
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
    def mock_assets(self, temp_workspace):
        """Create mock asset files for testing."""
        assets_dir = temp_workspace['root'] / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Create mock GreenLuma zip
        greenluma_zip = assets_dir / "greenluma.zip"
        with zipfile.ZipFile(greenluma_zip, 'w') as zip_ref:
            zip_ref.writestr("GreenLuma_2020_x64.dll", b"Mock DLL content")
            zip_ref.writestr("DLLInjector.exe", b"Mock executable")
            zip_ref.writestr("DLLInjector.ini", "[Settings]\nDLL=GreenLuma_2020_x64.dll\n")
        
        # Create mock Koalageddon config
        koa_config = assets_dir / "koalageddon.config"
        koa_config.write_text('{"EnableSteam": true, "EnableEpic": true}')
        
        return {
            'greenluma_zip': greenluma_zip,
            'koalageddon_config': koa_config
        }
    
    @pytest.mark.asyncio
    async def test_complete_setup_workflow_success(self, temp_workspace, mock_assets):
        """Test the complete setup workflow with successful execution."""
        # Create GamingSetupTool instance
        tool = GamingSetupTool(verbose=False)
        
        # Mock configuration
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/Koalageddon.exe",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock admin privileges
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute the complete workflow
            await tool.run()
            
            # Verify results
            assert tool.results is not None
            assert isinstance(tool.results, SetupResults)
            assert tool.results.end_time is not None
    
    @pytest.mark.asyncio
    async def test_setup_workflow_with_admin_privilege_failure(self, temp_workspace):
        """Test setup workflow when admin privileges are required but not available."""
        tool = GamingSetupTool(verbose=False)
        
        # Mock admin privilege failure
        with patch.object(tool.admin_manager, 'ensure_admin_privileges', 
                         side_effect=AdminPrivilegeError("Admin privileges required")):
            
            with pytest.raises(GamingSetupError):
                await tool.run()
    
    @pytest.mark.asyncio
    async def test_setup_workflow_with_network_failure(self, temp_workspace, mock_assets):
        """Test setup workflow with network download failure."""
        tool = GamingSetupTool(verbose=False)
        
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/Koalageddon.exe",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock successful operations except download
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=False), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute workflow - should complete but with warnings
            await tool.run()
            
            # Verify that download failure was handled gracefully
            assert tool.results is not None
            assert len(tool.results.warnings) > 0 or len(tool.results.errors) > 0
    
    @pytest.mark.asyncio
    async def test_setup_workflow_partial_success(self, temp_workspace, mock_assets):
        """Test setup workflow with partial success (some operations fail)."""
        tool = GamingSetupTool(verbose=False)
        
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/Koalageddon.exe",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock mixed success/failure scenarios
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=False), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=False), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, False]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Execute workflow
            await tool.run()
            
            # Verify partial success is handled
            assert tool.results is not None
            assert 0.0 < tool.results.success_rate < 1.0
    
    @pytest.mark.asyncio
    async def test_cleanup_on_failure(self, temp_workspace):
        """Test that cleanup is performed when the workflow fails."""
        tool = GamingSetupTool(verbose=False)
        
        # Create some temporary files
        temp_file = temp_workspace['temp'] / "test_file.txt"
        temp_file.write_text("test content")
        
        # Mock failure in the middle of workflow
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', side_effect=Exception("Extraction failed")), \
             patch.object(tool.cleanup_manager, 'cleanup_failed_installation') as mock_cleanup:
            
            # Mock cleanup to return proper result
            from cleanup_manager import CleanupResults
            mock_cleanup.return_value = CleanupResults()
            
            # Execute workflow - should fail and trigger cleanup
            with pytest.raises(Exception, match="Extraction failed"):
                await tool.run()
            
            # Verify cleanup was called
            mock_cleanup.assert_called_once()
    
    def test_manager_initialization(self):
        """Test that all managers are properly initialized."""
        tool = GamingSetupTool(verbose=False)
        
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
    
    def test_configuration_loading(self, temp_workspace):
        """Test configuration loading and validation."""
        tool = GamingSetupTool(verbose=True)
        
        # Test that configuration can be loaded
        assert tool.config is not None
        assert isinstance(tool.config, SetupConfig)
        assert tool.config.verbose_logging is True
    
    @pytest.mark.asyncio
    async def test_results_tracking(self, temp_workspace, mock_assets):
        """Test that results are properly tracked throughout the workflow."""
        tool = GamingSetupTool(verbose=False)
        
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/Koalageddon.exe",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock all operations to track results
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions') as mock_exclusions, \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Configure mock to properly update results
            async def mock_add_exclusions(paths, results):
                for path in paths:
                    results.exclusions_added.append((path, True))
            
            mock_exclusions.side_effect = mock_add_exclusions
            
            # Execute workflow
            await tool.run()
            
            # Verify results tracking
            assert tool.results is not None
            assert tool.results.start_time is not None
            assert tool.results.end_time is not None
            assert tool.results.duration is not None
            assert tool.results.success_rate >= 0.0


class TestGamingSetupToolErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_critical_error_handling(self):
        """Test handling of critical errors that should stop execution."""
        tool = GamingSetupTool(verbose=False)
        
        # Mock critical error
        with patch.object(tool.admin_manager, 'ensure_admin_privileges', 
                         side_effect=AdminPrivilegeError("Critical admin error")):
            
            with pytest.raises(GamingSetupError):
                await tool.run()
    
    @pytest.mark.asyncio
    async def test_recoverable_error_handling(self, temp_workspace):
        """Test handling of recoverable errors that allow continuation."""
        tool = GamingSetupTool(verbose=False)
        
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/Koalageddon.exe",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock recoverable error in one operation
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=False), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Should complete despite one failure
            await tool.run()
            
            # Verify error was recorded but execution continued
            assert tool.results is not None
            assert len(tool.results.errors) > 0 or len(tool.results.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, temp_workspace):
        """Test network error retry mechanisms."""
        tool = GamingSetupTool(verbose=False)
        
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/Koalageddon.exe",
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
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', side_effect=mock_download), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()):
            
            # Should eventually succeed after retries
            await tool.run()
            
            # Verify successful completion
            assert tool.results is not None
            assert tool.results.success_rate > 0.5


class TestGamingSetupToolPlatformSpecific:
    """Test platform-specific functionality."""
    
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_windows_specific_initialization(self):
        """Test Windows-specific initialization."""
        tool = GamingSetupTool(verbose=False)
        
        # Verify Windows-specific managers are properly configured
        assert tool.admin_manager.is_windows is True
        assert tool.security_manager._is_windows is True
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific test")
    def test_unix_specific_initialization(self):
        """Test Unix-specific initialization."""
        tool = GamingSetupTool(verbose=False)
        
        # Verify Unix-specific behavior
        assert tool.admin_manager.is_windows is False
        assert tool.security_manager._is_windows is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])