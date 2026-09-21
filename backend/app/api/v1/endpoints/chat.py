from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageUpdate,
    ConversationWithMessages,
    MessageResponse,
)
from app.services.chat_service import (
    create_conversation,
    get_conversations,
    get_conversation,
    delete_conversation,
    send_message_and_stream,
    get_messages,
    update_message,
    delete_message,
)
from app.models.user import User
from starlette.responses import StreamingResponse
from uuid import UUID

router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse)
async def create_conv(conv_in: ConversationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await create_conversation(db, current_user.id, conv_in)

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_convs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_conversations(db, current_user.id)

@router.get("/conversations/{conv_id}", response_model=ConversationWithMessages)
async def get_conv(conv_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = await get_conversation(db, current_user.id, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await get_messages(db, conv_id)
    conv_data = ConversationResponse.model_validate(conv).model_dump()
    conv_data["messages"] = [MessageResponse.model_validate(m) for m in messages]
    return ConversationWithMessages(**conv_data)

@router.delete("/conversations/{conv_id}")
async def delete_conv(conv_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = await delete_conversation(db, current_user.id, conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

@router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: UUID, message_in: MessageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = await get_conversation(db, current_user.id, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    stream = await send_message_and_stream(db, conv, message_in)
    return StreamingResponse(stream, media_type="text/event-stream")

@router.put("/conversations/{conv_id}/messages/{message_id}", response_model=MessageResponse)
async def update_msg(
    conv_id: UUID,
    message_id: UUID,
    msg_in: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = await update_message(db, current_user.id, conv_id, message_id, msg_in.content)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageResponse.model_validate(msg)

@router.delete("/conversations/{conv_id}/messages/{message_id}")
async def delete_msg(
    conv_id: UUID,
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = await delete_message(db, current_user.id, conv_id, message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "deleted"}
