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
        "You are DAI, an elite personal AI intelligence and autonomous project builder capable of solving ANY user request with precision, speed, and mastery.\n"
        "UNIVERSAL PROBLEM SOLVER: You can write production-ready code, debug complex errors, build full-stack web and mobile apps, design databases, execute shell commands, conduct deep real-time research, perform math, create presentations, and generate media. Always provide complete, robust, executable solutions without excuses or hesitation.\n"
        "REAL-TIME INFORMATION & LIVE WEB SEARCH: You have live web and real-time news access via `web_search` and `get_current_time`. When the user asks for today's news, current events, weather, stock updates, latest tech developments, or recent facts, ALWAYS invoke `web_search` or `get_current_time`. Synthesize live results with dates, summaries, and clarity. NEVER claim you lack real-time web browsing or that your knowledge cutoff prevents you from answering!\n"
        "MULTIMODAL & VISION: You have full multimodal vision! When the user attaches or pastes an image, diagram, screenshot, or document, you can clearly see and examine it. You can describe, analyze, OCR text, solve math/coding problems, or enhance it upon request.\n"
        "PINTEREST FOR ALL PICTURE REQUESTS (ABSOLUTE RULE): Whenever the user asks for ANY picture, photo, wallpaper, celebrity, actor, actress, anime character, vehicle, scene, style, aesthetic, or visual (e.g. 'give naruto image', 'show me photos of...', 'vijay pic', 'BMW wallpaper', 'sasuke photo', 'yuta image', 'pinterest pic'), ALWAYS AND ONLY invoke the `search_pinterest` tool! Pass clean search terms (e.g. query='naruto', query='sasuke', query='thalapathy vijay'). NEVER call `generate_image` for picture or character requests! NEVER call both `search_pinterest` and `generate_image` in the same turn! PRESENTATION RULE: Only output the clean image tags `![Title|pin=URL](IMAGE_URL)`. Do NOT output duplicate text links or raw URL lines below images!\n"
        "IMAGE ENHANCEMENT & HD CLARITY: You have access to the `enhance_image` tool! Whenever the user provides/uploads an image, or asks to enhance, upscale, clarify, make HD, retouch, or boost resolution on an image (e.g., 'enhance this pic', 'make it HD', 'increase quality', 'sharpen image', 'retouch this photo'), ALWAYS call `enhance_image`! It applies advanced detail enhancement, unsharp masking, contrast calibration, and 2x Lanczos super-resolution to deliver ultra-crisp HD output.\n"
        "IMAGE GENERATION (AI ART ONLY): You have access to the `generate_image` tool. ONLY call `generate_image` when the user EXPLICITLY commands you to synthesize artificial AI artwork from scratch using explicit commands like 'generate an AI image of...', 'draw AI art of...', 'paint an illustration of...'. NEVER use `generate_image` when the user simply asks for photos, pictures, characters, or wallpapers!\n"
        "PRESENTATIONS & DOCUMENTS: You can generate Microsoft PowerPoint (.pptx) decks via `generate_presentation` and Microsoft Word (.docx) documents via `generate_word_document`. When explicitly requested (e.g. 'generate a PPT on AI', 'create a Word doc proposal'), call the appropriate tool to produce the file and return the download link.\n"
        "TEXT-TO-VIDEO & REELS: You have access to the `generate_video` tool. Only when the user explicitly asks to generate or create a video, reel, short, or clip (e.g. 'generate a video of Avengers airport battle', 'make an Instagram reel on AI'), call `generate_video`. Break down the story into 3 to 5 scenes with a punchy headline, descriptive subtitle, and detailed `visual_prompt`. It renders an authentic cinematic MP4 video with real AI scene visuals, Ken Burns camera motion, and soundtrack.\n"
        "SOCIAL MEDIA CAROUSELS: You have access to the `generate_social_carousel` tool. Only when the user explicitly asks for a carousel, multi-slide post, or slide deck for Instagram or LinkedIn, call `generate_social_carousel` with 3 to 6 slides with title, description, bullet_points, and visual_prompt for each slide.\n"
        "TOOL DISCIPLINE: Only invoke media-generation tools (`generate_image`, `generate_video`, `generate_presentation`, `generate_social_carousel`, `generate_word_document`) when the user EXPLICITLY requests that media output. For general questions, recommendations, movie guides, explanations, and advice, answer purely in clear, high-quality text without generating unwanted media!\n"
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

                    # Execute the tool with explicit user request safeguards
                    if tc.name == "generate_image":
                        # Safeguard 1: If Pinterest search is in this batch or already executed, NEVER generate AI images
                        has_pinterest = any(c.name == "search_pinterest" for c in accumulated_tool_calls) or any(r.get("name") == "search_pinterest" for r in executed_tool_calls)
                        if has_pinterest:
                            exec_res = {
                                "status": "skipped",
                                "message": "Authentic pictures are already provided from Pinterest. Do not generate artificial images."
                            }
                        else:
                            # Safeguard 2: Only generate AI images if user explicitly commands AI artwork creation
                            user_req_lower = (message_in.content or "").lower()
                            ai_art_keywords = [
                                "generate an ai", "generate ai", "create an ai", "ai art", "ai image",
                                "ai picture", "draw", "paint", "synthesize", "dall-e", "midjourney",
                                "digital artwork", "create an illustration", "produce an ai", "வரை", "கலை"
                            ]
                            user_explicitly_asked = any(kw in user_req_lower for kw in ai_art_keywords)
                            if not user_explicitly_asked:
                                exec_res = {
                                    "status": "skipped",
                                    "message": "User requested real/anime picture, NOT artificial AI art. Do not generate AI art; use `search_pinterest` instead."
                                }
                            else:
                                exec_res = await tool_registry.execute(
                                    tc.name,
                                    tc.arguments,
                                    context={"user_id": conv.user_id, "db": db, "attachments": message_in.attachments},
                                )
                    else:
                        exec_res = await tool_registry.execute(
                            tc.name,
                            tc.arguments,
                            context={"user_id": conv.user_id, "db": db, "attachments": message_in.attachments},
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

            # Ensure any tool-generated image, Pinterest pins, enhancement, presentation, document, video, or carousel is included in full_content
            for tc in executed_tool_calls:
                raw_res = tc.get("result", {})
                res = raw_res.get("result") if isinstance(raw_res, dict) and "result" in raw_res else raw_res

                if tc.get("name") == "search_pinterest":
                    if isinstance(res, dict) and res.get("status") == "success":
                        pin_md = res.get("markdown")
                        if pin_md and pin_md not in full_content:
                            full_content += f"\n\n{pin_md}\n"
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': f'\n\n{pin_md}\n'})}\n\n"
                elif tc.get("name") == "enhance_image":
                    if isinstance(res, dict) and res.get("status") == "success":
                        enh_md = res.get("markdown")
                        if enh_md and enh_md not in full_content:
                            full_content += f"\n\n{enh_md}\n"
                            yield f"data: {json.dumps({'type': 'content_delta', 'content': f'\n\n{enh_md}\n'})}\n\n"
                elif tc.get("name") == "generate_image":
                    if isinstance(res, dict) and res.get("status") != "skipped":
                        img_url = res.get("image_url")
                        prompt_txt = res.get("prompt", "Generated Image")
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

            # Intent safeguard: if user asked for media/video/carousel and no tool was executed
            user_text = (message_in.content or "").strip().lower()
            refusal_patterns = ["cannot provide images", "limited to text", "cannot generate images", "unable to provide images", "cannot generate videos", "cannot create videos"]
            has_refusal = any(p in full_content.lower() for p in refusal_patterns)
            has_image_tool_run = any(tc.get("name") in ["search_pinterest", "generate_image", "enhance_image"] for tc in executed_tool_calls)
            is_image_prompt = any(k in user_text for k in ["image", "photo", "picture", "wallpaper", "logo", "draw", "artwork", "pic", "/image"]) or (message_in.mode and message_in.mode.upper() == "IMAGE")
            is_video_prompt = any(k in user_text for k in ["video", "reel", "shorts", "clip", "make video", "generate video", "create video", "text to video", "text-to-video"])
            is_carousel_prompt = any(k in user_text for k in ["carousel", "social carousel", "instagram carousel", "linkedin carousel", "multi slide", "slides post"])

            if (is_image_prompt and not has_image_tool_run and not is_video_prompt and not is_carousel_prompt) or (has_refusal and not has_image_tool_run):
                clean_prompt = user_text
                for prefix in ["/image", "give", "create", "generate", "show", "draw", "make", "an image of", "image of", "a photo of", "photo of", "picture of", "pic of"]:
                    if clean_prompt.startswith(prefix):
                        clean_prompt = clean_prompt[len(prefix):].strip()
                if not clean_prompt:
                    clean_prompt = user_text

                ai_art_keywords = ["generate an ai", "create an ai", "ai art", "ai image", "draw", "paint", "synthesize", "dall-e", "midjourney", "வரை", "கலை"]
                wants_ai_art = any(kw in user_text for kw in ai_art_keywords)

                if wants_ai_art:
                    gen_res = await tool_registry.execute("generate_image", {"prompt": clean_prompt})
                    inner = gen_res.get("result", gen_res)
                    img_url = inner.get("image_url") if isinstance(inner, dict) else None
                    if img_url:
                        img_md = f"\n\n![{clean_prompt}]({img_url})\n"
                        full_content += img_md
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': img_md})}\n\n"
                        executed_tool_calls.append({
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "name": "generate_image",
                            "arguments": {"prompt": clean_prompt},
                            "result": gen_res,
                        })
                else:
                    # STRICT RULE: Fetch authentic pictures from Pinterest
                    pin_res = await tool_registry.execute("search_pinterest", {"query": clean_prompt, "count": 4})
                    inner = pin_res.get("result", pin_res)
                    pin_md = inner.get("markdown") if isinstance(inner, dict) else None
                    if pin_md:
                        full_content += f"\n\n{pin_md}\n"
                        yield f"data: {json.dumps({'type': 'content_delta', 'content': f'\n\n{pin_md}\n'})}\n\n"
                        executed_tool_calls.append({
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "name": "search_pinterest",
                            "arguments": {"query": clean_prompt},
                            "result": pin_res,
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
