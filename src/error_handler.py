"""
Error Handler Module

Provides comprehensive error handling and user guidance with Rich-based UI elements.
Categorizes errors, displays formatted error panels, and provides troubleshooting suggestions.
"""

import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.logging import RichHandler


class ErrorCategory(Enum):
    """Categories of errors that can occur during setup."""
    PERMISSION = "Permission Error"
    NETWORK = "Network Error"
    FILESYSTEM = "File System Error"
    CONFIGURATION = "Configuration Error"
    ADMIN = "Administrator Error"
    DOWNLOAD = "Download Error"
    EXTRACTION = "Extraction Error"
    UNKNOWN = "Unknown Error"


@dataclass
class ErrorInfo:
    """Information about an error occurrence."""
    category: ErrorCategory
    message: str
    details: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    traceback_info: Optional[str] = None


class ErrorHandler:
    """Comprehensive error handler with Rich UI integration and logging."""
    
    def __init__(self, console: Optional[Console] = None, log_file: Optional[Path] = None):
        """
        Initialize the error handler.
        
        Args:
            console: Rich console instance for display
            log_file: Path to log file for error logging
        """
        self.console = console or Console()
        self.log_file = log_file or Path("setup_errors.log")
        self.error_history: List[ErrorInfo] = []
        
        # Setup logging
        self._setup_logging()
        
        # Error suggestion mappings
        self._suggestion_map = self._build_suggestion_map()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration with Rich handler."""
        # Create logger
        self.logger = logging.getLogger("setup_error_handler")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for persistent logging
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Rich handler for console output (optional, for debugging)
        if hasattr(self, '_debug_mode') and self._debug_mode:
            rich_handler = RichHandler(console=self.console, show_path=False)
            rich_handler.setLevel(logging.WARNING)
            self.logger.addHandler(rich_handler)
    
    def _build_suggestion_map(self) -> Dict[ErrorCategory, List[str]]:
        """Build mapping of error categories to common suggestions."""
        return {
            ErrorCategory.PERMISSION: [
                "Run the setup as Administrator (right-click → Run as administrator)",
                "Check if antivirus software is blocking the operation",
                "Ensure you have write permissions to the target directory",
                "Close any applications that might be using the files",
                "Try running from a different location (e.g., Desktop)"
            ],
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Verify that your firewall isn't blocking the download",
                "Try again in a few minutes (server might be temporarily unavailable)",
                "Check if you're behind a corporate proxy that requires configuration",
                "Ensure the download URL is accessible from your network"
            ],
            ErrorCategory.FILESYSTEM: [
                "Check available disk space (at least 500MB recommended)",
                "Verify the target path exists and is accessible",
                "Check if the file is corrupted and try re-downloading",
                "Ensure no other process is using the target files",
                "Try using a different target directory"
            ],
            ErrorCategory.CONFIGURATION: [
                "Verify the configuration file format is correct",
                "Check if required configuration values are present",
                "Ensure configuration files aren't read-only",
                "Try restoring default configuration settings",
                "Check for special characters in paths that might cause issues"
            ],
            ErrorCategory.ADMIN: [
                "Right-click the setup and select 'Run as administrator'",
                "Ensure your user account has administrator privileges",
                "Check if UAC (User Account Control) is blocking elevation",
                "Try running from an elevated command prompt",
                "Contact your system administrator if on a managed system"
            ],
            ErrorCategory.DOWNLOAD: [
                "Check your internet connection stability",
                "Verify the download URL is correct and accessible",
                "Try downloading to a different location",
                "Check if your antivirus is quarantining the download",
                "Ensure sufficient disk space for the download"
            ],
            ErrorCategory.EXTRACTION: [
                "Verify the archive file isn't corrupted",
                "Check available disk space for extraction",
                "Ensure no antivirus software is interfering",
                "Try extracting to a different location",
                "Check if you have write permissions to the target directory"
            ],
            ErrorCategory.UNKNOWN: [
                "Try running the setup again",
                "Check the error log file for more details",
                "Ensure all system requirements are met",
                "Try running in compatibility mode",
                "Contact support with the error details"
            ]
        }  
  
    def categorize_error(self, exception: Exception, context: str = "") -> ErrorCategory:
        """
        Categorize an error based on its type and context.
        
        Args:
            exception: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            ErrorCategory: The categorized error type
        """
        error_type = type(exception).__name__
        error_message = str(exception).lower()
        context_lower = context.lower()
        
        # Admin/elevation errors (check first to override permission errors)
        if ('admin' in context_lower or
            'elevation' in context_lower or
            'privilege' in error_message):
            return ErrorCategory.ADMIN
        
        # Permission-related errors
        if (error_type in ['PermissionError', 'OSError'] or 
            'permission denied' in error_message or
            'access is denied' in error_message or
            'operation not permitted' in error_message):
            return ErrorCategory.PERMISSION
        
        # Network-related errors
        if (error_type in ['URLError', 'HTTPError', 'ConnectionError', 'TimeoutError'] or
            'network' in error_message or
            'connection' in error_message or
            'timeout' in error_message or
            'download' in context_lower):
            return ErrorCategory.NETWORK
        
        # File system errors
        if (error_type in ['FileNotFoundError', 'IsADirectoryError', 'NotADirectoryError'] or
            'no such file' in error_message or
            'directory' in error_message or
            'disk' in error_message or
            'space' in error_message):
            return ErrorCategory.FILESYSTEM
        
        # Configuration errors
        if (error_type in ['JSONDecodeError', 'ConfigParser.Error', 'ValueError'] or
            'config' in context_lower or
            'json' in error_message or
            'ini' in error_message):
            return ErrorCategory.CONFIGURATION
        
        # Download-specific errors
        if ('download' in context_lower or
            'http' in error_message):
            return ErrorCategory.DOWNLOAD
        
        # Extraction errors
        if ('extract' in context_lower or
            'zip' in error_message or
            'archive' in error_message):
            return ErrorCategory.EXTRACTION
        
        return ErrorCategory.UNKNOWN
    
    def handle_error(self, 
                    exception: Exception, 
                    context: str = "",
                    custom_suggestions: Optional[List[str]] = None,
                    show_traceback: bool = False) -> ErrorInfo:
        """
        Handle an error by categorizing, logging, and displaying it.
        
        Args:
            exception: The exception that occurred
            context: Additional context about the error
            custom_suggestions: Custom suggestions to override defaults
            show_traceback: Whether to include traceback in display
            
        Returns:
            ErrorInfo: Information about the handled error
        """
        # Categorize the error
        category = self.categorize_error(exception, context)
        
        # Get suggestions
        suggestions = custom_suggestions or self._suggestion_map.get(category, [])
        
        # Get traceback if requested
        traceback_info = None
        if show_traceback:
            try:
                # Generate a proper traceback for the exception
                import sys
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_traceback is not None:
                    traceback_info = traceback.format_exc()
                else:
                    # If no current exception, create a minimal traceback
                    traceback_info = f"{type(exception).__name__}: {str(exception)}"
            except Exception:
                traceback_info = f"{type(exception).__name__}: {str(exception)}"
        
        # Create error info
        error_info = ErrorInfo(
            category=category,
            message=str(exception),
            details=context,
            suggestions=suggestions,
            traceback_info=traceback_info
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Display the error
        self.display_error(error_info)
        
        # Store in history
        self.error_history.append(error_info)
        
        return error_info
    
    def display_error(self, error_info: ErrorInfo) -> None:
        """
        Display an error using Rich panels with color coding.
        
        Args:
            error_info: Information about the error to display
        """
        # Create the main error message
        error_text = Text()
        error_text.append("Error: ", style="bold red")
        error_text.append(error_info.message, style="red")
        
        # Add details if available
        if error_info.details:
            error_text.append(f"\n\nContext: {error_info.details}", style="dim")
        
        # Add suggestions section
        if error_info.suggestions:
            error_text.append("\n\n")
            error_text.append("Troubleshooting Suggestions:", style="bold yellow")
            for i, suggestion in enumerate(error_info.suggestions, 1):
                error_text.append(f"\n{i}. {suggestion}", style="yellow")
        
        # Add traceback if available
        if error_info.traceback_info:
            error_text.append("\n\n")
            error_text.append("Technical Details:", style="bold dim")
            error_text.append(f"\n{error_info.traceback_info}", style="dim")
        
        # Create and display the panel
        error_panel = Panel(
            error_text,
            title=f"[bold red]{error_info.category.value}[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print()  # Add spacing
        self.console.print(error_panel)
        self.console.print()  # Add spacing
    
    def display_warning(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        """
        Display a warning message with optional suggestions.
        
        Args:
            message: Warning message to display
            suggestions: Optional troubleshooting suggestions
        """
        warning_text = Text()
        warning_text.append("Warning: ", style="bold yellow")
        warning_text.append(message, style="yellow")
        
        if suggestions:
            warning_text.append("\n\n")
            warning_text.append("Suggestions:", style="bold yellow")
            for i, suggestion in enumerate(suggestions, 1):
                warning_text.append(f"\n{i}. {suggestion}", style="yellow")
        
        warning_panel = Panel(
            warning_text,
            title="[bold yellow]Warning[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(warning_panel)
        self.console.print()
    
    def display_critical_error(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        """
        Display a critical error that stops the setup process.
        
        Args:
            message: Critical error message
            suggestions: Troubleshooting suggestions
        """
        critical_text = Text()
        critical_text.append("CRITICAL ERROR: ", style="bold red blink")
        critical_text.append(message, style="bold red")
        critical_text.append("\n\nThe setup cannot continue.", style="red")
        
        if suggestions:
            critical_text.append("\n\n")
            critical_text.append("Please try the following:", style="bold yellow")
            for i, suggestion in enumerate(suggestions, 1):
                critical_text.append(f"\n{i}. {suggestion}", style="yellow")
        
        critical_panel = Panel(
            critical_text,
            title="[bold red blink]CRITICAL ERROR[/bold red blink]",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(critical_panel)
        self.console.print()
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """
        Log error information to the log file.
        
        Args:
            error_info: Error information to log
        """
        log_message = (
            f"[{error_info.category.value}] {error_info.message}"
        )
        
        if error_info.details:
            log_message += f" | Context: {error_info.details}"
        
        # Log with appropriate level based on category
        if error_info.category in [ErrorCategory.PERMISSION, ErrorCategory.ADMIN]:
            self.logger.error(log_message)
        elif error_info.category == ErrorCategory.UNKNOWN:
            self.logger.critical(log_message)
        else:
            self.logger.warning(log_message)
        
        # Log traceback if available
        if error_info.traceback_info:
            self.logger.debug(f"Traceback: {error_info.traceback_info}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors that occurred during setup.
        
        Returns:
            Dict containing error statistics and recent errors
        """
        if not self.error_history:
            return {"total_errors": 0, "categories": {}, "recent_errors": []}
        
        # Count errors by category
        category_counts = {}
        for error in self.error_history:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get recent errors (last 5)
        recent_errors = []
        for error in self.error_history[-5:]:
            recent_errors.append({
                "category": error.category.value,
                "message": error.message,
                "timestamp": error.timestamp.strftime("%H:%M:%S")
            })
        
        return {
            "total_errors": len(self.error_history),
            "categories": category_counts,
            "recent_errors": recent_errors
        }
    
    def display_error_summary(self) -> None:
        """Display a summary of all errors that occurred."""
        summary = self.get_error_summary()
        
        if summary["total_errors"] == 0:
            return
        
        summary_text = Text()
        summary_text.append(f"Total errors encountered: {summary['total_errors']}\n\n", 
                          style="bold")
        
        # Show category breakdown
        if summary["categories"]:
            summary_text.append("Error breakdown by category:\n", style="bold")
            for category, count in summary["categories"].items():
                summary_text.append(f"• {category}: {count}\n", style="yellow")
        
        # Show recent errors
        if summary["recent_errors"]:
            summary_text.append("\nRecent errors:\n", style="bold")
            for error in summary["recent_errors"]:
                summary_text.append(
                    f"[{error['timestamp']}] {error['category']}: {error['message']}\n",
                    style="dim"
                )
        
        summary_panel = Panel(
            summary_text,
            title="[bold yellow]Error Summary[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(summary_panel)
        self.console.print()
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self.error_history.clear()
        self.logger.info("Error history cleared")
    
    def export_error_log(self, export_path: Optional[Path] = None) -> Path:
        """
        Export error history to a detailed log file.
        
        Args:
            export_path: Path to export the log to
            
        Returns:
            Path to the exported log file
        """
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Path(f"setup_error_report_{timestamp}.log")
        
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write("Setup Error Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total errors: {len(self.error_history)}\n\n")
            
            for i, error in enumerate(self.error_history, 1):
                f.write(f"Error #{i}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Timestamp: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Category: {error.category.value}\n")
                f.write(f"Message: {error.message}\n")
                
                if error.details:
                    f.write(f"Context: {error.details}\n")
                
                if error.suggestions:
                    f.write("Suggestions:\n")
                    for j, suggestion in enumerate(error.suggestions, 1):
                        f.write(f"  {j}. {suggestion}\n")
                
                if error.traceback_info:
                    f.write("Traceback:\n")
                    f.write(error.traceback_info)
                
                f.write("\n" + "=" * 50 + "\n\n")
        
        self.logger.info(f"Error report exported to: {export_path}")
        return export_path


# Convenience functions for common error scenarios
def create_permission_error(message: str, path: str = "") -> ErrorInfo:
    """Create a permission error with common suggestions."""
    suggestions = [
        "Run the setup as Administrator",
        "Check if antivirus software is blocking the operation",
        f"Ensure you have write permissions to {path}" if path else "Check file permissions",
        "Close any applications that might be using the files"
    ]
    
    return ErrorInfo(
        category=ErrorCategory.PERMISSION,
        message=message,
        details=f"Path: {path}" if path else None,
        suggestions=suggestions
    )


def create_network_error(message: str, url: str = "") -> ErrorInfo:
    """Create a network error with common suggestions."""
    suggestions = [
        "Check your internet connection",
        "Verify that your firewall isn't blocking the connection",
        "Try again in a few minutes",
        f"Verify the URL is accessible: {url}" if url else "Check the target URL"
    ]
    
    return ErrorInfo(
        category=ErrorCategory.NETWORK,
        message=message,
        details=f"URL: {url}" if url else None,
        suggestions=suggestions
    )


def create_filesystem_error(message: str, path: str = "") -> ErrorInfo:
    """Create a filesystem error with common suggestions."""
    suggestions = [
        "Check available disk space",
        "Verify the path exists and is accessible",
        f"Check permissions for: {path}" if path else "Check file permissions",
        "Ensure no other process is using the files"
    ]
    
    return ErrorInfo(
        category=ErrorCategory.FILESYSTEM,
        message=message,
        details=f"Path: {path}" if path else None,
        suggestions=suggestions
    )