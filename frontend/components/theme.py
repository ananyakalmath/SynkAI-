"""
SynkAI design system.

Holds the colour tokens, type scale and the global stylesheet that turns Streamlit's
default chrome into a calm, light, editorial SaaS surface:

    charcoal sidebar + warm ivory workspace + serif headings + clean sans body.
"""

import streamlit as st

# --- Colour tokens -----------------------------------------------------------------
INK = "#4A4A4A"            # INKCLOUD - sidebar, primary buttons
INK_DEEP = "#3E3E3D"       # Deeper charcoal for hovers inside the sidebar
MOSS = "#B8AFA6"           # MOSSMILK - accents, dividers, quiet marks
CANVAS = "#FAF8F5"         # Main background: warm ivory
CARD = "#FFFDFA"           # Cards: soft warm white
SURFACE = "#F3EFE9"        # Secondary surfaces: very light beige
SURFACE_DEEP = "#EFE9E0"   # Hero / emphasis beige
BORDER = "#E8E2D9"         # Subtle warm grey border
BORDER_STRONG = "#DCD4C8"  # Slightly stronger hairline
TEXT = "#2E2E2C"           # Dark charcoal
TEXT_SOFT = "#5C5A55"      # Body copy
TEXT_MUTED = "#8C857A"     # Muted warm grey
SIDEBAR_TEXT = "#EDE9E3"
SIDEBAR_MUTED = "#B8AFA6"

SERIF = "'Cormorant Garamond', 'Iowan Old Style', Garamond, Georgia, serif"
SANS = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

RADIUS = "6px"
SHADOW = "0 1px 2px rgba(74, 74, 74, 0.03), 0 10px 30px -18px rgba(74, 74, 74, 0.16)"
SHADOW_HOVER = "0 1px 2px rgba(74, 74, 74, 0.04), 0 16px 38px -20px rgba(74, 74, 74, 0.22)"


def _stylesheet() -> str:
    """
    Builds the global stylesheet.

    Returns:
        str: A <style> block covering layout, typography, native widget restyling
            and the removal of unnecessary Streamlit chrome.
    """
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,200..400,0,0&display=block');

/* Material Symbols used by native Streamlit controls: render as glyphs, never as
   the raw ligature text ("cottage", "tune", ...) if the bundled font is unavailable. */
[data-testid="stIconMaterial"], span.material-symbols-rounded {{
    font-family: 'Material Symbols Rounded' !important;
    font-weight: 300 !important;
    font-style: normal;
    font-size: 19px !important;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    direction: ltr;
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
    flex: 0 0 auto;
}}

/* ---------- Canvas ---------- */
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {CANVAS};
}}
[data-testid="stMainBlockContainer"], [data-testid="stMain"] .block-container {{
    max-width: 1180px;
    padding: 2.75rem 3.25rem 5.5rem 3.25rem !important;
}}
html, body, [class*="st-"], button, input, textarea, select {{
    font-family: {SANS};
    color: {TEXT};
}}
body {{
    -webkit-font-smoothing: antialiased;
}}

/* ---------- Remove unnecessary Streamlit chrome ---------- */
[data-testid="stHeader"] {{
    background: transparent;
    height: 0;
}}
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], #MainMenu, footer {{
    display: none !important;
}}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button {{
    color: {SIDEBAR_MUTED} !important;
}}
[data-testid="stSidebarCollapsedControl"] button {{
    color: {TEXT_MUTED} !important;
}}
[data-testid="stElementToolbar"] {{ display: none; }}

/* ---------- Typography ---------- */
h1, h2, h3, h4 {{
    font-family: {SERIF};
    color: {TEXT};
    font-weight: 500;
    letter-spacing: -0.01em;
}}
/* Streamlit ships its own heading rules, so the serif treatment is pinned. */
[data-testid="stMainBlockContainer"] h1.sk-greeting,
[data-testid="stMainBlockContainer"] h1.sk-page-title,
[data-testid="stMainBlockContainer"] .sk-hero-copy h2,
[data-testid="stMainBlockContainer"] .sk-panel-head h3 {{
    font-family: {SERIF} !important;
    font-weight: 400 !important;
    padding: 0 !important;
}}
[data-testid="stMainBlockContainer"] h1, [data-testid="stMainBlockContainer"] h2, [data-testid="stMainBlockContainer"] h3 {{
    padding: 0;
}}
/* Body defaults apply only to unclassed paragraphs, so the design-system classes
   below are not outranked by this attribute-scoped rule. */
