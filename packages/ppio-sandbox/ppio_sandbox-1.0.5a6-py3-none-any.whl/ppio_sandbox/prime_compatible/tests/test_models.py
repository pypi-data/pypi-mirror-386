"""Tests for Pydantic models"""

from datetime import datetime, timezone

import pytest

from ppio_sandbox.prime_compatible.models import (
    AdvancedConfigs,
    BulkDeleteSandboxRequest,
    BulkDeleteSandboxResponse,
    CommandRequest,
    CommandResponse,
    CreateSandboxRequest,
    FileUploadResponse,
    Sandbox,
    SandboxListResponse,
    SandboxLogsResponse,
    SandboxStatus,
    UpdateSandboxRequest,
)


class TestSandboxStatus:
    """Tests for SandboxStatus enum"""

    def test_status_values(self):
        """Test all SandboxStatus enum values"""
        assert SandboxStatus.PENDING == "PENDING"
        assert SandboxStatus.PROVISIONING == "PROVISIONING"
        assert SandboxStatus.RUNNING == "RUNNING"
        assert SandboxStatus.STOPPED == "STOPPED"
        assert SandboxStatus.ERROR == "ERROR"
        assert SandboxStatus.TERMINATED == "TERMINATED"
        assert SandboxStatus.TIMEOUT == "TIMEOUT"

    def test_status_string_enum(self):
        """Test SandboxStatus is a string enum"""
        assert isinstance(SandboxStatus.RUNNING, str)
        assert SandboxStatus.RUNNING.value == "RUNNING"


class TestAdvancedConfigs:
    """Tests for AdvancedConfigs model"""

    def test_empty_config(self):
        """Test creating empty AdvancedConfigs"""
        config = AdvancedConfigs()
        assert config is not None

    def test_config_with_extra_fields(self):
        """Test AdvancedConfigs allows extra fields"""
        config = AdvancedConfigs(custom_field="custom_value", another_field=123)
        assert config.model_extra["custom_field"] == "custom_value"
        assert config.model_extra["another_field"] == 123


