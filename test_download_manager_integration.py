"""Integration tests for Download Manager module."""

import tempfile
from pathlib import Path
from unittest.mock import patch
from rich.console import Console
from io import StringIO

from src.download_manager import DownloadManager
from src.ui_manager import UIManager


def test_download_manager_integration():
    """Test download manager integration with UI and file system."""
    # Create real console and UI manager
    console_output = StringIO()
    console = Console(file=console_output, width=80)
    ui_manager = UIManager(console=console)
    download_manager = DownloadManager(ui_manager)
    
    # Test initialization
    assert download_manager.ui is ui_manager
    assert download_manager.max_retries == 3
    assert download_manager.initial_retry_delay == 1.0
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        destination = Path(temp_dir) / "test_download.txt"
        
        # Test basic download with mocked urlretrieve
        with patch('urllib.request.urlretrieve') as mock_retrieve:
            result = download_manager.download_file(
                'http://example.com/test.txt',
                str(destination)
            )
            
            assert result is True
            assert mock_retrieve.called
            mock_retrieve.assert_called_once_with(
                'http://example.com/test.txt',
                str(destination)
            )
        
        # Test file size detection
        def mock_urlopen_with_size(url):
            class MockResponse:
                def __enter__(self):
                    return self
                    
                def __exit__(self, *args):
                    pass
                    
                @property
                def headers(self):
                    return {'Content-Length': '1024'}
            
            return MockResponse()
        
        with patch('urllib.request.urlopen', side_effect=mock_urlopen_with_size):
            size = download_manager.get_file_size('http://example.com/test.txt')
            assert size == 1024
        
        # Test error handling
        with patch('urllib.request.urlretrieve', side_effect=Exception("Network error")):
            result = download_manager.download_file(
                'http://example.com/error.txt',
                str(destination)
            )
            
            assert result is False
            # Verify error was displayed in console
            output = console_output.getvalue()
            assert "Failed to download file" in output
        
        print("All integration tests passed!")


if __name__ == '__main__':
    test_download_manager_integration()
    print("Integration test completed successfully!")