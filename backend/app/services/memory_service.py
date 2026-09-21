import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.memory import Memory, MemoryType
from app.schemas.memory import MemoryCreate
from app.core.redis import get_redis


class MemoryService:
    CACHE_EXPIRY = 300  # 5 minutes

    @staticmethod
    async def create_memory(db: AsyncSession, user_id: UUID, memory_in: MemoryCreate) -> Memory:
        mem_type = MemoryType(memory_in.type.upper())
        memory = Memory(
            user_id=user_id,
            project_id=memory_in.project_id,
            type=mem_type,
            content=memory_in.content,
            metadata_=memory_in.metadata_,
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)

        # Invalidate Redis cache for preferences
        try:
            redis = await get_redis()
            await redis.delete(f"user_memories:{user_id}")
        except Exception:
            pass

        return memory

    @staticmethod
    async def get_memories(
        db: AsyncSession,
        user_id: UUID,
        memory_type: str | None = None,
        project_id: UUID | None = None,
    ) -> list[Memory]:
        query = select(Memory).where(Memory.user_id == user_id)
        if memory_type:
            query = query.where(Memory.type == MemoryType(memory_type.upper()))
        if project_id:
            query = query.where(Memory.project_id == project_id)
        query = query.order_by(Memory.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_memory(db: AsyncSession, user_id: UUID, memory_id: UUID) -> bool:
        stmt = delete(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
        result = await db.execute(stmt)
        await db.commit()

        try:
            redis = await get_redis()
            await redis.delete(f"user_memories:{user_id}")
        except Exception:
            pass

        return result.rowcount > 0

    @staticmethod
    async def get_system_context_prompt(
        db: AsyncSession, user_id: UUID, project_id: UUID | None = None
    ) -> str:
        """Construct system context string with user preferences and decisions."""
        memories = await MemoryService.get_memories(db, user_id, project_id=project_id)
        if not memories:
            return ""

        context_lines = [
            "Below is the persistent user context and preferences retrieved from DAI memory:"
        ]
        for m in memories[:15]:  # limit to top 15 memories for context window budget
            context_lines.append(f"- [{m.type.value}]: {m.content}")

        return "\n".join(context_lines)
