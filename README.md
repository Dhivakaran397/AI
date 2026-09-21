# ?? DAI — Personal Intelligence & Project Builder

> **DAI** is an autonomous, full-stack personal AI software engineer and intelligence platform. It merges multi-agent swarms, sandbox code execution, a Monaco IDE workspace, real-time terminals, automated test generators, self-healing diagnostic loops, and dense RAG knowledge indexing into a unified product.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16_Turbopack-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-pgvector-336791?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker_Compose-Orchestrated-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![Tests](https://img.shields.io/badge/Pytest-38%2F38_Passing-success)](#)

---

## ??? Architecture Overview

`
+-----------------------------------------------------------------------------+
|                          Next.js 16 Frontend App Router                     |
|                                                                             |
|  [Home Dashboard]  [Chat & Tools]  [Projects & Tasks]  [Monaco Studio IDE]  |
|  [Agent Swarm]     [QA & Tests]    [Knowledge RAG]     [Settings & Audit]   |
+-----------------------------------------------------------------------------+
                                      |
                           REST APIs & WebSockets
                                      |
+-----------------------------------------------------------------------------+
|                         FastAPI ASGI Async Backend                          |
|                                                                             |
|  [Auth & JWT]    [State Machine]   [Tool Registry]   [Execution Sandbox]    |
|  [RAG Embedder]  [Agent Swarm]     [Self-Healing]    [Process Daemons]      |
+-----------------------------------------------------------------------------+
          |                                  |                     |
          v                                  v                     v
+-----------------------+        +----------------------+  +------------------+
|     PostgreSQL 16     |        |       Redis 7        |  | Isolated Project |
|  + pgvector (Dense)   |        |  (State, Ephemeral   |  | Execution Root   |
| (Relational + Chunks) |        |    Traces, Cache)    |  |  (Subprocesses)  |
+-----------------------+        +----------------------+  +------------------+
`

---

## ? Key Highlights & Core Capabilities

1. **Multi-Agent Swarm**: 8 specialized autonomous roles (Orchestrator, Architect, Researcher, Full-Stack Engineer, QA Tester, Diagnosis Debugger, Code Reviewer, Technical Writer) capable of goal decomposition, DAG pipeline execution, and autonomous code synthesis.
2. **Autonomous Self-Healing Loop**: If a test fails in the sandbox, DAI parses the traceback frame, pinpoints the culprit line, extracts surrounding context, generates a unified diff, writes the patch, and re-executes tests to verify the fix.
3. **Studio IDE & Live Environment**: Complete Monaco code and diff editors, integrated WebSocket terminal with ANSI capture, split-screen views, and background process management.
4. **Dense RAG Knowledge Engine**: Semantic document chunking (500 chars / 100 overlap) with 1536-dimensional normalized dense vectors and cosine similarity search for retrieval-augmented generation.
5. **Multi-Layer Memory**: Hierarchical short-term Redis cache combined with persistent PostgreSQL episodic memory.
6. **Multi-Provider AI Switching**: Seamlessly toggle between OpenAI, Anthropic, Google Gemini, and local Ollama instances with live temperature and model controls.

---

## ?? One-Click Production Deployment (Docker Compose)

### 1. Clone & Configure Environment
`ash
git clone https://github.com/your-repo/dai.git
cd dai

# Copy production environment configuration
cp .env.production.example .env
`

### 2. Build & Launch Containers
`ash
# Builds multi-stage backend and standalone Next.js frontend
docker compose up --build -d
`

### 3. Initialize & Seed Database
`ash
# Synchronizes schema, creates admin user, seeds 8 agents and starter RAG knowledge
docker compose exec backend python scripts/init_db.py
`

### 4. Access the Application
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Liveness Probe**: [http://localhost:8000/api/v1/healthz](http://localhost:8000/api/v1/healthz)
- **Readiness Probe**: [http://localhost:8000/api/v1/healthz/deep](http://localhost:8000/api/v1/healthz/deep)

---

## ?? Local Development Setup (Manual)

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 16 with pgvector & Redis 7 (or run via docker compose up -d postgres redis)

### 1. Backend Setup
`ash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate # macOS/Linux

# Install all dependencies including dev tools
pip install -e ".[dev]"

# Run database migrations or initialization
python scripts/init_db.py

# Launch development server with hot reload
uvicorn main:app --reload --port 8000
`

### 2. Frontend Setup
`ash
cd frontend

# Install dependencies
npm install

# Start Next.js Turbopack development server
npm run dev
`

---

## ?? Complete API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| /api/v1/healthz | GET | Basic liveness probe (200 OK) |
| /api/v1/healthz/deep | GET | Deep readiness probe verifying Postgres & Redis latency |
| /api/v1/auth/register | POST | User registration |
| /api/v1/auth/login | POST | JWT token authentication |
| /api/v1/auth/me | GET | Current authenticated user profile |
| /api/v1/chat/conversations | GET, POST | List and create chat conversations |
| /api/v1/chat/conversations/{id}/messages | POST | Send message with SSE streaming & tool execution loop |
| /api/v1/projects | GET, POST | Project state machine management |
| /api/v1/tasks | GET, POST, PATCH | Project task management & Kanban filtering |
| /api/v1/projects/{id}/files/tree | GET | Directory file tree hierarchy |
| /api/v1/projects/{id}/files | POST, PATCH, DELETE | Virtual filesystem CRUD with revision snapshots |
| /api/v1/projects/{id}/files/diff | GET | Unified diff computation against previous revision |
| /api/v1/projects/{id}/execute | POST | Sandboxed subprocess command execution |
| /api/v1/projects/{id}/terminal/ws | WebSocket | Real-time interactive streaming terminal |
| /api/v1/processes | GET, POST | Background dev server daemon lifecycle management |
| /api/v1/agents | GET | Roster of 8 specialized autonomous agents |
| /api/v1/agents/orchestrate | POST | Trigger multi-agent linear & branching DAG pipeline |
| /api/v1/agents/self-heal | POST | Autonomous self-healing diagnostic & patching loop |
| /api/v1/projects/{id}/tests/run | POST | Execute pytest/jest test suite with structured trace parsing |
| /api/v1/projects/{id}/tests/generate | POST | Synthesize automated test suite with edge cases |
| /api/v1/projects/{id}/debug/analyze | POST | Stack trace isolation & root cause diagnosis |
| /api/v1/projects/{id}/debug/apply-patch| POST | Safe patch application to file with revision record |
| /api/v1/documents | GET, POST, DELETE| RAG document ingestion and chunk management |
| /api/v1/documents/search | POST | Dense cosine similarity vector query |
| /api/v1/settings | GET, PUT | AI provider, model keys, and theme settings |
| /api/v1/activities | GET | Filterable project and platform audit log stream |

---

## ??? Autonomous Tool Registry

DAI provides agents with a secure, permissioned tool engine:

| Tool | Permission | Purpose |
| :--- | :--- | :--- |
| ead_file | READ | Inspect file contents in the project workspace |
| write_file | WRITE | Create or overwrite files with automatic revision tracking |
| edit_file | WRITE | High-precision substring replacement edit |
| list_files | READ | Inspect directory tree structure |
| execute_command | EXECUTE | Sandboxed subprocess command runner |
| manage_process | EXECUTE | Start/stop/tail background development servers |
| delegate_to_agent | WRITE | Delegate tasks to specialized agents in the swarm |
| un_self_correction | EXECUTE | Run end-to-end self-healing test and patch cycle |
| generate_tests | WRITE | Synthesize unit and integration test suites |
| un_test_suite | EXECUTE | Execute project test runners and return structured results |
| nalyze_error | READ | Isolate stack trace frames and synthesize fix diffs |
| search_knowledge_base| READ | Query dense RAG knowledge base via cosine similarity |
| ingest_document | WRITE | Partition and embed new technical documentation |
| web_search | EXTERNAL | Retrieve external information |

---

## ?? Comprehensive Verification

`ash
# 1. Run all backend tests
cd backend
pytest tests/ -v
# Output: 38 passed in 32s (100% pass rate)

# 2. Verify frontend TypeScript typing
cd frontend
npx tsc --noEmit
# Output: 0 errors

# 3. Build optimized production Next.js frontend
cd frontend
npm run build
# Output: 17 / 17 routes compiled cleanly
`

---

## ?? Completed Development Roadmap

- [x] **Phase 1**: Foundation & Responsive Application Shell
- [x] **Phase 2**: Autonomous AI Core, Multi-Layer Memory & Tool Calling
- [x] **Phase 3**: Project State Machine & Task Management System
- [x] **Phase 4**: Autonomous Coding Agent, Monaco IDE & Diff Engine
- [x] **Phase 5**: Execution Sandbox, Terminal & Process Daemon Manager
- [x] **Phase 6**: Multi-Agent Swarm Orchestration & Self-Healing Bug Loop
- [x] **Phase 7**: Automated Test Generation, Diagnostics & Code Patching
- [x] **Phase 8**: Document Ingestion & Dense Knowledge Base (RAG)
- [x] **Phase 9**: Deployment, Docker Containerization & Final Production Polish

---

## ?? License
Private & Proprietary. All rights reserved.
