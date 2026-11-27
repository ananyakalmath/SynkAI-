"""
Google Calendar Service for SynkAI (Phase 3).

Owns a user's "connection" (an encrypted refresh token, refreshed into short-lived
access tokens on demand) and the Calendar API v3 calls that create/update/delete an
event — with a Google Meet link via conferenceData.createRequest — on the organiser's
own "primary" calendar. Plain REST calls via `requests`, the same "direct HTTP
client" choice made for the rest of the Google integration (see
google_oauth_service.py).

Every public function here either succeeds or raises GoogleCalendarError — callers
(meeting_schedule_service) must treat a raise as "nothing happened on Google's side"
and fall back to the SMTP + .ics path, never surfacing a Meet link or event that was
never actually created.
"""

import datetime
import secrets
from typing import Any, Dict, List, Optional

import requests

from backend.db import get_db
from backend.services import google_oauth_service, token_crypto
from backend.services.google_oauth_service import GoogleOAuthError
from backend.services.token_crypto import TokenEncryptionError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

EVENTS_ENDPOINT = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

# Refresh an access token slightly before it actually expires, to avoid a request
# failing mid-flight on a token that expired a second ago.
ACCESS_TOKEN_SAFETY_MARGIN = datetime.timedelta(minutes=2)


class GoogleCalendarError(Exception):
    """Raised for any Google Calendar connection/API failure — callers must fall back."""


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat()


# ----------------------------------------------------------------------------
# Connection lifecycle
# ----------------------------------------------------------------------------

