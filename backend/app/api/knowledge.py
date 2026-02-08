from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.knowledge_graph_service import knowledge_graph_service
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class EntityCreate(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    domain: Optional[str] = None


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    properties: Optional[Dict[str, Any]] = None


@router.get("/stats")
async def get_statistics(
    current_user: User = Depends(get_current_user),
):
    """Get knowledge graph statistics."""
    stats = await knowledge_graph_service.get_statistics()
    return stats


@router.post("/entities")
async def create_entity(
    data: EntityCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge entity."""
    entity_id = await knowledge_graph_service.create_entity(
        name=data.name,
        entity_type=data.entity_type,
        description=data.description,
        properties=data.properties,
        source=data.source,
        domain=data.domain,
    )
    
    return {"id": entity_id, "message": "Entity created"}


@router.get("/entities/search")
async def search_entities(
    query: str,
    entity_type: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """Search for entities."""
    entities = await knowledge_graph_service.search_entities(
        query=query,
        entity_type=entity_type,
        domain=domain,
        limit=limit,
    )
    return entities


@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific entity with relationships."""
    entity = await knowledge_graph_service.get_entity(entity_id=entity_id)
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    
    return entity


@router.get("/entities/by-name/{entity_type}/{name}")
async def get_entity_by_name(
    entity_type: str,
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Get an entity by name and type."""
    entity = await knowledge_graph_service.get_entity(
        name=name,
        entity_type=entity_type,
    )
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    
    return entity


@router.post("/relationships")
async def create_relationship(
    data: RelationshipCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a relationship between entities."""
    success = await knowledge_graph_service.create_relationship(
        source_id=data.source_id,
        target_id=data.target_id,
        relationship_type=data.relationship_type,
        properties=data.properties,
    )
    
    if success:
        return {"message": "Relationship created"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create relationship",
        )


@router.get("/entities/{entity_id}/related")
async def get_related_entities(
    entity_id: str,
    relationship_type: Optional[str] = None,
    direction: str = "both",
    current_user: User = Depends(get_current_user),
):
    """Get entities related to a given entity."""
    entities = await knowledge_graph_service.get_related_entities(
        entity_id=entity_id,
        relationship_type=relationship_type,
        direction=direction,
    )
    return entities


@router.get("/path")
async def get_entity_path(
    source_id: str,
    target_id: str,
    max_depth: int = 5,
    current_user: User = Depends(get_current_user),
):
    """Find the shortest path between two entities."""
    path = await knowledge_graph_service.get_entity_path(
        source_id=source_id,
        target_id=target_id,
        max_depth=max_depth,
    )
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No path found between entities",
        )
    
    return path


@router.get("/domain/{domain}")
async def get_domain_entities(
    domain: str,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get all entities in a domain."""
    entities = await knowledge_graph_service.get_domain_entities(
        domain=domain,
        entity_type=entity_type,
    )
    return entities
