from typing import Any, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TestCaseResult(BaseModel):
    name: str
    suite: Optional[str] = None
    status: Literal["PASSED", "FAILED", "SKIPPED"]
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    failure_trace: Optional[str] = None


class TestSuiteRunResult(BaseModel):
    project_id: UUID
    command: str
    total_count: int
    passed_count: int
    failed_count: int
    skipped_count: int
    duration_ms: int
    cases: list[TestCaseResult] = Field(default_factory=list)
    raw_output: str
    exit_code: int


class TestGenerateRequest(BaseModel):
    file_path: str
    framework: Literal["pytest", "jest", "vitest"] = "pytest"
    extra_instructions: Optional[str] = None


class TestGenerateResponse(BaseModel):
    target_file: str
    test_file_path: str
    test_code: str
    framework: str
    test_count_estimated: int


class ErrorTraceAnalysisRequest(BaseModel):
    raw_trace: str
    command: Optional[str] = None


class ErrorTraceAnalysisResponse(BaseModel):
    error_type: str
    error_message: str
    culprit_file: Optional[str] = None
    culprit_line: Optional[int] = None
    surrounding_code: Optional[str] = None
    diagnosis: str
    suggested_diff: Optional[str] = None
    suggested_fix: Optional[str] = None


class ApplyPatchRequest(BaseModel):
    file_path: str
    patched_content: str
    description: Optional[str] = "Auto-applied diagnostic patch from test diagnosis"


class ApplyPatchResponse(BaseModel):
    file_path: str
    revision_id: Optional[UUID] = None
    success: bool
    message: str
