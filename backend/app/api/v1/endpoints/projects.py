from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.config import settings
from app.core.security import ALGORITHM
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse
from app.services.auth_service import get_user_by_id
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects belonging to the authenticated user."""
    return await ProjectService.get_projects(db, user_id=current_user.id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project initialized in IDEA state."""
    return await ProjectService.create_project(db, user_id=current_user.id, project_in=project_in)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project_detail(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full project details, tasks, and recent activities."""
    detail = await ProjectService.get_project_detail(db, user_id=current_user.id, project_id=project_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    update_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project attributes or advance its state machine status."""
    updated = await ProjectService.update_project(
        db, user_id=current_user.id, project_id=project_id, update_in=update_in
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete project and associated tasks."""
    deleted = await ProjectService.delete_project(db, user_id=current_user.id, project_id=project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}


@router.get("/{project_id}/download")
async def download_project(
    project_id: UUID,
    request: Request,
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Download the entire project code as a full ZIP folder for VS Code."""
    auth_header = request.headers.get("Authorization")
    raw_token = None
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header.split(" ", 1)[1]
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = UUID(user_id_str)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    project = await ProjectService.get_project(db, user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    zip_buffer, filename = await ProjectService.export_project_zip(db, project)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )

