from pydantic import BaseModel, ConfigDict
from typing import Any

class SettingsUpdate(BaseModel):
    ai_provider: str | None = None
    ai_model: str | None = None
    theme: str | None = None
    preferences: dict[str, Any] | None = None

class SettingsResponse(BaseModel):
    ai_provider: str
    ai_model: str
    theme: str
    preferences: dict[str, Any] | None = None
    model_config = ConfigDict(from_attributes=True)
