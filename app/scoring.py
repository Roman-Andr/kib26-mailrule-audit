"""Risk scoring and report assembly.

Scoring is deliberately simple and explainable: the user must be able to see
why a mailbox got its score. Each finding carries a fixed weight, a rule score
is the capped sum of its findings, and the mailbox score adds a bonus for
several compromised rules (an attacker usually leaves more than one).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from . import detectors
from .model import AuditReport, Finding, Mailbox, RuleAssessment

CRITICAL_THRESHOLD = 85
HIGH_THRESHOLD = 60
MEDIUM_THRESHOLD = 30
RISKY_RULE_THRESHOLD = 40

LEVELS = (
    (CRITICAL_THRESHOLD, "critical"),
    (HIGH_THRESHOLD, "high"),
    (MEDIUM_THRESHOLD, "medium"),
    (1, "low"),
    (0, "clean"),
)


def rule_score(findings: Sequence[Finding]) -> int:
    """Capped sum of finding weights for a single rule."""
    return min(100, sum(finding.weight for finding in findings))


def mailbox_score(
    rule_scores: Sequence[int], mailbox_findings: Sequence[Finding]
) -> int:
    """Overall score: the worst rule plus a bonus for repeated compromise."""
    candidates = list(rule_scores) + [finding.weight for finding in mailbox_findings]
    if not candidates:
        return 0
    base = max(candidates)
    risky_rules = sum(1 for score in rule_scores if score >= RISKY_RULE_THRESHOLD)
    bonus = 10 * max(0, risky_rules - 1)
    return min(100, base + bonus)


def level_for(score: int) -> str:
    """Map a numeric score to a machine level."""
    for threshold, level in LEVELS:
        if score >= threshold:
            return level
    return "clean"


def _action_keys(
    assessments: Sequence[RuleAssessment], mailbox_findings: Sequence[Finding]
) -> tuple[str, ...]:
    detector_ids = {f.detector_id for a in assessments for f in a.findings}
    detector_ids |= {f.detector_id for f in mailbox_findings}
    keys: list[str] = []
    if "EXT_DELEGATION" in detector_ids:
        keys.append("revoke_delegation")
    if detector_ids & {"EXT_FORWARD", "FORWARD_NO_COPY"}:
        keys.append("disable_forwarding")
    if "HIDDEN_FOLDER" in detector_ids:
        keys.append("inspect_folders")
    if detector_ids & {"RISKY_SESSION", "OFF_HOURS_RULE"}:
        keys.append("reset_credentials")
    if detector_ids & {"FINANCE_TARGET", "EXT_FORWARD", "HIDDEN_FOLDER"}:
        keys.append("check_payments")
    if not keys:
        keys.append("none")
    return tuple(keys[:4])


def audit(mailbox: Mailbox, now: datetime | None = None) -> AuditReport:
    """Run detectors, score every rule and build the final report."""
    per_rule, mailbox_findings = detectors.analyze(mailbox)
    assessments: list[RuleAssessment] = []
    for rule in mailbox.rules:
        findings = tuple(per_rule.get(rule.rule_id, ()))
        if not findings:
            continue
        findings = tuple(sorted(findings, key=lambda f: -f.weight))
        assessments.append(
            RuleAssessment(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                score=rule_score(findings),
                findings=findings,
            )
        )
    assessments.sort(key=lambda a: (-a.score, a.rule_id))
    score = mailbox_score([a.score for a in assessments], mailbox_findings)
    return AuditReport(
        mailbox_email=mailbox.email,
        mailbox_domain=mailbox.domain,
        generated_at=now or datetime.now(timezone.utc),
        rules_total=len(mailbox.rules),
        rules_flagged=len(assessments),
        score=score,
        level=level_for(score),
        assessments=tuple(assessments),
        mailbox_findings=tuple(mailbox_findings),
        action_keys=_action_keys(assessments, mailbox_findings),
        source=mailbox.source,
    )
