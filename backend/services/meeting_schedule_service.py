"""
Meeting Schedule Service for SynkAI.

Owns the scheduled-meeting lifecycle: create, update, cancel, and list, each change
emailing every participant a calendar invite (.ics, METHOD:REQUEST on create/update,
METHOD:CANCEL on cancel) plus optional 24h/1h reminder emails. Every email send is
reported back truthfully — a failure is recorded and surfaced to the caller, never
silently swallowed into a response that implies it went out.
"""

import datetime
import secrets
from typing import Any, Dict, List, Optional

from backend.db import get_db
from backend.services import agenda_service, analysis_store, google_calendar_service, ics_service
from backend.services.email_service import EmailService
from backend.services.google_calendar_service import GoogleCalendarError
from backend.services.ics_service import InvalidTimezoneError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MeetingNotFoundError(Exception):
    """Raised when a meeting_id doesn't exist in the caller's workspace."""


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _get_organiser(conn, user_id: str) -> Dict[str, Any]:
    row = conn.execute("SELECT id, full_name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"user_id": row["id"], "name": row["full_name"], "email": row["email"]}


def _fetch_participants(conn, meeting_id: str) -> List[Dict[str, str]]:
    rows = conn.execute(
        "SELECT name, email FROM meeting_participants WHERE meeting_id = ? ORDER BY id", (meeting_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_document_ids(conn, meeting_id: str) -> List[str]:
    rows = conn.execute(
        "SELECT document_id FROM meeting_documents WHERE meeting_id = ? ORDER BY id", (meeting_id,)
    ).fetchall()
    return [r["document_id"] for r in rows]


def _row_to_meeting_dict(conn, row) -> Dict[str, Any]:
    meeting = dict(row)
    return {
        "id": meeting["id"],
        "workspace_id": meeting["workspace_id"],
        "organiser": _get_organiser(conn, meeting["organiser_user_id"]),
        "title": meeting["title"],
        "objective": meeting["objective"],
        "meeting_type": meeting["meeting_type"],
        "date": meeting["date"],
        "start_time": meeting["start_time"],
        "end_time": meeting["end_time"],
        "timezone": meeting["timezone"],
        "location": meeting["location"],
        "status": meeting["status"],
        "participants": _fetch_participants(conn, meeting["id"]),
        "document_ids": _fetch_document_ids(conn, meeting["id"]),
        "previous_document_id": meeting["previous_document_id"],
        "sequence": meeting["sequence"],
        "reminder_24h_enabled": bool(meeting["reminder_24h_enabled"]),
        "reminder_1h_enabled": bool(meeting["reminder_1h_enabled"]),
        "reminder_24h_sent": bool(meeting["reminder_24h_sent"]),
        "reminder_1h_sent": bool(meeting["reminder_1h_sent"]),
        "google_event_id": meeting["google_event_id"],
        "google_meet_link": meeting["google_meet_link"],
        "calendar_sync_error": meeting["calendar_sync_error"],
        "created_at": meeting["created_at"],
        "updated_at": meeting["updated_at"],
    }


def _fetch_meeting_row(conn, workspace_id: str, meeting_id: str):
    row = conn.execute(
        "SELECT * FROM scheduled_meetings WHERE id = ? AND workspace_id = ?",
        (meeting_id, workspace_id),
    ).fetchone()
    if row is None:
        raise MeetingNotFoundError(f"Meeting '{meeting_id}' not found.")
    return row


def _replace_participants(conn, meeting_id: str, participants: List[Dict[str, str]]) -> None:
    conn.execute("DELETE FROM meeting_participants WHERE meeting_id = ?", (meeting_id,))
    for p in participants:
        conn.execute(
            "INSERT INTO meeting_participants (meeting_id, name, email) VALUES (?, ?, ?)",
            (meeting_id, p["name"], p["email"]),
        )


def _replace_documents(conn, meeting_id: str, document_ids: List[str]) -> None:
    conn.execute("DELETE FROM meeting_documents WHERE meeting_id = ?", (meeting_id,))
    for document_id in document_ids:
        conn.execute(
            "INSERT INTO meeting_documents (meeting_id, document_id) VALUES (?, ?)",
            (meeting_id, document_id),
        )


def _build_description(
    meeting: Dict[str, Any], agenda: List[str], last_meeting: Optional[Dict[str, List[str]]]
) -> str:
    lines: List[str] = []
    if meeting.get("objective"):
        lines.append(f"Objective: {meeting['objective']}")
        lines.append("")

    lines.append("Agenda:")
    lines += [f"- {item}" for item in agenda]

    if last_meeting:
        lines.append("")
        lines.append("From last meeting:")
        if last_meeting["decisions"]:
            lines.append("Decisions:")
            lines += [f"- {d}" for d in last_meeting["decisions"]]
        if last_meeting["pending_action_items"]:
            lines.append("Pending action items:")
            lines += [f"- {a}" for a in last_meeting["pending_action_items"]]
        if last_meeting["risks"]:
            lines.append("Open risks:")
            lines += [f"- {r}" for r in last_meeting["risks"]]

    return "\n".join(lines)


def _meeting_description(meeting: Dict[str, Any]) -> str:
    """Builds the agenda + 'from last meeting' text shared by the email body, the .ics
    DESCRIPTION, and the Google Calendar event description — one source, so all three
    never drift apart."""
    last_meeting = None
    if meeting.get("previous_document_id"):
        analysis = analysis_store.get_latest_analysis(meeting["workspace_id"], meeting["previous_document_id"])
        last_meeting = agenda_service.build_last_meeting_section(analysis)

    agenda = agenda_service.generate_agenda(meeting.get("objective"))
    return _build_description(meeting, agenda, last_meeting)


def _sync_meeting_with_google(meeting: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates or updates the organiser's Google Calendar event for this meeting, if
    they've connected Google Calendar. Never raises — returns
    {"synced": bool, "event_id": ..., "meet_link": ..., "error": ...} so the caller can
    fall back to SMTP + .ics on `synced=False` without losing the meeting itself.
    """
    organiser_user_id = meeting["organiser"]["user_id"]
    if not google_calendar_service.is_connected(organiser_user_id):
        return {
            "synced": False,
            "event_id": meeting.get("google_event_id"),
            "meet_link": meeting.get("google_meet_link"),
            "error": None,
        }

    description = _meeting_description(meeting)

    try:
        if meeting.get("google_event_id"):
            result = google_calendar_service.update_event(
                organiser_user_id, meeting["google_event_id"], meeting, meeting["participants"], description
            )
        else:
            result = google_calendar_service.create_event(
                organiser_user_id, meeting, meeting["participants"], description
            )
    except GoogleCalendarError as exc:
        logger.error(f"Google Calendar sync failed for meeting '{meeting['id']}': {exc}")
        return {
            "synced": False,
            "event_id": meeting.get("google_event_id"),
            "meet_link": meeting.get("google_meet_link"),
            "error": str(exc),
        }

    return {"synced": True, "event_id": result["event_id"], "meet_link": result.get("meet_link"), "error": None}


def _cancel_meeting_with_google(meeting: Dict[str, Any]) -> Dict[str, Any]:
    """Deletes the organiser's Google Calendar event, if one exists and they're still
    connected. Never raises — returns {"synced": bool, "error": ...}."""
    organiser_user_id = meeting["organiser"]["user_id"]
    event_id = meeting.get("google_event_id")
    if not event_id or not google_calendar_service.is_connected(organiser_user_id):
        return {"synced": False, "error": None}

    try:
        google_calendar_service.delete_event(organiser_user_id, event_id)
    except GoogleCalendarError as exc:
        logger.error(f"Google Calendar cancellation failed for meeting '{meeting['id']}': {exc}")
        return {"synced": False, "error": str(exc)}

    return {"synced": True, "error": None}


def _send_invites(meeting: Dict[str, Any], method: str) -> List[Dict[str, Any]]:
    """Emails every participant a calendar invite/update/cancellation. Reports truthfully."""
    description = _meeting_description(meeting)
    organiser = meeting["organiser"]

    when = f"{meeting['date']} {meeting['start_time']}–{meeting['end_time']} ({meeting['timezone']})"

    if method == "CANCEL":
        subject = f"Cancelled: {meeting['title']} — {meeting['date']}"
        intro = f"The following meeting has been cancelled:\n\n{meeting['title']}\n{when}"
    else:
        verb = "Updated invite" if meeting["sequence"] > 0 else "Invite"
        subject = f"{verb}: {meeting['title']} — {meeting['date']}"
        intro = f"{meeting['title']}\n{when}"
        if meeting.get("location"):
            intro += f"\nLocation: {meeting['location']}"

    organiser_label = organiser.get("name") or organiser["email"]
    body = f"{intro}\n\n{description}\n\nOrganised by {organiser_label}."

    try:
        ics_bytes = ics_service.build_ics(meeting, meeting["participants"], organiser, method, description)
    except InvalidTimezoneError as exc:
        logger.error(f"Could not build .ics for meeting '{meeting['id']}': {exc}")
        return [
            {"email": p["email"], "success": False, "error": str(exc)} for p in meeting["participants"]
        ]

    email_service = EmailService()
    results = []
    for participant in meeting["participants"]:
        sent = email_service.send(
            to=participant["email"],
            subject=subject,
            text_body=body,
            calendar_invite=(ics_bytes, method),
        )
        if not sent.success:
            logger.error(f"Failed to send meeting invite to '{participant['email']}': {sent.error}")
        results.append({"email": participant["email"], "success": sent.success, "error": sent.error})

    return results


def create_meeting(workspace_id: str, organiser_user_id: str, data: Dict[str, Any]) -> tuple:
    """
    Creates a meeting and emails every participant an invite.

    Returns:
        (meeting_dict, invite_results)

    Raises:
        InvalidTimezoneError: `data["timezone"]` isn't a known IANA zone.
    """
    ics_service.validate_timezone(data["timezone"])

    meeting_id = secrets.token_hex(16)
    now = _now_iso()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO scheduled_meetings (
                id, workspace_id, organiser_user_id, title, objective, meeting_type,
                date, start_time, end_time, timezone, location, status,
                previous_document_id, sequence, reminder_24h_enabled, reminder_1h_enabled,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, 0, ?, ?, ?, ?)
            """,
            (
                meeting_id, workspace_id, organiser_user_id, data["title"], data.get("objective"),
                data["meeting_type"], data["date"], data["start_time"], data["end_time"],
                data["timezone"], data.get("location"), data.get("previous_document_id"),
                int(data.get("reminder_24h_enabled", True)), int(data.get("reminder_1h_enabled", True)),
                now, now,
            ),
        )
        _replace_participants(conn, meeting_id, [p for p in data["participants"]])
        _replace_documents(conn, meeting_id, data.get("document_ids", []))

        row = _fetch_meeting_row(conn, workspace_id, meeting_id)
        meeting = _row_to_meeting_dict(conn, row)

    meeting, synced = _apply_google_sync_and_persist(workspace_id, meeting_id, meeting)
    invite_results = [] if synced else (_send_invites(meeting, "REQUEST") if meeting["participants"] else [])
    return meeting, invite_results


def update_meeting(workspace_id: str, meeting_id: str, data: Dict[str, Any]) -> tuple:
    """
    Replaces a meeting's details and emails every (new) participant an updated invite.

    Returns:
        (meeting_dict, invite_results)

    Raises:
        MeetingNotFoundError: no such meeting in this workspace.
        InvalidTimezoneError: `data["timezone"]` isn't a known IANA zone.
    """
    ics_service.validate_timezone(data["timezone"])
    now = _now_iso()

    with get_db() as conn:
        existing = _fetch_meeting_row(conn, workspace_id, meeting_id)
        if existing["status"] == "cancelled":
            raise MeetingNotFoundError(f"Meeting '{meeting_id}' has been cancelled.")

        conn.execute(
            """
            UPDATE scheduled_meetings SET
                title = ?, objective = ?, meeting_type = ?, date = ?, start_time = ?,
                end_time = ?, timezone = ?, location = ?, previous_document_id = ?,
                reminder_24h_enabled = ?, reminder_1h_enabled = ?,
                reminder_24h_sent = 0, reminder_1h_sent = 0,
                sequence = sequence + 1, updated_at = ?
            WHERE id = ? AND workspace_id = ?
            """,
            (
                data["title"], data.get("objective"), data["meeting_type"], data["date"],
                data["start_time"], data["end_time"], data["timezone"], data.get("location"),
                data.get("previous_document_id"), int(data.get("reminder_24h_enabled", True)),
                int(data.get("reminder_1h_enabled", True)), now, meeting_id, workspace_id,
            ),
        )
        _replace_participants(conn, meeting_id, data["participants"])
        _replace_documents(conn, meeting_id, data.get("document_ids", []))

        row = _fetch_meeting_row(conn, workspace_id, meeting_id)
        meeting = _row_to_meeting_dict(conn, row)

    meeting, synced = _apply_google_sync_and_persist(workspace_id, meeting_id, meeting)
    invite_results = [] if synced else (_send_invites(meeting, "REQUEST") if meeting["participants"] else [])
    return meeting, invite_results


def _apply_google_sync_and_persist(workspace_id: str, meeting_id: str, meeting: Dict[str, Any]) -> tuple:
    """Runs `_sync_meeting_with_google`, persists its outcome, and returns the
    refreshed (meeting_dict, synced) so the caller knows whether to also send an
    SMTP + .ics invite."""
    sync_result = _sync_meeting_with_google(meeting)
    with get_db() as conn:
        conn.execute(
            "UPDATE scheduled_meetings SET google_event_id = ?, google_meet_link = ?, calendar_sync_error = ? "
            "WHERE id = ?",
            (sync_result["event_id"], sync_result["meet_link"], sync_result["error"], meeting_id),
        )
        row = _fetch_meeting_row(conn, workspace_id, meeting_id)
        meeting = _row_to_meeting_dict(conn, row)
    return meeting, sync_result["synced"]


def cancel_meeting(workspace_id: str, meeting_id: str) -> tuple:
    """
    Cancels a meeting and emails every participant a cancellation.

    Returns:
        (meeting_dict, invite_results)

    Raises:
        MeetingNotFoundError: no such meeting in this workspace.
    """
    now = _now_iso()

    with get_db() as conn:
        _fetch_meeting_row(conn, workspace_id, meeting_id)
        conn.execute(
            "UPDATE scheduled_meetings SET status = 'cancelled', sequence = sequence + 1, updated_at = ? "
            "WHERE id = ? AND workspace_id = ?",
            (now, meeting_id, workspace_id),
        )
        row = _fetch_meeting_row(conn, workspace_id, meeting_id)
        meeting = _row_to_meeting_dict(conn, row)

    cancel_result = _cancel_meeting_with_google(meeting)
    if meeting.get("google_event_id"):
        with get_db() as conn:
            conn.execute(
                "UPDATE scheduled_meetings SET calendar_sync_error = ? WHERE id = ?",
                (cancel_result["error"], meeting_id),
            )
            row = _fetch_meeting_row(conn, workspace_id, meeting_id)
            meeting = _row_to_meeting_dict(conn, row)

    invite_results = [] if cancel_result["synced"] else (_send_invites(meeting, "CANCEL") if meeting["participants"] else [])
    return meeting, invite_results


def get_meeting(workspace_id: str, meeting_id: str) -> Dict[str, Any]:
    """Raises MeetingNotFoundError if `meeting_id` doesn't belong to `workspace_id`."""
    with get_db() as conn:
        row = _fetch_meeting_row(conn, workspace_id, meeting_id)
        return _row_to_meeting_dict(conn, row)


def list_meetings_by_month(workspace_id: str, year: int, month: int) -> List[Dict[str, Any]]:
    """Lists every meeting (any status) in `workspace_id` falling in the given month."""
    prefix = f"{year:04d}-{month:02d}"
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_meetings WHERE workspace_id = ? AND date LIKE ? ORDER BY date, start_time",
            (workspace_id, f"{prefix}%"),
        ).fetchall()
        return [_row_to_meeting_dict(conn, row) for row in rows]


# ----------------------------------------------------------------------------
# Reminders
# ----------------------------------------------------------------------------

def send_due_reminders(now: Optional[datetime.datetime] = None) -> int:
    """
    Scans every workspace's scheduled (non-cancelled) meetings and emails any 24h/1h
    reminder that's now due and hasn't already been sent. Safe to call repeatedly —
    the reminder_*_sent flags make each reminder a one-time send.

    Returns:
        Number of reminder emails sent.
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    sent_count = 0

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_meetings WHERE status = 'scheduled' "
            "AND (reminder_24h_sent = 0 OR reminder_1h_sent = 0)"
        ).fetchall()
        meetings = [_row_to_meeting_dict(conn, row) for row in rows]

    email_service = EmailService()

    for meeting in meetings:
        try:
            start_utc = ics_service.meeting_start_utc(meeting)
        except InvalidTimezoneError:
            continue

        time_until = start_utc - now
        when = f"{meeting['date']} {meeting['start_time']}–{meeting['end_time']} ({meeting['timezone']})"

        # Bounds are mutually exclusive (24h fires in (1h, 24h], 1h fires in [0, 1h]) so
        # a meeting created with little lead time triggers exactly one reminder, not
        # both at once just because it's also technically "under 24h away".
        windows = (
            (24, "reminder_24h_enabled", "reminder_24h_sent", datetime.timedelta(hours=1), datetime.timedelta(hours=24)),
            (1, "reminder_1h_enabled", "reminder_1h_sent", datetime.timedelta(0), datetime.timedelta(hours=1)),
        )
        for window_hours, enabled_column, flag_column, lower_bound, upper_bound in windows:
            if not meeting[enabled_column] or meeting[flag_column]:
                continue
            is_due = (lower_bound < time_until <= upper_bound) if window_hours == 24 else (lower_bound <= time_until <= upper_bound)
            if is_due:
                subject = f"Reminder: {meeting['title']} in {window_hours}h"
                body = (
                    f"Reminder — this meeting starts in about {window_hours} hour(s):\n\n"
                    f"{meeting['title']}\n{when}"
                    + (f"\nLocation: {meeting['location']}" if meeting.get("location") else "")
                )
                for participant in meeting["participants"]:
                    result = email_service.send(to=participant["email"], subject=subject, text_body=body)
                    if not result.success:
                        logger.error(
                            f"Failed to send {window_hours}h reminder to '{participant['email']}' "
                            f"for meeting '{meeting['id']}': {result.error}"
                        )
                    else:
                        sent_count += 1

                with get_db() as conn:
                    conn.execute(
                        f"UPDATE scheduled_meetings SET {flag_column} = 1 WHERE id = ?", (meeting["id"],)
                    )

    return sent_count
