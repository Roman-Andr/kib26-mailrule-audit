/**
 * KIB-26 «Пиксель» — выгрузка настроек Gmail в формат аудитора.
 *
 * Как запустить (браузер, без установки чего-либо):
 *   1. script.google.com → «Новый проект».
 *   2. Слева «Сервисы» → «+» → Gmail API → «Добавить».
 *   3. Вставить этот файл в Code.gs, сохранить.
 *   4. Запустить функцию exportMailboxRules и разрешить доступ (только чтение настроек).
 *   5. В логе появится ссылка на файл kib26-export-*.json в вашем Google Drive.
 *   6. Скачать файл и проверить: python -m app.cli --input kib26-export-*.json
 *
 * Скрипт только читает фильтры и метки. Он ничего не меняет и никуда не отправляет
 * данные: файл сохраняется в ваш собственный Drive.
 */
function exportMailboxRules() {
  if (typeof Gmail === 'undefined' || !Gmail.Users || !Gmail.Users.Settings) {
    throw new Error(
      'Не добавлен сервис Gmail API. Слева «Сервисы» → «+» → найдите Gmail API → ' +
      '«Добавить», сохраните проект и запустите снова.'
    );
  }

  var email = Session.getActiveUser().getEmail();
  var domain = email.split('@').pop();

  var labelNames = {};
  // В Gmail API метки живут в users.labels, а не в users.settings.labels.
  var labels = Gmail.Users.Labels.list('me').labels || [];
  labels.forEach(function (label) { labelNames[label.id] = label.name; });

  var filters = Gmail.Users.Settings.Filters.list('me').filter || [];
  var rules = filters.map(function (item, index) {
    var criteria = item.criteria || {};
    var action = item.action || {};
    var conditions = {};
    var keywords = [];

    if (criteria.from) { conditions.from = [criteria.from]; }
    if (criteria.to) { conditions.to = [criteria.to]; }
    if (criteria.subject) { keywords.push(criteria.subject); }
    if (criteria.query) {
      criteria.query.replace(/[()]/g, ' ').split(/\s+/).forEach(function (token) {
        var cleaned = token.replace(/^[-{}]+/, '').replace(/[{}]+$/, '');
        if (cleaned && ['OR', 'AND', 'NOT'].indexOf(cleaned.toUpperCase()) === -1) {
          keywords.push(cleaned);
        }
      });
    }
    if (keywords.length) { conditions.subject_contains = keywords; }
    if (criteria.hasAttachment) { conditions.has_attachment = true; }

    var removed = action.removeLabelIds || [];
    var added = (action.addLabelIds || []).map(function (id) { return labelNames[id] || id; });

    return {
      id: String(item.id || ('G-' + index)),
      name: 'Фильтр Gmail ' + index,
      enabled: true,
      forward_to: action.forward ? [action.forward] : [],
      keep_copy: removed.indexOf('INBOX') === -1,
      move_to: added.length ? added[0] : null,
      mark_as_read: removed.indexOf('UNREAD') !== -1,
      delete_after: false,
      conditions: conditions
    };
  });

  var payload = {
    mailbox: { email: email, domain: domain },
    exported_at: new Date().toISOString(),
    baseline: {
      internal_domains: [domain],
      known_countries: ['BY', 'RU'],
      work_start_hour: 9,
      work_end_hour: 18
    },
    rules: rules,
    sessions: [],
    delegations: [],
    source_note: 'Экспорт настроек Gmail: фильтры и метки. Сессии и делегирования ' +
      'недоступны в личном аккаунте Google, поэтому детекторы RISKY_SESSION и ' +
      'EXT_DELEGATION не сработают.'
  };

  var stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var file = DriveApp.createFile(
    'kib26-export-' + stamp + '.json',
    JSON.stringify(payload, null, 2),
    MimeType.PLAIN_TEXT
  );

  Logger.log('Правил выгружено: %s', rules.length);
  Logger.log('Файл: %s', file.getUrl());
  Logger.log('Скачайте файл и запустите: python -m app.cli --input kib26-export-%s.json', stamp);
  return file.getUrl();
}
