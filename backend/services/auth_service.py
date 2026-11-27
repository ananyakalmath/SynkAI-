"""
Auth Service for SynkAI.

Owns everything about "who is this, and what workspace are they in": user lookup/
creation (by Google subject or by email), workspace creation/join-by-domain, admin
approval of join requests, and session issuance/validation/revocation.

No passwords anywhere — accounts exist only via Google sign-in or an emailed one-time
code, per product decision. Session tokens are random and stored only as a SHA-256
hash, the same reasoning as the one-time email codes: if the database were ever read
by someone who shouldn't, they get hashes, not usable secrets.
"""

import datetime
import hashlib
import secrets
from dataclasses import dataclass
from typing import List, Optional, Tuple

from backend.config import settings
from backend.db import get_db
from backend.public_email_domains import is_public_domain
from backend.services.email_service import EmailService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_WORKSPACE_ID = "legacy"


class AuthError(Exception):
    """Raised for any authentication/authorization failure with a user-safe message."""


class RateLimitError(AuthError):
    """Raised when a caller is asking for email codes too often."""


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def extract_domain(email: str) -> str:
    """Returns the lowercase domain half of an email address."""
    return email.strip().lower().rsplit("@", 1)[-1]


@dataclass
class AuthContext:
    """Everything a request handler needs to know about the caller."""

    user_id: str
    email: str
    full_name: Optional[str]
    onboarded: bool
    workspace_id: Optional[str]
    role: Optional[str]           # 'admin' | 'member' | None (no workspace yet)
    membership_status: Optional[str]  # 'active' | 'pending' | None
    title: Optional[str] = None   # the role/title entered at onboarding, e.g. "CEO"
    google_connected: bool = False


# ----------------------------------------------------------------------------
# Users
# ----------------------------------------------------------------------------

def get_or_create_user_by_google(sub: str, email: str, full_name: Optional[str]) -> str:
    """Finds a user by Google subject or email, creating one if neither exists."""
    email = email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT id FROM users WHERE google_sub = ?", (sub,)).fetchone()
        if row:
            return row["id"]

        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            conn.execute("UPDATE users SET google_sub = ? WHERE id = ?", (sub, row["id"]))
            return row["id"]

        user_id = secrets.token_hex(16)
        conn.execute(
            "INSERT INTO users (id, email, full_name, google_sub, onboarded, created_at) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (user_id, email, full_name, sub, _iso(_now())),
        )
        return user_id


def get_or_create_user_by_email(email: str) -> str:
    """Finds a user by email, creating a (not-yet-onboarded) one if it doesn't exist."""
    email = email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return row["id"]

        user_id = secrets.token_hex(16)
        conn.execute(
            "INSERT INTO users (id, email, full_name, onboarded, created_at) VALUES (?, ?, NULL, 0, ?)",
            (user_id, email, _iso(_now())),
        )
        return user_id


# ----------------------------------------------------------------------------
# Sessions
# ----------------------------------------------------------------------------

def create_session(user_id: str, user_agent: Optional[str] = None) -> str:
    """Issues a new session token for `user_id` and returns the raw (unhashed) token."""
    raw_token = secrets.token_urlsafe(32)
    now = _now()
    expires = now + datetime.timedelta(days=settings.SESSION_TTL_DAYS)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at, revoked, user_agent) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (_hash(raw_token), user_id, _iso(now), _iso(expires), user_agent),
        )
    return raw_token


