# Telegram Monitor — деплой

Мониторинг канала (zakazyff и др.): новые сообщения с заголовком → уведомление в другой чат.

## Быстрый деплой (после git pull)

```bash
# На VPS из корня проекта
PROJECT_DIR=/root/contentzavod SERVICE_USER=root bash parsers/telegram_monitor/setup.sh
```

## Перед первым запуском

1. Заполни `.env` в корне проекта (см. `env.example`)
2. Выполни один раз: `PYTHONPATH=. ./venv/bin/python -m blocks.telegram_chat_reader login`

## Webhook

При push в main webhook перезапускает `telegram-monitor`. Убедись, что systemd-юнит установлен (setup.sh делает это).
