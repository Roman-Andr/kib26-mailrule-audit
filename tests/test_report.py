"""Report tests: structure, escaping and machine-readable output."""

from __future__ import annotations

import json

from app.parser import parse_export
from app.report import priority_for, render_markdown, to_dict
from app.scoring import audit
from tests.conftest import make_export, make_rule


def build(name: str = "Правило", **overrides):
    return audit(parse_export(make_export([make_rule(name=name, **overrides)])))


def test_markdown_contains_required_sections() -> None:
    text = render_markdown(build(forward_to=["collect@mail.ru"]))
    for heading in ("# Отчёт", "## Вердикт", "## Что делать", "## Находки по правилам", "## Ограничения"):
        assert heading in text


def test_clean_report_explains_itself() -> None:
    text = render_markdown(build(move_to="Архив"))
    assert "Признаков захвата нет" in text
    assert "Подозрительных правил и внешних доступов не найдено" in text


def test_pipe_in_rule_name_cannot_break_the_table() -> None:
    text = render_markdown(build("Пересылка | копия", forward_to=["x@mail.ru"]))
    assert "Пересылка \\| копия" in text


def test_html_is_escaped() -> None:
    text = render_markdown(build("<script>alert(1)</script>", move_to="Trash"))
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


def test_backticks_are_neutralised() -> None:
    text = render_markdown(build("`rm -rf`", move_to="Trash"))
    assert "`rm -rf`" not in text


def test_priority_boundaries() -> None:
    assert priority_for(100) == "P1"
    assert priority_for(85) == "P1"
    assert priority_for(84) == "P2"
    assert priority_for(60) == "P2"
    assert priority_for(59) == "P3"
    assert priority_for(40) == "P3"
    assert priority_for(39) == "P4"


def test_json_summary_is_serialisable() -> None:
    payload = to_dict(build(forward_to=["collect@mail.ru"], keep_copy=False))
    text = json.dumps(payload, ensure_ascii=False)
    assert "EXT_FORWARD" in text
    assert payload["score"] == 60
    assert payload["rules"][0]["priority"] == "P2"
    assert payload["rules"][0]["id"] == "R-1"