[data-testid="stMainBlockContainer"] p:not([class]), [data-testid="stMainBlockContainer"] li:not([class]) {{
    color: {TEXT_SOFT};
    font-size: 0.9rem;
    line-height: 1.65;
}}

.sk-eyebrow {{
    font-family: {SANS};
    font-size: 0.66rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin: 0;
}}
.sk-greeting {{
    font-family: {SERIF};
    font-size: 2.35rem;
    line-height: 1.1;
    font-weight: 400;
    color: {TEXT};
    margin: 0.35rem 0 0.5rem 0;
}}
.sk-page-title {{
    font-family: {SERIF};
    font-size: 2.1rem;
    line-height: 1.15;
    font-weight: 400;
    color: {TEXT};
    margin: 0.3rem 0 0.4rem 0;
}}
.sk-page-sub {{
    font-family: {SANS};
    font-size: 0.9rem;
    color: {TEXT_MUTED};
    margin: 0;
    max-width: 62ch;
    line-height: 1.6;
}}
.sk-section-title {{
    font-family: {SERIF};
    font-size: 1.4rem;
    font-weight: 500;
    color: {TEXT};
    margin: 0;
}}
.sk-meta {{
    font-family: {SANS};
    font-size: 0.78rem;
    color: {TEXT_MUTED};
    margin: 0;
}}

/* ---------- Page header row ---------- */
.sk-topbar {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 2rem;
}}
.sk-topbar-right {{
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding-top: 0.9rem;
    white-space: nowrap;
}}
.sk-date {{
    font-size: 0.78rem;
    color: {TEXT_MUTED};
    letter-spacing: 0.02em;
}}
.sk-bell {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border: 1px solid {BORDER};
    border-radius: 50%;
    background: {CARD};
    color: {INK};
    position: relative;
}}
.sk-bell::after {{
    content: '';
    position: absolute;
    top: 8px;
    right: 9px;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: {MOSS};
}}
.sk-rule {{
    height: 1px;
    background: {BORDER};
    border: 0;
    margin: 2.1rem 0 1.9rem 0;
}}

/* ---------- Hero ----------
   Rendered as a keyed Streamlit container so the real buttons live inside the card. */
[class*="st-key-herowrap"] {{
    position: relative;
    overflow: hidden;
    background: {SURFACE_DEEP};
    border: 1px solid {BORDER_STRONG};
    border-radius: {RADIUS};
    padding: 3rem 3.2rem 2.6rem 3.2rem;
    background-repeat: no-repeat;
    background-position: right -38px center;
}}
[class*="st-key-herowrap"] [data-testid="stHorizontalBlock"] {{
    position: relative;
    z-index: 2;
}}
[class*="st-key-herowrap"] [data-testid="stMarkdown"] {{
    position: relative;
    z-index: 2;
}}
.sk-hero-copy {{
    position: relative;
    z-index: 2;
    max-width: 33rem;
}}
.sk-hero-copy h2 {{
    font-size: 2.7rem;
    line-height: 1.12;
    color: {TEXT};
    margin: 0.8rem 0 1rem 0;
}}
.sk-hero-copy p {{
    font-size: 0.92rem;
    color: {TEXT_SOFT};
    line-height: 1.7;
    margin: 0;
    max-width: 30rem;
}}
/* Legacy static hero (kept for reuse elsewhere) */
.sk-hero {{
    position: relative;
    overflow: hidden;
    background: {SURFACE_DEEP};
    border: 1px solid {BORDER_STRONG};
    border-radius: {RADIUS};
    padding: 3.1rem 3.2rem;
    min-height: 268px;
    display: flex;
    align-items: center;
}}
.sk-hero h2 {{
    font-family: {SERIF};
    font-size: 2.75rem;
    line-height: 1.12;
    font-weight: 400;
    color: {TEXT};
    margin: 0.75rem 0 1rem 0;
}}
.sk-hero p {{
    font-size: 0.92rem;
    color: {TEXT_SOFT};
    line-height: 1.7;
    margin: 0;
    max-width: 30rem;
}}
.sk-hero-art {{
    position: absolute;
    right: -40px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1;
    opacity: 0.55;
    pointer-events: none;
}}

