"""Colour palettes and CSS for the Streamlit interface.

Streamlit paints its widgets from the theme in ``.streamlit/config.toml``, and
that file declares both ``[theme.light]`` and ``[theme.dark]``: the app starts in
the palette the viewer's operating system asks for, and the ⋮ menu can flip it.

The sidebar radio can force the *other* palette. Streamlit has no runtime theme
API, so in that case the widgets are repainted with the CSS built here, from the
same palette. When the radio agrees with Streamlit (the default, "system") only
the report table colours are injected and Streamlit keeps full control.

``string.Template.substitute`` is deliberate: a colour missing from a palette
fails loudly instead of leaking ``$name`` into the page.
"""

from __future__ import annotations

import string

import streamlit as st

LANGS = ("light", "dark")

PALETTE: dict[str, dict[str, str]] = {
    "light": {
        "scheme": "light",
        "app": "#ffffff",
        "surface": "#ffffff",
        "panel": "#f3f5f8",
        "text": "#1f2328",
        "muted": "#57606a",
        "border": "#d0d7de",
        "hover": "#eaeef4",
        "code_bg": "#f6f8fa",
        "accent": "#1f4e79",
        "link": "#0b5cad",
        "info": "#0969da",
        "warning": "#9a6700",
        "success": "#1a7f37",
        "danger": "#cf222e",
        "p1": "#b3261e",
        "p2": "#c25e00",
        "p3": "#8a6d00",
        "p4": "#57606a",
    },
    "dark": {
        "scheme": "dark",
        "app": "#0d1117",
        "surface": "#161b22",
        "panel": "#161b22",
        "text": "#e6edf3",
        "muted": "#9198a1",
        "border": "#30363d",
        "hover": "#21262d",
        "code_bg": "#161b22",
        "accent": "#4f9cf0",
        "link": "#6cb6ff",
        "info": "#4493f8",
        "warning": "#d29922",
        "success": "#3fb950",
        "danger": "#f85149",
        "p1": "#d1392f",
        "p2": "#b8730a",
        "p3": "#8a6d00",
        "p4": "#57606a",
    },
}

# Always injected: CSS variables plus the colours of the report table, which is
# the app's own HTML and therefore never themed by Streamlit.
_BASE = string.Template(
    """
:root, .stApp {
  color-scheme: $scheme;
  --kib-app: $app;
  --kib-surface: $surface;
  --kib-panel: $panel;
  --kib-text: $text;
  --kib-muted: $muted;
  --kib-border: $border;
  --kib-hover: $hover;
  --kib-code: $code_bg;
  --kib-accent: $accent;
  --kib-link: $link;
  --kib-info: $info;
  --kib-warning: $warning;
  --kib-success: $success;
  --kib-danger: $danger;
}
.kib-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.kib-table th, .kib-table td {
    border: 1px solid var(--kib-border);
    padding: 8px 10px; text-align: left; vertical-align: top;
}
.kib-table th { background-color: var(--kib-panel); color: var(--kib-text); font-weight: 600; }
.kib-table td { background-color: var(--kib-app); color: var(--kib-text); }
.stApp .kib-badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-weight: 600; font-size: 0.8rem; color: #ffffff !important;
}
.stApp .kib-badge.p1 { background-color: $p1; }
.stApp .kib-badge.p2 { background-color: $p2; }
.stApp .kib-badge.p3 { background-color: $p3; }
.stApp .kib-badge.p4 { background-color: $p4; }
/* The Deploy button belongs to the Streamlit toolbar, not to the report. */
[data-testid="stAppDeployButton"] { display: none !important; }
"""
)

