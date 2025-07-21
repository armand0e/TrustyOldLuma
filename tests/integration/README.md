# Luna Integration Tests

This directory contains integration tests for the Luna Gaming Tool. These tests verify the interaction between different Luna components and test end-to-end workflows.

## Test Files

- `test_luna_component_integration.py`: Tests the interaction between Luna injector and unlocker components, unified configuration management, and platform integration.
- `test_luna_workflow_integration.py`: Tests complete Luna workflows including installation, migration, desktop integration, and platform functionality.

## Running the Tests

You can run the Luna integration tests using the provided script:

```bash
python tests/run_luna_integration_tests.py
```

Or using pytest directly:

```bash
pytest tests/integration/test_luna_component_integration.py tests/integration/test_luna_workflow_integration.py -v
```

## Test Categories

### Component Integration Tests

These tests verify that the Luna components work together correctly:

- Luna core initialization and configuration
- Interaction between injector and unlocker components
- Configuration management across components
- Legacy configuration migration
- Platform integration
- Error handling and recovery

### Workflow Integration Tests

These tests verify end-to-end Luna workflows:

- Complete Luna installation from scratch
- Migration from existing GreenLuma/Koalageddon installations
- Desktop shortcuts and integration
- Platform-specific functionality
- Error handling and recovery scenarios

## Adding New Tests

When adding new integration tests:

1. Create a new test file in the `tests/integration` directory
2. Use the existing test files as templates
3. Add the new test file to `run_luna_integration_tests.py`
4. Add the new test file to `run_tests.py` in the `integration_test_files` list

## Test Fixtures

The integration tests use several fixtures to set up the test environment:

- `temp_workspace`: Creates a temporary directory structure for testing
- `luna_config_file`: Creates a Luna configuration file for testing
- `luna_core`: Creates a Luna core instance for testing
- `mock_console`: Creates a mock Rich console for testing
- `setup_config`: Creates a test LunaConfig instance

## Mocking

The tests use mocking to simulate external dependencies:

- File operations (extraction, download)
- Process management
- Security exclusions
- Shortcut creation

This allows the tests to run without requiring actual system resources or making changes to the system.