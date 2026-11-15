"""Translations for the interface and the report.

Two languages are supported: Russian (default) and English. Detector texts,
verdicts, actions and report headings live here so that the engine stays free
of presentation strings and every message has exactly one source of truth.
"""

from __future__ import annotations

from typing import Final

LANGS: Final = ("ru", "en")
DEFAULT_LANG: Final = "ru"

LANG_LABELS: Final = {
    "ru": "Русский",
    "en": "English",
}

VERDICTS: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "clean": "Признаков захвата нет",
        "low": "Низкий риск",
        "medium": "Средний риск",
        "high": "Высокий риск",
        "critical": "Критично",
    },
    "en": {
        "clean": "No signs of compromise",
        "low": "Low risk",
        "medium": "Medium risk",
        "high": "High risk",
        "critical": "Critical",
    },
}

DETECTORS: Final[dict[str, dict[str, dict[str, str]]]] = {
    "EXT_FORWARD": {
        "ru": {
            "title": "Пересылка на внешний адрес",
            "explanation": (
                "Правило отправляет копии писем за пределы компании. Так выглядит "
                "типовой сбор переписки после захвата ящика."
            ),
            "recommendation": (
                "Проверить автора правила, отключить пересылку и сменить пароль "
                "ящика; проверить, не уходили ли письма за период действия правила."
            ),
        },
        "en": {
            "title": "Forwarding to an external address",
            "explanation": (
                "The rule sends copies of messages outside the company. This is the "
                "standard way to collect correspondence after a mailbox takeover."
            ),
            "recommendation": (
                "Check who created the rule, disable forwarding and change the mailbox "
                "password; review whether messages left during the rule's lifetime."
            ),
        },
    },
    "FORWARD_NO_COPY": {
        "ru": {
            "title": "Пересылка без сохранения копии",
            "explanation": (
                "Письмо пересылается наружу и не остаётся в ящике владельца: "
                "исчезновение следов переписки — признак сокрытия."
            ),
            "recommendation": (
                "Включить сохранение копии или удалить правило; сверить журнал "
                "отправленных сообщений за период действия."
            ),
        },
        "en": {
            "title": "Forwarding without keeping a copy",
            "explanation": (
                "The message is forwarded outside and does not stay in the owner's "
                "mailbox: disappearing traces are a sign of concealment."
            ),
            "recommendation": (
                "Enable keeping a copy or delete the rule; review the sent-items log "
                "for the period the rule was active."
            ),
        },
    },
    "HIDDEN_FOLDER": {
        "ru": {
            "title": "Сокрытие письма в папке",
            "explanation": (
                "Письма переносятся в папку, которую владелец не просматривает, "
                "часто с отметкой «прочитано». Уведомление о входе и переписка "
                "с банком пропадают из виду."
            ),
            "recommendation": (
                "Вернуть правило в «Входящие» или удалить его; проверить содержимое "
                "папки, куда переносились письма."
            ),
        },
        "en": {
            "title": "Messages hidden in a folder",
            "explanation": (
                "Messages are moved to a folder the owner does not read, often marked "
                "as read. Bank notifications and correspondence disappear from view."
            ),
            "recommendation": (
                "Move the rule back to Inbox or delete it; inspect the folder the "
                "messages were moved to."
            ),
        },
    },
    "FINANCE_TARGET": {
        "ru": {
            "title": "Фильтр по финансовым ключевым словам",
            "explanation": (
                "Правило нацелено на письма о платежах, счетах и договорах: именно их "
                "нужно скрыть, чтобы компания не заметила подготовку мошеннического "
                "перевода."
            ),
            "recommendation": (
                "Удалить правило и проверить, не менялись ли реквизиты контрагентов "
                "в переписке за период его действия."
            ),
        },
        "en": {
            "title": "Filter on financial keywords",
            "explanation": (
                "The rule targets payment, invoice and contract messages: these are "
                "exactly the messages an attacker hides to keep the company from "
                "noticing a fraudulent transfer."
            ),
            "recommendation": (
                "Delete the rule and check whether counterparty details changed in "
                "correspondence during its lifetime."
            ),
        },
    },
    "OFF_HOURS_RULE": {
        "ru": {
            "title": "Правило создано в нерабочее время",
            "explanation": (
                "Правило появилось вне рабочих часов или в выходной. Само по себе это "
                "не нарушение, но вместе с пересылкой или сокрытием указывает на "
                "действия злоумышленника."
            ),
            "recommendation": (
                "Уточнить у автора правила, когда и зачем оно создавалось; сверить с "
                "историей входов в ящик."
            ),
        },
        "en": {
            "title": "Rule created outside working hours",
            "explanation": (
                "The rule appeared outside working hours or on a weekend. On its own "
                "it is not a violation, but together with forwarding or concealment it "
                "points to an intruder."
            ),
            "recommendation": (
                "Ask the rule's author when and why it was created; compare with the "
                "mailbox sign-in history."
            ),
        },
    },
    "RISKY_SESSION": {
        "ru": {
            "title": "Правило создано из подозрительной сессии",
            "explanation": (
                "Правило появилось в сессии, которая не похожа на обычную работу "
                "сотрудника."
            ),
            "recommendation": (
                "Завершить все сессии ящика, включить MFA, проверить журнал входов за "
                "последние 30 дней."
            ),
        },
        "en": {
            "title": "Rule created from a suspicious session",
            "explanation": (
                "The rule appeared in a session that does not look like the employee's "
                "normal activity."
            ),
            "recommendation": (
                "End all mailbox sessions, enable MFA and review the sign-in log for "
                "the last 30 days."
            ),
        },
    },
    "EXT_DELEGATION": {
        "ru": {
            "title": "Доступ к ящику выдан внешнему адресу",
            "explanation": (
                "Ящик открыт постороннему адресу. Такой доступ не требует правил "
                "пересылки: злоумышленник читает переписку напрямую."
            ),
            "recommendation": (
                "Отозвать доступ, сменить пароль, проверить, какие письма открывались "
                "с этого адреса."
            ),
        },
        "en": {
            "title": "Mailbox access granted to an external address",
            "explanation": (
                "The mailbox is shared with an outside address. Such access needs no "
                "forwarding rule: the intruder reads correspondence directly."
            ),
            "recommendation": (
                "Revoke access, change the password and check which messages were "
                "opened from that address."
            ),
        },
    },
}

