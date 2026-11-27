"""
ICS (RFC 5545) Service for SynkAI.

Builds a standard calendar invite as raw text rather than pulling in a calendar
library — a single VEVENT with an organiser and attendees is a small, well-specified
format, and hand-building it keeps this dependency-free and easy to unit-test byte
for byte. Produces a METHOD:REQUEST invite on create/update and a METHOD:CANCEL
cancellation, both carrying the same UID so calendar clients treat them as the same
event — with SEQUENCE incremented on every change, per RFC 5545, so a client knows a
re-sent REQUEST supersedes the one before it.
"""

import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.config import settings

LINE_FOLD_LIMIT = 75


class InvalidTimezoneError(ValueError):
    """Raised when a meeting's timezone string isn't a known IANA zone."""


def validate_timezone(timezone_name: str) -> None:
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise InvalidTimezoneError(f"Unknown timezone '{timezone_name}'.") from exc


def _local_to_utc(date: str, time: str, timezone_name: str) -> datetime.datetime:
    """Combines a YYYY-MM-DD date and HH:MM time in `timezone_name` into a UTC datetime."""
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise InvalidTimezoneError(f"Unknown timezone '{timezone_name}'.") from exc

    naive = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=tz).astimezone(datetime.timezone.utc)


def meeting_start_utc(meeting: Dict) -> datetime.datetime:
    return _local_to_utc(meeting["date"], meeting["start_time"], meeting["timezone"])


def meeting_end_utc(meeting: Dict) -> datetime.datetime:
    return _local_to_utc(meeting["date"], meeting["end_time"], meeting["timezone"])


def _format_utc(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape(text: str) -> str:
    """Escapes text per RFC 5545 §3.3.11: backslash, semicolon, comma, then newlines."""
    text = text or ""
    text = text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return text.replace("\r\n", "\\n").replace("\n", "\\n")


def _fold(line: str) -> str:
    """
    Folds a content line longer than 75 octets, continuing with CRLF + a space — per
    RFC 5545 §3.1, that leading space itself counts toward the next line's 75-octet
    budget, so continuation chunks are one octet shorter than the first.
    """
    if len(line) <= LINE_FOLD_LIMIT:
        return line

    parts = [line[:LINE_FOLD_LIMIT]]
    rest = line[LINE_FOLD_LIMIT:]
    continuation_limit = LINE_FOLD_LIMIT - 1  # 1 octet reserved for the leading space
    while rest:
        parts.append(rest[:continuation_limit])
        rest = rest[continuation_limit:]
    return "\r\n ".join(parts)


def build_ics(
    meeting: Dict,
    participants: List[Dict[str, str]],
    organiser: Dict[str, str],
    method: str,
    description: str = "",
) -> bytes:
    """
    Builds a complete .ics document for one meeting.

    Args:
        meeting: dict with id, title, date, start_time, end_time, timezone, location,
            sequence (int).
        participants: list of {"name": ..., "email": ...}.
        organiser: {"name": ..., "email": ...}.
        method: "REQUEST" (create/update) or "CANCEL".
        description: pre-built invite body (agenda, objective, "from last meeting", ...).

    Returns:
        UTF-8 encoded .ics file content.
    """
    if method not in ("REQUEST", "CANCEL"):
        raise ValueError(f"Unsupported ICS method '{method}'.")

    now = datetime.datetime.now(datetime.timezone.utc)
    dtstamp = _format_utc(now)
    dtstart = _format_utc(meeting_start_utc(meeting))
    dtend = _format_utc(meeting_end_utc(meeting))
    status = "CANCELLED" if method == "CANCEL" else "CONFIRMED"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{settings.APP_NAME}//Meeting Scheduler//EN",
        f"METHOD:{method}",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{meeting['id']}@synkai.local",
        f"SEQUENCE:{meeting.get('sequence', 0)}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{_escape(meeting['title'])}",
        f"STATUS:{status}",
        f"ORGANIZER;CN={_escape(organiser.get('name') or organiser['email'])}:mailto:{organiser['email']}",
    ]

    if meeting.get("location"):
        lines.append(f"LOCATION:{_escape(meeting['location'])}")

    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")

    for person in participants:
        lines.append(
            f"ATTENDEE;CN={_escape(person.get('name') or person['email'])};RSVP=TRUE:mailto:{person['email']}"
        )

    lines += ["END:VEVENT", "END:VCALENDAR"]

    folded = [_fold(line) for line in lines]
    return ("\r\n".join(folded) + "\r\n").encode("utf-8")
