#!/usr/bin/env python3
"""
Unit tests for display managers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console
from display_managers import (
    ProgressDisplayManager,
    ErrorDisplayManager,
    WelcomeScreenManager,
    CompletionScreenManager,
    ProgressContext
)
from models import LunaResults


class TestProgressDisplayManager:
    """Test cases for ProgressDisplayManager."""
    
    def test_initialization(self):
        """Test ProgressDisplayManager initialization."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        
        assert manager.console == console
        assert manager.current_progress is None
        assert manager.active_tasks == {}
    
    def test_create_progress_bar(self):
        """Test progress bar creation."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        
        context = manager.create_progress_bar("Test operation", 100)
        
        assert isinstance(context, ProgressContext)
        assert context.description == "Test operation"
        assert context.total == 100
    
    def test_create_progress_bar_no_total(self):
        """Test progress bar creation without total."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        
        context = manager.create_progress_bar("Test operation")
        
        assert isinstance(context, ProgressContext)
        assert context.description == "Test operation"
        assert context.total == 100  # Default value
    
    @patch('display_managers.Live')
    @patch('display_managers.Spinner')
    def test_show_spinner(self, mock_spinner, mock_live):
        """Test spinner display."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        
        with manager.show_spinner("Testing..."):
            pass
        
        mock_spinner.assert_called_once_with("dots", text="Testing...", style="cyan")
        mock_live.assert_called_once()


class TestProgressContext:
    """Test cases for ProgressContext."""
    
    def test_initialization(self):
        """Test ProgressContext initialization."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        
        context = ProgressContext(manager, "Test", 50)
        
        assert context.manager == manager
        assert context.description == "Test"
        assert context.total == 50
        assert context.task_id is None
        assert context.progress is None
    
    @patch('display_managers.Progress')
    def test_context_manager(self, mock_progress_class):
        """Test ProgressContext as context manager."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        mock_progress = Mock()
        mock_progress_class.return_value = mock_progress
        mock_progress.add_task.return_value = "task_id"
        
        context = ProgressContext(manager, "Test", 50)
        
        with context as ctx:
            assert ctx == context
            assert context.progress == mock_progress
            assert context.task_id == "task_id"
            mock_progress.start.assert_called_once()
            mock_progress.add_task.assert_called_once_with("Test", total=50)
        
        mock_progress.stop.assert_called_once()
    
    def test_update(self):
        """Test progress update."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        context = ProgressContext(manager, "Test", 50)
        
        # Mock progress and task_id
        context.progress = Mock()
        context.task_id = "test_task"
        
        context.update(10, "New description")
        
        context.progress.update.assert_called_once_with(
            "test_task", 
            advance=10, 
            description="New description"
        )
    
    def test_set_total(self):
        """Test setting total steps."""
        console = Mock(spec=Console)
        manager = ProgressDisplayManager(console)
        context = ProgressContext(manager, "Test", 50)
        
        # Mock progress and task_id
        context.progress = Mock()
        context.task_id = "test_task"
        
        context.set_total(200)
        
        context.progress.update.assert_called_once_with("test_task", total=200)


class TestErrorDisplayManager:
    """Test cases for ErrorDisplayManager."""
    
    def test_initialization(self):
        """Test ErrorDisplayManager initialization."""
        console = Mock(spec=Console)
        manager = ErrorDisplayManager(console)
        
        assert manager.console == console
    
    def test_display_error(self):
        """Test error display."""
        console = Mock(spec=Console)
        manager = ErrorDisplayManager(console)
        
        error = ValueError("Test error")
        manager.display_error(error, "Test context", "Test suggestion")
        
        # Verify console.print was called
        assert console.print.call_count >= 3  # Empty lines + panel
    
    def test_display_warning(self):
        """Test warning display."""
        console = Mock(spec=Console)
        manager = ErrorDisplayManager(console)
        
        manager.display_warning("Test warning", "Test suggestion")
        
        # Verify console.print was called
        assert console.print.call_count >= 3  # Empty lines + panel
    
    def test_display_success(self):
        """Test success display."""
        console = Mock(spec=Console)
        manager = ErrorDisplayManager(console)
        
        manager.display_success("Test success", "Test details")
        
        # Verify console.print was called
        assert console.print.call_count >= 3  # Empty lines + panel
    
    @patch('display_managers.Confirm.ask')
    def test_display_retry_prompt_retry(self, mock_confirm):
        """Test retry prompt when retry is possible."""
        console = Mock(spec=Console)
        manager = ErrorDisplayManager(console)
        mock_confirm.return_value = True
        
        result = manager.display_retry_prompt("Test operation", 1, 3)
        
        assert result is True
        mock_confirm.assert_called_once()
    
    def test_display_retry_prompt_max_attempts(self):
        """Test retry prompt when max attempts reached."""
        console = Mock(spec=Console)
        manager = ErrorDisplayManager(console)
        
        result = manager.display_retry_prompt("Test operation", 3, 3)
        
        assert result is False
        console.print.assert_called()


