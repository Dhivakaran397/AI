import io
import zipfile
import re
import json
from pathlib import Path
from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.models.document import ProjectFile
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus
from app.models.activity import Activity
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse
from app.schemas.task import TaskResponse
from app.schemas.activity import ActivityResponse
from app.services.activity_service import log_activity


# Valid State Transitions for the autonomous project builder
VALID_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.IDEA: {ProjectStatus.PLANNING, ProjectStatus.FAILED},
    ProjectStatus.PLANNING: {ProjectStatus.BUILDING, ProjectStatus.FAILED},
    ProjectStatus.BUILDING: {ProjectStatus.TESTING, ProjectStatus.FAILED},
    ProjectStatus.TESTING: {ProjectStatus.DEBUGGING, ProjectStatus.REVIEW, ProjectStatus.FAILED, ProjectStatus.COMPLETED},
    ProjectStatus.DEBUGGING: {ProjectStatus.BUILDING, ProjectStatus.TESTING, ProjectStatus.FAILED},
    ProjectStatus.REVIEW: {ProjectStatus.COMPLETED, ProjectStatus.BUILDING, ProjectStatus.FAILED},
    ProjectStatus.FAILED: {ProjectStatus.PLANNING, ProjectStatus.DEBUGGING, ProjectStatus.BUILDING},
    ProjectStatus.COMPLETED: {ProjectStatus.PLANNING, ProjectStatus.BUILDING},
}


