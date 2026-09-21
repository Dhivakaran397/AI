import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools.registry import tool_registry
from app.ai.tools.base import ToolPermission
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


@pytest.mark.asyncio
async def test_orchestrator_ai_tools(db_session: AsyncSession, test_user):
    """Test delegate_to_agent and run_self_correction tools via ToolRegistry."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Orchestrator Tools Test Project")
    )
    proj_id = str(proj.id)

    # 1. Check tools exist in registry
    delegate_tool = tool_registry.get("delegate_to_agent")
    heal_tool = tool_registry.get("run_self_correction")

    assert delegate_tool is not None
    assert delegate_tool.permission == ToolPermission.WRITE
    assert heal_tool is not None
    assert heal_tool.permission == ToolPermission.EXECUTE

    # 2. Test delegate_to_agent
    del_res = await tool_registry.execute(
        "delegate_to_agent",
        arguments={
            "project_id": proj_id,
            "agent_type": "ARCHITECT",
            "task": "Design modular schema for e-commerce orders",
        },
        context={"db": db_session},
        allowed_permissions=[ToolPermission.WRITE],
    )
    assert del_res["status"] == "success"
    assert del_res["result"]["agent_type"] == "ARCHITECT"
    assert del_res["result"]["status"] == "completed"

    # 3. Test run_self_correction
    heal_res = await tool_registry.execute(
        "run_self_correction",
        arguments={
            "project_id": proj_id,
            "test_command": "python -c \"print('ALL_GOOD')\"",
            "max_retries": 2,
        },
        context={"db": db_session},
        allowed_permissions=[ToolPermission.EXECUTE],
    )
    assert heal_res["status"] == "success"
    assert heal_res["result"]["resolved"] is True
    assert heal_res["result"]["initial_passed"] is True
