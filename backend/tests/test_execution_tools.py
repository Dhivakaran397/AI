import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools.registry import tool_registry
from app.ai.tools.base import ToolPermission
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


@pytest.mark.asyncio
async def test_ai_execution_tools(db_session: AsyncSession, test_user):
    """Test ExecuteCommandTool and ManageProcessTool via ToolRegistry."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="AI Tool Test Project")
    )
    proj_id = str(proj.id)

    # 1. Check tools are registered
    exec_tool = tool_registry.get("execute_command")
    proc_tool = tool_registry.get("manage_process")

    assert exec_tool is not None
    assert exec_tool.permission == ToolPermission.EXECUTE
    assert proc_tool is not None
    assert proc_tool.permission == ToolPermission.EXECUTE

    # 2. Test execute_command via tool_registry
    res = await tool_registry.execute(
        "execute_command",
        arguments={
            "project_id": proj_id,
            "command": "python -c \"print('EXECUTE_TOOL_OK')\"",
        },
        allowed_permissions=[ToolPermission.EXECUTE],
    )
    assert res["status"] == "success"
    assert res["result"]["exit_code"] == 0
    assert "EXECUTE_TOOL_OK" in res["result"]["stdout"]

    # 3. Test execute_command blocked command
    res_blocked = await tool_registry.execute(
        "execute_command",
        arguments={
            "project_id": proj_id,
            "command": "rm -rf /",
        },
        allowed_permissions=[ToolPermission.EXECUTE],
    )
    assert res_blocked["status"] == "success"
    assert res_blocked["result"]["status"] == "blocked"

    # 4. Test permission denial if EXECUTE not granted
    res_denied = await tool_registry.execute(
        "execute_command",
        arguments={
            "project_id": proj_id,
            "command": "echo test",
        },
        allowed_permissions=[ToolPermission.READ],
    )
    assert "Permission denied" in res_denied["error"]

    # 5. Test manage_process via tool_registry (start, list, stop)
    start_res = await tool_registry.execute(
        "manage_process",
        arguments={
            "action": "start",
            "project_id": proj_id,
            "command": "python -u -c \"import time; print('daemon running'); time.sleep(10)\"",
            "port": 4040,
        },
        allowed_permissions=[ToolPermission.EXECUTE],
    )
    assert start_res["status"] == "success"
    assert start_res["result"]["status"] == "started"
    process_id = start_res["result"]["process"]["process_id"]

    # List processes
    list_res = await tool_registry.execute(
        "manage_process",
        arguments={
            "action": "list",
            "project_id": proj_id,
        },
        allowed_permissions=[ToolPermission.EXECUTE],
    )
    assert list_res["status"] == "success"
    assert len(list_res["result"]["processes"]) >= 1

    # Stop process
    stop_res = await tool_registry.execute(
        "manage_process",
        arguments={
            "action": "stop",
            "project_id": proj_id,
            "process_id": process_id,
        },
        allowed_permissions=[ToolPermission.EXECUTE],
    )
    assert stop_res["status"] == "success"
    assert stop_res["result"]["stopped"] is True
