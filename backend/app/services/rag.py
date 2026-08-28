from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.services.embeddings import embedding_service
from app.core.config import settings
import structlog

logger = structlog.get_logger()


@dataclass
class RetrievalResult:
    content: str
    metadata: Dict[str, Any]
    score: float


class RAGService:
    def __init__(self):
        self.top_k = settings.TOP_K_RETRIEVAL
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD

    def retrieve(self, query: str, filter_metadata: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        try:
            results = embedding_service.query(
                query_text=query,
                n_results=self.top_k,
                where=filter_metadata,
            )
        except Exception as e:
            logger.warning("retrieval_error", error=str(e), query=query[:50])
            return []

        retrieval_results = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                score = 1.0 - distance

                if score >= self.similarity_threshold:
                    retrieval_results.append(RetrievalResult(
                        content=doc,
                        metadata=metadata,
                        score=score,
                    ))

        logger.info("retrieval_complete", query=query[:50], results=len(retrieval_results))
        return retrieval_results

    def format_context(self, results: List[RetrievalResult]) -> str:
        if not results:
            return "No relevant transcripts found."

        context_parts = []
        for i, result in enumerate(results, 1):
            source = f"[{result.metadata.get('title', 'Unknown')} - {result.metadata.get('source', 'Unknown')}]"
            context_parts.append(f"Source {i} {source}:\n{result.content}\n")

        return "\n---\n".join(context_parts)

    def format_citations(self, results: List[RetrievalResult]) -> str:
        if not results:
            return ""

        citations = []
        for i, result in enumerate(results, 1):
            title = result.metadata.get("title", "Unknown")
            source = result.metadata.get("source", "Unknown")
            url = result.metadata.get("url", "")
            citation = f"[{i}] {title} ({source})"
            if url:
                citation += f" - {url}"
            citations.append(citation)

        return "\n".join(citations)


rag_service = RAGService()