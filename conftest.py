"""
Pytest configuration and fixtures for Gaming Setup Tool tests.

This module provides shared fixtures and configuration for all test modules.
"""

import os
import sys
import pytest
import tempfile
import shutil
import asyncio
import zipfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock
from io import StringIO
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.text import Text

from models import SetupConfig, SetupResults, ShortcutConfig
from display_managers import (
    ProgressDisplayManager,
    ErrorDisplayManager,
    WelcomeScreenManager,
    CompletionScreenManager
)


# ============================================================================
# Session-scoped fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Console and Rich fixtures
# ============================================================================

@pytest.fixture
def mock_console():
    """Create a mock Rich console for testing."""
    console = Mock(spec=Console)
    console.file = StringIO()
    console.width = 80
    console.height = 24
    console.size = (80, 24)
    console.is_jupyter = False
    console.is_terminal = True
    console.options = Mock()
    console.get_time = Mock(return_value=0.0)
    console.set_live = Mock()
    console.show_cursor = Mock()
    console.push_render_hook = Mock()
    console.clear_live = Mock()
    console.input = Mock(return_value="")
    console.print = Mock()
    console.rule = Mock()
    console.status = Mock()
    console.__enter__ = Mock(return_value=console)
    console.__exit__ = Mock(return_value=None)
    return console


@pytest.fixture
def real_console():
    """Create a real Rich console for integration testing."""
    # Use StringIO to capture output without displaying it
    return Console(file=StringIO(), width=80, force_terminal=False)


@pytest.fixture
def console_output_capture():
    """Fixture to capture Rich console output for testing."""
    output_buffer = StringIO()
    console = Console(file=output_buffer, width=80, force_terminal=False)
    
    def get_output():
        return output_buffer.getvalue()
    
    def clear_output():
        output_buffer.seek(0)
        output_buffer.truncate(0)
    
    console.get_captured_output = get_output
    console.clear_captured_output = clear_output
    
    return console


@pytest.fixture
def rich_snapshot_console():
    """Console fixture for Rich output snapshot testing."""
    output_buffer = StringIO()
    console = Console(
        file=output_buffer,
        width=80,
        height=24,
        force_terminal=True,
        color_system="standard"
    )
    
    def get_snapshot():
        """Get the current console output as a snapshot."""
        return output_buffer.getvalue()
    
    def reset_snapshot():
        """Reset the console output buffer."""
        output_buffer.seek(0)
        output_buffer.truncate(0)
    
    console.get_snapshot = get_snapshot
    console.reset_snapshot = reset_snapshot
    
    return console


# ============================================================================
# File system fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_workspace(temp_dir):
    """Create a temporary workspace with common directory structure."""
    workspace = {
        'root': temp_dir,
        'documents': temp_dir / "Documents",
        'greenluma': temp_dir / "Documents" / "GreenLuma",
        'koalageddon': temp_dir / "Koalageddon",
        'temp': temp_dir / "temp",
        'desktop': temp_dir / "Desktop"
    }
    
    # Create directories
    for path in workspace.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
    
    return workspace


@pytest.fixture
def sample_zip_file(temp_dir):
    """Create a sample zip file for testing extraction."""
    zip_path = temp_dir / "sample.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zip_ref:
        # Add files with nested structure
        zip_ref.writestr("folder1/file1.txt", "Content of file 1")
        zip_ref.writestr("folder2/subfolder/file2.txt", "Content of file 2")
        zip_ref.writestr("root_file.txt", "Root file content")
        zip_ref.writestr("GreenLuma_2020_x64.dll", b"Mock DLL content")
        zip_ref.writestr("DLLInjector.ini", "[Settings]\nDLL=GreenLuma_2020_x64.dll\n")
    
    return zip_path


@pytest.fixture
def sample_config_files(temp_dir):
    """Create sample configuration files for testing."""
    configs = {}
    
    # DLLInjector.ini
    dll_config = temp_dir / "DLLInjector.ini"
    dll_config.write_text(
        "[Settings]\n"
        "DLL=C:\\OldPath\\GreenLuma_2020_x64.dll\n"
        "Timeout=30\n"
        "ProcessName=steam.exe\n"
    )
    configs['dll_injector'] = dll_config
    
    # Koalageddon config
    koa_config = temp_dir / "koalageddon.config"
    koa_config.write_text(
        '{\n'
        '  "EnableSteam": true,\n'
        '  "EnableEpic": true,\n'
        '  "EnableOrigin": false,\n'
        '  "LogLevel": "Info"\n'
        '}\n'
    )
    configs['koalageddon'] = koa_config
    
    return configs


