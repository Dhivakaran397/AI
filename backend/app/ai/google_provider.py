import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Type, TypeVar
import httpx
from pydantic import BaseModel

from .base import AIProvider
from .types import ChatMessage, ChatResponse, ModelInfo, StreamChunk, ToolCall
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class GoogleProvider(AIProvider):
    def __init__(self) -> None:
        self.api_key = settings.GOOGLE_API_KEY
        self.model = getattr(settings, "GOOGLE_MODEL", "gemini-3.6-flash") or "gemini-3.6-flash"

    def _sanitize_schema(self, schema: Any) -> Any:
        """Sanitize Pydantic OpenAPI schemas to conform to Google Gemini function calling constraints."""
        if not isinstance(schema, dict):
            return schema
        clean = {}
        allowed_keys = {"type", "format", "description", "nullable", "enum", "properties", "required", "items"}
        for k, v in schema.items():
            if k in allowed_keys:
                if k == "properties" and isinstance(v, dict):
                    clean[k] = {pk: self._sanitize_schema(pv) for pk, pv in v.items()}
                elif k == "items" and isinstance(v, dict):
                    clean[k] = self._sanitize_schema(v)
                else:
                    clean[k] = v

        if "anyOf" in schema:
            types = [
                sub.get("type")
                for sub in schema["anyOf"]
                if isinstance(sub, dict) and "type" in sub and sub["type"] != "null"
            ]
            if types:
                clean["type"] = types[0]
                clean["nullable"] = True

        return clean

    def _prepare_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Convert OpenAI tool specifications into Google Gemini functionDeclarations."""
        if not tools:
            return None

        function_declarations = []
        for t in tools:
            fn = t.get("function", {})
            name = fn.get("name")
            if not name:
                continue
            params = self._sanitize_schema(fn.get("parameters", {"type": "object", "properties": {}}))
            function_declarations.append({
                "name": name,
                "description": fn.get("description", ""),
                "parameters": params,
            })

        if not function_declarations:
            return None

        return [{"functionDeclarations": function_declarations}]

    def _prepare_contents(self, messages: list[ChatMessage]) -> tuple[list[dict[str, Any]], str | None]:
        contents: list[dict[str, Any]] = []
        system_instruction: str | None = None

        for m in messages:
            if m.role == "system":
                if system_instruction:
                    system_instruction += f"\n{m.content}"
                else:
                    system_instruction = m.content
                continue

            if m.role == "user":
                parts: list[dict[str, Any]] = [{"text": m.content or " "}]
                if m.attachments:
                    for att in m.attachments:
                        data_str = att.get("data") or ""
                        mime = att.get("type") or "image/jpeg"
                        if data_str.startswith("data:"):
                            comma_idx = data_str.find(",")
                            if comma_idx != -1:
                                mime_part = data_str[5:comma_idx].split(";")[0]
                                b64_clean = data_str[comma_idx + 1:]
                                parts.append({
                                    "inlineData": {
                                        "mimeType": mime_part or mime,
                                        "data": b64_clean.strip(),
                                    }
                                })
                        elif len(data_str) > 100 and not data_str.startswith("http"):
                            parts.append({
                                "inlineData": {
                                    "mimeType": mime,
                                    "data": data_str.strip(),
                                }
                            })
                        elif att.get("content"):
                            filename = att.get("name", "document.txt")
                            parts.append({
                                "text": f"\n\n--- Attachment: {filename} ---\n{att['content']}\n--- End Attachment ---\n"
                            })
                contents.append({
                    "role": "user",
                    "parts": parts,
                })
            elif m.role == "assistant":
                parts: list[dict[str, Any]] = []
                if m.content:
                    parts.append({"text": m.content})
                if m.tool_calls:
                    for tc in m.tool_calls:
                        fn = tc.get("function", {})
                        raw_args = fn.get("arguments", {})
                        if isinstance(raw_args, str):
                            try:
                                parsed_args = json.loads(raw_args)
                            except Exception:
                                parsed_args = {}
                        else:
                            parsed_args = raw_args
                        parts.append({
                            "functionCall": {
                                "name": fn.get("name", tc.get("name", "")),
                                "args": parsed_args,
                            }
                        })
                if not parts:
                    parts.append({"text": " "})
                contents.append({"role": "model", "parts": parts})
            elif m.role == "tool":
                # Provide function response back to the model
                raw_resp = m.content
                if isinstance(raw_resp, str):
                    try:
                        resp_obj = json.loads(raw_resp)
                    except Exception:
                        resp_obj = {"result": raw_resp}
                else:
                    resp_obj = raw_resp if isinstance(raw_resp, dict) else {"result": raw_resp}

                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": m.name or "tool",
                            "response": resp_obj,
                        }
                    }]
                })

        return contents, system_instruction

    async def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResponse:
        api_key = kwargs.get("api_key") or self.api_key
        if not api_key:
            return ChatResponse(
                content="⚠️ Google Gemini API Key is missing. Please set it in Settings (/settings).",
                model=self.model,
            )

        candidate_models = [
            self.model,
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.8-flash",
            "gemini-2.5-flash",
        ]
        seen = set()
        candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]
        last_error = None

        tools = kwargs.get("tools")
        gemini_tools = self._prepare_tools(tools)
        contents, system_inst = self._prepare_contents(messages)

        async with httpx.AsyncClient(timeout=90.0) as client:
            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload: dict[str, Any] = {
                    "contents": contents,
                    "generationConfig": {
                        "maxOutputTokens": 16384,
                        "temperature": 0.4,
                    },
                }
                if system_inst:
                    payload["systemInstruction"] = {"parts": [{"text": system_inst}]}
                if gemini_tools:
                    payload["tools"] = gemini_tools
                if model_name.startswith("gemini-2.5"):
                    payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

                for attempt in range(2):
                    try:
                        resp = await client.post(url, json=payload)
                        if resp.status_code in [404, 400, 429]:
                            last_error = Exception(f"HTTP {resp.status_code} from {model_name}")
                            break
                        if resp.status_code in [503, 500] and attempt == 0:
                            await asyncio.sleep(0.5)
                            continue
                        resp.raise_for_status()
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts if p.get("text"))
                            tool_calls: list[ToolCall] = []
                            for p in parts:
                                if "functionCall" in p:
                                    fn = p["functionCall"]
                                    tool_calls.append(ToolCall(
                                        id=f"call_{uuid.uuid4().hex[:8]}",
                                        name=fn.get("name", ""),
                                        arguments=fn.get("args", {}),
                                    ))
                            return ChatResponse(
                                content=text,
                                model=model_name,
                                tool_calls=tool_calls or None,
                            )
                    except Exception as e:
                        last_error = e
                        if attempt == 0:
                            await asyncio.sleep(0.5)
                        continue

        if last_error:
            raise last_error
        raise ValueError("Failed to generate content from Google Gemini")

    async def chat_stream(
        self, messages: list[ChatMessage], **kwargs: Any
    ) -> AsyncGenerator[StreamChunk, None]:
        api_key = kwargs.get("api_key") or self.api_key
        if not api_key:
            yield StreamChunk(
                content="⚠️ Google Gemini API Key is missing. Please set it in Settings (/settings).\n\nYou can get a free key at: https://aistudio.google.com/app/apikey",
                done=True,
            )
            return

        candidate_models = [
            self.model,
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.8-flash",
            "gemini-2.5-flash",
        ]
        seen = set()
        candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]
        last_error = None
        started_yielding = False

        tools = kwargs.get("tools")
        gemini_tools = self._prepare_tools(tools)
        contents, system_inst = self._prepare_contents(messages)

        for model_name in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={api_key}"
            payload: dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": 16384,
                    "temperature": 0.4,
                },
            }
            if system_inst:
                payload["systemInstruction"] = {"parts": [{"text": system_inst}]}
            if gemini_tools:
                payload["tools"] = gemini_tools
            if model_name.startswith("gemini-2.5"):
                payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}

            for attempt in range(2):
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        async with client.stream("POST", url, json=payload) as resp:
                            if resp.status_code in [404, 400, 429]:
                                last_error = Exception(f"HTTP {resp.status_code} from {model_name}")
                                break
                            if resp.status_code != 200:
                                last_error = Exception(f"HTTP {resp.status_code} from {model_name}")
                                if attempt == 0:
                                    await asyncio.sleep(0.5)
                                continue

                            async for line in resp.aiter_lines():
                                if not line.startswith("data: "):
                                    continue
                                raw = line[6:].strip()
                                try:
                                    data = json.loads(raw)
                                    candidates = data.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for p in parts:
                                            if "functionCall" in p:
                                                fn = p["functionCall"]
                                                started_yielding = True
                                                yield StreamChunk(
                                                    tool_calls=[ToolCall(
                                                        id=f"call_{uuid.uuid4().hex[:8]}",
                                                        name=fn.get("name", ""),
                                                        arguments=fn.get("args", {}),
                                                    )],
                                                    done=False,
                                                )
                                            txt = p.get("text", "")
                                            if txt:
                                                started_yielding = True
                                                yield StreamChunk(content=txt, done=False)
                                except Exception:
                                    pass

                            yield StreamChunk(content="", done=True)
                            return
                except Exception as e:
                    last_error = e
                    if started_yielding:
                        yield StreamChunk(content="", done=True)
                        return
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                    continue

        if last_error and not started_yielding:
            try:
                chat_res = await self.chat(messages, **kwargs)
                if chat_res.tool_calls:
                    yield StreamChunk(tool_calls=chat_res.tool_calls, done=False)
                if chat_res.content:
                    yield StreamChunk(content=chat_res.content, done=False)
                yield StreamChunk(content="", done=True)
                return
            except Exception:
                pass
            yield StreamChunk(content=f"Error connecting to AI service: {last_error}", done=True)

    async def chat_structured(
        self,
        messages: list[ChatMessage],
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        schema = json.dumps(response_model.model_json_schema(), indent=2)
        system_instruction = ChatMessage(
            role="user",
            content=f"IMPORTANT: You MUST respond ONLY with a valid JSON object strictly matching this schema:\n{schema}\nOutput raw JSON without markdown codeblocks.",
        )
        augmented_messages = [system_instruction] + messages
        resp = await self.chat(augmented_messages, **kwargs)
        clean_content = resp.content.strip()
        if clean_content.startswith("`json"):
            clean_content = clean_content[7:]
        if clean_content.startswith("`"):
            clean_content = clean_content[3:]
        if clean_content.endswith("`"):
            clean_content = clean_content[:-3]
        return response_model.model_validate_json(clean_content.strip())

    async def get_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="gemini-2.5-flash", name="Gemini 2.5 Flash", context_window=1000000),
            ModelInfo(id="gemini-2.5-pro", name="Gemini 2.5 Pro", context_window=2000000),
        ]

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return False

    @property
    def supports_vision(self) -> bool:
        return True
