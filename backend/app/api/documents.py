from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.services.document_service import document_service
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class DocumentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    filename: str
    file_size: int
    mime_type: str
    status: str
    chunk_count: int
    tags: List[str]
    created_at: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new document."""
    
    # Read file content
    content = await file.read()
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    try:
        # Upload document
        document = await document_service.upload_document(
            db=db,
            file_content=content,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            owner_id=str(current_user.id),
            title=title,
            description=description,
            tags=tag_list,
            team_access=[current_user.team] if current_user.team else [],
        )
        
        # Process document asynchronously
        # In production, this should be queued to a background worker
        import asyncio
        asyncio.create_task(document_service.process_document(db, str(document.id)))
        
        return document.to_dict()
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents."""
    
    filters = {}
    if status:
        filters["status"] = status
    
    documents = await document_service.list_documents(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
    )
    
    return [doc.to_dict() for doc in documents]


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    
    document = await document_service.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document.to_dict()


@router.post("/{document_id}/process")
async def process_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger document processing."""
    
    document = await document_service.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check ownership
    if str(document.owner_id) != str(current_user.id) and current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this document",
        )
    
    try:
        await document_service.process_document(db, document_id)
        return {"message": "Document processing started"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    
    document = await document_service.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check ownership
    if str(document.owner_id) != str(current_user.id) and current_user.role != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document",
        )
    
    success = await document_service.delete_document(db, document_id)
    
    if success:
        return {"message": "Document deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )
