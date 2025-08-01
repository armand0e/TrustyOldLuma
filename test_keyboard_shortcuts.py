"""Test keyboard shortcuts and navigation improvements."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from rich.console import Console

from src.ui_manager import UIManager
from src.setup_controller import SetupController


class TestKeyboardShortcuts:
    """Test keyboard shortcuts and navigation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console(file=StringIO(), width=80)
        self.ui = UIManager(console=self.console)
        
    def test_interrupt_handler_setup(self):
        """Test that interrupt handler is properly set up."""
        # Test that interrupt handler can be set
        handler_called = False
        
        def test_handler():
            nonlocal handler_called
            handler_called = True
            
        self.ui.set_interrupt_handler(test_handler)
        assert self.ui._interrupt_handler == test_handler
        
        # Simulate interrupt
        self.ui._interrupt_handler()
        assert handler_called
        
    def test_prompt_continue(self):
        """Test Enter key continuation prompts."""
        with patch('builtins.input', return_value=''):
            result = self.ui.prompt_continue("Test continue prompt")
            assert result is True
            
        # Test keyboard interrupt
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            result = self.ui.prompt_continue("Test continue prompt")
            assert result is False
            assert self.ui.was_interrupted()
            
    def test_prompt_confirmation(self):
        """Test confirmation dialog with keyboard navigation."""
        with patch('rich.prompt.Confirm.ask', return_value=True):
            result = self.ui.prompt_confirmation("Test confirmation?")
            assert result is True
            
        with patch('rich.prompt.Confirm.ask', return_value=False):
            result = self.ui.prompt_confirmation("Test confirmation?")
            assert result is False
            
        # Test keyboard interrupt
        with patch('rich.prompt.Confirm.ask', side_effect=KeyboardInterrupt):
            result = self.ui.prompt_confirmation("Test confirmation?")
            assert result is None
            assert self.ui.was_interrupted()
            
    def test_prompt_choice(self):
        """Test choice prompt with keyboard navigation."""
        choices = ["option1", "option2", "option3"]
        
        with patch('rich.prompt.Prompt.ask', return_value="option2"):
            result = self.ui.prompt_choice("Select option:", choices)
            assert result == "option2"
            
        # Test keyboard interrupt
        with patch('rich.prompt.Prompt.ask', side_effect=KeyboardInterrupt):
            result = self.ui.prompt_choice("Select option:", choices)
            assert result is None
            assert self.ui.was_interrupted()
            
    def test_show_menu(self):
        """Test interactive menu with keyboard navigation."""
        options = {
            "start": "Start process",
            "help": "Show help",
            "exit": "Exit"
        }
        
        with patch('rich.prompt.Prompt.ask', return_value="1"):
            result = self.ui.show_menu("Test Menu", options)
            assert result == "start"
            
        with patch('rich.prompt.Prompt.ask', return_value="2"):
            result = self.ui.show_menu("Test Menu", options)
            assert result == "help"
            
        # Test keyboard interrupt
        with patch('rich.prompt.Prompt.ask', side_effect=KeyboardInterrupt):
            result = self.ui.show_menu("Test Menu", options, allow_cancel=True)
            assert result is None
            
    def test_show_scrollable_content(self):
        """Test scrollable content display."""
        # Test short content (no scrolling needed)
        short_content = "This is short content"
        self.ui.show_scrollable_content(short_content, "Test Title")
        
        # Test long content (would trigger scrolling)
        long_content = "\n".join([f"Line {i}" for i in range(100)])
        with patch.object(self.ui.console, 'pager') as mock_pager:
            self.ui.show_scrollable_content(long_content, "Test Title")
            # Verify pager was used for long content
            mock_pager.assert_called_once()
            
    def test_progress_with_cancel(self):
        """Test cancellable progress bar."""
        cancel_called = False
        
        def cancel_callback():
            nonlocal cancel_called
            cancel_called = True
            
        progress = self.ui.show_progress_with_cancel("Test progress", 100, cancel_callback)
        assert progress is not None
        
        # Simulate setting the cancel handler
        assert self.ui._interrupt_handler is not None
        
    def test_interactive_status(self):
        """Test cancellable status spinner."""
        cancel_called = False
        
        def cancel_callback():
            nonlocal cancel_called
            cancel_called = True
            
        status = self.ui.show_interactive_status("Test status", cancel_callback)
        assert status is not None
        
        # Simulate setting the cancel handler
        assert self.ui._interrupt_handler is not None
        
    def test_interrupt_flag_management(self):
        """Test interrupt flag management."""
        # Initially not interrupted
        assert not self.ui.was_interrupted()
        
        # Set interrupted flag
        self.ui._keyboard_interrupt_received = True
        assert self.ui.was_interrupted()
        
        # Reset flag
        self.ui.reset_interrupt_flag()
        assert not self.ui.was_interrupted()
        
    def test_help_text_display(self):
        """Test help text display with keyboard shortcuts."""
        help_content = "This is additional help content"
        
        with patch.object(self.ui, 'show_scrollable_content') as mock_scrollable:
            self.ui.show_help_text(help_content)
            mock_scrollable.assert_called_once()
            
    def test_phase_transition_display(self):
        """Test phase transition display with Enter prompt."""
        with patch.object(self.ui, 'prompt_continue') as mock_prompt:
            self.ui.display_phase_transition("Phase 1", "Phase 2")
            mock_prompt.assert_called_once_with("Press Enter to continue to the next phase...")


class TestSetupControllerKeyboardIntegration:
    """Test keyboard integration in setup controller."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console(file=StringIO(), width=80)
        
    @patch('src.setup_controller.AdminHandler')
    @patch('src.setup_controller.FileOperationsManager')
    @patch('src.setup_controller.DownloadManager')
    @patch('src.setup_controller.ConfigurationManager')
    @patch('src.setup_controller.ErrorHandler')
    def test_setup_options_menu(self, mock_error, mock_config, mock_download, mock_file, mock_admin):
        """Test setup options menu functionality."""
        controller = SetupController()
        
        # Test start option
        with patch.object(controller.ui, 'show_menu', return_value="start"):
            result = controller._show_setup_options_menu()
            assert result == "start"
            
        # Test help option
        with patch.object(controller.ui, 'show_menu', return_value="help"):
            result = controller._show_setup_options_menu()
            assert result == "help"
            
        # Test exit option
        with patch.object(controller.ui, 'show_menu', return_value="exit"):
            result = controller._show_setup_options_menu()
            assert result is None
            
        # Test cancel (None)
        with patch.object(controller.ui, 'show_menu', return_value=None):
            result = controller._show_setup_options_menu()
            assert result is None
            
    @patch('src.setup_controller.AdminHandler')
    @patch('src.setup_controller.FileOperationsManager')
    @patch('src.setup_controller.DownloadManager')
    @patch('src.setup_controller.ConfigurationManager')
    @patch('src.setup_controller.ErrorHandler')
    def test_graceful_shutdown_handler(self, mock_error, mock_config, mock_download, mock_file, mock_admin):
        """Test graceful shutdown handler setup."""
        controller = SetupController()
        
        # Verify that interrupt handler is set on UI
        assert controller.ui._interrupt_handler is not None
        
        # Test that the handler performs cleanup
        with patch.object(controller, '_cleanup_on_exit') as mock_cleanup:
            with patch('sys.exit') as mock_exit:
                # Simulate interrupt handler call
                controller.ui._interrupt_handler()
                mock_cleanup.assert_called_once()
                mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main([__file__])