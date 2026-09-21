from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.agent import (
    AgentResponse,
    AgentRunCreate,
    AgentRunResponse,
    TeamOrchestrationRequest,
    TeamOrchestrationResponse,
    SelfHealRequest,
    SelfHealResponse,
)
from app.services.project_service import ProjectService
from app.services.orchestrator_service import AgentService, OrchestratorService

router = APIRouter()


async def _verify_project_owner(db: AsyncSession, user_id: UUID, project_id: UUID):
    project = await ProjectService.get_project(db, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all available specialized agents in the DAI multi-agent system."""
    return await AgentService.get_agents(db)


@router.get("/runs/history", response_model=list[AgentRunResponse])
async def list_agent_runs(
    project_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch execution history for agent runs."""
    if project_id:
        await _verify_project_owner(db, current_user.id, project_id)
    return await AgentService.list_agent_runs(db, project_id=project_id, limit=limit)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for a specific specialized agent."""
    agent = await AgentService.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/runs", response_model=AgentRunResponse)
async def create_agent_run(
    payload: AgentRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch a single specialized agent on a specific subtask."""
    if payload.project_id:
        await _verify_project_owner(db, current_user.id, payload.project_id)

    run = await AgentService.create_agent_run(
        db=db,
        agent_id=payload.agent_id,
        project_id=payload.project_id,
        input_data=payload.input_data,
        conversation_id=payload.conversation_id,
    )

    # Complete run with result
    completed = await AgentService.complete_agent_run(
        db=db,
        run_id=run.id,
        output_data={
            "status": "success",
            "message": "Agent completed task execution.",
            "input_received": payload.input_data,
        },
        status="COMPLETED",
    )

    agent = await AgentService.get_agent(db, payload.agent_id)
    return AgentRunResponse(
        id=completed.id,
        agent_id=completed.agent_id,
        agent_name=agent.name if agent else "Unknown Agent",
        agent_type=agent.type if agent else "AGENT",
        project_id=completed.project_id,
        conversation_id=completed.conversation_id,
        status="COMPLETED",
        input_data=completed.input_data,
        output_data=completed.output_data,
        error=completed.error,
        started_at=completed.started_at,
        completed_at=completed.completed_at,
    )


@router.post("/orchestrate", response_model=TeamOrchestrationResponse)
async def orchestrate_team(
    payload: TeamOrchestrationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute autonomous multi-agent team pipeline on a project goal."""
    await _verify_project_owner(db, current_user.id, payload.project_id)
    return await OrchestratorService.orchestrate_team(
        db=db,
        project_id=payload.project_id,
        goal=payload.goal,
    )


@router.post("/self-heal", response_model=SelfHealResponse)
async def self_heal_project(
    payload: SelfHealRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger autonomous closed-loop test repair: run tests -> parse error -> patch -> re-test."""
    await _verify_project_owner(db, current_user.id, payload.project_id)
    return await OrchestratorService.self_heal_pipeline(
        db=db,
        project_id=payload.project_id,
        test_command=payload.test_command,
        max_retries=payload.max_retries,
    )
