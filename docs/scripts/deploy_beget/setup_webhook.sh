#!/bin/bash
# Установка и настройка GitHub webhook сервера
# Запускать на VPS из КОРНЯ проекта

set -e

PROJECT_DIR="/home/u123/contentzavod"
SERVICE_USER="u123"
WEBHOOK_PORT=3000

echo "=== Установка GitHub webhook сервера ==="

# 1. Копируем webhook сервер
if [ ! -f "$PROJECT_DIR/webhook_server.py" ]; then
    echo "Ошибка: webhook_server.py не найден. Сначала загрузите его на сервер."
    exit 1
fi

# 2. Устанавливаем права
chown $SERVICE_USER:$SERVICE_USER "$PROJECT_DIR/webhook_server.py"
chmod +x "$PROJECT_DIR/webhook_server.py"

# 3. Создаем директорию для логов
mkdir -p "$PROJECT_DIR/storage"
chown $SERVICE_USER:$SERVICE_USER "$PROJECT_DIR/storage"

# 4. Устанавливаем systemd сервис
SERVICE_FILE="/etc/systemd/system/github-webhook.service"
if [ -f "$PROJECT_DIR/github-webhook.service" ]; then
    cp "$PROJECT_DIR/github-webhook.service" "$SERVICE_FILE"
    echo "Сервис скопирован в $SERVICE_FILE"
else
    echo "Ошибка: github-webhook.service не найден"
    exit 1
fi

# 5. Заменяем пути в сервисе
sed -i "s|/home/u123/contentzavod|$PROJECT_DIR|g" "$SERVICE_FILE"
sed -i "s|User=u123|User=$SERVICE_USER|g" "$SERVICE_FILE"

# 6. Перезагружаем systemd и запускаем сервис
systemctl daemon-reload
systemctl enable github-webhook
systemctl start github-webhook

# 7. Проверяем статус
sleep 3
if systemctl is-active --quiet github-webhook; then
    echo "✅ Webhook сервер запущен успешно"
    echo "Проверка статуса: systemctl status github-webhook"
    echo "Логи: journalctl -u github-webhook -f"
    echo ""
    echo "=== Следующие шаги ==="
    echo "1. Установите GITHUB_WEBHOOK_SECRET в сервисе:"
    echo "   sudo systemctl edit github-webhook"
    echo "   Добавьте:"
    echo "   [Service]"
    echo "   Environment=GITHUB_WEBHOOK_SECRET=ваш-секретный-токен"
    echo ""
    echo "2. Настройте GitHub webhook:"
    echo "   URL: http://85.198.66.62:$WEBHOOK_PORT/webhook"
    echo "   Content type: application/json"
    echo "   Secret: тот же токен, что и в GITHUB_WEBHOOK_SECRET"
    echo "   Events: Push events"
    echo ""
    echo "3. Проверьте работу:"
    echo "   curl http://85.198.66.62:$WEBHOOK_PORT/health"
else
    echo "❌ Не удалось запустить webhook сервер"
    echo "Проверьте логи: journalctl -u github-webhook"
    exit 1
fi
