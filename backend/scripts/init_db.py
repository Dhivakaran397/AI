"""
Production Database Initialization and Seeding Script for DAI.

Initializes database schema, seeds default agents, default admin user,
and starter RAG knowledge base documents.
"""

import asyncio
import os
import sys
import argparse

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, text
from app.models.base import Base
from app.models.user import User
from app.core.security import get_password_hash
from app.services.orchestrator_service import AgentService
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate


# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

STARTER_DOCUMENTS = [
    {
        "title": "DAI System Architecture & Micro-Engines",
        "type": "ARCHITECTURE",
        "content": """# DAI System Architecture Overview

DAI (Personal Intelligence & Project Builder) is a modular full-stack agentic platform designed for autonomous software creation and maintenance.

### Core Subsystems:
1. **Frontend Architecture**: Next.js 16 with Turbopack, Tailwind CSS v4, Monaco IDE code and diff editors, integrated WebSocket terminal, and split-screen studio workspace.
2. **Backend Engine**: FastAPI ASGI server with async SQLAlchemy 2.0, PostgreSQL with pgvector for dense embeddings, and Redis 7 for real-time caching and ephemeral agent traces.
3. **Execution Sandbox**: Path-isolated process runner with hazardous command filters (fork bombs, root deletion guards) and streaming stdout/stderr execution tracking.
4. **Multi-Agent Swarm**: 8 specialized agents coordinated by a centralized Orchestrator DAG pipeline with autonomous self-healing loops.
5. **RAG Knowledge Base**: Dense vector indexing, sliding-window chunking (500 chars / 100 overlap), and cosine similarity search for retrieval-augmented generation.
"""
    },
    {
        "title": "Multi-Agent Swarm Collaboration & Self-Healing Protocol",
        "type": "PROTOCOL",
        "content": """# Multi-Agent Swarm Collaboration Protocol

DAI incorporates 8 specialized autonomous roles:
- **Lead Orchestrator**: Decomposes user goals into DAG milestone pipelines and coordinates agent handoffs.
- **Systems Architect**: Designs database schemas, API contracts, and architectural diagrams.
- **Researcher**: Queries web, documentation, and RAG knowledge base for technical references.
- **Full-Stack Engineer**: Implements frontend components, backend endpoints, and algorithmic logic.
- **QA Automation Tester**: Generates pytest and jest test suites and validates edge cases.
- **Diagnosis Debugger**: Isolates stack traces, extracts culprit lines, and drafts unified diff patches.
- **Code Reviewer**: Inspects security, linting, code hygiene, and style conventions.
- **Technical Writer**: Synthesizes walkthroughs, API docs, and release notes.

### Self-Healing Loop:
When a test failure occurs during execution, the QA Tester captures the failure trace. The Diagnosis Debugger pinpoints the culprit file and line, synthesize a unified diff patch, and applies the repair. The test suite is re-executed to guarantee zero regressions.
"""
    },
    {
        "title": "Autonomous Tool Registry & Sandbox Security Guide",
        "type": "SECURITY",
        "content": """# Autonomous Tool Registry & Sandbox Security Guide

All tool invocations executed by agents must undergo authorization through the ToolRegistry.

### Tool Permission Levels:
- **READ**: Safe inspection tools (read_file, list_files, search_code, search_knowledge_base, analyze_error).
- **WRITE**: Workspace mutating tools (write_file, edit_file, revert_file, ingest_document, generate_tests).
- **EXECUTE**: Subprocess tools (execute_command, manage_process, run_test_suite, run_self_correction).
- **EXTERNAL**: Network access tools (web_search).

### Sandbox Safety Invariants:
1. Workspace root path confinement (DAI_WORKSPACE_DIR/<project_id>).
2. Regex command pattern blacklist preventing destructive commands (e.g., m -rf /, mkfs, fork bombs).
3. Process execution timeout bounds (default 30s) and bounded circular stdout buffers (10,000 characters).
"""
    }
]


async def init_database(db_url: str | None = None):
    print("[*] Starting DAI Database Initialization...")

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    if db_url:
        target_engine = create_async_engine(db_url, echo=False)
        session_factory = async_sessionmaker(target_engine, expire_on_commit=False, class_=AsyncSession)
    else:
        from app.core.database import engine as target_engine, async_session_factory as session_factory

    try:
        # 1. Initialize Tables
        print("[*] Connecting to database and creating schema...")
        async with target_engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                print("  [+] Vector extension enabled.")
            except Exception:
                print("  [*] Vector extension skipped (SQLite or already enabled).")
            await conn.run_sync(Base.metadata.create_all)
        print("  [+] Database schema synchronized successfully.")

        # 2. Seed Default Admin User
        async with session_factory() as db:
            print("[*] Ensuring default admin user exists...")
            result = await db.execute(select(User).where(User.email == "admin@dai.local"))
            admin_user = result.scalars().first()

            if not admin_user:
                admin_user = User(
                    email="admin@dai.local",
                    hashed_password=get_password_hash("admin123456"),
                    full_name="DAI Administrator",
                    is_active=True,
                )
                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)
                print(f"  [+] Admin user created: admin@dai.local (ID: {admin_user.id})")
            else:
                print(f"  [+] Admin user already exists: admin@dai.local (ID: {admin_user.id})")

            # 3. Seed Default AI Agents
            print("[*] Seeding 8 specialized AI agents...")
            await AgentService.seed_builtin_agents(db)
            agents = await AgentService.get_agents(db)
            print(f"  [+] {len(agents)} AI agents seeded and operational.")

            # 4. Seed Starter Knowledge Base Documents
            print("[*] Seeding starter RAG knowledge base documents...")
            for doc_data in STARTER_DOCUMENTS:
                doc_in = DocumentCreate(
                    filename=doc_data["title"] + ".md",
                    content=doc_data["content"],
                    file_type="markdown",
                )
                doc = await DocumentService.ingest_document(db, admin_user.id, doc_in)
                print(f"  [+] Ingested document: '{doc.filename}' ({len(doc.chunks)} chunks)")

        print("\n[OK] DAI Database Initialization & Seeding Complete!")
        return True

    except ConnectionRefusedError:
        print("\n[!] Database connection refused!")
        print("  Please ensure PostgreSQL is running before initializing:")
        print("  Run: docker compose up -d postgres")
        return False
    except Exception as e:
        print(f"\n[!] Initialization error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize and seed DAI database.")
    parser.add_argument("--db-url", type=str, default=None, help="Custom database URL (e.g., sqlite+aiosqlite:///:memory:)")
    args = parser.parse_args()

    asyncio.run(init_database(args.db_url))
