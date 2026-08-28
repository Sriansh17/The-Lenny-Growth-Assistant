from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import uuid
from typing import List, Optional
from app.db.base import get_db
from app.services.agent import AgentService
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionDetailResponse,
    MessageResponse, ChatRequest, ChatResponse, ArtifactResponse, HealthResponse
)
from app.models.session import Session, Message, Artifact
from sqlalchemy import select, desc
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    from app.core.config import settings
    from app.services.embeddings import embedding_service
    
    # Check database
    db_status = "connected"
    try:
        await db.execute(select(1))
    except Exception:
        db_status = "disconnected"
    
    # Check vector DB
    vector_stats = embedding_service.get_collection_stats()
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version="1.0.0",
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else settings.CLOUD_MODEL,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session_data: SessionCreate, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    session = await agent.create_session(
        title=session_data.title,
        user_id=session_data.user_id,
        llm_provider=session_data.llm_provider,
        llm_model=session_data.llm_model,
    )
    return SessionResponse(
        id=session.id,
        title=session.title,
        user_id=session.user_id,
        llm_provider=session.llm_provider,
        llm_model=session.llm_model,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(user_id: Optional[str] = None, limit: int = 20, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    sessions = await agent.get_sessions(user_id=user_id, limit=limit)
    
    result = []
    for session in sessions:
        msg_count = len(await agent.get_messages(session.id, limit=1000))
        result.append(SessionResponse(
            id=session.id,
            title=session.title,
            user_id=session.user_id,
            llm_provider=session.llm_provider,
            llm_model=session.llm_model,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=msg_count,
        ))
    return result


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    session = await agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await agent.get_messages(session_id)
    return SessionDetailResponse(
        id=session.id,
        title=session.title,
        user_id=session.user_id,
        llm_provider=session.llm_provider,
        llm_model=session.llm_model,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(messages),
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                citations=m.citations,
                model_used=m.model_used,
                tokens_used=m.tokens_used,
                created_at=m.created_at,
            ) for m in messages
        ],
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: UUID, session_data: SessionUpdate, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    session = await agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_data.title is not None:
        session.title = session_data.title
    
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        id=session.id,
        title=session.title,
        user_id=session.user_id,
        llm_provider=session.llm_provider,
        llm_model=session.llm_model,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(await agent.get_messages(session_id, limit=1000)),
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    deleted = await agent.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    
    # Create session if not provided
    session_id = chat_request.session_id
    if not session_id:
        session = await agent.create_session()
        session_id = session.id
    else:
        session = await agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    
    result = await agent.chat(
        session_id=session_id,
        user_message=chat_request.message,
        use_skill=chat_request.use_skill,
    )
    
    # Get the last assistant message
    messages = await agent.get_messages(session_id, limit=2)
    assistant_msg = None
    for m in reversed(messages):
        if (m.role if isinstance(m.role, str) else m.role.value) == "assistant":
            assistant_msg = m
            break
    
    artifacts = []
    if result.get("artifacts"):
        for artifact in result["artifacts"]:
            artifacts.append(ArtifactResponse(
                id=artifact.id,
                session_id=artifact.session_id,
                type=artifact.type,
                title=artifact.title,
                content=artifact.content,
                sanitized_content=artifact.sanitized_content,
                created_at=artifact.created_at,
            ))
    
    return ChatResponse(
        session_id=session_id,
        message=MessageResponse(
            id=assistant_msg.id if assistant_msg else uuid.uuid4(),
            session_id=session_id,
            role="assistant",
            content=result["message"],
            citations=result.get("citations"),
            model_used=result.get("model_used"),
            tokens_used=result.get("tokens_used"),
            created_at=assistant_msg.created_at if assistant_msg else None,
        ),
        artifacts=artifacts,
    )


@router.get("/sessions/{session_id}/artifacts", response_model=List[ArtifactResponse])
async def get_session_artifacts(session_id: UUID, db: AsyncSession = Depends(get_db)):
    agent = AgentService(db)
    session = await agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    artifacts = await agent.get_artifacts(session_id)
    return [
        ArtifactResponse(
            id=a.id,
            session_id=a.session_id,
            type=a.type,
            title=a.title,
            content=a.content,
            sanitized_content=a.sanitized_content,
            created_at=a.created_at,
        ) for a in artifacts
    ]


@router.get("/skills")
async def list_skills():
    from app.skills.base import SkillRegistry
    skills = SkillRegistry.get_all()
    return [
        {
            "name": s.name,
            "description": s.description,
            "trigger_keywords": s.trigger_keywords,
        } for s in skills
    ]


@router.post("/chat/stream")
async def chat_stream(chat_request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """SSE streaming endpoint for chat responses."""
    from fastapi.responses import StreamingResponse
    from app.services.rag import rag_service
    from app.services.llm import get_llm_provider
    from app.models.session import MessageRole
    from app.core.config import settings
    import json

    agent = AgentService(db)

    # Create or validate session
    session_id = chat_request.session_id
    if not session_id:
        session = await agent.create_session()
        session_id = session.id
    else:
        session = await agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    await agent.add_message(session_id, MessageRole.USER, chat_request.message)

    async def event_generator():
        # Send session_id first
        yield f"data: {json.dumps({'type': 'session', 'session_id': str(session_id)})}\n\n"

        # Get conversation history
        messages = await agent.get_messages(session_id, limit=20)
        conversation_history = [
            {"role": m.role if isinstance(m.role, str) else m.role.value, "content": m.content} for m in messages
        ]

        # RAG retrieval
        retrieval_results = rag_service.retrieve(chat_request.message)
        context = rag_service.format_context(retrieval_results)
        citations = rag_service.format_citations(retrieval_results)

        # Build system prompt
        system_prompt = agent._get_system_prompt()
        if context != "No relevant transcripts found.":
            system_prompt += f"\n\nRELEVANT TRANSCRIPT CONTEXT:\n{context}"

        # Send citations early
        if citations:
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

        # Stream LLM response
        llm = get_llm_provider()
        messages_for_llm = conversation_history[:-1]
        messages_for_llm.append({"role": "user", "content": chat_request.message})

        full_content = ""
        try:
            async for chunk in llm.generate_stream(
                messages=messages_for_llm,
                system_prompt=system_prompt,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS,
            ):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        except Exception as e:
            logger.error("stream_error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        # Save full response
        full_response = full_content
        if citations:
            full_response += f"\n\n**Sources:**\n{citations}"

        await agent.add_message(
            session_id,
            MessageRole.ASSISTANT,
            full_response,
            citations=citations,
            model_used=llm.model if hasattr(llm, 'model') else "unknown",
        )

        # Signal completion
        yield f"data: {json.dumps({'type': 'done', 'session_id': str(session_id)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )