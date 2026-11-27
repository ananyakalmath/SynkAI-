"""
Calendar view (Phase 2, basic only — full UI redesign is a later sprint).

A month grid with meeting days highlighted and colour-coded by meeting type; clicking
a day shows its meetings' details, agenda, and brief. A "Schedule meeting" form below
creates a new one.
"""

import calendar as calendar_module
import datetime

import streamlit as st

from frontend.components import api, ui

MEETING_TYPES = ["Standup", "Planning", "Review", "1:1", "All Hands", "Other"]

TYPE_COLORS = {
    "Standup": "#5B8DEF",
    "Planning": "#8A63D2",
    "Review": "#3FB68A",
    "1:1": "#E08E45",
    "All Hands": "#D1495B",
    "Other": "#8A8A8A",
}


def _month_meetings(year: int, month: int) -> dict:
    """Returns {day_number: [meeting, ...]} for the given month."""
    try:
        meetings = api.list_scheduled_meetings(year, month)
    except api.BackendError as exc:
        st.error(str(exc))
        return {}

    by_day: dict = {}
    for meeting in meetings:
        day = int(meeting["date"].split("-")[2])
        by_day.setdefault(day, []).append(meeting)
    return by_day


def _render_month_grid(year: int, month: int, by_day: dict) -> None:
    cal = calendar_module.Calendar(firstweekday=0)  # Monday first
    weeks = cal.monthdayscalendar(year, month)

    header_cols = st.columns(7)
    for col, label in zip(header_cols, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        col.markdown(f"**{label}**")

    for week in weeks:
        cols = st.columns(7)
        for col, day in zip(cols, week):
            if day == 0:
                col.write("")
                continue

            day_meetings = by_day.get(day, [])
            label = str(day)
            if day_meetings:
                titles = ", ".join(m["title"] for m in day_meetings[:2])
                label = f"{day} • {titles}"

            if col.button(label, key=f"cal_day_{year}_{month}_{day}", use_container_width=True):
                st.session_state.selected_calendar_day = f"{year:04d}-{month:02d}-{day:02d}"

            if day_meetings:
                dots = "".join(
                    f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
                    f'background:{TYPE_COLORS.get(m["meeting_type"], TYPE_COLORS["Other"])};margin-right:3px;"></span>'
                    for m in day_meetings
                )
                col.markdown(dots, unsafe_allow_html=True)


def _render_day_details(by_day: dict, selected_date: str) -> None:
    day = int(selected_date.split("-")[2])
    meetings = by_day.get(day, [])

    st.markdown(f"#### {selected_date}")
    if not meetings:
        st.caption("No meetings scheduled.")
        return

    for meeting in meetings:
        color = TYPE_COLORS.get(meeting["meeting_type"], TYPE_COLORS["Other"])
        status_label = "CANCELLED" if meeting["status"] == "cancelled" else meeting["meeting_type"]

        st.markdown(
            f"""
            <div style="border-left: 4px solid {color}; padding: 0.6rem 1rem; margin-bottom: 0.8rem;
                        border-radius: 6px; background: rgba(0,0,0,0.03);">
                <b>{ui.esc(meeting['title'])}</b> &nbsp;
                <span style="opacity:0.6; font-size:0.85rem;">[{ui.esc(status_label)}]</span><br/>
                <span style="opacity:0.7; font-size:0.9rem;">
                    {ui.esc(meeting['start_time'])}–{ui.esc(meeting['end_time'])} ({ui.esc(meeting['timezone'])})
                    {' · ' + ui.esc(meeting['location']) if meeting.get('location') else ''}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Details", expanded=False):
            if meeting.get("objective"):
                st.write(f"**Objective:** {meeting['objective']}")
            st.write(f"**Organiser:** {meeting['organiser'].get('name') or meeting['organiser']['email']}")
            if meeting.get("google_meet_link"):
                st.write(f"**Google Meet:** {meeting['google_meet_link']}")
            if meeting.get("calendar_sync_error"):
                st.warning(f"Google Calendar sync issue: {meeting['calendar_sync_error']}")
            if meeting["participants"]:
                st.write("**Participants:**")
                for p in meeting["participants"]:
                    st.write(f"- {p['name']} ({p['email']})")
            if meeting["document_ids"]:
                st.write(f"**Attached documents:** {', '.join(meeting['document_ids'])}")

            if meeting["status"] != "cancelled":
                if st.button("Cancel meeting", key=f"cancel_{meeting['id']}"):
                    try:
                        api.cancel_scheduled_meeting(meeting["id"])
                        st.success("Meeting cancelled and participants notified.")
                        st.rerun()
                    except api.BackendError as exc:
                        st.error(str(exc))


def _parse_participants(raw_text: str) -> list:
    participants = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            name, email = line.split(",", 1)
        elif "<" in line and ">" in line:
            name, email = line.split("<", 1)
            email = email.rstrip(">")
        else:
            name, email = line, line
        participants.append({"name": name.strip(), "email": email.strip()})
    return participants


def _render_schedule_form(default_date: datetime.date) -> None:
    st.markdown("### Schedule a meeting")

    title = st.text_input("Title", key="sched_title")
    objective = st.text_area("Objective", key="sched_objective", height=80)
    meeting_type = st.selectbox("Meeting type", MEETING_TYPES, key="sched_type")

    col1, col2, col3 = st.columns(3)
    with col1:
        date = st.date_input("Date", value=default_date, key="sched_date")
    with col2:
        start_time = st.time_input("Start time", value=datetime.time(9, 0), key="sched_start")
    with col3:
        end_time = st.time_input("End time", value=datetime.time(9, 30), key="sched_end")

    col4, col5 = st.columns(2)
    with col4:
        timezone = st.text_input("Timezone (IANA)", value="Asia/Kolkata", key="sched_tz")
    with col5:
        location = st.text_input("Location or meeting link", key="sched_location")

    participants_text = st.text_area(
        "Participants — one per line: `Name, email@example.com`",
        key="sched_participants",
        height=100,
    )

    previous_document_id = st.text_input(
        "Previous meeting's document ID (optional — pulls pending items into the invite)",
        key="sched_previous_doc",
    )

    col6, col7 = st.columns(2)
    with col6:
        reminder_24h = st.checkbox("Send a 24h reminder", value=True, key="sched_reminder_24h")
    with col7:
        reminder_1h = st.checkbox("Send a 1h reminder", value=True, key="sched_reminder_1h")

    if st.button("Schedule meeting", type="primary", use_container_width=True):
        if not title.strip():
            st.error("Title is required.")
            return

        participants = _parse_participants(participants_text)

        data = {
            "title": title.strip(),
            "objective": objective.strip() or None,
            "meeting_type": meeting_type,
            "date": date.strftime("%Y-%m-%d"),
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "timezone": timezone.strip() or "Asia/Kolkata",
            "location": location.strip() or None,
            "participants": participants,
            "previous_document_id": previous_document_id.strip() or None,
            "reminder_24h_enabled": reminder_24h,
            "reminder_1h_enabled": reminder_1h,
        }

        try:
            result = api.create_scheduled_meeting(data)
        except api.BackendError as exc:
            st.error(str(exc))
            return

        meet_link = result["meeting"].get("google_meet_link")
        sync_error = result["meeting"].get("calendar_sync_error")
        failed = [r for r in result.get("invite_results", []) if not r["success"]]

        if meet_link:
            st.success(f"Meeting scheduled on Google Calendar with a Meet link: {meet_link}")
        elif failed:
            failed_list = ", ".join(r["email"] for r in failed)
            st.warning(f"Meeting scheduled, but the invite email failed for: {failed_list}.")
        else:
            st.success("Meeting scheduled and invites sent.")

        if sync_error:
            st.warning(f"Google Calendar sync issue (invites were still emailed): {sync_error}")
        st.rerun()


def render(go) -> None:
    ui.page_header(
        "Workspace",
        "Calendar",
        "See what's scheduled this month, and plan the next meeting.",
    )
    ui.rule()

    today = datetime.date.today()
    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year
        st.session_state.calendar_month = today.month

    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.button("← Previous"):
            st.session_state.calendar_month -= 1
            if st.session_state.calendar_month < 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            st.rerun()
    with nav_col2:
        month_name = calendar_module.month_name[st.session_state.calendar_month]
        st.markdown(f"<h3 style='text-align:center'>{month_name} {st.session_state.calendar_year}</h3>", unsafe_allow_html=True)
    with nav_col3:
        if st.button("Next →"):
            st.session_state.calendar_month += 1
            if st.session_state.calendar_month > 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            st.rerun()

    year = st.session_state.calendar_year
    month = st.session_state.calendar_month
    by_day = _month_meetings(year, month)

    _render_month_grid(year, month, by_day)

    ui.spacer(1.0)
    selected = st.session_state.get("selected_calendar_day")
    if selected and selected.startswith(f"{year:04d}-{month:02d}"):
        _render_day_details(by_day, selected)
    else:
        st.caption("Click a day above to see its meetings.")

    ui.spacer(1.5)
    ui.rule()
    ui.spacer(1.0)
    _render_schedule_form(default_date=today)
