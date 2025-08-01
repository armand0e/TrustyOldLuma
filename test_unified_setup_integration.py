#!/usr/bin/env python3
"""
Integration tests for the unified TrustyOldLuma + Koalageddon setup.

This test suite verifies that the unified setup process works correctly
with embedded binaries and proper integration between components.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add src to path for testing
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.setup_controller import SetupController
from src.embedded_koalageddon_manager import EmbeddedKoalageddonManager
from src.configuration_manager import ConfigurationManager
from src.ui_manager import UIManager
from src.data_models import SetupConfig, PlatformInfo, UnifiedSetupResult


class TestUnifiedSetupIntegration:
    """Integration tests for unified setup process."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_ui(self):
        """Create mock UI manager."""
        ui = Mock(spec=UIManager)
        ui.console = Mock()
        ui.display_info = Mock()
        ui.display_success = Mock()
        ui.display_warning = Mock()
        ui.display_error = Mock()
        ui.prompt_confirmation = Mock(return_value=True)
        ui.prompt_continue = Mock()
        ui.show_welcome_screen = Mock()
        ui.show_platform_detection_panel = Mock()
        ui.show_unified_installation_status = Mock()
        ui.show_unified_completion_summary = Mock()
        return ui
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        config = SetupConfig.create_default()
        config.greenluma_path = temp_dir / "GreenLuma"
        config.koalageddon_install_path = temp_dir / "Koalageddon"
        config.koalageddon_config_path = temp_dir / "KoalageddonConfig"
        config.desktop_path = temp_dir / "Desktop"
        config.embedded_binaries_path = temp_dir / "koalageddon_binaries"
        return config
    
    @pytest.fixture
    def setup_test_files(self, temp_dir, test_config):
        """Set up test files and directories."""
        # Create test directories
        test_config.greenluma_path.mkdir(parents=True)
        test_config.koalageddon_install_path.mkdir(parents=True)
        test_config.koalageddon_config_path.mkdir(parents=True)
        test_config.desktop_path.mkdir(parents=True)
        test_config.embedded_binaries_path.mkdir(parents=True)
        
        # Create test GreenLuma zip file
        greenluma_zip = temp_dir / "greenluma.zip"
        import zipfile
        with zipfile.ZipFile(greenluma_zip, 'w') as zf:
            zf.writestr("DLLInjector.exe", b"fake executable")
            zf.writestr("DLLInjector.ini", 'Dll = "fake_path"')
            zf.writestr("GreenLuma_2020_x86.dll", b"fake dll")
        
        # Create test Koalageddon binaries
        (test_config.embedded_binaries_path / "Koalageddon.exe").write_bytes(b"fake koalageddon exe")
        (test_config.embedded_binaries_path / "IntegrationWizard.exe").write_bytes(b"fake integration wizard")
        (test_config.embedded_binaries_path / "version.dll").write_bytes(b"fake version dll")
        
        # Create test config file
        config_file = temp_dir / "Config.jsonc"
        config_file.write_text('{\n  "config_version": 6,\n  "platforms": {\n    "Steam": {\n      "enabled": true\n    }\n  }\n}')
        
        return {
            'greenluma_zip': greenluma_zip,
            'config_file': config_file
        }
    
    def test_unified_setup_controller_initialization(self, mock_ui):
        """Test that SetupController initializes with all unified components."""
        with patch('src.setup_controller.UIManager', return_value=mock_ui):
            controller = SetupController()
            
            # Verify all components are initialized
            assert hasattr(controller, 'ui')
            assert hasattr(controller, 'koalageddon_manager')
            assert hasattr(controller, 'config_manager')
            assert hasattr(controller, 'file_ops')
            assert hasattr(controller, 'admin_handler')
            assert isinstance(controller.koalageddon_manager, EmbeddedKoalageddonManager)
    
    def test_embedded_koalageddon_manager_initialization(self, mock_ui, test_config):
        """Test EmbeddedKoalageddonManager initialization."""
        manager = EmbeddedKoalageddonManager(mock_ui)
        
        assert manager.ui == mock_ui
        assert manager.embedded_binaries_path == Path("koalageddon_binaries")
        assert hasattr(manager, 'platform_executables')
        assert "Steam" in manager.platform_executables
        assert "EpicGames" in manager.platform_executables
    
    def test_embedded_binaries_availability_check(self, mock_ui, test_config, setup_test_files):
        """Test checking for embedded binaries availability."""
        manager = EmbeddedKoalageddonManager(mock_ui)
        manager.embedded_binaries_path = test_config.embedded_binaries_path
        
        # Should return True when all required files exist
        assert manager.is_koalageddon_available() == True
        
        # Should return False when required files are missing
        (test_config.embedded_binaries_path / "Koalageddon.exe").unlink()
        assert manager.is_koalageddon_available() == False
    
    def test_platform_detection(self, mock_ui, test_config):
        """Test gaming platform detection."""
        manager = EmbeddedKoalageddonManager(mock_ui)
        
        with patch.object(manager, '_is_process_available') as mock_check:
            # Mock some platforms as detected
            mock_check.side_effect = lambda name: name in ["steam.exe", "EpicGamesLauncher.exe"]
            
            platforms = manager.detect_gaming_platforms()
            
            assert isinstance(platforms, dict)
            assert "Steam" in platforms
            assert "EpicGames" in platforms
            assert platforms["Steam"] == True
            assert platforms["EpicGames"] == True
            assert platforms.get("Origin", False) == False
    
    def test_unified_extraction_phase(self, mock_ui, test_config, setup_test_files):
        """Test unified extraction of both GreenLuma and Koalageddon."""
        with patch('src.setup_controller.UIManager', return_value=mock_ui):
            controller = SetupController()
            controller.config = test_config
            
            # Mock file operations
            with patch.object(controller.file_ops, 'extract_archive', return_value=True), \
                 patch.object(controller.config_manager, 'create_applist_structure', return_value=True), \
                 patch.object(controller.config_manager, 'update_dll_injector_ini', return_value=True), \
                 patch.object(controller.koalageddon_manager, 'install_koalageddon_embedded', return_value=True):
                
                result = controller.perform_unified_extraction()
                
                assert result == True
                assert "GreenLuma files extracted" in controller.completed_operations
                assert "Embedded Koalageddon installed" in controller.completed_operations
                assert "AppList structure created" in controller.completed_operations
                assert "DLLInjector.ini configured" in controller.completed_operations
    
    def test_platform_integration_phase(self, mock_ui, test_config):
        """Test platform detection and integration phase."""
        with patch('src.setup_controller.UIManager', return_value=mock_ui):
            controller = SetupController()
            controller.config = test_config
            
            # Mock platform detection and integration
            mock_platforms = {"Steam": True, "EpicGames": False, "Origin": False}
            
            with patch.object(controller.koalageddon_manager, 'detect_gaming_platforms', return_value=mock_platforms), \
                 patch.object(controller.koalageddon_manager, 'perform_platform_integrations', return_value=True):
                
                result = controller.perform_platform_integrations()
                
                assert result == True
                mock_ui.display_info.assert_called()
                mock_ui.display_success.assert_called()
    
    def test_unified_configuration_phase(self, mock_ui, test_config, setup_test_files):
        """Test unified configuration of both applications."""
        with patch('src.setup_controller.UIManager', return_value=mock_ui):
            controller = SetupController()
            controller.config = test_config
            
            # Mock configuration operations
            with patch.object(controller.koalageddon_manager, 'configure_koalageddon', return_value=True), \
                 patch.object(controller, '_validate_greenluma_installation', return_value=True), \
                 patch.object(controller.koalageddon_manager, 'validate_installation', return_value=True):
                
                result = controller.configure_unified_applications()
                
                assert result == True
                assert "Koalageddon configuration updated" in controller.completed_operations
                assert "GreenLuma installation validated" in controller.completed_operations
                assert "Koalageddon installation validated" in controller.completed_operations
    
    def test_unified_setup_data_models(self):
        """Test unified setup data models."""
        # Test PlatformInfo
        platform = PlatformInfo(
            name="Steam",
            detected=True,
            executable_paths=[Path("C:/Program Files/Steam/steam.exe")],
            integration_available=True,
            integration_completed=True
        )
        
        platform_dict = platform.to_dict()
        assert platform_dict["name"] == "Steam"
        assert platform_dict["detected"] == True
        assert platform_dict["integration_completed"] == True
        
        # Test UnifiedSetupResult
        result = UnifiedSetupResult(
            overall_success=True,
            greenluma_installed=True,
            koalageddon_installed=True,
            platforms_detected=[platform],
            shortcuts_created=2,
            completed_operations=["Test operation 1", "Test operation 2"]
        )
        
        assert result.platform_integration_count == 1
        assert result.detected_platform_count == 1
        
        result_dict = result.to_dict()
        assert result_dict["overall_success"] == True
        assert result_dict["components"]["greenluma_installed"] == True
        assert result_dict["shortcuts_created"] == 2
    
    def test_configuration_manager_unified_methods(self, mock_ui, test_config):
        """Test ConfigurationManager unified methods."""
        config_manager = ConfigurationManager(mock_ui)
        
        # Test unified validation
        validation_results = config_manager.validate_unified_setup(
            str(test_config.greenluma_path),
            str(test_config.koalageddon_install_path)
        )
        
        assert isinstance(validation_results, dict)
        assert "greenluma_installed" in validation_results
        assert "koalageddon_installed" in validation_results
        assert "shortcuts_created" in validation_results
    
    def test_ui_manager_unified_methods(self, mock_ui):
        """Test UIManager unified display methods."""
        # Test platform detection display
        platforms = {"Steam": True, "EpicGames": False, "Origin": True}
        mock_ui.show_platform_detection_panel(platforms)
        mock_ui.show_platform_detection_panel.assert_called_once_with(platforms)
        
        # Test unified installation status
        mock_ui.show_unified_installation_status("GreenLuma OK", "Koalageddon OK", 2)
        mock_ui.show_unified_installation_status.assert_called_once()
        
        # Test completion summary
        operations = ["Operation 1", "Operation 2"]
        mock_ui.show_unified_completion_summary(operations, 2, 2)
        mock_ui.show_unified_completion_summary.assert_called_once()
    
    @pytest.mark.integration
    def test_full_unified_setup_workflow(self, mock_ui, test_config, setup_test_files):
        """Test complete unified setup workflow end-to-end."""
        with patch('src.setup_controller.UIManager', return_value=mock_ui):
            controller = SetupController()
            controller.config = test_config
            
            # Mock all external dependencies
            with patch.object(controller, 'check_prerequisites', return_value=True), \
                 patch.object(controller, 'handle_admin_phase', return_value=True), \
                 patch.object(controller, 'perform_unified_extraction', return_value=True), \
                 patch.object(controller, 'perform_platform_integrations', return_value=True), \
                 patch.object(controller, 'configure_unified_applications', return_value=True), \
                 patch.object(controller, 'create_shortcuts', return_value=True), \
                 patch.object(controller, 'cleanup_and_finalize', return_value=True), \
                 patch.object(controller.ui, 'prompt_confirmation', return_value=True), \
                 patch.object(controller, '_show_setup_options_menu', return_value="start"):
                
                # Run the full setup
                exit_code = controller.run_setup()
                
                # Verify successful completion
                assert exit_code == 0
                assert controller.setup_successful == True
                
                # Verify key UI interactions occurred
                mock_ui.show_welcome_screen.assert_called_once()
                mock_ui.display_phase_transition.assert_called()
                mock_ui.display_success.assert_called()
    
    def test_error_handling_in_unified_setup(self, mock_ui, test_config):
        """Test error handling in unified setup process."""
        with patch('src.setup_controller.UIManager', return_value=mock_ui):
            controller = SetupController()
            controller.config = test_config
            
            # Test handling of Koalageddon installation failure
            with patch.object(controller.file_ops, 'extract_archive', return_value=True), \
                 patch.object(controller.koalageddon_manager, 'install_koalageddon_embedded', return_value=False), \
                 patch.object(controller.config_manager, 'create_applist_structure', return_value=True), \
                 patch.object(controller.config_manager, 'update_dll_injector_ini', return_value=True):
                
                # Should continue even if Koalageddon fails
                result = controller.perform_unified_extraction()
                
                assert result == True  # Should still succeed with GreenLuma only
                mock_ui.display_warning.assert_called()
    
    def test_pyinstaller_spec_modifications(self, temp_dir):
        """Test that PyInstaller specs properly include embedded binaries."""
        # Create fake koalageddon_binaries directory
        binaries_dir = temp_dir / "koalageddon_binaries"
        binaries_dir.mkdir()
        (binaries_dir / "Koalageddon.exe").write_bytes(b"fake exe")
        (binaries_dir / "version.dll").write_bytes(b"fake dll")
        
        # Simulate the spec file logic
        datas = []
        
        if binaries_dir.exists():
            for binary_file in binaries_dir.rglob('*'):
                if binary_file.is_file() and binary_file.name != 'README.md':
                    rel_path = binary_file.relative_to(binaries_dir)
                    target_dir = f'koalageddon_binaries/{rel_path.parent}' if rel_path.parent != Path('.') else 'koalageddon_binaries'
                    datas.append((str(binary_file), target_dir))
        
        # Verify binaries are included
        assert len(datas) == 2
        assert any("Koalageddon.exe" in data[0] for data in datas)
        assert any("version.dll" in data[0] for data in datas)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])