#!/usr/bin/env python3
"""
Basic usage example for prime-compatible SDK with PPIO backend

This demonstrates using the Prime-compatible API with PPIO sandboxes.
"""

from ppio_sandbox.prime_compatible import (
    APIClient,
    APIError,
    CreateSandboxRequest,
    SandboxClient,
)


def main():
    """Basic sandbox lifecycle example"""
    try:
        # Initialize client (uses PPIO_API_KEY env var)
        # APIClient is kept for API compatibility but not used.
        client = APIClient()
        sandbox_client = SandboxClient(client)

        print("Creating sandbox...")
        sandbox = sandbox_client.create(
            CreateSandboxRequest(
                name="basic-example",
                docker_image="code-interpreter-v1",
                timeout_minutes=60,
            )
        )
        print(f"✓ Created: {sandbox.id}")

        print("\nWaiting for sandbox to be ready...")
        sandbox_client.wait_for_creation(sandbox.id)
        print("✓ Sandbox is running!")

        print("\nExecuting commands...")
        result = sandbox_client.execute_command(sandbox.id, "python --version")
        print(f"Python version: {result.stdout.strip()}")

        result = sandbox_client.execute_command(
            sandbox.id, "python -c 'print(\"Hello from sandbox!\")'"
        )
        print(f"Output: {result.stdout.strip()}")

        print("\nCleaning up...")
        sandbox_client.delete(sandbox.id)
        print("✓ Deleted")

    except APIError as e:
        print(f"✗ API Error: {e}")
        print("  Make sure PPIO_API_KEY is set")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
