"""Convert a Gmail settings dump into the export format of KIB-26.

Two ways to get the dump are described in ``docs/10-gmail-export.md``:
the Apps Script in ``scripts/gmail_export.gs`` or the Gmail API directly.
This script turns that dump into the JSON the auditor understands.

Only Gmail filters and labels are available for a personal account. Forwarding
addresses and delegates are not exposed by the consumer API, and sign-in
events are only available in Google Workspace admin reports, so the converter
leaves ``sessions`` and ``delegations`` empty and records what was missing.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

EXPORTED_AT_PLACEHOLDER = "1970-01-01T00:00:00+00:00"


def _label_names(labels: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    return {str(item.get("id")): str(item.get("name", "")) for item in labels}


def _split_query(query: str) -> list[str]:
    """Approximate a Gmail search query with plain keywords."""
    tokens = []
    for token in query.replace("(", " ").replace(")", " ").split():
        if token.upper() in {"OR", "AND", "NOT", "-"}:
            continue
        cleaned = token.strip("{}").lstrip("-")
        if cleaned and cleaned.upper() not in {"OR", "AND"}:
            tokens.append(cleaned)
    return tokens


def convert(dump: Mapping[str, Any], email: str = "") -> dict[str, Any]:
    """Build a KIB-26 export from a Gmail dump."""
    filters = dump.get("filters") or []
    labels = _label_names(dump.get("labels") or [])
    address = email or str(dump.get("email") or "user@gmail.com")
    domain = address.rsplit("@", 1)[-1]

    rules: list[dict[str, Any]] = []
    for index, item in enumerate(filters, start=1):
        criteria = item.get("criteria") or {}
        action = item.get("action") or {}
        conditions: dict[str, Any] = {}
        if criteria.get("from"):
            conditions["from"] = [str(criteria["from"])]
        if criteria.get("to"):
            conditions["to"] = [str(criteria["to"])]
        subject = str(criteria.get("subject") or "")
        query = str(criteria.get("query") or "")
        keywords = [subject] if subject else []
        keywords.extend(_split_query(query))
        if keywords:
            conditions["subject_contains"] = keywords
        if criteria.get("hasAttachment"):
            conditions["has_attachment"] = True

        forward_to = [str(action["forward"])] if action.get("forward") else []
        remove = [str(value) for value in action.get("removeLabelIds") or []]
        added = [labels.get(str(value), str(value)) for value in action.get("addLabelIds") or []]

        rules.append(
            {
                "id": str(item.get("id") or f"G-{index}"),
                "name": f"Фильтр Gmail {index}",
                "enabled": True,
                "forward_to": forward_to,
                "keep_copy": "INBOX" not in remove,
                "move_to": added[0] if added else None,
                "mark_as_read": "UNREAD" in remove,
                "delete_after": False,
                "conditions": conditions,
            }
        )

    return {
        "mailbox": {"email": address, "domain": domain},
        "exported_at": None,
        "baseline": {
            "internal_domains": [domain],
            "known_countries": ["BY", "RU"],
            "work_start_hour": 9,
            "work_end_hour": 18,
        },
        "rules": rules,
        "sessions": [],
        "delegations": [],
        "source_note": (
            "Экспорт настроек Gmail: фильтры и метки. Сессии и делегирования "
            "недоступны в личном аккаунте Google, поэтому детекторы RISKY_SESSION "
            "и EXT_DELEGATION не сработают."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Преобразовать дамп настроек Gmail в формат KIB-26"
    )
    parser.add_argument("--input", required=True, help="дамп filters+labels в JSON")
    parser.add_argument("--email", default="", help="адрес ящика, если его нет в дампе")
    parser.add_argument("--out", help="куда записать результат")
    args = parser.parse_args(argv)

    path = Path(args.input)
    if not path.is_file():
        print(f"ошибка: файл не найден: {path}", file=sys.stderr)
        return 2
    dump = json.loads(path.read_text(encoding="utf-8"))
    export = convert(dump, email=args.email)
    payload = json.dumps(export, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"готово: {args.out} ({len(export['rules'])} правил)")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