class TestSandbox:
    """Tests for Sandbox model"""

    def test_sandbox_with_camel_case_aliases(self):
        """Test Sandbox model handles API field aliases (camelCase)"""
        data = {
            "id": "test-123",
            "name": "test-sandbox",
            "dockerImage": "code-interpreter-v1",
            "cpuCores": 2,
            "memoryGB": 4,
            "diskSizeGB": 10,
            "diskMountPath": "/workspace",
            "gpuCount": 0,
            "status": "RUNNING",
            "timeoutMinutes": 120,
            "labels": ["test", "production"],
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T01:00:00Z",
        }

        sandbox = Sandbox.model_validate(data)

        assert sandbox.id == "test-123"
        assert sandbox.name == "test-sandbox"
        assert sandbox.docker_image == "code-interpreter-v1"
        assert sandbox.cpu_cores == 2
        assert sandbox.memory_gb == 4
        assert sandbox.disk_size_gb == 10
        assert sandbox.disk_mount_path == "/workspace"
        assert sandbox.gpu_count == 0
        assert sandbox.status == "RUNNING"
        assert sandbox.timeout_minutes == 120
        assert sandbox.labels == ["test", "production"]

    def test_sandbox_with_snake_case_fields(self):
        """Test Sandbox model with snake_case field names"""
        data = {
            "id": "test-456",
            "name": "test-sandbox-2",
            "docker_image": "base",
            "cpu_cores": 4,
            "memory_gb": 8,
            "disk_size_gb": 20,
            "disk_mount_path": "/data",
            "gpu_count": 1,
            "status": "PENDING",
            "timeout_minutes": 60,
            "labels": [],
            "created_at": "2024-01-02T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
        }

        sandbox = Sandbox.model_validate(data)

        assert sandbox.id == "test-456"
        assert sandbox.name == "test-sandbox-2"
        assert sandbox.docker_image == "base"
        assert sandbox.cpu_cores == 4
        assert sandbox.memory_gb == 8

    def test_sandbox_with_optional_fields(self):
        """Test Sandbox model with optional fields"""
        data = {
            "id": "test-789",
            "name": "test-sandbox-3",
            "dockerImage": "python:3.11",
            "startCommand": "python main.py",
            "cpuCores": 1,
            "memoryGB": 2,
            "diskSizeGB": 5,
            "diskMountPath": "/workspace",
            "gpuCount": 0,
            "status": "RUNNING",
            "timeoutMinutes": 30,
            "environmentVars": {"KEY1": "value1", "KEY2": "value2"},
            "labels": ["test"],
            "createdAt": "2024-01-03T00:00:00Z",
            "updatedAt": "2024-01-03T00:00:00Z",
            "startedAt": "2024-01-03T00:01:00Z",
            "terminatedAt": "2024-01-03T00:30:00Z",
            "exitCode": 0,
            "userId": "user-123",
            "teamId": "team-456",
            "kubernetesJobId": "job-789",
        }

        sandbox = Sandbox.model_validate(data)

        assert sandbox.start_command == "python main.py"
        assert sandbox.environment_vars == {"KEY1": "value1", "KEY2": "value2"}
        assert sandbox.started_at is not None
        assert sandbox.terminated_at is not None
        assert sandbox.exit_code == 0
        assert sandbox.user_id == "user-123"
        assert sandbox.team_id == "team-456"
        assert sandbox.kubernetes_job_id == "job-789"

    def test_sandbox_with_advanced_configs(self):
        """Test Sandbox model with advanced configs"""
        data = {
            "id": "test-adv",
            "name": "test-advanced",
            "dockerImage": "base",
            "cpuCores": 2,
            "memoryGB": 4,
            "diskSizeGB": 10,
            "diskMountPath": "/workspace",
            "gpuCount": 0,
            "status": "RUNNING",
            "timeoutMinutes": 60,
            "advancedConfigs": {"customSetting": "value"},
            "labels": [],
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }

        sandbox = Sandbox.model_validate(data)

        assert sandbox.advanced_configs is not None
        assert sandbox.advanced_configs.model_extra["customSetting"] == "value"


class TestSandboxListResponse:
    """Tests for SandboxListResponse model"""

    def test_list_response_basic(self):
        """Test basic SandboxListResponse"""
        data = {
            "sandboxes": [],
            "total": 0,
            "page": 1,
            "perPage": 10,
            "hasNext": False,
        }

        response = SandboxListResponse.model_validate(data)

        assert response.sandboxes == []
        assert response.total == 0
        assert response.page == 1
        assert response.per_page == 10
        assert response.has_next is False

    def test_list_response_with_sandboxes(self):
        """Test SandboxListResponse with sandboxes"""
        data = {
            "sandboxes": [
                {
                    "id": "sbx-1",
                    "name": "sandbox-1",
                    "dockerImage": "base",
                    "cpuCores": 1,
                    "memoryGB": 2,
                    "diskSizeGB": 5,
                    "diskMountPath": "/workspace",
                    "gpuCount": 0,
                    "status": "RUNNING",
                    "timeoutMinutes": 60,
                    "labels": [],
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z",
                },
            ],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "has_next": False,
        }

        response = SandboxListResponse.model_validate(data)

        assert len(response.sandboxes) == 1
        assert response.sandboxes[0].id == "sbx-1"
        assert response.total == 1
        assert response.has_next is False


