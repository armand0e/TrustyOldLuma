"""
Edge case and boundary condition tests for Gaming Setup Tool.

This module tests unusual scenarios, error conditions, and edge cases
that might not be covered in regular unit or integration tests.
"""

import pytest
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from models import SetupConfig, SetupResults, ShortcutConfig
from exceptions import (
    GamingSetupError,
    AdminPrivilegeError,
    FileOperationError,
    NetworkError,
    ConfigurationError,
    SecurityConfigError
)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_setup_config_edge_cases(self):
        """Test SetupConfig with edge case inputs."""
        # Test with very long paths
        long_path = Path("/" + "a" * 200 + "/very/long/path")
        
        with pytest.raises(ValueError):
            SetupConfig(
                greenluma_path=long_path,
                koalageddon_path=Path("/test").resolve(),
                koalageddon_config_path=Path("/test/config").resolve(),
                download_url="https://example.com/test.exe",
                app_id="480"
            )
        
        # Test with special characters in app ID
        with pytest.raises(ValueError):
            SetupConfig(
                greenluma_path=Path("/test").resolve(),
                koalageddon_path=Path("/test").resolve(),
                koalageddon_config_path=Path("/test/config").resolve(),
                download_url="https://example.com/test.exe",
                app_id="480-special"
            )
        
        # Test with very large app ID
        with pytest.raises(ValueError):
            SetupConfig(
                greenluma_path=Path("/test").resolve(),
                koalageddon_path=Path("/test").resolve(),
                koalageddon_config_path=Path("/test/config").resolve(),
                download_url="https://example.com/test.exe",
                app_id="9" * 20  # Very long numeric string
            )
    
    def test_setup_results_edge_cases(self):
        """Test SetupResults with edge case data."""
        results = SetupResults()
        
        # Test with very large number of operations
        for i in range(10000):
            results.directories_created.append(Path(f"/test/dir_{i}"))
            results.exclusions_added.append((Path(f"/test/path_{i}"), i % 2 == 0))
        
        # Should handle large datasets
        assert len(results.directories_created) == 10000
        assert len(results.exclusions_added) == 10000
        
        # Success rate calculation should work with large datasets
        success_rate = results.success_rate
        assert 0.0 <= success_rate <= 1.0
        
        # Test with extreme time values
        results.start_time = 0.0
        results.end_time = float('inf')
        
        # Should handle infinite duration gracefully
        duration = results.duration
        assert duration == float('inf')
    
    def test_shortcut_config_edge_cases(self):
        """Test ShortcutConfig with edge case inputs."""
        # Test with very long shortcut name
        long_name = "A" * 300
        
        with pytest.raises(ValueError):
            ShortcutConfig(
                name=long_name,
                target_path=Path("/test/target").resolve(),
                working_directory=Path("/test").resolve()
            )
        
        # Test with Unicode characters in name
        unicode_name = "Test 🎮 Shortcut ⚙️"
        config = ShortcutConfig(
            name=unicode_name,
            target_path=Path("/test/target").resolve(),
            working_directory=Path("/test").resolve()
        )
        assert config.name == unicode_name
        
        # Test with empty arguments
        config = ShortcutConfig(
            name="Test",
            target_path=Path("/test/target").resolve(),
            working_directory=Path("/test").resolve(),
            arguments=""
        )
        assert config.arguments == ""
    
    @pytest.mark.asyncio
    async def test_file_operations_edge_cases(self):
        """Test file operations with edge cases."""
        from file_operations_manager import FileOperationsManager
        
        console = Console(file=open(os.devnull, 'w'))
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test creating directories with very deep nesting
            deep_path = temp_path
            for i in range(50):  # Very deep nesting
                deep_path = deep_path / f"level_{i}"
            
            await file_manager.create_directories([deep_path], results)
            
            # Should handle deep nesting (up to OS limits)
            if len(str(deep_path)) < 260:  # Windows path limit
                assert deep_path.exists()
            
            # Test with paths containing special characters
            special_chars_path = temp_path / "test with spaces & symbols!@#"
            await file_manager.create_directories([special_chars_path], results)
            
            # Should handle special characters
            assert special_chars_path.exists()
    
    def test_console_edge_cases(self):
        """Test Rich console with edge cases."""
        from io import StringIO
        
        # Test with very wide console
        wide_console = Console(file=StringIO(), width=1000)
        wide_console.print("Test message")
        
        # Test with very narrow console
        narrow_console = Console(file=StringIO(), width=10)
        narrow_console.print("This is a very long message that should wrap")
        
        # Test with zero width (should not crash)
        try:
            zero_console = Console(file=StringIO(), width=0)
            zero_console.print("Test")
        except ValueError:
            pass  # Expected for invalid width
    
    @pytest.mark.asyncio
    async def test_network_edge_cases(self):
        """Test network operations with edge cases."""
        from file_operations_manager import FileOperationsManager
        
        console = Console(file=open(os.devnull, 'w'))
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test with invalid URLs
            invalid_urls = [
                "not-a-url",
                "ftp://example.com/file.exe",  # Wrong protocol
                "https://",  # Incomplete URL
                "https://example.com/" + "a" * 2000,  # Very long URL
            ]
            
            for url in invalid_urls:
                result = await file_manager.download_file(
                    url, temp_path, results=results
                )
                # Should fail gracefully
                assert result is False
    
    def test_error_handling_edge_cases(self):
        """Test error handling with edge cases."""
        from error_manager import ErrorManager, create_user_friendly_message
        
        console = Console(file=open(os.devnull, 'w'))
        error_manager = ErrorManager(console)
        
        # Test with very long error messages
        long_message = "Error: " + "A" * 10000
        long_error = ValueError(long_message)
        
        # Should handle long messages gracefully
        friendly_message = create_user_friendly_message(long_error, "test context")
        assert len(friendly_message) > 0
        
        # Test with None error message
        none_error = ValueError(None)
        friendly_message = create_user_friendly_message(none_error, "test context")
        assert len(friendly_message) > 0
        
        # Test with nested exceptions
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError as nested_error:
            friendly_message = create_user_friendly_message(nested_error, "test context")
            assert len(friendly_message) > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_edge_cases(self):
        """Test cleanup operations with edge cases."""
        from cleanup_manager import CleanupManager
        
        console = Console(file=open(os.devnull, 'w'))
        cleanup_manager = CleanupManager(console)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test cleanup of non-existent files
            nonexistent_files = [
                temp_path / "nonexistent1.txt",
                temp_path / "nonexistent2.txt"
            ]
            
            for file_path in nonexistent_files:
                cleanup_manager.register_temp_file(file_path, "test")
            
            # Should handle non-existent files gracefully
            results = await cleanup_manager.cleanup_temp_files()
            assert results.operations_attempted == 2
            # Success count may vary based on implementation
            
            # Test cleanup of files with permission issues
            if os.name == 'nt':
                # Windows-specific permission test
                restricted_file = temp_path / "restricted.txt"
                restricted_file.write_text("test")
                
                # Try to make file read-only
                try:
                    restricted_file.chmod(0o444)
                    cleanup_manager.register_temp_file(restricted_file, "test")
                    
                    results = await cleanup_manager.cleanup_temp_files()
                    # Should attempt cleanup even if it fails
                    assert results.operations_attempted >= 1
                except OSError:
                    pass  # Permission operations might not work in all environments
    
    def test_platform_detection_edge_cases(self):
        """Test platform detection with edge cases."""
        from admin_manager import AdminPrivilegeManager
        
        # Test with mocked unusual platform
        with patch('os.name', 'unknown_os'):
            with patch('platform.system', return_value='UnknownOS'):
                manager = AdminPrivilegeManager()
                
                # Should handle unknown platforms gracefully
                assert manager.platform_name == 'UnknownOS'
                assert manager.is_windows is False
    
    @pytest.mark.asyncio
    async def test_concurrent_access_edge_cases(self):
        """Test concurrent access scenarios."""
        from file_operations_manager import FileOperationsManager
        
        console = Console(file=open(os.devnull, 'w'))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test multiple managers accessing same files concurrently
            managers = [FileOperationsManager(console) for _ in range(5)]
            results_list = [SetupResults() for _ in range(5)]
            
            # All managers try to create the same directory
            same_dir = temp_path / "shared_directory"
            
            tasks = []
            for manager, results in zip(managers, results_list):
                task = manager.create_directories([same_dir], results)
                tasks.append(task)
            
            # Should handle concurrent access gracefully
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Directory should exist
            assert same_dir.exists()
    
    def test_memory_pressure_edge_cases(self):
        """Test behavior under memory pressure."""
        import gc
        
        # Create many large objects to simulate memory pressure
        large_objects = []
        try:
            for i in range(100):
                # Create large string objects
                large_obj = "A" * 1000000  # 1MB string
                large_objects.append(large_obj)
                
                # Test creating managers under memory pressure
                console = Console(file=open(os.devnull, 'w'))
                from file_operations_manager import FileOperationsManager
                manager = FileOperationsManager(console)
                
                # Should still work under memory pressure
                assert manager is not None
                
                # Clean up periodically
                if i % 10 == 0:
                    gc.collect()
        
        except MemoryError:
            # Expected in extreme cases
            pass
        finally:
            # Clean up
            large_objects.clear()
            gc.collect()
    
    def test_unicode_handling_edge_cases(self):
        """Test Unicode handling in various components."""
        # Test with various Unicode characters
        unicode_strings = [
            "Test 🎮 Gaming",
            "Тест на русском",
            "测试中文",
            "🎯🎮⚙️🔧",
            "Test\u0000Null",  # Null character
            "Test\u200BZero\u200CWidth",  # Zero-width characters
        ]
        
        for unicode_str in unicode_strings:
            try:
                # Test in SetupResults
                results = SetupResults()
                results.add_error(unicode_str)
                results.add_warning(unicode_str)
                
                assert unicode_str in results.errors
                assert unicode_str in results.warnings
                
                # Test in console output
                from io import StringIO
                console = Console(file=StringIO())
                console.print(unicode_str)
                
                output = console.file.getvalue()
                # Should handle Unicode gracefully (might be escaped)
                assert len(output) > 0
                
            except UnicodeError:
                # Some Unicode combinations might not be supported
                pass
    
    @pytest.mark.asyncio
    async def test_timeout_edge_cases(self):
        """Test timeout handling in async operations."""
        from file_operations_manager import FileOperationsManager
        
        console = Console(file=open(os.devnull, 'w'))
        file_manager = FileOperationsManager(console)
        
        # Test with very short timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                asyncio.sleep(1.0),  # Sleep longer than timeout
                timeout=0.1  # Very short timeout
            )
    
    def test_resource_exhaustion_edge_cases(self):
        """Test behavior when system resources are exhausted."""
        # Test with many file handles
        file_handles = []
        try:
            # Try to open many files (up to system limit)
            for i in range(1000):
                try:
                    handle = open(os.devnull, 'r')
                    file_handles.append(handle)
                except OSError:
                    # Hit system limit
                    break
            
            # Test that managers still work with limited resources
            console = Console(file=open(os.devnull, 'w'))
            from file_operations_manager import FileOperationsManager
            manager = FileOperationsManager(console)
            
            # Should still be able to create manager
            assert manager is not None
            
        finally:
            # Clean up file handles
            for handle in file_handles:
                try:
                    handle.close()
                except OSError:
                    pass


