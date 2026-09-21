import asyncio
import os
import re
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.sandbox import (
    is_safe_command,
    get_project_workspace_dir,
    MAX_OUTPUT_BYTES,
)
from app.models.document import ProjectFile
from app.schemas.execution import (
    CommandExecutionResponse,
    ProcessInfo,
    ProcessLogChunk,
    PreviewUrlResponse,
)


class ExecutionService:
    @staticmethod
    async def sync_files_to_disk(db: AsyncSession, project_id: UUID, target_dir: Path) -> int:
        """Materialize ProjectFiles from database onto disk for subprocess execution."""
        stmt = select(ProjectFile).where(ProjectFile.project_id == project_id)
        result = await db.execute(stmt)
        files = result.scalars().all()

        synced_count = 0
        for f in files:
            file_path = (target_dir / f.path).resolve()
            # Ensure path safety
            if not str(file_path).startswith(str(target_dir)):
                continue

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f.content, encoding="utf-8")
            synced_count += 1

        return synced_count

    @staticmethod
    async def execute_command(
        project_id: UUID,
        command: str,
        timeout_seconds: int = 60,
        working_dir: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> CommandExecutionResponse:
        """Safely execute a shell command in project workspace and return output."""
        is_safe, reason = is_safe_command(command)
        if not is_safe:
            return CommandExecutionResponse(
                command=command,
                exit_code=1,
                stdout="",
                stderr=reason or "Forbidden command",
                duration_ms=0,
                timed_out=False,
                status="blocked",
                error=reason,
            )

        workspace_dir = get_project_workspace_dir(project_id)
        if working_dir:
            cwd_path = (workspace_dir / working_dir).resolve()
            if not str(cwd_path).startswith(str(workspace_dir)):
                return CommandExecutionResponse(
                    command=command,
                    exit_code=1,
                    stdout="",
                    stderr="Invalid working directory traversal",
                    duration_ms=0,
                    status="blocked",
                    error="Working directory outside project jail",
                )
            exec_dir = cwd_path
        else:
            exec_dir = workspace_dir

        # Sync files from DB to disk if DB session is provided
        if db:
            await ExecutionService.sync_files_to_disk(db, project_id, workspace_dir)

        start_time = time.monotonic()
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(exec_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            stdout = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            stderr = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            exit_code = process.returncode or 0

            return CommandExecutionResponse(
                command=command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                timed_out=False,
                status="success" if exit_code == 0 else "failed",
            )

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass

            return CommandExecutionResponse(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout_seconds} seconds",
                duration_ms=duration_ms,
                timed_out=True,
                status="timeout",
                error=f"Timeout of {timeout_seconds}s exceeded",
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return CommandExecutionResponse(
                command=command,
                exit_code=1,
                stdout="",
                stderr=str(exc),
                duration_ms=duration_ms,
                timed_out=False,
                status="failed",
                error=str(exc),
            )


class ManagedProcess:
    def __init__(
        self,
        process_id: str,
        project_id: str,
        command: str,
        process: asyncio.subprocess.Process,
        port: Optional[int] = None,
    ):
        self.process_id = process_id
        self.project_id = project_id
        self.command = command
        self.process = process
        self.status = "RUNNING"
        self.port = port
        self.started_at = datetime.now(timezone.utc)
        self.logs: deque[ProcessLogChunk] = deque(maxlen=1000)
        self._reader_tasks: list[asyncio.Task] = []

    def to_info(self) -> ProcessInfo:
        return ProcessInfo(
            process_id=self.process_id,
            project_id=self.project_id,
            command=self.command,
            pid=self.process.pid if self.process else None,
            status=self.status,
            port=self.port,
            started_at=self.started_at,
            logs_count=len(self.logs),
        )


PORT_REGEX = re.compile(r"(?:localhost|127\.0\.0\.1|port)\s*[:]?\s*(\d{4,5})", re.IGNORECASE)


class ProcessManager:
    def __init__(self):
        self._processes: dict[str, ManagedProcess] = {}

    async def start_process(
        self,
        project_id: UUID,
        command: str,
        port: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> ProcessInfo:
        """Launch a long-running background process (dev server, watcher, test runner)."""
        is_safe, reason = is_safe_command(command)
        if not is_safe:
            raise ValueError(f"Forbidden command: {reason}")

        workspace_dir = get_project_workspace_dir(project_id)
        if db:
            await ExecutionService.sync_files_to_disk(db, project_id, workspace_dir)

        process = await asyncio.create_subprocess_shell(
            command,
            cwd=str(workspace_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        process_id = str(uuid.uuid4())
        managed = ManagedProcess(
            process_id=process_id,
            project_id=str(project_id),
            command=command,
            process=process,
            port=port,
        )

        # Attach asynchronous stdout and stderr stream consumers
        async def read_stream(stream: asyncio.StreamReader, stream_name: str):
            while not stream.at_eof():
                try:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break
                    line_text = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                    managed.logs.append(
                        ProcessLogChunk(
                            line=line_text,
                            timestamp=datetime.now(timezone.utc),
                            stream=stream_name,  # type: ignore
                        )
                    )
                    # Try to detect port if not supplied
                    if not managed.port:
                        match = PORT_REGEX.search(line_text)
                        if match:
                            try:
                                detected = int(match.group(1))
                                if 1024 <= detected <= 65535:
                                    managed.port = detected
                            except ValueError:
                                pass
                except Exception:
                    break

            if managed.process and managed.process.returncode is not None:
                managed.status = "STOPPED" if managed.process.returncode == 0 else "FAILED"

        async def monitor_exit():
            await process.wait()
            managed.status = "STOPPED" if process.returncode == 0 else "FAILED"

        t1 = asyncio.create_task(read_stream(process.stdout, "stdout"))  # type: ignore
        t2 = asyncio.create_task(read_stream(process.stderr, "stderr"))  # type: ignore
        t3 = asyncio.create_task(monitor_exit())
        managed._reader_tasks.extend([t1, t2, t3])

        self._processes[process_id] = managed
        return managed.to_info()

    async def stop_process(self, process_id: str) -> bool:
        """Stop a running background process."""
        managed = self._processes.get(process_id)
        if not managed:
            return False

        if managed.process and managed.process.returncode is None:
            try:
                managed.process.terminate()
                # Give it a moment to terminate gracefully, else kill
                try:
                    await asyncio.wait_for(managed.process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    managed.process.kill()
                    await managed.process.wait()
            except Exception:
                pass

        managed.status = "STOPPED"
        for t in managed._reader_tasks:
            t.cancel()

        return True

    def get_process_logs(self, process_id: str, limit: int = 100) -> list[ProcessLogChunk]:
        """Fetch latest log chunks for a process."""
        managed = self._processes.get(process_id)
        if not managed:
            return []
        items = list(managed.logs)
        return items[-limit:] if limit > 0 else items

    def list_processes(self, project_id: Optional[UUID] = None) -> list[ProcessInfo]:
        """List background processes, optionally filtered by project_id."""
        results: list[ProcessInfo] = []
        for p in self._processes.values():
            if project_id is None or p.project_id == str(project_id):
                # Update status if completed
                if p.process and p.process.returncode is not None and p.status == "RUNNING":
                    p.status = "STOPPED" if p.process.returncode == 0 else "FAILED"
                results.append(p.to_info())
        return results

    def get_preview_url(self, project_id: UUID) -> PreviewUrlResponse:
        """Detect live preview URL based on running processes for a project."""
        for p in self._processes.values():
            if p.project_id == str(project_id) and p.status == "RUNNING" and p.port:
                return PreviewUrlResponse(
                    url=f"http://localhost:{p.port}",
                    is_active=True,
                    port=p.port,
                )
        return PreviewUrlResponse(url=None, is_active=False, port=None)


# Global singleton instance for the app lifecycle
process_manager = ProcessManager()
