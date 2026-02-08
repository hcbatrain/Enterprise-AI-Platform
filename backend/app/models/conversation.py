import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=True)
    
    # User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Context
    context_type = Column(String(50), default="general")  # general, document, code, etc.
    context_id = Column(UUID(as_uuid=True), nullable=True)  # Related document/code ID
    
    # Role context
    user_role = Column(String(50), nullable=True)  # Role at time of conversation
    team_context = Column(String(100), nullable=True)  # Team context
    
    # Settings
    model = Column(String(100), default="default")
    temperature = Column(Float, default=0.7)
    system_prompt = Column(Text, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Stats
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="conversations")
    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    # Indexes
    __table_args__ = (
        Index('ix_conversations_user_id', 'user_id'),
        Index('ix_conversations_context_type', 'context_type'),
        Index('ix_conversations_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "title": self.title,
            "user_id": str(self.user_id),
            "context_type": self.context_type,
            "context_id": str(self.context_id) if self.context_id else None,
            "user_role": self.user_role,
            "team_context": self.team_context,
            "model": self.model,
            "message_count": self.message_count,
            "is_active": self.is_active,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # text, code, image, etc.
    
    # For assistant messages
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Source attribution for RAG
    sources = Column(JSON, default=list)  # List of source references
    
    # Metadata
    metadata_json = Column(JSON, default=dict)
    
    # Feedback
    feedback_rating = Column(Integer, nullable=True)  # 1-5 rating
    feedback_comment = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", backref="messages")
    
    # Indexes
    __table_args__ = (
        Index('ix_messages_conversation_id', 'conversation_id'),
        Index('ix_messages_role', 'role'),
        Index('ix_messages_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "content_type": self.content_type,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "sources": self.sources,
            "feedback_rating": self.feedback_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
