"""
Tests for SynkAI Phase 1 accounts: Google sign-in (mocked), emailed one-time login
codes (mocked SMTP), session issuance/expiry/logout, and onboarding/workspace creation
and join-by-domain.

These tests exercise real authentication, so each one starts by removing the
`get_current_user` override that tests/conftest.py applies by default for every other
(pre-existing) test in the suite.
"""

import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.db import get_db
from backend.dependencies import get_current_user
from backend.main import app
from backend.services import auth_service
from backend.services.email_service import EmailSendResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def real_auth():
    """Every test in this file exercises real authentication, not the test override."""
    app.dependency_overrides.pop(get_current_user, None)
    yield


# ----------------------------------------------------------------------------
# Email login codes
# ----------------------------------------------------------------------------

def test_email_code_request_and_verify_logs_in():
    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        response = client.post("/auth/email/request-code", json={"email": "ada@example.com"})
    assert response.status_code == 200

    with get_db() as conn:
        row = conn.execute(
            "SELECT code_hash FROM email_login_codes WHERE email = ?", ("ada@example.com",)
        ).fetchone()
    assert row is not None

    # Recover the real code the same way the service would check it, by trying the
    # verify endpoint with a wrong code first (must fail), then the service's own code.
    wrong = client.post("/auth/email/verify-code", json={"email": "ada@example.com", "code": "000000"})
    assert wrong.status_code == 401

    # Exercise the full service function directly to get a real code, then verify via HTTP.
    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        captured = {}

        def fake_send(to, subject, text_body, **kwargs):
            captured["code"] = text_body.split("code is ")[1].split(".")[0]
            return EmailSendResult(success=True)

        MockEmailService.return_value.send.side_effect = fake_send
        client.post("/auth/email/request-code", json={"email": "grace@example.com"})

    verified = client.post(
        "/auth/email/verify-code", json={"email": "grace@example.com", "code": captured["code"]}
    )
    assert verified.status_code == 200
    body = verified.json()
    assert "session_token" in body
    assert body["user"]["email"] == "grace@example.com"
    assert body["user"]["onboarded"] is False


def test_email_code_cannot_be_reused():
    captured = {}

    def fake_send(to, subject, text_body, **kwargs):
        captured["code"] = text_body.split("code is ")[1].split(".")[0]
        return EmailSendResult(success=True)

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.side_effect = fake_send
        client.post("/auth/email/request-code", json={"email": "once@example.com"})

    first = client.post("/auth/email/verify-code", json={"email": "once@example.com", "code": captured["code"]})
    assert first.status_code == 200

    second = client.post("/auth/email/verify-code", json={"email": "once@example.com", "code": captured["code"]})
    assert second.status_code == 401


def test_email_code_request_is_rate_limited():
    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        for _ in range(5):
            ok = client.post("/auth/email/request-code", json={"email": "busy@example.com"})
            assert ok.status_code == 200

        too_many = client.post("/auth/email/request-code", json={"email": "busy@example.com"})

    assert too_many.status_code == 429


def test_email_code_request_surfaces_smtp_failure_not_a_fake_success():
    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(
            success=False, error="Connection refused"
        )
        response = client.post("/auth/email/request-code", json={"email": "offline@example.com"})

    assert response.status_code == 502


# ----------------------------------------------------------------------------
# Google sign-in (OAuth exchange mocked — never calls the real Google API)
# ----------------------------------------------------------------------------

def test_google_login_returns_authorization_url():
    with patch("backend.config.settings.GOOGLE_CLIENT_ID", "test-client-id"):
        response = client.get("/auth/google/login")
    assert response.status_code == 200
    body = response.json()
    assert "accounts.google.com" in body["authorization_url"]
    assert body["state"]


def test_google_callback_creates_user_and_session():
    with patch("backend.config.settings.GOOGLE_CLIENT_ID", "test-client-id"):
        login_response = client.get("/auth/google/login")
    state = login_response.json()["state"]

    with (
        patch("backend.routes.auth.google_oauth_service.exchange_code_for_tokens") as mock_exchange,
        patch("backend.routes.auth.google_oauth_service.fetch_userinfo") as mock_userinfo,
    ):
        mock_exchange.return_value = {"access_token": "fake-access-token"}
        mock_userinfo.return_value = {
            "sub": "google-subject-123",
            "email": "founder@acme.com",
            "name": "Ada Founder",
        }
        response = client.post("/auth/google/callback", json={"code": "fake-code", "state": state})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "founder@acme.com"
    assert body["user"]["google_connected"] is True
    assert body["user"]["onboarded"] is False


