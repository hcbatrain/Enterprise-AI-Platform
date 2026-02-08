from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.services.rag_service import rag_service
from app.services.knowledge_graph_service import knowledge_graph_service
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    search_type: str = "hybrid"  # vector, keyword, hybrid
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    query: str
    search_type: str


@router.get("/documents")
async def search_documents(
    query: str = Query(..., min_length=1),
    search_type: str = "hybrid",
    top_k: int = 5,
    team: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search documents using vector and/or keyword search."""
    
    filters = {}
    if team:
        filters["team"] = team
    elif current_user.team:
        filters["team"] = current_user.team
    
    if search_type == "vector":
        results = await rag_service.search_documents(
            db=db,
            query=query,
            top_k=top_k,
            filters=filters,
        )
    elif search_type == "keyword":
        results = await rag_service.keyword_search(
            db=db,
            query=query,
            top_k=top_k,
            filters=filters,
        )
    else:  # hybrid
        results = await rag_service.hybrid_search(
            db=db,
            query=query,
            top_k=top_k,
            filters=filters,
        )
    
    return {
        "results": results,
        "total": len(results),
        "query": query,
        "search_type": search_type,
    }


@router.post("/documents")
async def search_documents_post(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search documents (POST method)."""
    
    filters = request.filters or {}
    if current_user.team and "team" not in filters:
        filters["team"] = current_user.team
    
    if request.search_type == "vector":
        results = await rag_service.search_documents(
            db=db,
            query=request.query,
            top_k=request.top_k,
            filters=filters,
        )
    elif request.search_type == "keyword":
        results = await rag_service.keyword_search(
            db=db,
            query=request.query,
            top_k=request.top_k,
            filters=filters,
        )
    else:  # hybrid
        results = await rag_service.hybrid_search(
            db=db,
            query=request.query,
            top_k=request.top_k,
            filters=filters,
        )
    
    return {
        "results": results,
        "total": len(results),
        "query": request.query,
        "search_type": request.search_type,
    }


@router.get("/knowledge")
async def search_knowledge(
    query: str = Query(..., min_length=1),
    entity_type: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """Search knowledge graph entities."""
    
    entities = await knowledge_graph_service.search_entities(
        query=query,
        entity_type=entity_type,
        domain=domain,
        limit=limit,
    )
    
    return {
        "results": entities,
        "total": len(entities),
        "query": query,
    }


@router.get("/unified")
async def unified_search(
    query: str = Query(..., min_length=1),
    include_documents: bool = True,
    include_knowledge: bool = True,
    top_k: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unified search across documents and knowledge graph."""
    
    results = {
        "query": query,
        "documents": [],
        "knowledge": [],
    }
    
    filters = {}
    if current_user.team:
        filters["team"] = current_user.team
    
    if include_documents:
        doc_results = await rag_service.hybrid_search(
            db=db,
            query=query,
            top_k=top_k,
            filters=filters,
        )
        results["documents"] = doc_results
    
    if include_knowledge:
        kg_results = await knowledge_graph_service.search_entities(
            query=query,
            limit=top_k,
        )
        results["knowledge"] = kg_results
    
    return results
