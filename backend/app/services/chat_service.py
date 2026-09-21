import json
import uuid
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.conversation import Conversation, ConversationMode
from app.models.message import Message
from app.schemas.chat import ConversationCreate, MessageCreate
from app.ai.registry import get_ai_provider
from app.ai.types import ChatMessage as AIChatMessage, ToolCall
from app.ai.tools.registry import tool_registry
from app.services.memory_service import MemoryService


async def create_conversation(
    db: AsyncSession, user_id: UUID, conv_in: ConversationCreate
) -> Conversation:
    raw_mode = (conv_in.mode or "CHAT").strip().upper()
    mode_map = {
        "BUILDER": ConversationMode.BUILD,
        "BUILD": ConversationMode.BUILD,
        "RESEARCH": ConversationMode.RESEARCH,
        "RESEARCHER": ConversationMode.RESEARCH,
        "AGENT": ConversationMode.AGENT,
        "ANALYZE": ConversationMode.ANALYZE,
        "ANALYSIS": ConversationMode.ANALYZE,
        "IMAGE": ConversationMode.IMAGE,
        "CHAT": ConversationMode.CHAT,
    }
    mode = mode_map.get(raw_mode, ConversationMode.CHAT)
    conv = Conversation(user_id=user_id, title=conv_in.title, mode=mode)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def get_conversations(db: AsyncSession, user_id: UUID) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(
    db: AsyncSession, user_id: UUID, conv_id: UUID
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    return result.scalars().first()


async def delete_conversation(
    db: AsyncSession, user_id: UUID, conv_id: UUID
) -> bool:
    conv = await get_conversation(db, user_id, conv_id)
    if not conv:
        return False
    await db.delete(conv)
    await db.commit()
    return True


async def create_message(
    db: AsyncSession,
    conv_id: UUID,
    role: str,
    content: str,
    mode: str | None = None,
    metadata_: dict | None = None,
) -> Message:
    msg = Message(
        conversation_id=conv_id,
        role=role,
        content=content,
        mode=mode,
        metadata_=metadata_,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, conv_id: UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def update_message(
    db: AsyncSession,
    user_id: UUID,
    conv_id: UUID,
    message_id: UUID,
    content: str,
) -> Message | None:
    conv = await get_conversation(db, user_id, conv_id)
    if not conv:
        return None
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conv_id,
        )
    )
    msg = result.scalars().first()
    if not msg:
        return None
    msg.content = content
    await db.commit()
    await db.refresh(msg)
    return msg


async def delete_message(
    db: AsyncSession,
    user_id: UUID,
    conv_id: UUID,
    message_id: UUID,
) -> bool:
    conv = await get_conversation(db, user_id, conv_id)
    if not conv:
        return False
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conv_id,
        )
    )
    msg = result.scalars().first()
    if not msg:
        return False
    await db.delete(msg)
    await db.commit()
    return True


def truncate_history(history: list[Message], max_messages: int = 30) -> list[Message]:
    """Sliding-window context truncation keeping the most recent conversation messages."""
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]


