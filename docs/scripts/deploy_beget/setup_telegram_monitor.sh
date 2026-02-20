#!/bin/bash
# Деплой мониторинга Telegram-канала на VPS.
# Запускать на сервере из корня проекта: bash docs/scripts/deploy_beget/setup_telegram_monitor.sh
#
# Перед запуском:
#   1. Подставь PROJECT_DIR и SERVICE_USER ниже
#   2. Убедись, что .env заполнен (TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN,
#      TELEGRAM_MONITOR_ALERT_CHAT_ID, TELEGRAM_MONITOR_HEADER)
#   3. Выполни один раз: python -m blocks.telegram_chat_reader login (интерактивно по телефону)
set -e

# ========== ПОДСТАВЬ СВОИ ЗНАЧЕНИЯ ==========
PROJECT_DIR="${PROJECT_DIR:-/root/contentzavod}"
SERVICE_USER="${SERVICE_USER:-root}"
# ============================================

if [ ! -d "$PROJECT_DIR/blocks" ]; then
  echo "Ошибка: в $PROJECT_DIR нет папки blocks/. Укажи PROJECT_DIR или запускай из корня проекта."
  exit 1
fi

cd "$PROJECT_DIR"

echo "=== 1. Установка зависимостей (Telethon) ==="
if [ -d venv ]; then
  source venv/bin/activate
  pip install -q telethon
  deactivate
else
  python3 -m venv venv
  source venv/bin/activate
  pip install -q telethon python-dotenv
  deactivate
fi

echo "=== 2. Папка для сессий Telethon ==="
mkdir -p storage/telegram_sessions

echo "=== 3. Проверка .env ==="
if [ ! -f .env ]; then
  echo "Создай .env с переменными:"
  echo "  TELEGRAM_API_ID, TELEGRAM_API_HASH"
  echo "  TELEGRAM_BOT_TOKEN"
  echo "  TELEGRAM_MONITOR_ENTITY=zakazyff"
  echo "  TELEGRAM_MONITOR_ALERT_CHAT_ID"
  echo "  TELEGRAM_MONITOR_HEADER=твой_заголовок"
  echo ""
  echo "Команда: nano $PROJECT_DIR/.env"
  exit 1
fi

echo "=== 4. Проверка авторизации Telethon ==="
if [ ! -f storage/telegram_sessions/chat_reader.session ] && [ ! -f storage/telegram_sessions/chat_reader.session-journal ]; then
  echo "Сессия Telethon не найдена. Выполни один раз (интерактивно):"
  echo "  cd $PROJECT_DIR && PYTHONPATH=$PROJECT_DIR $PROJECT_DIR/venv/bin/python -m blocks.telegram_chat_reader login"
  echo ""
  echo "Введи номер телефона и код из Telegram. После этого перезапусти: bash docs/scripts/deploy_beget/setup_telegram_monitor.sh"
  echo ""
  if [ "${SKIP_SESSION_CHECK:-}" != "1" ]; then
    echo "Чтобы установить сервис без сессии (запустить позже после login): SKIP_SESSION_CHECK=1 bash $0"
    exit 1
  fi
  echo "Продолжаем установку (SKIP_SESSION_CHECK=1). Не забудь выполнить login и перезапустить сервис."
fi

echo "=== 5. Установка systemd-сервиса ==="
SVC_FILE="/etc/systemd/system/telegram-monitor.service"
sudo tee "$SVC_FILE" > /dev/null << EOF
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

echo "Сервис записан в $SVC_FILE"
sudo systemctl daemon-reload
sudo systemctl enable telegram-monitor
sudo systemctl start telegram-monitor

echo ""
echo "=== Готово ==="
echo "Статус: sudo systemctl status telegram-monitor"
echo "Логи:   sudo journalctl -u telegram-monitor -f"