def resolve_session(raw_token: str) -> AuthContext:
    """
    Validates a session token and returns the caller's full context.

    Raises:
        AuthError: If the token is missing, unknown, revoked, or expired.
    """
    if not raw_token:
        raise AuthError("Authentication required.")

    token_hash = _hash(raw_token)

    with get_db() as conn:
        session_row = conn.execute(
            "SELECT * FROM sessions WHERE token_hash = ?", (token_hash,)
        ).fetchone()

        if session_row is None or session_row["revoked"]:
            raise AuthError("Invalid or expired session.")

        expires_at = datetime.datetime.fromisoformat(session_row["expires_at"])
        if expires_at < _now():
            raise AuthError("Invalid or expired session.")

        user_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (session_row["user_id"],)
        ).fetchone()
        if user_row is None:
            raise AuthError("Invalid or expired session.")

        membership = conn.execute(
            "SELECT * FROM memberships WHERE user_id = ?", (user_row["id"],)
        ).fetchone()

    return AuthContext(
        user_id=user_row["id"],
        email=user_row["email"],
        full_name=user_row["full_name"],
        onboarded=bool(user_row["onboarded"]),
        workspace_id=membership["workspace_id"] if membership else None,
        role=membership["role"] if membership else None,
        membership_status=membership["status"] if membership else None,
        title=membership["title"] if membership else None,
        google_connected=user_row["google_sub"] is not None,
    )


def get_context(user_id: str) -> AuthContext:
    """
    Builds an AuthContext straight from a known user_id, skipping session-token
    validation — for use right after an action we know the caller is authorized for
    (e.g. re-reading state immediately after onboarding) where re-presenting the raw
    session token would be awkward.
    """
    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_row is None:
            raise AuthError("User not found.")

        membership = conn.execute(
            "SELECT * FROM memberships WHERE user_id = ?", (user_id,)
        ).fetchone()

    return AuthContext(
        user_id=user_row["id"],
        email=user_row["email"],
        full_name=user_row["full_name"],
        onboarded=bool(user_row["onboarded"]),
        workspace_id=membership["workspace_id"] if membership else None,
        role=membership["role"] if membership else None,
        membership_status=membership["status"] if membership else None,
        title=membership["title"] if membership else None,
        google_connected=user_row["google_sub"] is not None,
    )


def revoke_session(raw_token: str) -> None:
    """Logs out a single session (idempotent — revoking twice is harmless)."""
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET revoked = 1 WHERE token_hash = ?", (_hash(raw_token),)
        )


def revoke_all_sessions(user_id: str) -> None:
    """Logs out every device for this user."""
    with get_db() as conn:
        conn.execute("UPDATE sessions SET revoked = 1 WHERE user_id = ?", (user_id,))


# ----------------------------------------------------------------------------
# OAuth CSRF state
# ----------------------------------------------------------------------------

def create_oauth_state(invite_code: Optional[str] = None) -> str:
    """
    Issues a short-lived, single-use nonce to guard the Google OAuth redirect. An
    invite code (if the user arrived via an invite link) rides along in this record,
    since a full redirect to Google and back is not a safe place to assume any
    client-held state (a query param, a form field) survives untouched.
    """
    state = secrets.token_urlsafe(24)
    now = _now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO oauth_states (state, created_at, expires_at, invite_code) VALUES (?, ?, ?, ?)",
            (state, _iso(now), _iso(now + datetime.timedelta(minutes=10)), invite_code),
        )
    return state


def create_calendar_connect_state(user_id: str) -> str:
    """
    Issues a short-lived, single-use nonce for the "Connect Google Calendar"
    incremental-authorization redirect. Prefixed so the frontend can tell this state
    apart from an ordinary sign-in state purely by looking at the value Google echoes
    back — no extra round trip needed to ask the backend which flow it belongs to.
    The target user_id rides along in this record for the same reason an invite code
    does: a full redirect out to Google and back cannot be relied on to preserve
    client-held state.
    """
    state = "cal_" + secrets.token_urlsafe(24)
    now = _now()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO oauth_states (state, created_at, expires_at, purpose, user_id) "
            "VALUES (?, ?, ?, 'calendar_connect', ?)",
            (state, _iso(now), _iso(now + datetime.timedelta(minutes=10)), user_id),
        )
    return state


def consume_oauth_state(state: str) -> Optional[dict]:
    """
    Validates and deletes a state token (single use). Returns
    `{"invite_code": ..., "purpose": ..., "user_id": ...}` on success, or None if the
    state is unknown, already used, or expired.
    """
    with get_db() as conn:
        row = conn.execute("SELECT * FROM oauth_states WHERE state = ?", (state,)).fetchone()
        if row is None:
            return None

        conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))

        expires_at = datetime.datetime.fromisoformat(row["expires_at"])
        if expires_at < _now():
            return None

        return {"invite_code": row["invite_code"], "purpose": row["purpose"], "user_id": row["user_id"]}