def is_connected(user_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM google_calendar_connections WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row is not None


def save_connection(
    user_id: str,
    refresh_token: str,
    access_token: Optional[str],
    expires_in: Optional[int],
    scope: Optional[str],
) -> None:
    """Stores (or replaces) a user's Google Calendar connection, refresh token encrypted."""
    now = _now()
    encrypted_refresh_token = token_crypto.encrypt(refresh_token)
    expires_at = _iso(now + datetime.timedelta(seconds=expires_in)) if expires_in else None

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO google_calendar_connections
                (user_id, encrypted_refresh_token, access_token, access_token_expires_at,
                 scope, connected_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                encrypted_refresh_token = excluded.encrypted_refresh_token,
                access_token = excluded.access_token,
                access_token_expires_at = excluded.access_token_expires_at,
                scope = excluded.scope,
                updated_at = excluded.updated_at
            """,
            (user_id, encrypted_refresh_token, access_token, expires_at, scope, _iso(now), _iso(now)),
        )


def disconnect(user_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM google_calendar_connections WHERE user_id = ?", (user_id,))


def _get_valid_access_token(user_id: str) -> str:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM google_calendar_connections WHERE user_id = ?", (user_id,)
        ).fetchone()

    if row is None:
        raise GoogleCalendarError("Google Calendar is not connected for this user.")

    if row["access_token"] and row["access_token_expires_at"]:
        expires_at = datetime.datetime.fromisoformat(row["access_token_expires_at"])
        if expires_at - ACCESS_TOKEN_SAFETY_MARGIN > _now():
            return row["access_token"]

    try:
        refresh_token = token_crypto.decrypt(row["encrypted_refresh_token"])
    except TokenEncryptionError as exc:
        raise GoogleCalendarError(str(exc)) from exc

    try:
        tokens = google_oauth_service.refresh_access_token(refresh_token)
    except GoogleOAuthError as exc:
        raise GoogleCalendarError(f"Could not refresh Google access token: {exc}") from exc

    access_token = tokens["access_token"]
    expires_in = tokens.get("expires_in", 3600)
    expires_at = _iso(_now() + datetime.timedelta(seconds=expires_in))

    with get_db() as conn:
        conn.execute(
            "UPDATE google_calendar_connections SET access_token = ?, access_token_expires_at = ?, updated_at = ? "
            "WHERE user_id = ?",
            (access_token, expires_at, _iso(_now()), user_id),
        )

    return access_token


# ----------------------------------------------------------------------------
# Calendar events
# ----------------------------------------------------------------------------

def _event_times(meeting: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    return {
        "start": {"dateTime": f"{meeting['date']}T{meeting['start_time']}:00", "timeZone": meeting["timezone"]},
        "end": {"dateTime": f"{meeting['date']}T{meeting['end_time']}:00", "timeZone": meeting["timezone"]},
    }


def _attendees(participants: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"email": p["email"], "displayName": p.get("name") or p["email"]} for p in participants]


def _extract_meet_link(event: Dict[str, Any]) -> Optional[str]:
    conference_data = event.get("conferenceData") or {}
    for entry_point in conference_data.get("entryPoints", []):
        if entry_point.get("entryPointType") == "video":
            return entry_point.get("uri")
    return event.get("hangoutLink")


def create_event(
    user_id: str, meeting: Dict[str, Any], participants: List[Dict[str, str]], description: str
) -> Dict[str, Optional[str]]:
    """
    Creates a Google Calendar event (with a Meet link) on `user_id`'s calendar.

    Returns {"event_id": ..., "meet_link": ...}. Raises GoogleCalendarError on any
    failure — the caller must fall back to SMTP + .ics, never claiming a Meet link
    exists.
    """
    access_token = _get_valid_access_token(user_id)

    body: Dict[str, Any] = {
        "summary": meeting["title"],
        "description": description,
        "attendees": _attendees(participants),
        "conferenceData": {
            "createRequest": {
                "requestId": secrets.token_hex(16),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        **_event_times(meeting),
    }
    if meeting.get("location"):
        body["location"] = meeting["location"]

    try:
        response = requests.post(
            EVENTS_ENDPOINT,
            params={"conferenceDataVersion": 1, "sendUpdates": "all"},
            headers={"Authorization": f"Bearer {access_token}"},
            json=body,
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        raise GoogleCalendarError(f"Could not reach Google Calendar: {exc}") from exc

    if response.status_code not in (200, 201):
        raise GoogleCalendarError(
            f"Google Calendar event creation failed (HTTP {response.status_code}): {response.text}"
        )

    event = response.json()
    return {"event_id": event["id"], "meet_link": _extract_meet_link(event)}


def update_event(
    user_id: str,
    event_id: str,
    meeting: Dict[str, Any],
    participants: List[Dict[str, str]],
    description: str,
) -> Dict[str, Optional[str]]:
    """
    Updates an existing event. Omits `conferenceData` entirely so the Meet link Google
    already assigned is preserved rather than regenerated.
    """
    access_token = _get_valid_access_token(user_id)

    body: Dict[str, Any] = {
        "summary": meeting["title"],
        "description": description,
        "attendees": _attendees(participants),
        **_event_times(meeting),
    }
    if meeting.get("location"):
        body["location"] = meeting["location"]

    try:
        response = requests.patch(
            f"{EVENTS_ENDPOINT}/{event_id}",
            params={"conferenceDataVersion": 1, "sendUpdates": "all"},
            headers={"Authorization": f"Bearer {access_token}"},
            json=body,
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        raise GoogleCalendarError(f"Could not reach Google Calendar: {exc}") from exc

    if response.status_code != 200:
        raise GoogleCalendarError(
            f"Google Calendar event update failed (HTTP {response.status_code}): {response.text}"
        )

    event = response.json()
    return {"event_id": event["id"], "meet_link": _extract_meet_link(event)}


def delete_event(user_id: str, event_id: str) -> None:
    """Deletes an event (Google emails attendees the cancellation via sendUpdates=all)."""
    access_token = _get_valid_access_token(user_id)

    try:
        response = requests.delete(
            f"{EVENTS_ENDPOINT}/{event_id}",
            params={"sendUpdates": "all"},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        raise GoogleCalendarError(f"Could not reach Google Calendar: {exc}") from exc

    # Google returns 410 Gone if the event was already deleted on its side — treat
    # that the same as success rather than as a failure to fall back from.
    if response.status_code not in (200, 204, 410):
        raise GoogleCalendarError(
            f"Google Calendar event deletion failed (HTTP {response.status_code}): {response.text}"
        )
