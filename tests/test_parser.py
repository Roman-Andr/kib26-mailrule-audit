"""Parser tests: schema validation, type errors and limits."""

from __future__ import annotations

import json

import pytest

from app.model import ValidationError
from app.parser import load_export, parse_export, split_email
from tests.conftest import make_export, make_rule


def test_parses_minimal_export() -> None:
    mailbox = parse_export(make_export([make_rule()]), source="memory")
    assert mailbox.email == "user@pixel-smb.by"
    assert mailbox.domain == "pixel-smb.by"
    assert len(mailbox.rules) == 1
    assert mailbox.baseline.internal_domains == ("pixel-smb.by",)
    assert mailbox.source == "memory"


def test_missing_mailbox_is_reported() -> None:
    with pytest.raises(ValidationError, match="mailbox"):
        parse_export({"rules": []})


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(ValidationError, match="адрес"):
        parse_export(make_export([], email="not-an-email"))


def test_wrong_type_for_rules_is_reported() -> None:
    payload = make_export()
    payload["rules"] = {"R-1": {}}
    with pytest.raises(ValidationError, match="rules"):
        parse_export(payload)


def test_duplicate_rule_ids_are_rejected() -> None:
    payload = make_export([make_rule("R-1"), make_rule("R-1", "Второе")])
    with pytest.raises(ValidationError, match="повторяющийся"):
        parse_export(payload)


def test_bad_datetime_is_reported() -> None:
    payload = make_export([make_rule(created_at="вчера вечером")])
    with pytest.raises(ValidationError, match="дата"):
        parse_export(payload)


def test_forward_to_requires_valid_address() -> None:
    payload = make_export([make_rule(forward_to=["attacker@"])])
    with pytest.raises(ValidationError, match="forward_to"):
        parse_export(payload)


def test_too_many_rules_are_rejected() -> None:
    rules = [make_rule(f"R-{index}") for index in range(501)]
    with pytest.raises(ValidationError, match="больше допустимого"):
        parse_export(make_export(rules))


def test_oversized_file_is_rejected(tmp_path) -> None:
    path = tmp_path / "big.json"
    path.write_bytes(b"{" + b" " * (3 * 1024 * 1024) + b"}")
    with pytest.raises(ValidationError, match="слишком большой"):
        load_export(path)


def test_broken_json_is_reported(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{"rules": [}', encoding="utf-8")
    with pytest.raises(ValidationError, match="JSON"):
        load_export(path)


def test_missing_file_is_reported(tmp_path) -> None:
    with pytest.raises(ValidationError, match="не найден"):
        load_export(tmp_path / "nope.json")


def test_load_export_roundtrip(tmp_path) -> None:
    path = tmp_path / "case.json"
    path.write_text(json.dumps(make_export([make_rule()]), ensure_ascii=False), encoding="utf-8")
    mailbox = load_export(path)
    assert mailbox.source.endswith("case.json")


def test_split_email_normalises_case() -> None:
    assert split_email("Boss@Pixel-SMB.BY") == ("boss", "pixel-smb.by")


def test_unknown_fields_are_ignored() -> None:
    payload = make_export([make_rule()])
    payload["extra"] = {"any": "value"}
    mailbox = parse_export(payload)
    assert len(mailbox.rules) == 1
