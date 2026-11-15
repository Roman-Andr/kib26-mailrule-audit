"""Streamlit interface: choose an export, get a readable verdict.

Run locally with::

    streamlit run app/ui.py

The page never sends the export anywhere: parsing, scoring and rendering all
happen in the same process. Language and theme are switched in the sidebar.

Streamlit itself renders light or dark depending on ``[theme.light]`` and
``[theme.dark]`` in ``.streamlit/config.toml``; the sidebar switch can force the
other palette, and :mod:`app.theme` repaints the widgets in that case.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app import i18n, theme  # noqa: E402
from app.parser import ValidationError, parse_export  # noqa: E402
from app.report import findings_rows, render_markdown, to_dict  # noqa: E402
from app.scoring import audit  # noqa: E402

DATA_DIR = ROOT / "data" / "synthetic"

LEVEL_ICON = {
    "critical": "🟥",
    "high": "🟧",
    "medium": "🟨",
    "low": "🟦",
    "clean": "🟩",
}


def _table(rows: list[dict[str, str]], headers: list[tuple[str, str]]) -> str:
    """Build an escaped HTML table from finding rows."""
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in headers)
    body = []
    for row in rows:
        cells = []
        for key, _ in headers:
            if key == "priority":
                cls = row[key].lower()
                cells.append(f'<td><span class="kib-badge {cls}">{html.escape(row[key])}</span></td>')
            else:
                cells.append(f"<td>{html.escape(row[key])}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<table class="kib-table"><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def _render_report(report, lang: str) -> None:
    icon = LEVEL_ICON.get(report.level, "⬜")
    left, middle, right = st.columns([2, 1, 1])
    with left:
        st.subheader(f"{icon} {i18n.verdict_text(lang, report.level)}")
    with middle:
        st.metric(i18n.ui(lang, "metric_score"), f"{report.score} / 100")
    with right:
        st.metric(
            i18n.ui(lang, "metric_flagged"),
            f"{report.rules_flagged} {i18n.ui(lang, 'metric_flagged_value')} {report.rules_total}",
        )

    st.progress(min(report.score, 100) / 100)

    st.markdown(f"### {i18n.ui(lang, 'actions_header')}")
    for index, key in enumerate(report.action_keys, start=1):
        st.markdown(f"{index}. {i18n.action_text(lang, key)}")

    if report.assessments:
        st.markdown(f"### {i18n.ui(lang, 'findings_header')}")
        rows = findings_rows(report, lang)
        headers = [
            ("priority", i18n.report_text(lang, "col_priority")),
            ("rule", i18n.report_text(lang, "col_rule")),
            ("finding", i18n.report_text(lang, "col_finding")),
            ("why", i18n.report_text(lang, "col_why")),
            ("fix", i18n.report_text(lang, "col_fix")),
        ]
        st.markdown(_table(rows, headers), unsafe_allow_html=True)

    if report.mailbox_findings:
        st.markdown(f"### {i18n.ui(lang, 'access_header')}")
        for finding in report.mailbox_findings:
            text = i18n.detector_text(lang, finding.detector_id)
            st.warning(
                f"**{text['title']}** — {finding.evidence}. {text['explanation']}"
            )

    if report.level == "clean":
        st.success(i18n.ui(lang, "clean_success"))

    st.download_button(
        i18n.ui(lang, "download_md"),
        data=render_markdown(report, lang),
        file_name=f"report-{report.mailbox_domain}-{lang}.md",
        mime="text/markdown",
    )
    st.download_button(
        i18n.ui(lang, "download_json"),
        data=json.dumps(to_dict(report, lang), ensure_ascii=False, indent=2),
        file_name=f"report-{report.mailbox_domain}-{lang}.json",
        mime="application/json",
    )


def main() -> None:
    st.set_page_config(page_title="KIB-26 · Mailbox rule auditor", page_icon="📮", layout="wide")

    with st.sidebar:
        st.header("Language / Язык")
        lang_label = st.radio(
            "Language / Язык",
            options=[i18n.LANG_LABELS[code] for code in i18n.LANGS],
            index=0,
            label_visibility="collapsed",
        )
        lang = next(code for code in i18n.LANGS if i18n.LANG_LABELS[code] == lang_label)

        st.divider()
        st.header(i18n.ui(lang, "settings_header"))
        theme_options = {
            "system": i18n.ui(lang, "theme_system"),
            "light": i18n.ui(lang, "theme_light"),
            "dark": i18n.ui(lang, "theme_dark"),
        }
        theme_choice = st.radio(
            i18n.ui(lang, "theme"),
            options=list(theme_options),
            format_func=lambda key: theme_options[key],
            index=0,
            horizontal=True,
        )

        st.divider()
        st.header(i18n.ui(lang, "sidebar_header"))
        cases = sorted(DATA_DIR.glob("case-*.json"))
        options = [i18n.ui(lang, "select_placeholder")] + [path.name for path in cases]
        chosen = st.selectbox(i18n.ui(lang, "select_example"), options)
        uploaded = st.file_uploader(i18n.ui(lang, "upload"), type=["json"])

        st.divider()
        st.markdown(i18n.ui(lang, "how_it_works"))
        st.markdown(i18n.ui(lang, "how_it_works_text"))

    native_theme = theme.system_theme()
    active_theme = theme.active_theme(theme_choice, native_theme)
    st.markdown(
        theme.css(active_theme, force=active_theme != native_theme),
        unsafe_allow_html=True,
    )

    st.title(i18n.ui(lang, "app_title"))
    st.caption(i18n.ui(lang, "caption"))

    payload: Any | None = None
    source = ""
    if uploaded is not None:
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
            source = uploaded.name
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            st.error(f"{i18n.ui(lang, 'error_json')}: {exc}")
            return
    elif chosen != options[0]:
        template = (DATA_DIR / chosen).read_text(encoding="utf-8")
        with st.expander(i18n.ui(lang, "show_source")):
            st.code(template, language="json")
        payload = json.loads(template)
        source = chosen

    if payload is None:
        st.info(i18n.ui(lang, "info_pick"))
        return

    try:
        mailbox = parse_export(payload, source=source)
    except ValidationError as exc:
        st.error(f"{i18n.ui(lang, 'error_validation')}: {exc}")
        return

    report = audit(mailbox)
    _render_report(report, lang)

    with st.expander(i18n.ui(lang, "limits_header")):
        st.markdown(i18n.ui(lang, "limits_text"))
    st.caption(i18n.ui(lang, "footer"))


if __name__ == "__main__":
    main()
