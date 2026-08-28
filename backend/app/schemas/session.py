from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ArtifactType(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"


class MessageBase(BaseModel):
    role: MessageRole
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: UUID
    session_id: UUID
    citations: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    title: Optional[str] = None
    user_id: Optional[str] = None


class SessionCreate(SessionBase):
    llm_provider: Literal["anthropic", "openai", "ollama"] = "ollama"
    llm_model: str = "llama3.1:8b"


class SessionUpdate(BaseModel):
    title: Optional[str] = None


class SessionResponse(SessionBase):
    id: UUID
    llm_provider: str
    llm_model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []


class ArtifactBase(BaseModel):
    type: ArtifactType
    title: str
    content: str


class ArtifactCreate(ArtifactBase):
    pass


class ArtifactResponse(ArtifactBase):
    id: UUID
    session_id: UUID
    sanitized_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: Optional[UUID] = None
    use_skill: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: UUID
    message: MessageResponse
    artifacts: List[ArtifactResponse] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    llm_provider: str
    llm_model: str