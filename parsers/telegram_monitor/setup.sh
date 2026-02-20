#!/bin/bash
# Деплой мониторинга Telegram-канала.
# Запуск: bash parsers/telegram_monitor/setup.sh
# Или: PROJECT_DIR=/root/contentzavod SERVICE_USER=root bash parsers/telegram_monitor/setup.sh
#
# PROJECT_DIR — корень проекта (где blocks/, .env). По умолчанию: родитель parsers/.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$PARSERS_DIR/.." && pwd)}"
SERVICE_USER="${SERVICE_USER:-root}"

if [ ! -d "$PROJECT_DIR/blocks" ]; then
  echo "Ошибка: в $PROJECT_DIR нет blocks/. Задай PROJECT_DIR."
  exit 1
fi

cd "$PROJECT_DIR"

echo "=== Проект: $PROJECT_DIR, пользователь: $SERVICE_USER ==="

echo "=== 1. Зависимости (Telethon) ==="
if [ -d venv ]; then
  ./venv/bin/pip install -q telethon
else
  python3 -m venv venv
  ./venv/bin/pip install -q telethon python-dotenv
fi

echo "=== 2. Папка сессий ==="
mkdir -p storage/telegram_sessions

echo "=== 3. Проверка .env ==="
if [ ! -f .env ]; then
  echo "Создай .env (см. parsers/telegram_monitor/env.example)"
  exit 1
fi

echo "=== 4. Проверка сессии Telethon ==="
if [ ! -f storage/telegram_sessions/chat_reader.session ] && [ ! -f storage/telegram_sessions/chat_reader.session-journal ]; then
  echo "Сессия не найдена. Выполни один раз:"
  echo "  PYTHONPATH=$PROJECT_DIR $PROJECT_DIR/venv/bin/python -m blocks.telegram_chat_reader login"
  echo ""
  [ "${SKIP_SESSION_CHECK:-}" = "1" ] || exit 1
fi

echo "=== 5. Systemd-сервис ==="
sudo tee /etc/systemd/system/telegram-monitor.service > /dev/null << EOF
[Unit]
Description=КонтентЗавод — мониторинг Telegram-канала
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
ExecStart=$PROJECT_DIR/venv/bin/python -m blocks.telegram_chat_reader monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-monitor
sudo systemctl start telegram-monitor

echo ""
echo "=== Готово ==="
echo "Статус: sudo systemctl status telegram-monitor"
echo "Логи:   sudo journalctl -u telegram-monitor -f"
