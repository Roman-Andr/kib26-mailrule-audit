# Как выгрузить свой почтовый ящик в JSON

Документ для демонстрации на реальном ящике. Есть три пути: ручной (быстро,
без кода), автоматический через Google Apps Script (2–3 минуты) и
административный для Google Workspace / Microsoft 365.

Правило безопасности: файл с реальными настройками — это внутренний документ.
Складывайте его в `data/real/` (каталог в `.gitignore`), не коммитьте и не
загружайте в облачную демо-версию приложения.

## Вариант 1. Руками, без кода

Подходит, если фильтров немного (до 5–7), а на демо нужно показать сам принцип.

1. Открыть Gmail → шестерёнка → **«Все настройки»**.
2. Вкладка **«Пересылка и POP/IMAP»**: посмотреть, включена ли пересылка и на
   какой адрес (блок «Пересылка»).
3. Вкладка **«Фильтры и заблокированные адреса»**: для каждого фильтра видно
   условия и действия.
4. Перенести в JSON по шаблону ниже — по одному объекту в `rules` на каждый
   фильтр.

```json
{
  "mailbox": { "email": "you@gmail.com" },
  "baseline": {
    "internal_domains": ["gmail.com"],
    "known_countries": ["BY", "RU"],
    "work_start_hour": 9,
    "work_end_hour": 18
  },
  "rules": [
    {
      "id": "F-1",
      "name": "Письма от банка",
      "enabled": true,
      "forward_to": ["someone@example.com"],
      "keep_copy": true,
      "move_to": "Банк",
      "mark_as_read": true,
      "delete_after": false,
      "conditions": { "subject_contains": ["счёт"], "from": ["*@bank.by"] }
    }
  ],
  "sessions": [],
  "delegations": []
}
```

5. Проверить: `python -m app.cli --input data/real/my-mailbox.json`.

Соответствие полей Gmail и JSON:

| В Gmail | В JSON |
|---------|--------|
| Фильтр «От» | `conditions.from` |
| Фильтр «Кому» | `conditions.to` |
| Фильтр «Тема» | `conditions.subject_contains` |
| Фильтр «Содержит слова» | `conditions.subject_contains` |
| Фильтр «Есть вложение» | `conditions.has_attachment` |
| Действие «Переслать по адресу» | `forward_to` (массив) |
| Действие «Применить метку» | `move_to` (имя метки) |
| Действие «Не помещать во «Входящие»» | `keep_copy: false` |
| Действие «Пометить как прочитанное» | `mark_as_read: true` |
| Действие «Удалить» | `delete_after: true` |

## Вариант 2. Автоматически, Google Apps Script

Ничего устанавливать не нужно, всё в браузере.

1. Открыть [script.google.com](https://script.google.com) → **«Новый проект»**.
2. Слева **«Сервисы»** → «+» → найти **Gmail API** → **«Добавить»**.
3. Скопировать в `Code.gs` содержимое `scripts/gmail_export.gs` из репозитория,
   сохранить.
4. Выбрать функцию `exportMailboxRules` → **«Выполнить»**. Google попросит
   разрешение на чтение настроек Gmail — это единственное право, которое
   запрашивает скрипт; отправлять письма или менять фильтры он не может.
5. В логе появятся две строки: сколько правил выгружено и ссылка на файл
   `kib26-export-ГГГГ-ММ-ДД.json` в вашем Google Drive.
6. Скачать файл, положить в `data/real/` и запустить:

```bash
python -m app.cli --input data/real/kib26-export-2026-11-15.json
```

Скрипт читает фильтры через `Gmail.Users.Settings.Filters.list` и метки через
`Gmail.Users.Labels.list` (в Gmail API метки лежат в `users.labels`, а не в
`users.settings.labels` — на этом легко споткнуться), переводит их в нашу схему и
сохраняет JSON в ваш Drive. Данные никуда не отправляются.

### Если скрипт упал

| Ошибка | Причина | Что сделать |
|--------|---------|-------------|
| `Cannot read properties of undefined (reading 'list')` | не добавлен сервис Gmail API или вызов идёт к `Settings.Labels` | «Сервисы» → «+» → Gmail API → «Добавить»; в коде должно быть `Gmail.Users.Labels.list('me')` |
| `Authorization is required to perform that action` | не выданы разрешения | запустить функцию заново и подтвердить доступ в окне согласия |
| `Google hasn't verified this app` | скрипт ваш собственный, проверка Google не проводилась | «Дополнительные настройки» → «Перейти к проекту (небезопасно)» — это нормально для личного скрипта |
| `Cannot read properties of null (reading 'filter')` | сервис вернул `null`: фильтров нет либо ответ пустой | обновить скрипт из репозитория (добавлена проверка на `null`) или вручную: `var r = Gmail.Users.Settings.Filters.list('me') \|\| {}; var filters = r.filter \|\| [];` |
| `Правил выгружено: 0` | в ящике нет фильтров | создать любой фильтр в настройках Gmail и повторить |

### Если хочется через Gmail API напрямую

Любой способ получить два массива — `filters` и `labels` — и сохранить их в
файл вида `{"email": "...", "filters": [...], "labels": [...]}`. Дальше
конвертер:

```bash
python scripts/gmail_to_export.py --input data/real/gmail-dump.json \
    --email you@gmail.com --out data/real/my-mailbox.json
```

## Вариант 3. Google Workspace (администратор)

В рабочем аккаунте доступно больше данных:

| Что | Откуда |
|-----|--------|
| Фильтры всех ящиков | Gmail API `users.settings.filters.list` под сервисным аккаунтом с делегированием |
| Адреса пересылки | `users.settings.forwardingAddresses.list` |
| Делегаты (общий доступ к ящику) | `users.settings.delegates.list` |
| Входы и сессии | Admin SDK Reports API, `gmail` activity, `login` activity |

Из этих выгрузок собирается полный JSON, включая `sessions` — тогда работают
все семь детекторов. Для личного `@gmail.com` сессии и делегаты недоступны:
конвертер оставляет массивы пустыми, а отчёт честно пишет, какие детекторы не
могли сработать.

## Вариант 4. Microsoft 365

```powershell
Connect-ExchangeOnline
Get-InboxRule -Mailbox user@firma.ru -IncludeHidden |
    Select-Object Name, Enabled, Description, ForwardTo, RedirectTo
Get-Mailbox user@firma.ru | Select-Object ForwardingSmtpAddress, DeliverToMailboxAndForward
Get-MailboxPermission user@firma.ru | Where-Object { $_.User -notlike "NT AUTHORITY*" }
```

Входы — журнал входов Entra ID. Формат PowerShell отличается от нашего,
поэтому нужен конвертер; в MVP он не реализован и вынесен в планы после
защиты.

## Что важно проговорить на демо

1. Мы выгружаем **настройки**, а не письма: содержимое переписки приложение не
   видит.
2. На личном ящике большая часть детекторов молчит не потому, что «всё
   хорошо», а потому что нет данных о сессиях и делегированиях — отчёт это
   показывает.
3. Реальный файл — только локально. В облачной демо-версии работаем с
   `data/synthetic/`, там вымышленные адреса.

## Быстрая проверка, что всё сошлось

```bash
python -m app.cli --input data/real/my-mailbox.json            # отчёт в терминал
python -m app.cli --input data/real/my-mailbox.json --format json --out /tmp/r.json
pytest -q                                                        # 123 теста, движок не сломан
```
