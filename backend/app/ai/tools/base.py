from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Type
from pydantic import BaseModel


class ToolPermission(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    EXTERNAL = "EXTERNAL"


class BaseTool(ABC):
    name: str
    description: str
    permission: ToolPermission = ToolPermission.READ
    args_schema: Type[BaseModel] | None = None

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with validated arguments."""
        pass

    def get_parameters_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for the tool parameters."""
        if self.args_schema:
            schema = self.args_schema.model_json_schema()
            # Clean schema for OpenAI compatibility
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            return {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        return {"type": "object", "properties": {}}

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI tool specification."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }
