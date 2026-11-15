# Аналоги и площадки запуска

Дата проверки — 15.11.2026. В матрице шесть облачных решений и два бесплатных подхода. Ячейки короткие; сегмент — оценка по прайсу, остальные факты — из официальных источников. Mimecast и Hornetsecurity не включены: критерий 4 по открытым источникам подтвердить не удалось.

## 1. Матрица аналогов

| Решение | 1. Категория и функция | 2. Сегмент | 3. Обнаружение | 4. Правила ящика | 5. Реагирование | 6. Интеграция | 7. Внедрение | 8. Лицензия и цена | 9. Данные | 10. Ограничения |
|---|---|---|---|---|---|---|---|---|---|---|
| Microsoft Defender for Office 365 | Защита почты M365 | МСБ до 300, крупнее | Сигнатуры, ML, алерты | Да: пересылка, скрытие | Авто-блок; правила вручную | Встроено; портал, PowerShell | Часы-дни; глобальный админ | $2/польз./мес, Plan 1 | Облако Microsoft 365 | Только M365; настройка алертов |
| Proofpoint Email Protection + ATO | Шлюз почты, модуль ATO | Средний и крупный | ML, threat intelligence | Да, модуль ATO | Автоудаление правил и приложений | API 48 ч или SEG | Дни; админ tenant | По запросу; модули | Облако или on-prem | Много модулей; ATO отдельно |
| Abnormal Security | Поведенческая AI-защита | Средний и крупный | Поведенческий AI, профиль нормы | Да: правила, пересылка | Авто-блок сессии | API к M365/Google | Минуты; согласие админа | По запросу | Облако Abnormal | Нет on-prem; только SaaS |
| Check Point Harmony Email & Collaboration | API-защита почты | МСБ и крупный | ThreatCloud AI, аномалии | Да: forward, delete-all | Авто-блок исходящих | API без смены MX | Минуты-часы; админ tenant | По запросу; пакеты | Облако Check Point | Ориентация на ИБ; тюнинг |
| Material Security | Защита Workspace/M365 | Средний бизнес и выше | AI-детект, поведение | Да, ATO Resilience | Авто-ремедиация писем | API/OAuth; без MX | Часы-дни; супер-админ | $4–6 + $3 ATO | Выделенный облачный инстанс | ATO — доплата; фокус на ИБ |
| Google Workspace, встроенные средства | Настройки и аудит Gmail | МСБ и средний | Журналы, политики | Частично: журнал, API | Вручную; отключение пересылки | Встроено; Gmail API | Сразу; супер-админ | Входит в тариф | Облако Google | Только Google; нет скора |
| Ручной чек-лист | Проверка без ПО | Любой, 10–50 | Экспертные признаки | Да, вручную | Вручную | Консоли админа | Часы; права админа | Бесплатно; время | Данные в tenant | Не масштабируется |
| PowerShell/API-скрипты | Свои проверки по API | Любой с IT-админом | Детерминированные проверки | Да: Get-InboxRule, Gmail API | Вручную или скриптом | PowerShell, Graph, Gmail API | Часы-дни; регистрация приложения | Бесплатно; лицензия почты | Локально; секреты у админа | Нет скоринга; своя поддержка |

## 2. Разбор решений

### Microsoft Defender for Office 365

Defender for Office 365 — облачная защита почты M365. Он оповещает о пересылке наружу и манипуляционным правилам: перенос в RSS, удаление писем, фильтры по словам вроде invoice; в расследовании видны New-InboxRule и скрытые правила через `Get-InboxRule -IncludeHidden`.[^1][^2][^3] Plan 1 — $2 за пользователя в месяц при годовой оплате, Business Premium ($22) включает его для компаний до 300 сотрудников.[^4] Это инструмент ИБ-специалиста, а не отчёт для директора, и только для M365.

### Proofpoint Email Protection и Account Takeover Protection

Proofpoint Core Email Protection — шлюз с API-подключением за 48 часов или через SEG.[^5] Модуль Account Takeover Protection видит изменения правил в M365, Google Workspace и Okta и умеет удалять вредоносные правила и отзывать приложения.[^5] Глубина близка к нашей задаче, но функции распределены по модулям, цена не публикуется, а для 10–50 человек нужен админ tenant. Простого отчёта для неспециалиста нет.

### Abnormal Security

