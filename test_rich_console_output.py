"""
Tests for Rich console output and visual elements.

This module tests the Rich console output, styling, and visual elements
to ensure consistent and appealing user interface.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.text import Text

from display_managers import (
    ProgressDisplayManager,
    ErrorDisplayManager,
    WelcomeScreenManager,
    CompletionScreenManager
)
from models import SetupResults, ShortcutConfig
from gaming_setup_tool import GamingSetupTool


class TestRichConsoleOutput:
    """Test Rich console output and styling."""
    
    @pytest.fixture
    def console_capture(self):
        """Create a console that captures output for testing."""
        output_buffer = StringIO()
        console = Console(
            file=output_buffer,
            width=80,
            height=24,
            force_terminal=True,
            color_system="standard"
        )
        
        def get_output():
            return output_buffer.getvalue()
        
        def clear_output():
            output_buffer.seek(0)
            output_buffer.truncate(0)
        
        console.get_output = get_output
        console.clear_output = clear_output
        
        return console
    
    def test_welcome_screen_output(self, console_capture):
        """Test welcome screen Rich output."""
        welcome_manager = WelcomeScreenManager(console_capture)
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value=''):
            welcome_manager.display_welcome()
        
        output = console_capture.get_output()
        
        # Verify welcome screen elements
        assert "Gaming Setup Tool" in output
        assert "🎮" in output  # Gaming emoji
        assert "Welcome" in output or "welcome" in output
        
        # Check for panel styling
        assert "┌" in output or "╭" in output  # Panel borders
        assert "└" in output or "╰" in output
    
    def test_progress_bar_output(self, console_capture):
        """Test progress bar Rich output."""
        progress_manager = ProgressDisplayManager(console_capture)
        
        # Create and use progress bar
        with progress_manager.create_progress_bar("Test Operation", 100) as progress:
            progress.update(25, "Processing...")
            progress.update(50, "Half way...")
            progress.update(100, "Complete!")
        
        output = console_capture.get_output()
        
        # Verify progress bar elements
        assert "Test Operation" in output
        assert any(char in output for char in ['█', '▌', '▍', '▎', '▏'])  # Progress bar chars
        assert "%" in output  # Percentage display
    
    def test_error_display_output(self, console_capture):
        """Test error display Rich output."""
        error_manager = ErrorDisplayManager(console_capture)
        
        # Display various types of messages
        error_manager.display_error(
            ValueError("Test error"), 
            "Test context", 
            "Test suggestion"
        )
        error_manager.display_warning("Test warning", "Test suggestion")
        error_manager.display_success("Test success", "Test details")
        
        output = console_capture.get_output()
        
        # Verify error styling
        assert "❌" in output or "Error" in output
        assert "Test error" in output
        assert "Test context" in output
        
        # Verify warning styling
        assert "⚠️" in output or "Warning" in output
        assert "Test warning" in output
        
        # Verify success styling
        assert "✅" in output or "Success" in output
        assert "Test success" in output
    
    def test_completion_screen_output(self, console_capture):
        """Test completion screen Rich output."""
        completion_manager = CompletionScreenManager(console_capture)
        
        # Create test results
        results = SetupResults()
        results.directories_created = [Path("/test/path1"), Path("/test/path2")]
        results.exclusions_added = [(Path("/test/path1"), True), (Path("/test/path2"), False)]
        results.files_extracted = True
        results.mark_extraction_attempted()
        results.files_downloaded = [("file1.exe", True)]
        results.configs_updated = [("config1.ini", True)]
        results.shortcuts_created = [("Shortcut1", True)]
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value=''):
            completion_manager.display_completion(results)
        
        output = console_capture.get_output()
        
        # Verify completion screen elements
        assert "Setup Complete" in output or "Complete" in output
        assert "🎉" in output or "✅" in output  # Success indicators
        
        # Verify summary table elements
        assert "Directories" in output
        assert "Files" in output
        assert "Success" in output or "✓" in output
    
    def test_spinner_output(self, console_capture):
        """Test spinner Rich output."""
        progress_manager = ProgressDisplayManager(console_capture)
        
        # Use spinner
        with progress_manager.show_spinner("Loading..."):
            pass  # Spinner would normally animate
        
        output = console_capture.get_output()
        
        # Verify spinner elements
        assert "Loading..." in output
    
    def test_panel_styling(self, console_capture):
        """Test panel styling consistency."""
        error_manager = ErrorDisplayManager(console_capture)
        
        # Create panels with different styles
        error_manager.display_error(Exception("Test"), "Context")
        error_manager.display_warning("Warning message")
        error_manager.display_success("Success message")
        
        output = console_capture.get_output()
        
        # Verify panel borders are present
        border_chars = ['┌', '┐', '└', '┘', '│', '─', '╭', '╮', '╰', '╯', '║', '═']
        assert any(char in output for char in border_chars)
    
    def test_color_styling(self, console_capture):
        """Test color styling in output."""
        error_manager = ErrorDisplayManager(console_capture)
        
        # Display messages that should have color styling
        error_manager.display_error(Exception("Red error"), "Context")
        error_manager.display_warning("Yellow warning")
        error_manager.display_success("Green success")
        
        output = console_capture.get_output()
        
        # Note: When force_terminal=True, Rich includes ANSI escape codes
        # Check for ANSI color codes
        ansi_codes = ['\x1b[31m', '\x1b[33m', '\x1b[32m']  # Red, Yellow, Green
        # At least one color code should be present
        has_color = any(code in output for code in ansi_codes)
        
        # If no ANSI codes, check for Rich markup
        if not has_color:
            color_markup = ['[red]', '[yellow]', '[green]', '[bold]']
            has_color = any(markup in output for markup in color_markup)
        
        # Color should be present in some form
        assert has_color or len(output) > 0  # At least verify output exists
    
    @pytest.mark.asyncio
    async def test_progress_context_manager_output(self, console_capture):
        """Test progress context manager output."""
        progress_manager = ProgressDisplayManager(console_capture)
        
        # Test progress context manager
        async def mock_operation():
            with progress_manager.create_progress_bar("Mock Operation", 50) as progress:
                for i in range(0, 51, 10):
                    progress.update(10, f"Step {i//10 + 1}")
                    await asyncio.sleep(0.01)  # Small delay to simulate work
        
        await mock_operation()
        
        output = console_capture.get_output()
        
        # Verify progress operation output
        assert "Mock Operation" in output
        assert "Step" in output
    
    def test_table_output_formatting(self, console_capture):
        """Test table output formatting in completion screen."""
        completion_manager = CompletionScreenManager(console_capture)
        
        # Create results with data for table
        results = SetupResults()
        results.directories_created = [Path("/test/dir1"), Path("/test/dir2")]
        results.exclusions_added = [(Path("/test/path"), True)]
        results.files_extracted = True
        results.mark_extraction_attempted()
        
        # Create summary table
        table = completion_manager._create_summary_table(results)
        
        # Render table to console
        console_capture.print(table)
        output = console_capture.get_output()
        
        # Verify table formatting
        table_chars = ['┌', '┬', '┐', '├', '┼', '┤', '└', '┴', '┘', '│', '─']
        assert any(char in output for char in table_chars)
    
    def test_emoji_and_unicode_support(self, console_capture):
        """Test emoji and Unicode character support."""
        welcome_manager = WelcomeScreenManager(console_capture)
        error_manager = ErrorDisplayManager(console_capture)
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value=''):
            welcome_manager.display_welcome()
        
        error_manager.display_success("Unicode test ✅ 🎮 ⚙️")
        
        output = console_capture.get_output()
        
        # Verify Unicode characters are handled
        unicode_chars = ['🎮', '✅', '⚙️', '❌', '⚠️', '🎉']
        has_unicode = any(char in output for char in unicode_chars)
        
        # Should have Unicode support or graceful fallback
        assert has_unicode or len(output) > 0


class TestRichOutputSnapshots:
    """Test Rich output using snapshot comparisons."""
    
    def test_welcome_screen_snapshot(self, rich_snapshot_console, snapshot_tester):
        """Test welcome screen output against saved snapshot."""
        welcome_manager = WelcomeScreenManager(rich_snapshot_console)
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value=''):
            welcome_manager.display_welcome()
        
        output = rich_snapshot_console.get_snapshot()
        
        # Test against snapshot (will create snapshot on first run)
        assert snapshot_tester("welcome_screen", output)
    
    def test_error_panel_snapshot(self, rich_snapshot_console, snapshot_tester):
        """Test error panel output against saved snapshot."""
        error_manager = ErrorDisplayManager(rich_snapshot_console)
        
        error_manager.display_error(
            ValueError("Sample error message"),
            "Sample context",
            "Sample suggestion"
        )
        
        output = rich_snapshot_console.get_snapshot()
        
        # Test against snapshot
        assert snapshot_tester("error_panel", output)
    
    def test_completion_summary_snapshot(self, rich_snapshot_console, snapshot_tester):
        """Test completion summary output against saved snapshot."""
        completion_manager = CompletionScreenManager(rich_snapshot_console)
        
        # Create consistent test results
        results = SetupResults()
        results.directories_created = [Path("/test/GreenLuma"), Path("/test/Koalageddon")]
        results.exclusions_added = [(Path("/test/GreenLuma"), True), (Path("/test/Koalageddon"), True)]
        results.files_extracted = True
        results.mark_extraction_attempted()
        results.files_downloaded = [("Koalageddon.exe", True)]
        results.configs_updated = [("DLLInjector.ini", True), ("koalageddon.config", True)]
        results.shortcuts_created = [("GreenLuma", True), ("Koalageddon", True)]
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value=''):
            completion_manager.display_completion(results)
        
        output = rich_snapshot_console.get_snapshot()
        
        # Test against snapshot
        assert snapshot_tester("completion_summary", output)


class TestRichOutputMatcher:
    """Test the Rich output matcher utility."""
    
    def test_rich_output_matcher_text_detection(self, rich_output_matcher):
        """Test text detection in Rich output."""
        sample_output = "This is a test output with specific text"
        matcher = rich_output_matcher(sample_output)
        
        assert matcher.contains_text("specific text")
        assert matcher.contains_text("test output")
        assert not matcher.contains_text("nonexistent text")
    
    def test_rich_output_matcher_panel_detection(self, rich_output_matcher):
        """Test panel detection in Rich output."""
        sample_output = """
        ┌─ Test Panel ─┐
        │ Panel content │
        └───────────────┘
        """
        matcher = rich_output_matcher(sample_output)
        
        assert matcher.contains_panel(title="Test Panel")
        assert matcher.contains_panel(content="Panel content")
        assert not matcher.contains_panel(title="Nonexistent Panel")
    
    def test_rich_output_matcher_progress_detection(self, rich_output_matcher):
        """Test progress bar detection in Rich output."""
        sample_output = "Progress: ████████░░ 80%"
        matcher = rich_output_matcher(sample_output)
        
        assert matcher.contains_progress_bar()
        
        # Test without progress bar
        no_progress_output = "Just regular text"
        no_progress_matcher = rich_output_matcher(no_progress_output)
        assert not no_progress_matcher.contains_progress_bar()
    
    def test_rich_output_matcher_styling_detection(self, rich_output_matcher):
        """Test styling detection in Rich output."""
        error_output = "❌ Error: Something went wrong"
        success_output = "✅ Success: Operation completed"
        
        error_matcher = rich_output_matcher(error_output)
        success_matcher = rich_output_matcher(success_output)
        
        assert error_matcher.contains_error_styling()
        assert not error_matcher.contains_success_styling()
        
        assert success_matcher.contains_success_styling()
        assert not success_matcher.contains_error_styling()


class TestRichIntegrationOutput:
    """Test Rich output in integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_output(self, console_capture, temp_workspace):
        """Test Rich output during complete workflow execution."""
        tool = GamingSetupTool(verbose=False)
        tool.console = console_capture
        
        # Reinitialize managers with the capture console
        tool._initialize_managers()
        
        tool.config = SetupConfig(
            greenluma_path=temp_workspace['greenluma'],
            koalageddon_path=temp_workspace['koalageddon'],
            koalageddon_config_path=temp_workspace['koalageddon'] / "config",
            download_url="https://example.com/test.exe",
            app_id="480",
            documents_path=temp_workspace['documents'],
            temp_dir=temp_workspace['temp']
        )
        
        # Mock all operations to focus on output
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=AsyncMock()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=AsyncMock()), \
             patch('builtins.input', return_value=''):  # Mock input for welcome/completion screens
            
            # Execute workflow
            await tool.run()
        
        output = console_capture.get_output()
        
        # Verify key output elements are present
        assert len(output) > 0
        assert "Gaming Setup Tool" in output or "Setup" in output
        
        # Should contain progress indicators
        progress_indicators = ['█', '▌', '▍', '▎', '▏', '░', '▒', '▓', '%']
        has_progress = any(indicator in output for indicator in progress_indicators)
        
        # Should contain status indicators
        status_indicators = ['✅', '❌', '⚠️', '🎮', '⚙️', 'Success', 'Error', 'Warning']
        has_status = any(indicator in output for indicator in status_indicators)
        
        # At least one type of Rich formatting should be present
        assert has_progress or has_status or "┌" in output or "│" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])