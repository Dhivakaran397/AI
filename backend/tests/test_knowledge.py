import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.project import ProjectCreate
from app.schemas.document import DocumentCreate, DocumentSearchRequest
from app.services.project_service import ProjectService
from app.services.document_service import DocumentService
from app.ai.tools.registry import tool_registry
from app.ai.tools.base import ToolPermission


SAMPLE_DOC_CONTENT = """# Authentication Specification for DAI
DAI uses PyJWT with HMAC-SHA256 for signing tokens.
Access tokens expire after 24 hours while refresh tokens persist for 7 days.
Passwords are encrypted using Argon2-cffi hashing algorithm with automated salt generation.
Cross-Origin Resource Sharing (CORS) is enforced with strict allowed origins.

# Database Architecture
PostgreSQL 16 is utilized with pgvector extension enabled for 1536-dimensional embeddings.
SQLAlchemy 2.0 async engine manages connections with an asyncpg driver.
Alembic provides schema migration tracking.
"""


@pytest.mark.asyncio
async def test_text_chunking_and_embeddings():
    """Verify sliding-window chunking and normalized dense vector embeddings."""
    chunks = DocumentService.chunk_text(SAMPLE_DOC_CONTENT, chunk_size=200, chunk_overlap=50)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) > 0

    emb1 = DocumentService.generate_embedding("Authentication with PyJWT and Argon2")
    emb2 = DocumentService.generate_embedding("JWT tokens and user password hashing")
    emb3 = DocumentService.generate_embedding("Completely unrelated baking recipe for chocolate cake")

    assert len(emb1) == 1536
    assert len(emb2) == 1536

    sim_related = DocumentService.cosine_similarity(emb1, emb2)
    sim_unrelated = DocumentService.cosine_similarity(emb1, emb3)

    assert sim_related > sim_unrelated


@pytest.mark.asyncio
async def test_document_ingestion_and_search(db_session: AsyncSession, test_user):
    """Verify document chunk storage and cosine similarity search in database."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="RAG Knowledge Project")
    )

    doc_in = DocumentCreate(
        filename="auth_spec.md",
        content=SAMPLE_DOC_CONTENT,
        file_type="text/markdown",
        project_id=proj.id,
    )
    doc_res = await DocumentService.ingest_document(db_session, test_user.id, doc_in)
    assert doc_res.filename == "auth_spec.md"
    assert doc_res.chunk_count >= 1
    assert len(doc_res.chunks) == doc_res.chunk_count

    # Search for authentication
    search_results = await DocumentService.search_knowledge(
        db=db_session,
        user_id=test_user.id,
        query="Argon2 password hashing algorithm",
        project_id=proj.id,
        top_k=2,
    )
    assert len(search_results) >= 1
    top_match = search_results[0]
    assert "Argon2" in top_match.content or "Authentication" in top_match.content
    assert top_match.similarity_score > 0.0

    # Test list & get
    doc_list = await DocumentService.list_documents(db_session, test_user.id, proj.id)
    assert len(doc_list) == 1
    assert doc_list[0].chunk_count == doc_res.chunk_count

    single_doc = await DocumentService.get_document(db_session, test_user.id, doc_res.id)
    assert single_doc is not None
    assert len(single_doc.chunks) == doc_res.chunk_count

    # Delete
    deleted = await DocumentService.delete_document(db_session, test_user.id, doc_res.id)
    assert deleted is True
    assert await DocumentService.get_document(db_session, test_user.id, doc_res.id) is None


@pytest.mark.asyncio
async def test_knowledge_ai_tools(db_session: AsyncSession, test_user):
    """Verify search_knowledge_base and ingest_document AI tools."""
    proj = await ProjectService.create_project(
        db_session, test_user.id, ProjectCreate(name="AI Tools Knowledge Project")
    )

    # 1. Ingest document tool
    ingest_tool = tool_registry.get("ingest_document")
    assert ingest_tool is not None
    assert ingest_tool.permission == ToolPermission.WRITE

    context = {"user_id": test_user.id, "db": db_session}
    ingest_res = await tool_registry.execute(
        "ingest_document",
        arguments={
            "filename": "microservices.txt",
            "content": "Microservices communicate via gRPC protocol and Redis pub/sub message brokers.",
            "project_id": str(proj.id),
        },
        context=context,
        allowed_permissions=[ToolPermission.WRITE],
    )
    assert ingest_res["status"] == "success"
    assert ingest_res["result"]["status"] == "ingested"

    # 2. Search knowledge tool
    search_tool = tool_registry.get("search_knowledge_base")
    assert search_tool is not None
    assert search_tool.permission == ToolPermission.READ

    search_res = await tool_registry.execute(
        "search_knowledge_base",
        arguments={"query": "gRPC communication and Redis message broker", "project_id": str(proj.id)},
        context=context,
        allowed_permissions=[ToolPermission.READ],
    )
    assert search_res["status"] == "success"
    assert search_res["result"]["match_count"] >= 1


@pytest.mark.asyncio
async def test_document_and_activity_api_endpoints(
    client: AsyncClient, auth_token: str, test_user, db_session: AsyncSession
):
    """Verify /documents and /activities REST endpoints."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 1. Ingest endpoint
    create_res = await client.post(
        "/api/v1/documents",
        json={
            "filename": "guidelines.md",
            "content": "Follow PEP8 conventions for Python and use strict TypeScript formatting.",
            "file_type": "text/markdown",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    doc_data = create_res.json()
    doc_id = doc_data["id"]
    assert doc_data["filename"] == "guidelines.md"
    assert doc_data["chunk_count"] >= 1

    # 2. List documents endpoint
    list_res = await client.get("/api/v1/documents", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Search endpoint
    search_res = await client.post(
        "/api/v1/documents/search",
        json={"query": "PEP8 conventions and TypeScript"},
        headers=headers,
    )
    assert search_res.status_code == 200
    matches = search_res.json()
    assert len(matches) >= 1
    assert "PEP8" in matches[0]["content"]

    # 4. Activity stream endpoint
    act_res = await client.get("/api/v1/activities?type=DOCUMENT_INGESTED", headers=headers)
    assert act_res.status_code == 200
    activities = act_res.json()
    assert len(activities) >= 1
    assert activities[0]["type"] == "DOCUMENT_INGESTED"

    # 5. Delete document endpoint
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204
