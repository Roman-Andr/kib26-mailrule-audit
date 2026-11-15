"""Quality metrics on the synthetic dataset.

These tests encode the acceptance criteria of the MVP: at least 18 correct
verdicts out of 20 cases, no more than one false positive and a report that is
built in under five seconds.
"""

from __future__ import annotations

import json
import time

import pytest

from app.parser import load_export
from app.report import render_markdown
from app.scoring import MEDIUM_THRESHOLD, audit
from tests.conftest import DATA

CASES = sorted(DATA.glob("case-*.json"))


def test_dataset_has_twenty_cases() -> None:
    assert len(CASES) == 20


def test_labels_cover_every_case() -> None:
    labels = json.loads((DATA / "labels.json").read_text(encoding="utf-8"))
    assert set(labels) == {path.stem for path in CASES}


@pytest.mark.parametrize("path", CASES, ids=[path.stem for path in CASES])
def test_report_is_built_quickly(path) -> None:
    started = time.perf_counter()
    report = audit(load_export(path))
    render_markdown(report)
    assert time.perf_counter() - started < 5.0


def test_accuracy_meets_the_threshold() -> None:
    labels = json.loads((DATA / "labels.json").read_text(encoding="utf-8"))
    correct = 0
    false_positives = 0
    false_negatives: list[str] = []
    for path in CASES:
        expected = labels[path.stem]["expected"]
        report = audit(load_export(path))
        predicted = "compromised" if report.score >= MEDIUM_THRESHOLD else "clean"
        if predicted == expected:
            correct += 1
        elif predicted == "compromised":
            false_positives += 1
        else:
            false_negatives.append(path.stem)
    assert correct >= 18, f"верных вердиктов {correct} из 20"
    assert false_positives <= 1, f"ложных срабатываний {false_positives}"
    assert not false_negatives, f"пропущенные инциденты: {false_negatives}"


def test_every_compromised_case_has_actions() -> None:
    labels = json.loads((DATA / "labels.json").read_text(encoding="utf-8"))
    for path in CASES:
        if labels[path.stem]["expected"] != "compromised":
            continue
        report = audit(load_export(path))
        assert report.actions
        assert not report.actions[0].startswith("Действий не требуется")
