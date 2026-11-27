"""
Tests for scheduled meetings: create/update/cancel/list APIs, email invites (mocked
SMTP) with generated agenda and "from last meeting" content, reminder scheduling, and
workspace isolation.
"""

import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from backend.db import get_db
from backend.dependencies import get_current_user
from backend.main import app
from backend.services import analysis_store
from backend.services.email_service import EmailSendResult
from backend.services.meeting_schedule_service import send_due_reminders
from tests.conftest import TEST_WORKSPACE_ID, _seed_default_test_identity

client = TestClient(app)


def _meeting_payload(**overrides) -> dict:
    payload = {
        "title": "Sprint planning",
        "objective": "Lock the Q3 rollout date",
        "meeting_type": "Planning",
        "date": "2026-03-10",
        "start_time": "09:00",
        "end_time": "09:30",
        "timezone": "Asia/Kolkata",
        "location": "https://meet.example.com/abc",
        "participants": [
            {"name": "Bob Builder", "email": "bob@example.com"},
            {"name": "Cara Dev", "email": "cara@example.com"},
        ],
    }
    payload.update(overrides)
    return payload


def _mock_email_service(success=True, error=None):
    patcher = patch("backend.services.meeting_schedule_service.EmailService")
    mock_cls = patcher.start()
    mock_cls.return_value.send.return_value = EmailSendResult(success=success, error=error)
    return patcher, mock_cls


def test_create_meeting_sends_invites_to_every_participant():
    patcher, mock_cls = _mock_email_service()
    try:
        response = client.post("/scheduled-meetings", json=_meeting_payload())
    finally:
        patcher.stop()

    assert response.status_code == 201
    body = response.json()
    assert body["meeting"]["title"] == "Sprint planning"
    assert body["meeting"]["status"] == "scheduled"
    assert body["meeting"]["sequence"] == 0
    assert len(body["meeting"]["participants"]) == 2
    assert len(body["invite_results"]) == 2
    assert all(r["success"] for r in body["invite_results"])
    assert mock_cls.return_value.send.call_count == 2

    # Invite carries a calendar part, method REQUEST, for a brand-new meeting.
    _, kwargs = mock_cls.return_value.send.call_args
    assert kwargs["calendar_invite"][1] == "REQUEST"


def test_create_meeting_rejects_unknown_timezone():
    patcher, _ = _mock_email_service()
    try:
        response = client.post("/scheduled-meetings", json=_meeting_payload(timezone="Mars/Olympus_Mons"))
    finally:
        patcher.stop()

    assert response.status_code == 400


def test_update_meeting_increments_sequence_and_resends_invites():
    patcher, mock_cls = _mock_email_service()
    try:
        created = client.post("/scheduled-meetings", json=_meeting_payload()).json()["meeting"]
        mock_cls.return_value.send.reset_mock()

        updated = client.put(
            f"/scheduled-meetings/{created['id']}",
            json=_meeting_payload(title="Sprint planning (rescheduled)", start_time="10:00", end_time="10:30"),
        )
    finally:
        patcher.stop()

    assert updated.status_code == 200
    body = updated.json()
    assert body["meeting"]["title"] == "Sprint planning (rescheduled)"
    assert body["meeting"]["sequence"] == 1
    assert len(body["invite_results"]) == 2
    _, kwargs = mock_cls.return_value.send.call_args
    assert kwargs["calendar_invite"][1] == "REQUEST"


def test_cancel_meeting_sends_cancellation_and_sets_status():
    patcher, mock_cls = _mock_email_service()
    try:
        created = client.post("/scheduled-meetings", json=_meeting_payload()).json()["meeting"]
        mock_cls.return_value.send.reset_mock()

        cancelled = client.post(f"/scheduled-meetings/{created['id']}/cancel")
    finally:
        patcher.stop()

    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["meeting"]["status"] == "cancelled"
    assert body["meeting"]["sequence"] == 1
    _, kwargs = mock_cls.return_value.send.call_args
    assert kwargs["calendar_invite"][1] == "CANCEL"


def test_email_failure_is_reported_not_hidden():
    patcher, mock_cls = _mock_email_service(success=False, error="Connection refused")
    try:
        response = client.post("/scheduled-meetings", json=_meeting_payload())
    finally:
        patcher.stop()

    assert response.status_code == 201  # the meeting itself is still created
    body = response.json()
    assert all(not r["success"] for r in body["invite_results"])
    assert all(r["error"] == "Connection refused" for r in body["invite_results"])


def test_get_meeting_returns_404_for_unknown_id():
    response = client.get("/scheduled-meetings/does-not-exist")
    assert response.status_code == 404


def test_list_meetings_by_month_filters_correctly():
    patcher, _ = _mock_email_service()
    try:
        client.post("/scheduled-meetings", json=_meeting_payload(date="2026-03-10"))
        client.post("/scheduled-meetings", json=_meeting_payload(title="April meeting", date="2026-04-05"))
    finally:
        patcher.stop()

    march = client.get("/scheduled-meetings", params={"year": 2026, "month": 3})
    assert march.status_code == 200
    march_titles = [m["title"] for m in march.json()["meetings"]]
    assert "Sprint planning" in march_titles
    assert "April meeting" not in march_titles

    april = client.get("/scheduled-meetings", params={"year": 2026, "month": 4})
    april_titles = [m["title"] for m in april.json()["meetings"]]
    assert "April meeting" in april_titles