async def send_message_and_stream(
    db: AsyncSession,
    conv: Conversation,
    message_in: MessageCreate,
):
    """Save user message, inject memory context, execute autonomous tool calling loop, and stream SSE."""
    # 1. Save user message to database with attachments
    user_meta = {"attachments": message_in.attachments} if message_in.attachments else None
    await create_message(db, conv.id, "USER", message_in.content, message_in.mode, metadata_=user_meta)

    # 2. Retrieve history and truncate to context window
    raw_history = await get_messages(db, conv.id)
    truncated = truncate_history(raw_history)

    # 3. Build messages payload starting with System Prompt + Memory Context
    memory_context = await MemoryService.get_system_context_prompt(
        db, conv.user_id, conv.project_id
    )
    system_instruction = (
        "You are DAI, an elite personal AI intelligence and autonomous project builder. "
        "You have access to tools for calculation, real-time information, memory management, image generation, and document creation.\n"
        "MULTIMODAL & VISION: You have full multimodal vision! When the user attaches or pastes an image, diagram, screenshot, or document, you can clearly see and examine it. You can describe, analyze, OCR text, solve math/coding problems, or enhance it upon request.\n"
        "IMAGE GENERATION: You have access to the `generate_image` tool. When asked for an image, photo, wallpaper, artwork, or logo, immediately call `generate_image` and display using Markdown `![<prompt>](<image_url>)`.\n"
        "PRESENTATIONS & DOCUMENTS: You can generate Microsoft PowerPoint (.pptx) decks via `generate_presentation` and Microsoft Word (.docx) documents via `generate_word_document`. When requested (e.g. 'generate a PPT on AI', 'create a Word doc proposal'), call the appropriate tool to produce the file and return the download link.\n"
        "TEXT-TO-VIDEO & REELS: You have access to the `generate_video` tool. When the user asks to generate or create a video, reel, short, or clip (e.g. 'generate a video of Avengers airport battle', 'make an Instagram reel on AI'), you MUST call `generate_video`. Break down the story into 3 to 5 scenes with a punchy headline, descriptive subtitle, and especially a detailed `visual_prompt` describing the characters, action, and cinematic visual for each scene! It renders an authentic cinematic MP4 video with real AI scene visuals, Ken Burns camera motion, and soundtrack.\n"
        "SOCIAL MEDIA CAROUSELS: You have access to the `generate_social_carousel` tool. When the user asks for a carousel, multi-slide post, or slide deck for Instagram or LinkedIn, you MUST call `generate_social_carousel` with 3 to 6 slides with title, description, bullet_points, and visual_prompt for each slide.\n"
        "Use tools proactively. Be concise, precise, and highly competent.\n"
    )
    if memory_context:
        system_instruction += f"\n{memory_context}\n"

    ai_messages: list[AIChatMessage] = [
        AIChatMessage(role="system", content=system_instruction)
    ]

    for m in truncated:
        role = "user" if m.role == "USER" else "assistant"
        msg_meta = m.metadata_ or {}
        att = msg_meta.get("attachments") if role == "user" else None
        ai_messages.append(AIChatMessage(role=role, content=m.content, attachments=att))

    provider = get_ai_provider()
    tools = tool_registry.get_openai_tools()

    async def stream_generator():
        yield f"data: {json.dumps({'type': 'message_start'})}\n\n"

        full_content = ""
        executed_tool_calls: list[dict] = []
        max_tool_iterations = 3
        iteration = 0

        try:
            while iteration < max_tool_iterations:
                iteration += 1
                accumulated_tool_calls: list[ToolCall] = []

                try:
                    async for chunk in provider.chat_stream(ai_messages, tools=tools):
                        if chunk.content:
                            full_content += chunk.content
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': chunk.content})}\n\n"
                        if chunk.tool_calls:
                            accumulated_tool_calls.extend(chunk.tool_calls)
                except Exception as stream_err:
                    if executed_tool_calls:
                        break
                    raise stream_err

                # If no tool calls were requested, generation is complete
                if not accumulated_tool_calls:
                    break

                # Handle requested tool calls
                for tc in accumulated_tool_calls:
                    # Notify frontend that tool execution started
                    yield f"data: {json.dumps({'type': 'tool_call_start', 'tool_call': {'id': tc.id, 'name': tc.name, 'arguments': tc.arguments}})}\n\n"

                    # Execute the tool
                    exec_res = await tool_registry.execute(
                        tc.name,
                        tc.arguments,
                        context={"user_id": conv.user_id, "db": db},
                    )

                    tool_record = {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                        "result": exec_res,
                    }
                    executed_tool_calls.append(tool_record)

                    # Notify frontend with tool execution result
                    yield f"data: {json.dumps({'type': 'tool_call_result', 'tool_call_id': tc.id, 'name': tc.name, 'result': exec_res})}\n\n"

                    # Add assistant tool call message + tool response message to the message loop
                    ai_messages.append(
                        AIChatMessage(
                            role="assistant",
                            content="",
                            tool_calls=[{
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": json.dumps(tc.arguments),
                                },
                            }],
                        )
                    )
                    ai_messages.append(
                        AIChatMessage(
                            role="tool",
                            name=tc.name,
                            tool_call_id=tc.id,
                            content=json.dumps(exec_res),
                        )
                    )

            # Ensure any tool-generated image, presentation, document, video, or carousel is included in full_content
            for tc in executed_tool_calls:
                raw_res = tc.get("result", {})
                res = raw_res.get("result") if isinstance(raw_res, dict) and "result" in raw_res else raw_res

                if tc.get("name") == "generate_image":
                    img_url = res.get("image_url") if isinstance(res, dict) else None
                    prompt_txt = res.get("prompt", "Generated Image") if isinstance(res, dict) else "Generated Image"
                    if img_url and img_url not in full_content:
                        img_md = f"\n\n![{prompt_txt}]({img_url})\n"
                        full_content += img_md
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': img_md})}\n\n"
                elif tc.get("name") in ["generate_presentation", "generate_word_document"]:
                    file_url = res.get("file_url") if isinstance(res, dict) else None
                    doc_title = res.get("title", "Document") if isinstance(res, dict) else "Document"
                    file_type = res.get("file_type", "doc").upper() if isinstance(res, dict) else "DOC"
                    if file_url and file_url not in full_content:
                        doc_md = f"\n\n[Download {file_type}: {doc_title}]({file_url})\n"
                        full_content += doc_md
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': doc_md})}\n\n"
                elif tc.get("name") == "generate_video":
                    vid_url = res.get("video_url") if isinstance(res, dict) else None
                    vid_title = res.get("title", "Generated Video") if isinstance(res, dict) else "Generated Video"
                    if vid_url and vid_url not in full_content:
                        vid_md = f"\n\n[🎬 Watch / Download Video: {vid_title}]({vid_url})\n"
                        full_content += vid_md
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': vid_md})}\n\n"
                elif tc.get("name") == "generate_social_carousel":
                    slides = res.get("slides", []) if isinstance(res, dict) else []
                    c_title = res.get("title", "Carousel") if isinstance(res, dict) else "Carousel"
                    first_slide = res.get("preview_image_url") or (slides[0].get("image_url") if slides else None) if isinstance(res, dict) else None
                    if first_slide and first_slide not in full_content:
                        c_md = f"\n\n![{c_title} - Slide 1]({first_slide})\n"
                        full_content += c_md
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': c_md})}\n\n"

            # Intent safeguard: if user explicitly asked for media/video/carousel and no tool was called
            user_text = (message_in.content or "").strip().lower()
            refusal_patterns = ["cannot provide images", "limited to text", "cannot generate images", "unable to provide images", "cannot generate videos", "cannot create videos"]
            has_refusal = any(p in full_content.lower() for p in refusal_patterns)
            is_image_prompt = any(k in user_text for k in ["image", "photo", "picture", "wallpaper", "logo", "draw", "artwork", "/image"]) or (message_in.mode and message_in.mode.upper() == "IMAGE")
            is_video_prompt = any(k in user_text for k in ["video", "reel", "shorts", "clip", "make video", "generate video", "create video", "text to video", "text-to-video"])
            is_carousel_prompt = any(k in user_text for k in ["carousel", "social carousel", "instagram carousel", "linkedin carousel", "multi slide", "slides post"])

            if (is_image_prompt and not any(tc.get("name") == "generate_image" for tc in executed_tool_calls) and not is_video_prompt and not is_carousel_prompt) or has_refusal:
                clean_prompt = user_text
                for prefix in ["/image", "give", "create", "generate", "show", "draw", "make", "an image of", "image of", "a photo of", "photo of", "picture of"]:
                    if clean_prompt.startswith(prefix):
                        clean_prompt = clean_prompt[len(prefix):].strip()
                if not clean_prompt:
                    clean_prompt = user_text

                gen_res = await tool_registry.execute("generate_image", {"prompt": clean_prompt, "style": "photorealistic"})
                inner = gen_res.get("result", gen_res)
                img_url = inner.get("image_url") if isinstance(inner, dict) else None
                if img_url:
                    if has_refusal:
                        full_content = f"Here is the visual you requested for **{clean_prompt}**:\n\n![{clean_prompt}]({img_url})\n"
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': f'\n\n![{clean_prompt}]({img_url})\n'})}\n\n"
                    else:
                        img_md = f"\n\n![{clean_prompt}]({img_url})\n"
                        full_content += img_md
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': img_md})}\n\n"
                    executed_tool_calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": "generate_image",
                        "arguments": {"prompt": clean_prompt},
                        "result": gen_res,
                    })
            elif is_video_prompt and not any(tc.get("name") == "generate_video" for tc in executed_tool_calls):
                clean_topic = user_text
                for pfx in ["make a video of", "create a video of", "generate a video of", "make a video on", "create a video on", "generate a video on", "video about", "reel about", "make video", "create video", "generate video", "video of", "reel on", "video on"]:
                    if pfx in clean_topic:
                        clean_topic = clean_topic.split(pfx, 1)[-1].strip()
                if not clean_topic:
                    clean_topic = "Epic Cinematic Reel"

                scenes = [
                    {
                        "headline": f"{clean_topic.title()}"[:45],
                        "subtitle": f"The story of {clean_topic.title()}"[:75],
                        "visual_prompt": f"{clean_topic}, epic cinematic opening shot, blockbuster film scene, 8k resolution, dramatic lighting, highly detailed",
                        "points": ["The journey begins", "Stage is set"],
                        "duration_sec": 3.5,
                    },
                    {
                        "headline": "Dynamic Action & Clash",
                        "subtitle": "Intense confrontation & high stakes"[:75],
                        "visual_prompt": f"{clean_topic}, dynamic action battle sequence, explosive visual effects, cinematic masterpiece, 8k, detailed characters",
                        "points": ["High stakes encounter", "Unstoppable momentum"],
                        "duration_sec": 3.5,
                    },
                    {
                        "headline": "The Ultimate Climax",
                        "subtitle": "The decisive final showdown"[:75],
                        "visual_prompt": f"{clean_topic}, climactic final showdown, breathtaking movie cinematography, dramatic atmosphere, 8k",
                        "points": ["Decisive moment", "Legendary finish"],
                        "duration_sec": 3.5,
                    },
                ]
                vid_res = await tool_registry.execute("generate_video", {"topic": clean_topic, "scenes": scenes})
                inner_v = vid_res.get("result", vid_res)
                vid_url = inner_v.get("video_url") if isinstance(inner_v, dict) else None
                if vid_url:
                    vid_md = f"\n\nHere is your generated video reel for **{clean_topic.title()}**:\n\n[🎬 Watch / Download Video: {clean_topic}]({vid_url})\n"
                    full_content += vid_md
                    yield f"data: {json.dumps({'type': 'content_delta', 'content': vid_md})}\n\n"
                    executed_tool_calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": "generate_video",
                        "arguments": {"topic": clean_topic, "scenes": scenes},
                        "result": vid_res,
                    })
            elif is_carousel_prompt and not any(tc.get("name") == "generate_social_carousel" for tc in executed_tool_calls):
                clean_c = user_text
                for pfx in ["make a carousel of", "create a carousel of", "generate a carousel of", "make a carousel on", "create a carousel on", "generate a carousel on", "carousel about", "carousel on", "make carousel", "create carousel"]:
                    if pfx in clean_c:
                        clean_c = clean_c.split(pfx, 1)[-1].strip()
                if not clean_c:
                    clean_c = "Essential Highlights"

                c_slides = [
                    {
                        "slide_number": 1,
                        "title": clean_c.title()[:45],
                        "description": f"An exclusive visual breakdown of {clean_c.title()}.",
                        "tag": "INTRO",
                        "visual_prompt": f"{clean_c}, stunning modern digital concept art, clean aesthetic, 8k",
                        "bullet_points": ["Key overview", "Essential context"],
                    },
                    {
                        "slide_number": 2,
                        "title": "Core Breakdown & Analysis",
                        "description": "Deep dive into the critical moments, strategy, and highlights.",
                        "tag": "HIGHLIGHT",
                        "visual_prompt": f"{clean_c}, dynamic cinematic composition, vivid colors, detailed artwork",
                        "bullet_points": ["Key action", "Critical takeaways"],
                    },
                    {
                        "slide_number": 3,
                        "title": "Conclusion & Final Verdict",
                        "description": "The ultimate outcome and final conclusions.",
                        "tag": "FINAL",
                        "visual_prompt": f"{clean_c}, epic conclusion, masterwork illustration, 8k",
                        "bullet_points": ["Final outcome", "Legacy & impact"],
                    },
                ]
                c_res = await tool_registry.execute("generate_social_carousel", {"topic": clean_c, "slides": c_slides})
                inner_c = c_res.get("result", c_res)
                first_slide = (inner_c.get("preview_image_url") or (inner_c.get("slides", [{}])[0].get("image_url"))) if isinstance(inner_c, dict) else None
                if first_slide:
                    c_md = f"\n\nHere is your social media carousel for **{clean_c.title()}**:\n\n![{clean_c} - Slide 1]({first_slide})\n"
                    full_content += c_md
                    yield f"data: {json.dumps({'type': 'content_delta', 'content': c_md})}\n\n"
                    executed_tool_calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": "generate_social_carousel",
                        "arguments": {"topic": clean_c, "slides": c_slides},
                        "result": c_res,
                    })

            # Save the assistant message with metadata
            meta = {"tool_calls": executed_tool_calls} if executed_tool_calls else None
            await create_message(
                db,
                conv.id,
                "ASSISTANT",
                full_content,
                message_in.mode,
                metadata_=meta,
            )

            yield f"data: {json.dumps({'type': 'message_end', 'metadata': meta})}\n\n"
        except Exception as e:
            if executed_tool_calls:
                meta = {"tool_calls": executed_tool_calls}
                await create_message(
                    db,
                    conv.id,
                    "ASSISTANT",
                    full_content or "Generated result successfully:",
                    message_in.mode,
                    metadata_=meta,
                )
                yield f"data: {json.dumps({'type': 'message_end', 'metadata': meta})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return stream_generator()
