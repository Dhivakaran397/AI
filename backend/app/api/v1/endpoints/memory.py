from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.memory import MemoryCreate, MemoryResponse
from app.services.memory_service import MemoryService

router = APIRouter()


@router.get("", response_model=list[MemoryResponse])
async def list_memories(
    type: Optional[str] = Query(None, description="Filter by memory type (e.g. PREFERENCE, DECISION)"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all stored memories for current user."""
    return await MemoryService.get_memories(
        db, user_id=current_user.id, memory_type=type, project_id=project_id
    )


@router.post("", response_model=MemoryResponse)
async def create_memory(
    memory_in: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly save a new memory item."""
    return await MemoryService.create_memory(
        db, user_id=current_user.id, memory_in=memory_in
    )


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a memory item."""
    deleted = await MemoryService.delete_memory(
        db, user_id=current_user.id, memory_id=memory_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted"}
