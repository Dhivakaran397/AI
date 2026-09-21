from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.file import (
    FileNode,
    FileWriteRequest,
    FileEditRequest,
    FileContentResponse,
    FileDiffResponse,
    SearchResult,
)
from app.services.project_service import ProjectService
from app.services.file_service import FileService

router = APIRouter()


async def _verify_project_owner(db: AsyncSession, user_id: UUID, project_id: UUID):
    project = await ProjectService.get_project(db, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/files/tree", response_model=list[FileNode])
async def get_file_tree(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full nested file directory tree for the project workspace."""
    await _verify_project_owner(db, current_user.id, project_id)
    return await FileService.get_file_tree(db, project_id)


@router.get("/{project_id}/files/content", response_model=Optional[FileContentResponse])
async def read_file(
    project_id: UUID,
    path: str = Query(..., description="Relative path of file"),
    optional: bool = Query(False, description="Return null instead of 404 if file does not exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read file content and metadata."""
    await _verify_project_owner(db, current_user.id, project_id)
    file_data = await FileService.read_file(db, project_id, path)
    if not file_data:
        if optional:
            return None
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")
    return file_data


@router.post("/{project_id}/files", response_model=FileContentResponse)
async def write_file(
    project_id: UUID,
    body: FileWriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or overwrite a file in the project workspace (snapshots prior revision)."""
    await _verify_project_owner(db, current_user.id, project_id)
    return await FileService.write_file(db, project_id, body.path, body.content)


@router.patch("/{project_id}/files", response_model=FileContentResponse)
async def edit_file(
    project_id: UUID,
    body: FileEditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Targeted search and replace inside an existing file with validation."""
    await _verify_project_owner(db, current_user.id, project_id)
    try:
        return await FileService.edit_file(
            db, project_id, body.path, body.target_content, body.replacement_content
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/files")
async def delete_file(
    project_id: UUID,
    path: str = Query(..., description="Path of file or directory to delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a file or folder from the workspace."""
    await _verify_project_owner(db, current_user.id, project_id)
    deleted = await FileService.delete_file(db, project_id, path)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted"}


@router.get("/{project_id}/files/diff", response_model=FileDiffResponse)
async def get_file_diff(
    project_id: UUID,
    path: str = Query(..., description="Path of file to inspect diff"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unified diff between current content and latest revision snapshot."""
    await _verify_project_owner(db, current_user.id, project_id)
    diff = await FileService.get_diff(db, project_id, path)
    if not diff:
        raise HTTPException(status_code=404, detail="File not found")
    return diff


@router.post("/{project_id}/files/revert", response_model=FileContentResponse)
async def revert_file(
    project_id: UUID,
    path: str = Query(..., description="Path of file to revert"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Roll back file to its previous revision."""
    await _verify_project_owner(db, current_user.id, project_id)
    reverted = await FileService.revert_file(db, project_id, path)
    if not reverted:
        raise HTTPException(status_code=400, detail="No revision history available to revert")
    return reverted


@router.get("/{project_id}/files/search", response_model=list[SearchResult])
async def search_code(
    project_id: UUID,
    query: str = Query(..., description="Text query to search for across project files"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search code across all files in the project."""
    await _verify_project_owner(db, current_user.id, project_id)
    return await FileService.search_code(db, project_id, query)
