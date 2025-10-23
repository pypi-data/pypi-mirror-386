"""Tests for AsyncSandboxClient (asynchronous)"""

import os
import tempfile
from datetime import datetime

import pytest

from ppio_sandbox.prime_compatible.sandbox import AsyncSandboxClient
from ppio_sandbox.prime_compatible.models import (
    CreateSandboxRequest,
    SandboxStatus,
)
from ppio_sandbox.prime_compatible.exceptions import (
    CommandTimeoutError,
    SandboxNotRunningError,
)
from ppio_sandbox.prime_compatible.prime_core import APIError


class TestAsyncSandboxClientCreate:
    """Tests for async sandbox creation"""

    @pytest.mark.skip_debug()
    async def test_create_sandbox_basic(self, async_sandbox_client: AsyncSandboxClient, template, sandbox_test_id):
        """Test creating a basic sandbox asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-create-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)

            assert sandbox is not None
            assert sandbox.id is not None
            assert sandbox.name == request.name
            assert sandbox.docker_image == template
            assert sandbox.timeout_minutes == 10
            assert sandbox.status in [SandboxStatus.RUNNING, SandboxStatus.PENDING]
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_create_sandbox_with_metadata(self, async_sandbox_client, template, sandbox_test_id):
        """Test creating a sandbox with metadata asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-metadata-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=["test", "async", "metadata"],
            environment_vars={"ASYNC_TEST": "async_value"},
            team_id="test-async-team",
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)

            assert sandbox is not None
            assert "test" in sandbox.labels
            assert "async" in sandbox.labels
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_create_sandbox_invalid_template(self, async_sandbox_client, sandbox_test_id):
        """Test creating a sandbox with invalid template asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-invalid-{sandbox_test_id[:8]}",
            docker_image="nonexistent-template-xyz-async",
            timeout_minutes=10,
        )

        with pytest.raises(APIError):
            await async_sandbox_client.create(request)


class TestAsyncSandboxClientList:
    """Tests for listing sandboxes asynchronously"""

    @pytest.mark.skip_debug()
    async def test_list_sandboxes_basic(self, async_sandbox_client):
        """Test listing sandboxes asynchronously"""
        response = await async_sandbox_client.list(page=1, per_page=10)

        assert response is not None
        assert isinstance(response.sandboxes, list)
        assert response.page == 1
        assert response.per_page == 10
        assert isinstance(response.has_next, bool)

    @pytest.mark.skip_debug()
    async def test_list_sandboxes_with_status_filter(self, async_sandbox_client, template, sandbox_test_id):
        """Test listing sandboxes filtered by status asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-list-status-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            response = await async_sandbox_client.list(
                status=SandboxStatus.RUNNING, per_page=50
            )

            # Check if our sandbox appears in the list
            sandbox_ids = [s.id for s in response.sandboxes]
            assert sandbox.id in sandbox_ids or not response.has_next
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_list_sandboxes_with_labels(self, async_sandbox_client, template, sandbox_test_id):
        """Test listing sandboxes filtered by labels asynchronously"""
        unique_label = f"test-async-label-{sandbox_test_id[:8]}"
        request = CreateSandboxRequest(
            name=f"test-async-list-labels-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=[unique_label, "async-test"],
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)

            response = await async_sandbox_client.list(labels=[unique_label], per_page=50)

            # Our sandbox should appear in the list
            sandbox_ids = [s.id for s in response.sandboxes]
            assert sandbox.id in sandbox_ids
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_list_sandboxes_pagination(self, async_sandbox_client):
        """Test pagination when listing sandboxes asynchronously"""
        # Test first page
        response_page1 = await async_sandbox_client.list(page=1, per_page=5)
        assert response_page1.page == 1

        # Test page beyond available items
        response_empty = await async_sandbox_client.list(page=1000, per_page=5)
        assert response_empty.page == 1000
        assert len(response_empty.sandboxes) == 0