# ============================================================================
# Model fixtures
# ============================================================================

@pytest.fixture
def setup_config(temp_workspace):
    """Create a test SetupConfig instance."""
    return SetupConfig(
        greenluma_path=temp_workspace['greenluma'],
        koalageddon_path=temp_workspace['koalageddon'],
        koalageddon_config_path=temp_workspace['koalageddon'] / "config",
        download_url="https://example.com/test.exe",
        app_id="480",
        verbose_logging=False,
        documents_path=temp_workspace['documents'],
        temp_dir=temp_workspace['temp']
    )


@pytest.fixture
def setup_results():
    """Create a test SetupResults instance."""
    return SetupResults()


@pytest.fixture
def sample_shortcut_configs(temp_workspace):
    """Create sample shortcut configurations."""
    return [
        ShortcutConfig(
            name="GreenLuma",
            target_path=temp_workspace['greenluma'] / "DLLInjector.exe",
            working_directory=temp_workspace['greenluma'],
            icon_path=temp_workspace['greenluma'] / "icon.ico",
            description="GreenLuma DLL Injector"
        ),
        ShortcutConfig(
            name="Koalageddon",
            target_path=temp_workspace['koalageddon'] / "Koalageddon.exe",
            working_directory=temp_workspace['koalageddon'],
            description="Koalageddon Game Unlocker"
        )
    ]


# ============================================================================
# Manager fixtures
# ============================================================================

@pytest.fixture
def progress_manager(mock_console):
    """Create a ProgressDisplayManager for testing."""
    manager = ProgressDisplayManager(mock_console)
    
    # Mock the progress context manager
    progress_context = Mock()
    progress_context.__enter__ = Mock(return_value=progress_context)
    progress_context.__exit__ = Mock(return_value=None)
    progress_context.update = Mock()
    progress_context.set_total = Mock()
    
    manager.create_progress_bar = Mock(return_value=progress_context)
    manager.show_spinner = Mock(return_value=progress_context)
    
    return manager


@pytest.fixture
def error_manager(mock_console):
    """Create an ErrorDisplayManager for testing."""
    manager = ErrorDisplayManager(mock_console)
    manager.display_error = Mock()
    manager.display_warning = Mock()
    manager.display_success = Mock()
    manager.display_retry_prompt = Mock(return_value=False)
    return manager


# ============================================================================
# Network mocking fixtures
# ============================================================================

