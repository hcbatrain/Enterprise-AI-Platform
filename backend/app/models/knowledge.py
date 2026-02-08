import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class KnowledgeEntity(Base):
    __tablename__ = "knowledge_entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity identification
    name = Column(String(500), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # BusinessConcept, SystemComponent, etc.
    
    # Description
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Aliases and synonyms
    aliases = Column(ARRAY(String), default=list)
    
    # Source
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    source_type = Column(String(50), nullable=True)  # document, code, manual, etc.
    source_reference = Column(String(500), nullable=True)
    
    # Domain
    domain = Column(String(100), nullable=True)  # workers_comp, general_liability, etc.
    
    # Metadata
    properties = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Confidence
    confidence_score = Column(Float, default=1.0)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Versioning
    version = Column(Integer, default=1)
    previous_version_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Status
    status = Column(String(50), default="active")  # active, deprecated, deleted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    source_document = relationship("Document", foreign_keys=[source_document_id])
    creator = relationship("User", foreign_keys=[created_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    # Indexes
    __table_args__ = (
        Index('ix_knowledge_entities_name_type', 'name', 'entity_type'),
        Index('ix_knowledge_entities_domain', 'domain'),
        Index('ix_knowledge_entities_tags', 'tags', postgresql_using='gin'),
        Index('ix_knowledge_entities_properties', 'properties', postgresql_using='gin'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "summary": self.summary,
            "aliases": self.aliases,
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "domain": self.domain,
            "properties": self.properties,
            "tags": self.tags,
            "confidence_score": self.confidence_score,
            "is_verified": self.is_verified,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KnowledgeRelationship(Base):
    __tablename__ = "knowledge_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationship endpoints
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entities.id"), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entities.id"), nullable=False)
    
    # Relationship type
    relationship_type = Column(String(100), nullable=False, index=True)  # IMPLEMENTS, DEPENDS_ON, etc.
    
    # Description
    description = Column(Text, nullable=True)
    
    # Properties
    properties = Column(JSON, default=dict)
    
    # Strength/weight
    weight = Column(Float, default=1.0)
    
    # Source
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    source_type = Column(String(50), nullable=True)
    
    # Confidence
    confidence_score = Column(Float, default=1.0)
    is_verified = Column(Boolean, default=False)
    
    # Versioning
    version = Column(Integer, default=1)
    
    # Status
    status = Column(String(50), default="active")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    source_entity = relationship("KnowledgeEntity", foreign_keys=[source_entity_id], backref="outgoing_relationships")
    target_entity = relationship("KnowledgeEntity", foreign_keys=[target_entity_id], backref="incoming_relationships")
    source_document = relationship("Document", foreign_keys=[source_document_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Indexes
    __table_args__ = (
        Index('ix_knowledge_relationships_source', 'source_entity_id'),
        Index('ix_knowledge_relationships_target', 'target_entity_id'),
        Index('ix_knowledge_relationships_type', 'relationship_type'),
        Index('ix_knowledge_relationships_source_target_type', 'source_entity_id', 'target_entity_id', 'relationship_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "source_entity_id": str(self.source_entity_id),
            "target_entity_id": str(self.target_entity_id),
            "relationship_type": self.relationship_type,
            "description": self.description,
            "properties": self.properties,
            "weight": self.weight,
            "confidence_score": self.confidence_score,
            "is_verified": self.is_verified,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
