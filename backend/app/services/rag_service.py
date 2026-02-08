from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.models.document import Document, DocumentChunk
from app.services.llm_service import llm_service

logger = get_logger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service."""
    
    def __init__(self):
        self.top_k = settings.VECTOR_SEARCH_TOP_K
        self.similarity_threshold = settings.VECTOR_SEARCH_SIMILARITY_THRESHOLD
    
    async def search_documents(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks using vector similarity."""
        
        # Get query embedding
        embeddings = await llm_service.get_embeddings([query])
        if not embeddings or not embeddings[0]:
            logger.error("Failed to generate query embedding")
            return []
        
        query_embedding = embeddings[0]
        
        # Build the similarity search query
        # Using pgvector's <=> operator for cosine distance
        similarity_threshold = self.similarity_threshold
        limit = top_k or self.top_k
        
        # Build filter conditions
        filter_conditions = []
        filter_params = {"query_embedding": query_embedding, "threshold": similarity_threshold, "limit": limit}
        
        if filters:
            if "document_type" in filters:
                filter_conditions.append("d.mime_type = :mime_type")
                filter_params["mime_type"] = filters["document_type"]
            if "tags" in filters:
                filter_conditions.append("d.tags && :tags")
                filter_params["tags"] = filters["tags"]
            if "team" in filters:
                filter_conditions.append("(:team = ANY(d.team_access) OR d.is_public = true)")
                filter_params["team"] = filters["team"]
        
        where_clause = ""
        if filter_conditions:
            where_clause = "AND " + " AND ".join(filter_conditions)
        
        sql = text(f"""
            SELECT 
                dc.id,
                dc.content,
                dc.chunk_index,
                dc.metadata_json,
                d.id as document_id,
                d.title as document_title,
                d.filename,
                d.mime_type,
                1 - (dc.embedding <=> :query_embedding) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.embedding IS NOT NULL
            AND 1 - (dc.embedding <=> :query_embedding) > :threshold
            {where_clause}
            ORDER BY dc.embedding <=> :query_embedding
            LIMIT :limit
        """)
        
        try:
            result = await db.execute(sql, filter_params)
            rows = result.fetchall()
            
            documents = []
            for row in rows:
                documents.append({
                    "chunk_id": str(row.id),
                    "content": row.content,
                    "chunk_index": row.chunk_index,
                    "metadata": row.metadata_json,
                    "document_id": str(row.document_id),
                    "document_title": row.document_title,
                    "filename": row.filename,
                    "mime_type": row.mime_type,
                    "similarity": float(row.similarity),
                })
            
            return documents
        
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector similarity and keyword matching."""
        
        # Get vector search results
        vector_results = await self.search_documents(db, query, top_k * 2, filters)
        
        # Get keyword search results
        keyword_results = await self.keyword_search(db, query, top_k * 2, filters)
        
        # Combine and deduplicate results
        seen_ids = set()
        combined_results = []
        
        # Add vector results first (higher priority)
        for result in vector_results:
            if result["chunk_id"] not in seen_ids:
                seen_ids.add(result["chunk_id"])
                result["search_type"] = "vector"
                combined_results.append(result)
        
        # Add keyword results
        for result in keyword_results:
            if result["chunk_id"] not in seen_ids:
                seen_ids.add(result["chunk_id"])
                result["search_type"] = "keyword"
                combined_results.append(result)
        
        # Sort by combined score and limit
        combined_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return combined_results[:top_k or self.top_k]
    
    async def keyword_search(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based search on document chunks."""
        
        # Build filter conditions
        filter_conditions = []
        filter_params = {"query": f"%{query}%", "limit": top_k or self.top_k}
        
        if filters:
            if "document_type" in filters:
                filter_conditions.append("d.mime_type = :mime_type")
                filter_params["mime_type"] = filters["document_type"]
            if "tags" in filters:
                filter_conditions.append("d.tags && :tags")
                filter_params["tags"] = filters["tags"]
        
        where_clause = ""
        if filter_conditions:
            where_clause = "AND " + " AND ".join(filter_conditions)
        
        sql = text(f"""
            SELECT 
                dc.id,
                dc.content,
                dc.chunk_index,
                dc.metadata_json,
                d.id as document_id,
                d.title as document_title,
                d.filename,
                d.mime_type,
                similarity(dc.content, :query) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.content ILIKE :query
            {where_clause}
            ORDER BY similarity DESC
            LIMIT :limit
        """)
        
        try:
            result = await db.execute(sql, filter_params)
            rows = result.fetchall()
            
            documents = []
            for row in rows:
                documents.append({
                    "chunk_id": str(row.id),
                    "content": row.content,
                    "chunk_index": row.chunk_index,
                    "metadata": row.metadata_json,
                    "document_id": str(row.document_id),
                    "document_title": row.document_title,
                    "filename": row.filename,
                    "mime_type": row.mime_type,
                    "similarity": float(row.similarity) if row.similarity else 0.5,
                })
            
            return documents
        
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    async def generate_with_context(
        self,
        db: AsyncSession,
        query: str,
        user_role: str = "developer",
        conversation_context: Optional[List[Dict[str, str]]] = None,
        persistent_memory: Optional[str] = None,  # NEW: Persistent memory across sessions
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a response using RAG with retrieved context AND persistent memory."""
        
        # Search for relevant documents
        relevant_docs = await self.hybrid_search(db, query, top_k, filters)
        
        if not relevant_docs:
            logger.warning(f"No relevant documents found for query: {query[:100]}...")
        
        # Build context from retrieved documents
        context_parts = []
        sources = []
        
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"[Source {i}] From {doc['document_title']}:\n{doc['content']}\n")
            sources.append({
                "index": i,
                "document_id": doc["document_id"],
                "document_title": doc["document_title"],
                "chunk_id": doc["chunk_id"],
                "similarity": doc["similarity"],
                "search_type": doc.get("search_type", "vector"),
            })
        
        context_text = "\n".join(context_parts)
        
        # Build the enhanced prompt with PERSISTENT MEMORY
        memory_section = ""
        if persistent_memory:
            memory_section = f"""
================================================================================
PERSISTENT MEMORY - I REMEMBER OUR PAST CONVERSATIONS
================================================================================
{persistent_memory}
================================================================================
"""
        
        prompt = f"""{memory_section}

Based on the following retrieved documents and my memory of our past conversations, please answer the user's question.

Retrieved Documents:
{context_text}

User Question: {query}

Please provide a comprehensive, personalized answer that:
1. Directly addresses the question
2. References our past conversations and your context when relevant
3. Cites specific document sources using [Source X] notation
4. Includes relevant technical details appropriate for a {user_role.replace('_', ' ')}
5. Acknowledges your specific projects, team context, and expertise
6. Builds upon previous discussions we've had

Answer:"""
        
        # Generate enhanced system prompt with memory awareness
        system_prompt = llm_service.create_system_prompt(
            role=user_role,
            context=persistent_memory  # Pass memory to system prompt
        )
        
        # Add memory-aware instructions to system prompt
        system_prompt += """

================================================================================
MEMORY AWARENESS INSTRUCTIONS:
================================================================================
You have access to PERSISTENT MEMORY about the user. This memory includes:
- Employee profile and background
- Team and company context
- Active and past projects
- Domain expertise and familiar topics
- Recent conversation summaries
- Frequently discussed topics

IMPORTANT RULES:
1. ALWAYS reference relevant past conversations when appropriate
2. Remember the user's specific context (team, projects, expertise)
3. Build upon previous discussions - don't start from scratch
4. Acknowledge when you're recalling something from memory
5. Use phrases like "As we discussed before..." or "Based on your work with..."
6. If the user mentions a project, reference what you know about it
7. Personalize responses based on their role and expertise level
8. NEVER say "I don't have memory" - you DO have persistent memory

This memory persists across ALL conversations, even if the user closes and reopens the chat.
================================================================================
"""
        
        # Generate response with full context
        response = await llm_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            context=conversation_context,
        )
        
        return {
            "content": response["content"],
            "sources": sources,
            "model": response["model"],
            "tokens_used": response["tokens_used"],
        }
    
    async def get_document_summary(
        self,
        db: AsyncSession,
        document_id: str,
    ) -> Optional[str]:
        """Generate a summary of a document."""
        
        # Get all chunks for the document
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = result.scalars().all()
        
        if not chunks:
            return None
        
        # Combine chunk contents (limit to first few chunks for summary)
        content = "\n\n".join([chunk.content for chunk in chunks[:5]])
        
        prompt = f"""Please provide a concise summary (2-3 paragraphs) of the following document:

{content}

Summary:"""
        
        response = await llm_service.generate(prompt=prompt)
        return response["content"]


# Global instance
rag_service = RAGService()
