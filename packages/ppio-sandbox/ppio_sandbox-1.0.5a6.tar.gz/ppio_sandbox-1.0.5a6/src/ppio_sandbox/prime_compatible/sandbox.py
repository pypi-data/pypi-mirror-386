"""Sandbox client implementations using ppio_sandbox.core."""

import json
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ppio_sandbox.core import Sandbox as PPIOSandbox, AsyncSandbox as PPIOAsyncSandbox
from ppio_sandbox.core import SandboxException, TimeoutException, NotFoundException
from ppio_sandbox.core.sandbox.sandbox_api import SandboxInfo, SandboxQuery
from ppio_sandbox.core.api.client.models import SandboxState

from .prime_core import APIClient, APIError
from .exceptions import CommandTimeoutError, SandboxNotRunningError
from .models import (
    SandboxStatus as PrimeSandboxStatus,
    BulkDeleteSandboxResponse,
    CommandResponse,
    CreateSandboxRequest,
    FileUploadResponse,
    Sandbox,
    SandboxListResponse,
)


DEFAULT_SANDBOX_TEMPLATE = "code-interpreter-v1"

def _map_ppio_state_to_prime_status(state: SandboxState) -> str:
    """Map PPIO sandbox state to Prime-compatible status"""
    if state == SandboxState.RUNNING:
        return PrimeSandboxStatus.RUNNING
    elif state == SandboxState.PAUSED:
        return PrimeSandboxStatus.PROVISIONING

def _labels_to_metadata(labels: List[str]) -> Dict[str, str]:
    """Convert labels to flat metadata KVs (label#<label>: 1)"""
    if not labels:
        return {}
    return {f"custom_label#{label}": "1" for label in labels if label}

def _extract_labels_from_metadata(metadata: Dict[str, str]) -> List[str]:
    """Extract labels from metadata"""
    labels = []
    for key, _ in metadata.items():
        if key.startswith("custom_label#"):
            labels.append(key.split("#")[1])
    return labels

def _envs_to_metadata(envs: Dict[str, str]) -> Dict[str, str]:
    """Convert environment vars to metadata"""
    if not envs:
        return {}
    return {"environment_vars": json.dumps(envs)}

