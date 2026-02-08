from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Enterprise AI Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://enterprise:enterprise123@localhost:5432/enterprise_ai"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "enterprise123"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM Service
    LLM_SERVICE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama2:7b"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    LLM_CONTEXT_WINDOW: int = 4096
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Vector Search
    VECTOR_SEARCH_TOP_K: int = 5
    VECTOR_SEARCH_SIMILARITY_THRESHOLD: float = 0.7
    
    # Document Processing
    MAX_DOCUMENT_SIZE_MB: int = 50
    SUPPORTED_DOCUMENT_TYPES: List[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    DOCUMENT_STORAGE_PATH: str = "/app/documents"
    
    # Knowledge Graph
    KNOWLEDGE_GRAPH_BATCH_SIZE: int = 100
    
    # Role Configuration
    ROLES: List[str] = [
        "business_analyst",
        "qa_tester",
        "developer",
        "data_engineer",
        "technical_architect",
        "project_manager",
        "manager",
        "administrator",
        "executive",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
