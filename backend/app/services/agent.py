from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.base import get_db
from app.models.session import Session, Message, MessageRole, Artifact, ArtifactType
from app.services.llm import get_llm_provider, BaseLLMProvider, LLMResponse
from app.services.rag import rag_service
from app.skills.base import SkillRegistry
from app.skills.ship30 import ship30_skill
from app.skills.artifact import artifact_skill
from app.services.sanitizer import sanitize_html, create_sandboxed_html
from app.core.config import settings
import structlog
import uuid

logger = structlog.get_logger()


class AgentService:
    def __init__(self, db: AsyncSession, llm_provider: Optional[BaseLLMProvider] = None):
        self.db = db
        self.llm = llm_provider

    async def create_session(
        self,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
        llm_provider: str = "ollama",
        llm_model: str = "llama3.1:8b",
    ) -> Session:
        session = Session(
            title=title,
            user_id=user_id,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> Optional[Session]:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def get_sessions(self, user_id: Optional[str] = None, limit: int = 20) -> List[Session]:
        query = select(Session).order_by(desc(Session.updated_at)).limit(limit)
        if user_id:
            query = query.where(Session.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_session(self, session_id: UUID) -> bool:
        session = await self.get_session(session_id)
        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True
        return False

    async def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        citations: Optional[str] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role.value if isinstance(role, MessageRole) else role,
            content=content,
            citations=citations,
            model_used=model_used,
            tokens_used=tokens_used,
        )
        self.db.add(message)

        # Update session timestamp
        session = await self.get_session(session_id)
        if session:
            from datetime import datetime
            session.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(self, session_id: UUID, limit: int = 50) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def save_artifact(
        self,
        session_id: UUID,
        artifact_type: ArtifactType,
        title: str,
        content: str,
    ) -> Artifact:
        type_value = artifact_type.value if isinstance(artifact_type, ArtifactType) else artifact_type
        sanitized = sanitize_html(content) if type_value == "html" else content
        
        artifact = Artifact(
            session_id=session_id,
            type=type_value,
            title=title,
            content=content,
            sanitized_content=sanitized,
        )
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def get_artifacts(self, session_id: UUID) -> List[Artifact]:
        result = await self.db.execute(
            select(Artifact).where(Artifact.session_id == session_id)
        )
        return list(result.scalars().all())

    def _get_system_prompt(self) -> str:
        return """You are The Lenny Growth Assistant, an AI assistant grounded in Lenny's Podcast transcripts.

CORE PRINCIPLES:
1. ANSWER FROM TRANSCRIPTS ONLY - Never use outside knowledge
2. CITE SOURCES - Reference specific episodes, speakers, and quotes
3. ACKNOWLEDGE LIMITATIONS - Say when transcripts don't cover a topic
4. MAINTAIN CONTEXT - Remember conversation history within the session
5. BE PRACTICAL - Give actionable insights for product/growth work

When uncertain, say: "Based on the available transcripts, I don't have enough information to answer this confidently."

You have access to skills for specialized tasks:
- ship30: Create Ship 30 for 30 style essays
- artifact: Generate Markdown/HTML documents"""

    async def chat(
        self,
        session_id: UUID,
        user_message: str,
        use_skill: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Save user message
        await self.add_message(session_id, MessageRole.USER, user_message)

        # Get conversation history
        messages = await self.get_messages(session_id, limit=20)
        conversation_history = [
            {"role": m.role if isinstance(m.role, str) else m.role.value, "content": m.content} for m in messages
        ]

        # Check for skill trigger
        skill = None
        if use_skill:
            skill = SkillRegistry.get(use_skill)
        else:
            skill = SkillRegistry.find_triggered(user_message)

        llm = self.llm or get_llm_provider()

        if skill:
            logger.info("skill_triggered", skill=skill.name, session_id=str(session_id))
            skill_result = await skill.execute(user_message, conversation_history[:-1])

            await self.add_message(
                session_id,
                MessageRole.ASSISTANT,
                skill_result.content,
                citations=skill_result.citations,
                model_used=llm.model if hasattr(llm, 'model') else "unknown",
            )

            artifacts = []
            if skill_result.artifacts:
                for artifact_data in skill_result.artifacts:
                    artifact = await self.save_artifact(
                        session_id,
                        ArtifactType(artifact_data["type"]),
                        artifact_data["title"],
                        artifact_data["content"],
                    )
                    artifacts.append(artifact)

            return {
                "message": skill_result.content,
                "citations": skill_result.citations,
                "artifacts": artifacts,
                "skill_used": skill.name,
            }

        # Use Anthropic Agent (tool-use) when provider is anthropic
        if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            try:
                from app.agents import get_anthropic_agent
                anthropic_agent = get_anthropic_agent()
                if anthropic_agent:
                    logger.info("using_anthropic_agent", session_id=str(session_id))
                    result = await anthropic_agent.run(
                        user_message=user_message,
                        conversation_history=conversation_history[:-1],
                    )

                    artifacts = []
                    for artifact_data in result.get("artifacts", []):
                        artifact = await self.save_artifact(
                            session_id,
                            ArtifactType(artifact_data["type"]),
                            artifact_data["title"],
                            artifact_data["content"],
                        )
                        artifacts.append(artifact)

                    full_response = result["content"]
                    if result.get("citations"):
                        full_response += f"\n\n**Sources:**\n{result['citations']}"

                    await self.add_message(
                        session_id,
                        MessageRole.ASSISTANT,
                        full_response,
                        citations=result.get("citations"),
                        model_used=result.get("model", "claude"),
                        tokens_used=result.get("tokens_used"),
                    )

                    return {
                        "message": full_response,
                        "citations": result.get("citations"),
                        "artifacts": artifacts,
                        "skill_used": None,
                    }
            except Exception as e:
                logger.warning("anthropic_agent_fallback", error=str(e))
                # Fall through to standard RAG

        # Standard RAG response (Ollama / OpenAI / fallback)
        retrieval_results = rag_service.retrieve(user_message)
        context = rag_service.format_context(retrieval_results)
        citations = rag_service.format_citations(retrieval_results)

        system_prompt = self._get_system_prompt()
        if context != "No relevant transcripts found.":
            system_prompt += f"\n\nRELEVANT TRANSCRIPT CONTEXT:\n{context}"

        messages_for_llm = conversation_history[:-1]  # Exclude current user message
        messages_for_llm.append({"role": "user", "content": user_message})

        response = await llm.generate(
            messages=messages_for_llm,
            system_prompt=system_prompt,
            temperature=settings.MODEL_TEMPERATURE,
            max_tokens=settings.MODEL_MAX_TOKENS,
        )

        # Add citations to response
        full_response = response.content
        if citations:
            full_response += f"\n\n**Sources:**\n{citations}"

        # Save assistant response
        await self.add_message(
            session_id,
            MessageRole.ASSISTANT,
            full_response,
            citations=citations,
            model_used=response.model,
            tokens_used=response.tokens_used,
        )

        return {
            "message": full_response,
            "citations": citations,
            "artifacts": [],
            "skill_used": None,
        }

    async def chat_stream(
        self,
        session_id: UUID,
        user_message: str,
        use_skill: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        # Save user message
        await self.add_message(session_id, MessageRole.USER, user_message)

        # Get conversation history
        messages = await self.get_messages(session_id, limit=20)
        conversation_history = [
            {"role": m.role if isinstance(m.role, str) else m.role.value, "content": m.content} for m in messages
        ]

        # Check for skill trigger
        skill = None
        if use_skill:
            skill = SkillRegistry.get(use_skill)
        else:
            skill = SkillRegistry.find_triggered(user_message)

        llm = self.llm or get_llm_provider()

        if skill:
            # For skills, we generate the full response first (skills are complex)
            skill_result = await skill.execute(user_message, conversation_history[:-1])

            await self.add_message(
                session_id,
                MessageRole.ASSISTANT,
                skill_result.content,
                citations=skill_result.citations,
                model_used=llm.model if hasattr(llm, 'model') else "unknown",
            )

            # Save artifacts
            if skill_result.artifacts:
                for artifact_data in skill_result.artifacts:
                    await self.save_artifact(
                        session_id,
                        ArtifactType(artifact_data["type"]),
                        artifact_data["title"],
                        artifact_data["content"],
                    )

            # Stream the result in chunks
            words = skill_result.content.split()
            for i in range(0, len(words), 10):
                chunk = " ".join(words[i:i+10]) + " "
                yield chunk
            return

        # Standard RAG streaming
        retrieval_results = rag_service.retrieve(user_message)
        context = rag_service.format_context(retrieval_results)
        citations = rag_service.format_citations(retrieval_results)

        system_prompt = self._get_system_prompt()
        if context != "No relevant transcripts found.":
            system_prompt += f"\n\nRELEVANT TRANSCRIPT CONTEXT:\n{context}"

        messages_for_llm = conversation_history[:-1]
        messages_for_llm.append({"role": "user", "content": user_message})

        full_content = ""
        async for chunk in llm.generate_stream(
            messages=messages_for_llm,
            system_prompt=system_prompt,
            temperature=settings.MODEL_TEMPERATURE,
            max_tokens=settings.MODEL_MAX_TOKENS,
        ):
            full_content += chunk
            yield chunk

        # Add citations
        if citations:
            full_content += f"\n\n**Sources:**\n{citations}"

        # Save assistant response
        await self.add_message(
            session_id,
            MessageRole.ASSISTANT,
            full_content,
            citations=citations,
            model_used=llm.model if hasattr(llm, 'model') else "unknown",
        )