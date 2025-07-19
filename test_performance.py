"""
Performance tests for Gaming Setup Tool.

This module contains tests to measure and verify performance
characteristics of the gaming setup tool components.
"""

import pytest
import asyncio
import time
import tempfile
import shutil
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch
from rich.console import Console

from gaming_setup_tool import GamingSetupTool
from file_operations_manager import FileOperationsManager
from models import SetupConfig, SetupResults


class TestPerformance:
    """Performance tests for various components."""
    
    @pytest.fixture
    def performance_workspace(self):
        """Create a performance testing workspace."""
        temp_dir = Path(tempfile.mkdtemp())
        workspace = {
            'root': temp_dir,
            'greenluma': temp_dir / "GreenLuma",
            'koalageddon': temp_dir / "Koalageddon",
            'temp': temp_dir / "temp",
            'assets': temp_dir / "assets"
        }
        
        for path in workspace.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        
        yield workspace
        
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def large_zip_file(self, performance_workspace):
        """Create a large zip file for performance testing."""
        zip_path = performance_workspace['assets'] / "large_test.zip"
        
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_ref:
            # Add multiple files to simulate a realistic archive
            for i in range(100):
                file_content = f"File {i} content " * 100  # ~1.5KB per file
                zip_ref.writestr(f"folder{i//10}/file_{i}.txt", file_content)
            
            # Add some binary-like content
            for i in range(10):
                binary_content = bytes(range(256)) * 100  # ~25KB per file
                zip_ref.writestr(f"binaries/file_{i}.bin", binary_content)
        
        return zip_path
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_file_extraction_performance(self, performance_workspace, large_zip_file, performance_timer):
        """Test file extraction performance with large archives."""
        console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        # Measure extraction time
        performance_timer.start()
        
        success = await file_manager.extract_archive(
            large_zip_file,
            performance_workspace['temp'],
            flatten=False,
            results=results
        )
        
        performance_timer.stop()
        
        # Verify success
        assert success is True
        assert results.files_extracted is True
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time is not None
        assert elapsed_time < 30.0  # Should complete within 30 seconds
        
        print(f"\n📊 File extraction performance:")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Files extracted: ~110 files")
        print(f"   Rate: {110/elapsed_time:.1f} files/second")
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_directory_creation_performance(self, performance_workspace, performance_timer):
        """Test directory creation performance with many directories."""
        console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        # Create many directories
        test_dirs = []
        for i in range(1000):
            test_dirs.append(performance_workspace['temp'] / f"dir_{i:04d}")
        
        # Measure creation time
        performance_timer.start()
        
        await file_manager.create_directories(test_dirs, results)
        
        performance_timer.stop()
        
        # Verify success
        assert len(results.directories_created) == 1000
        assert len(results.errors) == 0
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time is not None
        assert elapsed_time < 10.0  # Should complete within 10 seconds
        
        print(f"\n📊 Directory creation performance:")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Directories: 1000")
        print(f"   Rate: {1000/elapsed_time:.1f} dirs/second")
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_complete_workflow_performance(self, performance_workspace, performance_timer):
        """Test complete workflow performance."""
        tool = GamingSetupTool(verbose=False)
        
        # Mock configuration
        tool.config = SetupConfig(
            greenluma_path=performance_workspace['greenluma'],
            koalageddon_path=performance_workspace['koalageddon'],
            koalageddon_config_path=performance_workspace['koalageddon'] / "config",
            download_url="https://example.com/test.exe",
            app_id="480",
            temp_dir=performance_workspace['temp']
        )
        
        # Mock all operations to focus on workflow performance
        with patch.object(tool.admin_manager, 'ensure_admin_privileges'), \
             patch.object(tool.security_manager, 'add_defender_exclusions', return_value=asyncio.coroutine(lambda: None)()), \
             patch.object(tool.file_manager, 'extract_archive', return_value=True), \
             patch.object(tool.security_manager, 'verify_antivirus_protection', return_value=True), \
             patch.object(tool.config_handler, 'update_dll_injector_config', return_value=True), \
             patch.object(tool.file_manager, 'download_file', return_value=True), \
             patch.object(tool.config_handler, 'replace_koalageddon_config', return_value=True), \
             patch.object(tool.shortcut_manager, 'create_shortcuts', return_value=[True, True]), \
             patch.object(tool.applist_manager, 'setup_applist', return_value=True), \
             patch.object(tool.cleanup_manager, 'cleanup_temp_files', return_value=asyncio.coroutine(lambda: None)()):
            
            # Measure workflow time
            performance_timer.start()
            
            await tool.run()
            
            performance_timer.stop()
        
        # Verify completion
        assert tool.results is not None
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time is not None
        assert elapsed_time < 5.0  # Mocked workflow should be very fast
        
        print(f"\n📊 Complete workflow performance:")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Success rate: {tool.results.success_rate:.1%}")
    
    @pytest.mark.slow
    def test_console_output_performance(self, performance_timer):
        """Test Rich console output performance."""
        from io import StringIO
        
        output_buffer = StringIO()
        console = Console(file=output_buffer, width=80)
        
        # Test large amount of console output
        performance_timer.start()
        
        for i in range(1000):
            console.print(f"Test message {i} with some content")
            if i % 100 == 0:
                console.rule(f"Section {i//100}")
        
        performance_timer.stop()
        
        # Verify output was generated
        output = output_buffer.getvalue()
        assert len(output) > 0
        assert "Test message 999" in output
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time is not None
        assert elapsed_time < 2.0  # Should be very fast
        
        print(f"\n📊 Console output performance:")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Messages: 1000")
        print(f"   Rate: {1000/elapsed_time:.1f} messages/second")
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, performance_workspace, performance_timer):
        """Test performance of concurrent operations."""
        console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
        file_manager = FileOperationsManager(console)
        
        # Create multiple concurrent directory creation tasks
        async def create_batch_dirs(batch_id, count):
            results = SetupResults()
            dirs = [performance_workspace['temp'] / f"batch_{batch_id}" / f"dir_{i}" 
                   for i in range(count)]
            await file_manager.create_directories(dirs, results)
            return len(results.directories_created)
        
        # Measure concurrent execution time
        performance_timer.start()
        
        # Run 10 concurrent batches of 50 directories each
        tasks = [create_batch_dirs(i, 50) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        performance_timer.stop()
        
        # Verify all directories were created
        total_created = sum(results)
        assert total_created == 500
        
        # Performance assertions
        elapsed_time = performance_timer.elapsed
        assert elapsed_time is not None
        assert elapsed_time < 15.0  # Should complete within 15 seconds
        
        print(f"\n📊 Concurrent operations performance:")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Directories: 500 (10 batches of 50)")
        print(f"   Rate: {500/elapsed_time:.1f} dirs/second")
    
    @pytest.mark.slow
    def test_memory_usage_stability(self, performance_workspace):
        """Test memory usage stability during operations."""
        import gc
        import sys
        
        # Get initial memory usage (approximate)
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
        
        # Perform many operations that could cause memory leaks
        for i in range(100):
            # Create and destroy managers
            from file_operations_manager import FileOperationsManager
            from security_config_manager import SecurityConfigManager
            from configuration_handler import ConfigurationHandler
            
            file_mgr = FileOperationsManager(console)
            security_mgr = SecurityConfigManager(console)
            config_handler = ConfigurationHandler(console)
            
            # Create some results objects
            results = SetupResults()
            results.add_error(f"Test error {i}")
            results.add_warning(f"Test warning {i}")
            
            # Clean up references
            del file_mgr, security_mgr, config_handler, results
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not grow significantly
        object_growth = final_objects - initial_objects
        growth_ratio = object_growth / initial_objects if initial_objects > 0 else 0
        
        print(f"\n📊 Memory usage stability:")
        print(f"   Initial objects: {initial_objects}")
        print(f"   Final objects: {final_objects}")
        print(f"   Growth: {object_growth} objects ({growth_ratio:.1%})")
        
        # Allow some growth but not excessive
        assert growth_ratio < 0.5  # Less than 50% growth
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, performance_workspace, performance_timer):
        """Test performance impact of error handling."""
        console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
        file_manager = FileOperationsManager(console)
        results = SetupResults()
        
        # Test extraction of many non-existent files (should fail fast)
        nonexistent_files = [
            performance_workspace['temp'] / f"nonexistent_{i}.zip" 
            for i in range(100)
        ]
        
        performance_timer.start()
        
        for zip_file in nonexistent_files:
            await file_manager.extract_archive(
                zip_file,
                performance_workspace['temp'],
                results=results
            )
        
        performance_timer.stop()
        
        # Verify all operations failed as expected
        assert len(results.errors) == 100
        
        # Performance assertions - error handling should be fast
        elapsed_time = performance_timer.elapsed
        assert elapsed_time is not None
        assert elapsed_time < 5.0  # Should fail fast
        
        print(f"\n📊 Error handling performance:")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Failed operations: 100")
        print(f"   Rate: {100/elapsed_time:.1f} failures/second")


