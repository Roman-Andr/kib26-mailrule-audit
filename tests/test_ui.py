"""Interface smoke tests: the page renders, switches language and theme."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "app" / "ui.py"


def open_app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60).run()


def test_app_renders_without_errors() -> None:
    at = open_app()
    assert not list(at.exception)
    assert at.title[0].value == "Аудитор правил почтового ящика"


def test_language_switch_changes_the_interface() -> None:
    at = open_app()
    at.radio[0].set_value("English").run()
    assert not list(at.exception)
    assert at.title[0].value == "Mailbox rule auditor"


def test_theme_switch_keeps_the_app_alive() -> None:
    at = open_app()
    at.radio[1].set_value("dark").run()
    assert not list(at.exception)
    at.radio[1].set_value("light").run()
    assert not list(at.exception)


def test_theme_choice_repaints_the_widgets() -> None:
    at = open_app()
    at.radio[1].set_value("dark").run()
    css = "".join(markdown.value for markdown in at.markdown)
    assert "--kib-app: #0d1117" in css
    assert 'data-testid="stFileUploaderDropzone"' in css


def test_case_selection_renders_a_verdict() -> None:
    at = open_app()
    at.selectbox[0].select("case-10.json").run()
    assert not list(at.exception)
    assert "Критично" in at.subheader[0].value
    labels = [metric.label for metric in at.metric]
    assert "Балл риска" in labels


def test_english_report_for_a_clean_case() -> None:
    at = open_app()
    at.radio[0].set_value("English").run()
    at.selectbox[0].select("case-13.json").run()
    assert not list(at.exception)
    assert "No signs of compromise" in at.subheader[0].value