class TestCreateSandboxRequest:
    """Tests for CreateSandboxRequest model"""

    def test_create_request_minimal(self):
        """Test CreateSandboxRequest with minimal fields"""
        request = CreateSandboxRequest(
            name="test-sandbox",
            docker_image="base",
        )

        assert request.name == "test-sandbox"
        assert request.docker_image == "base"
        assert request.timeout_minutes == 60  # Default value
        assert request.labels == []  # Default value
        assert request.environment_vars is None
        assert request.team_id is None
        assert request.advanced_configs is None

    def test_create_request_with_all_fields(self):
        """Test CreateSandboxRequest with all fields"""
        request = CreateSandboxRequest(
            name="test-sandbox-full",
            docker_image="code-interpreter-v1",
            timeout_minutes=120,
            environment_vars={"VAR1": "value1", "VAR2": "value2"},
            labels=["test", "production"],
            team_id="team-123",
            advanced_configs=AdvancedConfigs(),
        )

        assert request.name == "test-sandbox-full"
        assert request.docker_image == "code-interpreter-v1"
        assert request.timeout_minutes == 120
        assert request.environment_vars == {"VAR1": "value1", "VAR2": "value2"}
        assert request.labels == ["test", "production"]
        assert request.team_id == "team-123"
        assert request.advanced_configs is not None

    def test_create_request_default_timeout(self):
        """Test CreateSandboxRequest default timeout value"""
        request = CreateSandboxRequest(
            name="test",
            docker_image="base",
        )

        assert request.timeout_minutes == 60


class TestUpdateSandboxRequest:
    """Tests for UpdateSandboxRequest model"""

    def test_update_request_timeout_only(self):
        """Test UpdateSandboxRequest with timeout only"""
        request = UpdateSandboxRequest(timeout_minutes=120)

        assert request.timeout_minutes == 120
        assert request.environment_vars is None

    def test_update_request_env_vars_only(self):
        """Test UpdateSandboxRequest with environment variables only"""
        request = UpdateSandboxRequest(
            environment_vars={"NEW_VAR": "new_value"}
        )

        assert request.timeout_minutes is None
        assert request.environment_vars == {"NEW_VAR": "new_value"}

    def test_update_request_all_fields(self):
        """Test UpdateSandboxRequest with all fields"""
        request = UpdateSandboxRequest(
            timeout_minutes=180,
            environment_vars={"VAR": "value"},
        )

        assert request.timeout_minutes == 180
        assert request.environment_vars == {"VAR": "value"}


class TestCommandRequest:
    """Tests for CommandRequest model"""

    def test_command_request_minimal(self):
        """Test CommandRequest with command only"""
        request = CommandRequest(command="echo hello")

        assert request.command == "echo hello"
        assert request.working_dir is None
        assert request.env is None

    def test_command_request_with_working_dir(self):
        """Test CommandRequest with working directory"""
        request = CommandRequest(
            command="ls -la",
            working_dir="/tmp",
        )

        assert request.command == "ls -la"
        assert request.working_dir == "/tmp"

    def test_command_request_with_env(self):
        """Test CommandRequest with environment variables"""
        request = CommandRequest(
            command="echo $VAR",
            env={"VAR": "value"},
        )

        assert request.command == "echo $VAR"
        assert request.env == {"VAR": "value"}

    def test_command_request_full(self):
        """Test CommandRequest with all fields"""
        request = CommandRequest(
            command="python script.py",
            working_dir="/workspace",
            env={"PYTHONPATH": "/app"},
        )

        assert request.command == "python script.py"
        assert request.working_dir == "/workspace"
        assert request.env == {"PYTHONPATH": "/app"}


class TestCommandResponse:
    """Tests for CommandResponse model"""

    def test_command_response_success(self):
        """Test CommandResponse for successful command"""
        response = CommandResponse(
            stdout="Hello World\n",
            stderr="",
            exit_code=0,
        )

        assert response.stdout == "Hello World\n"
        assert response.stderr == ""
        assert response.exit_code == 0

    def test_command_response_with_error(self):
        """Test CommandResponse with error output"""
        response = CommandResponse(
            stdout="",
            stderr="Error: file not found\n",
            exit_code=1,
        )

        assert response.stdout == ""
        assert response.stderr == "Error: file not found\n"
        assert response.exit_code == 1

    def test_command_response_both_outputs(self):
        """Test CommandResponse with both stdout and stderr"""
        response = CommandResponse(
            stdout="Output line 1\nOutput line 2\n",
            stderr="Warning: deprecated\n",
            exit_code=0,
        )

        assert "Output line 1" in response.stdout
        assert "Warning: deprecated" in response.stderr
        assert response.exit_code == 0


