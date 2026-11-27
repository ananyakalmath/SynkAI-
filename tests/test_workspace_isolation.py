"""
Proves the Phase 1 requirement that users must never see data from another workspace:
uploads, indexed RAG documents, and meeting history created in one workspace are
invisible from another — even when the second workspace knows the exact document_id
or filename to ask for.

Two real, independently onboarded workspaces are used (not the default test override),
each with its own admin user, so these tests exercise the real get_current_user →
workspace_id path the production routes depend on.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.dependencies import get_current_user
from backend.main import app
from backend.services.email_service import EmailSendResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def real_auth():
    """These tests need two real, distinct workspaces, not the shared test override."""
    app.dependency_overrides.pop(get_current_user, None)
    yield


def _onboard_new_workspace(email: str, company_name: str) -> str:
    """Logs in via an emailed code and completes onboarding, returning the session token."""
    captured = {}

    def fake_send(to, subject, text_body, **kwargs):
        captured["code"] = text_body.split("code is ")[1].split(".")[0]
        return EmailSendResult(success=True)

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.side_effect = fake_send
        client.post("/auth/email/request-code", json={"email": email})

    login = client.post("/auth/email/verify-code", json={"email": email, "code": captured["code"]})
    token = login.json()["session_token"]

    onboard = client.post(
        "/auth/onboarding",
        json={"full_name": "Founder", "company_name": company_name, "role_title": "CEO"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert onboard.status_code == 200
    assert onboard.json()["membership_status"] == "active"

    return token


@pytest.fixture
def two_workspaces():
    token_a = _onboard_new_workspace("owner@workspace-a.com", "Workspace A Inc")
    token_b = _onboard_new_workspace("owner@workspace-b.com", "Workspace B Inc")
    return token_a, token_b


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@patch("backend.routes.summary.summary_service.generate_summary")
def test_uploaded_file_is_not_summarizable_by_another_workspace(mock_generate_summary, two_workspaces):
    from backend.models.summary import SummaryResponse

    mock_generate_summary.return_value = SummaryResponse(
        executive_summary="x", key_discussion_points=[], meeting_outcome="x", model_used="qwen3"
    )
    token_a, token_b = two_workspaces

    upload = client.post(
        "/upload",
        files={"file": ("isolation-test.txt", b"Workspace A's confidential meeting notes.", "text/plain")},
        headers=_auth(token_a),
    )
    assert upload.status_code == 201
    filename = upload.json()["filename"]

    # The owning workspace finds and can summarize its own upload.
    own_attempt = client.post("/summarize", json={"filename": filename}, headers=_auth(token_a))
    assert own_attempt.status_code == 200

    # A different workspace, same filename, must not find it.
    other_attempt = client.post("/summarize", json={"filename": filename}, headers=_auth(token_b))
    assert other_attempt.status_code == 404


@patch("backend.services.vector_service.VectorService.generate_embedding", return_value=[0.1] * 768)
def test_indexed_document_is_not_queryable_by_another_workspace(mock_embed, two_workspaces):
    token_a, token_b = two_workspaces

    indexed = client.post(
        "/chat/upload",
        files={"file": ("secret-plan.txt", b"Workspace A is launching product X in Q3.", "text/plain")},
        headers=_auth(token_a),
    )
    assert indexed.status_code == 201
    document_id = indexed.json()["document_id"]

    # Owning workspace gets real retrieved context (non-empty sources).
    own_query = client.post(
        "/chat/query",
        json={"document_id": document_id, "question": "What is workspace A launching?"},
        headers=_auth(token_a),
    )
    assert own_query.status_code == 200
    assert len(own_query.json()["sources"]) > 0

    # The other workspace, given the exact same document_id, retrieves nothing.
    other_query = client.post(
        "/chat/query",
        json={"document_id": document_id, "question": "What is workspace A launching?"},
        headers=_auth(token_b),
    )
    assert other_query.status_code == 200
    assert other_query.json()["sources"] == []
    assert other_query.json()["answer"] == "I couldn't find that information in this meeting transcript."


@patch("backend.services.vector_service.VectorService.generate_embedding", return_value=[0.1] * 768)
def test_meeting_analysis_cannot_resolve_another_workspaces_document_id(mock_embed, two_workspaces):
    token_a, token_b = two_workspaces

    indexed = client.post(
        "/chat/upload",
        files={"file": ("quarterly.txt", b"Decision: ship the feature by Friday.", "text/plain")},
        headers=_auth(token_a),
    )
    document_id = indexed.json()["document_id"]

    leaked = client.post(
        "/meeting/analyze",
        json={"document_id": document_id},
        headers=_auth(token_b),
    )
    assert leaked.status_code == 404


@patch("backend.services.vector_service.VectorService.generate_embedding", return_value=[0.1] * 768)
def test_meetings_list_is_scoped_per_workspace(mock_embed, two_workspaces):
    token_a, token_b = two_workspaces

    client.post(
        "/chat/upload",
        files={"file": ("only-in-a.txt", b"Only workspace A should ever see this filename.", "text/plain")},
        headers=_auth(token_a),
    )

    meetings_a = client.get("/meetings", headers=_auth(token_a))
    meetings_b = client.get("/meetings", headers=_auth(token_b))

    assert meetings_a.status_code == 200
    assert meetings_b.status_code == 200

    filenames_a = [m["filename"] for m in meetings_a.json()["meetings"]]
    filenames_b = [m["filename"] for m in meetings_b.json()["meetings"]]

    assert "only-in-a.txt" in filenames_a
    assert "only-in-a.txt" not in filenames_b
