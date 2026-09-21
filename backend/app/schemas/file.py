from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FileNode(BaseModel):
    name: str
    path: str
    is_directory: bool
    size: int = 0
    children: list["FileNode"] = []


class FileWriteRequest(BaseModel):
    path: str
    content: str


class FileEditRequest(BaseModel):
    path: str
    target_content: str
    replacement_content: str


class FileContentResponse(BaseModel):
    path: str
    content: str
    size: int
    file_type: str
    has_revisions: bool = False
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileDiffResponse(BaseModel):
    path: str
    original_content: str
    current_content: str
    diff_unified: str
    revision_id: Optional[str] = None


class SearchResult(BaseModel):
    path: str
    line_number: int
    line_content: str
