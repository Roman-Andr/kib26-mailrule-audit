"""Scoring tests: weights, caps, bonuses and verdict thresholds."""

from __future__ import annotations

import pytest

from app.model import Finding
from app.parser import load_export, parse_export
from app.scoring import (
    CRITICAL_THRESHOLD,
    HIGH_THRESHOLD,
    MEDIUM_THRESHOLD,
    audit,
    mailbox_score,
    rule_score,
    verdict_for,
)
from tests.conftest import make_export, make_rule


def finding(weight: int, detector_id: str = "EXT_FORWARD") -> Finding:
    return Finding(
        detector_id=detector_id,
        rule_id="R-1",
        title="t",
        weight=weight,
        explanation="e",
        recommendation="r",
        evidence="ev",
    )


def test_rule_score_is_the_sum_of_weights() -> None:
    assert rule_score([finding(35), finding(25)]) == 60


def test_rule_score_is_capped_at_100() -> None:
    assert rule_score([finding(80), finding(60)]) == 100


def test_empty_mailbox_scores_zero() -> None:
    assert mailbox_score([], []) == 0


def test_mailbox_score_uses_the_worst_rule() -> None:
    assert mailbox_score([35, 10], []) == 35


def test_repeated_compromise_adds_a_bonus() -> None:
    assert mailbox_score([60, 45], []) == 70


def test_mailbox_score_is_capped_at_100() -> None:
    assert mailbox_score([100, 100, 100], []) == 100


def test_mailbox_findings_participate_in_the_score() -> None:
    assert mailbox_score([10], [finding(30, "EXT_DELEGATION")]) == 30


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0, "clean"),
        (1, "low"),
        (MEDIUM_THRESHOLD - 1, "low"),
        (MEDIUM_THRESHOLD, "medium"),
        (HIGH_THRESHOLD, "high"),
        (CRITICAL_THRESHOLD, "critical"),
        (100, "critical"),
    ],
)
def test_verdict_thresholds(score: int, level: str) -> None:
    assert verdict_for(score)[1] == level


def test_audit_builds_actions_for_forwarding() -> None:
    mailbox = parse_export(
        make_export([make_rule(forward_to=["collect@mail.ru"], keep_copy=False)])
    )
    report = audit(mailbox)
    assert report.score == 60
    assert report.level == "high"
    assert any("пересылк" in action.lower() for action in report.actions)


def test_audit_of_clean_mailbox() -> None:
    mailbox = parse_export(make_export([make_rule(move_to="Архив")]))
    report = audit(mailbox)
    assert report.score == 0
    assert report.level == "clean"
    assert report.rules_flagged == 0
    assert report.actions[0].startswith("Действий не требуется")


def test_audit_of_seeded_case() -> None:
    mailbox = load_export("data/synthetic/case-10.json")
    report = audit(mailbox)
    assert report.score == 100
    assert report.level == "critical"
    assert report.assessments[0].score == 100
    assert report.assessments[0].findings[0].weight == 35
