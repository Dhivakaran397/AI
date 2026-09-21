from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.services.activity_service import get_activities

router = APIRouter()

@router.get("", response_model=list[ActivityResponse])
@router.get("/", response_model=list[ActivityResponse], include_in_schema=False)
async def list_activities(
    type: Optional[str] = Query(None, description="Filter by activity type"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_activities(
        db=db,
        user_id=current_user.id,
        act_type=type,
        project_id=project_id,
        limit=limit,
    )