# ----------------------------------------------------------------------------
# Email login codes
# ----------------------------------------------------------------------------

def request_email_code(email: str, email_service: Optional[EmailService] = None) -> None:
    """
    Generates, stores, and emails a 10-minute one-time login code.

    Raises:
        RateLimitError: Too many codes requested for this email recently.
        AuthError: The email could not actually be sent — never pretend it was.
    """
    email = email.strip().lower()
    email_service = email_service or EmailService()
    now = _now()
    window_start = _iso(now - datetime.timedelta(hours=1))

    with get_db() as conn:
        recent = conn.execute(
            "SELECT COUNT(*) AS n FROM email_login_codes WHERE email = ? AND created_at > ?",
            (email, window_start),
        ).fetchone()["n"]

        if recent >= settings.EMAIL_CODE_RATE_LIMIT_PER_HOUR:
            raise RateLimitError(
                "Too many codes requested for this email. Please wait before trying again."
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        expires = now + datetime.timedelta(minutes=settings.EMAIL_CODE_TTL_MINUTES)

        conn.execute(
            "INSERT INTO email_login_codes (email, code_hash, created_at, expires_at, used, attempts) "
            "VALUES (?, ?, ?, ?, 0, 0)",
            (email, _hash(code), _iso(now), _iso(expires)),
        )

    sent = email_service.send(
        to=email,
        subject="Your SynkAI sign-in code",
        text_body=(
            f"Your SynkAI sign-in code is {code}.\n\n"
            f"It expires in {settings.EMAIL_CODE_TTL_MINUTES} minutes and can only be used once."
        ),
    )
    if not sent.success:
        logger.error(f"Failed to send login code to '{email}': {sent.error}")
        raise AuthError(f"Could not send the login code email: {sent.error}")


def verify_email_code(email: str, code: str) -> bool:
    """
    Validates a login code. Returns True if valid (and marks it used); False otherwise.

    Raises:
        AuthError: The code's attempt limit has been exhausted.
    """
    email = email.strip().lower()

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM email_login_codes WHERE email = ? AND used = 0 "
            "ORDER BY created_at DESC LIMIT 1",
            (email,),
        ).fetchone()

        if row is None:
            return False

        if row["attempts"] >= settings.EMAIL_CODE_MAX_ATTEMPTS:
            raise AuthError("Too many incorrect attempts. Request a new code.")

        expires_at = datetime.datetime.fromisoformat(row["expires_at"])
        if expires_at < _now():
            return False

        conn.execute(
            "UPDATE email_login_codes SET attempts = attempts + 1 WHERE id = ?", (row["id"],)
        )

        if not secrets.compare_digest(row["code_hash"], _hash(code.strip())):
            return False

        conn.execute("UPDATE email_login_codes SET used = 1 WHERE id = ?", (row["id"],))
        return True


# ----------------------------------------------------------------------------
# Onboarding & workspaces
# ----------------------------------------------------------------------------

