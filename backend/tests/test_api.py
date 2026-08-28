import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.main import app
from app.db.base import get_db, AsyncSessionLocal
from app.models.session import Session, Message, MessageRole, Artifact, ArtifactType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_session(db_session: AsyncSession):
    session = Session(
        title="Test Session",
        user_id="test-user",
        llm_provider="ollama",
        llm_model="llama3.1:8b",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "database" in data
        assert "llm_provider" in data


class TestSessionEndpoints:
    async def test_create_session(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/sessions",
            json={"title": "New Test Session", "llm_provider": "ollama", "llm_model": "llama3.1:8b"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Test Session"
        assert data["llm_provider"] == "ollama"
        assert "id" in data

    async def test_list_sessions(self, client: AsyncClient, test_session: Session):
        response = await client.get("/api/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["id"] == str(test_session.id) for s in data)

    async def test_get_session(self, client: AsyncClient, test_session: Session):
        response = await client.get(f"/api/v1/sessions/{test_session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_session.id)
        assert data["title"] == "Test Session"
        assert "messages" in data

    async def test_get_nonexistent_session(self, client: AsyncClient):
        response = await client.get(f"/api/v1/sessions/{uuid4()}")
        assert response.status_code == 404

    async def test_update_session(self, client: AsyncClient, test_session: Session):
        response = await client.patch(
            f"/api/v1/sessions/{test_session.id}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    async def test_delete_session(self, client: AsyncClient, test_session: Session):
        response = await client.delete(f"/api/v1/sessions/{test_session.id}")
        assert response.status_code == 204
        
        # Verify deleted
        response = await client.get(f"/api/v1/sessions/{test_session.id}")
        assert response.status_code == 404


class TestChatEndpoint:
    async def test_chat_creates_session_if_none(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "Hello, this is a test message"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert len(data["message"]["content"]) > 0

    async def test_chat_uses_existing_session(self, client: AsyncClient, test_session: Session):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "Follow up question", "session_id": str(test_session.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(test_session.id)


class TestArtifactEndpoints:
    async def test_get_artifacts(self, client: AsyncClient, test_session: Session, db_session: AsyncSession):
        # Create test artifact
        artifact = Artifact(
            session_id=test_session.id,
            type=ArtifactType.MARKDOWN,
            title="Test Artifact",
            content="# Test\n\nContent here",
        )
        db_session.add(artifact)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/sessions/{test_session.id}/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test Artifact"
        assert data[0]["type"] == "markdown"


class TestSkillsEndpoint:
    async def test_list_skills(self, client: AsyncClient):
        response = await client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # ship30 and artifact
        skill_names = {s["name"] for s in data}
        assert "ship30" in skill_names
        assert "artifact" in skill_names


class TestDatabaseModels:
    async def test_session_model(self, db_session: AsyncSession):
        session = Session(
            title="Model Test",
            user_id="test",
            llm_provider="ollama",
            llm_model="llama3.1:8b",
        )
        db_session.add(session)
        await db_session.commit()
        
        result = await db_session.execute(select(Session).where(Session.title == "Model Test"))
        found = result.scalar_one()
        assert found.title == "Model Test"
        assert found.llm_provider == "ollama"

    async def test_message_model(self, db_session: AsyncSession, test_session: Session):
        message = Message(
            session_id=test_session.id,
            role=MessageRole.USER,
            content="Test message",
        )
        db_session.add(message)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Message).where(Message.session_id == test_session.id)
        )
        found = result.scalar_one()
        assert found.content == "Test message"
        assert found.role == MessageRole.USER

    async def test_artifact_model(self, db_session: AsyncSession, test_session: Session):
        artifact = Artifact(
            session_id=test_session.id,
            type=ArtifactType.HTML,
            title="HTML Artifact",
            content="<h1>Test</h1>",
            sanitized_content="<h1>Test</h1>",
        )
        db_session.add(artifact)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Artifact).where(Artifact.session_id == test_session.id)
        )
        found = result.scalar_one()
        assert found.type == ArtifactType.HTML
        assert found.title == "HTML Artifact"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])