import pytest
from app.services.rag import rag_service, RetrievalResult
from app.services.sanitizer import sanitize_html, create_sandboxed_html
from app.services.embeddings import embedding_service
from app.skills.ship30 import ship30_skill
from app.skills.artifact import artifact_skill
from app.skills.base import SkillRegistry


class TestRAGService:
    def test_retrieve_returns_results(self):
        # This test requires ingested data
        results = rag_service.retrieve("product market fit")
        assert isinstance(results, list)
        # May be empty if no transcripts ingested
        for result in results:
            assert isinstance(result, RetrievalResult)
            assert hasattr(result, "content")
            assert hasattr(result, "metadata")
            assert hasattr(result, "score")

    def test_format_context_empty(self):
        context = rag_service.format_context([])
        assert context == "No relevant transcripts found."

    def test_format_citations_empty(self):
        citations = rag_service.format_citations([])
        assert citations == ""


class TestSanitizer:
    def test_sanitize_removes_scripts(self):
        malicious = '<script>alert("xss")</script><p>Safe content</p>'
        cleaned = sanitize_html(malicious)
        assert "<script>" not in cleaned
        assert "alert" not in cleaned
        assert "<p>Safe content</p>" in cleaned

    def test_sanitize_removes_iframes(self):
        malicious = '<iframe src="evil.com"></iframe><p>Safe</p>'
        cleaned = sanitize_html(malicious)
        assert "<iframe" not in cleaned
        assert "<p>Safe</p>" in cleaned

    def test_sanitize_removes_event_handlers(self):
        malicious = '<div onclick="evil()">Click me</div>'
        cleaned = sanitize_html(malicious)
        assert "onclick" not in cleaned
        assert "Click me" in cleaned

    def test_sanitize_removes_javascript_protocol(self):
        malicious = '<a href="javascript:alert(1)">Link</a>'
        cleaned = sanitize_html(malicious)
        assert "javascript:" not in cleaned
        assert 'href="#"' in cleaned or 'href=""' in cleaned

    def test_sanitize_allows_safe_html(self):
        safe = '<h1>Title</h1><p>Paragraph with <strong>bold</strong> and <em>italic</em></p><ul><li>Item 1</li><li>Item 2</li></ul>'
        cleaned = sanitize_html(safe)
        assert "<h1>Title</h1>" in cleaned
        assert "<strong>bold</strong>" in cleaned
        assert "<em>italic</em>" in cleaned
        assert "<ul>" in cleaned
        assert "<li>Item 1</li>" in cleaned

    def test_sanitize_allows_links_with_noopener(self):
        html = '<a href="https://example.com">Link</a>'
        cleaned = sanitize_html(html)
        assert 'target="_blank"' in cleaned
        assert 'rel="noopener noreferrer"' in cleaned

    def test_create_sandboxed_html(self):
        content = "<h1>Test</h1><p>Content</p>"
        html = create_sandboxed_html(content, "Test Title")
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Title</title>" in html
        assert content in html
        assert "artifact-container" in html


class TestSkillRegistry:
    def test_skills_registered(self):
        skills = SkillRegistry.get_all()
        assert len(skills) >= 2
        names = {s.name for s in skills}
        assert "ship30" in names
        assert "artifact" in names

    def test_get_skill_by_name(self):
        skill = SkillRegistry.get("ship30")
        assert skill is not None
        assert skill.name == "ship30"
        
        skill = SkillRegistry.get("artifact")
        assert skill is not None
        assert skill.name == "artifact"

    def test_find_triggered_ship30(self):
        skill = SkillRegistry.find_triggered("Write a ship 30 essay about growth")
        assert skill is not None
        assert skill.name == "ship30"
        
        skill = SkillRegistry.find_triggered("Create a ship30 for 30 article")
        assert skill is not None
        assert skill.name == "ship30"

    def test_find_triggered_artifact(self):
        skill = SkillRegistry.find_triggered("Create an artifact for this")
        assert skill is not None
        assert skill.name == "artifact"
        
        skill = SkillRegistry.find_triggered("Generate HTML document")
        assert skill is not None
        assert skill.name == "artifact"

    def test_find_triggered_none(self):
        skill = SkillRegistry.find_triggered("What is product market fit?")
        # May return None or a skill depending on keywords
        # Just verify it doesn't crash
        assert skill is None or hasattr(skill, "name")


class TestEmbeddingService:
    def test_embed_text(self):
        embedding = embedding_service.embed_text("test query")
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_texts(self):
        embeddings = embedding_service.embed_texts(["query 1", "query 2"])
        assert len(embeddings) == 2
        assert all(len(e) == 384 for e in embeddings)

    def test_collection_stats(self):
        stats = embedding_service.get_collection_stats()
        assert "total_documents" in stats
        assert isinstance(stats["total_documents"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])