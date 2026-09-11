"""
Line-art icon set for SynkAI.

Hand-picked minimal strokes (1.4px, round caps) so the icons read as quiet editorial
marks rather than colourful glyphs. `icon()` returns inline SVG for use inside custom HTML;
MATERIAL holds the Material Symbols names used by native Streamlit controls.
"""

from typing import Dict

# Paths are drawn on a 24x24 grid.
_PATHS: Dict[str, str] = {
    "summarize": (
        '<path d="M7 4h7.5L18 7.5V20H7z"/><path d="M14 4v4h4"/>'
        '<path d="M9.7 12h5.6M9.7 15.4h5.6M9.7 8.6h2.4"/>'
    ),
    "chat": (
        '<path d="M4.5 6.2h15v9.1h-9l-4.2 3.2a.4.4 0 0 1-.6-.3v-2.9h-1.2z"/>'
        '<path d="M9 10.3h6M9 12.9h3.6"/>'
    ),
    "analysis": (
        '<path d="M4.8 19.2h14.4"/><path d="M7.4 19.2V12"/><path d="M12 19.2V6.4"/>'
        '<path d="M16.6 19.2v-4.6"/>'
    ),
    "history": (
        '<path d="M12 6.6v5.6l3.6 2.1"/>'
        '<path d="M20 12a8 8 0 1 1-3.1-6.3"/><path d="M20.2 4.6v3.2h-3.2"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="2.6"/>'
        '<path d="M12 4.2v1.9M12 17.9v1.9M4.2 12h1.9M17.9 12h1.9'
        'M6.5 6.5l1.35 1.35M16.15 16.15L17.5 17.5M17.5 6.5l-1.35 1.35M7.85 16.15L6.5 17.5"/>'
    ),
    "home": (
        '<path d="M4.6 10.8 12 5l7.4 5.8V19a.8.8 0 0 1-.8.8h-3.9v-5.3H9.3v5.3H5.4a.8.8 0 0 1-.8-.8z"/>'
    ),
    "upload": (
        '<path d="M12 15.6V5.4"/><path d="M8.4 8.8 12 5.2l3.6 3.6"/>'
        '<path d="M5 15.2v2.6a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.6"/>'
    ),
    "bell": (
        '<path d="M12 5.4a4.2 4.2 0 0 0-4.2 4.2v3.1l-1.4 2.3h11.2l-1.4-2.3V9.6A4.2 4.2 0 0 0 12 5.4z"/>'
        '<path d="M10.5 17.4a1.6 1.6 0 0 0 3 0"/>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="6"/><path d="M15.6 15.6 20 20"/>'
    ),
    "document": (
        '<path d="M7 4h7.5L18 7.5V20H7z"/><path d="M14 4v4h4"/><path d="M9.7 12h5.6M9.7 15.4h3.9"/>'
    ),
    "check": (
        '<path d="M5.5 12.4l4 4L18.5 7.6"/>'
    ),
    "gavel": (
        '<path d="M5 19h8"/><path d="M7.6 15.4 13 10"/>'
        '<path d="M11.2 6.4l4.4 4.4"/><path d="M14 3.6l6.4 6.4-2.1 2.1L11.9 5.7z"/>'
    ),
    "calendar": (
        '<rect x="4.6" y="6.2" width="14.8" height="13.2" rx="1"/>'
        '<path d="M4.6 10.4h14.8M9 4.6v3.2M15 4.6v3.2"/>'
    ),
    "risk": (
        '<path d="M12 5.2 20 18.8H4z"/><path d="M12 10v3.6M12 16.1v.1"/>'
    ),
    "sparkle": (
        '<path d="M12 4.8l1.5 4.2 4.2 1.5-4.2 1.5L12 16.2l-1.5-4.2L6.3 10.5l4.2-1.5z"/>'
        '<path d="M18.2 15.4l.7 1.9 1.9.7-1.9.7-.7 1.9-.7-1.9-1.9-.7 1.9-.7z"/>'
    ),
    "user": (
        '<circle cx="12" cy="9.2" r="3.4"/><path d="M5.6 19.4a6.4 6.4 0 0 1 12.8 0"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="7.4"/><path d="M12 7.6V12l3.2 1.9"/>'
    ),
    "layers": (
        '<path d="M12 4.6 4.8 8.4 12 12.2l7.2-3.8z"/><path d="M4.8 12.6 12 16.4l7.2-3.8"/>'
        '<path d="M4.8 16.4 12 20.2l7.2-3.8"/>'
    ),
}

# Material Symbols names for native Streamlit controls (buttons support `icon=`).
MATERIAL: Dict[str, str] = {
    "home": ":material/cottage:",
    "upload": ":material/file_upload:",
    "chat": ":material/forum:",
    "analysis": ":material/insights:",
    "history": ":material/history:",
    "settings": ":material/tune:",
}


def icon(name: str, size: int = 18, stroke: str = "currentColor", width: float = 1.4) -> str:
    """
    Returns an inline SVG string for the named icon.

    Args:
        name (str): Key from the icon set.
        size (int): Rendered square size in pixels.
        stroke (str): Stroke colour (defaults to inherited text colour).
        width (float): Stroke width.

    Returns:
        str: Inline `<svg>` markup, or an empty string for an unknown name.
    """
    path = _PATHS.get(name)
    if not path:
        return ""

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{path}</svg>'
    )


def data_uri(svg: str) -> str:
    """
    Encodes inline SVG for use in a CSS `url()`.

    Args:
        svg (str): SVG markup.

    Returns:
        str: `data:` URI safe for a stylesheet.
    """
    from urllib.parse import quote
    return f"data:image/svg+xml,{quote(svg)}"


def search_glyph(color: str = "#8C857A") -> str:
    """
    Returns the magnifier used as the search field's background glyph.

    Args:
        color (str): Stroke colour.

    Returns:
        str: `data:` URI for CSS.
    """
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round">'
        '<circle cx="11" cy="11" r="6"/><path d="M15.6 15.6 20 20"/></svg>'
    )
    return data_uri(svg)


def hero_art(color: str = "#B8AFA6") -> str:
    """
    Returns the editorial line-art motif used on the right of the hero card:
    concentric arcs suggesting a soundwave resolving into order.

    Args:
        color (str): Stroke colour for the motif.

    Returns:
        str: Inline `<svg>` markup.
    """
    arcs = "".join(
        f'<circle cx="150" cy="150" r="{radius}" fill="none" stroke="{color}" '
        f'stroke-width="{1.1 if index % 2 == 0 else 0.7}" opacity="{0.55 - index * 0.06}"/>'
        for index, radius in enumerate((44, 66, 88, 110, 132))
    )
    bars = "".join(
        f'<rect x="{138 + i * 6}" y="{150 - h / 2}" width="1.6" height="{h}" rx="0.8" '
        f'fill="{color}" opacity="0.75"/>'
        for i, h in enumerate((18, 34, 52, 30, 14))
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" '
        'viewBox="0 0 300 300" aria-hidden="true">'
        f'{arcs}{bars}'
        '</svg>'
    )


def hero_art_uri(color: str = "#B8AFA6") -> str:
    """
    Returns the hero motif as a CSS-ready `data:` URI.

    Args:
        color (str): Stroke colour for the motif.

    Returns:
        str: `data:` URI for CSS.
    """
    return data_uri(hero_art(color))
