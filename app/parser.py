"""Parsing and validation of synthetic mailbox exports.

The parser is strict on purpose: an audit tool that silently ignores a
malformed rule would produce a false "clean" verdict, which is the worst
possible failure mode for the user. Every unexpected field type is reported
with its JSON path.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import (
    MAX_DELEGATIONS,
    MAX_RULES,
    MAX_SESSIONS,
    MAX_TEXT,
    Baseline,
    Delegation,
    Mailbox,
    Rule,
    RuleConditions,
    Session,
    ValidationError,
)

MAX_FILE_BYTES = 2 * 1024 * 1024

_EMAIL_RE = re.compile(r"^[^@\s<>]{1,120}@[A-Za-z0-9.-]{1,120}\.[A-Za-z]{2,24}$")
_LOCAL_TZ = timezone(timedelta(hours=3))


def _path(parent: str, key: str) -> str:
    return f"{parent}.{key}" if parent else key


def _as_dict(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{where}: ожидался объект")
    return value


def _as_list(value: Any, where: str, limit: int) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{where}: ожидался массив")
    if len(value) > limit:
        raise ValidationError(f"{where}: элементов больше допустимого ({limit})")
    return value


def _as_str(value: Any, where: str, required: bool = True, default: str = "") -> str:
    if value is None:
        if required:
            raise ValidationError(f"{where}: обязательное поле не заполнено")
        return default
    if not isinstance(value, str):
        raise ValidationError(f"{where}: ожидалась строка")
    text = value.strip()
    if len(text) > MAX_TEXT:
        raise ValidationError(f"{where}: строка длиннее {MAX_TEXT} символов")
    if required and not text:
        raise ValidationError(f"{where}: пустое значение")
    return text


def _as_bool(value: Any, where: str, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ValidationError(f"{where}: ожидалось true/false")


def _as_str_list(value: Any, where: str, limit: int = 50) -> tuple[str, ...]:
    if value is None:
        return ()
    items = _as_list(value, where, limit)
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(_as_str(item, f"{where}[{index}]", required=False))
    return tuple(item for item in result if item)


def _as_datetime(value: Any, where: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{where}: ожидалась строка с датой ISO 8601")
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(f"{where}: дата не разобрана ({exc})") from exc


def local_hour(moment: datetime) -> int:
    """Return the wall-clock hour in the company time zone."""
    if moment.tzinfo is None:
        return moment.hour
    return moment.astimezone(_LOCAL_TZ).hour


def weekday(moment: datetime) -> int:
    """Return the weekday in the company time zone (0 = Monday)."""
    if moment.tzinfo is None:
        return moment.weekday()
    return moment.astimezone(_LOCAL_TZ).weekday()


def split_email(address: str) -> tuple[str, str]:
    address = address.strip()
    if not _EMAIL_RE.match(address):
        raise ValidationError(f"адрес не распознан: {address[:60]!r}")
    local, domain = address.rsplit("@", 1)
    return local.lower(), domain.lower()


def _parse_conditions(raw: Any, where: str) -> RuleConditions:
    if raw is None:
        return RuleConditions()
    data = _as_dict(raw, where)
    return RuleConditions(
        from_patterns=_as_str_list(data.get("from"), _path(where, "from")),
        subject_keywords=_as_str_list(
            data.get("subject_contains"), _path(where, "subject_contains")
        ),
        recipients=_as_str_list(data.get("to"), _path(where, "to")),
        has_attachment=_as_bool(
            data.get("has_attachment"), _path(where, "has_attachment"), False
        ),
    )


def _parse_rule(raw: Any, index: int) -> Rule:
    where = f"rules[{index}]"
    data = _as_dict(raw, where)
    rule_id = _as_str(data.get("id"), _path(where, "id"))
    name = _as_str(data.get("name"), _path(where, "name"))
    forward_to = _as_str_list(data.get("forward_to"), _path(where, "forward_to"))
    for target in forward_to:
        try:
            split_email(target)
        except ValidationError as exc:
            raise ValidationError(f"{_path(where, 'forward_to')}: {exc}") from exc
    move_to = _as_str(data.get("move_to"), _path(where, "move_to"), required=False)
    return Rule(
        rule_id=rule_id,
        name=name,
        enabled=_as_bool(data.get("enabled"), _path(where, "enabled"), True),
        forward_to=forward_to,
        keep_copy=_as_bool(data.get("keep_copy"), _path(where, "keep_copy"), True),
        move_to=move_to or None,
        mark_as_read=_as_bool(
            data.get("mark_as_read"), _path(where, "mark_as_read"), False
        ),
        delete_after=_as_bool(
            data.get("delete_after"), _path(where, "delete_after"), False
        ),
        created_at=_as_datetime(data.get("created_at"), _path(where, "created_at")),
        session_id=_as_str(
            data.get("session_id"), _path(where, "session_id"), required=False
        )
        or None,
        conditions=_parse_conditions(data.get("conditions"), _path(where, "conditions")),
    )


def _parse_session(raw: Any, index: int) -> Session:
    where = f"sessions[{index}]"
    data = _as_dict(raw, where)
    return Session(
        session_id=_as_str(data.get("id"), _path(where, "id")),
        started_at=_as_datetime(data.get("started_at"), _path(where, "started_at")),
        country=_as_str(
            data.get("country"), _path(where, "country"), required=False
        ).upper()
        or None,
        ip=_as_str(data.get("ip"), _path(where, "ip"), required=False) or None,
        mfa=_as_bool(data.get("mfa"), _path(where, "mfa"), True),
    )


def _parse_delegation(raw: Any, index: int) -> Delegation:
    where = f"delegations[{index}]"
    data = _as_dict(raw, where)
    grantee = _as_str(data.get("grantee"), _path(where, "grantee"))
    split_email(grantee)
    return Delegation(
        delegation_id=_as_str(data.get("id"), _path(where, "id")),
        grantee=grantee,
        level=_as_str(
            data.get("level"), _path(where, "level"), required=False, default="read"
        )
        or "read",
        created_at=_as_datetime(data.get("created_at"), _path(where, "created_at")),
    )


def parse_export(data: Any, source: str = "") -> Mailbox:
    """Validate a decoded JSON export and build a :class:`Mailbox`."""
    root = _as_dict(data, "экспорт")
    mailbox_raw = _as_dict(root.get("mailbox"), "mailbox")
    email = _as_str(mailbox_raw.get("email"), "mailbox.email")
    _, domain = split_email(email)

    rules_raw = _as_list(root.get("rules"), "rules", MAX_RULES)
    rules: list[Rule] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(rules_raw):
        rule = _parse_rule(item, index)
        if rule.rule_id in seen_ids:
            raise ValidationError(f"rules[{index}].id: повторяющийся идентификатор")
        seen_ids.add(rule.rule_id)
        rules.append(rule)

    sessions_raw = _as_list(root.get("sessions", []), "sessions", MAX_SESSIONS)
    sessions = {}
    for index, item in enumerate(sessions_raw):
        session = _parse_session(item, index)
        sessions[session.session_id] = session

    delegations_raw = _as_list(root.get("delegations", []), "delegations", MAX_DELEGATIONS)
    delegations = tuple(
        _parse_delegation(item, index) for index, item in enumerate(delegations_raw)
    )

    baseline_raw = root.get("baseline")
    baseline_data = _as_dict(baseline_raw, "baseline") if baseline_raw else {}
    internal = _as_str_list(baseline_data.get("internal_domains"), "baseline.internal_domains")
    known = _as_str_list(baseline_data.get("known_countries"), "baseline.known_countries")
    baseline = Baseline(
        internal_domains=internal or (domain,),
        known_countries=known or ("BY", "RU"),
        work_start_hour=int(baseline_data.get("work_start_hour", 9) or 9),
        work_end_hour=int(baseline_data.get("work_end_hour", 18) or 18),
    )

    return Mailbox(
        email=email,
        domain=domain,
        rules=tuple(rules),
        sessions=sessions,
        delegations=delegations,
        baseline=baseline,
        exported_at=_as_datetime(root.get("exported_at"), "exported_at"),
        source=source,
    )


def load_export(path: str | Path) -> Mailbox:
    """Read an export from disk, enforcing a size limit."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ValidationError(f"файл не найден: {file_path}")
    size = file_path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValidationError(
            f"файл слишком большой: {size} байт (допустимо {MAX_FILE_BYTES})"
        )
    with file_path.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"JSON не разобран: {exc}") from exc
    return parse_export(data, source=str(file_path))
