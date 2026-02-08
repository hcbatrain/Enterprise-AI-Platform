import httpx
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with LLM models via Ollama/vLLM."""
    
    def __init__(self):
        self.base_url = settings.LLM_SERVICE_URL
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.context_window = settings.LLM_CONTEXT_WINDOW
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Generate a completion from the LLM."""
        
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add context messages if provided
        if context:
            messages.extend(context)
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "content": result.get("message", {}).get("content", ""),
                    "model": self.model,
                    "tokens_used": result.get("eval_count", 0),
                    "done": result.get("done", False),
                }
        
        except httpx.HTTPError as e:
            logger.error(f"LLM HTTP error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion from the LLM."""
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=120.0,
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
        
        except httpx.HTTPError as e:
            logger.error(f"LLM streaming HTTP error: {e}")
            raise Exception(f"Failed to generate streaming response: {str(e)}")
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts using the embedding model."""
        
        embeddings = []
        
        try:
            async with httpx.AsyncClient() as client:
                for text in texts:
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={
                            "model": settings.EMBEDDING_MODEL,
                            "prompt": text,
                        },
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    result = response.json()
                    embeddings.append(result.get("embedding", []))
        
        except httpx.HTTPError as e:
            logger.error(f"Embedding HTTP error: {e}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
        
        return embeddings
    
    def create_system_prompt(
        self,
        role: str,
        context: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """Create a role-aware system prompt."""
        
        base_prompt = f"""You are an Enterprise AI Assistant for an insurance software organization.
You have deep expertise in Workers' Compensation insurance and the Sapiens CourseSuite platform.

Current User Role: {role.replace('_', ' ').title()}
"""
        
        # Add role-specific instructions
        role_instructions = {
            "business_analyst": """
Focus on business impact, workflows, requirements, and stakeholder needs.
Provide clear explanations of business rules, exceptions, and process flows.
Use business terminology and reference BRDs, FRDs, and user stories when relevant.""",
            
            "developer": """
Focus on technical implementation details, APIs, database schemas, and code examples.
Provide SQL queries, code snippets, and technical architecture explanations.
Reference specific tables, fields, and integration points.""",
            
            "qa_tester": """
Focus on test scenarios, validation rules, edge cases, and acceptance criteria.
Provide test case templates, test data examples, and regression considerations.
Highlight potential issues and testing strategies.""",
            
            "technical_architect": """
Focus on system design, integration patterns, scalability, and technical trade-offs.
Provide architecture diagrams context, data flows, and dependency analysis.
Reference design patterns and architectural decisions.""",
            
            "manager": """
Focus on business impact, risk assessment, resource allocation, and compliance.
Provide high-level summaries, metrics, and strategic considerations.
Highlight organizational implications and decision factors.""",
            
            "executive": """
Focus on strategic value, ROI, risk mitigation, and organizational impact.
Provide concise summaries with key metrics and recommendations.
Highlight business outcomes and competitive advantages.""",
        }
        
        if role in role_instructions:
            base_prompt += role_instructions[role]
        
        if domain:
            base_prompt += f"\n\nDomain Context: {domain}"
        
        if context:
            base_prompt += f"\n\nAdditional Context:\n{context}"
        
        base_prompt += """

Guidelines:
- Always cite sources when providing information from documents
- If unsure, acknowledge uncertainty rather than hallucinating
- Provide code examples in the appropriate language (SQL, Python, Java, etc.)
- Explain both business logic and technical implementation when relevant
- Use the terminology appropriate for the user's role"""
        
        return base_prompt


# Global instance
llm_service = LLMService()
