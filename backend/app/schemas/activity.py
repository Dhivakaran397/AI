from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ActivityResponse(BaseModel):
    id: UUID
    type: str
    title: str
    description: str | None = None
    project_id: UUID | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
