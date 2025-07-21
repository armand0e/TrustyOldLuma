"""
Display managers for the Gaming Setup Tool.

This module contains Rich-based display managers for progress tracking,
error handling, and user interface components.
"""

import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress, 
    TaskID, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn, 
    TimeRemainingColumn, 
    TimeElapsedColumn
)
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.prompt import Confirm
from rich.live import Live
from rich.spinner import Spinner

from luna.models.models import LunaResults
from config import PANEL_STYLES


class ProgressDisplayManager:
    """Manages Rich progress displays and status indicators."""
    
    def __init__(self, console: Console):
        """Initialize the progress display manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.current_progress: Optional[Progress] = None
        self.active_tasks: Dict[str, TaskID] = {}
        
    def create_progress_bar(self, description: str, total: Optional[int] = None) -> 'ProgressContext':
        """Create a new progress bar context.
        
        Args:
            description: Description for the progress bar
            total: Total number of steps (None for indeterminate)
            
        Returns:
            ProgressContext for managing the progress bar
        """
        return ProgressContext(self, description, total)
    
    @contextmanager
    def show_spinner(self, message: str) -> Generator[None, None, None]:
        """Show spinner with status message.
        
        Args:
            message: Status message to display with spinner
        """
        spinner = Spinner("dots", text=message, style="cyan")
        with Live(spinner, console=self.console, refresh_per_second=10):
            yield
    
    def _get_progress_columns(self):
        """Get the standard progress bar columns."""
        return [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
        ]


class ProgressContext:
    """Context manager for progress bar operations."""
    
    def __init__(self, manager: ProgressDisplayManager, description: str, total: Optional[int] = None):
        """Initialize progress context.
        
        Args:
            manager: Parent progress display manager
            description: Progress bar description
            total: Total number of steps
        """
        self.manager = manager
        self.description = description
        self.total = total or 100
        self.task_id: Optional[TaskID] = None
        self.progress: Optional[Progress] = None
        
    def __enter__(self) -> 'ProgressContext':
        """Enter the progress context."""
        self.progress = Progress(
            *self.manager._get_progress_columns(),
            console=self.manager.console
        )
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=self.total)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the progress context."""
        if self.progress:
            self.progress.stop()
            
    def update(self, advance: int = 1, description: Optional[str] = None) -> None:
        """Update progress bar advancement.
        
        Args:
            advance: Number of steps to advance
            description: Optional new description
        """
        if self.progress and self.task_id is not None:
            update_kwargs = {"advance": advance}
            if description:
                update_kwargs["description"] = description
            self.progress.update(self.task_id, **update_kwargs)
            
    def set_total(self, total: int) -> None:
        """Set the total number of steps.
        
        Args:
            total: Total number of steps
        """
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, total=total)


