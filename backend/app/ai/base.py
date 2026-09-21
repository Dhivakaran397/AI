from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Type, TypeVar
from pydantic import BaseModel
from .types import ChatMessage, ChatResponse, ModelInfo, StreamChunk

T = TypeVar("T", bound=BaseModel)


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate a complete chat response, optionally with tool calling."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream chat completion chunks with tool call handling."""
        pass

    @abstractmethod
    async def chat_structured(
        self,
        messages: list[ChatMessage],
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        """Enforce structured output conforming strictly to a Pydantic model schema."""
        pass

    @abstractmethod
    async def get_models(self) -> list[ModelInfo]:
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        pass

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        pass

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        pass
