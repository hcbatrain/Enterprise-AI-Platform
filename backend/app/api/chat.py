from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from app.db.session import get_db
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.models.conversation import Conversation, Message

router = APIRouter()
logger = get_logger(__name__)


class MessageCreate(BaseModel):
    content: str
    conversation_id: Optional[str] = None
    context_type: Optional[str] = "general"
    context_id: Optional[str] = None
    context_key: Optional[str] = None  # For persistent conversation context


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]]
    created_at: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    context_type: Optional[str] = "general"
    context_id: Optional[str] = None
    context_key: Optional[str] = None  # e.g., "WC_Migration_Phase2"


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    context_type: str
    message_count: int
    created_at: str
    updated_at: str


class MemoryUpdateRequest(BaseModel):
    category: str  # employee, project, domain, preference
    key: str
    value: str
    tags: Optional[List[str]] = None


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation with persistent memory support."""
    
    conversation = Conversation(
        id=uuid.uuid4(),
        title=data.title or "New Conversation",
        user_id=current_user.id,
        context_type=data.context_type or "general",
        context_id=data.context_id,
        user_role=current_user.role,
        team_context=current_user.team,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    # If context_key provided, link to persistent conversation context
    if data.context_key:
        await memory_service.add_conversation_to_context(
            db, current_user.id, data.context_key, conversation.id
        )
    
    # Update user memory with new conversation
    memory = await memory_service.get_or_create_user_memory(db, current_user.id)
    memory.total_conversations += 1
    await db.commit()
    
    return conversation.to_dict()


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    context_key: Optional[str] = None,  # Filter by persistent context
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's conversations with optional context filtering."""
    from sqlalchemy import select
    
    # If context_key provided, get conversations from persistent context
    if context_key:
        context = await memory_service.get_or_create_conversation_context(
            db, current_user.id, context_key
        )
        if context.conversation_ids:
            result = await db.execute(
                select(Conversation)
                .where(Conversation.id.in_(context.conversation_ids))
                .where(Conversation.is_active == True)
                .order_by(Conversation.updated_at.desc())
            )
            conversations = result.scalars().all()
            return [conv.to_dict() for conv in conversations]
    
    # Standard conversation list
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .where(Conversation.is_active == True)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    conversations = result.scalars().all()
    return [conv.to_dict() for conv in conversations]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all messages and persistent memory context."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user.id)
    )
    
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    # Get persistent memory context for this user
    memory_context = await memory_service.get_memory_context_for_llm(
        db, current_user.id
    )
    
    return {
        **conversation.to_dict(),
        "messages": [msg.to_dict() for msg in conversation.messages],
        "persistent_memory": memory_context if memory_context else None,
    }


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI response with persistent memory."""
    from sqlalchemy import select
    
    # Get or create conversation
    if data.conversation_id:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == data.conversation_id)
            .where(Conversation.user_id == current_user.id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        conversation = Conversation(
            id=uuid.uuid4(),
            title=data.content[:50] + "..." if len(data.content) > 50 else data.content,
            user_id=current_user.id,
            context_type=data.context_type or "general",
            context_id=data.context_id,
            user_role=current_user.role,
            team_context=current_user.team,
        )
        db.add(conversation)
        
        # Update conversation count in memory
        memory = await memory_service.get_or_create_user_memory(db, current_user.id)
        memory.total_conversations += 1
    
    # Save user message
    user_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    
    # Get conversation history for context
    history = []
    for msg in conversation.messages[-10:]:  # Last 10 messages
        history.append({"role": msg.role, "content": msg.content})
    
    # Get PERSISTENT MEMORY context - this survives across all sessions!
    persistent_memory = await memory_service.get_memory_context_for_llm(
        db, 
        current_user.id,
        include_conversation_context=data.context_key
    )
    
    # Record this interaction
    await memory_service.record_interaction(db, current_user.id)
    
    # Extract and store key facts from user message (simple keyword-based extraction)
    await extract_and_store_facts(db, current_user.id, conversation.id, data.content)
    
    # Add frequent topic
    await memory_service.add_frequent_topic(db, current_user.id, extract_topic(data.content))
    
    # Generate response with RAG + persistent memory
    try:
        response_data = await rag_service.generate_with_context(
            db=db,
            query=data.content,
            user_role=current_user.role,
            conversation_context=history if len(history) > 0 else None,
            persistent_memory=persistent_memory,  # Pass persistent memory!
            filters={"team": current_user.team} if current_user.team else None,
        )
        
        # Save assistant message
        assistant_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="assistant",
            content=response_data["content"],
            model=response_data["model"],
            tokens_used=response_data["tokens_used"],
            sources=response_data["sources"],
        )
        db.add(assistant_message)
        
        # Update conversation
        conversation.message_count += 2
        conversation.last_message_at = datetime.utcnow()
        await db.commit()
        
        # If context_key provided, link conversation to persistent context
        if data.context_key:
            await memory_service.add_conversation_to_context(
                db, current_user.id, data.context_key, conversation.id
            )
        
        return assistant_message.to_dict()
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to generate response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}",
        )


@router.get("/memory")
async def get_user_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the persistent memory for the current user."""
    memory = await memory_service.get_or_create_user_memory(db, current_user.id)
    return memory.to_dict()


