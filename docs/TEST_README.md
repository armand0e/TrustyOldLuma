# Luna Testing Guide

This document provides information on how to test the Luna Gaming Tool, including unit tests, integration tests, and end-to-end workflow tests.

## Test Structure

The Luna test suite is organized into the following categories:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete workflows from start to finish

## Running Tests

### All Tests

To run all tests, use the `run_tests.py` script:

```bash
python run_tests.py --all
```

### Unit Tests

To run only unit tests:

```bash
python run_tests.py --unit
```

With coverage report:

```bash
python run_tests.py --unit --coverage
```

### Integration Tests

To run only integration tests:

```bash
python run_tests.py --integration
```

To run specifically the Luna integration tests:

```bash
python tests/run_luna_integration_tests.py
```

### End-to-End Tests

To run the end-to-end workflow test:

```bash
python tests/end_to_end_luna_test.py
```

Options:
- `--verbose`: Enable verbose output
- `--no-cleanup`: Don't clean up test files after running

## Test Categories

### Luna Component Integration Tests

These tests verify that the Luna components work together correctly:

- Luna core initialization and configuration
- Interaction between injector and unlocker components
- Configuration management across components
- Legacy configuration migration
- Platform integration
- Error handling and recovery

### Luna Workflow Integration Tests

These tests verify end-to-end Luna workflows:

- Complete Luna installation from scratch
- Migration from existing GreenLuma/Koalageddon installations
- Desktop shortcuts and integration
- Platform-specific functionality
- Error handling and recovery scenarios

## Adding New Tests

When adding new tests:

1. Create a new test file in the appropriate directory:
   - Unit tests: `tests/unit/`
   - Integration tests: `tests/integration/`
   - End-to-end tests: `tests/`

2. Follow the existing test patterns and naming conventions

3. Update the appropriate test runner script to include your new test file

## Test Fixtures

The test suite provides several fixtures to help with testing:

- `temp_workspace`: Creates a temporary directory structure for testing
- `luna_config_file`: Creates a Luna configuration file for testing
- `luna_core`: Creates a Luna core instance for testing
- `mock_console`: Creates a mock Rich console for testing
- `setup_config`: Creates a test LunaConfig instance

See `tests/conftest.py` for more fixtures and utilities.

## Mocking

The tests use mocking to simulate external dependencies:

- File operations (extraction, download)
- Process management
- Security exclusions
- Shortcut creation

This allows the tests to run without requiring actual system resources or making changes to the system.

## Continuous Integration

The test suite is designed to run in a CI environment. The following environment variables can be used to configure the tests:

- `LUNA_TEST_VERBOSE`: Set to `1` to enable verbose output
- `LUNA_TEST_COVERAGE`: Set to `1` to generate coverage reports
- `LUNA_TEST_SKIP_SLOW`: Set to `1` to skip slow tests

## Troubleshooting

If you encounter issues running the tests:

1. Make sure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Check that the project structure is correct and all required files are present

3. Try running with the `--verbose` flag for more detailed output

4. Check for import errors, which may indicate incorrect Python path configuration

5. For end-to-end tests, try running with the `--no-cleanup` flag to inspect the test environment after execution