"""UI Manager module for Rich-based terminal interface."""

import sys
import signal
import threading
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.status import Status
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt, Confirm
from rich.pager import Pager
from rich.live import Live
from typing import List, Optional, Callable, Dict, Any


class UIManager:
    """Handles all Rich-based terminal interface elements."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize UIManager with Rich Console and color system detection."""
        self.console = console or Console()
        self._interrupt_handler: Optional[Callable] = None
        self._keyboard_interrupt_received = False
        self._setup_keyboard_handlers()
        
    def show_welcome_screen(self, interactive: bool = True) -> None:
        """Display colorful welcome screen with rich text formatting and project branding."""
        # Create branded header with ASCII art style
        welcome_content = Text()
        welcome_content.append("╔══════════════════════════════════════════════════════════════╗\n", style="bold cyan")
        welcome_content.append("║                🎮 TrustyOldLuma Unified Setup                ║\n", style="bold cyan")
        welcome_content.append("║                    One-Click Gaming Solution                  ║\n", style="bold cyan")
        welcome_content.append("╚══════════════════════════════════════════════════════════════╝\n\n", style="bold cyan")
        
        welcome_content.append("Unified installation of GreenLuma + Koalageddon for the ultimate\n", style="bright_white")
        welcome_content.append("Steam gaming experience with automated platform integration.\n\n", style="bright_white")
        
        # Feature list with enhanced styling for unified setup
        welcome_content.append("🚀 This unified setup will:\n", style="bold yellow")
        welcome_content.append("   ✅ Configure Windows Security exclusions\n", style="bright_green")
        welcome_content.append("   ✅ Extract GreenLuma and install embedded Koalageddon\n", style="bright_green")
        welcome_content.append("   ✅ Detect and integrate with gaming platforms automatically\n", style="bright_green")
        welcome_content.append("   ✅ Create unified desktop shortcuts\n", style="bright_green")
        welcome_content.append("   ✅ Configure both applications seamlessly\n\n", style="bright_green")
        
        # Project branding and engagement
        welcome_content.append("💡 Features:\n", style="bold magenta")
        welcome_content.append("   • Rich visual interface with progress tracking\n", style="white")
        welcome_content.append("   • Intelligent error handling and recovery\n", style="white")
        welcome_content.append("   • Automated Windows Security configuration\n", style="white")
        welcome_content.append("   • One-click desktop integration\n\n", style="white")
        
        welcome_content.append("🌟 Support the project:\n", style="bold yellow")
        welcome_content.append("   Star us on GitHub: ", style="white")
        welcome_content.append("https://github.com/armand0e/TrustyOldLuma\n", style="blue underline")
        welcome_content.append("   Join our community for updates and support!\n", style="white")
        
        welcome_panel = Panel(
            Align.center(welcome_content),
            title="[bold cyan]🎮 Welcome to TrustyOldLuma Setup 🎮[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=70
        )
        
        self.console.print()
        self.console.print(welcome_panel)
        self.console.print()
        
        # Add interactive prompt to continue (optional for testing)
        if interactive:
            self.prompt_continue("Press Enter to begin the setup process...")
        
    def create_panel(self, content: str, title: str, style: str = "white") -> Panel:
        """Create panel with different styles for various setup phases."""
        return Panel(
            content,
            title=f"[bold {style}]{title}[/bold {style}]",
            border_style=style,
            padding=(0, 1)
        )
        
    def show_progress_bar(self, description: str, total: int) -> Progress:
        """Show progress bar with proper formatting."""
        progress = Progress(
            "[progress.description]{task.description}",
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[progress.bar]",
            "[progress.remaining]{task.remaining}",
            console=self.console
        )
        return progress
        
    def show_status_spinner(self, message: str) -> Status:
        """Show spinner display methods with proper formatting."""
        return Status(
            message,
            console=self.console,
            spinner="dots"
        )
        
    def display_error(self, error: str, suggestions: List[str]) -> None:
        """Display color-coded error messages."""
        error_content = f"[red]Error:[/red] {error}\n"
        
        if suggestions:
            error_content += "\n[yellow]Suggestions:[/yellow]\n"
            for suggestion in suggestions:
                error_content += f"• {suggestion}\n"
        
        error_panel = Panel(
            error_content.rstrip(),
            title="[red]Error[/red]",
            border_style="red",
            padding=(0, 1)
        )
        
        self.console.print()
        self.console.print(error_panel)
        self.console.print()
        
    def display_success(self, message: str) -> None:
        """Display color-coded success messages."""
        success_panel = Panel(
            f"[green]✅ {message}[/green]",
            title="[green]Success[/green]",
            border_style="green",
            padding=(0, 1)
        )
        
        self.console.print()
        self.console.print(success_panel)
        self.console.print()
        
    def display_warning(self, message: str) -> None:
        """Display color-coded warning messages."""
        warning_panel = Panel(
            f"[yellow]⚠️  {message}[/yellow]",
            title="[yellow]Warning[/yellow]",
            border_style="yellow",
            padding=(0, 1)
        )
        
        self.console.print()
        self.console.print(warning_panel)
        self.console.print()
        
    def display_info(self, message: str) -> None:
        """Display color-coded info messages."""
        info_panel = Panel(
            f"[blue]ℹ️  {message}[/blue]",
            title="[blue]Information[/blue]",
            border_style="blue",
            padding=(0, 1)
        )
        
        self.console.print()
        self.console.print(info_panel)
        self.console.print()
        
    def show_completion_summary(self, operations: List[str], failed_operations: Optional[List[str]] = None, interactive: bool = True) -> None:
        """Show comprehensive completion summary with operation status and next steps guidance."""
        # Create celebration header
        summary_content = Text()
        summary_content.append("╔══════════════════════════════════════════════════════════════╗\n", style="bold green")
        summary_content.append("║                    🎉 Setup Complete! 🎉                    ║\n", style="bold green")
        summary_content.append("║              TrustyOldLuma is ready to use!                 ║\n", style="bold green")
        summary_content.append("╚══════════════════════════════════════════════════════════════╝\n\n", style="bold green")
        
        # Operation status summary
        if operations:
            summary_content.append("✅ Successfully completed operations:\n", style="bold bright_green")
            for operation in operations:
                summary_content.append(f"   ✅ {operation}\n", style="bright_green")
            summary_content.append("\n")
        
        # Failed operations (if any)
        if failed_operations:
            summary_content.append("⚠️  Operations with issues:\n", style="bold yellow")
            for operation in failed_operations:
                summary_content.append(f"   ⚠️  {operation}\n", style="yellow")
            summary_content.append("\n")
        
        # Detailed next steps
        summary_content.append("🚀 Next Steps:\n", style="bold cyan")
        summary_content.append("   1. Launch Koalageddon from your desktop\n", style="bright_white")
        summary_content.append("      • Install platform integrations (Steam, Epic, etc.)\n", style="white")
        summary_content.append("      • Configure your preferred game platforms\n", style="white")
        summary_content.append("   2. Start GreenLuma by double-clicking the desktop shortcut\n", style="bright_white")
        summary_content.append("      • Your games will now be available for sharing\n", style="white")
        summary_content.append("      • Check the AppList folder for game configurations\n", style="white")
        summary_content.append("   3. Enjoy your enhanced gaming experience!\n\n", style="bright_white")
        
        # Troubleshooting section
        summary_content.append("🔧 Need Help?\n", style="bold magenta")
        summary_content.append("   • Check Windows Security exclusions are active\n", style="white")
        summary_content.append("   • Verify desktop shortcuts are working\n", style="white")
        summary_content.append("   • Visit our GitHub for troubleshooting guides\n", style="white")
        summary_content.append("   • Join our community for support\n\n", style="white")
        
        # Community engagement and promotion
        summary_content.append("🌟 Support TrustyOldLuma:\n", style="bold yellow")
        summary_content.append("   ⭐ Star us on GitHub: ", style="bright_white")
        summary_content.append("https://github.com/armand0e/TrustyOldLuma\n", style="blue underline")
        summary_content.append("   🐛 Report issues or request features\n", style="bright_white")
        summary_content.append("   💬 Share your experience with the community\n", style="bright_white")
        summary_content.append("   🔄 Check for updates and new features\n\n", style="bright_white")
        
        # Final message
        summary_content.append("Thank you for using TrustyOldLuma! 🎮✨\n", style="bold bright_cyan")
        summary_content.append("Happy gaming! 🚀", style="bold bright_magenta")
        
        summary_panel = Panel(
            Align.center(summary_content),
            title="[bold green]🎉 Setup Complete - Ready to Game! 🎉[/bold green]",
            border_style="green",
            padding=(1, 2),
            width=70
        )
        
        self.console.print()
        self.console.print(summary_panel)
        self.console.print()
        
        # Add final interactive prompt (optional for testing)
        if interactive:
            self.prompt_continue("Press Enter to exit setup...")
        
    def show_admin_phase_panel(self, status_messages: List[str]) -> None:
        """Show admin phase panel with current status."""
        admin_content = "🔐 Administrator Setup\n\n"
        
        for message in status_messages:
            admin_content += f"{message}\n"
        
        admin_panel = Panel(
            admin_content.rstrip(),
            title="[bold red]Administrator Setup[/bold red]",
            border_style="red",
            padding=(0, 1)
        )
        
        self.console.print()
        self.console.print(admin_panel)
        self.console.print()
        
    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()
        
    def print(self, *args, **kwargs) -> None:
        """Print to console with Rich formatting."""
        self.console.print(*args, **kwargs)
        
    def _setup_keyboard_handlers(self) -> None:
        """Setup keyboard interrupt handlers."""
        def keyboard_interrupt_handler(signum, frame):
            self._keyboard_interrupt_received = True
            if self._interrupt_handler:
                self._interrupt_handler()
            else:
                self.display_warning("Operation interrupted by user (Ctrl+C)")
                sys.exit(1)
                
        signal.signal(signal.SIGINT, keyboard_interrupt_handler)
        
    def set_interrupt_handler(self, handler: Callable) -> None:
        """Set custom interrupt handler for graceful shutdown."""
        self._interrupt_handler = handler
        
    def prompt_continue(self, message: str = "Press Enter to continue...") -> bool:
        """
        Show continuation prompt that responds to Enter key.
        
        Args:
            message: Message to display for the prompt
            
        Returns:
            bool: True if user pressed Enter, False if interrupted
        """
        try:
            self.console.print(f"\n[dim]{message}[/dim]", end="")
            input()  # Wait for Enter key
            return True
        except KeyboardInterrupt:
            self._keyboard_interrupt_received = True
            return False
            
    def prompt_confirmation(self, message: str, default: bool = True) -> Optional[bool]:
        """
        Show confirmation dialog with keyboard navigation.
        
        Args:
            message: Confirmation message
            default: Default value if user just presses Enter
            
        Returns:
            bool: User's choice, None if interrupted
        """
        try:
            return Confirm.ask(message, default=default, console=self.console)
        except KeyboardInterrupt:
            self._keyboard_interrupt_received = True
            return None
            
    def prompt_choice(self, message: str, choices: List[str], default: Optional[str] = None) -> Optional[str]:
        """
        Show choice prompt with keyboard navigation.
        
        Args:
            message: Prompt message
            choices: List of available choices
            default: Default choice if user just presses Enter
            
        Returns:
            str: Selected choice, None if interrupted
        """
        try:
            return Prompt.ask(
                message, 
                choices=choices, 
                default=default,
                console=self.console
            )
        except KeyboardInterrupt:
            self._keyboard_interrupt_received = True
            return None
            
    def show_menu(self, title: str, options: Dict[str, str], allow_cancel: bool = True) -> Optional[str]:
        """
        Show interactive menu with keyboard navigation.
        
        Args:
            title: Menu title
            options: Dictionary of option_key -> description
            allow_cancel: Whether to allow canceling with Ctrl+C
            
        Returns:
            str: Selected option key, None if canceled
        """
        try:
            menu_content = Text()
            menu_content.append(f"{title}\n\n", style="bold white")
            
            option_keys = list(options.keys())
            for i, (key, description) in enumerate(options.items(), 1):
                menu_content.append(f"{i}. {description}\n", style="white")
            
            if allow_cancel:
                menu_content.append("\nPress Ctrl+C to cancel", style="dim")
            
            menu_panel = Panel(
                menu_content,
                title="[bold cyan]Menu[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            )
            
            self.console.print(menu_panel)
            
            # Get user choice
            while True:
                try:
                    choice = Prompt.ask(
                        "Select option",
                        choices=[str(i) for i in range(1, len(option_keys) + 1)],
                        console=self.console
                    )
                    return option_keys[int(choice) - 1]
                except (ValueError, IndexError):
                    self.display_warning("Invalid choice. Please try again.")
                except KeyboardInterrupt:
                    if allow_cancel:
                        return None
                    else:
                        self.display_warning("Cancellation not allowed in this menu")
                        
        except KeyboardInterrupt:
            return None
            
    def show_scrollable_content(self, content: str, title: str = "Content") -> None:
        """
        Show long content with scrolling support.
        
        Args:
            content: Content to display
            title: Title for the content panel
        """
        try:
            # Create panel with content
            content_panel = Panel(
                content,
                title=f"[bold white]{title}[/bold white]",
                border_style="white",
                padding=(1, 2)
            )
            
            # Use Rich's pager for scrolling if content is long
            lines = content.split('\n')
            if len(lines) > self.console.size.height - 10:  # Leave room for UI elements
                with self.console.pager():
                    self.console.print(content_panel)
                self.console.print("\n[dim]Use arrow keys to scroll, 'q' to quit pager[/dim]")
            else:
                self.console.print(content_panel)
                
        except KeyboardInterrupt:
            self._keyboard_interrupt_received = True
            
    def show_progress_with_cancel(self, description: str, total: int, 
                                 cancel_callback: Optional[Callable] = None) -> Progress:
        """
        Show progress bar that can be canceled with Ctrl+C.
        
        Args:
            description: Progress description
            total: Total progress units
            cancel_callback: Function to call when canceled
            
        Returns:
            Progress: Rich Progress object
        """
        progress = Progress(
            "[progress.description]{task.description}",
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[progress.bar]",
            "[progress.remaining]{task.remaining}",
            "[dim]Press Ctrl+C to cancel[/dim]",
            console=self.console
        )
        
        # Set up cancel handler
        if cancel_callback:
            original_handler = self._interrupt_handler
            
            def cancel_handler():
                if cancel_callback:
                    cancel_callback()
                if original_handler:
                    original_handler()
                    
            self.set_interrupt_handler(cancel_handler)
            
        return progress
        
    def show_interactive_status(self, message: str, 
                              cancel_callback: Optional[Callable] = None) -> Status:
        """
        Show status spinner that can be canceled with Ctrl+C.
        
        Args:
            message: Status message
            cancel_callback: Function to call when canceled
            
        Returns:
            Status: Rich Status object
        """
        status_message = f"{message} [dim](Press Ctrl+C to cancel)[/dim]"
        
        # Set up cancel handler
        if cancel_callback:
            original_handler = self._interrupt_handler
            
            def cancel_handler():
                if cancel_callback:
                    cancel_callback()
                if original_handler:
                    original_handler()
                    
            self.set_interrupt_handler(cancel_handler)
            
        return Status(
            status_message,
            console=self.console,
            spinner="dots"
        )
        
    def was_interrupted(self) -> bool:
        """Check if keyboard interrupt was received."""
        return self._keyboard_interrupt_received
        
    def reset_interrupt_flag(self) -> None:
        """Reset the keyboard interrupt flag."""
        self._keyboard_interrupt_received = False
        
    def show_help_text(self, help_content: str) -> None:
        """
        Show help text with keyboard shortcuts information.
        
        Args:
            help_content: Help content to display
        """
        help_text = Text()
        help_text.append("Keyboard Shortcuts:\n", style="bold yellow")
        help_text.append("• Ctrl+C: Cancel current operation\n", style="white")
        help_text.append("• Enter: Continue to next step\n", style="white")
        help_text.append("• Arrow keys: Navigate in scrollable content\n", style="white")
        help_text.append("• Numbers: Select menu options\n", style="white")
        help_text.append("• Y/N: Confirm/deny prompts\n\n", style="white")
        
        if help_content:
            help_text.append("Additional Information:\n", style="bold yellow")
            help_text.append(help_content, style="white")
        
        help_panel = Panel(
            help_text,
            title="[bold yellow]Help[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.show_scrollable_content(str(help_panel), "Help")
        
    def display_phase_transition(self, from_phase: str, to_phase: str, progress_info: Optional[str] = None) -> None:
        """
        Display phase transition with clear visual separation using panels.
        
        Args:
            from_phase: Current phase name
            to_phase: Next phase name
            progress_info: Optional progress information to display
        """
        # Create visual separator
        separator = "═" * 50
        
        transition_content = Text()
        transition_content.append(f"{separator}\n", style="dim cyan")
        transition_content.append(f"✅ Phase Complete: {from_phase}\n", style="bold bright_green")
        transition_content.append(f"➡️  Next Phase: {to_phase}\n", style="bold bright_cyan")
        
        if progress_info:
            transition_content.append(f"📊 Progress: {progress_info}\n", style="bright_yellow")
        
        transition_content.append(f"{separator}\n", style="dim cyan")
        
        transition_panel = Panel(
            Align.center(transition_content),
            title="[bold cyan]🔄 Phase Transition 🔄[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=60
        )
        
        self.console.print()
        self.console.print(transition_panel)
        self.console.print()
        self.prompt_continue("Press Enter to continue to the next phase...")
        
    def show_phase_header(self, phase_name: str, phase_description: str, phase_number: int, total_phases: int) -> None:
        """
        Display phase header with clear visual branding.
        
        Args:
            phase_name: Name of the current phase
            phase_description: Description of what this phase does
            phase_number: Current phase number
            total_phases: Total number of phases
        """
        header_content = Text()
        header_content.append(f"Phase {phase_number}/{total_phases}: {phase_name}\n", style="bold bright_cyan")
        header_content.append(f"{phase_description}\n", style="bright_white")
        
        # Progress bar for phases
        progress_bar = "█" * phase_number + "░" * (total_phases - phase_number)
        header_content.append(f"\nProgress: [{progress_bar}] {phase_number}/{total_phases}", style="bright_yellow")
        
        header_panel = Panel(
            header_content,
            title=f"[bold cyan]🔧 {phase_name} 🔧[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=60
        )
        
        self.console.print()
        self.console.print(header_panel)
        self.console.print()
        
    def show_setup_progress_overview(self, completed_phases: List[str], current_phase: str, remaining_phases: List[str]) -> None:
        """
        Show overall setup progress with visual indicators.
        
        Args:
            completed_phases: List of completed phase names
            current_phase: Current phase name
            remaining_phases: List of remaining phase names
        """
        progress_content = Text()
        progress_content.append("📋 Setup Progress Overview\n\n", style="bold bright_cyan")
        
        # Completed phases
        if completed_phases:
            progress_content.append("✅ Completed:\n", style="bold bright_green")
            for phase in completed_phases:
                progress_content.append(f"   ✅ {phase}\n", style="bright_green")
            progress_content.append("\n")
        
        # Current phase
        progress_content.append("🔄 Currently Running:\n", style="bold bright_yellow")
        progress_content.append(f"   ⚡ {current_phase}\n\n", style="bright_yellow")
        
        # Remaining phases
        if remaining_phases:
            progress_content.append("⏳ Upcoming:\n", style="bold bright_blue")
            for phase in remaining_phases:
                progress_content.append(f"   ⏳ {phase}\n", style="bright_blue")
        
        progress_panel = Panel(
            progress_content,
            title="[bold cyan]📊 Progress Overview 📊[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=60
        )
        
        self.console.print()
        self.console.print(progress_panel)
        self.console.print()
        
    def create_branded_panel(self, content: str, title: str, panel_type: str = "info") -> Panel:
        """
        Create a branded panel with consistent styling and TrustyOldLuma branding.
        
        Args:
            content: Panel content
            title: Panel title
            panel_type: Type of panel (info, success, error, warning, admin)
            
        Returns:
            Panel: Styled Rich panel
        """
        # Define panel styles based on type
        panel_styles = {
            "info": {"border": "cyan", "title_style": "bold cyan", "emoji": "ℹ️"},
            "success": {"border": "green", "title_style": "bold green", "emoji": "✅"},
            "error": {"border": "red", "title_style": "bold red", "emoji": "❌"},
            "warning": {"border": "yellow", "title_style": "bold yellow", "emoji": "⚠️"},
            "admin": {"border": "red", "title_style": "bold red", "emoji": "🔐"},
            "download": {"border": "blue", "title_style": "bold blue", "emoji": "📥"},
            "config": {"border": "magenta", "title_style": "bold magenta", "emoji": "⚙️"},
            "complete": {"border": "green", "title_style": "bold green", "emoji": "🎉"}
        }
        
        style = panel_styles.get(panel_type, panel_styles["info"])
        
        # Add branding to title
        branded_title = f"[{style['title_style']}]{style['emoji']} {title} - TrustyOldLuma {style['emoji']}[/{style['title_style']}]"
        
        return Panel(
            content,
            title=branded_title,
            border_style=style["border"],
            padding=(1, 2),
            width=70
        )
    
    def show_platform_detection_panel(self, platforms: Dict[str, bool]) -> None:
        """
        Display platform detection results with visual indicators.
        
        Args:
            platforms: Dictionary mapping platform names to detection status
        """
        detection_content = Text()
        detection_content.append("🔍 Gaming Platform Detection Results\n\n", style="bold bright_cyan")
        
        detected_count = sum(platforms.values())
        total_count = len(platforms)
        
        detection_content.append(f"Found {detected_count}/{total_count} gaming platforms installed\n\n", style="bright_white")
        
        for platform, detected in platforms.items():
            if detected:
                detection_content.append(f"   ✅ {platform} - Detected and ready for integration\n", style="bright_green")
            else:
                detection_content.append(f"   ❌ {platform} - Not detected\n", style="dim white")
        
        if detected_count > 0:
            detection_content.append(f"\n🎮 Proceeding with integration for {detected_count} platform(s)", style="bold bright_green")
        else:
            detection_content.append(f"\n⚠️  No platforms detected - setup will continue with basic configuration", style="bold bright_yellow")
        
        detection_panel = Panel(
            detection_content,
            title="[bold cyan]🔍 Platform Detection 🔍[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=70
        )
        
        self.console.print()
        self.console.print(detection_panel)
        self.console.print()
    
    def show_unified_installation_status(self, greenluma_status: str, koalageddon_status: str, 
                                       platform_integrations: int = 0) -> None:
        """
        Display unified installation status for both tools.
        
        Args:
            greenluma_status: Status message for GreenLuma
            koalageddon_status: Status message for Koalageddon
            platform_integrations: Number of completed platform integrations
        """
        status_content = Text()
        status_content.append("🎮 Unified Gaming Tools Installation Status\n\n", style="bold bright_cyan")
        
        # GreenLuma status
        status_content.append("🟢 GreenLuma (Steam Sharing):\n", style="bold bright_green")
        status_content.append(f"   {greenluma_status}\n\n", style="bright_white")
        
        # Koalageddon status
        status_content.append("🟣 Koalageddon (DLC Unlocker):\n", style="bold bright_magenta")
        status_content.append(f"   {koalageddon_status}\n\n", style="bright_white")
        
        # Platform integrations
        if platform_integrations > 0:
            status_content.append("🔗 Platform Integrations:\n", style="bold bright_blue")
            status_content.append(f"   ✅ {platform_integrations} platform(s) integrated successfully\n", style="bright_green")
        
        status_panel = Panel(
            status_content,
            title="[bold cyan]📊 Installation Status 📊[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=70
        )
        
        self.console.print()
        self.console.print(status_panel)
        self.console.print()
    
    def show_unified_completion_summary(self, completed_operations: List[str], 
                                      shortcuts_created: int = 0,
                                      platforms_integrated: int = 0) -> None:
        """
        Display comprehensive completion summary for unified setup.
        
        Args:
            completed_operations: List of successfully completed operations
            shortcuts_created: Number of shortcuts created
            platforms_integrated: Number of platforms integrated
        """
        summary_content = Text()
        summary_content.append("🎉 UNIFIED SETUP COMPLETED SUCCESSFULLY! 🎉\n\n", style="bold bright_green")
        
        summary_content.append("📋 Installation Summary:\n", style="bold bright_cyan")
        
        # Completed operations
        if completed_operations:
            for operation in completed_operations:
                summary_content.append(f"   ✅ {operation}\n", style="bright_green")
        
        summary_content.append(f"\n🔗 Created {shortcuts_created} desktop shortcut(s)\n", style="bright_blue")
        summary_content.append(f"🎮 Integrated with {platforms_integrated} gaming platform(s)\n", style="bright_blue")
        
        # Next steps
        summary_content.append("\n🚀 What's Next:\n", style="bold bright_yellow")
        summary_content.append("   1. Launch GreenLuma from your desktop shortcut\n", style="bright_white")
        summary_content.append("   2. Open Koalageddon to verify configuration\n", style="bright_white")
        summary_content.append("   3. Start your favorite games and enjoy!\n", style="bright_white")
        
        # Support information
        summary_content.append("\n💝 Support the Project:\n", style="bold bright_magenta")
        summary_content.append("   ⭐ Star us on GitHub: https://github.com/armand0e/TrustyOldLuma\n", style="bright_white")
        summary_content.append("   🤝 Share with friends and fellow gamers\n", style="bright_white")
        
        completion_panel = Panel(
            Align.center(summary_content),
            title="[bold green]🎉 SETUP COMPLETE 🎉[/bold green]",
            border_style="green",
            padding=(2, 3),
            width=80
        )
        
        self.console.print()
        self.console.print(completion_panel)
        self.console.print()
        
        # Celebratory pause
        self.prompt_continue("Press Enter to exit setup...")
    
    def show_embedded_installation_progress(self, current_step: str, step_number: int, total_steps: int) -> None:
        """
        Show progress for embedded installation steps.
        
        Args:
            current_step: Description of current step
            step_number: Current step number
            total_steps: Total number of steps
        """
        progress_content = Text()
        progress_content.append(f"Step {step_number}/{total_steps}: {current_step}\n", style="bold bright_cyan")
        
        # Create a simple progress bar
        filled = "█" * step_number
        empty = "░" * (total_steps - step_number)
        progress_bar = f"[{filled}{empty}]"
        
        progress_content.append(f"\nProgress: {progress_bar} {step_number}/{total_steps}\n", style="bright_yellow")
        progress_content.append(f"Estimated time remaining: {(total_steps - step_number) * 10} seconds", style="dim white")
        
        progress_panel = Panel(
            progress_content,
            title="[bold blue]📦 Embedded Installation 📦[/bold blue]",
            border_style="blue",
            padding=(1, 2),
            width=60
        )
        
        self.console.print(progress_panel)
    
    def show_validation_results(self, validation_results: Dict[str, bool]) -> None:
        """
        Display validation results for the unified setup.
        
        Args:
            validation_results: Dictionary of validation results
        """
        validation_content = Text()
        validation_content.append("🔍 Setup Validation Results\n\n", style="bold bright_cyan")
        
        success_count = sum(validation_results.values())
        total_count = len(validation_results)
        
        for component, validated in validation_results.items():
            if validated:
                validation_content.append(f"   ✅ {component} - Validated successfully\n", style="bright_green")
            else:
                validation_content.append(f"   ❌ {component} - Validation failed\n", style="bright_red")
        
        validation_content.append(f"\n📊 Overall: {success_count}/{total_count} components validated", style="bold bright_white")
        
        if success_count == total_count:
            validation_content.append("\n🎉 All validations passed!", style="bold bright_green")
            border_style = "green"
        elif success_count > 0:
            validation_content.append("\n⚠️  Partial validation - some components may not work correctly", style="bold bright_yellow")
            border_style = "yellow"
        else:
            validation_content.append("\n❌ Validation failed - setup may need to be re-run", style="bold bright_red")
            border_style = "red"
        
        validation_panel = Panel(
            validation_content,
            title="[bold cyan]🔍 Validation Results 🔍[/bold cyan]",
            border_style=border_style,
            padding=(1, 2),
            width=70
        )
        
        self.console.print()
        self.console.print(validation_panel)
        self.console.print()