class TestAsyncSandboxClientGet:
    """Tests for getting sandbox info asynchronously"""

    @pytest.mark.skip_debug()
    async def test_get_sandbox(self, async_sandbox_client, template, sandbox_test_id):
        """Test getting a specific sandbox asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-get-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)

            retrieved = await async_sandbox_client.get(sandbox.id)

            assert retrieved.id == sandbox.id
            assert retrieved.name == sandbox.name
            assert retrieved.docker_image == template
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_get_nonexistent_sandbox(self, async_sandbox_client):
        """Test getting a nonexistent sandbox asynchronously"""
        with pytest.raises(APIError):
            await async_sandbox_client.get("nonexistent-async-sandbox-id-xyz")


class TestAsyncSandboxClientDelete:
    """Tests for deleting sandboxes asynchronously"""

    @pytest.mark.skip_debug()
    async def test_delete_sandbox(self, async_sandbox_client, template, sandbox_test_id):
        """Test deleting a sandbox asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-delete-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = await async_sandbox_client.create(request)
        result = await async_sandbox_client.delete(sandbox.id)

        assert result["success"] is True

    @pytest.mark.skip_debug()
    async def test_delete_nonexistent_sandbox(self, async_sandbox_client):
        """Test deleting a nonexistent sandbox asynchronously"""
        result = await async_sandbox_client.delete("nonexistent-async-sandbox-id-xyz")
        # Should not raise an error, just return success info
        assert "success" in result

    @pytest.mark.skip_debug()
    async def test_bulk_delete_by_ids(self, async_sandbox_client, template, sandbox_test_id):
        """Test bulk deleting sandboxes by IDs asynchronously"""
        # Create multiple sandboxes
        request1 = CreateSandboxRequest(
            name=f"test-async-bulk-1-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )
        request2 = CreateSandboxRequest(
            name=f"test-async-bulk-2-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox1 = None
        sandbox2 = None
        try:
            sandbox1 = await async_sandbox_client.create(request1)
            sandbox2 = await async_sandbox_client.create(request2)

            response = await async_sandbox_client.bulk_delete(
                sandbox_ids=[sandbox1.id, sandbox2.id]
            )

            assert len(response.succeeded) >= 1  # At least one should succeed
            assert "Deleted" in response.message
        finally:
            # Clean up any remaining sandboxes
            try:
                if sandbox1:
                    await async_sandbox_client.delete(sandbox1.id)
            except:
                pass
            try:
                if sandbox2:
                    await async_sandbox_client.delete(sandbox2.id)
            except:
                pass

    @pytest.mark.skip_debug()
    async def test_bulk_delete_by_labels(self, async_sandbox_client, template, sandbox_test_id):
        """Test bulk deleting sandboxes by labels asynchronously"""
        unique_label = f"async-bulk-delete-{sandbox_test_id[:8]}"

        request1 = CreateSandboxRequest(
            name=f"test-async-bulk-label-1-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=[unique_label],
        )
        request2 = CreateSandboxRequest(
            name=f"test-async-bulk-label-2-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=[unique_label],
        )

        sandbox1 = None
        sandbox2 = None
        try:
            sandbox1 = await async_sandbox_client.create(request1)
            sandbox2 = await async_sandbox_client.create(request2)

            response = await async_sandbox_client.bulk_delete(labels=[unique_label])

            assert len(response.succeeded) >= 1
            assert "Deleted" in response.message
        finally:
            # Clean up any remaining sandboxes
            try:
                if sandbox1:
                    await async_sandbox_client.delete(sandbox1.id)
            except:
                pass
            try:
                if sandbox2:
                    await async_sandbox_client.delete(sandbox2.id)
            except:
                pass

    @pytest.mark.skip_debug()
    async def test_bulk_delete_invalid_params(self, async_sandbox_client):
        """Test bulk delete with invalid parameters asynchronously"""
        # Both sandbox_ids and labels specified
        with pytest.raises(APIError):
            await async_sandbox_client.bulk_delete(
                sandbox_ids=["id1"], labels=["label1"]
            )

        # Neither sandbox_ids nor labels specified
        with pytest.raises(APIError):
            await async_sandbox_client.bulk_delete()


class TestAsyncSandboxClientCommands:
    """Tests for executing commands asynchronously"""

    @pytest.mark.skip_debug()
    async def test_execute_command_basic(self, async_sandbox_client, template, sandbox_test_id):
        """Test executing a basic command asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-cmd-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            response = await async_sandbox_client.execute_command(
                sandbox.id, "echo 'Hello Async World'", timeout=10
            )

            assert response.exit_code == 0
            assert "Hello Async World" in response.stdout
            assert response.stderr == ""
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_execute_command_with_env(self, async_sandbox_client, template, sandbox_test_id):
        """Test executing a command with environment variables asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-cmd-env-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            response = await async_sandbox_client.execute_command(
                sandbox.id,
                "echo $ASYNC_TEST_VAR",
                env={"ASYNC_TEST_VAR": "async_value"},
                timeout=10,
            )

            assert response.exit_code == 0
            assert "async_value" in response.stdout
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_execute_command_with_working_dir(self, async_sandbox_client, template, sandbox_test_id):
        """Test executing a command with a working directory asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-cmd-cwd-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Create a directory first
            await async_sandbox_client.execute_command(
                sandbox.id, "mkdir -p /tmp/async_testdir", timeout=10
            )

            # Execute command in that directory
            response = await async_sandbox_client.execute_command(
                sandbox.id, "pwd", working_dir="/tmp/async_testdir", timeout=10
            )

            assert response.exit_code == 0
            assert "/tmp/async_testdir" in response.stdout
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_execute_command_timeout(self, async_sandbox_client, template, sandbox_test_id):
        """Test command timeout asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-cmd-timeout-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            with pytest.raises(CommandTimeoutError):
                await async_sandbox_client.execute_command(
                    sandbox.id, "sleep 100", timeout=2
                )
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_execute_command_nonexistent_sandbox(self, async_sandbox_client):
        """Test executing command on nonexistent sandbox asynchronously"""
        with pytest.raises(SandboxNotRunningError):
            await async_sandbox_client.execute_command(
                "nonexistent-async-sandbox-id", "echo test", timeout=10
            )


class TestAsyncSandboxClientFiles:
    """Tests for file operations asynchronously"""

    @pytest.mark.skip_debug()
    async def test_upload_file(self, async_sandbox_client, template, sandbox_test_id):
        """Test uploading a file to sandbox asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-upload-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        temp_file = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                temp_file = f.name
                f.write("Async test content for upload\n")

            # Upload the file
            response = await async_sandbox_client.upload_file(
                sandbox.id, "/tmp/async_uploaded.txt", temp_file
            )

            assert response.success is True
            assert response.path == "/tmp/async_uploaded.txt"
            assert response.size > 0
            assert isinstance(response.timestamp, datetime)

            # Verify file was uploaded
            cmd_response = await async_sandbox_client.execute_command(
                sandbox.id, "cat /tmp/async_uploaded.txt", timeout=10
            )
            assert "Async test content for upload" in cmd_response.stdout
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_upload_nonexistent_file(self, async_sandbox_client, template, sandbox_test_id):
        """Test uploading a file that doesn't exist asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-upload-missing-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            with pytest.raises(FileNotFoundError):
                await async_sandbox_client.upload_file(
                    sandbox.id, "/tmp/test.txt", "/nonexistent/async_file.txt"
                )
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_download_file(self, async_sandbox_client, template, sandbox_test_id):
        """Test downloading a file from sandbox asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-download-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        temp_file = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Create a file in the sandbox
            await async_sandbox_client.execute_command(
                sandbox.id,
                "echo 'Async test content for download' > /tmp/async_download.txt",
                timeout=10,
            )

            # Download the file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name

            await async_sandbox_client.download_file(
                sandbox.id, "/tmp/async_download.txt", temp_file
            )

            # Verify the downloaded content
            with open(temp_file, "r") as f:
                content = f.read()
            assert "Async test content for download" in content
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_download_nonexistent_file(self, async_sandbox_client, template, sandbox_test_id):
        """Test downloading a file that doesn't exist in sandbox asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-download-missing-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        temp_file = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name

            with pytest.raises(APIError):
                await async_sandbox_client.download_file(
                    sandbox.id, "/nonexistent/async_file.txt", temp_file
                )
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)


class TestAsyncSandboxClientWait:
    """Tests for waiting operations asynchronously"""

    @pytest.mark.skip_debug()
    async def test_wait_for_creation(self, async_sandbox_client, template, sandbox_test_id):
        """Test waiting for sandbox to be ready asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-wait-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)

            # Wait should not raise an exception
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Sandbox should be running
            retrieved = await async_sandbox_client.get(sandbox.id)
            assert retrieved.status == SandboxStatus.RUNNING
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_bulk_wait_for_creation(self, async_sandbox_client, template, sandbox_test_id):
        """Test waiting for multiple sandboxes asynchronously"""
        request1 = CreateSandboxRequest(
            name=f"test-async-bulk-wait-1-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )
        request2 = CreateSandboxRequest(
            name=f"test-async-bulk-wait-2-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox1 = None
        sandbox2 = None
        try:
            sandbox1 = await async_sandbox_client.create(request1)
            sandbox2 = await async_sandbox_client.create(request2)

            statuses = await async_sandbox_client.bulk_wait_for_creation(
                [sandbox1.id, sandbox2.id], max_attempts=30
            )

            assert len(statuses) == 2
            assert statuses[sandbox1.id] == "RUNNING"
            assert statuses[sandbox2.id] == "RUNNING"
        finally:
            if sandbox1:
                await async_sandbox_client.delete(sandbox1.id)
            if sandbox2:
                await async_sandbox_client.delete(sandbox2.id)


class TestAsyncSandboxClientOther:
    """Tests for other operations asynchronously"""

    @pytest.mark.skip_debug()
    async def test_get_logs(self, async_sandbox_client, template, sandbox_test_id):
        """Test getting sandbox logs asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-logs-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)

            logs = await async_sandbox_client.get_logs(sandbox.id)

            # PPIO doesn't support direct logs, so we expect a message
            assert isinstance(logs, str)
            assert "not directly available" in logs or "not available" in logs.lower()
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    def test_clear_auth_cache(self, async_sandbox_client):
        """Test clearing auth cache (no-op) asynchronously"""
        # Should not raise an exception
        async_sandbox_client.clear_auth_cache()

    @pytest.mark.skip_debug()
    async def test_is_sandbox_reachable(self, async_sandbox_client, template, sandbox_test_id):
        """Test checking if sandbox is reachable asynchronously"""
        request = CreateSandboxRequest(
            name=f"test-async-reachable-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = await async_sandbox_client.create(request)
            await async_sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Should be reachable after waiting
            is_reachable = await async_sandbox_client._is_sandbox_reachable(
                sandbox.id, timeout=10
            )
            assert is_reachable is True
        finally:
            if sandbox:
                await async_sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    async def test_context_manager(self, template, sandbox_test_id):
        """Test AsyncSandboxClient context manager"""
        api_key = os.getenv("PPIO_API_KEY", "test-key")

        async with AsyncSandboxClient(api_key=api_key) as client:
            request = CreateSandboxRequest(
                name=f"test-async-context-{sandbox_test_id[:8]}",
                docker_image=template,
                timeout_minutes=10,
            )

            sandbox = None
            try:
                sandbox = await client.create(request)
                assert sandbox is not None
                assert sandbox.id is not None
            finally:
                if sandbox:
                    await client.delete(sandbox.id)

        # Client should be properly closed after exiting context