/* ---------- Cards ---------- */
.sk-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: {SHADOW};
    padding: 1.6rem 1.5rem 1.4rem 1.5rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: box-shadow 180ms ease, border-color 180ms ease, transform 180ms ease;
}}
.sk-card .sk-card-body {{ flex: 1 1 auto; }}
.sk-card .sk-card-arrow {{ margin-top: auto; }}

/* One shared height per card row, so every card bottom and arrow lines up.
   Scoped to the keyed rows that hold cards, to leave other layouts untouched. */
[class*="st-key-cardrow"] [data-testid="stHorizontalBlock"],
[class*="st-key-statrow"] [data-testid="stHorizontalBlock"] {{
    align-items: stretch;
}}
[class*="st-key-cardrow"] [data-testid="stColumn"],
[class*="st-key-statrow"] [data-testid="stColumn"] {{
    display: flex;
    flex-direction: column;
}}
/* Streamlit nests several unnamed wrappers between the column and the card, and each
   one defaults to `flex: 0 1 auto`, which stops the height from reaching the card. */
[class*="st-key-cardrow"] [data-testid="stColumn"] > div,
[class*="st-key-cardrow"] [data-testid="stColumn"] > div > div,
[class*="st-key-cardrow"] [data-testid="stColumn"] [data-testid="stElementContainer"],
[class*="st-key-cardrow"] [class*="st-key-cardwrap_"],
[class*="st-key-cardrow"] [data-testid="stMarkdown"],
[class*="st-key-cardrow"] [data-testid="stMarkdownContainer"],
[class*="st-key-statrow"] [data-testid="stColumn"] > div,
[class*="st-key-statrow"] [data-testid="stColumn"] > div > div,
[class*="st-key-statrow"] [data-testid="stColumn"] [data-testid="stElementContainer"],
[class*="st-key-statrow"] [data-testid="stMarkdown"],
[class*="st-key-statrow"] [data-testid="stMarkdownContainer"] {{
    flex: 1 1 auto !important;
    height: 100% !important;
    align-self: stretch;
}}
[class*="st-key-cardwrap_"] {{
    min-height: 232px;
    align-items: stretch;
}}
/* The overlay button must not be stretched by the rules above. */
[class*="st-key-cardrow"] [class*="st-key-cardbtn_"] {{
    flex: none !important;
    height: 100% !important;
}}

/* Feature cards: the whole card is the click target, via an invisible overlay button.
   Streamlit nests the <button> several divs deep, so every wrapper is stretched. */
[class*="st-key-cardwrap_"] {{ position: relative; }}
[class*="st-key-cardbtn_"] {{
    position: absolute;
    inset: 0;
    margin: 0;
    padding: 0;
    z-index: 3;
}}
[class*="st-key-cardbtn_"],
[class*="st-key-cardbtn_"] div,
[class*="st-key-cardbtn_"] .stButton,
[class*="st-key-cardbtn_"] button {{
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
}}
[class*="st-key-cardbtn_"] button {{
    opacity: 0;
    background: transparent !important;
    border: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    transform: none !important;
    cursor: pointer;
}}
[class*="st-key-cardwrap_"]:hover .sk-card {{
    box-shadow: {SHADOW_HOVER};
    border-color: {BORDER_STRONG};
    transform: translateY(-2px);
}}
[class*="st-key-cardwrap_"]:hover .sk-card-arrow {{ transform: translateX(3px); }}
.sk-card-arrow {{ transition: transform 180ms ease; }}
.sk-icon-circle {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: {SURFACE};
    border: 1px solid {BORDER};
    display: flex;
    align-items: center;
    justify-content: center;
    color: {INK};
    margin-bottom: 1.15rem;
}}
.sk-card-title {{
    font-family: {SERIF};
    font-size: 1.2rem;
    font-weight: 500;
    color: {TEXT};
    margin: 0 0 0.45rem 0;
}}
.sk-card-body {{
    font-size: 0.83rem;
    line-height: 1.6;
    color: {TEXT_MUTED};
    margin: 0 0 1.35rem 0;
}}
.sk-card-arrow {{
    color: {INK};
    font-size: 0.95rem;
    letter-spacing: 0.04em;
}}