ACTIONS: Final[dict[str, dict[str, str]]] = {
    "revoke_delegation": {
        "ru": "Отозвать доступ к ящику, выданный внешнему адресу.",
        "en": "Revoke mailbox access granted to an external address.",
    },
    "disable_forwarding": {
        "ru": "Отключить правила пересылки и сохранить их описание как доказательство.",
        "en": "Disable forwarding rules and keep their description as evidence.",
    },
    "inspect_folders": {
        "ru": "Проверить папки, куда переносились письма, и вернуть их во «Входящие».",
        "en": "Check the folders messages were moved to and return them to Inbox.",
    },
    "reset_credentials": {
        "ru": "Сменить пароль, завершить все сессии и включить MFA.",
        "en": "Change the password, end all sessions and enable MFA.",
    },
    "check_payments": {
        "ru": "Сверить платежи и реквизиты контрагентов за период действия правил.",
        "en": "Reconcile payments and counterparty details for the period the rules were active.",
    },
    "none": {
        "ru": "Действий не требуется: подозрительных правил не найдено.",
        "en": "No action needed: no suspicious rules found.",
    },
}

REPORT: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "title": "# Отчёт по правилам почтового ящика",
        "mailbox": "Ящик",
        "date": "Дата отчёта",
        "source": "Источник",
        "rules": "Проверено правил",
        "rules_value": "{total}, с находками: {flagged}",
        "verdict": "## Вердикт",
        "verdict_line": "**{verdict}** — {score} из 100",
        "clean_note": (
            "Подозрительных правил и внешних доступов не найдено. Это не гарантия "
            "отсутствия взлома: проверяются только правила, сессии и делегирования "
            "из экспорта."
        ),
        "actions": "## Что делать в первую очередь",
        "findings": "## Находки по правилам",
        "col_priority": "Приоритет",
        "col_rule": "Правило",
        "col_finding": "Находка",
        "col_why": "Почему опасно",
        "col_fix": "Что делать",
        "access": "## Доступы к ящику",
        "scoring": "## Как считается оценка",
        "scoring_text": (
            "Каждая находка имеет вес: пересылка на внешний адрес — 35, пересылка "
            "без копии — 25, внешний доступ к ящику — 30, сокрытие в папке — 20, "
            "фильтр по финансам — 15, подозрительная сессия — 15, нерабочее "
            "время — 10. Балл правила — сумма весов (не больше 100). Итог — худшее "
            "правило плюс 10 за каждое дополнительное правило с баллом 40 и выше."
        ),
        "limits": "## Ограничения",
        "limits_text": (
            "Отчёт построен по выгрузке правил, сессий и делегирований. Он не видит "
            "правила, созданные вне почты, не проверяет содержимое писем и не "
            "заменяет журнал платежей. Решение о блокировке принимает человек."
        ),
        "access_line": "**{title}** — {evidence}. {explanation}",
    },
    "en": {
        "title": "# Mailbox rule audit report",
        "mailbox": "Mailbox",
        "date": "Report date",
        "source": "Source",
        "rules": "Rules checked",
        "rules_value": "{total}, with findings: {flagged}",
        "verdict": "## Verdict",
        "verdict_line": "**{verdict}** — {score} out of 100",
        "clean_note": (
            "No suspicious rules or external access found. This is not a guarantee "
            "that the mailbox is safe: only rules, sessions and delegations from the "
            "export are checked."
        ),
        "actions": "## First steps",
        "findings": "## Findings by rule",
        "col_priority": "Priority",
        "col_rule": "Rule",
        "col_finding": "Finding",
        "col_why": "Why it matters",
        "col_fix": "What to do",
        "access": "## Mailbox access",
        "scoring": "## How the score is calculated",
        "scoring_text": (
            "Every finding has a weight: external forwarding — 35, forwarding without "
            "a copy — 25, external mailbox access — 30, concealment in a folder — 20, "
            "financial keyword filter — 15, suspicious session — 15, off-hours — 10. "
            "A rule score is the sum of weights (capped at 100). The total is the worst "
            "rule plus 10 for each additional rule scoring 40 or more."
        ),
        "limits": "## Limitations",
        "limits_text": (
            "The report is built from an export of rules, sessions and delegations. It "
            "does not see rules created outside the mailbox, does not read message "
            "content and does not replace the payment ledger. A human makes the final "
            "call."
        ),
        "access_line": "**{title}** — {evidence}. {explanation}",
    },
}

