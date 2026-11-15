"""Report rendering.

Two output formats are supported: Markdown for humans and a JSON summary for
tests and integrations. All user-controlled strings are escaped before they
reach the report, so a malicious rule name cannot break the table or inject
HTML into the Streamlit page.
"""

from __future__ import annotations

from typing import Any

from .model import AuditReport


def _safe(text: str, limit: int = 200) -> str:
    """Make a value safe for a Markdown table cell and for HTML rendering."""
    cleaned = " ".join(str(text).split())
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1] + "…"
    return (
        cleaned.replace("|", "\\|")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "'")
    )


def priority_for(score: int) -> str:
    if score >= 85:
        return "P1"
    if score >= 60:
        return "P2"
    if score >= 40:
        return "P3"
    return "P4"


def _verdict_line(report: AuditReport) -> str:
    return f"**{report.verdict}** — {report.score} из 100"


def render_markdown(report: AuditReport) -> str:
    """Render the human-readable report."""
    lines: list[str] = []
    lines.append("# Отчёт по правилам почтового ящика")
    lines.append("")
    lines.append(f"- Ящик: {_safe(report.mailbox_email, 120)}")
    lines.append(f"- Дата отчёта: {report.generated_at.strftime('%d.%m.%Y %H:%M')}")
    if report.source:
        lines.append(f"- Источник: {_safe(report.source, 120)}")
    lines.append(
        f"- Проверено правил: {report.rules_total}, с находками: {report.rules_flagged}"
    )
    lines.append("")
    lines.append("## Вердикт")
    lines.append("")
    lines.append(_verdict_line(report))
    lines.append("")

    if not report.assessments and not report.mailbox_findings:
        lines.append(
            "Подозрительных правил и внешних доступов не найдено. Это не "
            "гарантия отсутствия взлома: проверяются только правила, сессии "
            "и делегирования из экспорта."
        )
        lines.append("")

    if report.actions:
        lines.append("## Что делать в первую очередь")
        lines.append("")
        for index, action in enumerate(report.actions, start=1):
            lines.append(f"{index}. {_safe(action, 240)}")
        lines.append("")

    if report.assessments:
        lines.append("## Находки по правилам")
        lines.append("")
        lines.append("| Приоритет | Правило | Находка | Почему опасно | Что делать |")
        lines.append("|-----------|---------|---------|----------------|------------|")
        for assessment in report.assessments:
            name = _safe(f"{assessment.rule_id} «{assessment.rule_name}»", 90)
            for finding in assessment.findings:
                lines.append(
                    "| {priority} | {name} | {title} | {why} | {fix} |".format(
                        priority=priority_for(assessment.score),
                        name=name,
                        title=_safe(f"{finding.title}: {finding.evidence}", 90),
                        why=_safe(finding.explanation, 160),
                        fix=_safe(finding.recommendation, 160),
                    )
                )
        lines.append("")

    if report.mailbox_findings:
        lines.append("## Доступы к ящику")
        lines.append("")
        for finding in report.mailbox_findings:
            lines.append(
                f"- **{_safe(finding.title, 80)}** — {_safe(finding.evidence, 120)}. "
                f"{_safe(finding.explanation, 200)}"
            )
        lines.append("")

    lines.append("## Как считается оценка")
    lines.append("")
    lines.append(
        "Каждая находка имеет вес: пересылка на внешний адрес — 35, "
        "пересылка без копии — 25, внешний доступ к ящику — 30, "
        "сокрытие в папке — 20, фильтр по финансам — 15, "
        "подозрительная сессия — 15, нерабочее время — 10. "
        "Балл правила — сумма весов (не больше 100). Итог — худшее правило "
        "плюс 10 за каждое дополнительное правило с баллом 40 и выше."
    )
    lines.append("")
    lines.append("## Ограничения")
    lines.append("")
    lines.append(
        "Отчёт построен по выгрузке правил, сессий и делегирований. "
        "Он не видит правила, созданные вне почты, не проверяет содержимое "
        "писем и не заменяет журнал платежей. Решение о блокировке принимает "
        "человек."
    )
    lines.append("")
    return "\n".join(lines)


def to_dict(report: AuditReport) -> dict[str, Any]:
    """Machine-readable summary used by tests and integrations."""
    return {
        "mailbox": report.mailbox_email,
        "domain": report.mailbox_domain,
        "generated_at": report.generated_at.isoformat(),
        "score": report.score,
        "verdict": report.verdict,
        "level": report.level,
        "rules_total": report.rules_total,
        "rules_flagged": report.rules_flagged,
        "actions": list(report.actions),
        "rules": [
            {
                "id": assessment.rule_id,
                "name": assessment.rule_name,
                "score": assessment.score,
                "priority": priority_for(assessment.score),
                "findings": [
                    {
                        "detector": finding.detector_id,
                        "title": finding.title,
                        "weight": finding.weight,
                        "evidence": finding.evidence,
                    }
                    for finding in assessment.findings
                ],
            }
            for assessment in report.assessments
        ],
        "mailbox_findings": [
            {
                "detector": finding.detector_id,
                "title": finding.title,
                "weight": finding.weight,
                "evidence": finding.evidence,
            }
            for finding in report.mailbox_findings
        ],
        "source": report.source,
    }
