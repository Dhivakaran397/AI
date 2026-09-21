from typing import Any, Dict
from uuid import UUID
from app.ai.tools.base import BaseTool, ToolPermission
from app.core.database import async_session_factory
from app.services.test_service import TestService
from app.services.debug_service import DebugService


class GenerateTestsTool(BaseTool):
    name = "generate_tests"
    description = (
        "Autonomously generate comprehensive unit/integration tests with mocks and edge cases "
        "for a given source code file."
    )
    permission = ToolPermission.WRITE
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "UUID of the project.",
            },
            "file_path": {
                "type": "string",
                "description": "Relative path of the source file to test.",
            },
            "framework": {
                "type": "string",
                "enum": ["pytest", "jest", "vitest"],
                "description": "Target test runner framework (default 'pytest').",
                "default": "pytest",
            },
            "extra_instructions": {
                "type": "string",
                "description": "Optional instructions regarding scenarios or mocks.",
            },
        },
        "required": ["project_id", "file_path"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        project_id_str = kwargs.get("project_id")
        file_path = kwargs.get("file_path")
        framework = kwargs.get("framework", "pytest")
        extra_instructions = kwargs.get("extra_instructions")

        if not project_id_str or not file_path:
            return {"error": "'project_id' and 'file_path' are required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        db = kwargs.get("db")
        if db:
            res = await TestService.generate_tests(
                db=db,
                project_id=p_uuid,
                file_path=file_path,
                framework=framework,
                extra_instructions=extra_instructions,
            )
        else:
            async with async_session_factory() as session:
                res = await TestService.generate_tests(
                    db=session,
                    project_id=p_uuid,
                    file_path=file_path,
                    framework=framework,
                    extra_instructions=extra_instructions,
                )

        return res.model_dump()


class RunTestSuiteTool(BaseTool):
    name = "run_test_suite"
    description = (
        "Execute project test runner in the sandbox and return structured test case matrix "
        "(passed, failed, skipped, duration, failure traces)."
    )
    permission = ToolPermission.EXECUTE
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "UUID of the project.",
            },
            "command": {
                "type": "string",
                "description": "Test command to run (default 'pytest').",
                "default": "pytest",
            },
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        project_id_str = kwargs.get("project_id")
        command = kwargs.get("command", "pytest")

        if not project_id_str:
            return {"error": "'project_id' is required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        db = kwargs.get("db")
        if db:
            res = await TestService.run_tests(
                db=db,
                project_id=p_uuid,
                command=command,
            )
        else:
            async with async_session_factory() as session:
                res = await TestService.run_tests(
                    db=session,
                    project_id=p_uuid,
                    command=command,
                )

        return {
            "project_id": str(res.project_id),
            "command": res.command,
            "total_count": res.total_count,
            "passed_count": res.passed_count,
            "failed_count": res.failed_count,
            "skipped_count": res.skipped_count,
            "duration_ms": res.duration_ms,
            "exit_code": res.exit_code,
            "cases": [c.model_dump() for c in res.cases],
        }


class AnalyzeErrorTool(BaseTool):
    name = "analyze_error"
    description = (
        "Parse a runtime exception or test failure stack trace, extract culprit line and file, "
        "and generate root cause diagnosis and suggested diff."
    )
    permission = ToolPermission.READ
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "UUID of the project.",
            },
            "raw_trace": {
                "type": "string",
                "description": "Raw terminal failure output or stack trace.",
            },
            "command": {
                "type": "string",
                "description": "Optional failing command context.",
            },
        },
        "required": ["project_id", "raw_trace"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        project_id_str = kwargs.get("project_id")
        raw_trace = kwargs.get("raw_trace")
        command = kwargs.get("command")

        if not project_id_str or not raw_trace:
            return {"error": "'project_id' and 'raw_trace' are required"}

        try:
            p_uuid = UUID(project_id_str)
        except ValueError:
            return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        db = kwargs.get("db")
        if db:
            res = await DebugService.analyze_error(
                db=db,
                project_id=p_uuid,
                raw_trace=raw_trace,
                command=command,
            )
        else:
            async with async_session_factory() as session:
                res = await DebugService.analyze_error(
                    db=session,
                    project_id=p_uuid,
                    raw_trace=raw_trace,
                    command=command,
                )

        return res.model_dump()