class TestFileUploadResponse:
    """Tests for FileUploadResponse model"""

    def test_file_upload_response_success(self):
        """Test successful file upload response"""
        timestamp = datetime.now(timezone.utc)
        response = FileUploadResponse(
            success=True,
            path="/tmp/uploaded.txt",
            size=1024,
            timestamp=timestamp,
        )

        assert response.success is True
        assert response.path == "/tmp/uploaded.txt"
        assert response.size == 1024
        assert response.timestamp == timestamp

    def test_file_upload_response_failure(self):
        """Test failed file upload response"""
        timestamp = datetime.now(timezone.utc)
        response = FileUploadResponse(
            success=False,
            path="/tmp/failed.txt",
            size=0,
            timestamp=timestamp,
        )

        assert response.success is False
        assert response.size == 0


class TestSandboxLogsResponse:
    """Tests for SandboxLogsResponse model"""

    def test_logs_response_empty(self):
        """Test empty logs response"""
        response = SandboxLogsResponse(logs="")

        assert response.logs == ""

    def test_logs_response_with_content(self):
        """Test logs response with content"""
        logs_content = "Log line 1\nLog line 2\nLog line 3\n"
        response = SandboxLogsResponse(logs=logs_content)

        assert response.logs == logs_content
        assert "Log line 1" in response.logs


class TestBulkDeleteSandboxRequest:
    """Tests for BulkDeleteSandboxRequest model"""

    def test_bulk_delete_request_by_ids(self):
        """Test bulk delete request with sandbox IDs"""
        request = BulkDeleteSandboxRequest(
            sandbox_ids=["sbx-1", "sbx-2", "sbx-3"]
        )

        assert request.sandbox_ids == ["sbx-1", "sbx-2", "sbx-3"]
        assert request.labels is None

    def test_bulk_delete_request_by_labels(self):
        """Test bulk delete request with labels"""
        request = BulkDeleteSandboxRequest(labels=["test", "staging"])

        assert request.sandbox_ids is None
        assert request.labels == ["test", "staging"]

    def test_bulk_delete_request_empty(self):
        """Test bulk delete request with no fields"""
        request = BulkDeleteSandboxRequest()

        assert request.sandbox_ids is None
        assert request.labels is None


class TestBulkDeleteSandboxResponse:
    """Tests for BulkDeleteSandboxResponse model"""

    def test_bulk_delete_response_all_success(self):
        """Test bulk delete response with all successful"""
        response = BulkDeleteSandboxResponse(
            succeeded=["sbx-1", "sbx-2", "sbx-3"],
            failed=[],
            message="Deleted 3/3 sandboxes",
        )

        assert len(response.succeeded) == 3
        assert len(response.failed) == 0
        assert "3/3" in response.message

    def test_bulk_delete_response_partial_success(self):
        """Test bulk delete response with partial success"""
        response = BulkDeleteSandboxResponse(
            succeeded=["sbx-1", "sbx-2"],
            failed=[
                {"id": "sbx-3", "error": "Sandbox not found"},
            ],
            message="Deleted 2/3 sandboxes",
        )

        assert len(response.succeeded) == 2
        assert len(response.failed) == 1
        assert response.failed[0]["id"] == "sbx-3"
        assert "2/3" in response.message

    def test_bulk_delete_response_all_failed(self):
        """Test bulk delete response with all failed"""
        response = BulkDeleteSandboxResponse(
            succeeded=[],
            failed=[
                {"id": "sbx-1", "error": "Not found"},
                {"id": "sbx-2", "error": "Not found"},
            ],
            message="Deleted 0/2 sandboxes",
        )

        assert len(response.succeeded) == 0
        assert len(response.failed) == 2
        assert "0/2" in response.message
