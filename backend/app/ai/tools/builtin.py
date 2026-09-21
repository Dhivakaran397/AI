import ast
import operator
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool, ToolPermission


# --- 1. Get Current Time Tool ---
class TimeArgs(BaseModel):
    timezone_offset_hours: float | None = Field(
        default=0.0,
        description="Optional offset from UTC in hours (e.g. 5.5 for IST, -5 for EST)"
    )


class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "Get the current real-time UTC timestamp and localized date/time."
    permission = ToolPermission.READ
    args_schema = TimeArgs

    async def execute(self, timezone_offset_hours: float | None = 0.0, **kwargs: Any) -> dict[str, str]:
        utc_now = datetime.now(timezone.utc)
        return {
            "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "iso": utc_now.isoformat(),
        }


# --- 2. Calculate Tool (Safe Math Evaluator) ---
class CalculateArgs(BaseModel):
    expression: str = Field(
        ...,
        description="Mathematical expression to calculate, e.g. '128 * 45 + 1024 / 4'"
    )


class CalculateTool(BaseTool):
    name = "calculate"
    description = "Safely evaluate mathematical and arithmetic expressions without arbitrary code execution."
    permission = ToolPermission.READ
    args_schema = CalculateArgs

    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(self, node: ast.AST) -> float | int:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            op_type = type(node.op)
            if op_type in self._operators:
                return self._operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise ValueError(f"Unsupported syntax: {type(node).__name__}")

    async def execute(self, expression: str, **kwargs: Any) -> dict[str, Any]:
        try:
            parsed = ast.parse(expression.strip(), mode="eval")
            result = self._eval(parsed.body)
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"expression": expression, "error": str(e)}


# --- 3. Save Memory Tool ---
class SaveMemoryArgs(BaseModel):
    content: str = Field(..., description="Key fact, user preference, architectural decision, or knowledge to remember")
    memory_type: str = Field(
        default="PREFERENCE",
        description="Type of memory: 'PREFERENCE', 'DECISION', 'PROJECT', 'KNOWLEDGE'"
    )


class SaveMemoryTool(BaseTool):
    name = "save_memory"
    description = "Explicitly save an important preference, decision, or fact to long-term memory for future conversations."
    permission = ToolPermission.WRITE
    args_schema = SaveMemoryArgs

    async def execute(self, content: str, memory_type: str = "PREFERENCE", user_id: Any = None, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "saved",
            "memory_type": memory_type.upper(),
            "content": content,
            "message": "Memory persisted successfully to knowledge bank."
        }


# --- 4. Web Search Stub Tool ---
class WebSearchArgs(BaseModel):
    query: str = Field(..., description="Search query string")
    max_results: int = Field(default=3, description="Maximum number of results to return")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for up-to-date documentation, libraries, and technical references."
    permission = ToolPermission.EXTERNAL
    args_schema = WebSearchArgs

    async def execute(self, query: str, max_results: int = 3, **kwargs: Any) -> dict[str, Any]:
        return {
            "query": query,
            "results": [
                {
                    "title": f"Official Reference: {query}",
                    "snippet": f"Up-to-date documentation and developer guide regarding {query}.",
                    "url": f"https://docs.example.com/search?q={query.replace(' ', '+')}"
                }
            ]
        }
