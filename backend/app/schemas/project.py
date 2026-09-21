from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.schemas.task import TaskResponse
from app.schemas.activity import ActivityResponse


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    tech_stack: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    tech_stack: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    status: str
    tech_stack: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    completed_task_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    tasks: list[TaskResponse] = []
    recent_activities: list[ActivityResponse] = []
