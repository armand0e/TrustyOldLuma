#!/usr/bin/env python3
"""Test script for UIManager functionality."""

import sys
import time
from src.ui_manager import UIManager


def test_ui_manager():
    """Test all UIManager methods."""
    ui = UIManager()
    
    print("Testing UIManager implementation...")
    
    # Test welcome screen
    print("\n1. Testing welcome screen...")
    ui.show_welcome_screen()
    time.sleep(2)
    
    # Test info message
    print("\n2. Testing info message...")
    ui.display_info("This is an information message")
    time.sleep(1)
    
    # Test success message
    print("\n3. Testing success message...")
    ui.display_success("Operation completed successfully")
    time.sleep(1)
    
    # Test warning message
    print("\n4. Testing warning message...")
    ui.display_warning("This is a warning message")
    time.sleep(1)
    
    # Test error message with suggestions
    print("\n5. Testing error message...")
    ui.display_error(
        "Failed to access file", 
        ["Check file permissions", "Ensure file exists", "Run as administrator"]
    )
    time.sleep(2)
    
    # Test custom panel
    print("\n6. Testing custom panel...")
    panel = ui.create_panel(
        "This is a custom panel with blue styling",
        "Custom Panel",
        "blue"
    )
    ui.console.print(panel)
    time.sleep(1)
    
    # Test admin phase panel
    print("\n7. Testing admin phase panel...")
    ui.show_admin_phase_panel([
        "✅ Checking administrator privileges",
        "⏳ Adding Windows Security exclusions...",
        "   • GreenLuma folder: Documents\\GreenLuma",
        "   • Koalageddon folder: AppData\\Local\\Programs\\...",
        "⏳ Creating required directories..."
    ])
    time.sleep(2)
    
    # Test progress bar
    print("\n8. Testing progress bar...")
    with ui.show_progress_bar("Extracting files", 100) as progress:
        task = progress.add_task("Extracting GreenLuma files...", total=100)
        for i in range(101):
            progress.update(task, advance=1)
            time.sleep(0.02)
    
    # Test status spinner
    print("\n9. Testing status spinner...")
    with ui.show_status_spinner("Processing files..."):
        time.sleep(3)
    
    # Test completion summary
    print("\n10. Testing completion summary...")
    ui.show_completion_summary([
        "Windows Security exclusions added",
        "GreenLuma files extracted and configured",
        "Koalageddon downloaded and installed",
        "Desktop shortcuts created",
        "Configuration files updated"
    ])
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    test_ui_manager()