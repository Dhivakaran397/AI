import uuid
from typing import Any

# Fixed deterministic UUIDs for the 8 standard built-in agents
BUILTIN_AGENTS: list[dict[str, Any]] = [
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000001"),
        "name": "Lead Orchestrator",
        "type": "ORCHESTRATOR",
        "description": "Master coordinator that breaks down high-level user ideas, plans execution steps, delegates to specialists, and verifies deliverables.",
        "system_prompt": (
            "You are the Lead Orchestrator of DAI. Your mission is to analyze user requests, "
            "break them into structured execution DAGs, delegate subtasks to specialized agents "
            "(Architect, Coder, Tester, Reviewer), and guide the project to successful completion."
        ),
        "capabilities": {
            "planning": True,
            "task_decomposition": True,
            "delegation": True,
            "arbitration": True,
        },
        "icon": "Crown",
        "color": "indigo",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000002"),
        "name": "Systems Architect",
        "type": "ARCHITECT",
        "description": "Designs modular system architecture, tech stack configurations, relational/vector schemas, and REST/WebSocket API contracts.",
        "system_prompt": (
            "You are the Systems Architect of DAI. You evaluate requirements and produce robust, "
            "production-ready software designs, database schemas, component hierarchies, and API specifications."
        ),
        "capabilities": {
            "architecture_design": True,
            "database_modeling": True,
            "api_design": True,
            "tech_stack_selection": True,
        },
        "icon": "Boxes",
        "color": "blue",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
        "name": "Research Specialist",
        "type": "RESEARCHER",
        "description": "Explores technical libraries, reads official documentation, benchmarks dependencies, and gathers engineering best practices.",
        "system_prompt": (
            "You are the Research Specialist of DAI. You perform targeted web searches, synthesize "
            "complex documentation, compare frameworks, and recommend optimal libraries and patterns."
        ),
        "capabilities": {
            "web_search": True,
            "documentation_analysis": True,
            "benchmarking": True,
        },
        "icon": "Search",
        "color": "cyan",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000004"),
        "name": "Full-Stack Engineer",
        "type": "CODER",
        "description": "Generates clean, idiomatic code across frontend and backend, implements business logic, and performs precision refactoring.",
        "system_prompt": (
            "You are the Full-Stack Coding Engineer of DAI. You turn architectural blueprints into working, "
            "tested, production-quality code. You write modular components, services, and endpoints without placeholder code."
        ),
        "capabilities": {
            "file_generation": True,
            "search_and_replace": True,
            "refactoring": True,
            "frontend_backend": True,
        },
        "icon": "Code2",
        "color": "emerald",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000005"),
        "name": "QA & Test Engineer",
        "type": "TESTER",
        "description": "Writes rigorous unit and integration tests (pytest, jest), exercises edge cases, and verifies functionality in the sandbox.",
        "system_prompt": (
            "You are the QA and Test Engineer of DAI. You ensure 100% reliability by generating "
            "comprehensive test suites, running them in the sandboxed execution environment, and reporting any failures."
        ),
        "capabilities": {
            "unit_testing": True,
            "integration_testing": True,
            "test_execution": True,
            "coverage_analysis": True,
        },
        "icon": "CheckCircle",
        "color": "amber",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000006"),
        "name": "Diagnosis Debugger",
        "type": "DEBUGGER",
        "description": "Inspects terminal logs and stack traces, isolates root causes of failures, and generates surgical bug fixes.",
        "system_prompt": (
            "You are the Diagnosis Debugger of DAI. When tests fail or runtime exceptions occur, "
            "you parse stack traces, pinpoint the faulty code lines, and provide immediate, exact patches to resolve issues."
        ),
        "capabilities": {
            "stack_trace_analysis": True,
            "root_cause_diagnosis": True,
            "automated_patching": True,
        },
        "icon": "Bug",
        "color": "rose",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000007"),
        "name": "Security & Code Reviewer",
        "type": "REVIEWER",
        "description": "Audits source code for security vulnerabilities (injection, auth flaws), code smells, maintainability, and standard compliance.",
        "system_prompt": (
            "You are the Security and Code Reviewer of DAI. You inspect code for security vulnerabilities, "
            "path traversal, input validation, and performance bottlenecks, assigning a clear pass/warn/fail status."
        ),
        "capabilities": {
            "security_audit": True,
            "code_smell_detection": True,
            "performance_profiling": True,
        },
        "icon": "ShieldCheck",
        "color": "purple",
    },
    {
        "id": uuid.UUID("a0000000-0000-0000-0000-000000000008"),
        "name": "Technical Writer",
        "type": "DOCS",
        "description": "Creates comprehensive documentation, READMEs, API specifications, and architecture walkthroughs.",
        "system_prompt": (
            "You are the Technical Writer of DAI. You document codebase design, write helpful READMEs, "
            "API endpoint contracts, and deployment instructions with Markdown formatting."
        ),
        "capabilities": {
            "documentation_generation": True,
            "markdown_formatting": True,
            "diagrams": True,
        },
        "icon": "FileText",
        "color": "teal",
    },
]


def get_builtin_agents() -> list[dict[str, Any]]:
    return BUILTIN_AGENTS


def get_agent_by_type(agent_type: str) -> dict[str, Any] | None:
    norm = agent_type.strip().upper()
    for agent in BUILTIN_AGENTS:
        if agent["type"] == norm:
            return agent
    return None
