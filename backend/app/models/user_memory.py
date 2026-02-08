"""
Persistent User Memory System
Stores long-term context about employees, teams, projects, and conversations.
This memory persists across chat sessions and survives even when users leave and return.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserMemory(Base):
    """
    Persistent memory storage for each user.
    This stores facts, preferences, project context, and conversation history summaries
    that persist indefinitely across all sessions.
    """
    __tablename__ = "user_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Employee Profile Memory
    employee_facts = Column(JSON, default=dict)  # Key facts about the employee
    # Example: {"hire_date": "2022-03-15", "previous_companies": ["ABC Corp"], "specializations": ["data conversion", "WC policies"]}
    
    # Team & Company Context
    team_info = Column(JSON, default=dict)  # Team structure, responsibilities
    # Example: {"team": "Data Conversion", "manager": "John Smith", "teammates": ["Alice", "Bob"]}
    
    company_knowledge = Column(JSON, default=dict)  # Company-specific knowledge
    # Example: {"current_projects": ["WC Migration Phase 2"], "systems_access": ["Sapiens", "Legacy DB"]}
    
    # Project Memory
    active_projects = Column(JSON, default=list)  # Current projects with context
    # Example: [{"name": "WC Policy Migration", "status": "in_progress", "last_discussed": "2024-01-15"}]
    
    project_history = Column(JSON, default=list)  # Past projects
    # Example: [{"name": "CA WC Implementation", "completed": "2023-12-01", "role": "lead"}]
    
    # Conversation Summaries (key takeaways from past chats)
    conversation_summaries = Column(JSON, default=list)
    # Example: [{"topic": "Rating algorithm issue", "resolution": "Fixed in staging", "date": "2024-01-10"}]
    
    # Domain-Specific Memory (WC Insurance)
    domain_expertise = Column(JSON, default=dict)
    # Example: {"familiar_class_codes": ["8810", "8820"], "states_worked": ["CA", "NY", "TX"]}
    
    # Technical Preferences
    tech_preferences = Column(JSON, default=dict)
    # Example: {"preferred_languages": ["SQL", "Python"], "favorite_tools": ["DBeaver", "VS Code"]}
    
    # Learning & Development Tracking
    learning_progress = Column(JSON, default=dict)
    # Example: {"wc_certification": "in_progress", "sapiens_training": "completed"}
    
    # Frequently Asked Topics (for quick reference)
    frequent_topics = Column(JSON, default=list)
    # Example: ["WC rating algorithms", "Class code mapping", "Policy conversion"]
    
    # Custom Notes (user-specific notes the AI should remember)
    custom_notes = Column(Text, nullable=True)
    
    # Memory Statistics
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    last_interaction = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="memory", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('ix_user_memories_user_id', 'user_id'),
        Index('ix_user_memories_last_interaction', 'last_interaction'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "employee_facts": self.employee_facts,
            "team_info": self.team_info,
            "company_knowledge": self.company_knowledge,
            "active_projects": self.active_projects,
            "project_history": self.project_history,
            "conversation_summaries": self.conversation_summaries,
            "domain_expertise": self.domain_expertise,
            "tech_preferences": self.tech_preferences,
            "learning_progress": self.learning_progress,
            "frequent_topics": self.frequent_topics,
            "custom_notes": self.custom_notes,
            "total_conversations": self.total_conversations,
            "total_messages": self.total_messages,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_context_for_llm(self) -> str:
        """Generate a context string for the LLM based on stored memory."""
        context_parts = []
        
        # Employee facts
        if self.employee_facts:
            facts = self.employee_facts
            context_parts.append(f"Employee: {facts.get('full_name', 'Unknown')}")
            if 'hire_date' in facts:
                context_parts.append(f"Hire Date: {facts['hire_date']}")
            if 'specializations' in facts:
                context_parts.append(f"Specializations: {', '.join(facts['specializations'])}")
        
        # Team info
        if self.team_info:
            team = self.team_info
            context_parts.append(f"Team: {team.get('team', 'Unknown')}")
            if 'manager' in team:
                context_parts.append(f"Manager: {team['manager']}")
        
        # Active projects
        if self.active_projects:
            projects = [p['name'] for p in self.active_projects if 'name' in p]
            if projects:
                context_parts.append(f"Current Projects: {', '.join(projects)}")
        
        # Domain expertise
        if self.domain_expertise:
            de = self.domain_expertise
            if 'familiar_class_codes' in de:
                context_parts.append(f"Familiar Class Codes: {', '.join(de['familiar_class_codes'])}")
            if 'states_worked' in de:
                context_parts.append(f"States Experience: {', '.join(de['states_worked'])}")
        
        # Recent conversation summaries
        if self.conversation_summaries:
            recent = self.conversation_summaries[-3:]  # Last 3 summaries
            if recent:
                context_parts.append("Recent Context:")
                for summary in recent:
                    context_parts.append(f"  - {summary.get('topic', 'Unknown topic')}: {summary.get('resolution', 'No resolution')}")
        
        # Custom notes
        if self.custom_notes:
            context_parts.append(f"Important Notes: {self.custom_notes}")
        
        return "\n".join(context_parts) if context_parts else ""


class MemoryEntry(Base):
    """
    Individual memory entries for granular tracking.
    Each entry represents a specific fact or piece of information to remember.
    """
    __tablename__ = "memory_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Memory categorization
    category = Column(String(50), nullable=False)  # employee, project, technical, domain, preference, etc.
    key = Column(String(200), nullable=False)  # What to remember (e.g., "hire_date", "current_project")
    value = Column(Text, nullable=False)  # The actual value/fact
    
    # Context
    source_conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    confidence = Column(Integer, default=100)  # Confidence level (0-100)
    
    # Metadata
    tags = Column(JSON, default=list)  # For filtering
    metadata = Column(JSON, default=dict)  # Additional context
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Some memories may expire
    
    # Relationships
    user = relationship("User", backref="memory_entries")
    conversation = relationship("Conversation", backref="memory_entries")
    
    # Indexes
    __table_args__ = (
        Index('ix_memory_entries_user_id', 'user_id'),
        Index('ix_memory_entries_category', 'category'),
        Index('ix_memory_entries_key', 'key'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ConversationContext(Base):
    """
    Extended conversation context that persists beyond individual conversations.
    Links related conversations and maintains topic continuity.
    """
    __tablename__ = "conversation_contexts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Context identification
    context_type = Column(String(50), nullable=False)  # project, issue, topic, etc.
    context_key = Column(String(200), nullable=False)  # e.g., "WC_Migration_Phase2"
    
    # Context data
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, resolved, archived
    
    # Related conversations
    conversation_ids = Column(JSON, default=list)  # List of conversation IDs
    
    # Key information extracted
    key_facts = Column(JSON, default=list)  # Important facts from all conversations
    decisions_made = Column(JSON, default=list)  # Decisions recorded
    action_items = Column(JSON, default=list)  # Outstanding action items
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_conversation_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="conversation_contexts")
    
    # Indexes
    __table_args__ = (
        Index('ix_conversation_contexts_user_id', 'user_id'),
        Index('ix_conversation_contexts_context_key', 'context_key'),
        Index('ix_conversation_contexts_status', 'status'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "context_type": self.context_type,
            "context_key": self.context_key,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "conversation_ids": self.conversation_ids,
            "key_facts": self.key_facts,
            "decisions_made": self.decisions_made,
            "action_items": self.action_items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_conversation_at": self.last_conversation_at.isoformat() if self.last_conversation_at else None,
        }