def _extract_envs_from_metadata(metadata: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Retrieve environment vars from metadata"""
    env_str = metadata.get("environment_vars")
    if not env_str:
        return None
    try:
        parsed = json.loads(env_str)
        # Ensure we return a dict, not some other JSON type
        if isinstance(parsed, dict):
            return parsed if parsed else None
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def _sandbox_info_to_prime_sandbox(info: SandboxInfo, sbx_id: str) -> Sandbox:
    """Convert PPIO SandboxInfo to Prime Sandbox model"""
    # Extract metadata for mapping
    metadata = info.metadata or {}

    return Sandbox(
        id=sbx_id,
        name=metadata.get("sandbox_name", ""),
        # docker_image is similar to the "template" used to create the sandbox.
        # Refer to https://ppio.com/docs/sandbox/sandbox-template for more details.
        docker_image=info.name,
        # start_command is specified while building the sandbox template.
        # Refer to https://ppio.com/docs/sandbox/sandbox-template-start-cmd for more details.
        start_command=None,
        cpu_cores=info.cpu_count,
        # memory_mb represents memory in MiB (mebibytes); convert it to GB by dividing by 1024 and rounding up, which may result in a slightly higher value than the exact memory size in GB.
        memory_gb=math.ceil(info.memory_mb / 1024),
        # disk_size_gb is not directly available from PPIO SandboxInfo, using default or metadata
        disk_size_gb=int(metadata.get("disk_size_gb", 0)),
        # disk_mount_path is typically /home/user in PPIO sandboxes
        disk_mount_path=metadata.get("disk_mount_path", ""),
        # gpu_count is always 0 for now as PPIO doesn't support GPUs.
        gpu_count=0,
        status=_map_ppio_state_to_prime_status(info.state),
        timeout_minutes=int(
            (info.end_at - info.started_at).total_seconds() / 60),
        environment_vars=_extract_envs_from_metadata(metadata),
        advanced_configs=None,
        labels=_extract_labels_from_metadata(metadata),
        created_at=info.started_at,
        updated_at=info.started_at,
        started_at=info.started_at,
        terminated_at=None if info.state == SandboxState.RUNNING else info.end_at,
        exit_code=None,
        user_id=None,
        team_id=None,
        kubernetes_job_id=None,
    )


class SandboxClient:
    """Client for sandbox API operations using PPIO backend"""

    def __init__(self, api_client: APIClient):
        # api_client parameter is kept for API compatibility but not used.
        pass

    def _is_sandbox_reachable(self, sandbox_id: str, timeout: int = 10) -> bool:
        """Test if a sandbox is reachable by executing a simple echo command"""
        try:
            self.execute_command(
                sandbox_id, "echo 'sandbox ready'", timeout=timeout)
            return True
        except Exception:
            return False

    def clear_auth_cache(self) -> None:
        """Clear all cached auth tokens (no-op for PPIO backend)"""
        pass
    
    def create(self, request: CreateSandboxRequest) -> Sandbox:
        """Create a new sandbox"""
        # Build metadata to preserve Prime-specific fields
        metadata = {}
        
        request.docker_image = request.docker_image or DEFAULT_SANDBOX_TEMPLATE
        
        # Add sandbox name to metadata
        if request.name:
            metadata["sandbox_name"] = request.name

        if request.team_id:
            metadata["team_id"] = request.team_id

        # Add labels to metadata
        if request.labels:
            metadata.update(_labels_to_metadata(request.labels))

        # Add environment vars to metadata
        if request.environment_vars:
            metadata.update(_envs_to_metadata(request.environment_vars))

        # Create PPIO sandbox
        # Note: We use template "base" and try to configure closest settings
        # PPIO doesn't support custom docker images, so we store it in metadata
        try:
            sandbox = PPIOSandbox.create(
                template=request.docker_image,
                timeout=request.timeout_minutes * 60,  # Convert minutes to seconds
                metadata=metadata,
                envs=request.environment_vars,
            )

            # Get sandbox info and convert to Prime format
            info = sandbox.get_info()
            return _sandbox_info_to_prime_sandbox(info, sandbox.sandbox_id)

        except SandboxException as e:
            raise APIError(f"Failed to create sandbox: {str(e)}")
        except Exception as e:
            raise APIError(f"Unexpected error creating sandbox: {str(e)}")

    def list(
        self,
        team_id: Optional[str] = None,
        status: Optional[str] = None,
        labels: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 50,
        exclude_terminated: Optional[bool] = None,
    ) -> SandboxListResponse:
        """List sandboxes"""

        # exclude_terminated is unused for now, because we filter all the terminated sandboxes by default.
        _ = exclude_terminated

        try:
            # Build query filters
            query_metadata = {}
            if team_id:
                query_metadata["team_id"] = team_id
            if labels:
                label_metadata = _labels_to_metadata(labels)
                if label_metadata:  # Only update if not empty
                    query_metadata.update(label_metadata)

            query_states = None
            if status:
                # Map Prime status to PPIO states
                if status == PrimeSandboxStatus.RUNNING:
                    query_states = [SandboxState.RUNNING]
                elif status == PrimeSandboxStatus.PENDING or status == PrimeSandboxStatus.STOPPED:
                    query_states = [SandboxState.PAUSED]

            query = None
            if query_metadata or query_states:
                query = SandboxQuery(
                    metadata=query_metadata if query_metadata else None,
                    state=query_states,
                )

            # PPIO list returns a paginator
            paginator = PPIOSandbox.list(
                query=query,
                limit=per_page,
            )

            # Navigate to the requested page
            # For page 1, we're already there; for page N, we need to call next_items() N-1 times
            for _ in range(page - 1):
                if not paginator.has_next:
                    # Requested page doesn't exist
                    return SandboxListResponse(
                        sandboxes=[],
                        total=0,
                        page=page,
                        per_page=per_page,
                        has_next=False,
                    )
                paginator.next_items()

            # Get items for the current page
            page_items = paginator.next_items()

            # Convert to Prime sandboxes
            sandboxes = [
                _sandbox_info_to_prime_sandbox(info, info.sandbox_id)
                for info in page_items
            ]

            return SandboxListResponse(
                sandboxes=sandboxes,
                total=len(sandboxes),  # Note: PPIO doesn't provide total count
                page=page,
                per_page=per_page,
                has_next=paginator.has_next,
            )

        except SandboxException as e:
            raise APIError(f"Failed to list sandboxes: {str(e)}")
        except Exception as e:
            raise APIError(f"Unexpected error listing sandboxes: {str(e)}")

    def get(self, sandbox_id: str) -> Sandbox:
        """Get a specific sandbox"""
        try:
            info = PPIOSandbox.get_info(sandbox_id)
            return _sandbox_info_to_prime_sandbox(info, sandbox_id)
        except NotFoundException:
            raise APIError(f"Sandbox {sandbox_id} not found")
        except SandboxException as e:
            raise APIError(f"Failed to get sandbox: {str(e)}")
        # TODO: Remove this once we have a better error handling in PPIO SDK.
        # Since we'll get unexpected errors like "sandbox \"nonexistent-sandbox-id-xyz\" doesn't exist or you don't have access to it" when the sandbox is not found.
        except Exception as e:
            raise APIError(f"Unexpected error getting sandbox: {str(e)}")

    def delete(self, sandbox_id: str) -> Dict[str, Any]:
        """Delete a sandbox"""
        try:
            # Try to kill the sandbox
            killed = PPIOSandbox.kill(sandbox_id)
            return {"success": killed, "message": "Sandbox deleted" if killed else "Sandbox not found"}
        except Exception as e:
            raise APIError(f"Failed to delete sandbox: {str(e)}")

    def bulk_delete(
        self,
        sandbox_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> BulkDeleteSandboxResponse:
        """Bulk delete multiple sandboxes by IDs or labels (must specify one, not both)"""
        if (sandbox_ids is None and labels is None) or (sandbox_ids is not None and labels is not None):
            raise APIError(
                "Must specify either sandbox_ids or labels, but not both")

        ids_to_delete = sandbox_ids or []

        # If labels specified, find matching sandboxes
        if labels:
            try:
                list_response = self.list(labels=labels, per_page=1000)
                ids_to_delete = [sbx.id for sbx in list_response.sandboxes]
            except Exception as e:
                raise APIError(f"Failed to find sandboxes by labels: {str(e)}")

        succeeded = []
        failed = []

        for sandbox_id in ids_to_delete:
            try:
                self.delete(sandbox_id)
                succeeded.append(sandbox_id)
            except Exception as e:
                failed.append({"id": sandbox_id, "error": str(e)})

        return BulkDeleteSandboxResponse(
            succeeded=succeeded,
            failed=failed,
            message=f"Deleted {len(succeeded)}/{len(ids_to_delete)} sandboxes",
        )

    def get_logs(self, sandbox_id: str) -> str:
        """Get sandbox logs via backend

        Note: PPIO doesn't have a direct logs API, so we'll return a message
        """
        return "Logs not directly available via PPIO backend. Use sandbox.commands.run() to execute commands."

    def execute_command(
        self,
        sandbox_id: str,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> CommandResponse:
        """Execute command via PPIO sandbox"""
        try:
            sandbox = PPIOSandbox.connect(sandbox_id)

            # Execute the command
            effective_timeout = timeout if timeout is not None else 300

            try:
                result = sandbox.commands.run(
                    cmd=command,
                    cwd=working_dir or None,
                    envs=env or {},
                    timeout=effective_timeout,
                )

                return CommandResponse(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.exit_code,
                )
            except TimeoutException:
                raise CommandTimeoutError(
                    sandbox_id, command, effective_timeout)

        except NotFoundException:
            raise SandboxNotRunningError(sandbox_id, "NOT_FOUND")
        except SandboxException as e:
            raise APIError(f"Command execution failed: {str(e)}")

    def wait_for_creation(self, sandbox_id: str, max_attempts: int = 60) -> None:
        """Wait for sandbox to be running"""
        for attempt in range(max_attempts):
            try:
                sandbox = self.get(sandbox_id)
                if sandbox.status == "RUNNING":
                    if self._is_sandbox_reachable(sandbox_id):
                        return
                elif sandbox.status in ["ERROR", "TERMINATED", "TIMEOUT", "STOPPED"]:
                    raise SandboxNotRunningError(sandbox_id, sandbox.status)
            except APIError:
                pass  # Might not be ready yet

            # Aggressive polling for first 5 attempts (5 seconds), then back off
            sleep_time = 1 if attempt < 5 else 2
            time.sleep(sleep_time)

        raise SandboxNotRunningError(
            sandbox_id, "Timeout during sandbox creation")

    def bulk_wait_for_creation(
        self, sandbox_ids: List[str], max_attempts: int = 60
    ) -> Dict[str, str]:
        """Wait for multiple sandboxes to be running"""
        final_statuses = {}

        for attempt in range(max_attempts):
            all_ready = True

            for sandbox_id in sandbox_ids:
                if sandbox_id in final_statuses:
                    continue

                try:
                    sandbox = self.get(sandbox_id)

                    if sandbox.status == "RUNNING":
                        if self._is_sandbox_reachable(sandbox_id):
                            final_statuses[sandbox_id] = "RUNNING"
                        else:
                            all_ready = False
                    elif sandbox.status in ["ERROR", "TERMINATED", "TIMEOUT", "STOPPED"]:
                        raise RuntimeError(
                            f"Sandbox {sandbox_id} failed with status: {sandbox.status}")
                    else:
                        all_ready = False
                except APIError:
                    all_ready = False

            if len(final_statuses) == len(sandbox_ids) and all_ready:
                return final_statuses

            sleep_time = 1 if attempt < 5 else 2
            time.sleep(sleep_time)

        # Mark remaining as timeout
        for sandbox_id in sandbox_ids:
            if sandbox_id not in final_statuses:
                final_statuses[sandbox_id] = "TIMEOUT"

        raise RuntimeError(
            f"Timeout waiting for sandboxes to be ready. Status: {final_statuses}")

    def upload_file(
        self, sandbox_id: str, file_path: str, local_file_path: str
    ) -> FileUploadResponse:
        """Upload file to sandbox via PPIO"""
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        try:
            # Get or connect to the sandbox
            sandbox = PPIOSandbox.connect(sandbox_id)

            # Read local file and write to sandbox
            with open(local_file_path, "rb") as f:
                content = f.read()

            sandbox.files.write(file_path, content)

            # Get file size
            file_size = len(content)

            return FileUploadResponse(
                success=True,
                path=file_path,
                size=file_size,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            raise APIError(f"Upload failed: {str(e)}")

    def download_file(self, sandbox_id: str, file_path: str, local_file_path: str) -> None:
        """Download file from sandbox via PPIO"""
        try:
            # Get or connect to the sandbox
            sandbox = PPIOSandbox.connect(sandbox_id)

            # Read from sandbox and write to local file
            content = sandbox.files.read(file_path)

            # Ensure directory exists
            dir_path = os.path.dirname(local_file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # Write to local file
            if isinstance(content, bytes):
                with open(local_file_path, "wb") as f:
                    f.write(content)
            else:
                with open(local_file_path, "w") as f:
                    f.write(content)

        except Exception as e:
            raise APIError(f"Download failed: {str(e)}")


class AsyncSandboxClient:
    """Async client for sandbox API operations using PPIO backend"""

    def __init__(self, api_key: Optional[str] = None):
        # api_key parameter is kept for API compatibility but not used
        # PPIO SDK uses environment variables.
        pass

    async def _is_sandbox_reachable(self, sandbox_id: str, timeout: int = 10) -> bool:
        """Test if a sandbox is reachable by executing a simple echo command"""
        try:
            await self.execute_command(sandbox_id, "echo 'sandbox ready'", timeout=timeout)
            return True
        except Exception:
            return False

    def clear_auth_cache(self) -> None:
        """Clear all cached auth tokens (no-op for PPIO backend)"""
        pass

    async def create(self, request: CreateSandboxRequest) -> Sandbox:
        """Create a new sandbox"""
        # Build metadata to preserve Prime-specific fields
        metadata = {}
        request.docker_image = request.docker_image or DEFAULT_SANDBOX_TEMPLATE

        if request.name:
            metadata["sandbox_name"] = request.name

        if request.team_id:
            metadata["team_id"] = request.team_id

        # Add labels to metadata
        if request.labels:
            metadata.update(_labels_to_metadata(request.labels))

        # Add environment vars to metadata
        if request.environment_vars:
            metadata.update(_envs_to_metadata(request.environment_vars))

        # Create PPIO sandbox
        # Note: We use the docker_image as template name
        # PPIO doesn't support custom docker images, so we use it as template identifier
        try:
            sandbox = await PPIOAsyncSandbox.create(
                template=request.docker_image,
                timeout=request.timeout_minutes * 60,  # Convert minutes to seconds
                metadata=metadata,
                envs=request.environment_vars,
            )

            # Get sandbox info and convert to Prime format
            info = await sandbox.get_info()
            return _sandbox_info_to_prime_sandbox(info, sandbox.sandbox_id)

        except SandboxException as e:
            raise APIError(f"Failed to create sandbox: {str(e)}")
        except Exception as e:
            raise APIError(f"Unexpected error creating sandbox: {str(e)}")

    async def list(
        self,
        team_id: Optional[str] = None,
        status: Optional[str] = None,
        labels: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 50,
        exclude_terminated: Optional[bool] = None,
    ) -> SandboxListResponse:
        """List sandboxes"""

        # exclude_terminated is unused for now, because we filter all the terminated sandboxes by default.
        _ = exclude_terminated

        try:
            # Build query filters
            query_metadata = {}
            if team_id:
                query_metadata["team_id"] = team_id
            if labels:
                label_metadata = _labels_to_metadata(labels)
                if label_metadata:  # Only update if not empty
                    query_metadata.update(label_metadata)

            query_states = None
            if status:
                # Map Prime status to PPIO states
                if status == PrimeSandboxStatus.RUNNING:
                    query_states = [SandboxState.RUNNING]
                elif status == PrimeSandboxStatus.PENDING or status == PrimeSandboxStatus.STOPPED:
                    query_states = [SandboxState.PAUSED]

            query = None
            if query_metadata or query_states:
                query = SandboxQuery(
                    metadata=query_metadata if query_metadata else None,
                    state=query_states,
                )

            # PPIO list returns a paginator 
            paginator = PPIOAsyncSandbox.list(
                query=query,
                limit=per_page,
            )

            # Navigate to the requested page
            # For page 1, we're already there; for page N, we need to call next_items() N-1 times
            for _ in range(page - 1):
                if not paginator.has_next:
                    # Requested page doesn't exist
                    return SandboxListResponse(
                        sandboxes=[],
                        total=0,
                        page=page,
                        per_page=per_page,
                        has_next=False,
                    )
                await paginator.next_items()

            # Get items for the current page
            page_items = await paginator.next_items()

            # Convert to Prime sandboxes
            sandboxes = [
                _sandbox_info_to_prime_sandbox(info, info.sandbox_id)
                for info in page_items
            ]

            return SandboxListResponse(
                sandboxes=sandboxes,
                total=len(sandboxes),  # Note: PPIO doesn't provide total count
                page=page,
                per_page=per_page,
                has_next=paginator.has_next,
            )

        except SandboxException as e:
            raise APIError(f"Failed to list sandboxes: {str(e)}")
        except Exception as e:
            raise APIError(f"Unexpected error listing sandboxes: {str(e)}")

    async def get(self, sandbox_id: str) -> Sandbox:
        """Get a specific sandbox"""
        try:
            info = await PPIOAsyncSandbox.get_info(sandbox_id)
            return _sandbox_info_to_prime_sandbox(info, sandbox_id)
        except NotFoundException:
            raise APIError(f"Sandbox {sandbox_id} not found")
        except SandboxException as e:
            raise APIError(f"Failed to get sandbox: {str(e)}")
        # TODO: Remove this once we have a better error handling in PPIO SDK.
        # Since we'll get unexpected errors like "sandbox \"nonexistent-sandbox-id-xyz\" doesn't exist or you don't have access to it" when the sandbox is not found.
        except Exception as e:
            raise APIError(f"Unexpected error getting sandbox: {str(e)}")

    async def delete(self, sandbox_id: str) -> Dict[str, Any]:
        """Delete a sandbox"""
        try:
            # Try to kill the sandbox
            killed = await PPIOAsyncSandbox.kill(sandbox_id)

            return {"success": killed, "message": "Sandbox deleted" if killed else "Sandbox not found"}
        except Exception as e:
            raise APIError(f"Failed to delete sandbox: {str(e)}")

    async def bulk_delete(
        self,
        sandbox_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> BulkDeleteSandboxResponse:
        """Bulk delete multiple sandboxes by IDs or labels"""
        if (sandbox_ids is None and labels is None) or (sandbox_ids is not None and labels is not None):
            raise APIError(
                "Must specify either sandbox_ids or labels, but not both")

        ids_to_delete = sandbox_ids or []

        # If labels specified, find matching sandboxes
        if labels:
            try:
                list_response = await self.list(labels=labels, per_page=1000)
                ids_to_delete = [sbx.id for sbx in list_response.sandboxes]
            except Exception as e:
                raise APIError(f"Failed to find sandboxes by labels: {str(e)}")

        succeeded = []
        failed = []

        for sandbox_id in ids_to_delete:
            try:
                await self.delete(sandbox_id)
                succeeded.append(sandbox_id)
            except Exception as e:
                failed.append({"id": sandbox_id, "error": str(e)})

        return BulkDeleteSandboxResponse(
            succeeded=succeeded,
            failed=failed,
            message=f"Deleted {len(succeeded)}/{len(ids_to_delete)} sandboxes",
        )

    async def get_logs(self, sandbox_id: str) -> str:
        """Get sandbox logs

        Note: PPIO doesn't have a direct logs API, so we'll return a message
        """
        return "Logs not directly available via PPIO backend. Use sandbox.commands.run() to execute commands."

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> CommandResponse:
        """Execute command via PPIO sandbox (async)"""
        try:
            sandbox = await PPIOAsyncSandbox.connect(sandbox_id)

            # Execute the command
            effective_timeout = timeout if timeout is not None else 300

            try:
                result = await sandbox.commands.run(
                    cmd=command,
                    cwd=working_dir or None,
                    envs=env or {},
                    timeout=effective_timeout,
                )

                return CommandResponse(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.exit_code,
                )
            except TimeoutException:
                raise CommandTimeoutError(
                    sandbox_id, command, effective_timeout)

        except NotFoundException:
            raise SandboxNotRunningError(sandbox_id, "NOT_FOUND")
        except SandboxException as e:
            raise APIError(f"Command execution failed: {str(e)}")

    async def wait_for_creation(self, sandbox_id: str, max_attempts: int = 60) -> None:
        """Wait for sandbox to be running (async version)"""
        import asyncio

        for attempt in range(max_attempts):
            try:
                sandbox = await self.get(sandbox_id)
                if sandbox.status == "RUNNING":
                    if await self._is_sandbox_reachable(sandbox_id):
                        return
                elif sandbox.status in ["ERROR", "TERMINATED", "TIMEOUT", "STOPPED"]:
                    raise SandboxNotRunningError(sandbox_id, sandbox.status)
            except APIError:
                pass  # Might not be ready yet

            sleep_time = 1 if attempt < 5 else 2
            await asyncio.sleep(sleep_time)

        raise SandboxNotRunningError(
            sandbox_id, "Timeout during sandbox creation")

    async def bulk_wait_for_creation(
        self, sandbox_ids: List[str], max_attempts: int = 60
    ) -> Dict[str, str]:
        """Wait for multiple sandboxes to be running"""
        import asyncio

        final_statuses = {}

        for attempt in range(max_attempts):
            all_ready = True

            for sandbox_id in sandbox_ids:
                if sandbox_id in final_statuses:
                    continue

                try:
                    sandbox = await self.get(sandbox_id)

                    if sandbox.status == "RUNNING":
                        if await self._is_sandbox_reachable(sandbox_id):
                            final_statuses[sandbox_id] = "RUNNING"
                        else:
                            all_ready = False
                    elif sandbox.status in ["ERROR", "TERMINATED", "TIMEOUT", "STOPPED"]:
                        raise RuntimeError(
                            f"Sandbox {sandbox_id} failed with status: {sandbox.status}")
                    else:
                        all_ready = False
                except APIError:
                    all_ready = False

            if len(final_statuses) == len(sandbox_ids) and all_ready:
                return final_statuses

            sleep_time = 1 if attempt < 5 else 2
            await asyncio.sleep(sleep_time)

        # Mark remaining as timeout
        for sandbox_id in sandbox_ids:
            if sandbox_id not in final_statuses:
                final_statuses[sandbox_id] = "TIMEOUT"

        raise RuntimeError(
            f"Timeout waiting for sandboxes to be ready. Status: {final_statuses}")

    async def upload_file(
        self, sandbox_id: str, file_path: str, local_file_path: str
    ) -> FileUploadResponse:
        """Upload a file to a sandbox (async)"""
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        try:
            sandbox = await PPIOAsyncSandbox.connect(sandbox_id)

            # Read local file and write to sandbox
            with open(local_file_path, "rb") as f:
                content = f.read()

            await sandbox.files.write(file_path, content)

            # Get file size
            file_size = len(content)

            return FileUploadResponse(
                success=True,
                path=file_path,
                size=file_size,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            raise APIError(f"Upload failed: {str(e)}")

    async def download_file(self, sandbox_id: str, file_path: str, local_file_path: str) -> None:
        """Download a file from a sandbox (async)"""
        try:
            sandbox = await PPIOAsyncSandbox.connect(sandbox_id)

            # Read from sandbox and write to local file
            content = await sandbox.files.read(file_path)

            # Ensure directory exists
            dir_path = os.path.dirname(local_file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # Write to local file
            if isinstance(content, bytes):
                with open(local_file_path, "wb") as f:
                    f.write(content)
            else:
                with open(local_file_path, "w") as f:
                    f.write(content)

        except Exception as e:
            raise APIError(f"Download failed: {str(e)}")

    async def aclose(self) -> None:
        """Close the async client"""
        # No cleanup needed - PPIO SDK handles connection management
        pass

    async def __aenter__(self) -> "AsyncSandboxClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.aclose()
