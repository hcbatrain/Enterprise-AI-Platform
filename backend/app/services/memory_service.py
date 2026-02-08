"""
Persistent Memory Service
Manages long-term memory for users across all chat sessions.
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_memory import UserMemory, MemoryEntry, ConversationContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class MemoryService:
    """Service for managing persistent user memory."""
    
    async def get_or_create_user_memory(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> UserMemory:
        """Get existing user memory or create a new one."""
        result = await db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memory = result.scalar_one_or_none()
        
        if not memory:
            memory = UserMemory(user_id=user_id)
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            logger.info(f"Created new memory for user {user_id}")
        
        return memory
    
    async def update_employee_facts(
        self,
        db: AsyncSession,
        user_id: UUID,
        facts: Dict[str, Any],
    ) -> UserMemory:
        """Update employee facts in memory."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        if not memory.employee_facts:
            memory.employee_facts = {}
        
        memory.employee_facts.update(facts)
        memory.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(memory)
        
        # Also create individual memory entries for important facts
        for key, value in facts.items():
            await self.add_memory_entry(
                db, user_id, "employee", key, str(value),
                tags=["employee", "profile"]
            )
        
        return memory
    
    async def update_team_info(
        self,
        db: AsyncSession,
        user_id: UUID,
        team_info: Dict[str, Any],
    ) -> UserMemory:
        """Update team information in memory."""
        memory = await self.get_or_create_user_memory(db, user_id)
        memory.team_info = team_info
        memory.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def add_active_project(
        self,
        db: AsyncSession,
        user_id: UUID,
        project: Dict[str, Any],
    ) -> UserMemory:
        """Add a new active project to memory."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        if not memory.active_projects:
            memory.active_projects = []
        
        # Check if project already exists
        existing = next(
            (p for p in memory.active_projects if p.get('name') == project.get('name')),
            None
        )
        
        if existing:
            existing.update(project)
        else:
            memory.active_projects.append(project)
        
        memory.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(memory)
        
        # Create memory entry
        await self.add_memory_entry(
            db, user_id, "project", f"active_project_{project.get('name')}",
            json.dumps(project),
            tags=["project", "active"]
        )
        
        return memory
    
    async def complete_project(
        self,
        db: AsyncSession,
        user_id: UUID,
        project_name: str,
        completion_data: Dict[str, Any],
    ) -> UserMemory:
        """Move a project from active to history."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        if not memory.active_projects:
            memory.active_projects = []
        
        # Find and remove from active
        project = next(
            (p for p in memory.active_projects if p.get('name') == project_name),
            None
        )
        
        if project:
            memory.active_projects.remove(project)
            
            # Add to history
            if not memory.project_history:
                memory.project_history = []
            
            project.update(completion_data)
            project['completed_at'] = datetime.utcnow().isoformat()
            memory.project_history.append(project)
        
        memory.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def add_conversation_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        topic: str,
        resolution: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> UserMemory:
        """Add a summary of an important conversation."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        if not memory.conversation_summaries:
            memory.conversation_summaries = []
        
        summary = {
            "topic": topic,
            "resolution": resolution,
            "date": datetime.utcnow().isoformat(),
        }
        
        if additional_context:
            summary.update(additional_context)
        
        memory.conversation_summaries.append(summary)
        
        # Keep only last 50 summaries
        if len(memory.conversation_summaries) > 50:
            memory.conversation_summaries = memory.conversation_summaries[-50:]
        
        memory.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def update_domain_expertise(
        self,
        db: AsyncSession,
        user_id: UUID,
        expertise: Dict[str, Any],
    ) -> UserMemory:
        """Update domain expertise information."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        if not memory.domain_expertise:
            memory.domain_expertise = {}
        
        # Merge lists instead of replacing
        for key, value in expertise.items():
            if isinstance(value, list) and key in memory.domain_expertise:
                existing = set(memory.domain_expertise[key])
                existing.update(value)
                memory.domain_expertise[key] = list(existing)
            else:
                memory.domain_expertise[key] = value
        
        memory.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def add_frequent_topic(
        self,
        db: AsyncSession,
        user_id: UUID,
        topic: str,
    ) -> UserMemory:
        """Add a topic to frequent topics list."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        if not memory.frequent_topics:
            memory.frequent_topics = []
        
        if topic not in memory.frequent_topics:
            memory.frequent_topics.append(topic)
            
            # Keep only last 20 topics
            if len(memory.frequent_topics) > 20:
                memory.frequent_topics = memory.frequent_topics[-20:]
        
        memory.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def add_memory_entry(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: str,
        key: str,
        value: str,
        source_conversation_id: Optional[UUID] = None,
        confidence: int = 100,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Add a granular memory entry."""
        # Check if entry already exists
        result = await db.execute(
            select(MemoryEntry).where(
                and_(
                    MemoryEntry.user_id == user_id,
                    MemoryEntry.category == category,
                    MemoryEntry.key == key,
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing entry
            existing.value = value
            existing.confidence = confidence
            existing.updated_at = datetime.utcnow()
            if tags:
                existing.tags = list(set(existing.tags or []).union(tags))
            if metadata:
                existing.metadata = {**(existing.metadata or {}), **metadata}
            await db.commit()
            await db.refresh(existing)
            return existing
        
        # Create new entry
        entry = MemoryEntry(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            source_conversation_id=source_conversation_id,
            confidence=confidence,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        
        return entry
    
    async def get_memory_entries(
        self,
        db: AsyncSession,
        user_id: UUID,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[MemoryEntry]:
        """Get memory entries for a user, optionally filtered."""
        query = select(MemoryEntry).where(MemoryEntry.user_id == user_id)
        
        if category:
            query = query.where(MemoryEntry.category == category)
        
        result = await db.execute(query)
        entries = result.scalars().all()
        
        if tags:
            entries = [
                e for e in entries
                if any(tag in (e.tags or []) for tag in tags)
            ]
        
        return list(entries)
    
    async def get_or_create_conversation_context(
        self,
        db: AsyncSession,
        user_id: UUID,
        context_key: str,
        context_type: str = "project",
        title: Optional[str] = None,
    ) -> ConversationContext:
        """Get or create a conversation context for tracking related conversations."""
        result = await db.execute(
            select(ConversationContext).where(
                and_(
                    ConversationContext.user_id == user_id,
                    ConversationContext.context_key == context_key,
                )
            )
        )
        context = result.scalar_one_or_none()
        
        if not context:
            context = ConversationContext(
                user_id=user_id,
                context_type=context_type,
                context_key=context_key,
                title=title or context_key,
            )
            db.add(context)
            await db.commit()
            await db.refresh(context)
        
        return context
    
    async def add_conversation_to_context(
        self,
        db: AsyncSession,
        user_id: UUID,
        context_key: str,
        conversation_id: UUID,
        key_facts: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None,
    ) -> ConversationContext:
        """Add a conversation to a context and update facts/decisions."""
        context = await self.get_or_create_conversation_context(
            db, user_id, context_key
        )
        
        if not context.conversation_ids:
            context.conversation_ids = []
        
        if str(conversation_id) not in context.conversation_ids:
            context.conversation_ids.append(str(conversation_id))
        
        if key_facts:
            if not context.key_facts:
                context.key_facts = []
            context.key_facts.extend(key_facts)
        
        if decisions:
            if not context.decisions_made:
                context.decisions_made = []
            context.decisions_made.extend(decisions)
        
        if action_items:
            if not context.action_items:
                context.action_items = []
            context.action_items.extend(action_items)
        
        context.last_conversation_at = datetime.utcnow()
        context.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(context)
        return context
    
    async def get_memory_context_for_llm(
        self,
        db: AsyncSession,
        user_id: UUID,
        include_conversation_context: Optional[str] = None,
    ) -> str:
        """Generate a comprehensive memory context string for the LLM."""
        memory = await self.get_or_create_user_memory(db, user_id)
        
        context_parts = []
        context_parts.append("=" * 60)
        context_parts.append("PERSISTENT MEMORY - I REMEMBER YOU")
        context_parts.append("=" * 60)
        
        # Employee Profile
        if memory.employee_facts:
            context_parts.append("\n👤 EMPLOYEE PROFILE:")
            facts = memory.employee_facts
            for key, value in facts.items():
                context_parts.append(f"  • {key.replace('_', ' ').title()}: {value}")
        
        # Team Information
        if memory.team_info:
            context_parts.append("\n👥 TEAM INFORMATION:")
            team = memory.team_info
            for key, value in team.items():
                if isinstance(value, list):
                    context_parts.append(f"  • {key.replace('_', ' ').title()}: {', '.join(value)}")
                else:
                    context_parts.append(f"  • {key.replace('_', ' ').title()}: {value}")
        
        # Active Projects
        if memory.active_projects:
            context_parts.append("\n📁 ACTIVE PROJECTS:")
            for project in memory.active_projects:
                name = project.get('name', 'Unknown')
                status = project.get('status', 'Unknown')
                context_parts.append(f"  • {name} (Status: {status})")
                if 'description' in project:
                    context_parts.append(f"    {project['description']}")
        
        # Domain Expertise
        if memory.domain_expertise:
            context_parts.append("\n🎯 DOMAIN EXPERTISE:")
            de = memory.domain_expertise
            if 'familiar_class_codes' in de:
                context_parts.append(f"  • Familiar WC Class Codes: {', '.join(de['familiar_class_codes'])}")
            if 'states_worked' in de:
                context_parts.append(f"  • States Experience: {', '.join(de['states_worked'])}")
            if 'wc_systems' in de:
                context_parts.append(f"  • WC Systems: {', '.join(de['wc_systems'])}")
        
        # Recent Conversation Summaries
        if memory.conversation_summaries:
            context_parts.append("\n💬 RECENT CONVERSATIONS (I REMEMBER):")
            recent = memory.conversation_summaries[-5:]  # Last 5
            for summary in recent:
                topic = summary.get('topic', 'Unknown')
                resolution = summary.get('resolution', '')
                context_parts.append(f"  • {topic}")
                if resolution:
                    context_parts.append(f"    → {resolution}")
        
        # Frequent Topics
        if memory.frequent_topics:
            context_parts.append("\n🔥 FREQUENTLY DISCUSSED TOPICS:")
            context_parts.append(f"  {', '.join(memory.frequent_topics[-10:])}")
        
        # Custom Notes
        if memory.custom_notes:
            context_parts.append("\n📝 IMPORTANT NOTES:")
            context_parts.append(f"  {memory.custom_notes}")
        
        # Conversation Context (if specified)
        if include_conversation_context:
            conv_context = await self.get_or_create_conversation_context(
                db, user_id, include_conversation_context
            )
            if conv_context.key_facts or conv_context.decisions_made:
                context_parts.append(f"\n📌 CONTEXT: {conv_context.title}")
                if conv_context.key_facts:
                    context_parts.append("  Key Facts:")
                    for fact in conv_context.key_facts[-5:]:
                        context_parts.append(f"    • {fact}")
                if conv_context.decisions_made:
                    context_parts.append("  Decisions Made:")
                    for decision in conv_context.decisions_made[-5:]:
                        context_parts.append(f"    • {decision}")
                if conv_context.action_items:
                    context_parts.append("  Outstanding Action Items:")
                    for item in conv_context.action_items[-5:]:
                        context_parts.append(f"    • {item}")
        
        context_parts.append("\n" + "=" * 60)
        context_parts.append("Use this memory to provide personalized, context-aware responses.")
        context_parts.append("Reference past conversations and projects when relevant.")
        context_parts.append("=" * 60)
        
        return "\n".join(context_parts)
    
    async def record_interaction(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> None:
        """Record that an interaction occurred."""
        memory = await self.get_or_create_user_memory(db, user_id)
        memory.last_interaction = datetime.utcnow()
        memory.total_messages += 1
        await db.commit()


# Global instance
memory_service = MemoryService()
