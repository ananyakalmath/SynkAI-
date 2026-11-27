"""
Tests for Phase 3: Google Calendar connect/disconnect (incremental OAuth, mocked),
encrypted token storage, access-token refresh, and the create/update/cancel meeting
sync that creates a Calendar event with a Meet link — with the Calendar API mocked —
falling back to SMTP + .ics whenever the organiser isn't connected or the API call
fails.
"""

import datetime
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from backend.db import get_db
from backend.dependencies import get_current_user
from backend.main import app
from backend.services import auth_service, google_calendar_service, token_crypto
from backend.services.email_service import EmailSendResult
from tests.conftest import TEST_USER_ID, TEST_WORKSPACE_ID, _seed_default_test_identity

client = TestClient(app)

TEST_FERNET_KEY = Fernet.generate_key().decode()


class _FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text or str(json_data)

    def json(self):
        return self._json_data


def _event_json(event_id="fake-event-id", meet_link="https://meet.google.com/abc-defg-hij"):
    return {
        "id": event_id,
        "conferenceData": {"entryPoints": [{"entryPointType": "video", "uri": meet_link}]},
    }


def _connect(access_token_expires_in=3600):
    """Seeds a working Google Calendar connection for the default test user."""
    _seed_default_test_identity()
    with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY):
        google_calendar_service.save_connection(
            user_id=TEST_USER_ID,
            refresh_token="refresh-token-value",
            access_token="cached-access-token",
            expires_in=access_token_expires_in,
            scope="openid email profile https://www.googleapis.com/auth/calendar.events",
        )


def _meeting_payload(**overrides):
    payload = {
        "title": "Design review",
        "objective": "Approve the new layout",
        "meeting_type": "Review",
        "date": "2026-05-10",
        "start_time": "14:00",
        "end_time": "14:30",
        "timezone": "Asia/Kolkata",
        "participants": [{"name": "Dana", "email": "dana@example.com"}],
    }
    payload.update(overrides)
    return payload


# ----------------------------------------------------------------------------
# Connect / disconnect / status
# ----------------------------------------------------------------------------

def test_connect_returns_calendar_scoped_authorization_url():
    with patch("backend.config.settings.GOOGLE_CLIENT_ID", "test-client-id"):
        response = client.get("/auth/google/calendar/connect")

    assert response.status_code == 200
    body = response.json()
    assert "calendar.events" in body["authorization_url"]
    assert "access_type=offline" in body["authorization_url"]
    assert "prompt=consent" in body["authorization_url"]
    assert body["state"].startswith("cal_")


def test_connect_callback_stores_encrypted_refresh_token_and_reports_connected():
    _seed_default_test_identity()
    state = auth_service.create_calendar_connect_state(TEST_USER_ID)

    with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY), patch(
        "backend.services.google_oauth_service.exchange_code_for_tokens"
    ) as mock_exchange:
        mock_exchange.return_value = {
            "access_token": "AT",
            "refresh_token": "RT",
            "expires_in": 3600,
            "scope": "openid email profile https://www.googleapis.com/auth/calendar.events",
        }
        response = client.post("/auth/google/calendar/connect/callback", json={"code": "abc", "state": state})

    assert response.status_code == 200
    assert response.json() == {"connected": True}

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM google_calendar_connections WHERE user_id = ?", (TEST_USER_ID,)
        ).fetchone()
    assert row is not None
    assert row["encrypted_refresh_token"] != "RT"  # never stored in plaintext

    with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY):
        assert token_crypto.decrypt(row["encrypted_refresh_token"]) == "RT"

    status_response = client.get("/auth/google/calendar/status")
    assert status_response.json() == {"connected": True}


def test_connect_callback_rejects_missing_refresh_token():
    _seed_default_test_identity()
    state = auth_service.create_calendar_connect_state(TEST_USER_ID)

    with patch("backend.services.google_oauth_service.exchange_code_for_tokens") as mock_exchange:
        mock_exchange.return_value = {"access_token": "AT", "expires_in": 3600}  # no refresh_token
        response = client.post("/auth/google/calendar/connect/callback", json={"code": "abc", "state": state})

    assert response.status_code == 502
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM google_calendar_connections WHERE user_id = ?", (TEST_USER_ID,)
        ).fetchone()
    assert row is None


