"""
Reusable SynkAI interface components.

Everything here renders markup only — no backend calls and no state mutation — so pages
stay readable and the visual language stays identical across the app.
"""

import html
from datetime import datetime
from typing import Iterable, List, Optional, Sequence

import streamlit as st

from frontend.components import icons
from frontend.components.theme import MOSS


def esc(value: object) -> str:
    """
    Escapes a value for safe inclusion in custom HTML.

    Args:
        value (object): Any value; None becomes an empty string.

    Returns:
        str: HTML-escaped text.
    """
    if value is None:
        return ""
    return html.escape(str(value))


def spacer(rem: float = 1.0) -> None:
    """Inserts vertical whitespace."""
    st.markdown(f"<div style='height:{rem}rem'></div>", unsafe_allow_html=True)


def rule() -> None:
    """Inserts a hairline divider with editorial spacing."""
    st.markdown("<hr class='sk-rule'/>", unsafe_allow_html=True)


def page_header(
    eyebrow: str,
    title: str,
    subtitle: Optional[str] = None,
    show_date: bool = True,
    show_bell: bool = True,
) -> None:
    """
    Renders the top-of-page header: overline, serif title, optional subtitle, and the
    date / notification cluster on the right.

    Args:
        eyebrow (str): Small uppercase overline.
        title (str): Serif page title.
        subtitle (Optional[str]): Supporting sentence under the title.
        show_date (bool): Render today's date on the right.
        show_bell (bool): Render the notification mark on the right.
    """
    right_parts = []
    if show_date:
        right_parts.append(
            f"<span class='sk-date'>{esc(datetime.now().strftime('%d %b %Y'))}</span>"
        )
    if show_bell:
        right_parts.append(f"<span class='sk-bell'>{icons.icon('bell', 16)}</span>")

    subtitle_html = f"<p class='sk-page-sub'>{esc(subtitle)}</p>" if subtitle else ""

    st.markdown(
        f"""
        <div class="sk-topbar">
          <div>
            <p class="sk-eyebrow">{esc(eyebrow)}</p>
            <h1 class="sk-page-title">{esc(title)}</h1>
            {subtitle_html}
          </div>
          <div class="sk-topbar-right">{''.join(right_parts)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def greeting_header(name: str) -> None:
    """
    Renders the dashboard greeting block.

    Args:
        name (str): Person to greet.
    """
    hour = datetime.now().hour
    if hour < 12:
        part = "Good morning"
    elif hour < 17:
        part = "Good afternoon"
    else:
        part = "Good evening"

    st.markdown(
        f"""
        <div class="sk-topbar">
          <div>
            <h1 class="sk-greeting">{esc(part)}, {esc(name)}</h1>
            <p class="sk-eyebrow">Turn meetings into action</p>
          </div>
          <div class="sk-topbar-right">
            <span class="sk-date">{esc(datetime.now().strftime('%A, %d %B %Y'))}</span>
            <span class="sk-bell">{icons.icon('bell', 16)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, action_label: Optional[str] = None, action_key: Optional[str] = None) -> bool:
    """
    Renders a section title with an optional quiet text action on the right.

    Args:
        title (str): Serif section title.
        action_label (Optional[str]): Label for the right-hand action.
        action_key (Optional[str]): Streamlit key for the action button.

    Returns:
        bool: True when the action was clicked this run.
    """
    if not action_label:
        st.markdown(f"<p class='sk-section-title'>{esc(title)}</p>", unsafe_allow_html=True)
        return False

    left, right = st.columns([6, 1.5], vertical_alignment="center")
    with left:
        st.markdown(f"<p class='sk-section-title'>{esc(title)}</p>", unsafe_allow_html=True)
    with right:
        return st.button(action_label, key=action_key or f"link_{title}", use_container_width=True)


def hero_background_css() -> str:
    """
    Returns the one-off style that paints the hero motif onto the hero container.

    Returns:
        str: A <style> block.
    """
    return (
        "<style>"
        f'[class*="st-key-herowrap"] {{ background-image: url("{icons.hero_art_uri(MOSS)}"); }}'
        "</style>"
    )


def hero_copy() -> None:
    """
    Renders the hero's text block. Call inside the `herowrap` container so the
    hero's action buttons sit within the same card.
    """
    st.markdown(
        """
        <div class="sk-hero-copy">
          <p class="sk-eyebrow">Welcome to SynkAI</p>
          <h2>Upload. Understand.<br/>Take Action.</h2>
          <p>Summaries, insights, action items and more —<br/>all from your meetings, powered by AI.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon_name: str, title: str, body: str, key: str) -> bool:
    """
    Renders one feature card. The entire card is the click target: the card markup and an
    invisible full-size button share a keyed container, so nothing floats outside the card.

    Args:
        icon_name (str): Icon key for the circular badge.
        title (str): Serif card title.
        body (str): Muted description (line breaks preserved).
        key (str): Streamlit key suffix.

    Returns:
        bool: True when the card was clicked this run.
    """
    body_html = esc(body).replace("\n", "<br/>")
    with st.container(key=f"cardwrap_{key}"):
        st.markdown(
            f"""
            <div class="sk-card">
              <div class="sk-icon-circle">{icons.icon(icon_name, 18)}</div>
              <p class="sk-card-title">{esc(title)}</p>
              <p class="sk-card-body">{body_html}</p>
              <span class="sk-card-arrow">→</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return st.button(title, key=f"cardbtn_{key}", use_container_width=True)


def stat_card(icon_name: str, value: object, label: str) -> None:
    """
    Renders a single quick-stat card.

    Args:
        icon_name (str): Icon key shown top-right.
        value (object): Large serif figure.
        label (str): Small uppercase label.
    """
    st.markdown(
        f"""
        <div class="sk-stat">
          <div class="sk-stat-top">{icons.icon(icon_name, 17)}</div>
          <p class="sk-stat-value">{esc(value)}</p>
          <p class="sk-stat-label">{esc(label)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_class(status: str) -> str:
    """
    Maps a meeting status to its badge style.

    Args:
        status (str): Status text, e.g. "Analysed".

    Returns:
        str: CSS class list for the badge.
    """
    normalised = (status or "").strip().lower()
    if normalised == "analysed":
        return "sk-badge sk-badge-ink"
    if normalised == "summarised":
        return "sk-badge sk-badge-moss"
    return "sk-badge"


def meeting_row_html(title: str, meta: str, status: str, icon_name: str = "document") -> str:
    """
    Builds the markup for one horizontal meeting row: icon, name, date/time, status badge.

    Args:
        title (str): Meeting name.
        meta (str): "Date · Time" metadata line.
        status (str): Status label for the badge.
        icon_name (str): Icon key for the leading square.

    Returns:
        str: Row markup.
    """
    return (
        '<div class="sk-row">'
        f'<div class="sk-row-icon">{icons.icon(icon_name, 17)}</div>'
        '<div class="sk-row-main">'
        f'<p class="sk-row-title">{esc(title)}</p>'
        f'<p class="sk-row-meta">{esc(meta)}</p>'
        '</div>'
        f'<span class="{badge_class(status)}">{esc(status)}</span>'
        '</div>'
    )


def meeting_list(rows: Sequence[str]) -> None:
    """
    Renders meeting rows inside a single panel.

    Streamlit wraps each `st.markdown` call in its own element, so a panel must be emitted
    as one complete string — otherwise the container closes early and renders empty.

    Args:
        rows (Sequence[str]): Markup from `meeting_row_html`.
    """
    st.markdown(
        f"<div class='sk-panel' style='padding:1.15rem 1.7rem'>{''.join(rows)}</div>",
        unsafe_allow_html=True,
    )


def meeting_card(title: str, meta: str, status: str, icon_name: str = "document") -> None:
    """
    Renders a single meeting as a standalone card (used where each row needs its own action).

    Args:
        title (str): Meeting name.
        meta (str): "Date · Time" metadata line.
        status (str): Status label for the badge.
        icon_name (str): Icon key for the leading square.
    """
    st.markdown(
        f"<div class='sk-row-card'>{meeting_row_html(title, meta, status, icon_name)}</div>",
        unsafe_allow_html=True,
    )


def panel(title: str, body_html: str, icon_name: Optional[str] = None, count: Optional[object] = None) -> None:
    """
    Renders a complete panel in one call.

    Args:
        title (str): Serif panel heading.
        body_html (str): Pre-escaped inner markup.
        icon_name (Optional[str]): Icon key rendered before the heading.
        count (Optional[object]): Small uppercase counter beside the heading.
    """
    icon_html = (
        f"<span class='sk-icon-circle' style='margin:0;width:32px;height:32px'>"
        f"{icons.icon(icon_name, 16)}</span>"
        if icon_name else ""
    )
    count_html = f"<span class='sk-panel-count'>{esc(count)}</span>" if count is not None else ""
    st.markdown(
        f"""
        <div class="sk-panel">
          <div class="sk-panel-head">{icon_html}<h3>{esc(title)}</h3>{count_html}</div>
          {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def prose(text: str) -> str:
    """
    Wraps narrative text in the editorial prose style.

    Args:
        text (str): Plain text.

    Returns:
        str: Escaped paragraph markup.
    """
    return f"<p class='sk-prose'>{esc(text)}</p>"


def numbered_list(items: Iterable[str]) -> str:
    """
    Builds a serif-numbered editorial list.

    Args:
        items (Iterable[str]): Plain text entries.

    Returns:
        str: List markup.
    """
    rows = "".join(
        f"<li><span class='sk-list-index'>{index:02d}</span><span>{esc(item)}</span></li>"
        for index, item in enumerate(items, 1)
    )
    return f"<ul class='sk-list'>{rows}</ul>"


def detail_list(entries: Sequence[dict]) -> str:
    """
    Builds a list where each row has a primary line plus muted key/value metadata.

    Args:
        entries (Sequence[dict]): Items shaped
            `{"primary": str, "meta": [(label, value), ...]}`.

    Returns:
        str: List markup.
    """
    rows = []
    for index, entry in enumerate(entries, 1):
        meta_bits = [
            f"<span style='margin-right:1.1rem'>"
            f"<span style='letter-spacing:.1em;text-transform:uppercase;font-size:.66rem;"
            f"color:#8C857A'>{esc(label)}</span>&nbsp;&nbsp;{esc(value)}</span>"
            for label, value in entry.get("meta", [])
            if value
        ]
        meta_html = (
            f"<div style='margin-top:.4rem;font-size:.78rem;color:#5C5A55'>{''.join(meta_bits)}</div>"
            if meta_bits else ""
        )
        rows.append(
            f"<li><span class='sk-list-index'>{index:02d}</span>"
            f"<span><span style='color:#2E2E2C'>{esc(entry.get('primary'))}</span>{meta_html}</span></li>"
        )
    return f"<ul class='sk-list'>{''.join(rows)}</ul>"


def empty_state(title: str, message: str) -> None:
    """
    Renders a calm placeholder for sections without data yet.

    Args:
        title (str): Serif placeholder heading.
        message (str): Muted explanation.
    """
    st.markdown(
        f"""
        <div class="sk-quiet-panel">
          <p class="sk-quiet-title">{esc(title)}</p>
          <p>{esc(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def brand_quote(text: str = "Clarity today, progress tomorrow.") -> None:
    """
    Renders the subtle editorial brand mark used at the bottom of pages.

    Args:
        text (str): Quote text.
    """
    st.markdown(
        f"""
        <div class="sk-quote">
          <p class="sk-quote-text">“{esc(text)}”</p>
          <p class="sk-quote-mark">— SynkAI —</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chat_context(label: str, active: bool = True) -> None:
    """
    Renders the small indicator showing which meeting the chat is scoped to.

    Args:
        label (str): Meeting name or guidance text.
        active (bool): Whether a meeting is currently indexed.
    """
    dot_colour = MOSS if active else "#D8D2C8"
    st.markdown(
        f"""
        <span class="sk-chat-context">
          <span class="sk-chat-dot" style="background:{dot_colour}"></span>
          {esc(label)}
        </span>
        """,
        unsafe_allow_html=True,
    )


def user_message(text: str) -> None:
    """Renders a user chat message."""
    st.markdown(f"<div class='sk-msg-user'>{esc(text)}</div>", unsafe_allow_html=True)


def ai_message(answer: str, sources: Optional[List[dict]] = None) -> None:
    """
    Renders an assistant chat message with its source citations.

    Args:
        answer (str): Generated answer text.
        sources (Optional[List[dict]]): Citation dicts with `filename` / `chunk_number`.
    """
    cites = "".join(
        f"<span class='sk-cite'>{esc(source.get('filename', 'transcript'))} · chunk "
        f"{esc(source.get('chunk_number', '-'))}</span>"
        for source in (sources or [])
    )
    cite_block = (
        f"<div style='margin-top:.35rem'>"
        f"<p class='sk-msg-label' style='margin:.9rem 0 .1rem 0'>Sources</p>{cites}</div>"
        if cites else ""
    )
    st.markdown(
        f"""
        <div class="sk-msg-ai">
          <p class="sk-msg-label">SynkAI</p>
          <p class="sk-answer">{esc(answer)}</p>
          {cite_block}
        </div>
        """,
        unsafe_allow_html=True,
    )
