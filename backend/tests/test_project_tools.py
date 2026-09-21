import pytest
from app.ai.tools.registry import tool_registry


@pytest.mark.asyncio
async def test_autonomous_project_tools(db_session, test_user):
    context = {"user_id": test_user.id, "db": db_session}

    # 1. Create project via AI tool
    res = await tool_registry.execute(
        "create_project",
        {
            "name": "Autonomous Robot UI",
            "description": "Robotics fleet control dashboard",
            "tech_stack": {"frontend": "Next.js", "ros": "ROS2"},
        },
        context=context,
    )
    assert res["status"] == "success"
    project_id = res["result"]["project_id"]
    assert res["result"]["project_status"] == "IDEA"

    # 2. Add task via AI tool
    t_res = await tool_registry.execute(
        "create_task",
        {
            "project_id": project_id,
            "title": "Design ROS2 websocket bridge",
            "priority": "HIGH",
        },
        context=context,
    )
    assert t_res["status"] == "success"
    task_id = t_res["result"]["task_id"]

    # 3. Update task status via AI tool
    t_up = await tool_registry.execute(
        "update_task_status",
        {"task_id": task_id, "status": "IN_PROGRESS"},
        context=context,
    )
    assert t_up["status"] == "success"
    assert t_up["result"]["task_status"] == "IN_PROGRESS"

    # 4. Advance project status via AI tool
    p_up = await tool_registry.execute(
        "update_project_status",
        {"project_id": project_id, "status": "PLANNING"},
        context=context,
    )
    assert p_up["status"] == "success"
    assert p_up["result"]["new_status"] == "PLANNING"