@router.post("/memory")
async def update_user_memory(
    data: MemoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update persistent memory for the current user."""
    entry = await memory_service.add_memory_entry(
        db,
        current_user.id,
        data.category,
        data.key,
        data.value,
        tags=data.tags
    )
    return entry.to_dict()


@router.post("/memory/employee")
async def update_employee_facts(
    facts: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update employee facts in persistent memory."""
    memory = await memory_service.update_employee_facts(
        db, current_user.id, facts
    )
    return memory.to_dict()


@router.post("/memory/project")
async def add_project(
    project: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a project to persistent memory."""
    memory = await memory_service.add_active_project(
        db, current_user.id, project
    )
    return memory.to_dict()


@router.get("/memory/contexts")
async def list_conversation_contexts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all persistent conversation contexts for the user."""
    from sqlalchemy import select
    from app.models.user_memory import ConversationContext
    
    result = await db.execute(
        select(ConversationContext)
        .where(ConversationContext.user_id == current_user.id)
        .order_by(ConversationContext.updated_at.desc())
    )
    contexts = result.scalars().all()
    return [ctx.to_dict() for ctx in contexts]


@router.get("/memory/contexts/{context_key}")
async def get_conversation_context(
    context_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific persistent conversation context."""
    context = await memory_service.get_or_create_conversation_context(
        db, current_user.id, context_key
    )
    return context.to_dict()


@router.post("/messages/stream")
async def send_message_stream(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get streaming AI response with persistent memory."""
    
    async def generate_stream():
        # Get persistent memory for context
        persistent_memory = await memory_service.get_memory_context_for_llm(
            db, current_user.id
        )
        
        # In production, integrate with LLM's streaming API
        # For now, simulate streaming with memory context awareness
        response_chunks = [
            "I'm ",
            "analyzing ",
            "your ",
            "question ",
            "with ",
            "your ",
            "persistent ",
            "memory ",
            "context..."
        ]
        
        for chunk in response_chunks:
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        yield f"data: {json.dumps({'done': True, 'memory_used': True})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
    )


@router.post("/messages/{message_id}/feedback")
async def provide_feedback(
    message_id: str,
    rating: int = Field(..., ge=1, le=5),
    comment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Provide feedback on an AI response."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Message)
        .where(Message.id == message_id)
        .where(Message.role == "assistant")
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    message.feedback_rating = rating
    message.feedback_comment = comment
    await db.commit()
    
    return {"message": "Feedback recorded"}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation (soft delete)."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user.id)
    )
    
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    conversation.is_active = False
    await db.commit()
    
    return {"message": "Conversation deleted"}


# Helper functions

def extract_topic(message: str) -> str:
    """Extract the main topic from a message for frequent topics tracking."""
    # Simple keyword-based extraction
    keywords = {
        "policy": "WC Policies",
        "class code": "Class Codes",
        "rating": "Rating Algorithms",
        "conversion": "Data Conversion",
        "migration": "Data Migration",
        "sapiens": "Sapiens CourseSuite",
        "premium": "Premium Calculation",
        "claim": "Claims",
        "endorsement": "Endorsements",
        "state": "State Requirements",
        "report": "Reporting",
        "test": "Testing",
        "sql": "SQL Queries",
        "api": "API Integration",
    }
    
    message_lower = message.lower()
    for keyword, topic in keywords.items():
        if keyword in message_lower:
            return topic
    
    return "General"


async def extract_and_store_facts(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    message: str
):
    """Extract key facts from user message and store in memory."""
    # This is a simplified fact extraction
    # In production, you could use the LLM to extract facts
    
    message_lower = message.lower()
    
    # Extract project mentions
    if "working on" in message_lower or "project" in message_lower:
        # Try to extract project name
        import re
        project_match = re.search(r'(?:working on|project)\s+["\']?([^"\'.]+)', message_lower)
        if project_match:
            project_name = project_match.group(1).strip().title()
            await memory_service.add_active_project(
                db, user_id,
                {"name": project_name, "last_mentioned": datetime.utcnow().isoformat()}
            )
    
    # Extract state mentions
    states = ["california", "ca", "new york", "ny", "texas", "tx", "florida", "fl"]
    mentioned_states = [s.upper() for s in states if s in message_lower]
    if mentioned_states:
        await memory_service.update_domain_expertise(
            db, user_id,
            {"states_worked": mentioned_states}
        )
    
    # Extract class code mentions
    class_code_match = re.search(r'\b(\d{4})\b', message)
    if class_code_match:
        class_code = class_code_match.group(1)
        await memory_service.update_domain_expertise(
            db, user_id,
            {"familiar_class_codes": [class_code]}
        )
