"""Detector tests: each rule pattern must fire once and only when relevant."""

from __future__ import annotations

from app import detectors
from app.parser import parse_export
from tests.conftest import make_export, make_rule


def mailbox(**kwargs):
    return parse_export(make_export(**kwargs))


def test_external_forward_detected() -> None:
    mb = mailbox(rules=[make_rule(forward_to=["collect@mail.ru"])])
    finding = detectors.detect_external_forward(mb, mb.rules[0])
    assert finding is not None
    assert finding.weight == 35
    assert "collect@mail.ru" in finding.evidence


def test_internal_forward_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(forward_to=["director@pixel-smb.by"])])
    assert detectors.detect_external_forward(mb, mb.rules[0]) is None


def test_forward_without_copy_detected() -> None:
    mb = mailbox(rules=[make_rule(forward_to=["collect@mail.ru"], keep_copy=False)])
    finding = detectors.detect_forward_without_copy(mb, mb.rules[0])
    assert finding is not None
    assert finding.weight == 25


def test_forward_with_copy_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(forward_to=["collect@mail.ru"], keep_copy=True)])
    assert detectors.detect_forward_without_copy(mb, mb.rules[0]) is None


def test_rule_without_forward_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(move_to="Клиенты")])
    assert detectors.detect_forward_without_copy(mb, mb.rules[0]) is None


def test_hidden_folder_detected() -> None:
    mb = mailbox(rules=[make_rule(move_to="Удаленные/RSS", mark_as_read=True)])
    finding = detectors.detect_hidden_folder(mb, mb.rules[0])
    assert finding is not None
    assert finding.weight == 20


def test_visible_folder_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(move_to="Архив", mark_as_read=True)])
    assert detectors.detect_hidden_folder(mb, mb.rules[0]) is None


def test_custom_folder_with_finance_words_is_flagged() -> None:
    mb = mailbox(
        rules=[
            make_rule(
                move_to="Отчеты/2026",
                mark_as_read=True,
                conditions={"subject_contains": ["счет на оплату"]},
            )
        ]
    )
    assert detectors.detect_hidden_folder(mb, mb.rules[0]) is not None


def test_custom_folder_without_finance_words_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(move_to="Проекты", mark_as_read=True)])
    assert detectors.detect_hidden_folder(mb, mb.rules[0]) is None


def test_finance_target_detected() -> None:
    mb = mailbox(
        rules=[
            make_rule(
                forward_to=["x@mail.ru"], conditions={"subject_contains": ["платеж"]}
            )
        ]
    )
    finding = detectors.detect_finance_target(mb, mb.rules[0])
    assert finding is not None
    assert finding.weight == 15


def test_finance_filter_without_action_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(conditions={"subject_contains": ["invoice"]})])
    assert detectors.detect_finance_target(mb, mb.rules[0]) is None


def test_off_hours_rule_detected() -> None:
    mb = mailbox(rules=[make_rule(created_at="2026-11-03T02:40:00+03:00")])
    assert detectors.detect_off_hours_rule(mb, mb.rules[0]) is not None


def test_work_hours_rule_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(created_at="2026-11-03T14:00:00+03:00")])
    assert detectors.detect_off_hours_rule(mb, mb.rules[0]) is None


def test_risky_session_without_mfa() -> None:
    mb = mailbox(
        rules=[make_rule(session_id="S-1")],
        sessions=[{"id": "S-1", "started_at": "2026-11-03T10:00:00+03:00", "country": "BY", "mfa": False}],
    )
    finding = detectors.detect_risky_session(mb, mb.rules[0])
    assert finding is not None
    assert "без MFA" in finding.evidence


def test_risky_session_from_unknown_country() -> None:
    mb = mailbox(
        rules=[make_rule(session_id="S-2")],
        sessions=[{"id": "S-2", "started_at": "2026-11-03T10:00:00+03:00", "country": "BR", "mfa": True}],
    )
    assert detectors.detect_risky_session(mb, mb.rules[0]) is not None


def test_normal_session_is_not_flagged() -> None:
    mb = mailbox(
        rules=[make_rule(session_id="S-3")],
        sessions=[{"id": "S-3", "started_at": "2026-11-03T10:00:00+03:00", "country": "BY", "mfa": True}],
    )
    assert detectors.detect_risky_session(mb, mb.rules[0]) is None


def test_missing_session_is_not_flagged() -> None:
    mb = mailbox(rules=[make_rule(session_id="S-404")])
    assert detectors.detect_risky_session(mb, mb.rules[0]) is None


def test_external_delegation_detected() -> None:
    mb = mailbox(delegations=[{"id": "D-1", "grantee": "audit@outlook.com", "level": "full_access"}])
    assert detectors.detect_external_delegation(mb, mb.delegations[0]) is not None


def test_internal_delegation_is_not_flagged() -> None:
    mb = mailbox(delegations=[{"id": "D-2", "grantee": "assistant@pixel-smb.by", "level": "read"}])
    assert detectors.detect_external_delegation(mb, mb.delegations[0]) is None


def test_analyze_groups_findings_by_rule() -> None:
    mb = mailbox(
        rules=[
            make_rule("R-1", "Пересылка", forward_to=["x@mail.ru"], keep_copy=False),
            make_rule("R-2", "Сортировка", move_to="Рассылки"),
        ]
    )
    per_rule, mailbox_findings = detectors.analyze(mb)
    assert set(per_rule) == {"R-1"}
    assert len(per_rule["R-1"]) == 2
    assert mailbox_findings == []
