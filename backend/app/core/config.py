from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Literal
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "The Lenny Growth Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_assistant",
        description="PostgreSQL connection string"
    )
    DATABASE_ECHO: bool = False

    # Vector Database
    VECTOR_DB_PATH: str = "./data/chroma"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # LLM Configuration
    LLM_PROVIDER: Literal["anthropic", "openai", "ollama"] = "ollama"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    CLOUD_MODEL: str = "claude-3-5-sonnet-20241022"
    MODEL_TEMPERATURE: float = 0.3
    MODEL_MAX_TOKENS: int = 4096

    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    # Session
    SESSION_TTL_HOURS: int = 24

    # Security
    SECRET_KEY: str = Field(default="dev-secret-change-in-production", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "console"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()