def test_invite_includes_generated_agenda_and_last_meeting_section():
    _seed_default_test_identity()
    analysis_store.save_analysis(
        TEST_WORKSPACE_ID,
        "doc-from-last-time",
        {
            "executive_summary": "x",
            "action_items": [
                {"task": "Chase legal on the contract", "owner": "Priya", "status": "pending"},
                {"task": "Already finished this one", "owner": "Sam", "status": "done"},
            ],
            "decisions": ["Locked the rollout date for the 18th."],
            "deadlines": [],
            "risks": [{"risk": "Vendor hasn't countersigned yet."}],
        },
    )

    patcher, mock_cls = _mock_email_service()
    try:
        client.post(
            "/scheduled-meetings",
            json=_meeting_payload(previous_document_id="doc-from-last-time"),
        )
    finally:
        patcher.stop()

    _, kwargs = mock_cls.return_value.send.call_args
    body = kwargs["text_body"]

    assert "Lock the Q3 rollout date" in body  # the objective-derived agenda
    assert "From last meeting" in body
    assert "Chase legal on the contract (owner: Priya)" in body
    assert "Already finished this one" not in body  # done items are not "pending"
    assert "Locked the rollout date for the 18th." in body
    assert "Vendor hasn't countersigned yet." in body


def test_invite_omits_last_meeting_section_when_nothing_is_pending():
    _seed_default_test_identity()
    analysis_store.save_analysis(
        TEST_WORKSPACE_ID,
        "doc-all-clear",
        {
            "executive_summary": "x",
            "action_items": [{"task": "Done thing", "owner": "Sam", "status": "done"}],
            "decisions": [],
            "deadlines": [],
            "risks": [],
        },
    )

    patcher, mock_cls = _mock_email_service()
    try:
        client.post("/scheduled-meetings", json=_meeting_payload(previous_document_id="doc-all-clear"))
    finally:
        patcher.stop()

    _, kwargs = mock_cls.return_value.send.call_args
    assert "From last meeting" not in kwargs["text_body"]


def test_due_reminder_is_sent_once_and_not_duplicated():
    patcher, mock_cls = _mock_email_service()
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        start_in_30_min = now + datetime.timedelta(minutes=30)
        local = start_in_30_min.astimezone(ZoneInfo("Asia/Kolkata"))

        created = client.post(
            "/scheduled-meetings",
            json=_meeting_payload(
                date=local.strftime("%Y-%m-%d"),
                start_time=local.strftime("%H:%M"),
                end_time=(local + datetime.timedelta(minutes=30)).strftime("%H:%M"),
            ),
        ).json()["meeting"]
        mock_cls.return_value.send.reset_mock()

        sent_first = send_due_reminders(now=now)
        sent_second = send_due_reminders(now=now)
    finally:
        patcher.stop()

    # 2 participants x one due window (1h) = 2 reminder emails, exactly once.
    assert sent_first == 2
    assert sent_second == 0

    with get_db() as conn:
        row = conn.execute(
            "SELECT reminder_1h_sent, reminder_24h_sent FROM scheduled_meetings WHERE id = ?",
            (created["id"],),
        ).fetchone()
    assert row["reminder_1h_sent"] == 1
    assert row["reminder_24h_sent"] == 0  # not yet within the 24h-only part of the window


# ----------------------------------------------------------------------------
# Workspace isolation — two real, independently onboarded workspaces, not the
# shared default test override.
# ----------------------------------------------------------------------------

def _onboard_new_workspace(email: str, company_name: str) -> str:
    from backend.services.email_service import EmailSendResult as _Result

    captured = {}

    def fake_send(to, subject, text_body, **kwargs):
        captured["code"] = text_body.split("code is ")[1].split(".")[0]
        return _Result(success=True)

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
    return token


def test_scheduled_meeting_is_invisible_to_another_workspace():
    app.dependency_overrides.pop(get_current_user, None)
    try:
        token_a = _onboard_new_workspace("owner@meetings-a.com", "Meetings A Inc")
        token_b = _onboard_new_workspace("owner@meetings-b.com", "Meetings B Inc")
        auth_a = {"Authorization": f"Bearer {token_a}"}
        auth_b = {"Authorization": f"Bearer {token_b}"}

        patcher, _ = _mock_email_service()
        try:
            created = client.post("/scheduled-meetings", json=_meeting_payload(), headers=auth_a).json()["meeting"]
        finally:
            patcher.stop()

        # Workspace B cannot fetch it directly...
        leaked = client.get(f"/scheduled-meetings/{created['id']}", headers=auth_b)
        assert leaked.status_code == 404

        # ...nor see it in its month listing.
        listing_b = client.get("/scheduled-meetings", params={"year": 2026, "month": 3}, headers=auth_b)
        assert created["id"] not in [m["id"] for m in listing_b.json()["meetings"]]

        # Workspace A still sees its own meeting.
        listing_a = client.get("/scheduled-meetings", params={"year": 2026, "month": 3}, headers=auth_a)
        assert created["id"] in [m["id"] for m in listing_a.json()["meetings"]]

        # Workspace B cannot cancel it either.
        cancel_attempt = client.post(f"/scheduled-meetings/{created['id']}/cancel", headers=auth_b)
        assert cancel_attempt.status_code == 404
    finally:
        from tests.conftest import _default_test_context

        app.dependency_overrides[get_current_user] = _default_test_context
