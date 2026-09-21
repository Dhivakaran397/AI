from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    content: str
    type: str = "PREFERENCE"
    project_id: UUID | None = None
    metadata_: dict[str, Any] | None = None


class MemoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    project_id: UUID | None = None
    type: str
    content: str
    metadata_: dict[str, Any] | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