/* ---------- Panels (analysis / summary sections) ---------- */
.sk-panel {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: {SHADOW};
    padding: 1.85rem 1.9rem;
    margin-bottom: 1.1rem;
}}
.sk-panel-head {{
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin-bottom: 1.15rem;
}}
.sk-panel-head h3 {{
    font-family: {SERIF};
    font-size: 1.28rem;
    font-weight: 500;
    margin: 0;
    color: {TEXT};
}}
.sk-panel-count {{
    font-family: {SANS};
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-radius: 2px;
    padding: 0.2rem 0.5rem;
    background: {SURFACE};
}}
.sk-prose {{
    font-size: 0.93rem;
    line-height: 1.78;
    color: {TEXT_SOFT};
    margin: 0;
}}
.sk-quiet-panel {{
    background: {SURFACE};
    border: 1px dashed {BORDER_STRONG};
    border-radius: {RADIUS};
    padding: 2.4rem 2rem;
    text-align: center;
}}
.sk-quiet-panel p, .sk-quiet-panel .sk-quiet-title {{
    text-align: center;
}}
.sk-quiet-panel .sk-quiet-title {{
    font-family: {SERIF};
    font-size: 1.25rem;
    color: {TEXT};
    margin: 0 0 0.4rem 0;
}}
.sk-quiet-panel p {{
    font-size: 0.85rem;
    color: {TEXT_MUTED};
    margin: 0 auto;
    max-width: 44ch;
}}

/* ---------- Numbered / bulleted editorial lists ---------- */
.sk-list {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.sk-list li {{
    display: flex;
    gap: 0.95rem;
    padding: 0.85rem 0;
    border-top: 1px solid {BORDER};
    font-size: 0.9rem;
    line-height: 1.65;
    color: {TEXT_SOFT};
}}
.sk-list li:first-child {{
    border-top: 0;
    padding-top: 0;
}}
.sk-list li:last-child {{
    padding-bottom: 0;
}}
.sk-list-index {{
    font-family: {SERIF};
    font-size: 1rem;
    color: {MOSS};
    min-width: 1.4rem;
    line-height: 1.55;
}}

/* ---------- Meeting rows ---------- */
.sk-row {{
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding: 1.05rem 0.25rem;
    border-top: 1px solid {BORDER};
}}
.sk-row:first-of-type {{ border-top: 0; }}
.sk-row-icon {{
    width: 36px;
    height: 36px;
    border-radius: {RADIUS};
    background: {SURFACE};
    border: 1px solid {BORDER};
    display: flex;
    align-items: center;
    justify-content: center;
    color: {INK};
    flex: 0 0 auto;
}}
.sk-row-main {{ flex: 1 1 auto; min-width: 0; }}
.sk-row-title {{
    font-size: 0.92rem;
    font-weight: 500;
    color: {TEXT};
    margin: 0 0 0.2rem 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.sk-row-meta {{
    font-size: 0.76rem;
    color: {TEXT_MUTED};
    margin: 0;
    letter-spacing: 0.01em;
}}
.sk-badge {{
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.32rem 0.66rem;
    border-radius: 2px;
    border: 1px solid {BORDER_STRONG};
    background: {SURFACE};
    color: {TEXT_SOFT};
    white-space: nowrap;
    flex: 0 0 auto;
}}
.sk-badge-ink {{
    background: {INK};
    border-color: {INK};
    color: {SIDEBAR_TEXT};
}}
.sk-badge-moss {{
    background: rgba(184, 175, 166, 0.22);
    border-color: {MOSS};
    color: #6F6558;
}}

/* ---------- Stats ---------- */
.sk-stat {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: {SHADOW};
    padding: 1.35rem 1.4rem;
    height: 100%;
    min-height: 152px;
    display: flex;
    flex-direction: column;
}}
.sk-stat .sk-stat-value {{ margin-top: auto; }}
.sk-stat-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: {MOSS};
    margin-bottom: 0.85rem;
}}
.sk-stat-value {{
    font-family: {SERIF};
    font-size: 2.1rem;
    font-weight: 400;
    line-height: 1;
    color: {TEXT};
    margin: 0 0 0.4rem 0;
}}
.sk-stat-label {{
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin: 0;
}}

