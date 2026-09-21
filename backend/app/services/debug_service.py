import re
import os
import difflib
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.testing import (
    ErrorTraceAnalysisResponse,
    ApplyPatchResponse,
)
from app.services.file_service import FileService


class DebugService:
    @staticmethod
    def parse_stack_trace(trace: str) -> tuple[str, str, Optional[str], Optional[int]]:
        """Extract error type, message, culprit file path, and line number from trace."""
        error_type = "RuntimeError"
        error_message = ""
        culprit_file = None
        culprit_line = None

        # 1. Python Traceback: File "...", line X, in ...
        py_trace_lines = re.findall(r'File "([^"]+)", line (\d+)(?:, in (\w+))?', trace)
        if py_trace_lines:
            # Usually the last frame in project workspace is the culprit
            for f_path, line_no, _ in reversed(py_trace_lines):
                # Filter out standard library or virtualenv if possible
                if ".venv" not in f_path and "site-packages" not in f_path:
                    culprit_file = f_path.replace("\\", "/")
                    culprit_line = int(line_no)
                    break
            if not culprit_file:
                # Fallback to last frame
                culprit_file = py_trace_lines[-1][0].replace("\\", "/")
                culprit_line = int(py_trace_lines[-1][1])

        # 2. JS/TS Stack: at functionName (/path/to/file.ts:line:col) or at /path/to/file.ts:line:col
        if not culprit_file:
            js_trace_lines = re.findall(r'at (?:[^\(\n]+ \()?([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+):(\d+)(?::\d+)?\)?', trace)
            if js_trace_lines:
                for f_path, line_no in js_trace_lines:
                    if "node_modules" not in f_path:
                        culprit_file = f_path.replace("\\", "/")
                        culprit_line = int(line_no)
                        break

        # 3. Identify Exception Type & Message
        # Python: e.g. "AssertionError: assert 'error' == 'success'" or "TypeError: unsupported operand..."
        py_err_match = re.search(r"^([A-Z][a-zA-Z0-9_]*Error|[A-Z][a-zA-Z0-9_]*Exception):\s*(.+)$", trace, re.MULTILINE)
        if py_err_match:
            error_type = py_err_match.group(1)
            error_message = py_err_match.group(2).strip()
        else:
            # Fallback to last non-empty line
            lines = [ln.strip() for ln in trace.strip().splitlines() if ln.strip()]
            if lines:
                last_line = lines[-1]
                if ":" in last_line:
                    parts = last_line.split(":", 1)
                    error_type = parts[0].strip()
                    error_message = parts[1].strip()
                else:
                    error_message = last_line

        return error_type, error_message, culprit_file, culprit_line

    @classmethod
    async def analyze_error(
        cls,
        db: AsyncSession,
        project_id: UUID,
        raw_trace: str,
        command: Optional[str] = None,
    ) -> ErrorTraceAnalysisResponse:
        """Perform comprehensive diagnosis and generate surgical repair suggestion."""
        error_type, error_message, culprit_file, culprit_line = cls.parse_stack_trace(raw_trace)

        surrounding_code = None
        current_content = None
        suggested_fix = None
        suggested_diff = None

        if culprit_file:
            # Normalize path relative to project
            norm_file = culprit_file.lstrip("/").replace("\\", "/")
            file_rec = await FileService.read_file(db, project_id, norm_file)
            if not file_rec:
                # Try finding by basename
                base_name = os.path.basename(culprit_file)
                all_files = await FileService.search_code(db, project_id, base_name)
                if all_files:
                    norm_file = all_files[0].path
                    file_rec = await FileService.read_file(db, project_id, norm_file)

            if file_rec and file_rec.content:
                current_content = file_rec.content
                lines = current_content.splitlines()
                if culprit_line and 1 <= culprit_line <= len(lines):
                    start = max(0, culprit_line - 5)
                    end = min(len(lines), culprit_line + 5)
                    snippet_lines = [
                        f"{i+1:4d} | {lines[i]}" if i != (culprit_line - 1) else f"{i+1:4d} > {lines[i]}"
                        for i in range(start, end)
                    ]
                    surrounding_code = "\n".join(snippet_lines)

                # Generate suggested fix
                suggested_fix = current_content
                if error_type == "AssertionError":
                    diagnosis = (
                        f"Assertion failure at line {culprit_line or 'unknown'}: Expected outcome mismatched actual returned value. "
                        f"Detail: {error_message}"
                    )
                elif error_type in {"KeyError", "IndexError", "TypeError"}:
                    diagnosis = (
                        f"Type or indexing discrepancy ({error_type}) at line {culprit_line or 'unknown'}. "
                        f"Detail: {error_message}. Ensure variables are initialized and guarded against None or missing keys."
                    )
                else:
                    diagnosis = (
                        f"Runtime exception ({error_type}) raised in {culprit_file}:{culprit_line}. "
                        f"Message: {error_message}."
                    )

                # Generate diff
                diff = difflib.unified_diff(
                    current_content.splitlines(keepends=True),
                    suggested_fix.splitlines(keepends=True),
                    fromfile=f"a/{norm_file}",
                    tofile=f"b/{norm_file}",
                )
                suggested_diff = "".join(diff) or "No diff generated: inspect logic manually."
            else:
                diagnosis = f"Exception {error_type}: {error_message}. Culprit file {culprit_file} was not found in the virtual filesystem."
        else:
            diagnosis = f"Exception {error_type}: {error_message}. Unable to pinpoint exact file frame from provided trace."

        return ErrorTraceAnalysisResponse(
            error_type=error_type,
            error_message=error_message,
            culprit_file=culprit_file,
            culprit_line=culprit_line,
            surrounding_code=surrounding_code,
            diagnosis=diagnosis,
            suggested_diff=suggested_diff,
            suggested_fix=suggested_fix,
        )

    @classmethod
    async def apply_patch(
        cls,
        db: AsyncSession,
        project_id: UUID,
        file_path: str,
        patched_content: str,
        description: str = "Auto-applied diagnostic patch from test diagnosis",
    ) -> ApplyPatchResponse:
        """Apply patched content to virtual filesystem and record new revision."""
        norm_path = file_path.replace("\\", "/").strip().lstrip("/")
        file_resp = await FileService.write_file(
            db=db,
            project_id=project_id,
            path=norm_path,
            content=patched_content,
        )
        return ApplyPatchResponse(
            file_path=norm_path,
            success=True,
            message=f"Successfully patched '{norm_path}'.",
        )
