"""Detectors that turn mailbox configuration into BEC indicators.

Each detector is a pure function ``(mailbox, rule) -> Finding | None``.
The detectors never raise on valid data and never perform I/O, which keeps
them trivially testable and safe to run inside a web request. Human-readable
texts are resolved later from :mod:`app.i18n` by ``detector_id``.
"""

from __future__ import annotations

from typing import Callable

from .model import (
    FINANCE_KEYWORDS,
    HIDING_FOLDER_MARKERS,
    VISIBLE_FOLDERS,
    Delegation,
    Finding,
    Mailbox,
    Rule,
)
from .parser import local_hour, split_email, weekday

RuleDetector = Callable[[Mailbox, Rule], "Finding | None"]


def _domain_of(address: str) -> str:
    try:
        return split_email(address)[1]
    except Exception:  # pragma: no cover - parser already validates addresses
        return address.rsplit("@", 1)[-1].lower()


def is_external(address: str, mailbox: Mailbox) -> bool:
    """True when the address belongs to a domain outside the company."""
    return _domain_of(address) not in {d.lower() for d in mailbox.baseline.internal_domains}


def _finance_hits(rule: Rule) -> list[str]:
    hits: list[str] = []
    for keyword in rule.conditions.subject_keywords:
        lowered = keyword.lower()
        for marker in FINANCE_KEYWORDS:
            if marker in lowered:
                hits.append(keyword)
                break
    return hits


def _folder_hidden(rule: Rule) -> bool:
    if not rule.move_to:
        return False
    folder = rule.move_to.strip().lower()
    if any(folder == visible or folder.startswith(visible + "/") for visible in VISIBLE_FOLDERS):
        return False
    if any(marker in folder for marker in HIDING_FOLDER_MARKERS):
        return True
    # A custom folder plus "mark as read" is how silently hidden mail looks,
    # but only for rules that actually target money-related messages.
    return rule.mark_as_read and bool(_finance_hits(rule))


def detect_external_forward(mailbox: Mailbox, rule: Rule) -> Finding | None:
    external = [target for target in rule.forward_to if is_external(target, mailbox)]
    if not external:
        return None
    return Finding(
        detector_id="EXT_FORWARD",
        rule_id=rule.rule_id,
        weight=35,
        evidence=", ".join(external),
    )


def detect_forward_without_copy(mailbox: Mailbox, rule: Rule) -> Finding | None:
    if not rule.forwards:
        return None
    if rule.keep_copy and not rule.delete_after:
        return None
    return Finding(
        detector_id="FORWARD_NO_COPY",
        rule_id=rule.rule_id,
        weight=25,
        evidence=f"keep_copy={rule.keep_copy}, delete_after={rule.delete_after}",
    )


def detect_hidden_folder(mailbox: Mailbox, rule: Rule) -> Finding | None:
    if not _folder_hidden(rule):
        return None
    return Finding(
        detector_id="HIDDEN_FOLDER",
        rule_id=rule.rule_id,
        weight=20,
        evidence=f"move_to={rule.move_to}, mark_as_read={rule.mark_as_read}",
    )


def detect_finance_target(mailbox: Mailbox, rule: Rule) -> Finding | None:
    hits = _finance_hits(rule)
    if not hits:
        return None
    if not (rule.forwards or _folder_hidden(rule)):
        return None
    return Finding(
        detector_id="FINANCE_TARGET",
        rule_id=rule.rule_id,
        weight=15,
        evidence=", ".join(hits),
    )


def detect_off_hours_rule(mailbox: Mailbox, rule: Rule) -> Finding | None:
    moment = rule.created_at
    if moment is None:
        return None
    hour = local_hour(moment)
    if mailbox.baseline.is_work_hour(hour) and weekday(moment) < 5:
        return None
    return Finding(
        detector_id="OFF_HOURS_RULE",
        rule_id=rule.rule_id,
        weight=10,
        evidence=moment.isoformat(timespec="minutes"),
    )


def detect_risky_session(mailbox: Mailbox, rule: Rule) -> Finding | None:
    session = mailbox.session(rule.session_id)
    if session is None:
        return None
    foreign = session.country and session.country not in {
        c.upper() for c in mailbox.baseline.known_countries
    }
    if session.mfa and not foreign:
        return None
    reasons = []
    if not session.mfa:
        reasons.append("MFA: нет")
    if foreign:
        reasons.append(f"country={session.country}")
    return Finding(
        detector_id="RISKY_SESSION",
        rule_id=rule.rule_id,
        weight=15,
        evidence=", ".join(reasons),
    )


def detect_external_delegation(mailbox: Mailbox, delegation: Delegation) -> Finding | None:
    if not is_external(delegation.grantee, mailbox):
        return None
    return Finding(
        detector_id="EXT_DELEGATION",
        rule_id=delegation.delegation_id,
        weight=30,
        evidence=f"{delegation.grantee} ({delegation.level})",
    )


RULE_DETECTORS: tuple[RuleDetector, ...] = (
    detect_external_forward,
    detect_forward_without_copy,
    detect_hidden_folder,
    detect_finance_target,
    detect_off_hours_rule,
    detect_risky_session,
)


def analyze(mailbox: Mailbox) -> tuple[dict[str, list[Finding]], list[Finding]]:
    """Run every detector and group findings by rule."""
    per_rule: dict[str, list[Finding]] = {}
    for rule in mailbox.rules:
        for detector in RULE_DETECTORS:
            finding = detector(mailbox, rule)
            if finding is not None:
                per_rule.setdefault(rule.rule_id, []).append(finding)
    mailbox_findings: list[Finding] = []
    for delegation in mailbox.delegations:
        finding = detect_external_delegation(mailbox, delegation)
        if finding is not None:
            mailbox_findings.append(finding)
    return per_rule, mailbox_findings