def test_connect_callback_rejects_a_login_purpose_state():
    """A plain sign-in state must never be redeemable as a calendar connection."""
    login_state = auth_service.create_oauth_state()
    response = client.post(
        "/auth/google/calendar/connect/callback", json={"code": "abc", "state": login_state}
    )
    assert response.status_code == 400


def test_connect_callback_rejects_unknown_state():
    response = client.post(
        "/auth/google/calendar/connect/callback", json={"code": "abc", "state": "cal_does-not-exist"}
    )
    assert response.status_code == 400


def test_disconnect_removes_the_connection():
    _connect()
    assert client.get("/auth/google/calendar/status").json() == {"connected": True}

    response = client.post("/auth/google/calendar/disconnect")
    assert response.status_code == 200
    assert response.json() == {"connected": False}
    assert client.get("/auth/google/calendar/status").json() == {"connected": False}


# ----------------------------------------------------------------------------
# Access token refresh
# ----------------------------------------------------------------------------

def test_expired_access_token_is_refreshed_before_use():
    _connect(access_token_expires_in=-10)  # already expired

    with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY), patch(
        "backend.services.google_oauth_service.refresh_access_token"
    ) as mock_refresh, patch("backend.services.google_calendar_service.requests.post") as mock_post:
        mock_refresh.return_value = {"access_token": "fresh-access-token", "expires_in": 3600}
        mock_post.return_value = _FakeResponse(200, _event_json())

        google_calendar_service.create_event(
            TEST_USER_ID,
            {"title": "x", "date": "2026-05-10", "start_time": "09:00", "end_time": "09:30", "timezone": "UTC"},
            [],
            "desc",
        )

    mock_refresh.assert_called_once_with("refresh-token-value")
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer fresh-access-token"


# ----------------------------------------------------------------------------
# Meeting create/update/cancel sync
# ----------------------------------------------------------------------------

def _mock_email_service():
    patcher = patch("backend.services.meeting_schedule_service.EmailService")
    mock_cls = patcher.start()
    mock_cls.return_value.send.return_value = EmailSendResult(success=True)
    return patcher, mock_cls


def test_create_meeting_syncs_to_google_and_skips_smtp_when_connected():
    _connect()
    email_patcher, mock_email_cls = _mock_email_service()
    try:
        with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY), patch(
            "backend.services.google_calendar_service.requests.post"
        ) as mock_post:
            mock_post.return_value = _FakeResponse(200, _event_json())
            response = client.post("/scheduled-meetings", json=_meeting_payload())
    finally:
        email_patcher.stop()

    assert response.status_code == 201
    body = response.json()
    assert body["meeting"]["google_event_id"] == "fake-event-id"
    assert body["meeting"]["google_meet_link"] == "https://meet.google.com/abc-defg-hij"
    assert body["meeting"]["calendar_sync_error"] is None
    assert body["invite_results"] == []  # Google already notified attendees
    mock_email_cls.return_value.send.assert_not_called()

    # The create call requested a Meet link and notified attendees itself.
    _, kwargs = mock_post.call_args
    assert kwargs["params"]["sendUpdates"] == "all"
    assert "conferenceData" in kwargs["json"]


def test_create_meeting_falls_back_to_smtp_when_google_api_call_fails():
    _connect()
    email_patcher, mock_email_cls = _mock_email_service()
    try:
        with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY), patch(
            "backend.services.google_calendar_service.requests.post"
        ) as mock_post:
            mock_post.return_value = _FakeResponse(500, text="Internal error")
            response = client.post("/scheduled-meetings", json=_meeting_payload())
    finally:
        email_patcher.stop()

    assert response.status_code == 201
    body = response.json()
    assert body["meeting"]["google_event_id"] is None
    assert body["meeting"]["google_meet_link"] is None
    assert body["meeting"]["calendar_sync_error"] is not None
    assert len(body["invite_results"]) == 1  # fell back to SMTP + .ics
    mock_email_cls.return_value.send.assert_called_once()


