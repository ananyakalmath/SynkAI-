"""
Unit tests for ICS (.ics) generation: valid RFC 5545 structure, correct UTC conversion
from a local date/time/timezone, REQUEST vs CANCEL, and line folding.
"""

import pytest

from backend.services.ics_service import (
    InvalidTimezoneError,
    build_ics,
    meeting_end_utc,
    meeting_start_utc,
    validate_timezone,
)

MEETING = {
    "id": "meeting-abc123",
    "title": "Sprint planning",
    "date": "2026-03-10",
    "start_time": "09:00",
    "end_time": "09:30",
    "timezone": "Asia/Kolkata",
    "location": "Conference Room A",
    "sequence": 0,
}

ORGANISER = {"name": "Ada Founder", "email": "ada@acme.com"}
PARTICIPANTS = [
    {"name": "Bob Builder", "email": "bob@acme.com"},
    {"name": "Cara Dev", "email": "cara@acme.com"},
]


def _decode(ics_bytes: bytes) -> str:
    return ics_bytes.decode("utf-8")


def test_ist_to_utc_conversion_is_correct():
    # Asia/Kolkata is UTC+5:30, no DST — 09:00 IST is 03:30 UTC the same day.
    start = meeting_start_utc(MEETING)
    assert start.isoformat() == "2026-03-10T03:30:00+00:00"

    end = meeting_end_utc(MEETING)
    assert end.isoformat() == "2026-03-10T03:30:00+00:00".replace("03:30", "04:00")


def test_build_ics_request_has_valid_structure():
    ics = _decode(build_ics(MEETING, PARTICIPANTS, ORGANISER, "REQUEST", description="Agenda:\n- Item one"))

    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.rstrip("\r\n").endswith("END:VCALENDAR")
    assert "VERSION:2.0\r\n" in ics
    assert "METHOD:REQUEST\r\n" in ics
    assert "BEGIN:VEVENT\r\n" in ics
    assert "END:VEVENT\r\n" in ics
    assert "UID:meeting-abc123@synkai.local\r\n" in ics
    assert "SEQUENCE:0\r\n" in ics
    assert "DTSTART:20260310T033000Z\r\n" in ics
    assert "DTEND:20260310T040000Z\r\n" in ics
    assert "SUMMARY:Sprint planning\r\n" in ics
    assert "STATUS:CONFIRMED\r\n" in ics
    assert "ORGANIZER;CN=Ada Founder:mailto:ada@acme.com\r\n" in ics
    assert "ATTENDEE;CN=Bob Builder;RSVP=TRUE:mailto:bob@acme.com\r\n" in ics
    assert "ATTENDEE;CN=Cara Dev;RSVP=TRUE:mailto:cara@acme.com\r\n" in ics
    assert "LOCATION:Conference Room A\r\n" in ics


def test_build_ics_cancel_has_cancel_method_and_status():
    ics = _decode(build_ics(MEETING, PARTICIPANTS, ORGANISER, "CANCEL"))
    assert "METHOD:CANCEL\r\n" in ics
    assert "STATUS:CANCELLED\r\n" in ics


def test_build_ics_rejects_unknown_method():
    with pytest.raises(ValueError):
        build_ics(MEETING, PARTICIPANTS, ORGANISER, "BOGUS")


def test_build_ics_increments_sequence():
    updated = dict(MEETING, sequence=3)
    ics = _decode(build_ics(updated, PARTICIPANTS, ORGANISER, "REQUEST"))
    assert "SEQUENCE:3\r\n" in ics


def test_special_characters_are_escaped():
    meeting = dict(MEETING, title="Q&A, Review; Notes\nSecond line")
    ics = _decode(build_ics(meeting, [], ORGANISER, "REQUEST"))
    assert "SUMMARY:Q&A\\, Review\\; Notes\\nSecond line\r\n" in ics


def test_long_description_line_is_folded_per_rfc5545():
    long_text = "x" * 200
    ics = _decode(build_ics(MEETING, [], ORGANISER, "REQUEST", description=long_text))
    # Every physical line emitted (after \r\n splitting) must be at most 75 octets,
    # except a folded continuation line, which starts with a single leading space.
    for line in ics.split("\r\n"):
        assert len(line) <= 75


def test_validate_timezone_accepts_known_zone():
    validate_timezone("Asia/Kolkata")  # must not raise


def test_validate_timezone_rejects_unknown_zone():
    with pytest.raises(InvalidTimezoneError):
        validate_timezone("Mars/Olympus_Mons")
