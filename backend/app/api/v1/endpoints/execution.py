import asyncio
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.execution import (
    CommandExecutionRequest,
    CommandExecutionResponse,
    ProcessStartRequest,
    ProcessInfo,
    ProcessLogResponse,
    PreviewUrlResponse,
)
from app.services.project_service import ProjectService
from app.services.execution_service import ExecutionService, process_manager

router = APIRouter()


async def _verify_project_owner(db: AsyncSession, user_id: UUID, project_id: UUID):
    project = await ProjectService.get_project(db, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/execute", response_model=CommandExecutionResponse)
async def execute_command(
    project_id: UUID,
    payload: CommandExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Safely execute a one-off shell command in project directory and return result."""
    await _verify_project_owner(db, current_user.id, project_id)
    return await ExecutionService.execute_command(
        project_id=project_id,
        command=payload.command,
        timeout_seconds=payload.timeout_seconds,
        working_dir=payload.working_dir,
        db=db,
    )


@router.get("/{project_id}/processes", response_model=list[ProcessInfo])
async def list_processes(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List background processes for a project."""
    await _verify_project_owner(db, current_user.id, project_id)
    return process_manager.list_processes(project_id=project_id)


@router.post("/{project_id}/processes", response_model=ProcessInfo)
async def start_process(
    project_id: UUID,
    payload: ProcessStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a long-running background process (e.g. dev server, watcher)."""
    await _verify_project_owner(db, current_user.id, project_id)
    try:
        return await process_manager.start_process(
            project_id=project_id,
            command=payload.command,
            port=payload.port,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/processes/{process_id}/stop")
async def stop_process(
    project_id: UUID,
    process_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop a running background process."""
    await _verify_project_owner(db, current_user.id, project_id)
    stopped = await process_manager.stop_process(process_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="Process not found or already stopped")
    return {"success": True, "process_id": process_id}


@router.get("/{project_id}/processes/{process_id}/logs", response_model=ProcessLogResponse)
async def get_process_logs(
    project_id: UUID,
    process_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch recent logs for a background process."""
    await _verify_project_owner(db, current_user.id, project_id)
    logs = process_manager.get_process_logs(process_id, limit=limit)
    return ProcessLogResponse(process_id=process_id, logs=logs)


@router.get("/{project_id}/preview/url", response_model=PreviewUrlResponse)
async def get_preview_url(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get active live preview URL detected from running background processes."""
    await _verify_project_owner(db, current_user.id, project_id)
    return process_manager.get_preview_url(project_id)


@router.websocket("/{project_id}/terminal/ws")
async def terminal_websocket(websocket: WebSocket, project_id: UUID):
    """Interactive bidirectional terminal WebSocket session."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "execute":
                cmd = data.get("command", "")
                await websocket.send_json({"type": "output", "data": f"\r\n$ {cmd}\r\n"})
                res = await ExecutionService.execute_command(
                    project_id=project_id,
                    command=cmd,
                    timeout_seconds=60,
                )
                if res.stdout:
                    await websocket.send_json({"type": "output", "data": res.stdout})
                if res.stderr:
                    await websocket.send_json({"type": "output", "data": res.stderr})
                await websocket.send_json({"type": "exit", "code": res.exit_code, "status": res.status})

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
