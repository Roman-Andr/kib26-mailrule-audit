"""Generate the synthetic dataset used for demos, tests and metrics.

Every case is deterministic and contains no real data: mailbox names,
addresses and rules are invented. Twelve cases reproduce patterns of account
takeover, eight cases are legitimate configurations that must stay clean.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"

INTERNAL = "pixel-smb.by"


def rule(
    rule_id: str,
    name: str,
    *,
    forward_to: list[str] | None = None,
    keep_copy: bool = True,
    move_to: str | None = None,
    mark_as_read: bool = False,
    delete_after: bool = False,
    created_at: str | None = None,
    session_id: str | None = None,
    subject_contains: list[str] | None = None,
    from_patterns: list[str] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    conditions: dict[str, Any] = {}
    if subject_contains:
        conditions["subject_contains"] = subject_contains
    if from_patterns:
        conditions["from"] = from_patterns
    item: dict[str, Any] = {
        "id": rule_id,
        "name": name,
        "enabled": enabled,
        "forward_to": forward_to or [],
        "keep_copy": keep_copy,
        "mark_as_read": mark_as_read,
        "delete_after": delete_after,
        "conditions": conditions,
    }
    if move_to:
        item["move_to"] = move_to
    if created_at:
        item["created_at"] = created_at
    if session_id:
        item["session_id"] = session_id
    return item


def session(session_id: str, started_at: str, country: str, *, mfa: bool = True) -> dict[str, Any]:
    return {
        "id": session_id,
        "started_at": started_at,
        "country": country,
        "ip": f"10.{sum(ord(ch) for ch in session_id) % 250}.{len(session_id)}.7",
        "mfa": mfa,
    }


def delegation(delegation_id: str, grantee: str, level: str = "read", created_at: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"id": delegation_id, "grantee": grantee, "level": level}
    if created_at:
        item["created_at"] = created_at
    return item


def export(
    email: str,
    rules: list[dict[str, Any]],
    *,
    sessions: list[dict[str, Any]] | None = None,
    delegations: list[dict[str, Any]] | None = None,
    internal_domains: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "mailbox": {"email": email, "domain": email.rsplit("@", 1)[-1]},
        "exported_at": "2026-11-14T09:00:00+03:00",
        "baseline": {
            "internal_domains": internal_domains or [INTERNAL],
            "known_countries": ["BY", "RU"],
            "work_start_hour": 9,
            "work_end_hour": 18,
        },
        "rules": rules,
        "sessions": sessions or [],
        "delegations": delegations or [],
    }


def build_cases() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}

    # 1. Classic takeover: external forward created at night from a foreign session.
    cases["case-01"] = export(
        f"accountant@{INTERNAL}",
        [
            rule("R-101", "Пересылка копий", forward_to=["pixel.smb.arch@gmail.com"],
                 created_at="2026-11-02T02:41:00+03:00", session_id="S-901"),
        ],
        sessions=[session("S-901", "2026-11-02T02:37:00+03:00", "NL", mfa=False)],
    )

    # 2. Forward-and-delete: the message never stays in the mailbox.
    cases["case-02"] = export(
        f"director@{INTERNAL}",
        [
            rule("R-102", "Копия для архива", forward_to=["box2026@mail.ru"],
                 keep_copy=False, delete_after=True,
                 created_at="2026-11-03T14:12:00+03:00"),
        ],
        sessions=[session("S-902", "2026-11-03T14:10:00+03:00", "BY")],
    )

    # 3. Hiding in a folder the owner never opens, combined with finance keywords.
    cases["case-03"] = export(
        f"office@{INTERNAL}",
        [
            rule("R-103", "Входящие — сортировка", move_to="Удаленные/RSS",
                 mark_as_read=True, subject_contains=["платеж", "счет"],
                 created_at="2026-11-04T11:20:00+03:00"),
        ],
    )

    # 4. Finance keyword filter that forwards payment notifications.
    cases["case-04"] = export(
        f"ceo@{INTERNAL}",
        [
            rule("R-104", "Уведомления банка", forward_to=["finance-help@proton.me"],
                 subject_contains=["платежное поручение"],
                 created_at="2026-11-05T10:05:00+03:00"),
        ],
    )

    # 5. Custom folder plus "mark as read": slow, quiet concealment.
    cases["case-05"] = export(
        f"bookkeeper@{INTERNAL}",
        [
            rule("R-105", "Документы", move_to="Отчеты/2026", mark_as_read=True,
                 subject_contains=["счет на оплату", "invoice"],
                 created_at="2026-11-06T16:40:00+03:00"),
        ],
    )

    # 6. Full mailbox access handed to an outside address.
    cases["case-06"] = export(
        f"chief@{INTERNAL}",
        [rule("R-106", "Правило отпуска", subject_contains=["отпуск"])],
        delegations=[delegation("D-601", "audit-service@outlook.com", "full_access",
                                "2026-11-06T21:15:00+03:00")],
    )

    # 7. Two rules: one malicious, one ordinary sorting rule.
    cases["case-07"] = export(
        f"manager@{INTERNAL}",
        [
            rule("R-107", "Сортировка рассылок", move_to="Рассылки", mark_as_read=True),
            rule("R-108", "Копия входящих", forward_to=["collect2026@yandex.ru"],
                 keep_copy=True, created_at="2026-11-07T09:30:00+03:00"),
        ],
    )

    # 8. Rule created at 02:40 — off-hours marker next to an external forward.
    cases["case-08"] = export(
        f"logist@{INTERNAL}",
        [
            rule("R-109", "Автоответ", forward_to=["orders@pixel-logistic.com.ua"],
                 created_at="2026-11-08T02:40:00+03:00"),
        ],
    )

    # 9. Rule created from a session without MFA in an unusual country.
    cases["case-09"] = export(
        f"hr@{INTERNAL}",
        [
            rule("R-110", "Резюме кандидатов", forward_to=["cv-inbox@yandex.ru"],
                 created_at="2026-11-09T12:10:00+03:00", session_id="S-903"),
        ],
        sessions=[session("S-903", "2026-11-09T12:05:00+03:00", "BR", mfa=False)],
    )

    # 10. Full set: bank keywords, external forward, no copy.
    cases["case-10"] = export(
        f"accountant@{INTERNAL}",
        [
            rule("R-111", "Банк", forward_to=["payments@mail.ru"], keep_copy=False,
                 subject_contains=["bank", "swift"], from_patterns=["*@bank*.by"],
                 created_at="2026-11-10T03:05:00+03:00", session_id="S-904"),
        ],
        sessions=[session("S-904", "2026-11-10T03:01:00+03:00", "TR", mfa=False)],
    )

    # 11. External delegation plus a hidden folder: two independent paths.
    cases["case-11"] = export(
        f"director@{INTERNAL}",
        [
            rule("R-112", "Архив переписки", move_to="Trash/Old", mark_as_read=True,
                 subject_contains=["договор"]),
        ],
        delegations=[delegation("D-602", "partner-check@yandex.com", "read",
                                "2026-11-10T18:45:00+03:00")],
    )

    # 12. Long rule list where only one rule is malicious.
    many = [
        rule(f"R-12{index}", f"Сортировка {index}", move_to=f"Клиенты/{index}",
             subject_contains=[f"тема {index}"])
        for index in range(1, 8)
    ]
    many.append(
        rule("R-129", "Резервная копия", forward_to=["backup-2026@mail.ru"],
             keep_copy=False, created_at="2026-11-11T23:50:00+03:00")
    )
    cases["case-12"] = export(f"support@{INTERNAL}", many)

    # 13. Auto-reply and newsletter sorting: no forwarding, no finance topics.
    cases["case-13"] = export(
        f"sales@{INTERNAL}",
        [
            rule("R-130", "Автоответ", subject_contains=["новый запрос"]),
            rule("R-131", "Рассылки", move_to="Рассылки", mark_as_read=True,
                 from_patterns=["*@news.example"]),
        ],
        sessions=[session("S-905", "2026-11-12T10:00:00+03:00", "BY")],
    )

    # 14. Forwarding inside the company only.
    cases["case-14"] = export(
        f"assistant@{INTERNAL}",
        [
            rule("R-132", "Копия руководителю", forward_to=[f"director@{INTERNAL}"],
                 keep_copy=True, created_at="2026-11-12T11:15:00+03:00"),
        ],
    )

    # 15. Rule created late in the evening by the administrator: low risk only.
    cases["case-15"] = export(
        f"sysadmin@{INTERNAL}",
        [
            rule("R-133", "Письма клиентов", move_to="Клиенты", created_at="2026-11-12T22:15:00+03:00"),
        ],
    )

    # 16. Delegation to a colleague inside the company.
    cases["case-16"] = export(
        f"director@{INTERNAL}",
        [rule("R-134", "Важное", move_to="Важное", subject_contains=["договор"])],
        delegations=[delegation("D-603", f"assistant@{INTERNAL}", "read")],
    )

    # 17. Finance filter that only marks messages, without moving or forwarding.
    cases["case-17"] = export(
        f"accountant@{INTERNAL}",
        [rule("R-135", "Контроль счетов", subject_contains=["счет", "invoice"])],
    )

    # 18. Foreign session with MFA and a harmless action.
    cases["case-18"] = export(
        f"manager@{INTERNAL}",
        [
            rule("R-136", "Архив", move_to="Архив", created_at="2026-11-13T15:30:00+03:00",
                 session_id="S-906"),
        ],
        sessions=[session("S-906", "2026-11-13T15:00:00+03:00", "PL", mfa=True)],
    )

    # 19. Large but legitimate configuration.
    bulk = [
        rule(f"R-14{index}", f"Папка {index}", move_to=f"Проекты/{index}",
             subject_contains=[f"проект {index}"])
        for index in range(1, 10)
    ]
    cases["case-19"] = export(f"pm@{INTERNAL}", bulk)

    # 20. Empty configuration: nothing to flag.
    cases["case-20"] = export(f"newbie@{INTERNAL}", [])

    return cases


LABELS = {
    "case-01": ("compromised", "внешняя пересылка из ночной сессии без MFA"),
    "case-02": ("compromised", "forward-and-delete на mail.ru"),
    "case-03": ("compromised", "сокрытие в папке «Удаленные/RSS» с финансовыми словами"),
    "case-04": ("compromised", "пересылка платёжных уведомлений"),
    "case-05": ("compromised", "скрытие счетов в пользовательской папке"),
    "case-06": ("compromised", "полный доступ к ящику для внешнего адреса"),
    "case-07": ("compromised", "внешняя пересылка рядом с обычной сортировкой"),
    "case-08": ("compromised", "правило создано в 02:40 и пересылает наружу"),
    "case-09": ("compromised", "сессия из Бразилии без MFA"),
    "case-10": ("compromised", "банковские слова, пересылка, без копии"),
    "case-11": ("compromised", "внешнее делегирование и скрытая папка"),
    "case-12": ("compromised", "одно вредоносное правило в длинном списке"),
    "case-13": ("clean", "автоответ и сортировка рассылок"),
    "case-14": ("clean", "пересылка внутри компании"),
    "case-15": ("clean", "правило создано вечером администратором"),
    "case-16": ("clean", "делегирование коллеге внутри компании"),
    "case-17": ("clean", "фильтр по счетам без пересылки и перемещения"),
    "case-18": ("clean", "зарубежная сессия с MFA"),
    "case-19": ("clean", "большая легитимная конфигурация"),
    "case-20": ("clean", "пустая конфигурация"),
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    labels: dict[str, dict[str, str]] = {}
    for name, payload in cases.items():
        path = OUT_DIR / f"{name}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        expected, note = LABELS[name]
        labels[name] = {"expected": expected, "note": note}
    with (OUT_DIR / "labels.json").open("w", encoding="utf-8") as handle:
        json.dump(labels, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"записано {len(cases)} конфигураций в {OUT_DIR}")


if __name__ == "__main__":
    main()
