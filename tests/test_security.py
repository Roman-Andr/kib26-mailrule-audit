"""Security tests for the MVP.

The product promises three properties: it never touches the network, it never
evaluates markup from the export, and it refuses oversized or malformed input.
These tests keep those promises honest.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from app.parser import load_export
from app.report import render_markdown
from app.scoring import audit
from tests.conftest import DATA

APP_DIR = Path(__file__).resolve().parent.parent / "app"


def test_audit_works_with_network_disabled(monkeypatch) -> None:
    def blocked(*args, **kwargs):
        raise AssertionError("приложение попыталось открыть сетевое соединение")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    report = audit(load_export(DATA / "case-10.json"))
    assert report.score == 100
    assert "Находки" in render_markdown(report)


@pytest.mark.parametrize("path", sorted(APP_DIR.glob("*.py")), ids=lambda p: p.name)
def test_modules_do_not_import_network_libraries(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    forbidden = ("import requests", "import urllib", "import http.client", "import httpx", "import socket")
    for pattern in forbidden:
        assert pattern not in source, f"{path.name} использует сеть: {pattern}"


@pytest.mark.parametrize("path", sorted(APP_DIR.glob("*.py")), ids=lambda p: p.name)
def test_modules_do_not_evaluate_code(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    for pattern in ("eval(", "exec(", "pickle.loads", "os.system"):
        assert pattern not in source, f"{path.name} содержит небезопасный вызов: {pattern}"


def test_rule_name_with_markup_is_neutralised() -> None:
    payload = {
        "mailbox": {"email": "user@pixel-smb.by"},
        "rules": [
            {
                "id": "R-1",
                "name": "<img src=x onerror=alert(1)>",
                "forward_to": ["x@mail.ru"],
            }
        ],
    }
    from app.parser import parse_export

    text = render_markdown(audit(parse_export(payload)))
    assert "<img" not in text
    assert "&lt;img" in text


def test_directory_instead_of_file_is_rejected(tmp_path) -> None:
    with pytest.raises(Exception):
        load_export(tmp_path)