@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session for testing downloads."""
    session = AsyncMock()
    response = AsyncMock()
    
    # Configure successful response
    response.status = 200
    response.headers = {'content-length': '1024'}
    
    # Mock content iteration
    async def mock_iter_chunked(chunk_size):
        yield b'test_chunk_1'
        yield b'test_chunk_2'
        yield b'test_chunk_3'
    
    response.content.iter_chunked = mock_iter_chunked
    
    # Configure session
    session.get.return_value.__aenter__.return_value = response
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    
    return session


@pytest.fixture
def mock_failed_download():
    """Create a mock for failed download scenarios."""
    session = AsyncMock()
    response = AsyncMock()
    
    # Configure failed response
    response.status = 404
    response.request_info = Mock()
    response.history = []
    
    session.get.return_value.__aenter__.return_value = response
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    
    return session


# ============================================================================
# Platform-specific fixtures
# ============================================================================

@pytest.fixture
def windows_environment():
    """Mock Windows environment for testing."""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('os.name', 'nt')
        m.setattr('platform.system', lambda: 'Windows')
        yield


@pytest.fixture
def unix_environment():
    """Mock Unix environment for testing."""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('os.name', 'posix')
        m.setattr('platform.system', lambda: 'Linux')
        yield


# ============================================================================
# Rich output testing utilities
# ============================================================================

class RichOutputMatcher:
    """Utility class for matching Rich console output."""
    
    def __init__(self, console_output: str):
        self.output = console_output
    
    def contains_text(self, text: str) -> bool:
        """Check if output contains specific text."""
        return text in self.output
    
    def contains_panel(self, title: str = None, content: str = None) -> bool:
        """Check if output contains a panel with specific title/content."""
        # This is a simplified check - in a real implementation,
        # you might want to parse the Rich markup more thoroughly
        if title and title not in self.output:
            return False
        if content and content not in self.output:
            return False
        return True
    
    def contains_progress_bar(self) -> bool:
        """Check if output contains progress bar elements."""
        progress_indicators = ['█', '▌', '▍', '▎', '▏', '░', '▒', '▓']
        return any(indicator in self.output for indicator in progress_indicators)
    
    def contains_error_styling(self) -> bool:
        """Check if output contains error styling."""
        error_indicators = ['❌', '✗', '[red]', 'ERROR', 'Error']
        return any(indicator in self.output for indicator in error_indicators)
    
    def contains_success_styling(self) -> bool:
        """Check if output contains success styling."""
        success_indicators = ['✅', '✓', '[green]', 'SUCCESS', 'Success']
        return any(indicator in self.output for indicator in success_indicators)


@pytest.fixture
def rich_output_matcher():
    """Factory fixture for creating RichOutputMatcher instances."""
    def _create_matcher(console_output: str) -> RichOutputMatcher:
        return RichOutputMatcher(console_output)
    return _create_matcher


# ============================================================================
# Snapshot testing utilities
# ============================================================================

@pytest.fixture
def snapshot_dir(request):
    """Create directory for storing test snapshots."""
    test_file = Path(request.fspath)
    snapshot_dir = test_file.parent / "__snapshots__" / test_file.stem
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    return snapshot_dir


def save_snapshot(snapshot_dir: Path, test_name: str, content: str):
    """Save a snapshot of console output."""
    snapshot_file = snapshot_dir / f"{test_name}.snapshot"
    snapshot_file.write_text(content, encoding='utf-8')


def load_snapshot(snapshot_dir: Path, test_name: str) -> Optional[str]:
    """Load a previously saved snapshot."""
    snapshot_file = snapshot_dir / f"{test_name}.snapshot"
    if snapshot_file.exists():
        return snapshot_file.read_text(encoding='utf-8')
    return None


@pytest.fixture
def snapshot_tester(snapshot_dir):
    """Fixture for snapshot testing of Rich output."""
    def _test_snapshot(test_name: str, actual_output: str, update_snapshots: bool = False):
        """Test actual output against saved snapshot."""
        if update_snapshots:
            save_snapshot(snapshot_dir, test_name, actual_output)
            return True
        
        expected_output = load_snapshot(snapshot_dir, test_name)
        if expected_output is None:
            # First time running test - save snapshot
            save_snapshot(snapshot_dir, test_name, actual_output)
            return True
        
        return actual_output == expected_output
    
    return _test_snapshot


# ============================================================================
# Async testing utilities
# ============================================================================

@pytest.fixture
def async_test_timeout():
    """Default timeout for async tests."""
    return 30.0


# ============================================================================
# Parametrized fixtures for cross-platform testing
# ============================================================================

@pytest.fixture(params=['windows', 'linux', 'macos'])
def platform_config(request):
    """Parametrized fixture for testing across different platforms."""
    platform_configs = {
        'windows': {
            'os_name': 'nt',
            'system': 'Windows',
            'shortcut_ext': '.lnk',
            'path_sep': '\\',
            'supports_admin': True,
            'supports_defender': True
        },
        'linux': {
            'os_name': 'posix',
            'system': 'Linux',
            'shortcut_ext': '.desktop',
            'path_sep': '/',
            'supports_admin': False,
            'supports_defender': False
        },
        'macos': {
            'os_name': 'posix',
            'system': 'Darwin',
            'shortcut_ext': '.app',
            'path_sep': '/',
            'supports_admin': False,
            'supports_defender': False
        }
    }
    
    return platform_configs[request.param]


# ============================================================================
# Error simulation fixtures
# ============================================================================

@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing."""
    return {
        'permission_denied': PermissionError("Access denied"),
        'file_not_found': FileNotFoundError("File not found"),
        'network_timeout': TimeoutError("Connection timed out"),
        'invalid_zip': zipfile.BadZipFile("Invalid zip file"),
        'disk_full': OSError("No space left on device"),
        'admin_required': PermissionError("Administrator privileges required")
    }


# ============================================================================
# Performance testing fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Fixture for measuring test performance."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()