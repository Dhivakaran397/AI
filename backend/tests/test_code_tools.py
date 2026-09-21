import pytest
from app.ai.tools.registry import tool_registry
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


@pytest.mark.asyncio
async def test_coding_agent_tools(db_session, test_user):
    context = {"user_id": test_user.id, "db": db_session}

    # Setup project
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Coding Tool Test Project")
    )
    proj_id = str(proj.id)

    # 1. Write file tool
    w_res = await tool_registry.execute(
        "write_file",
        {
            "project_id": proj_id,
            "path": "server.py",
            "content": "from fastapi import FastAPI\napp = FastAPI()\n",
        },
        context=context,
    )
    assert w_res["status"] == "success"
    assert "server.py" in w_res["result"]["path"]

    # 2. Read file tool
    r_res = await tool_registry.execute(
        "read_file",
        {"project_id": proj_id, "path": "server.py"},
        context=context,
    )
    assert r_res["status"] == "success"
    assert "FastAPI" in r_res["result"]["content"]

    # 3. Edit file tool
    e_res = await tool_registry.execute(
        "edit_file",
        {
            "project_id": proj_id,
            "path": "server.py",
            "target_content": "app = FastAPI()",
            "replacement_content": "app = FastAPI(title='DAI Engine')",
        },
        context=context,
    )
    assert e_res["status"] == "success"

    # 4. Search code tool
    s_res = await tool_registry.execute(
        "search_code",
        {"project_id": proj_id, "query": "DAI Engine"},
        context=context,
    )
    assert s_res["status"] == "success"
    assert s_res["result"]["matches_count"] >= 1

    # 5. Revert file tool
    rev_res = await tool_registry.execute(
        "revert_file",
        {"project_id": proj_id, "path": "server.py"},
        context=context,
    )
    assert rev_res["status"] == "success"

    # Check that it reverted
    r_after = await tool_registry.execute(
        "read_file",
        {"project_id": proj_id, "path": "server.py"},
        context=context,
    )
    assert "DAI Engine" not in r_after["result"]["content"]
    assert "app = FastAPI()" in r_after["result"]["content"]