/* ---------- Chat ---------- */
.sk-chat-context {{
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 999px;
    padding: 0.4rem 0.95rem;
    font-size: 0.78rem;
    color: {TEXT_SOFT};
}}
.sk-chat-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: {MOSS};
    display: inline-block;
}}
.sk-msg-user {{
    background: {INK};
    color: {SIDEBAR_TEXT};
    border-radius: {RADIUS};
    padding: 0.95rem 1.15rem;
    font-size: 0.89rem;
    line-height: 1.6;
    max-width: 78%;
    margin-left: auto;
}}
.sk-msg-ai {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: {SHADOW};
    padding: 1.3rem 1.45rem;
    max-width: 88%;
}}
.sk-msg-ai .sk-msg-label {{
    font-size: 0.64rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {MOSS};
    margin: 0 0 0.6rem 0;
}}
.sk-msg-ai p.sk-answer {{
    font-size: 0.91rem;
    line-height: 1.75;
    color: {TEXT_SOFT};
    margin: 0;
}}
.sk-cite {{
    display: inline-block;
    font-size: 0.7rem;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    background: {SURFACE};
    border-radius: 2px;
    padding: 0.22rem 0.55rem;
    margin: 0.75rem 0.4rem 0 0;
}}

/* ---------- Brand quote ---------- */
.sk-quote {{
    text-align: center;
    padding: 3.6rem 1rem 1.2rem 1rem;
}}
.sk-quote-text {{
    font-family: {SERIF};
    font-style: italic;
    font-size: 1.28rem;
    font-weight: 300;
    color: {TEXT_MUTED};
    margin: 0 0 1.1rem 0;
}}
.sk-quote-mark {{
    font-family: {SANS};
    font-size: 0.64rem;
    letter-spacing: 0.42em;
    text-transform: uppercase;
    color: {MOSS};
    margin: 0;
}}

/* ---------- Sidebar ---------- */
/* Width is pinned on every layer; Streamlit's own min-width otherwise overflows
   the section and clips the brand block. */
[data-testid="stSidebar"] {{
    background: {INK};
    border-right: 1px solid rgba(0, 0, 0, 0.08);
    width: 276px !important;
    min-width: 276px !important;
    max-width: 276px !important;
}}
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
    background: {INK};
    width: 100%;
    min-width: 0;
}}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    width: 100%;
    min-width: 0;
}}
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
    padding-bottom: 0;
}}
[data-testid="stSidebarUserContent"] {{
    padding: 2.1rem 1.35rem 1.6rem 1.35rem;
}}
[data-testid="stSidebar"] .sk-brand {{
    font-family: {SERIF};
    font-size: 1.7rem;
    font-weight: 500;
    letter-spacing: 0.01em;
    color: #FFFFFF;
    margin: 0;
}}
[data-testid="stSidebar"] .sk-brand-tag {{
    font-family: {SANS};
    font-size: 0.72rem;
    color: {SIDEBAR_MUTED};
    margin: 0.35rem 0 0 0;
    letter-spacing: 0.02em;
}}
[data-testid="stSidebar"] .sk-nav-label {{
    font-size: 0.6rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(184, 175, 166, 0.75);
    margin: 0 0 0.5rem 0.15rem;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255, 255, 255, 0.1);
    margin: 1.4rem 0;
}}

/* Sidebar navigation buttons */
[data-testid="stSidebar"] .stButton > button {{
    width: 100%;
    justify-content: flex-start;
    gap: 0.7rem;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    color: rgba(237, 233, 227, 0.82);
    font-family: {SANS};
    font-size: 0.855rem;
    font-weight: 400;
    letter-spacing: 0.01em;
    padding: 0.52rem 0.7rem;
    box-shadow: none;
    transition: background 150ms ease, color 150ms ease;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255, 255, 255, 0.07);
    color: #FFFFFF;
    border-color: transparent;
}}
[data-testid="stSidebar"] .stButton > button:focus:not(:active) {{
    color: #FFFFFF;
    border-color: transparent;
    box-shadow: none;
}}
[data-testid="stSidebar"] .stButton > button p {{
    font-size: 0.855rem;
    font-weight: 400;
}}
/* Streamlit centres button content; navigation reads better left-aligned. */
[data-testid="stSidebar"] .stButton > button > div,
[data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] {{
    width: 100%;
    justify-content: flex-start;
    text-align: left;
}}
[data-testid="stSidebar"] .stButton > button {{
    text-align: left;
}}
[data-testid="stSidebar"] .sk-nav-active > div > .stButton > button,
[data-testid="stSidebar"] .sk-nav-active .stButton > button {{
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
}}
[data-testid="stSidebar"] [class*="st-key-nav_"] button[aria-pressed="true"] {{
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
}}

