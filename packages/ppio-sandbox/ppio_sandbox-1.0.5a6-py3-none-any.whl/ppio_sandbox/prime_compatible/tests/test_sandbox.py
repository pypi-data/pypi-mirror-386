"""Tests for SandboxClient (synchronous)"""

import os
import tempfile
import time
from datetime import datetime

import pytest

from ppio_sandbox.prime_compatible.sandbox import SandboxClient
from ppio_sandbox.prime_compatible.models import (
    CreateSandboxRequest,
    SandboxStatus,
)
from ppio_sandbox.prime_compatible.exceptions import (
    CommandTimeoutError,
    SandboxNotRunningError,
)
from ppio_sandbox.prime_compatible.prime_core import APIError


class TestSandboxClientCreate:
    """Tests for sandbox creation"""

    @pytest.mark.skip_debug()
    def test_create_sandbox_basic(self, sandbox_client, template, sandbox_test_id):
        """Test creating a basic sandbox"""
        request = CreateSandboxRequest(
            name=f"test-create-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)

            assert sandbox is not None
            assert sandbox.id is not None
            assert sandbox.name == request.name
            assert sandbox.docker_image == template
            assert sandbox.timeout_minutes == 10
            assert sandbox.status in [SandboxStatus.RUNNING, SandboxStatus.PROVISIONING]
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_create_sandbox_with_metadata(self, sandbox_client: SandboxClient, template, sandbox_test_id):
        """Test creating a sandbox with metadata (labels, env vars)"""
        request = CreateSandboxRequest(
            name=f"test-metadata-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=["test", "metadata"],
            environment_vars={"TEST_VAR": "test_value"},
            team_id="test-team",
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)

            assert sandbox is not None
            assert "test" in sandbox.labels
            assert "metadata" in sandbox.labels
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_create_sandbox_invalid_template(self, sandbox_client: SandboxClient, sandbox_test_id: str):
        """Test creating a sandbox with invalid template"""
        request = CreateSandboxRequest(
            name=f"test-invalid-{sandbox_test_id[:8]}",
            docker_image="nonexistent-template-xyz",
            timeout_minutes=10,
        )

        with pytest.raises(APIError):
            sandbox_client.create(request)


class TestSandboxClientList:
    """Tests for listing sandboxes"""

    @pytest.mark.skip_debug()
    def test_list_sandboxes_basic(self, sandbox_client):
        """Test listing sandboxes"""
        response = sandbox_client.list(page=1, per_page=10)

        assert response is not None
        assert isinstance(response.sandboxes, list)
        assert response.page == 1
        assert response.per_page == 10
        assert isinstance(response.has_next, bool)

    @pytest.mark.skip_debug()
    def test_list_sandboxes_with_status_filter(self, sandbox_client, template, sandbox_test_id):
        """Test listing sandboxes filtered by status"""
        request = CreateSandboxRequest(
            name=f"test-list-status-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            response = sandbox_client.list(status=SandboxStatus.RUNNING, per_page=50)

            # Check if our sandbox appears in the list
            sandbox_ids = [s.id for s in response.sandboxes]
            assert sandbox.id in sandbox_ids or not response.has_next
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_list_sandboxes_with_labels(self, sandbox_client, template, sandbox_test_id):
        """Test listing sandboxes filtered by labels"""
        unique_label = f"test-label-{sandbox_test_id[:8]}"
        request = CreateSandboxRequest(
            name=f"test-list-labels-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=[unique_label, "test"],
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)

            response = sandbox_client.list(labels=[unique_label], per_page=50)

            # Our sandbox should appear in the list
            sandbox_ids = [s.id for s in response.sandboxes]
            assert sandbox.id in sandbox_ids
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_list_sandboxes_pagination(self, sandbox_client):
        """Test pagination when listing sandboxes"""
        # Test first page
        response_page1 = sandbox_client.list(page=1, per_page=5)
        assert response_page1.page == 1

        # Test page beyond available items
        response_empty = sandbox_client.list(page=1000, per_page=5)
        assert response_empty.page == 1000
        assert len(response_empty.sandboxes) == 0


class TestSandboxClientGet:
    """Tests for getting sandbox info"""

    @pytest.mark.skip_debug()
    def test_get_sandbox(self, sandbox_client: SandboxClient, template: str, sandbox_test_id: str):
        """Test getting a specific sandbox"""
        request = CreateSandboxRequest(
            name=f"test-get-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)

            retrieved = sandbox_client.get(sandbox.id)
            
            print(sandbox)
            print(retrieved)

            assert retrieved.id == sandbox.id
            assert retrieved.name == sandbox.name
            assert retrieved.docker_image == template
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_get_nonexistent_sandbox(self, sandbox_client: SandboxClient):
        """Test getting a nonexistent sandbox"""
        with pytest.raises(APIError):
            sandbox_client.get("nonexistent-sandbox-id-xyz")


class TestSandboxClientDelete:
    """Tests for deleting sandboxes"""

    @pytest.mark.skip_debug()
    def test_delete_sandbox(self, sandbox_client, template, sandbox_test_id):
        """Test deleting a sandbox"""
        request = CreateSandboxRequest(
            name=f"test-delete-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = sandbox_client.create(request)
        result = sandbox_client.delete(sandbox.id)

        assert result["success"] is True

    @pytest.mark.skip_debug()
    def test_delete_nonexistent_sandbox(self, sandbox_client):
        """Test deleting a nonexistent sandbox"""
        result = sandbox_client.delete("nonexistent-sandbox-id-xyz")
        # Should not raise an error, just return success=False
        assert "success" in result

    @pytest.mark.skip_debug()
    def test_bulk_delete_by_ids(self, sandbox_client, template, sandbox_test_id):
        """Test bulk deleting sandboxes by IDs"""
        # Create multiple sandboxes
        request1 = CreateSandboxRequest(
            name=f"test-bulk-1-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )
        request2 = CreateSandboxRequest(
            name=f"test-bulk-2-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox1 = None
        sandbox2 = None
        try:
            sandbox1 = sandbox_client.create(request1)
            sandbox2 = sandbox_client.create(request2)

            response = sandbox_client.bulk_delete(
                sandbox_ids=[sandbox1.id, sandbox2.id]
            )

            assert len(response.succeeded) >= 1  # At least one should succeed
            assert "Deleted" in response.message
        finally:
            # Clean up any remaining sandboxes
            try:
                if sandbox1:
                    sandbox_client.delete(sandbox1.id)
            except:
                pass
            try:
                if sandbox2:
                    sandbox_client.delete(sandbox2.id)
            except:
                pass

    @pytest.mark.skip_debug()
    def test_bulk_delete_by_labels(self, sandbox_client, template, sandbox_test_id):
        """Test bulk deleting sandboxes by labels"""
        unique_label = f"bulk-delete-{sandbox_test_id[:8]}"

        request1 = CreateSandboxRequest(
            name=f"test-bulk-label-1-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=[unique_label],
        )
        request2 = CreateSandboxRequest(
            name=f"test-bulk-label-2-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
            labels=[unique_label],
        )

        sandbox1 = None
        sandbox2 = None
        try:
            sandbox1 = sandbox_client.create(request1)
            sandbox2 = sandbox_client.create(request2)

            response = sandbox_client.bulk_delete(labels=[unique_label])

            assert len(response.succeeded) >= 1
            assert "Deleted" in response.message
        finally:
            # Clean up any remaining sandboxes
            try:
                if sandbox1:
                    sandbox_client.delete(sandbox1.id)
            except:
                pass
            try:
                if sandbox2:
                    sandbox_client.delete(sandbox2.id)
            except:
                pass

    @pytest.mark.skip_debug()
    def test_bulk_delete_invalid_params(self, sandbox_client):
        """Test bulk delete with invalid parameters"""
        # Both sandbox_ids and labels specified
        with pytest.raises(APIError):
            sandbox_client.bulk_delete(
                sandbox_ids=["id1"], labels=["label1"]
            )

        # Neither sandbox_ids nor labels specified
        with pytest.raises(APIError):
            sandbox_client.bulk_delete()


class TestSandboxClientCommands:
    """Tests for executing commands"""

    @pytest.mark.skip_debug()
    def test_execute_command_basic(self, sandbox_client, template, sandbox_test_id):
        """Test executing a basic command"""
        request = CreateSandboxRequest(
            name=f"test-cmd-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            response = sandbox_client.execute_command(
                sandbox.id, "echo 'Hello World'", timeout=10
            )

            assert response.exit_code == 0
            assert "Hello World" in response.stdout
            assert response.stderr == ""
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_execute_command_with_env(self, sandbox_client, template, sandbox_test_id):
        """Test executing a command with environment variables"""
        request = CreateSandboxRequest(
            name=f"test-cmd-env-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            response = sandbox_client.execute_command(
                sandbox.id,
                "echo $TEST_VAR",
                env={"TEST_VAR": "test_value"},
                timeout=10,
            )

            assert response.exit_code == 0
            assert "test_value" in response.stdout
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_execute_command_with_working_dir(self, sandbox_client, template, sandbox_test_id):
        """Test executing a command with a working directory"""
        request = CreateSandboxRequest(
            name=f"test-cmd-cwd-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Create a directory first
            sandbox_client.execute_command(sandbox.id, "mkdir -p /tmp/testdir", timeout=10)

            # Execute command in that directory
            response = sandbox_client.execute_command(
                sandbox.id, "pwd", working_dir="/tmp/testdir", timeout=10
            )

            assert response.exit_code == 0
            assert "/tmp/testdir" in response.stdout
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_execute_command_timeout(self, sandbox_client, template, sandbox_test_id):
        """Test command timeout"""
        request = CreateSandboxRequest(
            name=f"test-cmd-timeout-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            with pytest.raises(CommandTimeoutError):
                sandbox_client.execute_command(
                    sandbox.id, "sleep 100", timeout=2
                )
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_execute_command_nonexistent_sandbox(self, sandbox_client):
        """Test executing command on nonexistent sandbox"""
        with pytest.raises(SandboxNotRunningError):
            sandbox_client.execute_command(
                "nonexistent-sandbox-id", "echo test", timeout=10
            )


class TestSandboxClientFiles:
    """Tests for file operations"""

    @pytest.mark.skip_debug()
    def test_upload_file(self, sandbox_client, template, sandbox_test_id):
        """Test uploading a file to sandbox"""
        request = CreateSandboxRequest(
            name=f"test-upload-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        temp_file = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                temp_file = f.name
                f.write("Test content for upload\n")

            # Upload the file
            response = sandbox_client.upload_file(
                sandbox.id, "/tmp/uploaded.txt", temp_file
            )

            assert response.success is True
            assert response.path == "/tmp/uploaded.txt"
            assert response.size > 0
            assert isinstance(response.timestamp, datetime)

            # Verify file was uploaded
            cmd_response = sandbox_client.execute_command(
                sandbox.id, "cat /tmp/uploaded.txt", timeout=10
            )
            assert "Test content for upload" in cmd_response.stdout
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_upload_nonexistent_file(self, sandbox_client, template, sandbox_test_id):
        """Test uploading a file that doesn't exist"""
        request = CreateSandboxRequest(
            name=f"test-upload-missing-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            with pytest.raises(FileNotFoundError):
                sandbox_client.upload_file(
                    sandbox.id, "/tmp/test.txt", "/nonexistent/file.txt"
                )
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_download_file(self, sandbox_client, template, sandbox_test_id):
        """Test downloading a file from sandbox"""
        request = CreateSandboxRequest(
            name=f"test-download-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        temp_file = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Create a file in the sandbox
            sandbox_client.execute_command(
                sandbox.id,
                "echo 'Test content for download' > /tmp/download.txt",
                timeout=10,
            )

            # Download the file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name

            sandbox_client.download_file(sandbox.id, "/tmp/download.txt", temp_file)

            # Verify the downloaded content
            with open(temp_file, "r") as f:
                content = f.read()
            assert "Test content for download" in content
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_download_nonexistent_file(self, sandbox_client, template, sandbox_test_id):
        """Test downloading a file that doesn't exist in sandbox"""
        request = CreateSandboxRequest(
            name=f"test-download-missing-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        temp_file = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name

            with pytest.raises(APIError):
                sandbox_client.download_file(
                    sandbox.id, "/nonexistent/file.txt", temp_file
                )
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            if sandbox:
                sandbox_client.delete(sandbox.id)


class TestSandboxClientWait:
    """Tests for waiting operations"""

    @pytest.mark.skip_debug()
    def test_wait_for_creation(self, sandbox_client, template, sandbox_test_id):
        """Test waiting for sandbox to be ready"""
        request = CreateSandboxRequest(
            name=f"test-wait-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)

            # Wait should not raise an exception
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Sandbox should be running
            retrieved = sandbox_client.get(sandbox.id)
            assert retrieved.status == SandboxStatus.RUNNING
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    @pytest.mark.skip_debug()
    def test_bulk_wait_for_creation(self, sandbox_client, template, sandbox_test_id):
        """Test waiting for multiple sandboxes"""
        request1 = CreateSandboxRequest(
            name=f"test-bulk-wait-1-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )
        request2 = CreateSandboxRequest(
            name=f"test-bulk-wait-2-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox1 = None
        sandbox2 = None
        try:
            sandbox1 = sandbox_client.create(request1)
            sandbox2 = sandbox_client.create(request2)

            statuses = sandbox_client.bulk_wait_for_creation(
                [sandbox1.id, sandbox2.id], max_attempts=30
            )

            assert len(statuses) == 2
            assert statuses[sandbox1.id] == "RUNNING"
            assert statuses[sandbox2.id] == "RUNNING"
        finally:
            if sandbox1:
                sandbox_client.delete(sandbox1.id)
            if sandbox2:
                sandbox_client.delete(sandbox2.id)


class TestSandboxClientOther:
    """Tests for other operations"""

    @pytest.mark.skip_debug()
    def test_get_logs(self, sandbox_client, template, sandbox_test_id):
        """Test getting sandbox logs"""
        request = CreateSandboxRequest(
            name=f"test-logs-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)

            logs = sandbox_client.get_logs(sandbox.id)

            # PPIO doesn't support direct logs, so we expect a message
            assert isinstance(logs, str)
            assert "not directly available" in logs or "not available" in logs.lower()
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

    def test_clear_auth_cache(self, sandbox_client):
        """Test clearing auth cache (no-op)"""
        # Should not raise an exception
        sandbox_client.clear_auth_cache()

    @pytest.mark.skip_debug()
    def test_is_sandbox_reachable(self, sandbox_client, template, sandbox_test_id):
        """Test checking if sandbox is reachable"""
        request = CreateSandboxRequest(
            name=f"test-reachable-{sandbox_test_id[:8]}",
            docker_image=template,
            timeout_minutes=10,
        )

        sandbox = None
        try:
            sandbox = sandbox_client.create(request)
            sandbox_client.wait_for_creation(sandbox.id, max_attempts=30)

            # Should be reachable after waiting
            is_reachable = sandbox_client._is_sandbox_reachable(sandbox.id, timeout=10)
            assert is_reachable is True
        finally:
            if sandbox:
                sandbox_client.delete(sandbox.id)