def complete_onboarding(
    user_id: str,
    full_name: str,
    company_name: Optional[str],
    role_title: str,
    invite_code: Optional[str] = None,
) -> str:
    """
    Records the user's name/role and places them in a workspace, in one of three ways:

    1. `invite_code` given: joins exactly the workspace that invite names, as an active
       member — the only path onto a workspace whose domain is public (gmail.com, ...)
       or that otherwise isn't the user's own email domain.
    2. No invite, public email domain (gmail.com, outlook.com, ...): a public domain
       says nothing about which company someone works for, so two strangers sharing a
       mail provider must never land in the same workspace. They always get a brand
       new workspace, named after whatever `company_name` they typed, and become its
       admin immediately.
    3. No invite, company-owned domain: matched by the user's verified email domain —
       never by the company name they typed, so nobody can join another company's
       workspace just by guessing or typing its name.

    Returns:
        The resulting membership status: 'active' or 'pending' (awaiting approval from
        an existing admin — only possible via path 3).
    """
    full_name = full_name.strip()
    company_name = (company_name or "").strip()
    role_title = role_title.strip()

    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_row is None:
            raise AuthError("User not found.")

        now_dt = _now()
        now = _iso(now_dt)

        conn.execute(
            "UPDATE users SET full_name = ?, onboarded = 1 WHERE id = ?",
            (full_name, user_id),
        )

        existing = conn.execute(
            "SELECT * FROM memberships WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            return existing["status"]

        # Path 1: a specific invite names a specific workspace — domain rules never apply.
        if invite_code:
            invite = conn.execute(
                "SELECT * FROM workspace_invites WHERE code = ?", (invite_code,)
            ).fetchone()
            if invite is None:
                raise AuthError("This invite code is invalid.")
            if invite["used"]:
                raise AuthError("This invite has already been used.")
            if invite["invited_email"].lower() != user_row["email"].lower():
                raise AuthError("This invite was issued for a different email address.")
            if datetime.datetime.fromisoformat(invite["expires_at"]) < now_dt:
                raise AuthError("This invite has expired. Ask the workspace admin to send a new one.")

            conn.execute("UPDATE workspace_invites SET used = 1 WHERE code = ?", (invite_code,))
            conn.execute(
                "INSERT INTO memberships (user_id, workspace_id, role, status, title, created_at) "
                "VALUES (?, ?, 'member', 'active', ?, ?)",
                (user_id, invite["workspace_id"], role_title, now),
            )
            return "active"

        domain = extract_domain(user_row["email"])

        # Path 2: a public/freemail domain never auto-groups strangers into one workspace.
        if is_public_domain(domain):
            if not company_name:
                raise AuthError("Company name is required.")
            workspace_id = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO workspaces (id, company_name, domain, created_at) VALUES (?, ?, NULL, ?)",
                (workspace_id, company_name, now),
            )
            conn.execute(
                "INSERT INTO memberships (user_id, workspace_id, role, status, title, created_at) "
                "VALUES (?, ?, 'admin', 'active', ?, ?)",
                (user_id, workspace_id, role_title, now),
            )
            return "active"

        # Path 3: a company-owned domain — join-by-domain, admin approval required.
        workspace = conn.execute(
            "SELECT * FROM workspaces WHERE domain = ?", (domain,)
        ).fetchone()

        if workspace is None:
            if not company_name:
                raise AuthError("Company name is required.")
            workspace_id = secrets.token_hex(16)
            conn.execute(
                "INSERT INTO workspaces (id, company_name, domain, created_at) VALUES (?, ?, ?, ?)",
                (workspace_id, company_name, domain, now),
            )
            conn.execute(
                "INSERT INTO memberships (user_id, workspace_id, role, status, title, created_at) "
                "VALUES (?, ?, 'admin', 'active', ?, ?)",
                (user_id, workspace_id, role_title, now),
            )
            return "active"

        conn.execute(
            "INSERT INTO memberships (user_id, workspace_id, role, status, title, created_at) "
            "VALUES (?, ?, 'member', 'pending', ?, ?)",
            (user_id, workspace["id"], role_title, now),
        )
        return "pending"


def update_profile(user_id: str, full_name: str, role_title: str) -> None:
    """Updates the editable parts of a profile: display name and workspace title."""
    full_name = full_name.strip()
    role_title = role_title.strip()

    with get_db() as conn:
        conn.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name, user_id))
        conn.execute(
            "UPDATE memberships SET title = ? WHERE user_id = ?", (role_title, user_id)
        )


def rename_workspace(workspace_id: str, company_name: str) -> None:
    """Admin-only: renames the workspace's display name (never its join-matching domain)."""
    company_name = company_name.strip()
    with get_db() as conn:
        conn.execute(
            "UPDATE workspaces SET company_name = ? WHERE id = ?", (company_name, workspace_id)
        )


