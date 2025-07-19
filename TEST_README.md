# Gaming Setup Tool - Test Suite Documentation

This document provides comprehensive information about the test suite for the Gaming Setup Tool.

## Overview

The test suite is designed to provide comprehensive coverage of all components with multiple testing approaches:

- **Unit Tests**: Test individual components in isolation with mocked dependencies
- **Integration Tests**: Test complete workflows with real file system operations
- **Rich Console Output Tests**: Verify Rich console output and styling with snapshot comparisons
- **Performance Tests**: Measure and verify performance characteristics
- **Edge Case Tests**: Test boundary conditions and unusual scenarios

## Test Structure

### Core Test Files

#### Unit Tests
- `test_admin_manager.py` - Admin privilege management tests
- `test_file_operations_manager.py` - File operations tests with mocked dependencies
- `test_security_config_manager.py` - Windows Defender and security configuration tests
- `test_configuration_handler.py` - Configuration file handling tests
- `test_shortcut_manager.py` - Desktop shortcut creation tests
- `test_applist_manager.py` - GreenLuma AppList management tests
- `test_cleanup_manager.py` - Cleanup and temporary file management tests
- `test_error_manager.py` - Error handling and categorization tests
- `test_display_managers.py` - Rich console display manager tests
- `test_models.py` - Data model validation and functionality tests

#### Integration Tests
- `test_gaming_setup_integration.py` - Complete workflow integration tests
- `test_complete_workflow_integration.py` - Real file operations integration tests
- `test_applist_integration.py` - AppList functionality integration tests
- `test_cleanup_integration.py` - Cleanup functionality integration tests
- `test_file_operations_integration.py` - File operations integration tests

#### Specialized Tests
- `test_rich_console_output.py` - Rich console output and styling tests
- `test_performance.py` - Performance and scalability tests
- `test_edge_cases.py` - Edge cases and boundary condition tests

### Test Configuration Files

- `pytest.ini` - Pytest configuration with markers, coverage, and options
- `conftest.py` - Shared fixtures and test utilities
- `run_tests.py` - Test runner script with various execution options
- `TEST_README.md` - This documentation file

## Test Fixtures

### Console Fixtures
- `mock_console` - Mock Rich console for unit testing
- `real_console` - Real Rich console for integration testing
- `console_output_capture` - Console with output capture for verification
- `rich_snapshot_console` - Console for Rich output snapshot testing

### File System Fixtures
- `temp_dir` - Temporary directory for file operations
- `temp_workspace` - Complete temporary workspace with directory structure
- `sample_zip_file` - Sample zip file for extraction testing
- `sample_config_files` - Sample configuration files for testing

### Model Fixtures
- `setup_config` - Test SetupConfig instance
- `setup_results` - Test SetupResults instance
- `sample_shortcut_configs` - Sample shortcut configurations

### Manager Fixtures
- `progress_manager` - Mocked ProgressDisplayManager
- `error_manager` - Mocked ErrorDisplayManager

### Network Fixtures
- `mock_aiohttp_session` - Mock aiohttp session for download testing
- `mock_failed_download` - Mock failed download scenarios

## Running Tests

### Using the Test Runner Script

```bash
# Install test dependencies
python run_tests.py --install-deps

# Run all tests
python run_tests.py --all

# Run unit tests with coverage
python run_tests.py --unit --coverage

# Run integration tests
python run_tests.py --integration -v

# Run Rich console output tests
python run_tests.py --rich-output

# Run performance tests
python run_tests.py --performance

# Run specific tests
python run_tests.py --specific "test_admin"

# Clean test artifacts
python run_tests.py --clean
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m rich_output
pytest -m slow

# Run specific test files
pytest test_admin_manager.py
pytest test_gaming_setup_integration.py

# Run tests matching pattern
pytest -k "test_admin"

# Run tests in parallel
pytest -n auto
```

## Test Categories and Markers

### Markers
- `unit` - Unit tests with mocked dependencies
- `integration` - Integration tests with real operations
- `rich_output` - Rich console output verification tests
- `slow` - Performance and long-running tests
- `network` - Tests requiring network access
- `windows` - Windows-specific tests
- `unix` - Unix-specific tests

### Test Categories

#### Unit Tests
- Test individual components in isolation
- Use mocked dependencies to avoid side effects
- Fast execution (< 1 second per test)
- High coverage of code paths and edge cases

#### Integration Tests
- Test complete workflows with real file operations
- Minimal mocking to verify actual functionality
- Use temporary directories for file system operations
- Verify end-to-end behavior

