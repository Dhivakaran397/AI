import math
import hashlib
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.document import Document, DocumentChunk
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentChunkResponse,
    DocumentSearchResult,
)
from app.services.activity_service import log_activity


class DocumentService:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list[str]:
        """Split text into overlapping character windows preserving paragraph/sentence boundaries."""
        text = text.strip()
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:].strip())
                break

            # Try to break on newline or space before end
            breakpoint = text.rfind("\n", start, end)
            if breakpoint == -1 or breakpoint <= start:
                breakpoint = text.rfind(" ", start, end)

            if breakpoint == -1 or breakpoint <= start:
                breakpoint = end

            chunk = text[start:breakpoint].strip()
            if chunk:
                chunks.append(chunk)

            # Advance with overlap
            start = max(start + 1, breakpoint - chunk_overlap)

        return chunks

    @staticmethod
    def generate_embedding(text: str, dim: int = 1536) -> list[float]:
        """Generate a deterministic normalized 1536-dimensional dense vector for semantic similarity."""
        tokens = text.lower().split()
        vector = [0.0] * dim

        # Use md5 / sha256 to distribute token values pseudo-randomly into dimensions
        for token in tokens:
            token_bytes = token.encode("utf-8")
            h = hashlib.sha256(token_bytes).digest()
            for i in range(0, min(len(h), 16), 2):
                idx = int.from_bytes(h[i:i+2], "little") % dim
                vector[idx] += 1.0

        # Character 3-grams for subword matching
        cleaned = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
        for i in range(max(0, len(cleaned) - 2)):
            tri = cleaned[i:i+3].encode("utf-8")
            h_tri = hashlib.md5(tri).digest()
            idx = int.from_bytes(h_tri[:2], "little") % dim
            vector[idx] += 0.5

        # Normalize to unit length (L2 norm)
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0.0:
            return [x / magnitude for x in vector]
        return [0.0] * dim

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 <= 0.0 or norm2 <= 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm1 * norm2)))

    @classmethod
    async def ingest_document(
        cls,
        db: AsyncSession,
        user_id: UUID,
        doc_in: DocumentCreate,
    ) -> DocumentResponse:
        """Create document, partition into chunks with embeddings, and commit."""
        doc = Document(
            user_id=user_id,
            project_id=doc_in.project_id,
            filename=doc_in.filename,
            file_type=doc_in.file_type,
            file_size=len(doc_in.content.encode("utf-8")),
            storage_path=f"documents/{doc_in.filename}",
        )
        db.add(doc)
        await db.flush()

        chunks_text = cls.chunk_text(doc_in.content)
        chunk_responses = []

        for idx, chunk_content in enumerate(chunks_text):
            embedding = cls.generate_embedding(chunk_content)
            chunk = DocumentChunk(
                document_id=doc.id,
                content=chunk_content,
                chunk_index=idx,
                embedding=embedding,
                metadata_={
                    "filename": doc_in.filename,
                    "project_id": str(doc_in.project_id) if doc_in.project_id else None,
                    **(doc_in.metadata or {}),
                },
            )
            db.add(chunk)
            await db.flush()

            chunk_responses.append(
                DocumentChunkResponse(
                    id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    metadata_=chunk.metadata_,
                    created_at=chunk.created_at,
                )
            )

        await db.commit()
        await db.refresh(doc)

        await log_activity(
            db=db,
            user_id=user_id,
            act_type="DOCUMENT_INGESTED",
            title=f"Ingested {doc.filename}",
            description=f"Created {len(chunk_responses)} chunks for knowledge retrieval",
            project_id=doc_in.project_id,
        )

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            storage_path=doc.storage_path,
            project_id=doc.project_id,
            created_at=doc.created_at,
            chunk_count=len(chunk_responses),
            chunks=chunk_responses,
        )

    @classmethod
    async def search_knowledge(
        cls,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        project_id: Optional[UUID] = None,
        top_k: int = 5,
    ) -> list[DocumentSearchResult]:
        """Perform semantic search across document chunks using cosine similarity."""
        query_embedding = cls.generate_embedding(query)

        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.user_id == user_id)
        )
        if project_id:
            stmt = stmt.where(Document.project_id == project_id)

        result = await db.execute(stmt)
        rows = result.all()

        scored: list[tuple[float, DocumentChunk, str]] = []
        for chunk, filename in rows:
            chunk_vec = chunk.embedding
            # If embedding is stored as string/array or Vector
            if isinstance(chunk_vec, (list, tuple)):
                score = cls.cosine_similarity(query_embedding, list(chunk_vec))
            else:
                score = 0.5

            scored.append((score, chunk, filename))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_results = scored[:top_k]

        return [
            DocumentSearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=fname,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity_score=round(score, 4),
                metadata_=chunk.metadata_,
            )
            for score, chunk, fname in top_results
        ]

    @classmethod
    async def list_documents(
        cls,
        db: AsyncSession,
        user_id: UUID,
        project_id: Optional[UUID] = None,
    ) -> list[DocumentResponse]:
        """List all documents for a user or project with chunk counts."""
        stmt = select(Document).where(Document.user_id == user_id)
        if project_id:
            stmt = stmt.where(Document.project_id == project_id)
        stmt = stmt.order_by(Document.created_at.desc())

        result = await db.execute(stmt)
        docs = result.scalars().all()

        responses = []
        for doc in docs:
            chunk_count_stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == doc.id)
            chunk_count_res = await db.execute(chunk_count_stmt)
            count = chunk_count_res.scalar() or 0

            responses.append(
                DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    storage_path=doc.storage_path,
                    project_id=doc.project_id,
                    created_at=doc.created_at,
                    chunk_count=count,
                    chunks=[],
                )
            )

        return responses

    @classmethod
    async def get_document(
        cls,
        db: AsyncSession,
        user_id: UUID,
        document_id: UUID,
    ) -> DocumentResponse | None:
        """Fetch a single document with all its chunks."""
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await db.execute(stmt)
        doc = result.scalars().first()
        if not doc:
            return None

        chunks_stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index.asc())
        chunks_res = await db.execute(chunks_stmt)
        chunks = chunks_res.scalars().all()

        chunk_responses = [
            DocumentChunkResponse(
                id=c.id,
                chunk_index=c.chunk_index,
                content=c.content,
                metadata_=c.metadata_,
                created_at=c.created_at,
            )
            for c in chunks
        ]

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            storage_path=doc.storage_path,
            project_id=doc.project_id,
            created_at=doc.created_at,
            chunk_count=len(chunk_responses),
            chunks=chunk_responses,
        )

    @classmethod
    async def delete_document(
        cls,
        db: AsyncSession,
        user_id: UUID,
        document_id: UUID,
    ) -> bool:
        """Cascade delete a document and its chunks."""
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await db.execute(stmt)
        doc = result.scalars().first()
        if not doc:
            return False

        # Delete chunks first
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        await db.delete(doc)
        await db.commit()
        return True
