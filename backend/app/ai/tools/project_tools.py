from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.ai.tools.base import BaseTool, ToolPermission
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


# 1. Create Project Tool
class CreateProjectArgs(BaseModel):
    name: str = Field(..., description="The name of the new software project")
    description: str | None = Field(None, description="Detailed description of what the project builds")
    tech_stack: dict[str, Any] | None = Field(
        None, description="Suggested tech stack dictionary e.g. {'frontend': 'Next.js', 'backend': 'FastAPI'}"
    )


class CreateProjectTool(BaseTool):
    name = "create_project"
    description = "Create and initialize a new project workspace starting in IDEA state."
    permission = ToolPermission.WRITE
    args_schema = CreateProjectArgs

    async def execute(self, name: str, description: str | None = None, tech_stack: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        user_id: UUID | None = kwargs.get("user_id")
        db = kwargs.get("db")
        if not user_id or not db:
            return {"status": "error", "error": "Database session or user context unavailable"}

        project_in = ProjectCreate(name=name, description=description, tech_stack=tech_stack)
        project = await ProjectService.create_project(db=db, user_id=user_id, project_in=project_in)
        return {
            "status": "success",
            "project_id": str(project.id),
            "name": project.name,
            "project_status": project.status,
            "message": f"Project '{project.name}' successfully initialized.",
        }


# 2. Update Project Status Tool
class UpdateProjectStatusArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project")
    status: str = Field(
        ...,
        description="New state machine status: 'PLANNING', 'BUILDING', 'TESTING', 'DEBUGGING', 'REVIEW', 'COMPLETED', 'FAILED'"
    )


class UpdateProjectStatusTool(BaseTool):
    name = "update_project_status"
    description = "Advance or update the state machine status of an active project."
    permission = ToolPermission.WRITE
    args_schema = UpdateProjectStatusArgs

    async def execute(self, project_id: str, status: str, **kwargs: Any) -> dict[str, Any]:
        user_id: UUID | None = kwargs.get("user_id")
        db = kwargs.get("db")
        if not user_id or not db:
            return {"status": "error", "error": "Database session or user context unavailable"}

        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid UUID: {project_id}"}

        update_in = ProjectUpdate(status=status)
        project = await ProjectService.update_project(db=db, user_id=user_id, project_id=p_uuid, update_in=update_in)
        if not project:
            return {"status": "error", "error": f"Project {project_id} not found."}

        return {
            "status": "success",
            "project_id": str(project.id),
            "new_status": project.status,
            "message": f"Project transitioned to {project.status}.",
        }


# 3. Create Task Tool
class CreateTaskArgs(BaseModel):
    project_id: str = Field(..., description="UUID of the project this task belongs to")
    title: str = Field(..., description="Title of the task")
    description: str | None = Field(None, description="Detailed instructions and acceptance criteria")
    priority: str = Field(default="MEDIUM", description="'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'")


class CreateTaskTool(BaseTool):
    name = "create_task"
    description = "Create a development or research task under a specific project."
    permission = ToolPermission.WRITE
    args_schema = CreateTaskArgs

    async def execute(self, project_id: str, title: str, description: str | None = None, priority: str = "MEDIUM", **kwargs: Any) -> dict[str, Any]:
        user_id: UUID | None = kwargs.get("user_id")
        db = kwargs.get("db")
        if not user_id or not db:
            return {"status": "error", "error": "Database session or user context unavailable"}

        try:
            p_uuid = UUID(project_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid project UUID: {project_id}"}

        task_in = TaskCreate(project_id=p_uuid, title=title, description=description, priority=priority)
        task = await TaskService.create_task(db=db, user_id=user_id, task_in=task_in)
        if not task:
            return {"status": "error", "error": f"Project {project_id} not found."}

        return {
            "status": "success",
            "task_id": str(task.id),
            "title": task.title,
            "task_status": task.status,
            "priority": task.priority,
            "message": f"Task '{task.title}' created.",
        }


# 4. Update Task Status Tool
class UpdateTaskStatusArgs(BaseModel):
    task_id: str = Field(..., description="UUID of the task")
    status: str = Field(..., description="'TODO', 'IN_PROGRESS', 'BLOCKED', 'REVIEW', 'DONE'")


class UpdateTaskStatusTool(BaseTool):
    name = "update_task_status"
    description = "Update the progress status of a task."
    permission = ToolPermission.WRITE
    args_schema = UpdateTaskStatusArgs

    async def execute(self, task_id: str, status: str, **kwargs: Any) -> dict[str, Any]:
        user_id: UUID | None = kwargs.get("user_id")
        db = kwargs.get("db")
        if not user_id or not db:
            return {"status": "error", "error": "Database session or user context unavailable"}

        try:
            t_uuid = UUID(task_id)
        except ValueError:
            return {"status": "error", "error": f"Invalid task UUID: {task_id}"}

        update_in = TaskUpdate(status=status)
        task = await TaskService.update_task(db=db, user_id=user_id, task_id=t_uuid, update_in=update_in)
        if not task:
            return {"status": "error", "error": f"Task {task_id} not found."}

        return {
            "status": "success",
            "task_id": str(task.id),
            "task_status": task.status,
            "message": f"Task '{task.title}' updated to {task.status}.",
        }