class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, user_id: UUID, project_in: ProjectCreate) -> ProjectResponse:
        project = Project(
            user_id=user_id,
            name=project_in.name,
            description=project_in.description,
            status=ProjectStatus.IDEA,
            tech_stack=project_in.tech_stack,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # Log activity
        await log_activity(
            db=db,
            user_id=user_id,
            act_type="PROJECT_CREATED",
            title=f"Project '{project.name}' initialized",
            description=f"Status set to {project.status.value}",
            project_id=project.id,
        )

        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            tech_stack=project.tech_stack,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=0,
            completed_task_count=0,
        )

    @staticmethod
    async def get_projects(db: AsyncSession, user_id: UUID) -> list[ProjectResponse]:
        query = select(Project).where(Project.user_id == user_id).order_by(Project.updated_at.desc())
        result = await db.execute(query)
        projects = list(result.scalars().all())

        responses = []
        for p in projects:
            # Query task counts
            count_res = await db.execute(
                select(
                    func.count(Task.id),
                    func.count().filter(Task.status == TaskStatus.DONE),
                ).where(Task.project_id == p.id)
            )
            total_tasks, completed_tasks = count_res.first() or (0, 0)

            responses.append(
                ProjectResponse(
                    id=p.id,
                    user_id=p.user_id,
                    name=p.name,
                    description=p.description,
                    status=p.status.value,
                    tech_stack=p.tech_stack,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    task_count=total_tasks or 0,
                    completed_task_count=completed_tasks or 0,
                )
            )
        return responses

    @staticmethod
    async def get_project(db: AsyncSession, user_id: UUID, project_id: UUID) -> Project | None:
        result = await db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_project_detail(db: AsyncSession, user_id: UUID, project_id: UUID) -> ProjectDetailResponse | None:
        project = await ProjectService.get_project(db, user_id, project_id)
        if not project:
            return None

        # Fetch tasks
        tasks_res = await db.execute(
            select(Task).where(Task.project_id == project.id).order_by(Task.created_at.asc())
        )
        tasks = list(tasks_res.scalars().all())

        # Fetch recent activities for this project
        acts_res = await db.execute(
            select(Activity)
            .where(Activity.project_id == project.id)
            .order_by(Activity.created_at.desc())
            .limit(10)
        )
        activities = list(acts_res.scalars().all())

        completed = sum(1 for t in tasks if t.status == TaskStatus.DONE)

        return ProjectDetailResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            tech_stack=project.tech_stack,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=len(tasks),
            completed_task_count=completed,
            tasks=[
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
            ],
            recent_activities=[
                ActivityResponse(
                    id=a.id,
                    type=a.type,
                    title=a.title,
                    description=a.description,
                    project_id=a.project_id,
                    created_at=a.created_at,
                )
                for a in activities
            ],
        )

    @staticmethod
    async def update_project(
        db: AsyncSession, user_id: UUID, project_id: UUID, update_in: ProjectUpdate
    ) -> ProjectResponse | None:
        project = await ProjectService.get_project(db, user_id, project_id)
        if not project:
            return None

        old_status = project.status
        if update_in.name is not None:
            project.name = update_in.name
        if update_in.description is not None:
            project.description = update_in.description
        if update_in.tech_stack is not None:
            project.tech_stack = update_in.tech_stack

        if update_in.status is not None:
            new_status = ProjectStatus(update_in.status.upper())
            project.status = new_status

            if old_status != new_status:
                await log_activity(
                    db=db,
                    user_id=user_id,
                    act_type="STATUS_CHANGED",
                    title=f"Project '{project.name}' moved to {new_status.value}",
                    description=f"Transitioned from {old_status.value} -> {new_status.value}",
                    project_id=project.id,
                )

        await db.commit()
        await db.refresh(project)

        count_res = await db.execute(
            select(
                func.count(Task.id),
                func.count().filter(Task.status == TaskStatus.DONE),
            ).where(Task.project_id == project.id)
        )
        total_tasks, completed_tasks = count_res.first() or (0, 0)

        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            tech_stack=project.tech_stack,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=total_tasks or 0,
            completed_task_count=completed_tasks or 0,
        )

    @staticmethod
    async def delete_project(db: AsyncSession, user_id: UUID, project_id: UUID) -> bool:
        project = await ProjectService.get_project(db, user_id, project_id)
        if not project:
            return False

        # Cascade delete tasks & activities
        await db.execute(delete(Task).where(Task.project_id == project_id))
        await db.execute(delete(Activity).where(Activity.project_id == project_id))
        await db.delete(project)
        await db.commit()
        return True

    @staticmethod
    async def export_project_zip(db: AsyncSession, project: Project) -> tuple[io.BytesIO, str]:
        """Bundle all project workspace files into a clean, downloadable ZIP archive."""
        # 1. Fetch files stored in database
        query = select(ProjectFile).where(ProjectFile.project_id == project.id)
        result = await db.execute(query)
        db_files: dict[str, str] = {
            pf.path.replace("\\", "/").lstrip("/"): pf.content or ""
            for pf in result.scalars().all()
        }

        # 2. Check disk workspace for any additional generated assets or files
        workspace_dir = Path("workspaces") / str(project.id)
        if workspace_dir.exists() and workspace_dir.is_dir():
            for disk_file in workspace_dir.rglob("*"):
                if disk_file.is_file():
                    rel_path = disk_file.relative_to(workspace_dir).as_posix().lstrip("/")
                    if rel_path not in db_files:
                        try:
                            db_files[rel_path] = disk_file.read_text(encoding="utf-8", errors="replace")
                        except Exception:
                            pass

        safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", project.name).strip("_") or "project"

        # 3. If there is an index.html and no package.json, generate package.json for quick npm start
        if "index.html" in db_files and "package.json" not in db_files:
            pkg_json = {
                "name": safe_name.lower().replace("_", "-"),
                "version": "1.0.0",
                "description": project.description or f"{project.name} built with DAI",
                "scripts": {
                    "start": "npx serve .",
                    "dev": "npx serve ."
                },
                "keywords": ["dai", "ai-generated"],
                "author": "DAI Autonomous Engine",
                "license": "MIT"
            }
            db_files["package.json"] = json.dumps(pkg_json, indent=2)

        # 4. If no README.md exists, generate comprehensive setup instructions for VS Code
        if "README.md" not in db_files:
            db_files["README.md"] = rf"""# {project.name}

{project.description or "Generated autonomously by DAI Studio AI."}

---

## 🚀 How to Run in VS Code

### Method 1: VS Code Live Server (Recommended)
1. Open this folder in **VS Code** (`File > Open Folder...`).
2. If you have the **Live Server** extension installed:
   - Right-click `index.html` in the file explorer.
   - Click **"Open with Live Server"**.
   - Your application will open automatically in your browser at `http://127.0.0.1:5500`.

### Method 2: Node.js / NPX Serve
1. Open the integrated terminal in VS Code (`Ctrl + \`` or `Ctrl + ~`).
2. Run:
   ```bash
   npx serve .
   ```
3. Open `http://localhost:3000` in your browser.

### Method 3: Direct Browser Open
- Double-click `index.html` to launch it immediately in Google Chrome, Microsoft Edge, or Firefox.

---
*Created with DAI Autonomous Studio*
"""

        # 5. Pack into in-memory ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in db_files.items():
                arcname = f"{safe_name}/{path}"
                zf.writestr(arcname, content.encode("utf-8"))

        zip_buffer.seek(0)
        return zip_buffer, f"{safe_name}.zip"

