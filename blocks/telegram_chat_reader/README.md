# Telegram Chat Reader

Чтение истории сообщений из чатов и каналов Telegram через **Telethon** (MTProto API).

## Ограничения Bot API

Боты Telegram (Bot API) **не видят** историю чата — только новые сообщения после добавления бота. Для выгрузки истории нужен **пользовательский аккаунт** и Telethon.

## Настройка

### 1. Получить API_ID и API_HASH

1. Зайти на https://my.telegram.org/apps
2. Войти по номеру телефона
3. Создать приложение (любое название)
4. Скопировать **api_id** (число) и **api_hash** (строка)

### 2. Добавить в .env

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
```

### 3. Авторизоваться (один раз)

```bash
python -m blocks.telegram_chat_reader login
```

Ввести номер телефона (с кодом страны, например +79001234567), затем код из Telegram. Сессия сохранится в `storage/telegram_sessions/`.

### 4. Выгрузить историю

```bash
# Последние 100 сообщений (в консоль)
python -m blocks.telegram_chat_reader fetch zakazyff

# До 500 сообщений в JSON
python -m blocks.telegram_chat_reader fetch zakazyff -n 500 -o storage/chat_zakazyff.json

# Тот же чат по ссылке
python -m blocks.telegram_chat_reader fetch https://t.me/zakazyff -n 200 -o zakazyff_history.json
```

## Требования к чату

- **Публичный** канал/группа: достаточно знать username (zakazyff).
- **Приватный**: сначала присоединиться по приглашению в Telegram, затем использовать username или invite-ссылку.

Ваш аккаунт должен быть **участником** чата.

## Мониторинг новых сообщений

Скрипт следит за каналом, проверяет новые сообщения по заголовку (или через GRS AI) и при совпадении отправляет уведомление ботом в другой чат.

```bash
python -m blocks.telegram_chat_reader monitor
```

**Режим по заголовку** (без AI, быстрее):

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_MONITOR_HEADER` | Заголовок: если он есть в сообщении — отправить уведомление |
| `TELEGRAM_MONITOR_ENTITY` | Канал (по умолч. zakazyff) |
| `TELEGRAM_MONITOR_ALERT_CHAT_ID` | Куда слать (или `TELEGRAM_ALERT_CHAT_ID`) |
| `TELEGRAM_BOT_TOKEN` | Бот для отправки |

**Режим через GRS AI** (если `TELEGRAM_MONITOR_HEADER` не задан):

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_MONITOR_CATEGORY_PROMPT` | Промпт для AI |
| `GRS_AI_API_KEY` | Ключ GRS AI |

## MCP-инструмент

В MCP-сервере проекта доступен инструмент `telegram_chat_history` — он вызывает тот же код и возвращает сообщения в Cursor.

## Структура JSON

```json
{
  "entity": "zakazyff",
  "count": 50,
  "messages": [
    {
      "id": 123,
      "date": "2025-02-20T12:00:00",
      "text": "Текст сообщения",
      "sender_id": 123456789,
      "reply_to_msg_id": null,
      "views": 100,
      "has_media": false
    }
  ]
}
```
