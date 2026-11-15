"""Detectors that turn mailbox configuration into BEC indicators.

Each detector is a pure function ``(mailbox, rule) -> Finding | None``.
The detectors never raise on valid data and never perform I/O, which keeps
them trivially testable and safe to run inside a web request.
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


def _domains(address: str) -> str:
    try:
        return split_email(address)[1]
    except Exception:  # pragma: no cover - parser already validates addresses
        return address.rsplit("@", 1)[-1].lower()


def is_external(address: str, mailbox: Mailbox) -> bool:
    """True when the address belongs to a domain outside the company."""
    return _domains(address) not in {d.lower() for d in mailbox.baseline.internal_domains}


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
        title="Пересылка на внешний адрес",
        weight=35,
        explanation=(
            "Правило отправляет копии писем за пределы компании. Так выглядит "
            "типовой сбор переписки после захвата ящика."
        ),
        recommendation=(
            "Проверить автора правила, отключить пересылку и сменить пароль "
            "ящика; проверить, не уходили ли письма за период действия правила."
        ),
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
        title="Пересылка без сохранения копии",
        weight=25,
        explanation=(
            "Письмо пересылается наружу и не остаётся в ящике владельца: "
            "исчезновение следов переписки — признак сокрытия."
        ),
        recommendation=(
            "Включить сохранение копии или удалить правило; сверить журнал "
            "отправленных сообщений за период действия."
        ),
        evidence=f"keep_copy={rule.keep_copy}, delete_after={rule.delete_after}",
    )


def detect_hidden_folder(mailbox: Mailbox, rule: Rule) -> Finding | None:
    if not _folder_hidden(rule):
        return None
    folder = rule.move_to or ""
    return Finding(
        detector_id="HIDDEN_FOLDER",
        rule_id=rule.rule_id,
        title="Сокрытие письма в папке",
        weight=20,
        explanation=(
            "Письма переносятся в папку, которую владелец не просматривает, "
            "часто с отметкой «прочитано». Уведомление о входе и переписка "
            "с банком пропадают из виду."
        ),
        recommendation=(
            "Вернуть правило в «Входящие» или удалить его; проверить "
            f"содержимое папки «{folder}»."
        ),
        evidence=f"move_to={folder}, mark_as_read={rule.mark_as_read}",
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
        title="Фильтр по финансовым ключевым словам",
        weight=15,
        explanation=(
            "Правило нацелено на письма о платежах, счетах и договорах: "
            "именно их нужно скрыть, чтобы компания не заметила подготовку "
            "мошеннического перевода."
        ),
        recommendation=(
            "Удалить правило и проверить, не менялись ли реквизиты "
            "контрагентов в переписке за период его действия."
        ),
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
        title="Правило создано в нерабочее время",
        weight=10,
        explanation=(
            "Правило появилось вне рабочих часов или в выходной. Само по себе "
            "это не нарушение, но вместе с пересылкой или сокрытием указывает "
            "на действия злоумышленника."
        ),
        recommendation=(
            "Уточнить у автора правила, когда и зачем оно создавалось; "
            "сверить с историей входов в ящик."
        ),
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
        reasons.append("вход без MFA")
    if foreign:
        reasons.append(f"страна входа {session.country}")
    return Finding(
        detector_id="RISKY_SESSION",
        rule_id=rule.rule_id,
        title="Правило создано из подозрительной сессии",
        weight=15,
        explanation=(
            "Правило появилось в сессии, которая не похожа на обычную работу "
            "сотрудника."
        ),
        recommendation=(
            "Завершить все сессии ящика, включить MFA, проверить журнал "
            "входов за последние 30 дней."
        ),
        evidence=", ".join(reasons),
    )


def detect_external_delegation(mailbox: Mailbox, delegation: Delegation) -> Finding | None:
    if not is_external(delegation.grantee, mailbox):
        return None
    return Finding(
        detector_id="EXT_DELEGATION",
        rule_id=delegation.delegation_id,
        title="Доступ к ящику выдан внешнему адресу",
        weight=30,
        explanation=(
            "Ящик открыт постороннему адресу. Такой доступ не требует правил "
            "пересылки: злоумышленник читает переписку напрямую."
        ),
        recommendation=(
            "Отозвать доступ, сменить пароль, проверить, какие письма "
            "открывались с этого адреса."
        ),
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
