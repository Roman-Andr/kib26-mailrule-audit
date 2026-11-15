"""Translation tests: both languages must be complete and consistent."""

from __future__ import annotations

import pytest

from app import detectors, i18n
from app.parser import parse_export
from app.report import findings_rows, render_markdown, to_dict
from app.scoring import audit
from tests.conftest import make_export, make_rule


def build(**overrides):
    return audit(parse_export(make_export([make_rule(**overrides)])))


def test_every_detector_has_both_languages() -> None:
    ids = {
        "EXT_FORWARD",
        "FORWARD_NO_COPY",
        "HIDDEN_FOLDER",
        "FINANCE_TARGET",
        "OFF_HOURS_RULE",
        "RISKY_SESSION",
        "EXT_DELEGATION",
    }
    assert ids == set(i18n.DETECTORS)
    for detector_id, messages in i18n.DETECTORS.items():
        assert set(messages) == set(i18n.LANGS), detector_id
        for lang in i18n.LANGS:
            for field in ("title", "explanation", "recommendation"):
                assert messages[lang][field].strip(), f"{detector_id}.{lang}.{field}"


def test_detector_ids_match_the_code() -> None:
    source = detectors.__file__
    text = open(source, encoding="utf-8").read()
    for detector_id in i18n.DETECTORS:
        assert f'"{detector_id}"' in text, detector_id


def test_ui_and_report_keys_are_complete() -> None:
    assert set(i18n.UI["ru"]) == set(i18n.UI["en"])
    assert set(i18n.REPORT["ru"]) == set(i18n.REPORT["en"])
    assert set(i18n.VERDICTS["ru"]) == set(i18n.VERDICTS["en"])
    assert set(i18n.ACTIONS) >= {"none", "disable_forwarding", "revoke_delegation"}


def test_unknown_language_falls_back_to_russian() -> None:
    assert i18n.normalise("de") == "ru"
    assert i18n.normalise(None) == "ru"
    assert i18n.verdict_text("xx", "high") == "Высокий риск"


def test_report_is_translated() -> None:
    report = build(forward_to=["collect@mail.ru"], keep_copy=False)
    russian = render_markdown(report, "ru")
    english = render_markdown(report, "en")
    assert "Отчёт по правилам почтового ящика" in russian
    assert "Mailbox rule audit report" in english
    assert "Высокий риск" in russian
    assert "High risk" in english
    assert "Пересылка на внешний адрес" in russian
    assert "Forwarding to an external address" in english


def test_json_summary_carries_language() -> None:
    report = build(forward_to=["collect@mail.ru"], keep_copy=False)
    assert to_dict(report, "ru")["verdict"] == "Высокий риск"
    assert to_dict(report, "en")["verdict"] == "High risk"
    assert to_dict(report, "en")["lang"] == "en"


def test_findings_rows_follow_the_language() -> None:
    report = build(move_to="Trash", mark_as_read=True)
    assert findings_rows(report, "ru")[0]["fix"].startswith("Вернуть правило")
    assert findings_rows(report, "en")[0]["fix"].startswith("Move the rule")


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_actions_are_translated(lang: str) -> None:
    report = build(forward_to=["collect@mail.ru"], keep_copy=False)
    text = render_markdown(report, lang)
    first_action = i18n.action_text(lang, report.action_keys[0])
    assert first_action in text


def test_clean_report_in_both_languages() -> None:
    report = build(move_to="Архив")
    assert "Признаков захвата нет" in render_markdown(report, "ru")
    assert "No signs of compromise" in render_markdown(report, "en")