/* Sidebar user block */
[data-testid="stSidebar"] .sk-user {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.9rem 0.1rem 0 0.1rem;
}}
[data-testid="stSidebar"] .sk-avatar {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: {SERIF};
    font-size: 0.95rem;
    color: #FFFFFF;
    flex: 0 0 auto;
}}
[data-testid="stSidebar"] .sk-user-name {{
    font-size: 0.85rem;
    color: #FFFFFF;
    margin: 0;
    font-weight: 500;
}}
[data-testid="stSidebar"] .sk-user-tag {{
    font-size: 0.68rem;
    color: {SIDEBAR_MUTED};
    margin: 0.1rem 0 0 0;
}}
[data-testid="stSidebar"] .sk-status {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.7rem;
    color: {SIDEBAR_MUTED};
    padding: 0.2rem 0.1rem 0 0.1rem;
}}
[data-testid="stSidebar"] .sk-status-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}}

/* ---------- Native widgets ---------- */
[data-testid="stMainBlockContainer"] .stButton > button {{
    font-family: {SANS};
    font-size: 0.83rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    border-radius: 4px;
    padding: 0.58rem 1.35rem;
    background: {INK};
    color: #FFFFFF;
    border: 1px solid {INK};
    box-shadow: none;
    transition: background 150ms ease, transform 150ms ease;
}}
[data-testid="stMainBlockContainer"] .stButton > button:hover {{
    background: {INK_DEEP};
    border-color: {INK_DEEP};
    color: #FFFFFF;
    transform: translateY(-1px);
}}
[data-testid="stMainBlockContainer"] .stButton > button:focus:not(:active) {{
    color: #FFFFFF;
    border-color: {INK_DEEP};
    box-shadow: none;
}}
/* Streamlit nests the label under a <span> that carries the default text colour, so
   every descendant of a button is pinned to the button's own colour. */
[data-testid="stMainBlockContainer"] .stButton button * {{
    color: inherit !important;
}}
[data-testid="stMainBlockContainer"] .stButton button p {{
    font-size: 0.83rem;
    font-weight: 500;
    letter-spacing: 0.03em;
}}
[data-testid="stSidebar"] .stButton button * {{
    color: inherit !important;
}}
/* Quiet / secondary buttons */
[data-testid="stMainBlockContainer"] [class*="st-key-quiet_"] button,
[data-testid="stMainBlockContainer"] [class*="st-key-card_"] button,
[data-testid="stMainBlockContainer"] [class*="st-key-link_"] button {{
    background: transparent;
    color: {INK};
    border: 1px solid transparent;
    padding: 0.35rem 0.2rem;
    font-weight: 500;
    letter-spacing: 0.06em;
}}
[data-testid="stMainBlockContainer"] [class*="st-key-quiet_"] button:hover,
[data-testid="stMainBlockContainer"] [class*="st-key-card_"] button:hover,
[data-testid="stMainBlockContainer"] [class*="st-key-link_"] button:hover {{
    background: transparent;
    color: {TEXT};
    border-color: transparent;
    transform: none;
    text-decoration: none;
}}
[data-testid="stMainBlockContainer"] [class*="st-key-outline_"] button {{
    background: {CARD};
    color: {INK};
    border: 1px solid {BORDER_STRONG};
}}
[data-testid="stMainBlockContainer"] [class*="st-key-outline_"] button:hover {{
    background: {SURFACE};
    color: {TEXT};
    border-color: {MOSS};
}}

/* Columns stretch so cards in a row share one height */
[data-testid="stMainBlockContainer"] [data-testid="stColumn"] > div,
[data-testid="stMainBlockContainer"] [data-testid="stColumn"] [data-testid="stVerticalBlock"] {{
    height: 100%;
}}

