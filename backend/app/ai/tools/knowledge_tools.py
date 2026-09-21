from typing import Any, Dict
from uuid import UUID
from app.ai.tools.base import BaseTool, ToolPermission
from app.core.database import async_session_factory
from app.services.document_service import DocumentService
from app.schemas.document import DocumentCreate


class SearchKnowledgeTool(BaseTool):
    name = "search_knowledge_base"
    description = (
        "Search the user's uploaded documents, architecture specs, and project knowledge base "
        "using semantic vector similarity."
    )
    permission = ToolPermission.READ
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query or keywords to search for in documents.",
            },
            "project_id": {
                "type": "string",
                "description": "Optional UUID of the project to narrow the search scope.",
            },
            "top_k": {
                "type": "integer",
                "description": "Maximum number of most relevant passages to return (default 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        query = kwargs.get("query")
        project_id_str = kwargs.get("project_id")
        top_k = kwargs.get("top_k", 5)

        if not query:
            return {"error": "'query' is required"}

        p_uuid = None
        if project_id_str:
            try:
                p_uuid = UUID(project_id_str)
            except ValueError:
                return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        db = kwargs.get("db")
        user_id = kwargs.get("user_id")

        if db and user_id:
            results = await DocumentService.search_knowledge(
                db=db,
                user_id=user_id,
                query=query,
                project_id=p_uuid,
                top_k=int(top_k),
            )
        else:
            return {"error": "Database session and user context required to search knowledge"}

        return {
            "query": query,
            "match_count": len(results),
            "results": [r.model_dump() for r in results],
        }


class IngestDocumentTool(BaseTool):
    name = "ingest_document"
    description = (
        "Ingest a text or markdown document into the project knowledge base, splitting it into "
        "searchable semantic chunks with vector embeddings."
    )
    permission = ToolPermission.WRITE
    parameters = {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Name of the document e.g. 'architecture.md' or 'api_spec.txt'.",
            },
            "content": {
                "type": "string",
                "description": "Full text or markdown contents of the document.",
            },
            "project_id": {
                "type": "string",
                "description": "Optional UUID of the project associated with this document.",
            },
            "file_type": {
                "type": "string",
                "description": "MIME type or file extension e.g. 'text/markdown'.",
                "default": "text/markdown",
            },
        },
        "required": ["filename", "content"],
    }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        filename = kwargs.get("filename")
        content = kwargs.get("content")
        project_id_str = kwargs.get("project_id")
        file_type = kwargs.get("file_type", "text/markdown")

        if not filename or not content:
            return {"error": "'filename' and 'content' are required"}

        p_uuid = None
        if project_id_str:
            try:
                p_uuid = UUID(project_id_str)
            except ValueError:
                return {"error": f"Invalid project_id UUID format: {project_id_str}"}

        db = kwargs.get("db")
        user_id = kwargs.get("user_id")

        if not db or not user_id:
            return {"error": "Database session and user context required to ingest document"}

        doc_in = DocumentCreate(
            filename=filename,
            content=content,
            file_type=file_type,
            project_id=p_uuid,
        )

        doc = await DocumentService.ingest_document(
            db=db,
            user_id=user_id,
            doc_in=doc_in,
        )

        return {
            "document_id": str(doc.id),
            "filename": doc.filename,
            "chunk_count": doc.chunk_count,
            "status": "ingested",
        }