class TestBoundaryConditions:
    """Test boundary conditions and limits."""
    
    def test_path_length_boundaries(self):
        """Test path length boundary conditions."""
        # Test maximum path length (varies by OS)
        max_length = 260 if os.name == 'nt' else 4096
        
        # Test path just under the limit
        base_path = "C:\\" if os.name == 'nt' else "/"
        remaining_length = max_length - len(base_path) - 10  # Leave some margin
        
        if remaining_length > 0:
            long_path_str = base_path + "a" * remaining_length
            long_path = Path(long_path_str)
            
            # Should handle long paths up to system limits
            try:
                config = SetupConfig(
                    greenluma_path=long_path.resolve(),
                    koalageddon_path=Path("/test").resolve(),
                    koalageddon_config_path=Path("/test/config").resolve(),
                    download_url="https://example.com/test.exe",
                    app_id="480"
                )
                assert config.greenluma_path == long_path.resolve()
            except (OSError, ValueError):
                # Expected for paths that exceed system limits
                pass
    
    def test_numeric_boundaries(self):
        """Test numeric boundary conditions."""
        results = SetupResults()
        
        # Test with maximum integer values
        import sys
        max_int = sys.maxsize
        
        results.start_time = float(max_int)
        results.end_time = float(max_int + 1)
        
        # Should handle large numbers
        assert results.duration == 1.0
        
        # Test with very small numbers
        results.start_time = 1e-10
        results.end_time = 2e-10
        
        assert results.duration == 1e-10
    
    def test_collection_size_boundaries(self):
        """Test collection size boundary conditions."""
        results = SetupResults()
        
        # Test with empty collections
        assert results.success_rate == 1.0  # No operations = 100% success
        
        # Test with single item collections
        results.directories_created.append(Path("/test"))
        assert results.success_rate == 1.0
        
        results.exclusions_added.append((Path("/test"), False))
        assert results.success_rate < 1.0  # Now has one failure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])