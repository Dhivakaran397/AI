from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.activity_service import log_activity


class TaskService:
    @staticmethod
    async def create_task(db: AsyncSession, user_id: UUID, task_in: TaskCreate) -> TaskResponse | None:
        # Verify project belongs to user
        proj_res = await db.execute(
            select(Project).where(Project.id == task_in.project_id, Project.user_id == user_id)
        )
        project = proj_res.scalars().first()
        if not project:
            return None

        task = Task(
            project_id=task_in.project_id,
            title=task_in.title,
            description=task_in.description,
            status=TaskStatus.TODO,
            priority=TaskPriority(task_in.priority.upper()),
            dependencies=task_in.dependencies,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Log activity
        await log_activity(
            db=db,
            user_id=user_id,
            act_type="TASK_CREATED",
            title=f"Task added: '{task.title}'",
            description=f"Priority: {task.priority.value}",
            project_id=project.id,
        )

        return TaskResponse(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            assigned_agent=task.assigned_agent,
            dependencies=task.dependencies,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    async def get_tasks(
        db: AsyncSession,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> list[TaskResponse]:
        # Join Project to ensure user ownership
        query = select(Task).join(Project, Task.project_id == Project.id).where(Project.user_id == user_id)

        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == TaskStatus(status.upper()))
        if priority:
            query = query.where(Task.priority == TaskPriority(priority.upper()))

        query = query.order_by(Task.created_at.desc())
        result = await db.execute(query)
        tasks = list(result.scalars().all())

        return [
            TaskResponse(
                id=t.id,
                project_id=t.project_id,
                title=t.title,
                description=t.description,
                status=t.status.value,
                priority=t.priority.value,
                assigned_agent=t.assigned_agent,
                dependencies=t.dependencies,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tasks
        ]

    @staticmethod
    async def get_task(db: AsyncSession, user_id: UUID, task_id: UUID) -> Task | None:
        query = select(Task).join(Project, Task.project_id == Project.id).where(
            Task.id == task_id, Project.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def update_task(
        db: AsyncSession, user_id: UUID, task_id: UUID, update_in: TaskUpdate
    ) -> TaskResponse | None:
        task = await TaskService.get_task(db, user_id, task_id)
        if not task:
            return None

        old_status = task.status
        if update_in.title is not None:
            task.title = update_in.title
        if update_in.description is not None:
            task.description = update_in.description
        if update_in.priority is not None:
            task.priority = TaskPriority(update_in.priority.upper())
        if update_in.assigned_agent is not None:
            task.assigned_agent = update_in.assigned_agent
        if update_in.dependencies is not None:
            task.dependencies = update_in.dependencies

        if update_in.status is not None:
            new_status = TaskStatus(update_in.status.upper())
            task.status = new_status

            if old_status != new_status and new_status == TaskStatus.DONE:
                await log_activity(
                    db=db,
                    user_id=user_id,
                    act_type="TASK_COMPLETED",
                    title=f"Task completed: '{task.title}'",
                    project_id=task.project_id,
                )

        await db.commit()
        await db.refresh(task)

        return TaskResponse(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            assigned_agent=task.assigned_agent,
            dependencies=task.dependencies,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    async def delete_task(db: AsyncSession, user_id: UUID, task_id: UUID) -> bool:
        task = await TaskService.get_task(db, user_id, task_id)
        if not task:
            return False

        await db.delete(task)
        await db.commit()
        return True
