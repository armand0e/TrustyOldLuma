"""
Demo script to showcase the Error Handler functionality.

This script demonstrates the error handler's capabilities including:
- Error categorization
- Rich panel display
- Troubleshooting suggestions
- Error logging
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from src.error_handler import ErrorHandler, create_permission_error, create_network_error


def demo_error_handler():
    """Demonstrate the error handler functionality."""
    console = Console()
    
    console.print("\n[bold blue]🔧 Error Handler Demo[/bold blue]")
    console.print("=" * 50)
    
    # Create error handler
    error_handler = ErrorHandler(console=console)
    
    # Demo 1: Permission Error
    console.print("\n[bold yellow]Demo 1: Permission Error[/bold yellow]")
    try:
        raise PermissionError("Access denied to C:\\Windows\\System32\\config")
    except PermissionError as e:
        error_handler.handle_error(e, context="admin setup phase")
    
    # Demo 2: Network Error
    console.print("\n[bold yellow]Demo 2: Network Error[/bold yellow]")
    try:
        raise ConnectionError("Failed to connect to download server")
    except ConnectionError as e:
        error_handler.handle_error(e, context="downloading Koalageddon")
    
    # Demo 3: Custom Error with Suggestions
    console.print("\n[bold yellow]Demo 3: Custom Error with Suggestions[/bold yellow]")
    try:
        raise ValueError("Invalid configuration in Config.jsonc")
    except ValueError as e:
        custom_suggestions = [
            "Check the JSON syntax in Config.jsonc",
            "Ensure all required fields are present",
            "Try restoring the default configuration"
        ]
        error_handler.handle_error(e, context="configuration loading", 
                                 custom_suggestions=custom_suggestions)
    
    # Demo 4: Warning Display
    console.print("\n[bold yellow]Demo 4: Warning Display[/bold yellow]")
    error_handler.display_warning(
        "Windows Defender may interfere with the setup process",
        suggestions=[
            "Add the setup folder to Windows Defender exclusions",
            "Temporarily disable real-time protection during setup"
        ]
    )
    
    # Demo 5: Critical Error
    console.print("\n[bold yellow]Demo 5: Critical Error[/bold yellow]")
    error_handler.display_critical_error(
        "Unable to create required directories due to insufficient permissions",
        suggestions=[
            "Run the setup as Administrator",
            "Check if the target drive has sufficient space",
            "Ensure antivirus software isn't blocking directory creation"
        ]
    )
    
    # Demo 6: Error Summary
    console.print("\n[bold yellow]Demo 6: Error Summary[/bold yellow]")
    error_handler.display_error_summary()
    
    # Demo 7: Convenience Functions
    console.print("\n[bold yellow]Demo 7: Convenience Error Creation[/bold yellow]")
    
    # Create and display a permission error
    perm_error = create_permission_error(
        "Cannot write to GreenLuma directory", 
        "C:\\Users\\Documents\\GreenLuma"
    )
    error_handler.display_error(perm_error)
    
    # Create and display a network error
    net_error = create_network_error(
        "Download timeout occurred",
        "https://github.com/acidicoala/Koalageddon/releases/latest"
    )
    error_handler.display_error(net_error)
    
    console.print("\n[bold green]✅ Error Handler Demo Complete![/bold green]")
    console.print(f"Check the log file: {error_handler.log_file}")


if __name__ == "__main__":
    demo_error_handler()