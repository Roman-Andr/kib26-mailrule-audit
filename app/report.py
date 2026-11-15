"""Report rendering.

Two output formats are supported: Markdown for humans and a JSON summary for
tests and integrations. All user-controlled strings are escaped before they
reach the report, so a malicious rule name cannot break the table or inject
HTML into the Streamlit page. Every visible string comes from :mod:`app.i18n`.
"""

from __future__ import annotations

from typing import Any

from . import i18n
from .model import AuditReport, Finding


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


def _finding_title(finding: Finding, lang: str) -> str:
    return i18n.detector_text(lang, finding.detector_id)["title"]


def findings_rows(report: AuditReport, lang: str = i18n.DEFAULT_LANG) -> list[dict[str, str]]:
    """Flatten findings into rows ready for a table."""
    code = i18n.normalise(lang)
    rows: list[dict[str, str]] = []
    for assessment in report.assessments:
        for finding in assessment.findings:
            text = i18n.detector_text(code, finding.detector_id)
            rows.append(
                {
                    "priority": priority_for(assessment.score),
                    "rule": f"{assessment.rule_id} «{assessment.rule_name}»",
                    "finding": f"{text['title']}: {finding.evidence}",
                    "why": text["explanation"],
                    "fix": text["recommendation"],
                    "detector": finding.detector_id,
                }
            )
    return rows


def render_markdown(report: AuditReport, lang: str = i18n.DEFAULT_LANG) -> str:
    """Render the human-readable report in the requested language."""
    code = i18n.normalise(lang)
    t = lambda key: i18n.report_text(code, key)  # noqa: E731

    lines: list[str] = [t("title"), ""]
    lines.append(f"- {t('mailbox')}: {_safe(report.mailbox_email, 120)}")
    lines.append(f"- {t('date')}: {report.generated_at.strftime('%d.%m.%Y %H:%M')}")
    if report.source:
        lines.append(f"- {t('source')}: {_safe(report.source, 120)}")
    lines.append(
        "- "
        + t("rules")
        + ": "
        + t("rules_value").format(total=report.rules_total, flagged=report.rules_flagged)
    )
    lines.append("")
    lines.append(t("verdict"))
    lines.append("")
    lines.append(
        t("verdict_line").format(
            verdict=i18n.verdict_text(code, report.level), score=report.score
        )
    )
    lines.append("")

    if not report.assessments and not report.mailbox_findings:
        lines.append(t("clean_note"))
        lines.append("")

    if report.action_keys:
        lines.append(t("actions"))
        lines.append("")
        for index, key in enumerate(report.action_keys, start=1):
            lines.append(f"{index}. {_safe(i18n.action_text(code, key), 240)}")
        lines.append("")

    if report.assessments:
        lines.append(t("findings"))
        lines.append("")
        lines.append(
            f"| {t('col_priority')} | {t('col_rule')} | {t('col_finding')} "
            f"| {t('col_why')} | {t('col_fix')} |"
        )
        lines.append("|-----------|---------|---------|----------------|------------|")
        for row in findings_rows(report, code):
            lines.append(
                "| {priority} | {rule} | {finding} | {why} | {fix} |".format(
                    priority=row["priority"],
                    rule=_safe(row["rule"], 90),
                    finding=_safe(row["finding"], 90),
                    why=_safe(row["why"], 160),
                    fix=_safe(row["fix"], 160),
                )
            )
        lines.append("")

    if report.mailbox_findings:
        lines.append(t("access"))
        lines.append("")
        for finding in report.mailbox_findings:
            text = i18n.detector_text(code, finding.detector_id)
            lines.append(
                "- "
                + t("access_line").format(
                    title=_safe(text["title"], 80),
                    evidence=_safe(finding.evidence, 120),
                    explanation=_safe(text["explanation"], 200),
                )
            )
        lines.append("")

    lines.append(t("scoring"))
    lines.append("")
    lines.append(t("scoring_text"))
    lines.append("")
    lines.append(t("limits"))
    lines.append("")
    lines.append(t("limits_text"))
    lines.append("")
    return "\n".join(lines)


def to_dict(report: AuditReport, lang: str = i18n.DEFAULT_LANG) -> dict[str, Any]:
    """Machine-readable summary used by tests and integrations."""
    code = i18n.normalise(lang)
    return {
        "mailbox": report.mailbox_email,
        "domain": report.mailbox_domain,
        "generated_at": report.generated_at.isoformat(),
        "lang": code,
        "score": report.score,
        "verdict": i18n.verdict_text(code, report.level),
        "level": report.level,
        "rules_total": report.rules_total,
        "rules_flagged": report.rules_flagged,
        "actions": [i18n.action_text(code, key) for key in report.action_keys],
        "rules": [
            {
                "id": assessment.rule_id,
                "name": assessment.rule_name,
                "score": assessment.score,
                "priority": priority_for(assessment.score),
                "findings": [
                    {
                        "detector": finding.detector_id,
                        "title": _finding_title(finding, code),
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
                "title": _finding_title(finding, code),
                "weight": finding.weight,
                "evidence": finding.evidence,
            }
            for finding in report.mailbox_findings
        ],
        "source": report.source,
    }