#### Rich Console Output Tests
- Verify Rich console output formatting and styling
- Use snapshot testing for consistent output verification
- Test progress bars, panels, tables, and styling
- Ensure Unicode and emoji support

#### Performance Tests
- Measure execution time and resource usage
- Test scalability with varying workloads
- Verify memory usage stability
- Test concurrent operation performance

#### Edge Case Tests
- Test boundary conditions and unusual inputs
- Test error handling with extreme scenarios
- Test resource exhaustion scenarios
- Test Unicode and special character handling

## Coverage Requirements

The test suite aims for comprehensive coverage:

- **Line Coverage**: > 90%
- **Branch Coverage**: > 85%
- **Function Coverage**: > 95%

### Coverage Exclusions
- Test files themselves
- Platform-specific code not available in test environment
- Error handling for system-level failures

## Rich Console Output Testing

### Snapshot Testing
Rich console output is tested using snapshot comparisons:

1. **First Run**: Creates baseline snapshots
2. **Subsequent Runs**: Compares output against saved snapshots
3. **Update Mode**: Updates snapshots when output changes intentionally

### Output Verification
- Text content verification
- Panel and border detection
- Progress bar element detection
- Color and styling verification
- Unicode and emoji support

## Performance Testing

### Performance Metrics
- **File Operations**: Files/second for extraction and creation
- **Directory Operations**: Directories/second for creation
- **Memory Usage**: Object count growth and stability
- **Concurrent Operations**: Performance under concurrent load

### Performance Thresholds
- File extraction: > 10 files/second
- Directory creation: > 100 directories/second
- Memory growth: < 50% increase during operations
- Complete workflow: < 30 seconds (mocked operations)

## Continuous Integration

### Test Execution Strategy
1. **Fast Tests**: Unit tests run on every commit
2. **Integration Tests**: Run on pull requests
3. **Performance Tests**: Run nightly or on release branches
4. **Full Suite**: Run before releases

### Test Environment Requirements
- Python 3.8+
- Windows and Linux test environments
- Sufficient disk space for temporary files
- Network access for download tests (optional)

## Troubleshooting

### Common Issues

#### Permission Errors
- Ensure test runner has appropriate permissions
- Use temporary directories for file operations
- Clean up test artifacts between runs

#### Platform-Specific Failures
- Some tests are platform-specific (Windows/Unix)
- Use appropriate skip markers for platform tests
- Mock platform-specific functionality when needed

#### Rich Console Output Issues
- Ensure terminal supports Unicode and colors
- Use appropriate console width settings
- Handle different terminal capabilities gracefully

#### Performance Test Failures
- Performance thresholds may vary by system
- Adjust thresholds for slower test environments
- Consider system load when running performance tests

### Debugging Tests

```bash
# Run with maximum verbosity
pytest -vvv

# Run with debugging output
pytest --tb=long

# Run specific failing test
pytest test_file.py::TestClass::test_method -v

# Run with pdb debugger
pytest --pdb

# Capture print statements
pytest -s
```

## Contributing to Tests

### Adding New Tests

1. **Choose Appropriate Test Type**:
   - Unit test for isolated component testing
   - Integration test for workflow testing
   - Performance test for timing-critical code

2. **Use Existing Fixtures**:
   - Leverage shared fixtures from `conftest.py`
   - Create new fixtures for reusable test data

3. **Follow Naming Conventions**:
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`

4. **Add Appropriate Markers**:
   - Mark tests with appropriate categories
   - Use skip markers for platform-specific tests

5. **Document Complex Tests**:
   - Add docstrings explaining test purpose
   - Comment complex test logic

### Test Quality Guidelines

- **Isolation**: Tests should not depend on each other
- **Repeatability**: Tests should produce consistent results
- **Speed**: Unit tests should be fast (< 1 second)
- **Clarity**: Test intent should be clear from name and structure
- **Coverage**: Tests should cover both success and failure paths

## Test Data Management

### Temporary Files
- Use `tempfile` module for temporary directories
- Clean up temporary files in fixture teardown
- Use context managers for automatic cleanup

### Mock Data
- Create realistic but minimal test data
- Use factories for generating test objects
- Store complex test data in fixture files

### Asset Files
- Store test assets in `assets/` directory
- Use small files to keep repository size manageable
- Generate test files programmatically when possible

## Maintenance

### Regular Maintenance Tasks
- Update test dependencies regularly
- Review and update performance thresholds
- Clean up obsolete tests
- Update snapshots when UI changes
- Review test coverage reports

### Test Suite Health Monitoring
- Monitor test execution time trends
- Track test failure rates
- Review coverage reports
- Update documentation as needed

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)