def test_google_callback_rejects_reused_state():
    with patch("backend.config.settings.GOOGLE_CLIENT_ID", "test-client-id"):
        login_response = client.get("/auth/google/login")
    state = login_response.json()["state"]

    with (
        patch("backend.routes.auth.google_oauth_service.exchange_code_for_tokens") as mock_exchange,
        patch("backend.routes.auth.google_oauth_service.fetch_userinfo") as mock_userinfo,
    ):
        mock_exchange.return_value = {"access_token": "fake-access-token"}
        mock_userinfo.return_value = {"sub": "s1", "email": "a@b.com", "name": "A"}
        first = client.post("/auth/google/callback", json={"code": "fake-code", "state": state})
        assert first.status_code == 200

        second = client.post("/auth/google/callback", json={"code": "fake-code", "state": state})

    assert second.status_code == 400


def test_google_callback_rejects_unknown_state():
    response = client.post("/auth/google/callback", json={"code": "fake-code", "state": "never-issued"})
    assert response.status_code == 400


# ----------------------------------------------------------------------------
# Sessions: expiry, logout, logout-all
# ----------------------------------------------------------------------------

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _login_with_email_code(email: str) -> str:
    captured = {}

    def fake_send(to, subject, text_body, **kwargs):
        captured["code"] = text_body.split("code is ")[1].split(".")[0]
        return EmailSendResult(success=True)

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.side_effect = fake_send
        client.post("/auth/email/request-code", json={"email": email})

    verified = client.post("/auth/email/verify-code", json={"email": email, "code": captured["code"]})
    return verified.json()["session_token"]


def test_me_requires_a_valid_session():
    assert client.get("/auth/me").status_code == 401

    token = _login_with_email_code("session@example.com")
    ok = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == "session@example.com"


def test_expired_session_is_rejected():
    token = _login_with_email_code("expiring@example.com")

    with get_db() as conn:
        past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
        conn.execute(
            "UPDATE sessions SET expires_at = ? WHERE token_hash = ?",
            (past, auth_service._hash(token)),
        )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_logout_revokes_only_that_session():
    token_a = _login_with_email_code("multi-device@example.com")
    token_b = auth_service.create_session(
        auth_service.get_or_create_user_by_email("multi-device@example.com")
    )

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    assert logout.status_code == 200

    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token_b}"}).status_code == 200


def test_logout_all_revokes_every_session():
    token_a = _login_with_email_code("everywhere@example.com")
    token_b = auth_service.create_session(
        auth_service.get_or_create_user_by_email("everywhere@example.com")
    )

    response = client.post("/auth/logout-all", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200

    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token_b}"}).status_code == 401


# ----------------------------------------------------------------------------
# Onboarding & workspace creation / join-by-domain / admin approval
# ----------------------------------------------------------------------------

