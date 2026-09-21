import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.definitions import BUILTIN_AGENTS
from app.services.orchestrator_service import AgentService, OrchestratorService
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


@pytest.mark.asyncio
async def test_agent_service_seeding_and_runs(db_session: AsyncSession, test_user):
    """Test seeding 8 agents, fetching them, and logging agent runs."""
    # 1. Seeding
    await AgentService.seed_builtin_agents(db_session)
    agents = await AgentService.get_agents(db_session)
    assert len(agents) == 8

    # Verify agent roles
    types = {a.type for a in agents}
    assert "ORCHESTRATOR" in types
    assert "ARCHITECT" in types
    assert "CODER" in types
    assert "TESTER" in types
    assert "DEBUGGER" in types
    assert "REVIEWER" in types
    assert "DOCS" in types
    assert "RESEARCHER" in types

    # 2. Agent run logging
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Agent Run Project")
    )
    first_agent = agents[0]

    run = await AgentService.create_agent_run(
        db=db_session,
        agent_id=first_agent.id,
        project_id=proj.id,
        input_data={"task": "Plan development roadmap"},
    )
    assert run.status == "RUNNING"

    completed = await AgentService.complete_agent_run(
        db=db_session,
        run_id=run.id,
        output_data={"milestones": ["M1", "M2", "M3"]},
        status="COMPLETED",
    )
    assert completed.status == "COMPLETED"
    assert completed.output_data["milestones"] == ["M1", "M2", "M3"]

    # 3. List runs
    runs = await AgentService.list_agent_runs(db_session, project_id=proj.id)
    assert len(runs) >= 1
    assert runs[0].agent_name == first_agent.name


@pytest.mark.asyncio
async def test_orchestrator_service_pipeline(db_session: AsyncSession, test_user):
    """Test full multi-agent collaborative pipeline execution."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Orchestration Project")
    )

    # Decompose
    steps = OrchestratorService.decompose_goal("Build a user authentication API")
    assert len(steps) == 5
    assert steps[0]["agent_type"] == "ORCHESTRATOR"
    assert steps[1]["agent_type"] == "ARCHITECT"
    assert steps[2]["agent_type"] == "CODER"
    assert steps[3]["agent_type"] == "TESTER"
    assert steps[4]["agent_type"] == "REVIEWER"

    # Orchestrate
    res = await OrchestratorService.orchestrate_team(
        db=db_session,
        project_id=proj.id,
        goal="Build a user authentication API",
    )
    assert res.status == "COMPLETED"
    assert len(res.steps) == 5
    assert len(res.created_files) >= 3
    assert "docs/architecture.md" in res.created_files
    assert "src/main.py" in res.created_files
    assert "tests/test_main.py" in res.created_files
    assert "docs/code_review.md" in res.created_files


@pytest.mark.asyncio
async def test_self_healing_pipeline(db_session: AsyncSession, test_user):
    """Test autonomous self-healing test repair."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Self Healing Project")
    )

    # Test with command that passes
    res = await OrchestratorService.self_heal_pipeline(
        db=db_session,
        project_id=proj.id,
        test_command="python -c \"print('ALL_TESTS_PASS')\"",
        max_retries=2,
    )
    assert res.initial_passed is True
    assert res.resolved is True
    assert res.iterations == 0


@pytest.mark.asyncio
async def test_agents_api_endpoints(client: AsyncClient, test_user):
    """Test REST API endpoints for agent listing, runs, and team orchestration."""
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. GET /agents
    agents_res = await client.get("/api/v1/agents", headers=headers)
    assert agents_res.status_code == 200
    agent_list = agents_res.json()
    assert len(agent_list) == 8

    agent_id = agent_list[0]["id"]

    # 3. GET /agents/{id}
    detail_res = await client.get(f"/api/v1/agents/{agent_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == agent_list[0]["name"]

    # 4. Create project
    proj_res = await client.post(
        "/api/v1/projects",
        json={"name": "Agents API Test Project"},
        headers=headers,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 5. POST /agents/runs
    run_res = await client.post(
        "/api/v1/agents/runs",
        json={
            "agent_id": agent_id,
            "project_id": proj_id,
            "input_data": {"action": "Run initial analysis"},
        },
        headers=headers,
    )
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "COMPLETED"

    # 6. GET /agents/runs/history
    history_res = await client.get(
        f"/api/v1/agents/runs/history?project_id={proj_id}",
        headers=headers,
    )
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1

    # 7. POST /agents/orchestrate
    orch_res = await client.post(
        "/api/v1/agents/orchestrate",
        json={
            "project_id": proj_id,
            "goal": "Create a task tracking REST API",
        },
        headers=headers,
    )
    assert orch_res.status_code == 200
    orch_data = orch_res.json()
    assert orch_data["status"] == "COMPLETED"
    assert len(orch_data["steps"]) == 5

    # 8. POST /agents/self-heal
    heal_res = await client.post(
        "/api/v1/agents/self-heal",
        json={
            "project_id": proj_id,
            "test_command": "python -c \"print('OK')\"",
            "max_retries": 2,
        },
        headers=headers,
    )
    assert heal_res.status_code == 200
    assert heal_res.json()["resolved"] is True