/* Search fields carry a quiet magnifier glyph */
[data-testid="stMainBlockContainer"] [class*="st-key-home_search"] input,
[data-testid="stMainBlockContainer"] [class*="st-key-history_search"] input {{
    background-image: url("{{SEARCH_GLYPH}}");
    background-repeat: no-repeat;
    background-position: 15px center;
    padding-left: 42px;
    height: 46px;
}}

/* History rows render as standalone cards next to their action */
.sk-row-card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: {SHADOW};
    padding: 0.35rem 1.25rem;
    margin-bottom: 0.7rem;
}}
.sk-row-card .sk-row {{ border-top: 0; }}

/* Inputs */
[data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input,
[data-testid="stMainBlockContainer"] [data-testid="stTextArea"] textarea,
[data-testid="stMainBlockContainer"] [data-baseweb="select"] > div {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    font-size: 0.86rem;
    color: {TEXT};
    box-shadow: none;
}}
[data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input::placeholder,
[data-testid="stMainBlockContainer"] [data-testid="stTextArea"] textarea::placeholder {{
    color: {TEXT_MUTED};
}}
[data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input:focus,
[data-testid="stMainBlockContainer"] [data-testid="stTextArea"] textarea:focus {{
    border-color: {MOSS};
    box-shadow: none;
}}
[data-testid="stMainBlockContainer"] [data-baseweb="input"],
[data-testid="stMainBlockContainer"] [data-baseweb="base-input"] {{
    background: transparent;
    border: none;
}}
[data-testid="stMainBlockContainer"] label p {{
    font-size: 0.74rem !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {TEXT_MUTED} !important;
    font-weight: 500;
}}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {{
    background: {SURFACE};
    border: 1px dashed {BORDER_STRONG};
    border-radius: {RADIUS};
    padding: 2.9rem 2rem;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {MOSS};
    background: #F6F2EC;
}}
[data-testid="stFileUploaderDropzone"] button {{
    background: {CARD} !important;
    color: {INK} !important;
    border: 1px solid {BORDER_STRONG} !important;
    border-radius: 4px !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div {{
    color: {TEXT_MUTED};
    font-size: 0.82rem;
}}
/* Streamlit advertises its own 200MB limit, which contradicts MAX_UPLOAD_SIZE_MB. */
[data-testid="stFileUploaderDropzoneInstructions"] small {{
    display: none;
}}
[data-testid="stFileUploaderDropzoneInstructions"]::after {{
    content: 'Drag a transcript here, or browse your files';
    font-size: 0.82rem;
    color: {TEXT_MUTED};
}}
[data-testid="stFileUploaderDropzoneInstructions"] svg {{
    fill: {MOSS};
}}
[data-testid="stFileUploaderFile"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 0.6rem 0.8rem;
}}

/* Chat input */
[data-testid="stChatInput"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: {SHADOW};
}}
[data-testid="stChatInput"] textarea {{
    font-size: 0.88rem;
    color: {TEXT};
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: {TEXT_MUTED};
}}
[data-testid="stChatInput"] button {{
    background: {INK} !important;
    border-radius: 4px !important;
}}
[data-testid="stChatInput"] button svg {{
    fill: #FFFFFF;
}}

/* Expander */
[data-testid="stExpander"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    box-shadow: none;
}}
[data-testid="stExpander"] summary {{
    font-size: 0.79rem;
    color: {TEXT_MUTED};
    letter-spacing: 0.04em;
}}
[data-testid="stExpander"] summary:hover {{
    color: {TEXT};
}}

/* Feedback blocks */
[data-testid="stAlert"] {{
    border-radius: {RADIUS};
    border: 1px solid {BORDER_STRONG};
    background: {SURFACE};
    box-shadow: none;
}}
[data-testid="stAlert"] p {{
    font-size: 0.85rem;
    color: {TEXT_SOFT};
}}
[data-testid="stSpinner"] p {{
    font-size: 0.82rem;
    color: {TEXT_MUTED};
}}
[data-testid="stSpinner"] svg {{
    stroke: {MOSS};
}}
[data-testid="stToast"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
}}

/* Tables / dataframes kept quiet if ever used */
[data-testid="stTable"] table, [data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    font-size: 0.84rem;
}}

/* Progress */
[data-testid="stProgress"] > div > div > div > div {{
    background: {INK};
}}

