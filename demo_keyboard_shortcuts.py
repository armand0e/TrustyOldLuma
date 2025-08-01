#!/usr/bin/env python3
"""Demo script to showcase keyboard shortcuts and navigation improvements."""

import time
from src.ui_manager import UIManager


def demo_keyboard_shortcuts():
    """Demonstrate keyboard shortcuts and navigation features."""
    ui = UIManager()
    
    # Show welcome
    ui.show_welcome_screen()
    
    # Demo 1: Setup options menu
    ui.display_info("Demo 1: Interactive Menu with Keyboard Navigation")
    options = {
        "demo": "Continue with demo",
        "help": "Show help information",
        "exit": "Exit demo"
    }
    
    choice = ui.show_menu("Demo Menu", options)
    if choice == "exit" or choice is None:
        ui.display_info("Demo cancelled by user")
        return
    elif choice == "help":
        ui.show_help_text("This demo shows keyboard shortcuts and navigation features.")
        if not ui.prompt_confirmation("Continue with demo?", default=True):
            return
    
    # Demo 2: Confirmation prompts
    ui.display_info("Demo 2: Confirmation Prompts")
    if ui.prompt_confirmation("Do you want to see progress bar demo?", default=True):
        
        # Demo 3: Cancellable progress bar
        ui.display_info("Demo 3: Cancellable Progress Bar (Press Ctrl+C to cancel)")
        
        cancel_called = False
        def cancel_callback():
            nonlocal cancel_called
            cancel_called = True
            ui.display_warning("Progress cancelled by user!")
        
        with ui.show_progress_with_cancel("Demo Progress", 100, cancel_callback) as progress:
            task = progress.add_task("Processing...", total=100)
            
            for i in range(100):
                if cancel_called or ui.was_interrupted():
                    break
                time.sleep(0.05)  # Simulate work
                progress.update(task, advance=1)
        
        if not cancel_called and not ui.was_interrupted():
            ui.display_success("Progress completed successfully!")
    
    # Demo 4: Phase transitions
    ui.display_info("Demo 4: Phase Transitions with Enter Key Prompts")
    ui.display_phase_transition("Demo Phase 1", "Demo Phase 2")
    ui.display_phase_transition("Demo Phase 2", "Demo Phase 3")
    
    # Demo 5: Scrollable content
    ui.display_info("Demo 5: Scrollable Content Display")
    long_content = "\n".join([
        "Keyboard Shortcuts Available:",
        "",
        "• Ctrl+C: Cancel current operation or exit",
        "• Enter: Continue to next step or confirm",
        "• Numbers (1-9): Select menu options",
        "• Y/N: Confirm or deny prompts",
        "• Arrow keys: Navigate in scrollable content",
        "• Q: Quit pager when viewing long content",
        "",
        "Navigation Features:",
        "",
        "• Interactive menus with numbered options",
        "• Confirmation dialogs with default values",
        "• Cancellable progress bars and operations",
        "• Phase transitions with clear prompts",
        "• Scrollable content for long text",
        "• Graceful shutdown on interruption",
        "",
        "Error Handling:",
        "",
        "• Keyboard interrupts are handled gracefully",
        "• Operations can be cancelled safely",
        "• Cleanup is performed on exit",
        "• User feedback is provided for all actions",
        "",
        "This content demonstrates scrolling when it's longer than the terminal height.",
        "You can use arrow keys to scroll up and down when viewing in the pager.",
        "Press 'q' to quit the pager and return to the main interface.",
        "",
        "Additional lines to make content longer...",
        *[f"Line {i}: This is additional content to demonstrate scrolling" for i in range(20, 50)]
    ])
    
    ui.show_scrollable_content(long_content, "Keyboard Shortcuts Help")
    
    # Demo 6: Choice prompts
    ui.display_info("Demo 6: Choice Prompts")
    demo_choice = ui.prompt_choice(
        "Which demo feature did you like most?",
        ["menu", "progress", "scrolling", "transitions"],
        default="menu"
    )
    
    if demo_choice:
        ui.display_success(f"You selected: {demo_choice}")
    else:
        ui.display_info("No choice selected")
    
    # Final completion
    ui.show_completion_summary([
        "Interactive menu navigation demonstrated",
        "Confirmation prompts tested",
        "Cancellable progress bars shown",
        "Phase transitions displayed",
        "Scrollable content viewed",
        "Choice prompts completed"
    ])
    
    ui.prompt_continue("Press Enter to exit demo...")


if __name__ == "__main__":
    try:
        demo_keyboard_shortcuts()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"Demo error: {e}")