# Injected only when the radio overrides Streamlit's own theme. Every selector
# below is a stable `data-testid` hook, not an emotion hash.
_FORCE = string.Template(
    """
/* ---------- surfaces ---------- */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] { background-color: var(--kib-app) !important; }
header[data-testid="stHeader"] { background-color: var(--kib-app) !important; }
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stLogoSpacer"] { background-color: transparent !important; }
section[data-testid="stSidebar"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] { background-color: var(--kib-panel) !important; }
[data-testid="stSidebarResizeHandle"] { background-color: var(--kib-border) !important; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background-color: var(--kib-app); }
::-webkit-scrollbar-thumb { background-color: var(--kib-border); border-radius: 5px; }

/* ---------- text ---------- */
.stApp { color: var(--kib-text) !important; }
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] ol,
[data-testid="stMarkdownContainer"] ul,
[data-testid="stHeading"] p,
[data-testid="stHeading"] span,
[data-testid="stWidgetLabel"] p { color: var(--kib-text) !important; }
[data-testid="stCaptionContainer"] p,
[data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--kib-muted) !important; }
.stApp a, [data-testid="stMarkdownContainer"] a { color: var(--kib-link) !important; }
hr { border-color: var(--kib-border) !important; }

/* ---------- element toolbar (copy button above code) ---------- */
[data-testid="stElementToolbar"],
[data-testid="stElementToolbarButton"],
div:has(> [data-testid="stElementToolbarButton"]) {
    background-color: var(--kib-surface) !important;
    color: var(--kib-text) !important;
}
[data-testid="stElementToolbarButton"] * { background-color: transparent !important; }
[data-testid="stElementToolbarButton"] svg { fill: var(--kib-text) !important; }

/* ---------- toolbar icons ---------- */
[data-testid="stMainMenuButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stMainMenuButton"] svg,
[data-testid="stSidebarCollapseButton"] svg { color: var(--kib-text) !important; fill: var(--kib-text) !important; }

/* ---------- selectbox ---------- */
[data-testid="stSelectbox"] div[role="group"] {
    background-color: var(--kib-surface) !important;
    border: 1px solid var(--kib-border) !important;
    border-radius: 8px;
}
[data-testid="stSelectbox"] input {
    background-color: transparent !important; color: var(--kib-text) !important;
}
[data-testid="stSelectbox"] input::placeholder { color: var(--kib-muted) !important; }
[data-testid="stSelectbox"] button { background-color: transparent !important; color: var(--kib-muted) !important; }
[data-testid="stSelectbox"] svg { fill: var(--kib-muted) !important; }
[data-testid="stSelectboxVirtualDropdown"] {
    background-color: var(--kib-surface) !important;
    border: 1px solid var(--kib-border) !important;
    border-radius: 8px;
}
[data-testid="stSelectboxVirtualDropdown"] [role="option"] { color: var(--kib-text) !important; }
[data-testid="stSelectboxVirtualDropdown"] [data-item-hl] { background-color: transparent !important; }
[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"],
[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"] [data-item-hl],
[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover [data-item-hl] { background-color: var(--kib-hover) !important; }

/* ---------- file uploader ---------- */
[data-testid="stFileUploaderDropzone"] {
    background-color: var(--kib-surface) !important;
    border: 1px dashed var(--kib-border) !important;
    border-radius: 8px;
}
[data-testid="stFileUploaderDropzoneInstructions"] div { color: var(--kib-muted) !important; }
[data-testid="stFileChip"] {
    background-color: var(--kib-hover) !important;
    border: 1px solid var(--kib-border) !important;
    border-radius: 8px;
}
[data-testid="stFileChip"] div,
[data-testid="stFileChip"] span { color: var(--kib-text) !important; }
[data-testid="stFileChip"] svg { fill: var(--kib-text) !important; }

/* ---------- buttons ---------- */
button[data-testid^="stBaseButton"] {
    background-color: var(--kib-surface) !important;
    color: var(--kib-text) !important;
    border: 1px solid var(--kib-border) !important;
    border-radius: 8px;
}
button[data-testid^="stBaseButton"]:hover,
button[data-testid^="stBaseButton"]:focus {
    background-color: var(--kib-hover) !important;
    color: var(--kib-text) !important;
}
button[data-testid^="stBaseButton"] p,
button[data-testid^="stBaseButton"] span,
button[data-testid^="stBaseButton"] svg { color: var(--kib-text) !important; fill: var(--kib-text) !important; }
button[data-testid="stBaseButton-headerNoPadding"] {
    background-color: transparent !important; border: 0 !important;
}
button[data-testid="stBaseButton-primary"] {
    background-color: var(--kib-accent) !important; border-color: var(--kib-accent) !important;
}
button[data-testid="stBaseButton-primary"] p { color: #ffffff !important; }

/* ---------- radio ---------- */
[data-testid="stRadioOption"] p { color: var(--kib-text) !important; }
[data-testid="stRadioOption"] > div > div:first-child {
    background-color: transparent !important;
    border: 1px solid var(--kib-border) !important;
}
[data-testid="stRadioOption"]:has(input:checked) > div > div:first-child {
    background-color: var(--kib-accent) !important;
    border-color: var(--kib-accent) !important;
}
[data-testid="stRadioOption"]:has(input:checked) > div > div:first-child > div {
    background-color: var(--kib-app) !important;
}

/* ---------- progress ---------- */
[data-testid="stProgressBarTrack"] { background-color: var(--kib-border) !important; }
[data-testid="stProgressBarTrack"] > div { background-color: var(--kib-accent) !important; }

/* ---------- alerts ---------- */
[data-testid="stAlertContainer"] {
    background-color: var(--kib-surface) !important;
    border: 1px solid var(--kib-border) !important;
    border-radius: 8px;
    color: var(--kib-text) !important;
}
[data-testid="stAlertContainer"] p,
[data-testid="stAlertContainer"] span,
[data-testid="stAlertContainer"] div { color: var(--kib-text) !important; }
[data-testid="stAlertContainer"] a { color: var(--kib-link) !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {
    box-shadow: inset 4px 0 0 0 var(--kib-info) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
    box-shadow: inset 4px 0 0 0 var(--kib-warning) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
    box-shadow: inset 4px 0 0 0 var(--kib-success) !important;
}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
    box-shadow: inset 4px 0 0 0 var(--kib-danger) !important;
}

/* ---------- expander ---------- */
[data-testid="stExpander"] details {
    background-color: transparent !important;
    border: 1px solid var(--kib-border) !important;
    border-radius: 8px;
}
[data-testid="stExpander"] summary { background-color: var(--kib-surface) !important; }
[data-testid="stExpander"] summary:hover { background-color: var(--kib-hover) !important; }
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span { color: var(--kib-text) !important; }
[data-testid="stExpanderDetails"] { background-color: transparent !important; }

/* ---------- code ---------- */
[data-testid="stCode"],
[data-testid="stCode"] pre,
[data-testid="stCode"] code { background-color: var(--kib-code) !important; color: var(--kib-text) !important; }
[data-testid="stCode"] pre span { color: var(--kib-text) !important; }
[data-testid="stMarkdownContainer"] code {
    background-color: var(--kib-code) !important; color: var(--kib-text) !important;
}

/* ---------- metrics ---------- */
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div { color: var(--kib-text) !important; }
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p { color: var(--kib-muted) !important; }
"""
)


def palette(theme: str) -> dict[str, str]:
    """Return the colour palette for ``theme``, falling back to light."""
    return PALETTE[theme if theme in PALETTE else "light"]


def system_theme() -> str:
    """Return the theme Streamlit itself is using for this viewer."""
    try:
        theme = st.context.theme
    except Exception:  # noqa: BLE001 - any Streamlit internals may break here
        return "light"
    value = getattr(theme, "type", None)
    if value is None and isinstance(theme, dict):
        value = theme.get("type")
    return "dark" if str(value).lower() == "dark" else "light"


def active_theme(choice: str, current: str | None = None) -> str:
    """Resolve the radio choice into the theme the page should be drawn in."""
    if choice == "system":
        return current if current in LANGS else system_theme()
    return choice if choice in LANGS else "light"


def css(theme: str, *, force: bool = False) -> str:
    """Return the stylesheet for ``theme``.

    ``force`` adds the widget repaint used when the sidebar radio contradicts
    Streamlit's own theme; without it Streamlit stays in charge of the widgets.
    """
    colors = palette(theme)
    parts = [_BASE.substitute(colors)]
    if force:
        parts.append(_FORCE.substitute(colors))
    return "<style>\n" + "\n".join(part.strip() for part in parts) + "\n</style>"