def test_onboarding_creates_workspace_and_makes_first_user_admin():
    token = _login_with_email_code("founder@newco.com")

    response = client.post(
        "/auth/onboarding",
        json={"full_name": "Founder Person", "company_name": "NewCo", "role_title": "CEO"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["onboarded"] is True
    assert body["membership_role"] == "admin"
    assert body["membership_status"] == "active"
    assert body["workspace"]["company_name"] == "NewCo"
    assert body["workspace"]["domain"] == "newco.com"


def test_second_user_same_domain_requests_to_join_and_needs_approval():
    founder_token = _login_with_email_code("founder@shared-domain.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Founder", "company_name": "Shared Domain Inc", "role_title": "CEO"},
        headers={"Authorization": f"Bearer {founder_token}"},
    )

    colleague_token = _login_with_email_code("colleague@shared-domain.com")
    response = client.post(
        "/auth/onboarding",
        # Deliberately types a different company name — domain is what must govern
        # who can join, never the text the user typed.
        json={"full_name": "Colleague", "company_name": "Totally Different Name Inc", "role_title": "Manager"},
        headers={"Authorization": f"Bearer {colleague_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["membership_status"] == "pending"
    assert body["membership_role"] == "member"
    # The workspace they joined is the EXISTING one (by domain), not a new one named
    # after whatever they typed.
    assert body["workspace"]["company_name"] == "Shared Domain Inc"

    # A pending member cannot use workspace-scoped resources yet.
    blocked = client.get("/meetings", headers={"Authorization": f"Bearer {colleague_token}"})
    assert blocked.status_code == 403
    assert "pending" in blocked.json()["detail"].lower()

    members = client.get("/workspace/members", headers={"Authorization": f"Bearer {founder_token}"})
    assert members.status_code == 200
    pending_emails = [m["email"] for m in members.json()["pending"]]
    assert "colleague@shared-domain.com" in pending_emails

    # Non-admin cannot see the pending queue.
    colleague_view = client.get("/workspace/members", headers={"Authorization": f"Bearer {colleague_token}"})
    assert colleague_view.json()["pending"] == []


def test_admin_can_approve_a_pending_join_request():
    founder_token = _login_with_email_code("founder@approve-me.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Founder", "company_name": "Approve Me Inc", "role_title": "CEO"},
        headers={"Authorization": f"Bearer {founder_token}"},
    )

    colleague_token = _login_with_email_code("colleague@approve-me.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Colleague", "company_name": "Approve Me Inc", "role_title": "Manager"},
        headers={"Authorization": f"Bearer {colleague_token}"},
    )

    colleague_id = client.get("/auth/me", headers={"Authorization": f"Bearer {colleague_token}"}).json()["id"]

    # A non-admin cannot approve anyone.
    denied = client.post(
        f"/workspace/requests/{colleague_id}/approve",
        headers={"Authorization": f"Bearer {colleague_token}"},
    )
    assert denied.status_code == 403

    approved = client.post(
        f"/workspace/requests/{colleague_id}/approve",
        headers={"Authorization": f"Bearer {founder_token}"},
    )
    assert approved.status_code == 200

    refreshed = client.get("/auth/me", headers={"Authorization": f"Bearer {colleague_token}"})
    assert refreshed.json()["membership_status"] == "active"


def test_profile_update_changes_name_and_title():
    token = _login_with_email_code("editme@example.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Old Name", "company_name": "EditCo", "role_title": "Analyst"},
        headers=_auth(token),
    )

    response = client.put(
        "/auth/profile",
        json={"full_name": "New Name", "role_title": "Senior Analyst"},
        headers=_auth(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "New Name"
    assert body["role_title"] == "Senior Analyst"


def test_only_admin_can_rename_workspace():
    founder_token = _login_with_email_code("founder@renameco.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Founder", "company_name": "RenameCo", "role_title": "CEO"},
        headers=_auth(founder_token),
    )

    member_token = _login_with_email_code("member@renameco.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Member", "company_name": "RenameCo", "role_title": "Analyst"},
        headers=_auth(member_token),
    )

    denied = client.put("/workspace/", json={"company_name": "New Name Inc"}, headers=_auth(member_token))
    assert denied.status_code == 403

    allowed = client.put("/workspace/", json={"company_name": "New Name Inc"}, headers=_auth(founder_token))
    assert allowed.status_code == 200
    assert allowed.json()["company_name"] == "New Name Inc"
    # The domain — what actually governs who can join — never changes.
    assert allowed.json()["domain"] == "renameco.com"


def test_is_public_domain_recognizes_common_freemail_providers():
    from backend.public_email_domains import is_public_domain

    assert is_public_domain("gmail.com")
    assert is_public_domain("GMail.com")  # case-insensitive
    assert is_public_domain("yahoo.co.uk")
    assert is_public_domain("outlook.com")
    assert is_public_domain("icloud.com")
    assert is_public_domain("rediffmail.com")
    assert not is_public_domain("acme.com")
    assert not is_public_domain("synkai.com")


def test_two_gmail_users_get_separate_workspaces_not_grouped_by_domain():
    token_a = _login_with_email_code("alice@gmail.com")
    onboard_a = client.post(
        "/auth/onboarding",
        json={"full_name": "Alice", "company_name": "Alice's Startup", "role_title": "Founder"},
        headers=_auth(token_a),
    )
    assert onboard_a.status_code == 200
    assert onboard_a.json()["membership_status"] == "active"
    assert onboard_a.json()["membership_role"] == "admin"
    workspace_a = onboard_a.json()["workspace"]["id"]

    token_b = _login_with_email_code("bob@gmail.com")
    onboard_b = client.post(
        "/auth/onboarding",
        # Even the exact same company name must not merge them — gmail.com tells us
        # nothing about who actually works together.
        json={"full_name": "Bob", "company_name": "Alice's Startup", "role_title": "Founder"},
        headers=_auth(token_b),
    )
    assert onboard_b.status_code == 200
    assert onboard_b.json()["membership_status"] == "active"
    assert onboard_b.json()["membership_role"] == "admin"
    workspace_b = onboard_b.json()["workspace"]["id"]

    assert workspace_a != workspace_b
    # Public-domain workspaces never carry the mail provider as their join-matching domain.
    assert onboard_a.json()["workspace"]["domain"] is None
    assert onboard_b.json()["workspace"]["domain"] is None


def test_public_domain_onboarding_requires_company_name():
    token = _login_with_email_code("nocompany@gmail.com")
    response = client.post(
        "/auth/onboarding",
        json={"full_name": "No Company", "role_title": "Founder"},
        headers=_auth(token),
    )
    assert response.status_code == 400


