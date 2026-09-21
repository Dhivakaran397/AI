from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class CommandExecutionRequest(BaseModel):
    command: str
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    working_dir: Optional[str] = None


class CommandExecutionResponse(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    status: Literal["success", "failed", "timeout", "blocked"]
    error: Optional[str] = None


class ProcessStartRequest(BaseModel):
    command: str
    port: Optional[int] = None


class ProcessLogChunk(BaseModel):
    line: str
    timestamp: datetime
    stream: Literal["stdout", "stderr"]


class ProcessInfo(BaseModel):
    process_id: str
    project_id: str
    command: str
    pid: Optional[int] = None
    status: Literal["RUNNING", "STOPPED", "FAILED"]
    port: Optional[int] = None
    started_at: datetime
    logs_count: int = 0


class ProcessLogResponse(BaseModel):
    process_id: str
    logs: list[ProcessLogChunk]


class PreviewUrlResponse(BaseModel):
    url: Optional[str] = None
    is_active: bool = False
    port: Optional[int] = None
