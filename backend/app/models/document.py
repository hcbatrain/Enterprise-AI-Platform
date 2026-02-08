import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # File info
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    checksum = Column(String(64), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=True)  # 'text', 'markdown', 'html'
    
    # Metadata
    source = Column(String(200), nullable=True)  # 'upload', 'email', 'teams', etc.
    metadata_json = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    
    # Access control
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_access = Column(ARRAY(String), default=list)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", backref="documents")
    chunks = relationship("DocumentChunk", backref="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_documents_status', 'status'),
        Index('ix_documents_tags', 'tags', postgresql_using='gin'),
        Index('ix_documents_metadata', 'metadata_json', postgresql_using='gin'),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Vector embedding (stored as array for pgvector)
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, default=dict)
    
    # Search ranking
    search_count = Column(Integer, default=0)
    last_searched = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", backref="chunks")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_chunks_document_id', 'document_id'),
        Index('ix_document_chunks_chunk_index', 'chunk_index'),
    )
