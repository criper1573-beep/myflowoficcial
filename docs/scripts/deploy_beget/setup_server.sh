#!/bin/bash
# Запускать на VPS из КОРНЯ проекта (там, где лежит папка blocks/).
# Использование: bash docs/scripts/deploy_beget/setup_server.sh
#
# Перед запуском подставь в переменные ниже свои значения:
#   PROJECT_DIR  — полный путь к проекту на сервере (например /home/u123/contentzavod)
#   SERVICE_USER — пользователь, от которого крутится сервис (например u123)

set -e

# ========== ПОДСТАВЬ СВОИ ЗНАЧЕНИЯ ==========
PROJECT_DIR="/home/u123/contentzavod"
SERVICE_USER="u123"
# ============================================

if [ ! -d "$PROJECT_DIR/blocks" ]; then
  echo "Ошибка: в $PROJECT_DIR нет папки blocks/. Запускай скрипт из корня проекта или задай верный PROJECT_DIR."
  exit 1
fi

cd "$PROJECT_DIR"

echo "=== 1. Обновление пакетов и установка Python venv (если нет) ==="
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip 2>/dev/null || true

echo "=== 2. Создание виртуального окружения и установка зависимостей ==="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r docs/config/requirements.txt -q 2>/dev/null || pip install requests python-dotenv PyYAML pydantic -q
pip install -r blocks/analytics/requirements.txt -q
pip install python-dotenv -q
deactivate

echo "=== 3. Папка storage ==="
mkdir -p storage

echo "=== 4. Файл .env ==="
if [ ! -f .env ]; then
  if [ -f docs/scripts/deploy_beget/env.server.example ]; then
    cp docs/scripts/deploy_beget/env.server.example .env
    echo "Создан .env из примера. Отредактируй: nano .env"
  else
    echo "Создай .env вручную: nano .env (минимум: ANALYTICS_DB_PATH=storage/analytics.db)"
  fi
else
  echo ".env уже есть."
fi

echo "=== 5. Проверка запуска приложения ==="
export PYTHONPATH="$PROJECT_DIR"
$PROJECT_DIR/venv/bin/uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050 &
UVICORN_PID=$!
sleep 3
if kill -0 $UVICORN_PID 2>/dev/null; then
  echo "Приложение запустилось. Останавливаю тестовый процесс."
  kill $UVICORN_PID 2>/dev/null || true
else
  echo "Предупреждение: не удалось проверить запуск. Продолжаем."
fi

echo ""
echo "Готово. Дальше вручную:"
echo "  1. Настроить systemd: скопировать analytics-dashboard.service.example в /etc/systemd/system/analytics-dashboard.service, подставить пользователя и путь, затем:"
echo "     sudo systemctl daemon-reload && sudo systemctl enable analytics-dashboard && sudo systemctl start analytics-dashboard"
echo "  2. Настроить Nginx и SSL — см. docs/guides/DEPLOY_FULL_PROJECT_BEGET.md"
echo "  3. В .env добавить DASHBOARD_PUBLIC_URL=https://твой-домен после получения SSL"
