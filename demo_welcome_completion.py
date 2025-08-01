#!/usr/bin/env python3
"""Demo script to showcase enhanced welcome screen and completion summary displays."""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui_manager import UIManager


def demo_welcome_and_completion():
    """Demonstrate the enhanced welcome screen and completion summary."""
    ui = UIManager()
    
    print("🎬 TrustyOldLuma Setup - Welcome & Completion Demo")
    print("=" * 60)
    
    # Demo 1: Enhanced Welcome Screen
    print("\n1. Enhanced Welcome Screen with Project Branding:")
    print("-" * 50)
    ui.show_welcome_screen()
    
    # Demo 2: Phase Header Display
    print("\n2. Phase Header Display:")
    print("-" * 30)
    ui.show_phase_header(
        "Admin Setup", 
        "Configuring Windows Security exclusions and creating directories", 
        1, 
        5
    )
    
    # Demo 3: Phase Transition Display
    print("\n3. Phase Transition Display:")
    print("-" * 35)
    ui.display_phase_transition(
        "Admin Setup", 
        "File Operations", 
        "1/5 phases complete"
    )
    
    # Demo 4: Setup Progress Overview
    print("\n4. Setup Progress Overview:")
    print("-" * 35)
    ui.show_setup_progress_overview(
        completed_phases=["Welcome", "Admin Setup"],
        current_phase="File Operations",
        remaining_phases=["Download Manager", "Configuration", "Completion"]
    )
    
    # Demo 5: Branded Panels
    print("\n5. Branded Panel Examples:")
    print("-" * 35)
    
    # Info panel
    info_panel = ui.create_branded_panel(
        "This is an informational message with TrustyOldLuma branding.",
        "Information",
        "info"
    )
    ui.console.print(info_panel)
    
    # Success panel
    success_panel = ui.create_branded_panel(
        "Operation completed successfully with enhanced visual feedback.",
        "Success",
        "success"
    )
    ui.console.print(success_panel)
    
    # Admin panel
    admin_panel = ui.create_branded_panel(
        "Administrator privileges required for this operation.",
        "Admin Required",
        "admin"
    )
    ui.console.print(admin_panel)
    
    # Demo 6: Enhanced Completion Summary
    print("\n6. Enhanced Completion Summary:")
    print("-" * 40)
    
    # Simulate successful operations
    successful_operations = [
        "Windows Security exclusions configured",
        "GreenLuma files extracted and configured", 
        "Koalageddon downloaded and installed",
        "Desktop shortcuts created",
        "Configuration files updated"
    ]
    
    # Simulate some minor issues
    failed_operations = [
        "Optional desktop wallpaper download (non-critical)",
        "Automatic browser bookmark creation (skipped)"
    ]
    
    ui.show_completion_summary(successful_operations, failed_operations)
    
    print("\n🎉 Demo completed! The enhanced UI provides:")
    print("   ✅ Rich project branding and visual appeal")
    print("   ✅ Clear phase transitions with progress tracking")
    print("   ✅ Comprehensive completion summary with next steps")
    print("   ✅ GitHub repository promotion and user engagement")
    print("   ✅ Professional visual hierarchy and formatting")


def main():
    """Run the demo."""
    try:
        demo_welcome_and_completion()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user (Ctrl+C)")
        print("Thank you for viewing the TrustyOldLuma UI enhancements!")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)