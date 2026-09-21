from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    filename: str
    content: str
    file_type: str = "text/plain"
    project_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None


class DocumentChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    content: str
    metadata_: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size: int
    storage_path: str
    project_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    chunk_count: int = 0
    chunks: list[DocumentChunkResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DocumentSearchRequest(BaseModel):
    query: str
    project_id: Optional[UUID] = None
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    similarity_score: float
    metadata_: Optional[dict[str, Any]] = None
