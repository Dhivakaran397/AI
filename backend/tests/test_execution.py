import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sandbox import is_safe_command
from app.services.execution_service import ExecutionService, process_manager
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


def test_command_safety_filter():
    """Verify that dangerous destructive commands are blocked by sandbox policy."""
    assert is_safe_command("npm test")[0] is True
    assert is_safe_command("pytest -v")[0] is True
    assert is_safe_command("python main.py")[0] is True
    assert is_safe_command("ls -la")[0] is True

    # Dangerous commands
    assert is_safe_command("rm -rf /")[0] is False
    assert is_safe_command("rm -rf $HOME")[0] is False
    assert is_safe_command("del /s /q c:\\")[0] is False
    assert is_safe_command("format d:")[0] is False
    assert is_safe_command("mkfs.ext4 /dev/sda1")[0] is False
    assert is_safe_command(":(){ :|:& };:")[0] is False
    assert is_safe_command("chmod -R 777 /")[0] is False
    assert is_safe_command("")[0] is False


@pytest.mark.asyncio
async def test_execution_service_safe_and_blocked(db_session: AsyncSession, test_user):
    """Test ExecutionService executing command and blocking unsafe commands."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Exec Test Project")
    )

    # Run safe command
    res = await ExecutionService.execute_command(
        project_id=proj.id,
        command="python -c \"print('DAI_SANDBOX_SUCCESS')\"",
        timeout_seconds=10,
        db=db_session,
    )
    assert res.exit_code == 0
    assert "DAI_SANDBOX_SUCCESS" in res.stdout
    assert res.status == "success"
    assert res.timed_out is False

    # Run blocked command
    blocked_res = await ExecutionService.execute_command(
        project_id=proj.id,
        command="rm -rf /",
        timeout_seconds=5,
    )
    assert blocked_res.status == "blocked"
    assert blocked_res.exit_code == 1
    assert "forbidden" in blocked_res.stderr.lower() or "hazardous" in blocked_res.stderr.lower()


@pytest.mark.asyncio
async def test_process_manager_lifecycle(db_session: AsyncSession, test_user):
    """Test ProcessManager start, port detection, logs, and stop."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Process Test Project")
    )

    # Start long-running simulated server
    script = "python -u -c \"import time; print('App listening on localhost:8080', flush=True); time.sleep(15)\""
    proc_info = await process_manager.start_process(
        project_id=proj.id,
        command=script,
        db=db_session,
    )

    assert proc_info.status == "RUNNING"
    assert proc_info.process_id in process_manager._processes

    # Wait briefly for stdout consumer to capture port & logs
    import asyncio
    await asyncio.sleep(1.0)

    # Check logs
    logs = process_manager.get_process_logs(proc_info.process_id)
    assert len(logs) > 0
    assert any("localhost:8080" in log.line for log in logs)

    # Check preview URL detection
    preview = process_manager.get_preview_url(proj.id)
    assert preview.is_active is True
    assert preview.port == 8080
    assert "8080" in preview.url

    # Stop process
    stopped = await process_manager.stop_process(proc_info.process_id)
    assert stopped is True


@pytest.mark.asyncio
async def test_execution_api_endpoints(client: AsyncClient, test_user):
    """Test REST endpoints for command execution and processes."""
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project
    proj_res = await client.post(
        "/api/v1/projects",
        json={"name": "API Exec Test Project", "description": "Testing API execution"},
        headers=headers,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 3. POST /execute
    exec_res = await client.post(
        f"/api/v1/projects/{proj_id}/execute",
        json={"command": "python -c \"print('EXECUTE_ENDPOINT_OK')\"", "timeout_seconds": 15},
        headers=headers,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "success"
    assert "EXECUTE_ENDPOINT_OK" in exec_data["stdout"]

    # 4. POST /processes
    proc_res = await client.post(
        f"/api/v1/projects/{proj_id}/processes",
        json={"command": "python -u -c \"import time; print('ready'); time.sleep(10)\"", "port": 5050},
        headers=headers,
    )
    assert proc_res.status_code == 200
    proc_id = proc_res.json()["process_id"]
    assert proc_res.json()["port"] == 5050

    # 5. GET /processes
    list_res = await client.get(
        f"/api/v1/projects/{proj_id}/processes",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 6. GET /preview/url
    preview_res = await client.get(
        f"/api/v1/projects/{proj_id}/preview/url",
        headers=headers,
    )
    assert preview_res.status_code == 200
    assert preview_res.json()["is_active"] is True
    assert preview_res.json()["port"] == 5050

    # 7. POST /processes/{id}/stop
    stop_res = await client.post(
        f"/api/v1/projects/{proj_id}/processes/{proc_id}/stop",
        headers=headers,
    )
    assert stop_res.status_code == 200
    assert stop_res.json()["success"] is True
