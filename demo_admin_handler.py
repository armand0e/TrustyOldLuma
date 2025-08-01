"""Demonstration script for AdminHandler functionality."""

from src.admin_handler import AdminHandler
from src.ui_manager import UIManager


def main():
    """Demonstrate AdminHandler functionality."""
    ui = UIManager()
    admin_handler = AdminHandler()
    
    ui.show_welcome_screen()
    
    # Check admin privileges
    is_admin = admin_handler.is_admin()
    
    if is_admin:
        ui.display_success("Administrator privileges detected")
        
        # Get common paths
        exclusion_paths = admin_handler.get_common_exclusion_paths()
        admin_dirs = admin_handler.get_common_admin_directories()
        
        # Display admin phase panel
        status_messages = [
            "✅ Checking administrator privileges",
            "⏳ Adding Windows Security exclusions...",
            f"   • {len(exclusion_paths)} paths to exclude:",
        ]
        
        for path in exclusion_paths[:2]:  # Show first 2 paths
            status_messages.append(f"     - {path}")
        
        status_messages.extend([
            "⏳ Creating required directories...",
            f"   • {len(admin_dirs)} directories to create:",
        ])
        
        for path in admin_dirs[:2]:  # Show first 2 directories
            status_messages.append(f"     - {path}")
        
        ui.show_admin_phase_panel(status_messages)
        
        # Note: In a real scenario, we would actually perform these operations
        # For demo purposes, we'll just show what would happen
        ui.display_info("Demo mode: Operations would be performed here")
        
    else:
        ui.display_warning("Administrator privileges not detected")
        ui.display_info("In a real setup, elevation would be requested")
        
        # Demonstrate what elevation request would look like
        result = admin_handler.request_elevation()
        if not result.success:
            ui.display_error(result.message, result.suggestions)
    
    ui.display_info("AdminHandler demonstration complete")


if __name__ == "__main__":
    main()