Abnormal Security учит норму коммуникаций и ищет отклонения. Вендор заявляет корреляцию изменений правил, авто-пересылки и бокового фишинга, а сессию блокирует автоматически менее чем за шесть секунд.[^6] Подключение — API к M365 или Google Workspace, без смены MX, по обещанию вендора за минуты.[^6] Для МСБ 10–50 это платформа с ценой по запросу; она анализирует поток событий, а не разовый аудит экспорта.

### Check Point Harmony Email & Collaboration

Harmony Email & Collaboration — API-защита для M365 и Google Workspace с мониторингом или блокировкой без смены MX.[^7] В описании аномалий есть наши кейсы: пересылка на внешний адрес, «удалить все письма», перенос в подпапку; серьёзность зависит от условия.[^7] Для скомпрометированных аккаунтов есть авто-блок исходящих, но разбор остаётся аналитику. Цена по запросу, интерфейс для ИБ-команды — для 10–50 человек избыточна.

### Material Security

Material Security защищает Google Workspace и M365, добавляя контроль файлов, OAuth и захвата аккаунтов. В ATO Resilience заявлены подозрительные правила пересылки, аудит исторических чувствительных писем и honeypot-подход.[^8] Подключение — API и OAuth, без обязательной смены MX.[^8] Цены публичные: $4 за Essentials, $6 за Advanced, ATO — плюс $3 или $5 за пользователя в месяц.[^8] Но ATO — доплата, продукт ориентирован на ИБ-команды, а не на директора.

### Встроенные средства Google Workspace

Это настройки Gmail, журналы и API, а не отдельный продукт. Администратор может запретить авто-пересылку, увидеть события Gmail и выгрузить фильтры, адреса пересылки и делегатов через API.[^9] Этого хватает для ручного поиска, но нет единой картины по ящикам и риск-скора; security center — инструмент администратора, а не готовый аудит.[^9] Для нас это источник данных и минимум проверок, а не конкурент по отчёту.

### Ручной чек-лист

Бесплатный подход без ПО. Он опирается на процедуру Microsoft: проверить `ForwardingSmtpAddress` и `DeliverToMailboxAndForward`, затем `Get-InboxRule -IncludeHidden`, отдельно делегирования и события входа.[^3][^10] Плюсы — нулевая цена и реальный tenant; минусы — человеческий фактор и невозможность сравнить десятки ящиков. Это первый шаг, но не продукт.

### PowerShell и API-скрипты

`Get-InboxRule`, `Get-Mailbox` и `Get-MailboxPermission` для Exchange Online, `users.settings.filters`, `forwardingAddresses` и `delegates` для Gmail.[^10][^9][^3] Скрипт можно сделать воспроизводимым, но его придётся писать и поддерживать под каждый tenant, а результаты интерпретировать вручную. Секреты и права администратора — отдельный риск. Открытый ScubaGear проверяет политику пересылки tenant, но не правила отдельных ящиков.[^11] Наш продукт заменяет эти скрипты JSON-парсером и отчётом.

## 3. Сравнение с KIB-26 «Пиксель»

| Критерий | Аналоги | KIB-26 «Пиксель» |
|---|---|---|
| Цена | $2–6 за ящик в месяц, часто по запросу | 0 руб., учебный проект |
| Порог входа | Админ tenant, API-согласия, дни | JSON-файл, локальный запуск, минуты |
| Фокус на правилах ящика | Один из модулей платформы | Единственный фокус, 7 детекторов |
| Язык отчёта | Англоязычные интерфейсы, термины для ИБ | Русский, пояснения для неспециалиста |
| Работа без облака | Облако обязательно | Полностью офлайн, без вызовов |
| Требования к данным | Доступ к tenant и потоку писем | Синтетический JSON-экспорт |
| Реагирование | Авто-блокировки, удаление правил | Только рекомендации |
| Мониторинг | Непрерывный | Разовая проверка экспорта |

Наши сильные стороны — цена, офлайн-работа и язык отчёта. Но по нескольким пунктам мы проигрываем осознанно. Нет потокового мониторинга: мы видим снимок экспорта, а не новые правила в момент создания. Нет автоматического реагирования: только рекомендации, без удаления правил и блокировки сессий. Набор источников ограничен одной JSON-схемой; нативных коннекторов к M365 и Google Workspace нет. Кроме того, нет ML-профиля и корреляции с почтовым потоком.

## 4. Площадки для запуска

