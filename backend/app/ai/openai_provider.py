import json
from typing import Any, AsyncGenerator, Type, TypeVar
import httpx
from pydantic import BaseModel

from .base import AIProvider
from .types import ChatMessage, ChatResponse, ModelInfo, StreamChunk, ToolCall
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = (settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _prepare_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        formatted = []
        for m in messages:
            item: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.name:
                item["name"] = m.name
            if m.tool_call_id:
                item["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                item["tool_calls"] = m.tool_calls
            formatted.append(item)
        return formatted

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        is_dummy_key = not self.api_key or "your-openai-api-key" in self.api_key or self.api_key.startswith("sk-your")
        if is_dummy_key:
            return ChatResponse(
                content=(
                    "👋 **வணக்கம்! I am DAI — Personal Intelligence & Project Builder!**\n\n"
                    "⚠️ **OpenAI API Key Not Configured**: Your `.env` currently has the placeholder key (`sk-your-openai-api-key`).\n\n"
                    "### How to activate live AI generation:\n"
                    "1. Click **Settings** (`/settings`) in the sidebar.\n"
                    "2. Enter your real **OpenAI API Key** (or select **Ollama** for 100% free offline AI!).\n"
                    "3. Click **Save Settings**.\n\n"
                    "✨ *All other DAI features (Monaco IDE `/workspace`, Projects `/projects`, Multi-Agent Swarm `/agents`, and RAG `/knowledge`) are 100% active and ready!*"
                ),
                model="dai-assistant",
            )

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload: dict[str, Any] = {
                "model": kwargs.get("model", settings.OPENAI_MODEL),
                "messages": self._prepare_messages(messages),
                "stream": False,
            }
            if tools:
                payload["tools"] = tools
                if tool_choice:
                    payload["tool_choice"] = tool_choice

            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            if resp.status_code == 401:
                return ChatResponse(
                    content=(
                        "👋 **வணக்கம்! I am DAI — Personal Intelligence & Project Builder!**\n\n"
                        "⚠️ **OpenAI API Key Error (401 Unauthorized)**: The provided OpenAI API key is invalid or expired.\n\n"
                        "### How to fix:\n"
                        "1. Go to **Settings** (`/settings`) in the sidebar.\n"
                        "2. Paste a valid **OpenAI API Key** (or choose **Ollama** for free local AI without any API key!).\n"
                        "3. Click **Save Settings**."
                    ),
                    model="dai-assistant",
                )
            if resp.status_code == 429:
                return ChatResponse(
                    content=(
                        "👋 **வணக்கம்! I am DAI — Personal Intelligence & Project Builder!**\n\n"
                        "⚠️ **OpenAI Quota Exceeded (429 Too Many Requests)**: உங்கள் OpenAI API Key சரியாக உள்ளது! ஆனால் உங்கள் OpenAI கணக்கில் பயன்பாட்டு கிரெடிட் இல்லை ($0.00 Balance).\n\n"
                        "### 2 எளிய வழிகள்:\n"
                        "1. **Free Google Gemini (100% இலவசம்!)**: [Google AI Studio](https://aistudio.google.com/app/apikey)-ல் இலவச Gemini Key எடுத்து **Settings**-ல் போடலாம்.\n"
                        "2. **OpenAI Billing**: [OpenAI Billing](https://platform.openai.com/settings/organization/billing)-ல் $5 கிரெடிட் சேர்க்கலாம்.\n\n"
                        "✨ *DAI-ன் மற்ற அனைத்து அம்சங்களும் (Monaco IDE `/workspace`, Projects `/projects`, Multi-Agent Swarm `/agents`) 100% தயார்!*"
                    ),
                    model="dai-assistant",
                )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            message_data = choice.get("message", {})

            # Extract tool calls if returned by model
            parsed_tool_calls: list[ToolCall] | None = None
            if "tool_calls" in message_data and message_data["tool_calls"]:
                parsed_tool_calls = []
                for tc in message_data["tool_calls"]:
                    fn = tc.get("function", {})
                    fn_args = {}
                    try:
                        fn_args = json.loads(fn.get("arguments", "{}"))
                    except Exception:
                        pass
                    parsed_tool_calls.append(
                        ToolCall(
                            id=tc.get("id", ""),
                            name=fn.get("name", ""),
                            arguments=fn_args,
                        )
                    )

            return ChatResponse(
                content=message_data.get("content") or "",
                model=data.get("model", payload["model"]),
                usage=data.get("usage"),
                tool_calls=parsed_tool_calls,
            )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamChunk, None]:
        is_dummy_key = not self.api_key or "your-openai-api-key" in self.api_key or self.api_key.startswith("sk-your")
        if is_dummy_key:
            demo_msg = (
                "👋 **வணக்கம்! I am DAI — Personal Intelligence & Project Builder!**\n\n"
                "⚠️ **OpenAI API Key Not Configured**: Your `.env` currently has the placeholder key (`sk-your-openai-api-key`).\n\n"
                "### How to activate live AI generation:\n"
                "1. Click **Settings** (`/settings`) in the sidebar.\n"
                "2. Enter your real **OpenAI API Key** (or select **Ollama** for 100% free offline AI!).\n"
                "3. Click **Save Settings**.\n\n"
                "✨ *All other DAI features (Monaco IDE `/workspace`, Projects `/projects`, Multi-Agent Swarm `/agents`, and RAG `/knowledge`) are 100% active and ready!*"
            )
            for word in demo_msg.split(" "):
                yield StreamChunk(content=word + " ", done=False)
            yield StreamChunk(content="", done=True)
            return

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload: dict[str, Any] = {
                "model": kwargs.get("model", settings.OPENAI_MODEL),
                "messages": self._prepare_messages(messages),
                "stream": True,
            }
            if tools:
                payload["tools"] = tools
                if tool_choice:
                    payload["tool_choice"] = tool_choice

            # Buffer for assembling streaming tool calls
            current_tool_calls: dict[int, dict[str, Any]] = {}

            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            ) as resp:
                if resp.status_code == 401:
                    auth_msg = (
                        "👋 **வணக்கம்! I am DAI — Personal Intelligence & Project Builder!**\n\n"
                        "⚠️ **OpenAI API Key Error (401 Unauthorized)**: The provided OpenAI API key is invalid or expired.\n\n"
                        "### How to fix:\n"
                        "1. Go to **Settings** (`/settings`) in the sidebar.\n"
                        "2. Paste a valid **OpenAI API Key** (or choose **Ollama** for free local AI without any API key!).\n"
                        "3. Click **Save Settings**."
                    )
                    for word in auth_msg.split(" "):
                        yield StreamChunk(content=word + " ", done=False)
                    yield StreamChunk(content="", done=True)
                    return

                if resp.status_code == 429:
                    quota_msg = (
                        "👋 **வணக்கம்! I am DAI — Personal Intelligence & Project Builder!**\n\n"
                        "⚠️ **OpenAI Quota Exceeded (429 Too Many Requests)**: உங்கள் OpenAI API Key சரியாக இணைக்கப்பட்டுள்ளது! ஆனால் உங்கள் OpenAI கணக்கில் பயன்பாட்டு கிரெடிட் இல்லை ($0.00 Balance).\n\n"
                        "### தீர்வுகள்:\n"
                        "1. **Free Google Gemini (100% இலவசம்!)**: [Google AI Studio](https://aistudio.google.com/app/apikey)-ல் இலவச Gemini Key எடுத்து **Settings**-ல் போடலாம்.\n"
                        "2. **OpenAI Billing**: [OpenAI Billing](https://platform.openai.com/settings/organization/billing)-ல் $5 கிரெடிட் சேர்க்கலாம்.\n\n"
                        "✨ *DAI-ன் மற்ற அனைத்து அம்சங்களும் (Monaco IDE `/workspace`, Projects `/projects`, Multi-Agent Swarm `/agents`) தயார்!*"
                    )
                    for word in quota_msg.split(" "):
                        yield StreamChunk(content=word + " ", done=False)
                    yield StreamChunk(content="", done=True)
                    return

                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw_data = line[6:].strip()
                    if raw_data == "[DONE]":
                        # If tool calls were accumulated, yield them in the final chunk
                        final_tool_calls: list[ToolCall] = []
                        for _, tc_buf in current_tool_calls.items():
                            args = {}
                            try:
                                args = json.loads(tc_buf["arguments"])
                            except Exception:
                                pass
                            final_tool_calls.append(
                                ToolCall(
                                    id=tc_buf.get("id", ""),
                                    name=tc_buf.get("name", ""),
                                    arguments=args,
                                )
                            )
                        yield StreamChunk(
                            content="",
                            done=True,
                            tool_calls=final_tool_calls if final_tool_calls else None,
                        )
                        break

                    try:
                        data = json.loads(raw_data)
                        delta = data["choices"][0].get("delta", {})

                        # Standard content token
                        content_token = delta.get("content") or ""

                        # Accumulate streaming tool calls
                        if "tool_calls" in delta and delta["tool_calls"]:
                            for tc_chunk in delta["tool_calls"]:
                                idx = tc_chunk.get("index", 0)
                                if idx not in current_tool_calls:
                                    current_tool_calls[idx] = {
                                        "id": tc_chunk.get("id", ""),
                                        "name": tc_chunk.get("function", {}).get("name", ""),
                                        "arguments": "",
                                    }
                                else:
                                    if "id" in tc_chunk and tc_chunk["id"]:
                                        current_tool_calls[idx]["id"] = tc_chunk["id"]
                                    if "name" in tc_chunk.get("function", {}):
                                        current_tool_calls[idx]["name"] = tc_chunk["function"]["name"]

                                fn_part = tc_chunk.get("function", {})
                                if "arguments" in fn_part:
                                    current_tool_calls[idx]["arguments"] += fn_part["arguments"]

                        if content_token:
                            yield StreamChunk(content=content_token, done=False)
                    except json.JSONDecodeError:
                        continue

    async def chat_structured(
        self,
        messages: list[ChatMessage],
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        """Enforce structured JSON output validated against response_model."""
        schema_json = json.dumps(response_model.model_json_schema())
        system_instruction = ChatMessage(
            role="system",
            content=f"You must respond with valid JSON strictly conforming to this JSON schema:\n{schema_json}",
        )
        augmented_messages = [system_instruction] + messages

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload: dict[str, Any] = {
                "model": kwargs.get("model", settings.OPENAI_MODEL),
                "messages": self._prepare_messages(augmented_messages),
                "response_format": {"type": "json_object"},
                "stream": False,
            }
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_json = data["choices"][0]["message"]["content"]
            return response_model.model_validate_json(raw_json)

    async def get_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="gpt-4o", name="GPT-4o", context_window=128000),
            ModelInfo(id="gpt-4o-mini", name="GPT-4o Mini", context_window=128000),
        ]

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return True

    @property
    def supports_vision(self) -> bool:
        return True
