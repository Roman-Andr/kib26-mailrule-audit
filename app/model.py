"""Domain model for mailbox configuration exports.

The model is intentionally small and immutable: every object is parsed once,
validated by :mod:`app.parser` and then only read by detectors, scoring and
reporting. Nothing here performs I/O or network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

MAX_RULES = 500
MAX_SESSIONS = 2000
MAX_DELEGATIONS = 200
MAX_TEXT = 300

# Folders that are considered normal destinations: a message moved there is
# still visible to the owner, so moving alone is not treated as concealment.
VISIBLE_FOLDERS = (
    "входящие",
    "inbox",
    "архив",
    "archive",
    "важное",
    "important",
    "отправленные",
    "sent",
    "клиенты",
    "contracts",
    "договоры",
)

# Folder fragments that signal concealment: mail is hidden from the owner.
HIDING_FOLDER_MARKERS = (
    "удал",
    "корзин",
    "deleted",
    "trash",
    "rss",
    "спам",
    "spam",
    "junk",
    "temp",
    "врем",
    "old",
    "стары",
)

FINANCE_KEYWORDS = (
    "банк",
    "bank",
    "платеж",
    "платёж",
    "payment",
    "счет",
    "счёт",
    "invoice",
    "договор",
    "contract",
    "реквизит",
    "swift",
    "iban",
)


class ValidationError(ValueError):
    """Raised when an export does not match the expected schema."""


@dataclass(frozen=True)
class RuleConditions:
    """Condition part of a mail rule."""

    from_patterns: tuple[str, ...] = ()
    subject_keywords: tuple[str, ...] = ()
    recipients: tuple[str, ...] = ()
    has_attachment: bool = False


@dataclass(frozen=True)
class Rule:
    """A single mail rule (filter) configured in the mailbox."""

    rule_id: str
    name: str
    enabled: bool
    forward_to: tuple[str, ...] = ()
    keep_copy: bool = True
    move_to: str | None = None
    mark_as_read: bool = False
    delete_after: bool = False
    created_at: datetime | None = None
    session_id: str | None = None
    conditions: RuleConditions = RuleConditions()

    @property
    def forwards(self) -> bool:
        return bool(self.forward_to)

    @property
    def hides(self) -> bool:
        return bool(self.move_to) or self.delete_after


@dataclass(frozen=True)
class Session:
    """An authentication session that could have created a rule."""

    session_id: str
    started_at: datetime | None = None
    country: str | None = None
    ip: str | None = None
    mfa: bool = True


@dataclass(frozen=True)
class Delegation:
    """Access granted to another mailbox."""

    delegation_id: str
    grantee: str
    level: str = "read"
    created_at: datetime | None = None


@dataclass(frozen=True)
class Baseline:
    """What the administrator considers normal for this mailbox."""

    internal_domains: tuple[str, ...] = ()
    known_countries: tuple[str, ...] = ("BY", "RU")
    work_start_hour: int = 9
    work_end_hour: int = 18

    def is_work_hour(self, hour: int) -> bool:
        return self.work_start_hour <= hour < self.work_end_hour


@dataclass(frozen=True)
class Mailbox:
    """Parsed mailbox export."""

    email: str
    domain: str
    rules: tuple[Rule, ...] = ()
    sessions: Mapping[str, Session] = field(default_factory=dict)
    delegations: tuple[Delegation, ...] = ()
    baseline: Baseline = Baseline()
    exported_at: datetime | None = None
    source: str = ""

    def session(self, session_id: str | None) -> Session | None:
        if not session_id:
            return None
        return self.sessions.get(session_id)


@dataclass(frozen=True)
class Finding:
    """One detector hit.

    Presentation strings live in :mod:`app.i18n` and are resolved by
    ``detector_id`` when the report is rendered, so a finding stays language
    neutral.
    """

    detector_id: str
    rule_id: str
    weight: int
    evidence: str


@dataclass(frozen=True)
class RuleAssessment:
    """Aggregated verdict for a single rule."""

    rule_id: str
    rule_name: str
    score: int
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class AuditReport:
    """Final report for one mailbox export."""

    mailbox_email: str
    mailbox_domain: str
    generated_at: datetime
    rules_total: int
    rules_flagged: int
    score: int
    level: str
    assessments: tuple[RuleAssessment, ...]
    mailbox_findings: tuple[Finding, ...]
    action_keys: tuple[str, ...]
    source: str = ""
