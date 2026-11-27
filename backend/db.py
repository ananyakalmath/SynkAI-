"""
SQLite persistence for SynkAI accounts, sessions, and workspaces.

Why SQLite (not the existing flat-JSON pattern used for the old password-based
data/users.json): accounts, workspaces, memberships and sessions are genuinely
relational — "which workspace does this user belong to, and is their membership
active" is exactly the kind of query flat JSON files make awkward and race-prone
under concurrent requests. SQLite is stdlib, needs no extra service, and fits the
project's local-first approach the same way ChromaDB and the uploads/ directory do.

A new connection is opened per call rather than shared across threads — SQLite
connections aren't safe to share across threads, and FastAPI runs blocking work
(including these calls) via asyncio.to_thread, so a short-lived connection per
operation is simpler and safer than coordinating one long-lived connection.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    domain TEXT UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    google_sub TEXT UNIQUE,
    onboarded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- At most one membership per user: onboarding sets a single company/workspace.
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
    status TEXT NOT NULL CHECK (status IN ('active', 'pending')),
    title TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0,
    user_agent TEXT
);

CREATE TABLE IF NOT EXISTS email_login_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0
);

-- `purpose` distinguishes an ordinary sign-in redirect from an incremental
-- "Connect Google Calendar" authorization (Phase 3); `user_id` is set only for the
-- latter, since that flow starts from an already-known, already-logged-in user.
CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    invite_code TEXT,
    purpose TEXT NOT NULL DEFAULT 'login',
    user_id TEXT
);

-- An admin-issued, single-use, 7-day invite for one specific email to join one
-- specific workspace — the only way to join a workspace whose domain is public
-- (gmail.com etc.) or that simply isn't the invitee's own email domain.
CREATE TABLE IF NOT EXISTS workspace_invites (
    code TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    invited_email TEXT NOT NULL,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);

-- A scheduled meeting. date/start_time/end_time are local to `timezone`; `sequence`
-- follows RFC5545 (incremented on every update/cancel) so calendar clients recognize
-- a re-sent .ics as a newer version of the same event rather than a duplicate.
CREATE TABLE IF NOT EXISTS scheduled_meetings (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    organiser_user_id TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    objective TEXT,
    meeting_type TEXT NOT NULL DEFAULT 'Other',
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    location TEXT,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'cancelled')) DEFAULT 'scheduled',
    previous_document_id TEXT,
    sequence INTEGER NOT NULL DEFAULT 0,
    reminder_24h_enabled INTEGER NOT NULL DEFAULT 1,
    reminder_1h_enabled INTEGER NOT NULL DEFAULT 1,
    reminder_24h_sent INTEGER NOT NULL DEFAULT 0,
    reminder_1h_sent INTEGER NOT NULL DEFAULT 0,
    google_event_id TEXT,
    google_meet_link TEXT,
    calendar_sync_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meeting_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES scheduled_meetings(id),
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meeting_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES scheduled_meetings(id),
    document_id TEXT NOT NULL,
    filename TEXT
);

-- A persisted snapshot of a /meeting/analyze result, so a later meeting can pull
-- "pending tasks/decisions from last meeting" into its invite email and agenda.
CREATE TABLE IF NOT EXISTS meeting_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    document_id TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- One row per user who has connected their Google account for calendar sync
-- (Phase 3) — at most one connection per user. The refresh token is the only
-- long-lived secret here and is stored encrypted (see token_crypto.py); the access
-- token is a short-lived cache to avoid refreshing on every single API call.
CREATE TABLE IF NOT EXISTS google_calendar_connections (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    encrypted_refresh_token TEXT NOT NULL,
    access_token TEXT,
    access_token_expires_at TEXT,
    scope TEXT,
    connected_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


# (table, column, column_ddl) for columns added to an *already-shipped* table after a
# real database may already exist on someone's machine — CREATE TABLE IF NOT EXISTS
# only handles brand-new tables, never retroactively adds columns to one that's already
# there. New tables never need an entry here.
ADDITIVE_COLUMNS = [
    ("oauth_states", "invite_code", "TEXT"),
    ("oauth_states", "purpose", "TEXT NOT NULL DEFAULT 'login'"),
    ("oauth_states", "user_id", "TEXT"),
    ("scheduled_meetings", "google_event_id", "TEXT"),
    ("scheduled_meetings", "google_meet_link", "TEXT"),
    ("scheduled_meetings", "calendar_sync_error", "TEXT"),
]


def _apply_additive_migrations(conn: sqlite3.Connection) -> None:
    for table, column, column_ddl in ADDITIVE_COLUMNS:
        existing_columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_ddl}")
            logger.info(f"Migrated existing '{table}' table: added column '{column}'.")


def init_db() -> None:
    """Creates every table if it doesn't already exist, then applies any additive
    column migrations needed by a database created before those columns existed. Safe
    to call repeatedly."""
    db_dir = os.path.dirname(settings.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with get_db() as conn:
        conn.executescript(SCHEMA)
        _apply_additive_migrations(conn)

    logger.info(f"Database ready at '{settings.DATABASE_PATH}'.")


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """
    Yields a connection with row access by column name, foreign keys enforced, and
    commit-on-success / rollback-on-error semantics.
    """
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
