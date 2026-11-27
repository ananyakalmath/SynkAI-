"""
Shared pytest fixtures for the SynkAI test suite.

Two things happen here for every test, automatically:

1. The accounts database (backend.db) is pointed at a fresh temp file and re-initialized,
   so tests never share or pollute each other's users/workspaces/sessions, and never
   touch the real data/synkai.db used by a developer running the app locally.

2. `get_current_user` is overridden to return a fixed, already-onboarded test identity
   in an active workspace. This is what lets the 39 pre-existing tests (upload, chat,
   analysis, meetings — none of which ever sent an auth header) keep passing unmodified
   now that those routes require a workspace-scoped caller: they all exercise the real
   route logic, including the real workspace-filtering in vector_service/retrieval_service,
   just under one consistent identity instead of a real bearer token.

Tests that need to exercise *real* authentication (session issuance/expiry/revocation,
onboarding, workspace isolation *between* two different workspaces) remove this override
for the duration of the test — see tests/test_auth.py and tests/test_workspace_isolation.py.
"""

import datetime

import pytest

from backend.config import settings
from backend.db import get_db, init_db
from backend.dependencies import get_current_user
from backend.main import app
from backend.services import auth_service
from backend.services.auth_service import AuthContext

TEST_USER_ID = "test-user-0001"
TEST_WORKSPACE_ID = "test-workspace-0001"
TEST_USER_EMAIL = "tester@synkai-tests.local"


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """
    Points backend.db at a fresh temp SQLite file, and workspace-scoped uploads at a
    fresh temp directory, for the duration of one test — so test runs never create
    users/workspaces/sessions or upload directories inside the real project tree.
    """
    db_path = tmp_path / "synkai-test.db"
    monkeypatch.setattr(settings, "DATABASE_PATH", str(db_path))
    monkeypatch.setattr(settings, "UPLOADS_DIR", str(tmp_path / "uploads"))
    init_db()
    auth_service.ensure_default_workspace()
    yield


def _seed_default_test_identity() -> None:
    """Inserts the fixed user/workspace/membership the dependency override returns."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO workspaces (id, company_name, domain, created_at) VALUES (?, ?, ?, ?)",
            (TEST_WORKSPACE_ID, "Test Co", "synkai-tests.local", now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, full_name, onboarded, created_at) VALUES (?, ?, ?, 1, ?)",
            (TEST_USER_ID, TEST_USER_EMAIL, "Test User", now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO memberships (user_id, workspace_id, role, status, title, created_at) "
            "VALUES (?, ?, 'admin', 'active', 'Tester', ?)",
            (TEST_USER_ID, TEST_WORKSPACE_ID, now),
        )


def _default_test_context() -> AuthContext:
    _seed_default_test_identity()
    return AuthContext(
        user_id=TEST_USER_ID,
        email=TEST_USER_EMAIL,
        full_name="Test User",
        onboarded=True,
        workspace_id=TEST_WORKSPACE_ID,
        role="admin",
        membership_status="active",
        title="Tester",
        google_connected=False,
    )


@pytest.fixture(autouse=True)
def default_auth_override(isolated_database):
    """
    Makes every protected route see a fixed, active, onboarded test user by default.
    Tests exercising real authentication call `app.dependency_overrides.pop(get_current_user, None)`
    themselves (restored automatically at the end of this fixture).
    """
    app.dependency_overrides[get_current_user] = _default_test_context
    yield
    app.dependency_overrides.pop(get_current_user, None)
