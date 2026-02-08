from typing import List, Dict, Any, Optional
from datetime import datetime
from neo4j import AsyncGraphDatabase
import uuid

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeGraphService:
    """Service for managing the knowledge graph in Neo4j."""
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver = None
    
    async def connect(self):
        """Initialize Neo4j connection."""
        if not self.driver:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
    
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
    
    async def create_entity(
        self,
        name: str,
        entity_type: str,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """Create a new entity in the knowledge graph."""
        await self.connect()
        
        entity_id = str(uuid.uuid4())
        
        query = """
        CREATE (e:Entity {
            id: $id,
            name: $name,
            type: $type,
            description: $description,
            properties: $properties,
            source: $source,
            domain: $domain,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN e.id as id
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                id=entity_id,
                name=name,
                type=entity_type,
                description=description or "",
                properties=properties or {},
                source=source or "",
                domain=domain or "",
            )
            record = await result.single()
            return record["id"] if record else None
    
    async def get_entity(
        self,
        entity_id: Optional[str] = None,
        name: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get an entity by ID or name."""
        await self.connect()
        
        if entity_id:
            query = """
            MATCH (e:Entity {id: $id})
            RETURN e {
                .*,
                relationships: [(e)-[r]->(target) | {
                    type: type(r),
                    target: target.name,
                    target_type: target.type,
                    target_id: target.id
                }],
                incoming: [(source)-[r]->(e) | {
                    type: type(r),
                    source: source.name,
                    source_type: source.type,
                    source_id: source.id
                }]
            } as entity
            """
            params = {"id": entity_id}
        elif name and entity_type:
            query = """
            MATCH (e:Entity {name: $name, type: $type})
            RETURN e {
                .*,
                relationships: [(e)-[r]->(target) | {
                    type: type(r),
                    target: target.name,
                    target_type: target.type,
                    target_id: target.id
                }],
                incoming: [(source)-[r]->(e) | {
                    type: type(r),
                    source: source.name,
                    source_type: source.type,
                    source_id: source.id
                }]
            } as entity
            """
            params = {"name": name, "type": entity_type}
        else:
            return None
        
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record["entity"] if record else None
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a relationship between two entities."""
        await self.connect()
        
        query = f"""
        MATCH (source:Entity {{id: $source_id}})
        MATCH (target:Entity {{id: $target_id}})
        CREATE (source)-[r:{relationship_type} $properties]->(target)
        SET r.created_at = datetime()
        RETURN r
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                properties=properties or {},
            )
            record = await result.single()
            return record is not None
    
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for entities by name or description."""
        await self.connect()
        
        cypher = """
        MATCH (e:Entity)
        WHERE (e.name CONTAINS $query OR e.description CONTAINS $query)
        """
        
        params = {"query": query, "limit": limit}
        
        if entity_type:
            cypher += " AND e.type = $type"
            params["type"] = entity_type
        
        if domain:
            cypher += " AND e.domain = $domain"
            params["domain"] = domain
        
        cypher += """
        RETURN e {
            .*,
            relationship_count: size((e)-[]->()) + size((e)<-[]-())
        } as entity
        ORDER BY e.name
        LIMIT $limit
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, **params)
            records = await result.data()
            return [r["entity"] for r in records]
    
    async def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "both",  # 'outgoing', 'incoming', 'both'
    ) -> List[Dict[str, Any]]:
        """Get entities related to a given entity."""
        await self.connect()
        
        if direction == "outgoing":
            if relationship_type:
                query = f"""
                MATCH (e:Entity {{id: $id}})-[:{relationship_type}]->(related)
                RETURN related {{.*, relationship_type: '{relationship_type}'}} as entity
                """
            else:
                query = """
                MATCH (e:Entity {id: $id})-[r]->(related)
                RETURN related {.*, relationship_type: type(r)} as entity
                """
        elif direction == "incoming":
            if relationship_type:
                query = f"""
                MATCH (e:Entity {{id: $id}})<-[:{relationship_type}]-(related)
                RETURN related {{.*, relationship_type: '{relationship_type}'}} as entity
                """
            else:
                query = """
                MATCH (e:Entity {id: $id})<-[r]-(related)
                RETURN related {.*, relationship_type: type(r)} as entity
                """
        else:  # both
            if relationship_type:
                query = f"""
                MATCH (e:Entity {{id: $id}})-[:{relationship_type}]-(related)
                RETURN related {{.*, relationship_type: '{relationship_type}'}} as entity
                """
            else:
                query = """
                MATCH (e:Entity {id: $id})-[r]-(related)
                RETURN related {.*, relationship_type: type(r)} as entity
                """
        
        async with self.driver.session() as session:
            result = await session.run(query, id=entity_id)
            records = await result.data()
            return [r["entity"] for r in records]
    
    async def get_entity_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find the shortest path between two entities."""
        await self.connect()
        
        query = """
        MATCH path = shortestPath(
            (source:Entity {id: $source_id})-[*1..$max_depth]-(target:Entity {id: $target_id})
        )
        RETURN [node in nodes(path) | {
            id: node.id,
            name: node.name,
            type: node.type
        }] as path_nodes,
        [rel in relationships(path) | {
            type: type(rel)
        }] as path_relationships
        """
        
        async with self.driver.session() as session:
            result = await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                max_depth=max_depth,
            )
            record = await result.single()
            if record:
                return {
                    "nodes": record["path_nodes"],
                    "relationships": record["path_relationships"],
                }
            return None
    
    async def get_domain_entities(
        self,
        domain: str,
        entity_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all entities in a specific domain."""
        await self.connect()
        
        if entity_type:
            query = """
            MATCH (e:Entity {domain: $domain, type: $type})
            RETURN e {.*} as entity
            ORDER BY e.name
            """
            params = {"domain": domain, "type": entity_type}
        else:
            query = """
            MATCH (e:Entity {domain: $domain})
            RETURN e {.*} as entity
            ORDER BY e.type, e.name
            """
            params = {"domain": domain}
        
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            records = await result.data()
            return [r["entity"] for r in records]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        await self.connect()
        
        query = """
        MATCH (e:Entity)
        WITH count(e) as entity_count
        MATCH ()-[r]->()
        WITH entity_count, count(r) as relationship_count
        MATCH (e:Entity)
        WITH entity_count, relationship_count, collect(DISTINCT e.type) as entity_types
        RETURN entity_count, relationship_count, entity_types
        """
        
        async with self.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            if record:
                return {
                    "entity_count": record["entity_count"],
                    "relationship_count": record["relationship_count"],
                    "entity_types": record["entity_types"],
                }
            return {"entity_count": 0, "relationship_count": 0, "entity_types": []}


# Global instance
knowledge_graph_service = KnowledgeGraphService()
