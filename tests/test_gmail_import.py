"""Import tests: Gmail settings dump becomes a valid KIB-26 export."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.parser import parse_export
from app.scoring import audit
from scripts.gmail_to_export import convert

ROOT = Path(__file__).resolve().parent.parent

DUMP = {
    "email": "user@gmail.com",
    "labels": [{"id": "Label_1", "name": "Банк"}],
    "filters": [
        {
            "id": "F1",
            "criteria": {"from": "*@bank.by", "subject": "счёт"},
            "action": {"addLabelIds": ["Label_1"], "removeLabelIds": ["UNREAD"]},
        },
        {
            "id": "F2",
            "criteria": {"query": "(invoice OR payment)"},
            "action": {"forward": "collect@mail.ru", "removeLabelIds": ["INBOX"]},
        },
    ],
}


def test_filters_are_converted() -> None:
    export = convert(DUMP)
    assert export["mailbox"]["email"] == "user@gmail.com"
    assert len(export["rules"]) == 2
    first, second = export["rules"]
    assert first["move_to"] == "Банк"
    assert first["mark_as_read"] is True
    assert first["keep_copy"] is True
    assert first["conditions"]["from"] == ["*@bank.by"]
    assert second["forward_to"] == ["collect@mail.ru"]
    assert second["keep_copy"] is False
    assert "invoice" in second["conditions"]["subject_contains"]
    assert "payment" in second["conditions"]["subject_contains"]
    assert "OR" not in second["conditions"]["subject_contains"]


def test_converted_export_is_accepted_by_the_parser() -> None:
    mailbox = parse_export(convert(DUMP))
    report = audit(mailbox)
    assert mailbox.email == "user@gmail.com"
    assert report.rules_total == 2
    assert report.score >= 30
    assert any("пересылк" in action.lower() for action in report.actions)


def test_missing_sessions_are_reported_in_the_export() -> None:
    export = convert(DUMP)
    assert export["sessions"] == []
    assert export["delegations"] == []
    assert "RISKY_SESSION" in export["source_note"]


def test_empty_mailbox_is_valid() -> None:
    export = convert({"email": "empty@gmail.com", "filters": [], "labels": []})
    report = audit(parse_export(export))
    assert report.score == 0
    assert report.rules_total == 0


def test_cli_converts_a_dump(tmp_path) -> None:
    dump_path = tmp_path / "dump.json"
    dump_path.write_text(json.dumps(DUMP, ensure_ascii=False), encoding="utf-8")
    out_path = tmp_path / "export.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "gmail_to_export.py"),
            "--input",
            str(dump_path),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(payload["rules"]) == 2
