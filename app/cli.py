"""Command line interface for the mailbox rule auditor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .i18n import DEFAULT_LANG, LANGS
from .parser import ValidationError, load_export
from .report import render_markdown, to_dict
from .scoring import audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kib26-audit",
        description="Аудит правил почтового ящика: поиск пересылки и сокрытия писем",
    )
    parser.add_argument("--input", required=True, help="JSON-файл экспорта")
    parser.add_argument(
        "--format", choices=("md", "json"), default="md", help="формат отчёта"
    )
    parser.add_argument("--out", help="файл для записи отчёта (по умолчанию stdout)")
    parser.add_argument(
        "--lang", choices=LANGS, default=DEFAULT_LANG, help="язык отчёта (ru/en)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="вернуть код 3, если найдены подозрительные правила",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        mailbox = load_export(args.input)
    except ValidationError as exc:
        print(f"ошибка: {exc}", file=sys.stderr)
        return 2

    report = audit(mailbox)
    if args.format == "json":
        payload = json.dumps(to_dict(report, args.lang), ensure_ascii=False, indent=2)
    else:
        payload = render_markdown(report, args.lang)

    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"отчёт сохранён: {args.out}")
    else:
        print(payload)

    if args.check and report.level != "clean":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
