from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
import enum
from datetime import datetime


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

    def __str__(self):
        return self.value


class ArtifactType(str, enum.Enum):
    MARKDOWN = "markdown"
    HTML = "html"

    def __str__(self):
        return self.value


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    llm_provider = Column(String(50), nullable=False, default="ollama")
    llm_model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum('user', 'assistant', 'system', name='messagerole', create_constraint=False), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="messages")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum('markdown', 'html', name='artifacttype', create_constraint=False), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    sanitized_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("Session", back_populates="artifacts")