/* ---------- Specificity guard ----------
   Streamlit styles markdown paragraphs with `[data-testid="stMarkdownContainer"] p`,
   which outranks a single class. The design-system sizes are restated here with the
   main-container prefix so the type scale is never silently reset to 1rem. */
[data-testid="stMainBlockContainer"] .sk-eyebrow {{ font-size: 0.66rem; }}
[data-testid="stMainBlockContainer"] .sk-page-sub {{ font-size: 0.9rem; }}
[data-testid="stMainBlockContainer"] .sk-meta {{ font-size: 0.78rem; }}
[data-testid="stMainBlockContainer"] .sk-date {{ font-size: 0.78rem; }}
[data-testid="stMainBlockContainer"] .sk-section-title {{ font-size: 1.4rem; font-family: {SERIF}; }}
[data-testid="stMainBlockContainer"] .sk-card-title {{ font-size: 1.2rem; font-family: {SERIF}; }}
[data-testid="stMainBlockContainer"] .sk-card-body {{ font-size: 0.83rem; }}
[data-testid="stMainBlockContainer"] .sk-card-arrow {{ font-size: 0.95rem; }}
[data-testid="stMainBlockContainer"] .sk-row-title {{ font-size: 0.92rem; }}
[data-testid="stMainBlockContainer"] .sk-row-meta {{ font-size: 0.76rem; }}
[data-testid="stMainBlockContainer"] .sk-stat-value {{ font-size: 2.1rem; font-family: {SERIF}; line-height: 1; }}
[data-testid="stMainBlockContainer"] .sk-stat-label {{ font-size: 0.7rem; }}
[data-testid="stMainBlockContainer"] .sk-prose {{ font-size: 0.93rem; line-height: 1.78; }}
[data-testid="stMainBlockContainer"] .sk-quiet-title {{ font-size: 1.25rem; font-family: {SERIF}; }}
[data-testid="stMainBlockContainer"] .sk-quiet-panel p {{ font-size: 0.85rem; }}
[data-testid="stMainBlockContainer"] .sk-quote-text {{ font-size: 1.28rem; font-family: {SERIF}; }}
[data-testid="stMainBlockContainer"] .sk-quote-mark {{ font-size: 0.64rem; }}
[data-testid="stMainBlockContainer"] .sk-answer {{ font-size: 0.91rem; line-height: 1.75; }}
[data-testid="stMainBlockContainer"] .sk-msg-label {{ font-size: 0.64rem; }}
[data-testid="stMainBlockContainer"] .sk-msg-user {{ font-size: 0.89rem; }}
[data-testid="stMainBlockContainer"] .sk-list li {{ font-size: 0.9rem; }}
[data-testid="stMainBlockContainer"] .sk-list-index {{ font-size: 1rem; font-family: {SERIF}; }}
[data-testid="stMainBlockContainer"] .sk-hero-copy h2 {{ font-size: 2.7rem; }}
[data-testid="stMainBlockContainer"] .sk-greeting {{ font-size: 2.35rem; }}
[data-testid="stMainBlockContainer"] .sk-page-title {{ font-size: 2.1rem; }}
[data-testid="stMainBlockContainer"] .sk-panel-head h3 {{ font-size: 1.28rem; }}

/* ---------- Responsive ---------- */
@media (max-width: 1200px) {{
    [data-testid="stMainBlockContainer"] .block-container {{ padding: 2.25rem 2rem 4rem 2rem; }}
    .sk-hero {{ padding: 2.4rem 2.2rem; }}
    .sk-hero h2 {{ font-size: 2.25rem; }}
    .sk-hero-art {{ display: none; }}
}}
@media (max-width: 760px) {{
    .sk-greeting {{ font-size: 1.9rem; }}
    .sk-hero h2 {{ font-size: 1.85rem; }}
    .sk-topbar {{ flex-direction: column; gap: 0.9rem; }}
    .sk-topbar-right {{ padding-top: 0; }}
}}
</style>
"""


def apply_theme() -> None:
    """
    Injects the SynkAI stylesheet. Safe to call on every rerun.
    """
    from frontend.components import icons

    css = _stylesheet().replace("{SEARCH_GLYPH}", icons.search_glyph(TEXT_MUTED))
    st.markdown(css, unsafe_allow_html=True)