def test_create_meeting_uses_smtp_when_organiser_not_connected():
    """No Google connection at all: unchanged Phase 2 behaviour, no Calendar API call."""
    email_patcher, mock_email_cls = _mock_email_service()
    try:
        with patch("backend.services.google_calendar_service.requests.post") as mock_post:
            response = client.post("/scheduled-meetings", json=_meeting_payload())
    finally:
        email_patcher.stop()

    assert response.status_code == 201
    mock_post.assert_not_called()
    body = response.json()
    assert body["meeting"]["google_event_id"] is None
    assert len(body["invite_results"]) == 1


def test_update_meeting_patches_the_existing_google_event():
    _connect()
    email_patcher, mock_email_cls = _mock_email_service()
    try:
        with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY):
            with patch("backend.services.google_calendar_service.requests.post") as mock_post:
                mock_post.return_value = _FakeResponse(200, _event_json())
                created = client.post("/scheduled-meetings", json=_meeting_payload()).json()["meeting"]

            with patch("backend.services.google_calendar_service.requests.patch") as mock_patch:
                mock_patch.return_value = _FakeResponse(200, _event_json())
                updated = client.put(
                    f"/scheduled-meetings/{created['id']}",
                    json=_meeting_payload(title="Design review (moved)"),
                )
    finally:
        email_patcher.stop()

    assert updated.status_code == 200
    body = updated.json()
    assert body["meeting"]["google_event_id"] == "fake-event-id"
    assert body["invite_results"] == []
    mock_email_cls.return_value.send.assert_not_called()

    call_args, call_kwargs = mock_patch.call_args
    assert call_args[0].endswith("/fake-event-id")
    assert "conferenceData" not in call_kwargs["json"]  # preserves the existing Meet link


def test_cancel_meeting_deletes_the_google_event_and_skips_smtp():
    _connect()
    email_patcher, mock_email_cls = _mock_email_service()
    try:
        with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY):
            with patch("backend.services.google_calendar_service.requests.post") as mock_post:
                mock_post.return_value = _FakeResponse(200, _event_json())
                created = client.post("/scheduled-meetings", json=_meeting_payload()).json()["meeting"]

            mock_email_cls.return_value.send.reset_mock()

            with patch("backend.services.google_calendar_service.requests.delete") as mock_delete:
                mock_delete.return_value = _FakeResponse(204)
                cancelled = client.post(f"/scheduled-meetings/{created['id']}/cancel")
    finally:
        email_patcher.stop()

    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["meeting"]["status"] == "cancelled"
    assert body["invite_results"] == []
    mock_email_cls.return_value.send.assert_not_called()

    call_args, call_kwargs = mock_delete.call_args
    assert call_args[0].endswith("/fake-event-id")
    assert call_kwargs["params"]["sendUpdates"] == "all"


def test_cancel_meeting_falls_back_to_smtp_when_google_delete_fails():
    _connect()
    email_patcher, mock_email_cls = _mock_email_service()
    try:
        with patch("backend.config.settings.TOKEN_ENCRYPTION_KEY", TEST_FERNET_KEY):
            with patch("backend.services.google_calendar_service.requests.post") as mock_post:
                mock_post.return_value = _FakeResponse(200, _event_json())
                created = client.post("/scheduled-meetings", json=_meeting_payload()).json()["meeting"]

            mock_email_cls.return_value.send.reset_mock()

            with patch("backend.services.google_calendar_service.requests.delete") as mock_delete:
                mock_delete.return_value = _FakeResponse(500, text="boom")
                cancelled = client.post(f"/scheduled-meetings/{created['id']}/cancel")
    finally:
        email_patcher.stop()

    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["meeting"]["calendar_sync_error"] is not None
    assert len(body["invite_results"]) == 1  # SMTP cancellation fallback
    mock_email_cls.return_value.send.assert_called_once()


# ----------------------------------------------------------------------------
# Workspace/account isolation: one user's Google connection must never be usable
# for another user's meetings.
# ----------------------------------------------------------------------------

def test_connection_is_scoped_to_the_connecting_user_only():
    _connect()
    assert google_calendar_service.is_connected(TEST_USER_ID) is True
    assert google_calendar_service.is_connected("some-other-user-id") is False
