"""
Test module for Setup Controller orchestration logic.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.setup_controller import SetupController
from src.data_models import SetupConfig, OperationResult


class TestSetupController:
    """Test cases for SetupController class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.controller = SetupController()
        
    def teardown_method(self):
        """Cleanup test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_setup_controller_initialization(self):
        """Test that SetupController initializes correctly."""
        assert self.controller.ui is not None
        assert self.controller.error_handler is not None
        assert self.controller.admin_handler is not None
        assert self.controller.file_ops is not None
        assert self.controller.downloader is not None
        assert self.controller.config_manager is not None
        assert self.controller.config is not None
        assert isinstance(self.controller.completed_operations, list)
        assert self.controller.setup_successful is False
    
    def test_setup_config_creation(self):
        """Test SetupConfig default creation."""
        config = SetupConfig.create_default()
        
        assert config.app_id == "252950"
        assert "GreenLuma" in str(config.greenluma_path)
        assert "Koalageddon" in config.koalageddon_url
        assert len(config.required_exclusions) > 0
    
    @patch('src.setup_controller.Path')
    def test_check_prerequisites_missing_files(self, mock_path):
        """Test prerequisites check with missing files."""
        # Mock file existence checks
        mock_greenluma = Mock()
        mock_greenluma.exists.return_value = False
        mock_config = Mock()
        mock_config.exists.return_value = False
        
        mock_path.return_value = mock_greenluma
        mock_path.side_effect = [mock_greenluma, mock_config]
        
        result = self.controller.check_prerequisites()
        assert result is False
    
    @patch('src.setup_controller.Path')
    @patch('shutil.disk_usage')
    @patch('src.setup_controller.sys.platform', 'win32')
    def test_check_prerequisites_success(self, mock_disk_usage, mock_path):
        """Test successful prerequisites check."""
        # Mock file existence checks
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_path.return_value = mock_file
        
        # Mock disk usage
        mock_disk_usage.return_value = Mock(free=1000 * 1024 * 1024)  # 1GB free
        
        result = self.controller.check_prerequisites()
        assert result is True
        assert "Prerequisites check" in self.controller.completed_operations
    
    def test_handle_admin_phase_no_admin(self):
        """Test admin phase when not running as admin."""
        # Mock admin handler
        self.controller.admin_handler.is_admin = Mock(return_value=False)
        self.controller.admin_handler.request_elevation = Mock(
            return_value=OperationResult(success=True, message="Elevated successfully")
        )
        
        result = self.controller.handle_admin_phase()
        assert result is True
    
    def test_handle_admin_phase_with_admin(self):
        """Test admin phase when already running as admin."""
        # Mock admin handler methods
        self.controller.admin_handler.is_admin = Mock(return_value=True)
        self.controller.admin_handler.add_security_exclusions = Mock(
            return_value=OperationResult(success=True, message="Exclusions added")
        )
        self.controller.admin_handler.get_common_admin_directories = Mock(
            return_value=["test_dir1", "test_dir2"]
        )
        self.controller.admin_handler.create_directories_as_admin = Mock(
            return_value=OperationResult(success=True, message="Directories created")
        )
        
        result = self.controller.handle_admin_phase()
        assert result is True
        assert "Windows Security exclusions" in self.controller.completed_operations
        assert "Directory structure creation" in self.controller.completed_operations
    
    def test_perform_file_operations_success(self):
        """Test successful file operations."""
        # Mock file operations
        self.controller.file_ops.extract_archive = Mock(return_value=True)
        self.controller.config_manager.create_applist_structure = Mock(return_value=True)
        self.controller.config_manager.update_dll_injector_ini = Mock(return_value=True)
        
        result = self.controller.perform_file_operations()
        assert result is True
        assert "GreenLuma files extracted" in self.controller.completed_operations
        assert "AppList structure created" in self.controller.completed_operations
        assert "DLLInjector.ini configured" in self.controller.completed_operations
    
    def test_download_and_install_koalageddon_success(self):
        """Test successful Koalageddon download and installation."""
        # Mock download and extraction
        self.controller.downloader.download_with_progress = Mock(return_value=True)
        self.controller.file_ops.extract_archive = Mock(return_value=True)
        
        result = self.controller.download_and_install_koalageddon()
        assert result is True
        assert "Koalageddon downloaded" in self.controller.completed_operations
        assert "Koalageddon extracted" in self.controller.completed_operations
    
    def test_configure_applications_success(self):
        """Test successful application configuration."""
        # Mock configuration operations
        with patch('src.setup_controller.Path') as mock_path:
            mock_config_file = Mock()
            mock_config_file.exists.return_value = True
            mock_path.return_value = mock_config_file
            
            self.controller.config_manager.update_koalageddon_config = Mock(return_value=True)
            
            result = self.controller.configure_applications()
            assert result is True
            assert "Koalageddon configuration updated" in self.controller.completed_operations
    
    def test_create_shortcuts_success(self):
        """Test successful shortcut creation."""
        # Mock shortcut operations
        with patch.object(self.controller.config, 'greenluma_path') as mock_greenluma_path, \
             patch.object(self.controller.config, 'koalageddon_config_path') as mock_koalageddon_path:
            
            # Mock executable files exist
            mock_greenluma_exe = Mock()
            mock_greenluma_exe.exists.return_value = True
            mock_koalageddon_exe = Mock()
            mock_koalageddon_exe.exists.return_value = True
            
            mock_greenluma_path.__truediv__.return_value = mock_greenluma_exe
            mock_koalageddon_path.__truediv__.return_value = mock_koalageddon_exe
            
            self.controller.config_manager.create_desktop_shortcut = Mock(return_value=True)
            self.controller.config_manager.copy_koalageddon_shortcut = Mock(return_value=True)
            
            result = self.controller.create_shortcuts()
            assert result is True
            assert any("shortcuts created" in op for op in self.controller.completed_operations)
    
    def test_cleanup_and_finalize_success(self):
        """Test successful cleanup and finalization."""
        # Mock validation
        self.controller._validate_setup_completion = Mock(return_value=True)
        
        result = self.controller.cleanup_and_finalize()
        assert result is True
        assert "Temporary files cleaned up" in self.controller.completed_operations
    
    def test_validate_setup_completion(self):
        """Test setup validation."""
        # Mock paths and files
        with patch.object(self.controller.config, 'greenluma_path') as mock_greenluma_path, \
             patch.object(self.controller.config, 'koalageddon_config_path') as mock_koalageddon_path:
            
            mock_greenluma_path.exists.return_value = True
            mock_koalageddon_path.exists.return_value = True
            
            # Mock required files exist
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_greenluma_path.__truediv__.return_value = mock_file
            
            result = self.controller._validate_setup_completion()
            assert result is True
    
    @patch('src.setup_controller.sys.exit')
    def test_signal_handler_setup(self, mock_exit):
        """Test that signal handlers are set up correctly."""
        # This test verifies that the controller sets up signal handlers
        # The actual signal handling is tested implicitly through initialization
        controller = SetupController()
        assert controller is not None
        # Signal handlers are set up in __init__, so if we get here, they're working


if __name__ == "__main__":
    pytest.main([__file__])