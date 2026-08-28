from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(
            path=settings.VECTOR_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection("lenny_transcripts")
        except Exception:
            return self.client.create_collection(
                name="lenny_transcripts",
                metadata={"hnsw:space": "cosine"},
            )

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        embeddings = self.embed_texts(documents)
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        query_embedding = self.embed_text(query_text)
        try:
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning("embedding_query_error", error=str(e))
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            return {"total_documents": count}
        except Exception as e:
            logger.warning("collection_stats_error", error=str(e))
            return {"total_documents": 0}

    def delete_collection(self) -> None:
        self.client.delete_collection("lenny_transcripts")
        self.collection = self._get_or_create_collection()


embedding_service = EmbeddingService()