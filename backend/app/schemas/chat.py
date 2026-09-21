from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Any

class ConversationCreate(BaseModel):
    title: str
    mode: str

class ConversationResponse(BaseModel):
    id: UUID
    title: str
    mode: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    content: str
    mode: str | None = None
    attachments: list[dict[str, Any]] | None = None

class MessageUpdate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    mode: str | None = None
    metadata_: dict[str, Any] | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationWithMessages(ConversationResponse):
    messages: list[MessageResponse]
