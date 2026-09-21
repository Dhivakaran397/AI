from datetime import datetime
from typing import Any, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AgentResponse(BaseModel):
    id: UUID
    name: str
    type: str
    description: Optional[str] = None
    system_prompt: str
    capabilities: dict[str, Any]
    is_active: bool = True
    icon: Optional[str] = None
    color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AgentRunCreate(BaseModel):
    agent_id: UUID
    project_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    input_data: dict[str, Any]


class AgentRunResponse(BaseModel):
    id: UUID
    agent_id: UUID
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    project_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    input_data: dict[str, Any]
    output_data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrchestrationStep(BaseModel):
    step_id: str
    agent_type: str
    agent_name: str
    action: str
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"] = "PENDING"
    input_summary: str
    output_summary: Optional[str] = None
    artifacts: list[str] = Field(default_factory=list)
    duration_ms: Optional[int] = None


class TeamOrchestrationRequest(BaseModel):
    project_id: UUID
    goal: str


class TeamOrchestrationResponse(BaseModel):
    project_id: UUID
    goal: str
    status: Literal["COMPLETED", "FAILED", "IN_PROGRESS"]
    summary: str
    steps: list[OrchestrationStep]
    created_files: list[str] = Field(default_factory=list)


class SelfHealRequest(BaseModel):
    project_id: UUID
    test_command: str = "pytest"
    max_retries: int = Field(default=3, ge=1, le=5)


class SelfHealResponse(BaseModel):
    project_id: UUID
    test_command: str
    initial_passed: bool
    resolved: bool
    iterations: int
    diagnosis: Optional[str] = None
    patches_applied: list[str] = Field(default_factory=list)
    final_output: str
