from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.activity import Activity
from uuid import UUID
from typing import Any

async def log_activity(db: AsyncSession, user_id: UUID, act_type: str, title: str, description: str | None = None, project_id: UUID | None = None, metadata_: dict[str, Any] | None = None) -> Activity:
    act = Activity(
        user_id=user_id,
        type=act_type,
        title=title,
        description=description,
        project_id=project_id,
        metadata_=metadata_
    )
    db.add(act)
    await db.commit()
    await db.refresh(act)
    return act

async def get_activities(
    db: AsyncSession,
    user_id: UUID,
    act_type: str | None = None,
    project_id: UUID | None = None,
    limit: int = 50,
) -> list[Activity]:
    stmt = select(Activity).where(Activity.user_id == user_id)
    if act_type:
        stmt = stmt.where(Activity.type == act_type)
    if project_id:
        stmt = stmt.where(Activity.project_id == project_id)
    stmt = stmt.order_by(Activity.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