| Площадка | Аудитория | Формат | Что публикуем | Ожидаемый эффект | Риски |
|---|---|---|---|---|---|
| Habr[^12] | Инженеры, админы, ИБ | Статья 8–12 тыс. знаков | Кейс BEC, архитектура, пример | Обратная связь, переходы в репозиторий | Модерация рекламы |
| vc.ru[^13] | Предприниматели МСБ | Колонка 5–7 тыс. | Риск 10–50, чек-лист, демо | Запросы на пилот, отзывы бизнеса | Не ИБ; рекламный тон |
| Product Hunt[^14] | Международные ранние пользователи | Карточка и комментарий автора | Офлайн-аудит, скриншоты, демо | Видимость, отзывы | Мало трафика; английский |

План запуска:

1. Лендинг в README: проблема, GIF демо, синтетика, ограничения, лицензия.
2. Статья на Habr с техническим разбором; отвечать на комментарии 48 часов.
3. Карточка Product Hunt на английском с комментарием автора и бесплатным демо.
4. Колонка на vc.ru на языке бизнеса, без продаж.
5. Отзывы в issues, обновление README и roadmap, итоги через две недели.

## 5. Выводы

1. Берём у Microsoft связку «правило + событие создания + сессия и IP»: это ядро скоринга и объяснения.
2. Берём у Check Point и Material названия аномалий и логику «серьёзность зависит от условия»; добавляем делегирования и forward-and-delete.
3. Не делаем потоковый мониторинг, авто-реагирование, ML-профилирование и коннекторы к tenant: это отдельный продукт с другими правами и ценой.
4. Не собираем реальные письма и не делаем сетевых вызовов: только синтетика и экспорт правил.
5. Отличие — простой русский отчёт для человека без ИБ, работа офлайн и фокус только на правилах ящика.

## Источники

[^1]: Microsoft Learn. Alert classification for suspicious email forwarding activity. https://learn.microsoft.com/en-us/defender-xdr/alert-grading-playbook-email-forwarding
[^2]: Microsoft Learn. Alert classification for suspicious inbox manipulation rules. https://learn.microsoft.com/en-us/defender-xdr/alert-grading-playbook-inbox-manipulation-rules
[^3]: Microsoft Learn. Respond to a compromised cloud email account. https://learn.microsoft.com/en-us/defender-office-365/responding-to-a-compromised-email-account
[^4]: Microsoft. Microsoft 365 security pricing for business. https://www.microsoft.com/en-us/security/small-medium-business
[^5]: Proofpoint. Core Email Protection. https://www.proofpoint.com/us/products/email-protection ; Account Takeover Protection. https://www.proofpoint.com/us/products/account-takeover-protection
[^6]: Abnormal. Prevent Account Takeover. https://abnormal.ai/solutions/prevent-account-takeover ; Platform overview. https://abnormal.ai/platform/overview
[^7]: Check Point. Email Security. https://www.checkpoint.com/harmony/email-security/ ; Suspected Anomalies. https://sc1.checkpoint.com/documents/Harmony_Email_and_Collaboration/Email_Security/Admin_Guide/Topics/anomaly-detection/suspected-anomalies.html ; Critical Anomalies. https://sc1.checkpoint.com/documents/Harmony_Email_and_Collaboration/Email_Security/Admin_Guide/Topics/anomaly-detection/supported-anomalies.html
[^8]: Material Security. Pricing. https://material.security/pricing ; Email Identity Protection. https://docs.material.security/email-protections/email-identity-protection.md ; Connect & Sync. https://docs.material.security/getting-started/deployment-guides/your-first-30-days/1-connect-and-sync.md
[^9]: Google. Let users automatically forward their own Gmail emails. https://support.google.com/a/answer/14724207 ; Gmail Activity Events. https://developers.google.com/workspace/admin/reports/v1/appendix/activity/gmail ; users.settings.filters. https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.filters ; users.settings.delegates. https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.delegates ; users.settings.forwardingAddresses. https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.forwardingAddresses ; About the security center. https://knowledge.workspace.google.com/admin/security/about-the-security-center
[^10]: Microsoft Learn. Get-InboxRule. https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-inboxrule ; Get-MailboxPermission. https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-mailboxpermission
[^11]: CISA ScubaGear. Sample Exchange Online report. https://github.com/cisagov/ScubaGear/blob/main/PowerShell/ScubaGear/Sample-Reports/IndividualReports/EXOReport.html ; репозиторий. https://github.com/cisagov/ScubaGear
[^12]: Habr. Правила сайта. https://habr.com/ru/docs/help/rules/
[^13]: vc.ru. https://vc.ru/
[^14]: Product Hunt. Launch. https://www.producthunt.com/launch
