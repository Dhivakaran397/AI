import pytest
from uuid import uuid4
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


@pytest.mark.asyncio
async def test_project_lifecycle(db_session, test_user):
    user_id = test_user.id
    # 1. Create project
    proj_in = ProjectCreate(
        name="AI Analytics Dashboard",
        description="Real-time analytics builder",
        tech_stack={"frontend": "Next.js", "backend": "FastAPI"},
    )
    project = await ProjectService.create_project(db_session, user_id, proj_in)
    assert project.id is not None
    assert project.name == "AI Analytics Dashboard"
    assert project.status == "IDEA"

    # 2. Add tasks to project
    t1 = await TaskService.create_task(
        db_session, user_id, TaskCreate(project_id=project.id, title="Setup Database Schema", priority="HIGH")
    )
    t2 = await TaskService.create_task(
        db_session, user_id, TaskCreate(project_id=project.id, title="Implement Auth", priority="CRITICAL")
    )
    assert t1 is not None
    assert t2 is not None

    # 3. Advance state machine: IDEA -> PLANNING
    up1 = await ProjectService.update_project(
        db_session, user_id, project.id, ProjectUpdate(status="PLANNING")
    )
    assert up1.status == "PLANNING"

    # 4. Advance: PLANNING -> BUILDING
    up2 = await ProjectService.update_project(
        db_session, user_id, project.id, ProjectUpdate(status="BUILDING")
    )
    assert up2.status == "BUILDING"

    # 5. Complete a task
    t1_updated = await TaskService.update_task(
        db_session, user_id, t1.id, TaskUpdate(status="DONE")
    )
    assert t1_updated.status == "DONE"

    # 6. Check Project Detail with tasks and stats
    detail = await ProjectService.get_project_detail(db_session, user_id, project.id)
    assert detail is not None
    assert detail.task_count == 2
    assert detail.completed_task_count == 1
    assert len(detail.tasks) == 2

    # 7. Delete Project (cascade check)
    deleted = await ProjectService.delete_project(db_session, user_id, project.id)
    assert deleted is True

    # Confirm tasks were cleaned up
    remaining_tasks = await TaskService.get_tasks(db_session, user_id, project_id=project.id)
    assert len(remaining_tasks) == 0


@pytest.mark.asyncio
async def test_project_api_endpoints(client, auth_token):
    # 1. Create project via API
    resp = await client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Cloud Deployment Tool",
            "description": "Multi-cloud infrastructure manager",
            "tech_stack": {"infra": "Terraform", "cloud": "AWS"},
        },
    )
    assert resp.status_code == 201
    proj_data = resp.json()
    proj_id = proj_data["id"]
    assert proj_data["status"] == "IDEA"

    # 2. Create task via API
    t_resp = await client.post(
        "/api/v1/tasks",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "project_id": proj_id,
            "title": "Configure AWS IAM credentials",
            "priority": "HIGH",
        },
    )
    assert t_resp.status_code == 201
    task_id = t_resp.json()["id"]

    # 3. Update task to IN_PROGRESS
    patch_t = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"status": "IN_PROGRESS"},
    )
    assert patch_t.status_code == 200
    assert patch_t.json()["status"] == "IN_PROGRESS"

    # 4. Get Project Detail
    det_resp = await client.get(
        f"/api/v1/projects/{proj_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert det_resp.status_code == 200
    det_data = det_resp.json()
    assert len(det_data["tasks"]) == 1

    # 5. Delete project
    del_resp = await client.delete(
        f"/api/v1/projects/{proj_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert del_resp.status_code == 200
