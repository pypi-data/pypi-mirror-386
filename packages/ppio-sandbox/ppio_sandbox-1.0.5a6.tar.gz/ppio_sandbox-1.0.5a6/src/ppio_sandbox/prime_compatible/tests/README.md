# Prime Compatible SDK Tests

This directory contains comprehensive unit tests for the `prime_compatible` module, specifically for the `sandbox.py` module.

## Test Structure

The tests are organized as follows:

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_models.py           # Tests for Pydantic models
├── test_sandbox.py          # Tests for SandboxClient (synchronous)
├── test_sandbox_async.py    # Tests for AsyncSandboxClient (asynchronous)
└── README.md               # This file
```

## Test Coverage

### `test_sandbox.py` (Synchronous Tests)

Tests for the `SandboxClient` class:

1. **TestSandboxClientCreate**: Sandbox creation tests
   - Basic sandbox creation
   - Sandbox creation with metadata (labels, env vars)
   - Invalid template handling

2. **TestSandboxClientList**: Sandbox listing tests
   - Basic listing
   - Filtering by status
   - Filtering by labels
   - Pagination

3. **TestSandboxClientGet**: Get sandbox info tests
   - Get existing sandbox
   - Get nonexistent sandbox

4. **TestSandboxClientDelete**: Sandbox deletion tests
   - Delete single sandbox
   - Bulk delete by IDs
   - Bulk delete by labels
   - Invalid parameters handling

5. **TestSandboxClientCommands**: Command execution tests
   - Basic command execution
   - Commands with environment variables
   - Commands with working directory
   - Command timeouts
   - Commands on nonexistent sandboxes

6. **TestSandboxClientFiles**: File operations tests
   - Upload files
   - Download files
   - Handling nonexistent files

7. **TestSandboxClientWait**: Wait operations tests
   - Wait for single sandbox creation
   - Bulk wait for multiple sandboxes

8. **TestSandboxClientOther**: Other operations tests
   - Get logs
   - Clear auth cache
   - Check sandbox reachability

### `test_sandbox_async.py` (Asynchronous Tests)

Equivalent tests for the `AsyncSandboxClient` class, all running asynchronously:

- All test classes mirror the synchronous version
- Additional test for context manager functionality

## Running the Tests

### Prerequisites

1. Install the package with test dependencies:
   ```bash
   poetry install
   ```

2. Set required environment variables:
   ```bash
   export PPIO_API_KEY="your-api-key"
   ```

### Run All Tests

```bash
# From the project root
poetry run pytest src/ppio_sandbox/prime_compatible/tests/

# Or from this directory
poetry run pytest .
```

### Run Specific Test Files

```bash
# Run only synchronous tests
poetry run pytest src/ppio_sandbox/prime_compatible/tests/test_sandbox.py

# Run only asynchronous tests
poetry run pytest src/ppio_sandbox/prime_compatible/tests/test_sandbox_async.py

# Run only model tests
poetry run pytest src/ppio_sandbox/prime_compatible/tests/test_models.py
```

### Run Specific Test Classes

```bash
# Run only creation tests
poetry run pytest src/ppio_sandbox/prime_compatible/tests/test_sandbox.py::TestSandboxClientCreate

# Run async command tests
poetry run pytest src/ppio_sandbox/prime_compatible/tests/test_sandbox_async.py::TestAsyncSandboxClientCommands
```

### Run Specific Tests

```bash
# Run a specific test
poetry run pytest src/ppio_sandbox/prime_compatible/tests/test_sandbox.py::TestSandboxClientCreate::test_create_sandbox_basic
```

### Run with Verbose Output

```bash
poetry run pytest -v src/ppio_sandbox/prime_compatible/tests/
```

### Run with Coverage

```bash
poetry run pytest --cov=ppio_sandbox.prime_compatible --cov-report=html src/ppio_sandbox/prime_compatible/tests/
```

## Test Markers

### `@pytest.mark.skip_debug()`

Tests marked with `@pytest.mark.skip_debug()` will be skipped when the `PPIO_DEBUG` environment variable is set. This is useful for tests that require actual sandbox operations.

To skip debug tests:
```bash
export PPIO_DEBUG=1
poetry run pytest src/ppio_sandbox/prime_compatible/tests/
```

## Test Fixtures

The following fixtures are available (defined in `conftest.py`):

- `sandbox_test_id`: Unique session ID for test sandboxes
- `template`: Default template to use (`"base"`)
- `api_client`: API client instance
- `sandbox_client`: Synchronous SandboxClient instance
- `async_sandbox_client`: Asynchronous AsyncSandboxClient instance
- `create_sandbox_request`: Default CreateSandboxRequest
- `debug`: Whether debug mode is enabled

## Notes

1. **Resource Cleanup**: All tests properly clean up sandboxes in `finally` blocks to prevent resource leaks.

2. **Test Isolation**: Each test creates its own sandbox with a unique name to avoid conflicts.

3. **Timeout Handling**: Tests use reasonable timeouts (usually 10 seconds for commands, 30 attempts for waiting).

4. **Error Handling**: Tests verify both successful operations and error cases.

5. **Async Tests**: Asynchronous tests use `async`/`await` and are marked with `async def`.

## Common Issues

### Tests timing out

If tests are timing out, try increasing the `max_attempts` parameter or check your network connection.

### Sandbox not found errors

These can occur if sandboxes are deleted by another process. The tests are designed to handle this gracefully.

### API key not set

Make sure the `PPIO_API_KEY` environment variable is set:
```bash
export PPIO_API_KEY="your-api-key"
```

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Use appropriate test classes to group related tests
3. Always clean up resources in `finally` blocks
4. Add docstrings to describe what each test does
5. Use the `@pytest.mark.skip_debug()` marker for tests that create actual sandboxes

