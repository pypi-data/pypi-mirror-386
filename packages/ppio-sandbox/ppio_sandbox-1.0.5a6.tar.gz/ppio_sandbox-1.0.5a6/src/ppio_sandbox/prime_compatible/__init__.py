"""Prime-Compatible Sandboxes SDK (PPIO Backend).

A Prime Intellect Sandboxes API-compatible SDK implementation using PPIO sandbox backend.
Provides the same interface as Prime Sandboxes SDK, allowing you to use PPIO sandboxes
with Prime-compatible code.

Note: This implementation uses PPIO's infrastructure, so some features (like custom
Docker images) are stored in metadata but may not affect actual sandbox configuration.
"""

from .prime_core import (
    APIClient,
    APIError,
    APITimeoutError,
    AsyncAPIClient,
    Config,
    PaymentRequiredError,
    UnauthorizedError,
)

from .exceptions import CommandTimeoutError, SandboxNotRunningError
from .models import (
    AdvancedConfigs,
    BulkDeleteSandboxRequest,
    BulkDeleteSandboxResponse,
    CommandRequest,
    CommandResponse,
    CreateSandboxRequest,
    FileUploadResponse,
    Sandbox,
    SandboxListResponse,
    SandboxStatus,
    UpdateSandboxRequest,
)
from .sandbox import AsyncSandboxClient, SandboxClient

__version__ = "0.1.0"

# Deprecated alias for backward compatibility
TimeoutError = APITimeoutError

__all__ = [
    # Core HTTP Client & Config
    "APIClient",
    "AsyncAPIClient",
    "Config",
    # Sandbox Clients
    "SandboxClient",
    "AsyncSandboxClient",
    # Models
    "Sandbox",
    "SandboxStatus",
    "SandboxListResponse",
    "CreateSandboxRequest",
    "UpdateSandboxRequest",
    "CommandRequest",
    "CommandResponse",
    "FileUploadResponse",
    "BulkDeleteSandboxRequest",
    "BulkDeleteSandboxResponse",
    "AdvancedConfigs",
    # Exceptions
    "APIError",
    "UnauthorizedError",
    "PaymentRequiredError",
    "APITimeoutError",
    "TimeoutError",  # Deprecated alias
    "SandboxNotRunningError",
    "CommandTimeoutError",
]
