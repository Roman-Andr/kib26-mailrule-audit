"""Streamlit interface: choose an export, get a readable verdict.

Run locally with::

    streamlit run app/ui.py

The page never sends the export anywhere: parsing, scoring and rendering all
happen in the same process.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from app.parser import ValidationError, parse_export  # noqa: E402
from app.report import priority_for, render_markdown, to_dict  # noqa: E402
from app.scoring import audit  # noqa: E402

DATA_DIR = ROOT / "data" / "synthetic"

LEVEL_ICON = {
    "critical": "🟥",
    "high": "🟧",
    "medium": "🟨",
    "low": "🟦",
    "clean": "🟩",
}


def _cases() -> list[Path]:
    return sorted(DATA_DIR.glob("case-*.json"))


def _render_report(report) -> None:
    icon = LEVEL_ICON.get(report.level, "⬜")
    left, middle, right = st.columns([2, 1, 1])
    with left:
        st.subheader(f"{icon} {report.verdict}")
    with middle:
        st.metric("Балл риска", f"{report.score} / 100")
    with right:
        st.metric("Правил с находками", f"{report.rules_flagged} из {report.rules_total}")

    st.progress(min(report.score, 100) / 100)

    st.markdown("### Что делать в первую очередь")
    for index, action in enumerate(report.actions, start=1):
        st.markdown(f"{index}. {action}")

    if report.assessments:
        st.markdown("### Находки по правилам")
        rows: list[dict[str, Any]] = []
        for assessment in report.assessments:
            for finding in assessment.findings:
                rows.append(
                    {
                        "Приоритет": priority_for(assessment.score),
                        "Правило": f"{assessment.rule_id} «{assessment.rule_name}»",
                        "Находка": f"{finding.title}: {finding.evidence}",
                        "Почему опасно": finding.explanation,
                        "Что делать": finding.recommendation,
                    }
                )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    if report.mailbox_findings:
        st.markdown("### Доступы к ящику")
        for finding in report.mailbox_findings:
            st.warning(f"**{finding.title}** — {finding.evidence}. {finding.explanation}")

    if report.level == "clean":
        st.success(
            "Подозрительных правил не найдено. Проверяются только правила, "
            "сессии и делегирования из выгрузки."
        )

    st.download_button(
        "Скачать отчёт (Markdown)",
        data=render_markdown(report),
        file_name=f"report-{report.mailbox_domain}.md",
        mime="text/markdown",
    )
    st.download_button(
        "Скачать отчёт (JSON)",
        data=json.dumps(to_dict(report), ensure_ascii=False, indent=2),
        file_name=f"report-{report.mailbox_domain}.json",
        mime="application/json",
    )


def main() -> None:
    st.set_page_config(page_title="Аудитор правил ящика", page_icon="📮", layout="wide")
    st.title("Аудитор правил почтового ящика")
    st.caption(
        "KIB-26 «Пиксель». Только синтетические данные: приложение не делает "
        "сетевых вызовов и не отправляет выгрузку никуда, кроме этой страницы."
    )

    cases = _cases()
    with st.sidebar:
        st.header("Выгрузка")
        options = ["— выберите пример —"] + [path.name for path in cases]
        chosen = st.selectbox("Синтетический пример", options)
        uploaded = st.file_uploader("Или загрузите свой JSON", type=["json"])
        st.divider()
        st.markdown(
            "**Как это работает**\n\n"
            "1. Экспорт правил, сессий и делегирований.\n"
            "2. Семь детекторов ищут пересылку и сокрытие писем.\n"
            "3. Скор 0–100 и отчёт на понятном языке."
        )

    payload: Any | None = None
    source = ""
    if uploaded is not None:
        try:
            payload = json.loads(uploaded.getvalue().decode("utf-8"))
            source = uploaded.name
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            st.error(f"Файл не разобран: {exc}")
            return
    elif chosen != options[0]:
        template = (DATA_DIR / chosen).read_text(encoding="utf-8")
        with st.expander("Показать исходную выгрузку"):
            st.code(template, language="json")
        payload = json.loads(template)
        source = chosen

    if payload is None:
        st.info("Выберите пример слева или загрузите JSON-экспорт правил ящика.")
        return

    try:
        mailbox = parse_export(payload, source=source)
    except ValidationError as exc:
        st.error(f"Выгрузка не прошла проверку: {exc}")
        return

    report = audit(mailbox)
    _render_report(report)

    with st.expander("Ограничения"):
        st.markdown(
            "Отчёт построен по выгрузке правил, сессий и делегирований. "
            "Он не видит правила, созданные вне почты, не читает содержимое "
            "писем и не заменяет журнал платежей. Решение принимает человек."
        )


if __name__ == "__main__":
    main()
