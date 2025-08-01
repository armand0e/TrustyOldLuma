#!/usr/bin/env python3
"""Test script for enhanced welcome screen and completion summary displays."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui_manager import UIManager
from rich.console import Console
from io import StringIO


def test_welcome_screen():
    """Test the enhanced welcome screen display."""
    print("Testing enhanced welcome screen...")
    
    # Create UI manager with string buffer for testing
    console = Console(file=StringIO(), width=80, legacy_windows=False)
    ui = UIManager(console=console)
    
    # Test welcome screen in non-interactive mode
    ui.show_welcome_screen(interactive=False)
    
    # Get output
    output = console.file.getvalue()
    
    # Verify key elements are present
    assert "TrustyOldLuma Setup" in output
    assert "Professional Edition" in output
    assert "Configure Windows Security exclusions" in output
    assert "https://github.com/armand0e/TrustyOldLuma" in output
    assert "Support the project" in output
    
    print("✅ Welcome screen test passed!")
    return True


def test_completion_summary():
    """Test the enhanced completion summary display."""
    print("Testing enhanced completion summary...")
    
    # Create UI manager with string buffer for testing
    console = Console(file=StringIO(), width=80, legacy_windows=False)
    ui = UIManager(console=console)
    
    # Test completion summary with successful operations in non-interactive mode
    operations = [
        "Windows Security exclusions configured",
        "GreenLuma files extracted and configured",
        "Koalageddon downloaded and installed",
        "Desktop shortcuts created",
        "Configuration files updated"
    ]
    
    failed_operations = ["Optional feature X (non-critical)"]
    
    ui.show_completion_summary(operations, failed_operations, interactive=False)
    
    # Get output
    output = console.file.getvalue()
    
    # Verify key elements are present
    assert "Setup Complete!" in output
    assert "Successfully completed operations" in output
    assert "Windows Security exclusions configured" in output
    assert "Next Steps:" in output
    assert "Launch Koalageddon" in output
    assert "Support TrustyOldLuma" in output
    assert "https://github.com/armand0e/TrustyOldLuma" in output
    assert "Operations with issues" in output
    assert "Optional feature X" in output
    
    print("✅ Completion summary test passed!")
    return True


def test_phase_transitions():
    """Test the enhanced phase transition displays."""
    print("Testing phase transition displays...")
    
    # Create UI manager with string buffer for testing
    console = Console(file=StringIO(), width=80, legacy_windows=False)
    ui = UIManager(console=console)
    
    # Mock the prompt_continue method to avoid blocking
    original_prompt = ui.prompt_continue
    ui.prompt_continue = lambda msg="": True
    
    # Test phase transition
    ui.display_phase_transition("Admin Setup", "File Operations", "3/5 phases complete")
    
    # Get output
    output = console.file.getvalue()
    
    # Restore original method
    ui.prompt_continue = original_prompt
    
    # Verify key elements are present
    assert "Phase Complete: Admin Setup" in output
    assert "Next Phase: File Operations" in output
    assert "3/5 phases complete" in output
    assert "Phase Transition" in output
    
    print("✅ Phase transition test passed!")
    return True


def test_phase_header():
    """Test the phase header display."""
    print("Testing phase header display...")
    
    # Create UI manager with string buffer for testing
    console = Console(file=StringIO(), width=80, legacy_windows=False)
    ui = UIManager(console=console)
    
    # Test phase header
    ui.show_phase_header(
        "Admin Setup", 
        "Configuring Windows Security and creating required directories", 
        2, 
        5
    )
    
    # Get output
    output = console.file.getvalue()
    
    # Verify key elements are present
    assert "Phase 2/5: Admin Setup" in output
    assert "Configuring Windows Security" in output
    assert "Progress:" in output
    assert "2/5" in output
    
    print("✅ Phase header test passed!")
    return True


def test_branded_panel():
    """Test the branded panel creation."""
    print("Testing branded panel creation...")
    
    # Create UI manager
    ui = UIManager()
    
    # Test different panel types
    panel_types = ["info", "success", "error", "warning", "admin", "download", "config", "complete"]
    
    for panel_type in panel_types:
        panel = ui.create_branded_panel(
            f"Test content for {panel_type} panel",
            f"Test {panel_type.title()} Panel",
            panel_type
        )
        
        # Verify panel was created
        assert panel is not None
        assert "TrustyOldLuma" in str(panel.title)
    
    print("✅ Branded panel test passed!")
    return True


def main():
    """Run all tests."""
    print("🧪 Testing enhanced welcome screen and completion summary displays...\n")
    
    tests = [
        test_welcome_screen,
        test_completion_summary,
        test_phase_transitions,
        test_phase_header,
        test_branded_panel
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
            failed += 1
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Welcome screen and completion summary enhancements are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)