import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.ingest import COLLECTION_NAME
from app.schemas import RetrievedChunk


class Retriever:
    def __init__(self, persist_dir: str | None = None):
        self._client = chromadb.PersistentClient(path=persist_dir or settings.chroma_dir)
        self._collection = self._client.get_collection(COLLECTION_NAME)
        self._model = SentenceTransformer(settings.embedding_model)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        embedding = self._model.encode([query], normalize_embeddings=True).tolist()
        results = self._collection.query(query_embeddings=embedding, n_results=top_k)

        chunks = []
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        for text, metadata, distance in zip(documents, metadatas, distances):
            similarity = 1 - distance
            chunks.append(RetrievedChunk(
                doc_id=metadata.get("doc_id", ""),
                source_type=metadata.get("source_type", "doc"),
                title=metadata.get("title", ""),
                text=text,
                similarity=similarity,
            ))
        return chunks
