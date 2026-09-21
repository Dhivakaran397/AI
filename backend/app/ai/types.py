from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResult(BaseModel):
    tool_call_id: str
    name: str
    result: Any
    is_error: bool = False


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: dict[str, int] | None = None
    tool_calls: list[ToolCall] | None = None


class ModelInfo(BaseModel):
    id: str
    name: str
    context_window: int


class StreamEventType(str, Enum):
    MESSAGE_START = "message_start"
    CONTENT_DELTA = "content_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_RESULT = "tool_call_result"
    MESSAGE_END = "message_end"
    ERROR = "error"


class StreamChunk(BaseModel):
    content: str = ""
    done: bool = False
    tool_calls: list[ToolCall] | None = None