def create_invite(workspace_id: str, invited_email: str, created_by: str) -> dict:
    """
    Issues a single-use, 7-day invite for `invited_email` to join `workspace_id`, and
    emails it. The code/link/expiry are returned regardless of whether the email send
    succeeded, so the admin can still share it by hand — but the caller is told the
    truth about whether it was actually emailed, never a fabricated "sent" status.
    """
    invited_email = invited_email.strip().lower()
    code = secrets.token_urlsafe(24)
    now = _now()
    expires = now + datetime.timedelta(days=settings.INVITE_TTL_DAYS)

    with get_db() as conn:
        workspace = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if workspace is None:
            raise AuthError("Workspace not found.")

        conn.execute(
            "INSERT INTO workspace_invites (code, workspace_id, invited_email, created_by, created_at, expires_at, used) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (code, workspace_id, invited_email, created_by, _iso(now), _iso(expires)),
        )

    invite_url = f"{settings.FRONTEND_URL}?invite={code}"

    email_service = EmailService()
    sent = email_service.send(
        to=invited_email,
        subject=f"You're invited to join {workspace['company_name']} on SynkAI",
        text_body=(
            f"You've been invited to join {workspace['company_name']}'s SynkAI workspace.\n\n"
            f"Accept here: {invite_url}\n\n"
            f"This invite expires in {settings.INVITE_TTL_DAYS} days and can only be used once, "
            f"with this email address ({invited_email})."
        ),
    )
    if not sent.success:
        logger.error(f"Failed to email invite to '{invited_email}': {sent.error}")

    return {
        "code": code,
        "invited_email": invited_email,
        "expires_at": _iso(expires),
        "invite_url": invite_url,
        "email_sent": sent.success,
        "email_error": sent.error,
    }


def list_invites(workspace_id: str) -> List[dict]:
    """Lists outstanding (unused, unexpired) invites for a workspace."""
    now = _iso(_now())
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM workspace_invites WHERE workspace_id = ? AND used = 0 AND expires_at > ? "
            "ORDER BY created_at DESC",
            (workspace_id, now),
        ).fetchall()
    return [dict(r) for r in rows]


def approve_membership(workspace_id: str, target_user_id: str) -> None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM memberships WHERE user_id = ? AND workspace_id = ?",
            (target_user_id, workspace_id),
        ).fetchone()
        if row is None:
            raise AuthError("No such join request.")
        conn.execute(
            "UPDATE memberships SET status = 'active' WHERE user_id = ? AND workspace_id = ?",
            (target_user_id, workspace_id),
        )


def reject_membership(workspace_id: str, target_user_id: str) -> None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM memberships WHERE user_id = ? AND workspace_id = ?",
            (target_user_id, workspace_id),
        ).fetchone()
        if row is None:
            raise AuthError("No such join request.")
        conn.execute(
            "DELETE FROM memberships WHERE user_id = ? AND workspace_id = ?",
            (target_user_id, workspace_id),
        )


def list_members(workspace_id: str) -> Tuple[List[dict], List[dict]]:
    """Returns (active_members, pending_members) for a workspace."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT m.user_id, m.role, m.status, m.title, u.full_name, u.email
            FROM memberships m JOIN users u ON u.id = m.user_id
            WHERE m.workspace_id = ?
            ORDER BY m.created_at ASC
            """,
            (workspace_id,),
        ).fetchall()

    active = [dict(r) for r in rows if r["status"] == "active"]
    pending = [dict(r) for r in rows if r["status"] == "pending"]
    return active, pending


def get_workspace(workspace_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        return dict(row) if row else None


def ensure_default_workspace() -> None:
    """Creates the fixed-ID workspace that pre-account Sprint 1-4 data is migrated into."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM workspaces WHERE id = ?", (DEFAULT_WORKSPACE_ID,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO workspaces (id, company_name, domain, created_at) VALUES (?, ?, NULL, ?)",
                (DEFAULT_WORKSPACE_ID, settings.DEFAULT_WORKSPACE_NAME, _iso(_now())),
            )
            logger.info(f"Created default workspace '{DEFAULT_WORKSPACE_ID}' for migrated data.")
