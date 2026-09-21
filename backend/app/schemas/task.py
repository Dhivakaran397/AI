from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    project_id: UUID
    title: str
    description: str | None = None
    priority: str = "MEDIUM"
    dependencies: dict[str, Any] | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_agent: UUID | None = None
    dependencies: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None = None
    status: str
    priority: str
    assigned_agent: UUID | None = None
    dependencies: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
