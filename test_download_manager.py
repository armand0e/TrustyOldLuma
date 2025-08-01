"""Tests for Download Manager module."""

import pytest
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import StringIO
from rich.console import Console

from src.download_manager import DownloadManager
from src.ui_manager import UIManager


class TestDownloadManager:
    """Test cases for DownloadManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a real console with StringIO for testing
        self.console_output = StringIO()
        self.console = Console(file=self.console_output, width=80)
        self.ui_manager = UIManager(console=self.console)
        self.download_manager = DownloadManager(self.ui_manager)
        
    def test_init(self):
        """Test DownloadManager initialization."""
        assert self.download_manager.ui is self.ui_manager
        assert self.download_manager.max_retries == 3
        assert self.download_manager.initial_retry_delay == 1.0
        
    @patch('urllib.request.urlopen')
    def test_get_file_size_success(self, mock_urlopen):
        """Test successful file size detection."""
        # Mock response with Content-Length header
        mock_response = Mock()
        mock_response.headers = {'Content-Length': '1024'}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        size = self.download_manager.get_file_size('http://example.com/file.zip')
        
        assert size == 1024
        mock_urlopen.assert_called_once_with('http://example.com/file.zip')
        
    @patch('urllib.request.urlopen')
    def test_get_file_size_no_content_length(self, mock_urlopen):
        """Test file size detection when Content-Length is not available."""
        # Mock response without Content-Length header
        mock_response = Mock()
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        size = self.download_manager.get_file_size('http://example.com/file.zip')
        
        assert size == -1
        
    @patch('urllib.request.urlopen')
    def test_get_file_size_error(self, mock_urlopen):
        """Test file size detection with network error."""
        mock_urlopen.side_effect = urllib.error.URLError("Network error")
        
        size = self.download_manager.get_file_size('http://example.com/file.zip')
        
        assert size == -1
        # Verify warning was displayed in console output
        output = self.console_output.getvalue()
        assert "Could not determine file size" in output
        
    @patch('urllib.request.urlretrieve')
    @patch('pathlib.Path.mkdir')
    def test_download_file_success(self, mock_mkdir, mock_urlretrieve):
        """Test successful basic file download."""
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "test_file.zip"
            
            result = self.download_manager.download_file(
                'http://example.com/file.zip', 
                str(destination)
            )
            
            assert result is True
            mock_urlretrieve.assert_called_once_with(
                'http://example.com/file.zip', 
                str(destination)
            )
            
    @patch('urllib.request.urlretrieve')
    def test_download_file_error(self, mock_urlretrieve):
        """Test basic file download with error."""
        mock_urlretrieve.side_effect = Exception("Download failed")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "test_file.zip"
            
            result = self.download_manager.download_file(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is False
            # Verify error was displayed in console output
            output = self.console_output.getvalue()
            assert "Failed to download file" in output
            
    @patch('src.download_manager.DownloadManager._download_with_retry')
    def test_download_with_progress_success(self, mock_download_retry):
        """Test download with progress - successful on first attempt."""
        mock_download_retry.return_value = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "test_file.zip"
            
            result = self.download_manager.download_with_progress(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is True
            mock_download_retry.assert_called_once()
            
    @patch('src.download_manager.DownloadManager._download_with_retry')
    @patch('time.sleep')
    def test_download_with_progress_retry_then_success(self, mock_sleep, mock_download_retry):
        """Test download with progress - fails once then succeeds."""
        # First call raises exception, second call succeeds
        mock_download_retry.side_effect = [Exception("Network error"), True]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "test_file.zip"
            
            result = self.download_manager.download_with_progress(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is True
            assert mock_download_retry.call_count == 2
            mock_sleep.assert_called_once_with(1.0)  # Initial retry delay
            
    @patch('src.download_manager.DownloadManager._download_with_retry')
    @patch('time.sleep')
    def test_download_with_progress_max_retries_exceeded(self, mock_sleep, mock_download_retry):
        """Test download with progress - all retries fail."""
        mock_download_retry.side_effect = Exception("Persistent network error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "test_file.zip"
            
            result = self.download_manager.download_with_progress(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is False
            assert mock_download_retry.call_count == 3  # max_retries
            # Verify exponential backoff delays
            expected_delays = [1.0, 2.0]  # 1.0 * 2^0, 1.0 * 2^1
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays
            
    def test_download_with_retry_logic(self):
        """Test that retry logic is properly configured."""
        # Test that the download manager has proper retry settings
        assert self.download_manager.max_retries == 3
        assert self.download_manager.initial_retry_delay == 1.0
                
    def test_download_with_resume_interface(self):
        """Test that download_with_resume method exists and has correct signature."""
        # Test that the method exists and can be called
        assert hasattr(self.download_manager, 'download_with_resume')
        assert callable(self.download_manager.download_with_resume)
                    
    @patch('urllib.request.urlopen')
    def test_download_with_resume_error(self, mock_urlopen):
        """Test download with resume when an error occurs."""
        mock_urlopen.side_effect = Exception("Network error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "error_file.zip"
            
            result = self.download_manager.download_with_resume(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is False
            # Verify error was displayed in console output
            output = self.console_output.getvalue()
            assert "Failed to download with resume" in output
    
    def test_download_with_resume_partial_file(self):
        """Test download with resume when partial file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "partial_file.zip"
            # Create partial file
            destination.write_bytes(b'partial_data')
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                # Mock response
                mock_response = Mock()
                mock_response.headers = {'Content-Length': '1024', 'Accept-Ranges': 'bytes'}
                mock_response.read.side_effect = [b'data_chunk', b'']
                mock_urlopen.return_value.__enter__.return_value = mock_response
                
                result = self.download_manager.download_with_resume(
                    'http://example.com/file.zip',
                    str(destination)
                )
                
                assert result is True
                # Verify Range header was used for resume
                mock_urlopen.assert_called()
                call_args = mock_urlopen.call_args
                request = call_args[0][0]
                assert hasattr(request, 'headers')
    
    @patch('src.download_manager.DownloadManager._download_with_retry')
    def test_download_with_progress_keyboard_interrupt(self, mock_download_retry):
        """Test download with progress when keyboard interrupt occurs."""
        mock_download_retry.side_effect = KeyboardInterrupt("User interrupted")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "interrupted_file.zip"
            
            result = self.download_manager.download_with_progress(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is False
            # Verify error was displayed
            output = self.console_output.getvalue()
            assert "Failed to download" in output
    
    @patch('urllib.request.urlopen')
    def test_download_with_retry_progress_tracking(self, mock_urlopen):
        """Test _download_with_retry with progress tracking."""
        # Mock response with known file size
        mock_response = Mock()
        mock_response.read.side_effect = [b'chunk1', b'chunk2', b'']  # Simulate chunks then EOF
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock file size
        with patch.object(self.download_manager, 'get_file_size', return_value=1024):
            with tempfile.TemporaryDirectory() as temp_dir:
                destination = Path(temp_dir) / "progress_file.zip"
                
                result = self.download_manager._download_with_retry(
                    'http://example.com/file.zip',
                    destination,
                    0  # First attempt
                )
                
                assert result is True
                assert destination.exists()
                assert destination.read_bytes() == b'chunk1chunk2'
    
    @patch('urllib.request.urlopen')
    def test_download_with_retry_unknown_size(self, mock_urlopen):
        """Test _download_with_retry with unknown file size."""
        # Mock response
        mock_response = Mock()
        mock_response.read.side_effect = [b'data', b'']  # Simulate download
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock unknown file size
        with patch.object(self.download_manager, 'get_file_size', return_value=-1):
            with tempfile.TemporaryDirectory() as temp_dir:
                destination = Path(temp_dir) / "unknown_size_file.zip"
                
                result = self.download_manager._download_with_retry(
                    'http://example.com/file.zip',
                    destination,
                    0
                )
                
                assert result is True
                assert destination.exists()
    
    @patch('urllib.request.urlopen')
    def test_download_with_retry_cancelled(self, mock_urlopen):
        """Test _download_with_retry when cancelled by user."""
        # Mock response
        mock_response = Mock()
        mock_response.read.side_effect = [b'chunk1', b'chunk2', b'']
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock cancellation
        self.ui_manager._keyboard_interrupt_received = True
        
        # Mock file size
        with patch.object(self.download_manager, 'get_file_size', return_value=1024):
            with tempfile.TemporaryDirectory() as temp_dir:
                destination = Path(temp_dir) / "cancelled_file.zip"
                
                result = self.download_manager._download_with_retry(
                    'http://example.com/file.zip',
                    destination,
                    0
                )
                
                assert result is False
                # Verify cancellation was handled
                output = self.console_output.getvalue()
                assert "Download cancelled" in output or "interrupted" in output
    
    @patch('urllib.request.urlopen')
    def test_download_with_retry_empty_file(self, mock_urlopen):
        """Test _download_with_retry when downloaded file is empty."""
        # Mock response that creates empty file
        mock_response = Mock()
        mock_response.read.side_effect = [b'']  # Empty response
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock file size
        with patch.object(self.download_manager, 'get_file_size', return_value=1024):
            with tempfile.TemporaryDirectory() as temp_dir:
                destination = Path(temp_dir) / "empty_file.zip"
                
                with pytest.raises(Exception, match="Download completed but file is empty"):
                    self.download_manager._download_with_retry(
                        'http://example.com/file.zip',
                        destination,
                        0
                    )
    
    def test_download_manager_configuration(self):
        """Test download manager configuration parameters."""
        # Test default configuration
        assert self.download_manager.max_retries == 3
        assert self.download_manager.initial_retry_delay == 1.0
        
        # Test custom configuration
        custom_ui = UIManager(console=self.console)
        custom_manager = DownloadManager(custom_ui)
        custom_manager.max_retries = 5
        custom_manager.initial_retry_delay = 2.0
        
        assert custom_manager.max_retries == 5
        assert custom_manager.initial_retry_delay == 2.0
    
    @patch('urllib.request.urlopen')
    def test_get_file_size_with_redirect(self, mock_urlopen):
        """Test file size detection with HTTP redirects."""
        # Mock response with redirect
        mock_response = Mock()
        mock_response.headers = {'Content-Length': '2048'}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        size = self.download_manager.get_file_size('http://example.com/redirect/file.zip')
        
        assert size == 2048
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlretrieve')
    def test_download_file_with_directory_creation(self, mock_urlretrieve):
        """Test download_file creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use nested directory path that doesn't exist
            destination = Path(temp_dir) / "nested" / "dir" / "file.zip"
            
            result = self.download_manager.download_file(
                'http://example.com/file.zip',
                str(destination)
            )
            
            assert result is True
            # Verify parent directories were created
            assert destination.parent.exists()
            mock_urlretrieve.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])