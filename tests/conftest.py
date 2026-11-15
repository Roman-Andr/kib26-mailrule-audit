"""Shared fixtures for the test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "synthetic"


def make_rule(rule_id: str = "R-1", name: str = "Правило", **overrides: Any) -> dict[str, Any]:
    rule: dict[str, Any] = {
        "id": rule_id,
        "name": name,
        "enabled": True,
        "forward_to": [],
        "keep_copy": True,
        "mark_as_read": False,
        "delete_after": False,
        "conditions": {},
    }
    rule.update(overrides)
    return rule


def make_export(
    rules: list[dict[str, Any]] | None = None,
    sessions: list[dict[str, Any]] | None = None,
    delegations: list[dict[str, Any]] | None = None,
    email: str = "user@pixel-smb.by",
    internal: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "mailbox": {"email": email},
        "baseline": {
            "internal_domains": internal or ["pixel-smb.by"],
            "known_countries": ["BY", "RU"],
            "work_start_hour": 9,
            "work_end_hour": 18,
        },
        "rules": rules or [],
        "sessions": sessions or [],
        "delegations": delegations or [],
    }


@pytest.fixture()
def labels() -> dict[str, dict[str, str]]:
    return json.loads((DATA / "labels.json").read_text(encoding="utf-8"))


@pytest.fixture()
def data_dir() -> Path:
    return DATA
