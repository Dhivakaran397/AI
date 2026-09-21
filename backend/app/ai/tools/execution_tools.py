import uuid
from typing import Any, Dict
from uuid import UUID

from app.ai.tools.base import BaseTool, ToolPermission
from app.services.execution_service import ExecutionService, process_manager


class ExecuteCommandTool(BaseTool):
    name = "execute_command"
    description = (
        "Execute a shell command in the project workspace (e.g., npm test, pytest, "
        "npm run build, pip install, ls). Enforces security filters to block hazardous commands."
    )
    permission = ToolPermission.EXECUTE
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "UUID of the project in which to run the command.",
            },
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Execution timeout in seconds (default 60, maximum 300).",
                "default": 60,
            },
            "working_dir": {
                "type": "string",
                "description": "Optional subdirectory within the project workspace.",
            },
        },
        "required": ["project_id", "command"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        project_id_str = kwargs.get("project_id")
        command = kwargs.get("command")
        timeout_seconds = kwargs.get("timeout_seconds", 60)
        working_dir = kwargs.get("working_dir")

        if not project_id_str or not command:
            return {"error": "Both 'project_id' and 'command' are required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        result = await ExecutionService.execute_command(
            project_id=p_uuid,
            command=command,
            timeout_seconds=int(timeout_seconds),
            working_dir=working_dir,
        )

        return {
            "command": result.command,
            "exit_code": result.exit_code,
            "status": result.status,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "timed_out": result.timed_out,
            "error": result.error,
        }


class ManageProcessTool(BaseTool):
    name = "manage_process"
    description = (
        "Manage background processes (e.g. dev servers, test watchers). "
        "Actions: 'start' (launch process), 'stop' (kill process), 'logs' (tail logs), 'list' (list running)."
    )
    permission = ToolPermission.EXECUTE
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "stop", "logs", "list"],
                "description": "Action to perform on processes.",
            },
            "project_id": {
                "type": "string",
                "description": "UUID of the project.",
            },
            "command": {
                "type": "string",
                "description": "Shell command to run (required for 'start').",
            },
            "process_id": {
                "type": "string",
                "description": "Process ID (required for 'stop' and 'logs').",
            },
            "port": {
                "type": "integer",
                "description": "Optional port number expected for web servers.",
            },
        },
        "required": ["action", "project_id"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        project_id_str = kwargs.get("project_id")

        if not action or not project_id_str:
            return {"error": "Both 'action' and 'project_id' are required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID: {project_id_str}"}

        if action == "start":
            cmd = kwargs.get("command")
            if not cmd:
                return {"error": "'command' is required to start a process"}
            port = kwargs.get("port")
            try:
                proc = await process_manager.start_process(project_id=p_uuid, command=cmd, port=port)
                return {
                    "action": "start",
                    "status": "started",
                    "process": proc.model_dump(mode="json"),
                }
            except Exception as exc:
                return {"error": f"Failed to start process: {exc}"}

        elif action == "stop":
            proc_id = kwargs.get("process_id")
            if not proc_id:
                return {"error": "'process_id' is required to stop a process"}
            stopped = await process_manager.stop_process(proc_id)
            return {"action": "stop", "stopped": stopped, "process_id": proc_id}

        elif action == "logs":
            proc_id = kwargs.get("process_id")
            if not proc_id:
                return {"error": "'process_id' is required to fetch logs"}
            logs = process_manager.get_process_logs(proc_id, limit=50)
            return {
                "action": "logs",
                "process_id": proc_id,
                "logs": [log.model_dump(mode="json") for log in logs],
            }

        elif action == "list":
            procs = process_manager.list_processes(project_id=p_uuid)
            return {
                "action": "list",
                "processes": [p.model_dump(mode="json") for p in procs],
            }

        return {"error": f"Unknown action: {action}"}
