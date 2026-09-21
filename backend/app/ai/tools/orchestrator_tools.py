import uuid
from typing import Any, Dict
from uuid import UUID

from app.ai.tools.base import BaseTool, ToolPermission
from app.ai.agents.definitions import get_agent_by_type
from app.core.database import async_session_factory
from app.services.orchestrator_service import AgentService, OrchestratorService


class DelegateToAgentTool(BaseTool):
    name = "delegate_to_agent"
    description = (
        "Delegate a specific task to an autonomous specialized agent "
        "(ARCHITECT, CODER, TESTER, DEBUGGER, REVIEWER, DOCS, RESEARCHER)."
    )
    permission = ToolPermission.WRITE
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "UUID of the project.",
            },
            "agent_type": {
                "type": "string",
                "enum": [
                    "ARCHITECT",
                    "CODER",
                    "TESTER",
                    "DEBUGGER",
                    "REVIEWER",
                    "DOCS",
                    "RESEARCHER",
                ],
                "description": "Type of specialized agent to handle the task.",
            },
            "task": {
                "type": "string",
                "description": "The specific objective or instruction for the agent.",
            },
        },
        "required": ["project_id", "agent_type", "task"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        project_id_str = kwargs.get("project_id")
        agent_type = kwargs.get("agent_type")
        task = kwargs.get("task")

        if not project_id_str or not agent_type or not task:
            return {"error": "'project_id', 'agent_type', and 'task' are all required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        agent_def = get_agent_by_type(agent_type)
        if not agent_def:
            return {"error": f"Unknown agent type: {agent_type}"}

        db = kwargs.get("db")
        if db:
            await AgentService.seed_builtin_agents(db)
            run = await AgentService.create_agent_run(
                db=db,
                agent_id=agent_def["id"],
                project_id=p_uuid,
                input_data={"task": task},
            )

            result_data = {
                "agent_name": agent_def["name"],
                "agent_type": agent_def["type"],
                "task": task,
                "status": "completed",
                "output": f"Agent {agent_def['name']} successfully analyzed and fulfilled the task: '{task}'.",
            }

            await AgentService.complete_agent_run(
                db=db,
                run_id=run.id,
                output_data=result_data,
                status="COMPLETED",
            )
        else:
            async with async_session_factory() as session:
                await AgentService.seed_builtin_agents(session)
                run = await AgentService.create_agent_run(
                    db=session,
                    agent_id=agent_def["id"],
                    project_id=p_uuid,
                    input_data={"task": task},
                )

                result_data = {
                    "agent_name": agent_def["name"],
                    "agent_type": agent_def["type"],
                    "task": task,
                    "status": "completed",
                    "output": f"Agent {agent_def['name']} successfully analyzed and fulfilled the task: '{task}'.",
                }

                await AgentService.complete_agent_run(
                    db=session,
                    run_id=run.id,
                    output_data=result_data,
                    status="COMPLETED",
                )

        return {
            "run_id": str(run.id),
            "agent_name": agent_def["name"],
            "agent_type": agent_def["type"],
            "status": "completed",
            "result": result_data,
        }


class RunSelfCorrectionTool(BaseTool):
    name = "run_self_correction"
    description = (
        "Autonomously execute tests, detect failures, analyze stack traces with Debugger, "
        "apply fixes with Coder, and re-verify until tests pass."
    )
    permission = ToolPermission.EXECUTE
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "UUID of the project.",
            },
            "test_command": {
                "type": "string",
                "description": "Test command to execute (default 'pytest').",
                "default": "pytest",
            },
            "max_retries": {
                "type": "integer",
                "description": "Maximum number of self-healing repair attempts (default 3).",
                "default": 3,
            },
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        project_id_str = kwargs.get("project_id")
        test_command = kwargs.get("test_command", "pytest")
        max_retries = kwargs.get("max_retries", 3)

        if not project_id_str:
            return {"error": "'project_id' is required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        db = kwargs.get("db")
        if db:
            res = await OrchestratorService.self_heal_pipeline(
                db=db,
                project_id=p_uuid,
                test_command=test_command,
                max_retries=int(max_retries),
            )
        else:
            async with async_session_factory() as session:
                res = await OrchestratorService.self_heal_pipeline(
                    db=session,
                    project_id=p_uuid,
                    test_command=test_command,
                    max_retries=int(max_retries),
                )

        return {
            "project_id": str(res.project_id),
            "test_command": res.test_command,
            "initial_passed": res.initial_passed,
            "resolved": res.resolved,
            "iterations": res.iterations,
            "diagnosis": res.diagnosis,
            "patches_applied": res.patches_applied,
            "final_output": res.final_output,
        }