UI: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "page_title": "Аудитор правил ящика",
        "app_title": "Аудитор правил почтового ящика",
        "caption": (
            "KIB-26 «Пиксель». Только синтетические данные: приложение не делает "
            "сетевых вызовов и не отправляет выгрузку никуда, кроме этой страницы."
        ),
        "sidebar_header": "Выгрузка",
        "select_example": "Синтетический пример",
        "select_placeholder": "— выберите пример —",
        "upload": "Или загрузите свой JSON",
        "how_it_works": "**Как это работает**",
        "how_it_works_text": (
            "1. Экспорт правил, сессий и делегирований.\n"
            "2. Семь детекторов ищут пересылку и сокрытие писем.\n"
            "3. Скор 0–100 и отчёт на понятном языке."
        ),
        "settings_header": "Оформление",
        "language": "Язык",
        "theme": "Тема",
        "theme_light": "Светлая",
        "theme_dark": "Тёмная",
        "theme_system": "Как в системе",
        "show_source": "Показать исходную выгрузку",
        "info_pick": "Выберите пример слева или загрузите JSON-экспорт правил ящика.",
        "error_json": "Файл не разобран",
        "error_validation": "Выгрузка не прошла проверку",
        "metric_score": "Балл риска",
        "metric_flagged": "Правил с находками",
        "metric_flagged_value": "из",
        "actions_header": "Что делать в первую очередь",
        "findings_header": "Находки по правилам",
        "access_header": "Доступы к ящику",
        "clean_success": (
            "Подозрительных правил не найдено. Проверяются только правила, сессии и "
            "делегирования из выгрузки."
        ),
        "download_md": "Скачать отчёт (Markdown)",
        "download_json": "Скачать отчёт (JSON)",
        "limits_header": "Ограничения",
        "limits_text": (
            "Отчёт построен по выгрузке правил, сессий и делегирований. Он не видит "
            "правила, созданные вне почты, не читает содержимое писем и не заменяет "
            "журнал платежей. Решение принимает человек."
        ),
        "footer": "Данные не покидают эту страницу.",
    },
    "en": {
        "page_title": "Mailbox rule auditor",
        "app_title": "Mailbox rule auditor",
        "caption": (
            "KIB-26 Pixel. Synthetic data only: the app makes no network calls and "
            "sends the export nowhere but this page."
        ),
        "sidebar_header": "Export",
        "select_example": "Synthetic example",
        "select_placeholder": "— pick an example —",
        "upload": "Or upload your own JSON",
        "how_it_works": "**How it works**",
        "how_it_works_text": (
            "1. An export of rules, sessions and delegations.\n"
            "2. Seven detectors look for forwarding and concealed messages.\n"
            "3. A 0–100 score and a report in plain language."
        ),
        "settings_header": "Appearance",
        "language": "Language",
        "theme": "Theme",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "theme_system": "Match system",
        "show_source": "Show the raw export",
        "info_pick": "Pick an example on the left or upload a mailbox rule export.",
        "error_json": "The file could not be parsed",
        "error_validation": "The export failed validation",
        "metric_score": "Risk score",
        "metric_flagged": "Rules with findings",
        "metric_flagged_value": "of",
        "actions_header": "First steps",
        "findings_header": "Findings by rule",
        "access_header": "Mailbox access",
        "clean_success": (
            "No suspicious rules found. Only rules, sessions and delegations from the "
            "export are checked."
        ),
        "download_md": "Download report (Markdown)",
        "download_json": "Download report (JSON)",
        "limits_header": "Limitations",
        "limits_text": (
            "The report is built from an export of rules, sessions and delegations. It "
            "does not see rules created outside the mailbox, does not read message "
            "content and does not replace the payment ledger. A human decides."
        ),
        "footer": "Data never leaves this page.",
    },
}


def normalise(lang: str | None) -> str:
    """Return a supported language code, falling back to the default."""
    code = (lang or DEFAULT_LANG).lower()[:2]
    return code if code in LANGS else DEFAULT_LANG


def ui(lang: str, key: str) -> str:
    """Return an interface string."""
    return UI[normalise(lang)][key]


def verdict_text(lang: str, level: str) -> str:
    """Return a human verdict for a machine level."""
    return VERDICTS[normalise(lang)].get(level, level)


def detector_text(lang: str, detector_id: str) -> dict[str, str]:
    """Return title, explanation and recommendation for a detector."""
    code = normalise(lang)
    messages = DETECTORS[detector_id][code]
    return messages


def action_text(lang: str, action_key: str) -> str:
    """Return a human action for a machine action key."""
    messages = ACTIONS.get(action_key)
    if not messages:
        return action_key
    return messages.get(normalise(lang), messages[DEFAULT_LANG])


def report_text(lang: str, key: str) -> str:
    """Return a report string."""
    return REPORT[normalise(lang)][key]
