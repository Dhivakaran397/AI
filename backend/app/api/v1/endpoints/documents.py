from typing import Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
)
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def ingest_document(
    doc_in: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Ingest a text/markdown document, chunk it, and compute vector embeddings."""
    return await DocumentService.ingest_document(
        db=db,
        user_id=current_user.id,
        doc_in=doc_in,
    )


@router.get("", response_model=list[DocumentResponse])
@router.get("/", response_model=list[DocumentResponse], include_in_schema=False)
async def list_documents(
    project_id: Optional[UUID] = Query(None, description="Optional filter by project ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all documents for the authenticated user or specific project."""
    return await DocumentService.list_documents(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch a document along with all its indexed semantic chunks."""
    doc = await DocumentService.get_document(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Cascade delete a document and all its chunks from the knowledge base."""
    deleted = await DocumentService.delete_document(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )


@router.post("/search", response_model=list[DocumentSearchResult])
async def search_knowledge_base(
    req: DocumentSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Perform semantic similarity search across knowledge base chunks."""
    return await DocumentService.search_knowledge(
        db=db,
        user_id=current_user.id,
        query=req.query,
        project_id=req.project_id,
        top_k=req.top_k,
    )
