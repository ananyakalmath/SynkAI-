"""
Tests for the read-only meeting listing endpoint that backs the SynkAI dashboard.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_meetings_endpoint_groups_chunks_by_document():
    """
    Each indexed document should appear once, newest first, with its chunk count.
    """
    stored = {
        "metadatas": [
            {"document_id": "doc-a", "filename": "sprint.docx", "upload_timestamp": "2026-09-10T09:00:00+00:00"},
            {"document_id": "doc-a", "filename": "sprint.docx", "upload_timestamp": "2026-09-10T09:00:01+00:00"},
            {"document_id": "doc-b", "filename": "review.txt", "upload_timestamp": "2026-09-11T14:00:00+00:00"},
        ]
    }

    with patch("backend.routes.meetings.vector_service.collection") as collection:
        collection.get.return_value = stored
        response = client.get("/meetings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2

    # Newest first.
    assert [m["document_id"] for m in payload["meetings"]] == ["doc-b", "doc-a"]

    doc_a = payload["meetings"][1]
    assert doc_a["filename"] == "sprint.docx"
    assert doc_a["number_of_chunks"] == 2
    assert doc_a["indexed_at"] == "2026-09-10T09:00:00+00:00"


def test_meetings_endpoint_handles_empty_store():
    """
    An empty vector store is a valid state, not an error.
    """
    with patch("backend.routes.meetings.vector_service.collection") as collection:
        collection.get.return_value = {"metadatas": []}
        response = client.get("/meetings")

    assert response.status_code == 200
    assert response.json() == {"meetings": [], "total": 0}


def test_meetings_endpoint_reports_store_failure():
    """
    A failing vector store must surface as an explicit error, not an empty list.
    """
    with patch("backend.routes.meetings.vector_service.collection") as collection:
        collection.get.side_effect = RuntimeError("chroma unavailable")
        response = client.get("/meetings")

    assert response.status_code == 500
    assert "chroma unavailable" in response.json()["detail"]