class TestScalability:
    """Test scalability with varying workloads."""
    
    @pytest.mark.slow
    @pytest.mark.parametrize("file_count", [10, 50, 100, 500])
    @pytest.mark.asyncio
    async def test_extraction_scalability(self, file_count, performance_timer):
        """Test extraction performance with different file counts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create zip file with specified number of files
            zip_path = temp_path / "scalability_test.zip"
            with zipfile.ZipFile(zip_path, 'w') as zip_ref:
                for i in range(file_count):
                    content = f"File {i} content " * 10
                    zip_ref.writestr(f"file_{i:04d}.txt", content)
            
            # Test extraction
            console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
            file_manager = FileOperationsManager(console)
            results = SetupResults()
            
            performance_timer.start()
            
            success = await file_manager.extract_archive(
                zip_path,
                temp_path / "extracted",
                results=results
            )
            
            performance_timer.stop()
            
            assert success is True
            elapsed_time = performance_timer.elapsed
            
            print(f"\n📊 Scalability test ({file_count} files):")
            print(f"   Time: {elapsed_time:.2f} seconds")
            print(f"   Rate: {file_count/elapsed_time:.1f} files/second")
            
            # Performance should scale reasonably
            if file_count <= 100:
                assert elapsed_time < 10.0
            else:
                assert elapsed_time < 30.0
    
    @pytest.mark.slow
    @pytest.mark.parametrize("dir_count", [10, 100, 500, 1000])
    @pytest.mark.asyncio
    async def test_directory_creation_scalability(self, dir_count, performance_timer):
        """Test directory creation performance with different counts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            console = Console(file=open('nul' if os.name == 'nt' else '/dev/null', 'w'))
            file_manager = FileOperationsManager(console)
            results = SetupResults()
            
            # Create directory list
            dirs = [temp_path / f"dir_{i:04d}" for i in range(dir_count)]
            
            performance_timer.start()
            
            await file_manager.create_directories(dirs, results)
            
            performance_timer.stop()
            
            assert len(results.directories_created) == dir_count
            elapsed_time = performance_timer.elapsed
            
            print(f"\n📊 Directory scalability test ({dir_count} dirs):")
            print(f"   Time: {elapsed_time:.2f} seconds")
            print(f"   Rate: {dir_count/elapsed_time:.1f} dirs/second")
            
            # Performance should scale reasonably
            if dir_count <= 100:
                assert elapsed_time < 5.0
            else:
                assert elapsed_time < 15.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])