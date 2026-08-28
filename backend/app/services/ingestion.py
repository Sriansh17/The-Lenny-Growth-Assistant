from pathlib import Path
from typing import List, Dict, Any
import json
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.embeddings import embedding_service
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class TranscriptIngestionService:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.data_dir = Path("data/transcripts")

    def load_transcripts(self) -> List[Dict[str, Any]]:
        transcripts = []
        if not self.data_dir.exists():
            logger.warning("transcripts_dir_not_found", path=str(self.data_dir))
            return transcripts

        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    transcripts.append({
                        "source": file_path.stem,
                        "title": data.get("title", file_path.stem),
                        "url": data.get("url", ""),
                        "date": data.get("date", ""),
                        "content": data.get("content", ""),
                        "speaker": data.get("speaker", "Lenny"),
                    })
            except Exception as e:
                logger.error("transcript_load_error", file=str(file_path), error=str(e))

        return transcripts

    def chunk_transcript(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = self.splitter.split_text(transcript["content"])
        chunked = []
        for i, chunk in enumerate(chunks):
            chunked.append({
                "id": f"{transcript['source']}-{i}",
                "source": transcript["source"],
                "title": transcript["title"],
                "url": transcript["url"],
                "date": transcript["date"],
                "speaker": transcript["speaker"],
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
        return chunked

    def ingest_all(self) -> Dict[str, Any]:
        transcripts = self.load_transcripts()
        if not transcripts:
            return {"status": "no_transcripts_found", "count": 0}

        all_chunks = []
        for transcript in transcripts:
            chunks = self.chunk_transcript(transcript)
            all_chunks.extend(chunks)

        if not all_chunks:
            return {"status": "no_chunks_created", "count": 0}

        documents = [c["content"] for c in all_chunks]
        metadatas = [{
            "source": c["source"],
            "title": c["title"],
            "url": c["url"],
            "date": c["date"],
            "speaker": c["speaker"],
            "chunk_index": c["chunk_index"],
            "total_chunks": c["total_chunks"],
        } for c in all_chunks]
        ids = [c["id"] for c in all_chunks]

        embedding_service.add_documents(documents, metadatas, ids)

        logger.info("ingestion_complete", chunks=len(all_chunks), sources=len(transcripts))
        return {
            "status": "success",
            "transcripts_processed": len(transcripts),
            "chunks_created": len(all_chunks),
        }

    def refresh(self) -> Dict[str, Any]:
        embedding_service.delete_collection()
        return self.ingest_all()


ingestion_service = TranscriptIngestionService()