# ----------------------------------------------------------------------------
# Workspace invites
# ----------------------------------------------------------------------------

def test_admin_can_invite_someone_by_email_and_they_join_directly():
    admin_token = _login_with_email_code("admin@invite-co.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Admin", "company_name": "Invite Co", "role_title": "CEO"},
        headers=_auth(admin_token),
    )

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        invite = client.post(
            "/workspace/invites",
            json={"email": "newperson@gmail.com"},
            headers=_auth(admin_token),
        )

    assert invite.status_code == 200
    body = invite.json()
    assert body["invited_email"] == "newperson@gmail.com"
    assert body["email_sent"] is True
    code = body["code"]

    invitee_token = _login_with_email_code("newperson@gmail.com")
    onboard = client.post(
        "/auth/onboarding",
        json={"full_name": "New Person", "role_title": "Engineer", "invite_code": code},
        headers=_auth(invitee_token),
    )

    assert onboard.status_code == 200
    body = onboard.json()
    assert body["membership_status"] == "active"
    assert body["membership_role"] == "member"
    assert body["workspace"]["company_name"] == "Invite Co"


def test_invite_cannot_be_used_by_a_different_email():
    admin_token = _login_with_email_code("admin@strict-co.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Admin", "company_name": "Strict Co", "role_title": "CEO"},
        headers=_auth(admin_token),
    )

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        invite = client.post(
            "/workspace/invites", json={"email": "intended@gmail.com"}, headers=_auth(admin_token)
        )
    code = invite.json()["code"]

    wrong_person_token = _login_with_email_code("imposter@gmail.com")
    response = client.post(
        "/auth/onboarding",
        json={"full_name": "Imposter", "role_title": "Engineer", "invite_code": code},
        headers=_auth(wrong_person_token),
    )
    assert response.status_code == 400


def test_invite_cannot_be_reused():
    admin_token = _login_with_email_code("admin@once-co.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Admin", "company_name": "Once Co", "role_title": "CEO"},
        headers=_auth(admin_token),
    )

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        invite = client.post(
            "/workspace/invites", json={"email": "person@gmail.com"}, headers=_auth(admin_token)
        )
    code = invite.json()["code"]

    first_token = _login_with_email_code("person@gmail.com")
    first = client.post(
        "/auth/onboarding",
        json={"full_name": "Person", "role_title": "Engineer", "invite_code": code},
        headers=_auth(first_token),
    )
    assert first.status_code == 200

    # Same invite, a fresh (still-onboarding) account trying the same code again.
    second_token = _login_with_email_code("person2@gmail.com")
    second = client.post(
        "/auth/onboarding",
        json={"full_name": "Person Two", "role_title": "Engineer", "invite_code": code},
        headers=_auth(second_token),
    )
    assert second.status_code == 400


def test_expired_invite_is_rejected():
    admin_token = _login_with_email_code("admin@expiry-co.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Admin", "company_name": "Expiry Co", "role_title": "CEO"},
        headers=_auth(admin_token),
    )

    with patch("backend.services.auth_service.EmailService") as MockEmailService:
        MockEmailService.return_value.send.return_value = EmailSendResult(success=True)
        invite = client.post(
            "/workspace/invites", json={"email": "late@gmail.com"}, headers=_auth(admin_token)
        )
    code = invite.json()["code"]

    with get_db() as conn:
        past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
        conn.execute("UPDATE workspace_invites SET expires_at = ? WHERE code = ?", (past, code))

    invitee_token = _login_with_email_code("late@gmail.com")
    response = client.post(
        "/auth/onboarding",
        json={"full_name": "Late", "role_title": "Engineer", "invite_code": code},
        headers=_auth(invitee_token),
    )
    assert response.status_code == 400


def test_non_admin_cannot_create_invite():
    admin_token = _login_with_email_code("admin@gatekept-co.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Admin", "company_name": "Gatekept Co", "role_title": "CEO"},
        headers=_auth(admin_token),
    )
    member_token = _login_with_email_code("member@gatekept-co.com")
    client.post(
        "/auth/onboarding",
        json={"full_name": "Member", "company_name": "Gatekept Co", "role_title": "Analyst"},
        headers=_auth(member_token),
    )

    response = client.post(
        "/workspace/invites", json={"email": "someone@gmail.com"}, headers=_auth(member_token)
    )
    assert response.status_code == 403


def test_onboarding_rejects_missing_fields():
    token = _login_with_email_code("incomplete@example.com")
    response = client.post(
        "/auth/onboarding",
        json={"full_name": "", "company_name": "", "role_title": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
