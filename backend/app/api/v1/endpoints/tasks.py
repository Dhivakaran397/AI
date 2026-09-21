from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    project_id: Optional[UUID] = Query(None, description="Filter tasks by project"),
    status: Optional[str] = Query(None, description="Filter tasks by status (e.g. TODO, IN_PROGRESS, DONE)"),
    priority: Optional[str] = Query(None, description="Filter tasks by priority (e.g. LOW, HIGH, CRITICAL)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks belonging to user projects, with optional filters."""
    return await TaskService.get_tasks(
        db, user_id=current_user.id, project_id=project_id, status=status, priority=priority
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task under a user project."""
    task = await TaskService.create_task(db, user_id=current_user.id, task_in=task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    update_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task status, priority, title, or assigned agent."""
    updated = await TaskService.update_task(
        db, user_id=current_user.id, task_id=task_id, update_in=update_in
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a task."""
    deleted = await TaskService.delete_task(db, user_id=current_user.id, task_id=task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted"}