class TestWelcomeScreenManager:
    """Test cases for WelcomeScreenManager."""
    
    def test_initialization(self):
        """Test WelcomeScreenManager initialization."""
        console = Mock(spec=Console)
        manager = WelcomeScreenManager(console)
        
        assert manager.console == console
    
    @patch('builtins.input', return_value='')
    def test_display_welcome(self, mock_input):
        """Test welcome screen display."""
        console = Mock(spec=Console)
        manager = WelcomeScreenManager(console)
        
        manager.display_welcome()
        
        # Verify console.print was called multiple times
        assert console.print.call_count >= 5  # Multiple panels and spacing
        mock_input.assert_called_once()


class TestCompletionScreenManager:
    """Test cases for CompletionScreenManager."""
    
    def test_initialization(self):
        """Test CompletionScreenManager initialization."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        
        assert manager.console == console
    
    def test_create_summary_table_empty_results(self):
        """Test summary table creation with empty results."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        results = SetupResults()
        
        table = manager._create_summary_table(results)
        
        # Should return a table even with empty results
        assert table is not None
    
    def test_create_summary_table_with_data(self):
        """Test summary table creation with data."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        results = SetupResults()
        
        # Add some test data
        results.directories_created = ["/test/path1", "/test/path2"]
        results.exclusions_added = [("/test/path1", True), ("/test/path2", False)]
        results.files_extracted = True
        results.mark_extraction_attempted()
        
        table = manager._create_summary_table(results)
        
        assert table is not None
    
    def test_create_next_steps_panel_success(self):
        """Test next steps panel for successful setup."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        results = SetupResults()
        results.directories_created = ["/test/path"]  # High success rate
        
        panel = manager._create_next_steps_panel(results)
        
        assert panel is not None
    
    def test_create_next_steps_panel_failure(self):
        """Test next steps panel for failed setup."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        results = SetupResults()
        results.add_error("Test error")  # Low success rate
        
        panel = manager._create_next_steps_panel(results)
        
        assert panel is not None
    
    def test_display_errors(self):
        """Test error display in completion screen."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        
        errors = ["Error 1", "Error 2"]
        manager._display_errors(errors)
        
        # Verify console.print was called
        assert console.print.call_count >= 2
    
    def test_display_warnings(self):
        """Test warning display in completion screen."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        
        warnings = ["Warning 1", "Warning 2"]
        manager._display_warnings(warnings)
        
        # Verify console.print was called
        assert console.print.call_count >= 2
    
    def test_display_errors_empty_list(self):
        """Test error display with empty list."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        
        manager._display_errors([])
        
        # Should not call console.print for empty list
        console.print.assert_not_called()
    
    def test_display_warnings_empty_list(self):
        """Test warning display with empty list."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        
        manager._display_warnings([])
        
        # Should not call console.print for empty list
        console.print.assert_not_called()
    
    @patch('builtins.input', return_value='')
    def test_display_completion(self, mock_input):
        """Test complete completion screen display."""
        console = Mock(spec=Console)
        manager = CompletionScreenManager(console)
        results = SetupResults()
        results.directories_created = ["/test/path"]
        
        manager.display_completion(results)
        
        # Verify console.print was called multiple times
        assert console.print.call_count >= 5
        mock_input.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])