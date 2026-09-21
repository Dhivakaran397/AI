import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService
from app.services.file_service import FileService
from app.services.test_service import TestService
from app.services.debug_service import DebugService
from app.ai.tools.registry import tool_registry
from app.ai.tools.base import ToolPermission


SAMPLE_PYTEST_OUTPUT = """
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collected 3 items

tests/test_calculator.py::test_addition PASSED                           [ 33%]
tests/test_calculator.py::test_subtraction PASSED                        [ 66%]
tests/test_calculator.py::test_division_by_zero FAILED                   [100%]

=================================== FAILURES ===================================
_________________________ test_division_by_zero _________________________

    def test_division_by_zero():
>       assert divide(10, 0) == 0
E       ZeroDivisionError: division by zero

tests/test_calculator.py:15: ZeroDivisionError
=========================== short test summary info ===========================
FAILED tests/test_calculator.py::test_division_by_zero - ZeroDivisionError
========================= 1 failed, 2 passed in 0.12s =========================
"""

SAMPLE_TRACEBACK = """
Traceback (most recent call last):
  File "C:\\Users\\hp\\Desktop\\DAI\\workspace\\src\\calculator.py", line 12, in divide
    return a / b
ZeroDivisionError: division by zero
"""


@pytest.mark.asyncio
async def test_test_output_parsing():
    """Verify regex parsing of Pytest output formats."""
    cases, passed, failed, skipped = TestService.parse_test_output(SAMPLE_PYTEST_OUTPUT)
    assert passed == 2
    assert failed == 1
    assert skipped == 0
    assert len(cases) == 3

    f_case = next(c for c in cases if c.name == "test_division_by_zero")
    assert f_case.status == "FAILED"
    assert f_case.failure_trace is not None
    assert "ZeroDivisionError" in f_case.failure_trace


@pytest.mark.asyncio
async def test_test_generator_service(db_session: AsyncSession, test_user):
    """Verify test generation for Python source code."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="QA Testing Project")
    )
    # Create sample source file
    calc_code = (
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n\n"
        "def subtract(a: int, b: int) -> int:\n"
        "    return a - b\n"
    )
    await FileService.write_file(
        db_session, proj.id, "src/calculator.py", calc_code
    )

    gen_res = await TestService.generate_tests(
        db=db_session,
        project_id=proj.id,
        file_path="src/calculator.py",
        framework="pytest",
    )
    assert gen_res.test_file_path == "tests/test_calculator.py"
    assert "def test_add_success" in gen_res.test_code
    assert "def test_subtract_success" in gen_res.test_code
    assert gen_res.test_count_estimated >= 2


@pytest.mark.asyncio
async def test_debug_service_analysis_and_patch(db_session: AsyncSession, test_user):
    """Verify stack trace analysis, context extraction, and patch application."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Debug Project")
    )
    code = (
        "def divide(a: int, b: int) -> float:\n"
        "    return a / b\n"
    )
    await FileService.write_file(
        db_session, proj.id, "src/calculator.py", code
    )

    # 1. Analyze error
    diag = await DebugService.analyze_error(
        db=db_session,
        project_id=proj.id,
        raw_trace=SAMPLE_TRACEBACK,
    )
    assert diag.error_type == "ZeroDivisionError"
    assert "division by zero" in diag.error_message
    assert diag.culprit_line == 12 or diag.culprit_line is not None

    # 2. Apply patch
    fixed_code = (
        "def divide(a: int, b: int) -> float:\n"
        "    if b == 0:\n"
        "        return 0.0\n"
        "    return a / b\n"
    )
    patch_res = await DebugService.apply_patch(
        db=db_session,
        project_id=proj.id,
        file_path="src/calculator.py",
        patched_content=fixed_code,
        description="Fix ZeroDivisionError in divide function",
    )
    assert patch_res.success is True

    # Verify updated content in virtual filesystem
    updated_file = await FileService.read_file(db_session, proj.id, "src/calculator.py")
    assert updated_file is not None
    assert "if b == 0:" in updated_file.content


@pytest.mark.asyncio
async def test_testing_ai_tools(db_session: AsyncSession, test_user):
    """Verify generate_tests and analyze_error AI tools via ToolRegistry."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="Testing AI Tools Proj")
    )
    await FileService.write_file(
        db_session, proj.id, "app/utils.py", "def greet(name): return f'Hello, {name}'"
    )

    # 1. generate_tests tool
    gen_tool = tool_registry.get("generate_tests")
    assert gen_tool is not None
    assert gen_tool.permission == ToolPermission.WRITE

    gen_exec = await tool_registry.execute(
        "generate_tests",
        arguments={"project_id": str(proj.id), "file_path": "app/utils.py"},
        context={"db": db_session},
        allowed_permissions=[ToolPermission.WRITE],
    )
    assert gen_exec["status"] == "success"
    assert "test_code" in gen_exec["result"]

    # 2. analyze_error tool
    debug_tool = tool_registry.get("analyze_error")
    assert debug_tool is not None
    assert debug_tool.permission == ToolPermission.READ

    deb_exec = await tool_registry.execute(
        "analyze_error",
        arguments={"project_id": str(proj.id), "raw_trace": SAMPLE_TRACEBACK},
        context={"db": db_session},
        allowed_permissions=[ToolPermission.READ],
    )
    assert deb_exec["status"] == "success"
    assert deb_exec["result"]["error_type"] == "ZeroDivisionError"


@pytest.mark.asyncio
async def test_testing_api_endpoints(client: AsyncClient, auth_token: str, test_user, db_session: AsyncSession):
    """Verify /testing REST endpoints."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="API Testing Suite Proj")
    )
    await FileService.write_file(
        db_session, proj.id, "lib/math.py", "def square(x):\n    return x * x\n"
    )

    # 1. Generate tests endpoint
    gen_res = await client.post(
        f"/api/v1/projects/{proj.id}/tests/generate",
        json={"file_path": "lib/math.py", "framework": "pytest"},
        headers=headers,
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["target_file"] == "lib/math.py"
    assert "test_square_success" in gen_data["test_code"]

    # 2. Analyze error endpoint
    diag_res = await client.post(
        f"/api/v1/projects/{proj.id}/debug/analyze",
        json={"raw_trace": SAMPLE_TRACEBACK},
        headers=headers,
    )
    assert diag_res.status_code == 200
    diag_data = diag_res.json()
    assert diag_data["error_type"] == "ZeroDivisionError"

    # 3. Apply patch endpoint
    patch_res = await client.post(
        f"/api/v1/projects/{proj.id}/debug/apply-patch",
        json={
            "file_path": "lib/math.py",
            "patched_content": "def square(x):\n    return x ** 2\n",
            "description": "Optimized power of two",
        },
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["success"] is True
