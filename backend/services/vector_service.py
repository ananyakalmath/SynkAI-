"""
Vector Service for SynkAI.
Manages ChromaDB vector store interactions and embedding generation via Ollama (nomic-embed-text).
"""

import os
import datetime
from typing import List, Dict, Any, Optional
import requests
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VectorService:
    """
    Service for generating vector embeddings and interacting with ChromaDB vector database.
    """

    def __init__(
        self,
        db_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embed_model: Optional[str] = None
    ):
        self.db_dir = db_dir or settings.CHROMA_DB_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embed_model = embed_model or settings.OLLAMA_EMBED_MODEL
        self.ollama_url = settings.OLLAMA_BASE_URL.rstrip("/")

        # Ensure directory exists
        os.makedirs(self.db_dir, exist_ok=True)

        # Initialize ChromaDB persistent client
        logger.info(f"Initializing ChromaDB client at '{self.db_dir}'...")
        self.client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates embedding vector for text using Ollama /api/embeddings.

        Args:
            text (str): Input text chunk.

        Returns:
            List[float]: High-dimensional embedding vector.
        """
        endpoint = f"{self.ollama_url}/api/embeddings"
        payload = {
            "model": self.embed_model,
            "prompt": text
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            if response.status_code != 200:
                # Try fallback endpoint /api/embed if /api/embeddings fails
                fallback_endpoint = f"{self.ollama_url}/api/embed"
                fallback_payload = {"model": self.embed_model, "input": text}
                response = requests.post(fallback_endpoint, json=fallback_payload, timeout=30)

            if response.status_code != 200:
                raise RuntimeError(f"Ollama embedding request failed HTTP {response.status_code}: {response.text}")

            data = response.json()
            embedding = data.get("embedding") or (data.get("embeddings", [[]])[0] if "embeddings" in data else None)

            if not embedding:
                raise ValueError("No embedding vector returned from Ollama response.")

            return embedding
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to connect to Ollama embedding service ({self.embed_model}) at {endpoint}: {exc}")
            raise ConnectionError(
                f"Ollama embedding service is unreachable. Please verify Ollama is running and model '{self.embed_model}' is pulled."
            ) from exc

    def store_chunks(self, document_id: str, filename: str, chunks: List[Dict[str, Any]]) -> int:
        """
        Generates embeddings and stores text chunks in ChromaDB vector collection.

        Args:
            document_id (str): Unique document identifier.
            filename (str): Name of the source transcript file.
            chunks (List[Dict[str, Any]]): List of chunk objects.

        Returns:
            int: Count of vectors successfully stored.
        """
        if not chunks:
            logger.warning(f"No chunks provided to store for document '{document_id}' (filename: '{filename}').")
            return 0

        logger.info(f"Generating embeddings and storing {len(chunks)} chunks for document '{document_id}'...")
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        ids: List[str] = []
        documents: List[str] = []
        embeddings: List[List[float]] = []
        metadatas: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            chunk_num = chunk.get("chunk_number", idx + 1)
            chunk_text = chunk.get("chunk_text", "")

            # Generate vector embedding via Ollama
            emb_vector = self.generate_embedding(chunk_text)

            chunk_id = f"{document_id}_chunk_{chunk_num}"
            ids.append(chunk_id)
            documents.append(chunk_text)
            embeddings.append(emb_vector)
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_number": chunk_num,
                "upload_timestamp": timestamp,
                "chunk_text": chunk_text
            })

            logger.debug(f"Embeddings generated for chunk {chunk_num}/{len(chunks)} of document '{document_id}'.")

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"Vectors stored successfully for document '{document_id}' ({len(ids)} vectors total).")
        return len(ids)

    def similarity_search(self, query_text: str, document_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against ChromaDB filtered by document_id.

        Args:
            query_text (str): User question / query string.
            document_id (str): Document ID to filter search.
            top_k (int): Number of top matches to retrieve.

        Returns:
            List[Dict[str, Any]]: List of matching chunk dicts with distance metrics and metadata.
        """
        logger.info(f"Generating embedding for similarity query: '{query_text[:50]}...'")
        query_embedding = self.generate_embedding(query_text)

        where_filter = {"document_id": document_id}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )

        matches: List[Dict[str, Any]] = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                matches.append({
                    "chunk_text": doc,
                    "document_id": meta.get("document_id", ""),
                    "filename": meta.get("filename", "unknown"),
                    "chunk_number": meta.get("chunk_number", 0),
                    "upload_timestamp": meta.get("upload_timestamp", ""),
                    "distance": float(dist)
                })

        logger.info(f"Retrieval complete: Found {len(matches)} matching vector chunks.")
        return matches

    def delete_document(self, document_id: str) -> None:
        """
        Deletes all chunks associated with a document_id from the collection.

        Args:
            document_id (str): Document ID to delete.
        """
        logger.info(f"Deleting all vectors for document_id '{document_id}'...")
        self.collection.delete(where={"document_id": document_id})
        logger.info(f"Successfully deleted document_id '{document_id}' from vector store.")

