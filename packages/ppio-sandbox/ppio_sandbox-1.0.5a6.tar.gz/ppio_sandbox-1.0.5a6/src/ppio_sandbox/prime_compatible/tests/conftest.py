"""Pytest configuration and fixtures for prime_compatible tests"""

import os
import uuid
from logging import warning

import pytest
import pytest_asyncio

from ppio_sandbox.prime_compatible.sandbox import SandboxClient, AsyncSandboxClient
from ppio_sandbox.prime_compatible.models import CreateSandboxRequest
from ppio_sandbox.prime_compatible.prime_core import APIClient


@pytest.fixture(scope="session")
def sandbox_test_id():
    """Generate a unique test ID for this session"""
    return f"prime_test_{uuid.uuid4()}"


@pytest.fixture()
def template():
    """Default template to use for tests"""
    return "code-interpreter-v1"


@pytest.fixture()
def api_client():
    """Create an API client instance"""
    # The APIClient is used for compatibility but not actually used by SandboxClient
    api_key = os.getenv("PPIO_API_KEY", "")
    if not api_key:
        raise ValueError("PPIO_API_KEY is not set")
    return APIClient(api_key=api_key)


@pytest.fixture()
def sandbox_client(api_client):
    """Create a SandboxClient instance"""
    return SandboxClient(api_client)


@pytest.fixture()
def async_sandbox_client():
    """Create an AsyncSandboxClient instance"""
    api_key = os.getenv("PPIO_API_KEY", "test-key")
    return AsyncSandboxClient(api_key=api_key)


@pytest.fixture()
def create_sandbox_request(template, sandbox_test_id):
    """Create a default CreateSandboxRequest"""
    return CreateSandboxRequest(
        name=f"test-sandbox-{sandbox_test_id[:8]}",
        docker_image=template,
        timeout_minutes=10,
        labels=["test", f"test-id-{sandbox_test_id}"],
    )


@pytest.fixture
def debug():
    """Check if debug mode is enabled"""
    return os.getenv("PPIO_DEBUG") is not None


@pytest.fixture(autouse=True)
def skip_by_debug(request, debug):
    """Skip tests marked with skip_debug if PPIO_DEBUG is set"""
    if request.node.get_closest_marker("skip_debug"):
        if debug:
            pytest.skip("skipped because PPIO_DEBUG is set")

