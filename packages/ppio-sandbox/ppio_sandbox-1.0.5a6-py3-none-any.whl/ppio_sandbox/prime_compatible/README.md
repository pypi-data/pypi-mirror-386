# Prime-Compatible Sandboxes SDK (PPIO Backend)

This is a Prime Intellect Sandboxes API-compatible SDK implementation that uses the PPIO sandbox service as the backend. It provides the same interface as the Prime Sandboxes SDK, allowing you to use PPIO sandboxes with Prime-compatible code.

## Features

- **Prime-compatible API** - Drop-in replacement for Prime Sandboxes SDK
- **PPIO backend** - Powered by PPIO's robust sandbox infrastructure
- **Synchronous and async clients** - Use with sync or async/await code
- **Full sandbox lifecycle** - Create, list, execute commands, upload/download files, delete
- **Type-safe** - Full type hints and Pydantic models
- **Bulk operations** - Create and manage multiple sandboxes efficiently

## Important Notes

This implementation uses PPIO sandboxes under the hood, which means:

- **Templates instead of Docker images**: PPIO uses pre-built templates (e.g., "base"). Custom docker_image values are stored in metadata but not actively used.
- **Limited customization**: Some Prime-specific features like custom CPU/memory/GPU configs are stored in metadata but may not affect the actual sandbox resources.
- **Different pricing**: You'll be billed according to PPIO's pricing model.

## Quick Start

```python
from ppio_sandbox.prime_compatible import APIClient, SandboxClient, CreateSandboxRequest

# Initialize (uses PPIO_API_KEY environment variable)
client = APIClient(api_key="your-ppio-api-key")
sandbox_client = SandboxClient(client)

# Create a sandbox
request = CreateSandboxRequest(
    name="my-sandbox",
    docker_image="python:3.11-slim",  # Stored in metadata, actual template is "base"
    cpu_cores=2,
    memory_gb=4,
)

sandbox = sandbox_client.create(request)
print(f"Created: {sandbox.id}")

# Wait for it to be ready
sandbox_client.wait_for_creation(sandbox.id)

# Execute commands
result = sandbox_client.execute_command(sandbox.id, "python --version")
print(result.stdout)

# Clean up
sandbox_client.delete(sandbox.id)
```

## Async Usage

```python
import asyncio
from ppio_sandbox.prime_compatible import AsyncSandboxClient, CreateSandboxRequest

async def main():
    async with AsyncSandboxClient(api_key="your-ppio-api-key") as client:
        # Create sandbox
        sandbox = await client.create(CreateSandboxRequest(
            name="async-sandbox",
            docker_image="python:3.11-slim",
        ))

        # Wait and execute
        await client.wait_for_creation(sandbox.id)
        result = await client.execute_command(sandbox.id, "echo 'Hello from async!'")
        print(result.stdout)

        # Clean up
        await client.delete(sandbox.id)

asyncio.run(main())
```

## Authentication

The SDK looks for credentials in this order:

1. **Direct parameter**: `APIClient(api_key="your-ppio-api-key")`
2. **Environment variable**: `export PPIO_API_KEY="your-ppio-api-key"` (recommended)
3. **Prime config file fallback**: `~/.prime/config.json` (if available)

## Advanced Features

### File Operations

```python
# Upload a file
sandbox_client.upload_file(
    sandbox_id=sandbox.id,
    file_path="/app/script.py",
    local_file_path="./local_script.py"
)

# Download a file
sandbox_client.download_file(
    sandbox_id=sandbox.id,
    file_path="/app/output.txt",
    local_file_path="./output.txt"
)
```

### Bulk Operations

```python
# Create multiple sandboxes
sandbox_ids = []
for i in range(5):
    sandbox = sandbox_client.create(CreateSandboxRequest(
        name=f"sandbox-{i}",
        docker_image="python:3.11-slim",
    ))
    sandbox_ids.append(sandbox.id)

# Wait for all to be ready
statuses = sandbox_client.bulk_wait_for_creation(sandbox_ids)

# Delete by IDs or labels
sandbox_client.bulk_delete(sandbox_ids=sandbox_ids)
# OR by labels
sandbox_client.bulk_delete(labels=["experiment-1"])
```

### Labels & Filtering

```python
# Create with labels
sandbox = sandbox_client.create(CreateSandboxRequest(
    name="labeled-sandbox",
    docker_image="python:3.11-slim",
    labels=["experiment", "ml-training"],
))

# List with filters
sandboxes = sandbox_client.list(
    status="RUNNING",
    labels=["experiment"],
    page=1,
    per_page=50,
)

for s in sandboxes.sandboxes:
    print(f"{s.name}: {s.status}")
```