class ErrorDisplayManager:
    """Manages error display with Rich formatting and Luna-specific error handling."""
    
    def __init__(self, console: Console):
        """Initialize the error display manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        self.luna_error_categories = {
            'migration': '🔄',
            'component': '⚙️',
            'configuration': '📝',
            'compatibility': '🔧',
            'general': '❌'
        }
        
    def display_error(self, error: Exception, context: str, suggestion: Optional[str] = None) -> None:
        """Display error in styled panel with context.
        
        Args:
            error: Exception that occurred
            context: Context where the error occurred
            suggestion: Optional suggestion for resolution
        """
        error_text = Text()
        error_text.append(f"Context: {context}\n", style="bold")
        error_text.append(f"Error: {str(error)}", style="red")
        
        if suggestion:
            error_text.append(f"\n\nSuggestion: {suggestion}", style="yellow")
            
        panel = Panel(
            error_text,
            title="❌ Error",
            **PANEL_STYLES['error']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
    def display_luna_error(self, error: Exception, context: str, category: str = 'general', 
                          suggestion: Optional[str] = None) -> None:
        """Display Luna-specific error with enhanced formatting and categorization.
        
        Args:
            error: Exception that occurred
            context: Context where the error occurred
            category: Luna error category ('migration', 'component', 'configuration', 'compatibility', 'general')
            suggestion: Optional suggestion for resolution
        """
        category_emoji = self.luna_error_categories.get(category, '❌')
        
        error_text = Text()
        error_text.append(f"Luna {category.title()} Error\n", style="bold red")
        error_text.append(f"Context: {context}\n", style="bold")
        error_text.append(f"Error: {str(error)}", style="red")
        
        if suggestion:
            error_text.append(f"\n\nLuna Suggestion: {suggestion}", style="yellow")
        else:
            # Provide Luna-specific default suggestions based on category
            default_suggestion = self._get_luna_default_suggestion(category)
            if default_suggestion:
                error_text.append(f"\n\nLuna Suggestion: {default_suggestion}", style="yellow")
            
        panel = Panel(
            error_text,
            title=f"{category_emoji} Luna Error",
            **PANEL_STYLES['error']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
    def display_migration_error(self, error: Exception, legacy_tool: str, 
                               suggestion: Optional[str] = None) -> None:
        """Display migration-specific error with Luna branding.
        
        Args:
            error: Migration exception that occurred
            legacy_tool: Name of the legacy tool being migrated
            suggestion: Optional suggestion for resolution
        """
        error_text = Text()
        error_text.append(f"Luna Migration Error\n", style="bold red")
        error_text.append(f"Legacy Tool: {legacy_tool}\n", style="bold")
        error_text.append(f"Error: {str(error)}", style="red")
        
        if suggestion:
            error_text.append(f"\n\nMigration Suggestion: {suggestion}", style="yellow")
        else:
            error_text.append(f"\n\nMigration Suggestion: Check if {legacy_tool} is properly installed and accessible. Luna may need to run with administrator privileges for migration.", style="yellow")
            
        panel = Panel(
            error_text,
            title="🔄 Luna Migration Error",
            **PANEL_STYLES['error']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
    def _get_luna_default_suggestion(self, category: str) -> Optional[str]:
        """Get default Luna-specific suggestion based on error category.
        
        Args:
            category: Error category
            
        Returns:
            Default suggestion string or None
        """
        suggestions = {
            'migration': 'Ensure legacy installations are accessible and Luna has administrator privileges.',
            'component': 'Verify Luna components are properly installed and not blocked by antivirus.',
            'configuration': 'Check Luna configuration files for syntax errors and proper permissions.',
            'compatibility': 'Verify system compatibility and ensure all Luna dependencies are met.',
            'general': 'Try running Luna with administrator privileges and check system requirements.'
        }
        return suggestions.get(category)
        
    def categorize_luna_error(self, error: Exception) -> str:
        """Categorize error for Luna-specific handling.
        
        Args:
            error: Exception to categorize
            
        Returns:
            Error category string
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if 'migration' in error_str or 'legacy' in error_str:
            return 'migration'
        elif 'config' in error_str or 'configuration' in error_str:
            return 'configuration'
        elif 'component' in error_str or 'luna' in error_str:
            return 'component'
        elif 'compatibility' in error_str or 'system' in error_str:
            return 'compatibility'
        else:
            return 'general'
        
    def display_warning(self, message: str, suggestion: Optional[str] = None) -> None:
        """Display warning with optional suggestion.
        
        Args:
            message: Warning message
            suggestion: Optional suggestion for resolution
        """
        warning_text = Text()
        warning_text.append(message, style="yellow")
        
        if suggestion:
            warning_text.append(f"\n\nSuggestion: {suggestion}", style="cyan")
            
        panel = Panel(
            warning_text,
            title="⚠️  Warning",
            **PANEL_STYLES['warning']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
        
    def display_retry_prompt(self, operation: str, attempt: int, max_attempts: int) -> bool:
        """Display retry prompt and get user decision.
        
        Args:
            operation: Name of the operation that failed
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            
        Returns:
            True if user wants to retry, False otherwise
        """
        retry_text = f"Operation '{operation}' failed (attempt {attempt}/{max_attempts})"
        
        if attempt < max_attempts:
            return Confirm.ask(f"{retry_text}. Would you like to retry?", default=True)
        else:
            self.console.print(f"[red]{retry_text}. Maximum attempts reached.[/red]")
            return False
            
    def display_success(self, message: str, details: Optional[str] = None) -> None:
        """Display success message with optional details.
        
        Args:
            message: Success message
            details: Optional additional details
        """
        success_text = Text()
        success_text.append(message, style="green")
        
        if details:
            success_text.append(f"\n\n{details}", style="dim")
            
        panel = Panel(
            success_text,
            title="✅ Success",
            **PANEL_STYLES['success']
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()


class WelcomeScreenManager:
    """Manages the welcome screen display."""
    
    def __init__(self, console: Console):
        """Initialize the welcome screen manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        
    def display_welcome(self) -> None:
        """Display welcome screen with Rich panels and styling."""
        # Create main welcome text
        welcome_text = Text()
        welcome_text.append("Luna Gaming Tool", style="bold cyan")
        welcome_text.append("\n\nThis unified tool will set up Luna with:\n")
        
        # Add feature list with emojis
        features = [
            "🎯 Rich progress indicators and visual feedback",
            "🔐 Automatic administrator privilege handling",
            "🛡️ Windows Defender exclusion configuration",
            "📁 Automatic directory and file management",
            "⬇️ Luna component download and installation",
            "⚙️ Configuration file updates and management",
            "🔗 Desktop shortcut creation",
            "📊 Comprehensive error handling and logging"
        ]
        
        for feature in features:
            welcome_text.append(f"  {feature}\n")
            
        # Add warning about admin privileges
        welcome_text.append("\n")
        welcome_text.append("⚠️ Note: ", style="yellow bold")
        welcome_text.append("This tool requires administrator privileges for some operations.", style="yellow")
        
        # Create the main panel
        main_panel = Panel.fit(
            welcome_text,
            title="🌙 Welcome to Luna",
            **PANEL_STYLES['welcome']
        )
        
        # Create info panel
        info_text = Text()
        info_text.append("Before we begin Luna setup:\n", style="bold")
        info_text.append("• Ensure you have a stable internet connection\n")
        info_text.append("• Close any running games or related applications\n")
        info_text.append("• Make sure you have sufficient disk space\n")
        info_text.append("• Luna setup process may take a few minutes")
        
        info_panel = Panel(
            info_text,
            title="ℹ️ Information",
            border_style="blue",
            padding=(1, 2)
        )
        
        # Display the welcome screen
        self.console.print()
        self.console.print(main_panel)
        self.console.print()
        self.console.print(info_panel)
        self.console.print()
        
        # Wait for user acknowledgment
        self.console.print("[dim]Press Enter to continue...[/dim]", end="")
        input()
        self.console.print()


class CompletionScreenManager:
    """Manages the completion screen display with summary and next steps."""
    
    def __init__(self, console: Console):
        """Initialize the completion screen manager.
        
        Args:
            console: Rich console instance for output
        """
        self.console = console
        
    def display_completion(self, results: LunaResults) -> None:
        """Display completion summary and next steps.
        
        Args:
            results: Setup results containing operation outcomes
        """
        # Determine overall status
        success_rate = results.success_rate
        has_errors = results.has_errors
        
        if success_rate >= 0.9 and not has_errors:
            status_emoji = "🌙"
            status_text = "Luna Setup Completed Successfully!"
            status_style = "green bold"
        elif success_rate >= 0.7:
            status_emoji = "⚠️"
            status_text = "Luna Setup Completed with Warnings"
            status_style = "yellow bold"
        else:
            status_emoji = "❌"
            status_text = "Luna Setup Completed with Errors"
            status_style = "red bold"
            
        # Create summary table
        summary_table = self._create_summary_table(results)
        
        # Create main completion panel
        completion_text = Text()
        completion_text.append(f"{status_emoji} {status_text}", style=status_style)
        completion_text.append(f"\n\nSuccess Rate: {success_rate:.1%}", style="cyan")
        
        if results.duration:
            completion_text.append(f"\nDuration: {results.duration:.1f} seconds", style="dim")
            
        main_panel = Panel(
            completion_text,
            title="🌙 Luna Setup Complete",
            **PANEL_STYLES['completion']
        )
        
        # Create next steps panel
        next_steps = self._create_next_steps_panel(results)
        
        # Display completion screen
        self.console.print()
        self.console.print(main_panel)
        self.console.print()
        self.console.print(Panel(summary_table, title="📊 Summary", border_style="cyan"))
        self.console.print()
        self.console.print(next_steps)
        
        # Display errors and warnings if any
        if results.has_errors:
            self._display_errors(results.errors)
        if results.has_warnings:
            self._display_warnings(results.warnings)
            
        self.console.print()
        self.console.print("[dim]Press Enter to exit...[/dim]", end="")
        input()
        
    def _create_summary_table(self, results: LunaResults) -> Table:
        """Create a summary table of setup results.
        
        Args:
            results: Setup results
            
        Returns:
            Rich Table with summary information
        """
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Operation", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")
        
        # Directory creation
        if results.directories_created:
            table.add_row(
                "📁 Directory Creation",
                "✅ Success",
                f"{len(results.directories_created)} directories created"
            )
        
        # Security exclusions
        if results.exclusions_added:
            successful = sum(1 for _, success in results.exclusions_added if success)
            total = len(results.exclusions_added)
            status = "✅ Success" if successful == total else f"⚠️  Partial ({successful}/{total})"
            table.add_row(
                "🛡️  Security Exclusions",
                status,
                f"{successful} of {total} exclusions added"
            )
        
        # File extraction
        if hasattr(results, '_extraction_attempted'):
            status = "✅ Success" if results.files_extracted else "❌ Failed"
            table.add_row(
                "📦 File Extraction",
                status,
                "Luna components extracted" if results.files_extracted else "Extraction failed"
            )
        
        # Downloads
        if results.files_downloaded:
            successful = sum(1 for _, success in results.files_downloaded if success)
            total = len(results.files_downloaded)
            status = "✅ Success" if successful == total else f"⚠️  Partial ({successful}/{total})"
            table.add_row(
                "⬇️  Downloads",
                status,
                f"{successful} of {total} files downloaded"
            )
        
        # Configuration updates
        if results.configs_updated:
            successful = sum(1 for _, success in results.configs_updated if success)
            total = len(results.configs_updated)
            status = "✅ Success" if successful == total else f"⚠️  Partial ({successful}/{total})"
            table.add_row(
                "⚙️  Configuration",
                status,
                f"{successful} of {total} configs updated"
            )
        
        # Shortcuts
        if results.shortcuts_created:
            successful = sum(1 for _, success in results.shortcuts_created if success)
            total = len(results.shortcuts_created)
            status = "✅ Success" if successful == total else f"⚠️  Partial ({successful}/{total})"
            table.add_row(
                "🔗 Shortcuts",
                status,
                f"{successful} of {total} shortcuts created"
            )
        
        return table
        
    def _create_next_steps_panel(self, results: LunaResults) -> Panel:
        """Create next steps panel based on setup results.
        
        Args:
            results: Setup results
            
        Returns:
            Rich Panel with next steps information
        """
        next_steps_text = Text()
        next_steps_text.append("What to do next:\n\n", style="bold")
        
        if results.success_rate >= 0.9:
            # Successful setup
            steps = [
                "1. Launch Luna from your desktop shortcut",
                "2. Configure your game library in Luna",
                "3. Set up Luna's injection and unlocking features",
                "4. Configure platform-specific settings in Luna",
                "5. Enjoy your unified Luna gaming experience!"
            ]
        else:
            # Partial or failed setup
            steps = [
                "1. Review any error messages above",
                "2. Check the Luna log files for detailed information",
                "3. Ensure you have administrator privileges",
                "4. Try running the Luna setup again",
                "5. Consult the Luna documentation for troubleshooting"
            ]
            
        for step in steps:
            next_steps_text.append(f"  {step}\n")
            
        # Add useful links
        next_steps_text.append("\nUseful Resources:\n", style="bold")
        next_steps_text.append("  • Luna Documentation: Check the Luna user guide\n", style="blue")
        next_steps_text.append("  • Luna Support: Visit the Luna support community\n", style="blue")
        next_steps_text.append("  • Migration Guide: See Luna migration documentation\n", style="blue")
        
        return Panel(
            next_steps_text,
            title="🚀 Next Steps",
            border_style="green" if results.success_rate >= 0.9 else "yellow",
            padding=(1, 2)
        )
        
    def _display_errors(self, errors: List[str]) -> None:
        """Display error messages in a styled panel.
        
        Args:
            errors: List of error messages
        """
        if not errors:
            return
            
        error_text = Text()
        error_text.append("The following errors occurred during Luna setup:\n\n", style="bold red")
        
        for i, error in enumerate(errors, 1):
            error_text.append(f"{i}. {error}\n", style="red")
            
        panel = Panel(
            error_text,
            title="❌ Errors",
            **PANEL_STYLES['error']
        )
        
        self.console.print()
        self.console.print(panel)
        
    def _display_warnings(self, warnings: List[str]) -> None:
        """Display warning messages in a styled panel.
        
        Args:
            warnings: List of warning messages
        """
        if not warnings:
            return
            
        warning_text = Text()
        warning_text.append("The following warnings were generated:\n\n", style="bold yellow")
        
        for i, warning in enumerate(warnings, 1):
            warning_text.append(f"{i}. {warning}\n", style="yellow")
            
        panel = Panel(
            warning_text,
            title="⚠️  Warnings",
            **PANEL_STYLES['warning']
        )
        
        self.console.print()
        self.console.print(panel)