"""
Unit and integration tests for SynkAI Sprint 3 RAG pipeline.
Tests ChunkingService, VectorService, RetrievalService, and FastAPI chat endpoints.
Uses unittest.mock to mock Ollama interactions for environment independence.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.chunking_service import ChunkingService
from backend.services.vector_service import VectorService
from backend.services.retrieval_service import RetrievalService

client = TestClient(app)


def test_chunking_service():
    """
    Verifies that ChunkingService correctly splits text into structured overlapping chunks.
    """
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "This is sentence one. This is sentence two. This is sentence three. "
        "This is sentence four. This is sentence five. This is sentence six."
    )
    chunks = service.chunk_text(sample_text)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "chunk_number" in chunk
        assert "chunk_text" in chunk
        assert len(chunk["chunk_text"]) > 0


@patch("backend.services.vector_service.VectorService.generate_embedding")
def test_vector_service_store_and_search(mock_embed):
    """
    Tests that VectorService stores document chunks and retrieves them using similarity search.
    """
    # Mock embedding to return a dummy 3-dimensional vector
    mock_embed.return_value = [0.1, 0.2, 0.3]

    with tempfile.TemporaryDirectory() as temp_db_dir:
        service = VectorService(
            db_dir=temp_db_dir,
            collection_name="test_collection",
            embed_model="test-embed-model"
        )

        test_doc_id = "doc_test_123"
        test_filename = "test_meeting.txt"
        test_chunks = [
            {"chunk_number": 1, "chunk_text": "This is chunk number one of the roadmap meeting."},
            {"chunk_number": 2, "chunk_text": "Action items: Alice will write the embeddings engine."}
        ]

        stored_count = service.store_chunks(
            document_id=test_doc_id,
            filename=test_filename,
            chunks=test_chunks
        )
        assert stored_count == 2

        # Verify semantic search with mocked query embedding
        matches = service.similarity_search(
            query_text="roadmap meeting",
            document_id=test_doc_id,
            top_k=2
        )
        assert len(matches) == 2
        assert matches[0]["document_id"] == test_doc_id
        assert matches[0]["filename"] == test_filename
        assert "chunk_text" in matches[0]

        # Test delete helper
        service.delete_document(test_doc_id)
        post_delete_matches = service.similarity_search(
            query_text="roadmap meeting",
            document_id=test_doc_id,
            top_k=2
        )
        assert len(post_delete_matches) == 0


@patch("backend.services.vector_service.VectorService.generate_embedding")
@patch("backend.services.ollama_service.OllamaService.generate")
def test_retrieval_service_rag(mock_llm, mock_embed):
    """
    Tests that RetrievalService retrieves context and generates synthesised RAG answer.
    """
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_llm.return_value = "Alice owns the embeddings task."

    with tempfile.TemporaryDirectory() as temp_db_dir:
        vec_service = VectorService(
            db_dir=temp_db_dir,
            collection_name="test_collection"
        )
        ret_service = RetrievalService(vector_service=vec_service)

        doc_id = "doc_999"
        filename = "meeting_transcript.txt"
        chunks = [
            {"chunk_number": 1, "chunk_text": "Context: Alice owns the embeddings task for Sprint 3."}
        ]
        vec_service.store_chunks(document_id=doc_id, filename=filename, chunks=chunks)

        res = ret_service.answer_question(
            document_id=doc_id,
            question="Who owns the embeddings task?"
        )

        assert res["answer"] == "Alice owns the embeddings task."
        assert len(res["sources"]) == 1
        assert res["sources"][0]["filename"] == filename
        assert res["sources"][0]["chunk_number"] == 1


@patch("backend.services.vector_service.VectorService.generate_embedding")
@patch("backend.services.ollama_service.OllamaService.generate")
def test_retrieval_service_unavailable(mock_llm, mock_embed):
    """
    Verifies that RetrievalService returns exact unavailable statement when context is empty or LLM fails to find it.
    """
    mock_embed.return_value = [0.1, 0.2, 0.3]
    # Simulate LLM returning a negative response phrase
    mock_llm.return_value = "Based on the transcript, there is no mention of Bob."

    with tempfile.TemporaryDirectory() as temp_db_dir:
        vec_service = VectorService(
            db_dir=temp_db_dir,
            collection_name="test_collection"
        )
        ret_service = RetrievalService(vector_service=vec_service)

        doc_id = "doc_888"
        filename = "meeting_transcript.txt"
        chunks = [
            {"chunk_number": 1, "chunk_text": "Roadmap planning discussion."}
        ]
        vec_service.store_chunks(document_id=doc_id, filename=filename, chunks=chunks)

        res = ret_service.answer_question(
            document_id=doc_id,
            question="What is Bob's task?"
        )
        # Should be post-processed to the exact negative answer phrase
        assert res["answer"] == "I couldn't find that information in this meeting transcript."


@patch("backend.routes.chat.vector_service.generate_embedding")
@patch("backend.routes.chat.vector_service.collection")
def test_chat_upload_endpoint(mock_collection, mock_embed):
    """
    Tests POST /chat/upload FastAPI endpoint.
    """
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_collection.upsert.return_value = None

    # Write a dummy transcript file to verify parser
    file_content = b"This is a dummy transcript used to test chat upload endpoint chunking."
    files = {"file": ("test_transcript.txt", file_content, "text/plain")}

    response = client.post("/chat/upload", files=files)
    assert response.status_code == 201

    json_data = response.json()
    assert "document_id" in json_data
    assert json_data["filename"] == "test_transcript.txt"
    assert json_data["number_of_chunks"] > 0


@patch("backend.routes.chat.retrieval_service.answer_question")
def test_chat_query_endpoint(mock_answer):
    """
    Tests POST /chat/query FastAPI endpoint.
    """
    mock_answer.return_value = {
        "answer": "Sprint 3 deadline is next Tuesday.",
        "sources": [{"filename": "meeting.txt", "chunk_number": 1}],
        "model_used": "qwen3"
    }

    payload = {
        "document_id": "test-doc-id-111",
        "question": "When is the deadline?"
    }

    response = client.post("/chat/query", json=payload)
    assert response.status_code == 200

    json_data = response.json()
    assert json_data["answer"] == "Sprint 3 deadline is next Tuesday."
    assert len(json_data["sources"]) == 1
    assert json_data["sources"][0]["filename"] == "meeting.txt"
    assert json_data["sources"][0]["chunk_number"] == 1
