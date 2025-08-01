"""Download Manager module for handling file downloads with Rich progress integration."""

import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple
from rich.progress import Progress, TaskID, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from .ui_manager import UIManager


class DownloadManager:
    """Manages file downloads with progress tracking and retry logic."""
    
    def __init__(self, ui_manager: UIManager):
        """Initialize DownloadManager with UI manager for progress display."""
        self.ui = ui_manager
        self.max_retries = 3
        self.initial_retry_delay = 1.0  # seconds
        
    def get_file_size(self, url: str) -> int:
        """Get file size from URL headers for accurate progress calculation."""
        try:
            with urllib.request.urlopen(url) as response:
                content_length = response.headers.get('Content-Length')
                if content_length:
                    return int(content_length)
                else:
                    # If Content-Length is not available, return -1 to indicate unknown size
                    return -1
        except (urllib.error.URLError, ValueError) as e:
            self.ui.display_warning(f"Could not determine file size for {url}: {e}")
            return -1
            
    def download_file(self, url: str, destination: str) -> bool:
        """Download file with basic functionality (no progress display)."""
        try:
            destination_path = Path(destination)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            urllib.request.urlretrieve(url, destination)
            return True
            
        except Exception as e:
            self.ui.display_error(
                f"Failed to download file from {url}",
                [f"Error: {str(e)}", "Check your internet connection", "Verify the URL is accessible"]
            )
            return False
            
    def download_with_progress(self, url: str, destination: str) -> bool:
        """Download file with Rich progress bar showing speed, ETA, and percentage."""
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try download with retries
        for attempt in range(self.max_retries):
            try:
                return self._download_with_retry(url, destination_path, attempt)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Last attempt failed
                    self.ui.display_error(
                        f"Failed to download after {self.max_retries} attempts",
                        [
                            f"Final error: {str(e)}",
                            "Check your internet connection",
                            "Verify the URL is accessible",
                            "Try running the setup again later"
                        ]
                    )
                    return False
                else:
                    # Wait before retry with exponential backoff
                    retry_delay = self.initial_retry_delay * (2 ** attempt)
                    self.ui.display_warning(
                        f"Download attempt {attempt + 1} failed, retrying in {retry_delay:.1f} seconds..."
                    )
                    time.sleep(retry_delay)
                    
        return False
        
    def _download_with_retry(self, url: str, destination_path: Path, attempt: int) -> bool:
        """Internal method to perform download with progress tracking."""
        # Get file size for progress calculation
        file_size = self.get_file_size(url)
        
        # Track download cancellation
        download_cancelled = False
        
        def cancel_download():
            nonlocal download_cancelled
            download_cancelled = True
            self.ui.display_warning("Download cancelled by user")
        
        # Create cancellable progress bar with download-specific columns
        progress = Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            TextColumn("[dim]Press Ctrl+C to cancel[/dim]"),
            console=self.ui.console
        )
        
        # Set up cancel handler
        original_handler = self.ui._interrupt_handler
        self.ui.set_interrupt_handler(cancel_download)
        
        try:
            with progress:
                # Add task with known or unknown total
                if file_size > 0:
                    task_id = progress.add_task(f"Downloading {destination_path.name}", total=file_size)
                else:
                    task_id = progress.add_task(f"Downloading {destination_path.name}", total=None)
                
                # Open URL and destination file
                with urllib.request.urlopen(url) as response:
                    with open(destination_path, 'wb') as dest_file:
                        downloaded = 0
                        chunk_size = 8192  # 8KB chunks
                        
                        while True:
                            # Check if download was cancelled
                            if download_cancelled or self.ui.was_interrupted():
                                self.ui.display_warning("Download cancelled, cleaning up...")
                                # Clean up partial download
                                try:
                                    if destination_path.exists():
                                        destination_path.unlink()
                                except Exception:
                                    pass  # Don't fail cleanup
                                return False
                            
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                                
                            dest_file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            if file_size > 0:
                                progress.update(task_id, completed=downloaded)
                            else:
                                # For unknown size, just show data transferred
                                progress.update(task_id, completed=downloaded, total=downloaded + 1)
        finally:
            # Restore original handler
            self.ui.set_interrupt_handler(original_handler)
        
        # Verify download completed successfully
        if destination_path.exists() and destination_path.stat().st_size > 0:
            self.ui.display_success(f"Successfully downloaded {destination_path.name}")
            return True
        else:
            raise Exception("Download completed but file is empty or missing")
            
    def download_with_resume(self, url: str, destination: str) -> bool:
        """Download file with resume capability for interrupted downloads."""
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if partial file exists
        resume_pos = 0
        if destination_path.exists():
            resume_pos = destination_path.stat().st_size
            self.ui.display_info(f"Resuming download from {resume_pos} bytes")
        
        try:
            # Create request with Range header for resume
            request = urllib.request.Request(url)
            if resume_pos > 0:
                request.add_header('Range', f'bytes={resume_pos}-')
            
            # Get total file size
            file_size = self.get_file_size(url)
            
            # Create progress bar
            progress = Progress(
                TextColumn("[bold blue]{task.description}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•", 
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
                console=self.ui.console
            )
            
            with progress:
                if file_size > 0:
                    task_id = progress.add_task(
                        f"Downloading {destination_path.name}", 
                        total=file_size,
                        completed=resume_pos
                    )
                else:
                    task_id = progress.add_task(
                        f"Downloading {destination_path.name}",
                        total=None,
                        completed=resume_pos
                    )
                
                # Open URL and destination file (append mode for resume)
                with urllib.request.urlopen(request) as response:
                    mode = 'ab' if resume_pos > 0 else 'wb'
                    with open(destination_path, mode) as dest_file:
                        downloaded = resume_pos
                        chunk_size = 8192
                        
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                                
                            dest_file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            if file_size > 0:
                                progress.update(task_id, completed=downloaded)
                            else:
                                progress.update(task_id, completed=downloaded, total=downloaded + 1)
            
            # Verify download
            if destination_path.exists() and destination_path.stat().st_size > 0:
                self.ui.display_success(f"Successfully downloaded {destination_path.name}")
                return True
            else:
                raise Exception("Download completed but file is empty or missing")
                
        except Exception as e:
            self.ui.display_error(
                f"Failed to download with resume from {url}",
                [
                    f"Error: {str(e)}",
                    "Check your internet connection",
                    "Verify the URL supports resume (Range requests)",
                    "Try downloading without resume"
                ]
            )
            return False