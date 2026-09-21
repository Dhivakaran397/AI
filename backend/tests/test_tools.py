import pytest
from app.ai.tools.registry import tool_registry
from app.ai.tools.base import ToolPermission
from app.ai.tools.builtin import CalculateTool, GetCurrentTimeTool


@pytest.mark.asyncio
async def test_calculate_tool():
    tool = CalculateTool()
    # Simple addition
    res = await tool.execute("12 + 34")
    assert res["result"] == 46

    # Multiplication and order of operations
    res2 = await tool.execute("(10 + 2) * 5")
    assert res2["result"] == 60

    # Division
    res3 = await tool.execute("100 / 4")
    assert res3["result"] == 25.0


@pytest.mark.asyncio
async def test_get_current_time_tool():
    tool = GetCurrentTimeTool()
    res = await tool.execute()
    assert "utc" in res
    assert "iso" in res


def test_tool_registry_openai_export():
    openai_tools = tool_registry.get_openai_tools()
    assert len(openai_tools) >= 4

    tool_names = [t["function"]["name"] for t in openai_tools]
    assert "calculate" in tool_names
    assert "get_current_time" in tool_names
    assert "save_memory" in tool_names
    assert "web_search" in tool_names


@pytest.mark.asyncio
async def test_tool_registry_execution_and_permissions():
    # Successful execution through registry
    res = await tool_registry.execute("calculate", {"expression": "2 ** 8"})
    assert res["status"] == "success"
    assert res["result"]["result"] == 256

    # Permission check failure
    denied = await tool_registry.execute(
        "web_search",
        {"query": "python"},
        allowed_permissions=[ToolPermission.READ],  # web_search requires EXTERNAL
    )
    assert "error" in denied
    assert "Permission denied" in denied["error"]
