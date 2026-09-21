from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.testing import (
    TestSuiteRunResult,
    TestGenerateRequest,
    TestGenerateResponse,
    ErrorTraceAnalysisRequest,
    ErrorTraceAnalysisResponse,
    ApplyPatchRequest,
    ApplyPatchResponse,
)
from app.services.test_service import TestService
from app.services.debug_service import DebugService
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("/{project_id}/tests/run", response_model=TestSuiteRunResult)
async def run_project_tests(
    project_id: UUID,
    command: str = "pytest",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Execute test suite within sandboxed project workspace and return structured matrix."""
    project = await ProjectService.get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return await TestService.run_tests(
        db=db,
        project_id=project_id,
        command=command,
    )


@router.post("/{project_id}/tests/generate", response_model=TestGenerateResponse)
async def generate_tests_for_file(
    project_id: UUID,
    req: TestGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate comprehensive test suite for a given source code file."""
    project = await ProjectService.get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return await TestService.generate_tests(
        db=db,
        project_id=project_id,
        file_path=req.file_path,
        framework=req.framework,
        extra_instructions=req.extra_instructions,
    )


@router.post("/{project_id}/debug/analyze", response_model=ErrorTraceAnalysisResponse)
async def analyze_error_trace(
    project_id: UUID,
    req: ErrorTraceAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Analyze stack trace or error log and diagnose root cause with suggested patch."""
    project = await ProjectService.get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return await DebugService.analyze_error(
        db=db,
        project_id=project_id,
        raw_trace=req.raw_trace,
        command=req.command,
    )


@router.post("/{project_id}/debug/apply-patch", response_model=ApplyPatchResponse)
async def apply_diagnostic_patch(
    project_id: UUID,
    req: ApplyPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Apply verified diagnostic patch to project file and commit new revision."""
    project = await ProjectService.get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return await DebugService.apply_patch(
        db=db,
        project_id=project_id,
        file_path=req.file_path,
        patched_content=req.patched_content,
        description=req.description or "Applied diagnostic patch",
    )
