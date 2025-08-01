"""Integration test for AdminHandler with UIManager."""

import pytest
from unittest.mock import patch, Mock
from src.admin_handler import AdminHandler
from src.data_models import OperationResult
from src.ui_manager import UIManager
from io import StringIO
from rich.console import Console


class TestAdminIntegration:
    """Integration tests for AdminHandler with UIManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create UIManager with StringIO console for testing
        self.console = Console(file=StringIO(), width=80)
        self.ui_manager = UIManager(console=self.console)
        self.admin_handler = AdminHandler()
    
    @patch.object(AdminHandler, 'is_admin')
    def test_admin_phase_display_no_admin(self, mock_is_admin):
        """Test admin phase display when user is not admin."""
        mock_is_admin.return_value = False
        
        # Display admin phase panel
        status_messages = [
            "❌ Checking administrator privileges",
            "⚠️  Administrator privileges required"
        ]
        
        self.ui_manager.show_admin_phase_panel(status_messages)
        
        # Get console output
        output = self.console.file.getvalue()
        
        # Verify admin panel is displayed
        assert "Administrator Setup" in output
        assert "❌ Checking administrator privileges" in output
        assert "⚠️  Administrator privileges required" in output
    
    @patch.object(AdminHandler, 'is_admin')
    @patch.object(AdminHandler, 'add_security_exclusions')
    @patch.object(AdminHandler, 'create_directories_as_admin')
    def test_admin_phase_display_with_admin(self, mock_create_dirs, mock_add_exclusions, mock_is_admin):
        """Test admin phase display when user has admin privileges."""
        mock_is_admin.return_value = True
        mock_add_exclusions.return_value = OperationResult(
            success=True,
            message="Successfully added security exclusions"
        )
        mock_create_dirs.return_value = OperationResult(
            success=True,
            message="Successfully created directories"
        )
        
        # Simulate admin operations
        exclusion_paths = self.admin_handler.get_common_exclusion_paths()
        admin_dirs = self.admin_handler.get_common_admin_directories()
        
        # Display admin phase panel
        status_messages = [
            "✅ Checking administrator privileges",
            "⏳ Adding Windows Security exclusions...",
            f"   • {len(exclusion_paths)} paths to exclude",
            "⏳ Creating required directories...",
            f"   • {len(admin_dirs)} directories to create"
        ]
        
        self.ui_manager.show_admin_phase_panel(status_messages)
        
        # Get console output
        output = self.console.file.getvalue()
        
        # Verify admin panel is displayed with progress
        assert "Administrator Setup" in output
        assert "✅ Checking administrator privileges" in output
        assert "⏳ Adding Windows Security exclusions" in output
        assert "⏳ Creating required directories" in output
    
    @patch.object(AdminHandler, 'add_security_exclusions')
    def test_error_display_integration(self, mock_add_exclusions):
        """Test error display integration with AdminHandler."""
        # Mock a failed security exclusion operation
        mock_add_exclusions.return_value = OperationResult(
            success=False,
            message="Failed to add security exclusions",
            details="Windows Defender is not accessible",
            suggestions=[
                "Check if Windows Defender is running",
                "Try adding exclusions manually in Windows Security",
                "Verify administrator privileges"
            ]
        )
        
        # Perform the operation
        result = self.admin_handler.add_security_exclusions(["/test/path"])
        
        # Display the error using UIManager
        self.ui_manager.display_error(result.message, result.suggestions)
        
        # Get console output
        output = self.console.file.getvalue()
        
        # Verify error is displayed properly
        assert "Error" in output
        assert "Failed to add security exclusions" in output
        assert "Check if Windows Defender is running" in output
        assert "Try adding exclusions manually" in output
        assert "Verify administrator privileges" in output
    
    @patch.object(AdminHandler, 'create_directories_as_admin')
    def test_success_display_integration(self, mock_create_dirs):
        """Test success display integration with AdminHandler."""
        # Mock a successful directory creation operation
        mock_create_dirs.return_value = OperationResult(
            success=True,
            message="Successfully created 4 directories",
            details="Created: Documents\\GreenLuma, AppData\\Local\\Programs\\Koalageddon"
        )
        
        # Perform the operation
        result = self.admin_handler.create_directories_as_admin(["/test/path1", "/test/path2"])
        
        # Display the success using UIManager
        self.ui_manager.display_success(result.message)
        
        # Get console output
        output = self.console.file.getvalue()
        
        # Verify success is displayed properly
        assert "Success" in output
        assert "Successfully created 4 directories" in output
        assert "✅" in output
    
    def test_common_paths_integration(self):
        """Test that common paths are properly formatted for display."""
        exclusion_paths = self.admin_handler.get_common_exclusion_paths()
        admin_dirs = self.admin_handler.get_common_admin_directories()
        
        # Verify we have the expected number of paths
        assert len(exclusion_paths) == 3
        assert len(admin_dirs) == 4
        
        # Verify paths contain expected components
        assert any("GreenLuma" in path for path in exclusion_paths)
        assert any("Koalageddon" in path for path in exclusion_paths)
        assert any("GreenLuma" in path for path in admin_dirs)
        assert any("Koalageddon" in path for path in admin_dirs)
        
        # Test displaying paths in a panel
        paths_content = "Exclusion paths:\n"
        for path in exclusion_paths:
            paths_content += f"• {path}\n"
        
        panel = self.ui_manager.create_panel(paths_content, "Security Exclusions", "yellow")
        self.ui_manager.console.print(panel)
        
        # Get console output
        output = self.console.file.getvalue()
        
        # Verify paths are displayed in panel
        assert "Security Exclusions" in output
        assert "Exclusion paths:" in output


if __name__ == "__main__":
    pytest.main([__file__])