#!/bin/bash
# Обновление проекта на сервере после git push с компа.
# Скопируй в корень проекта на VPS и запускай: ./update.sh
# Или оставь в docs/scripts/deploy_beget/ и запускай: bash docs/scripts/deploy_beget/update.sh

set -e
cd "$(dirname "$0")/../.."
echo "Обновление в $(pwd)..."

git pull

if [ -d venv ]; then
  source venv/bin/activate
  pip install -q -r docs/config/requirements.txt 2>/dev/null || true
  pip install -q -r blocks/analytics/requirements.txt
  deactivate
fi

if systemctl is-active --quiet analytics-dashboard 2>/dev/null; then
  sudo systemctl restart analytics-dashboard
  echo "Сервис analytics-dashboard перезапущен."
else
  echo "Сервис analytics-dashboard не найден или не запущен. Перезапуск не выполнен."
fi

if systemctl is-active --quiet grs-image-web 2>/dev/null; then
  sudo systemctl restart grs-image-web
  echo "Сервис grs-image-web перезапущен."
fi

echo "Готово."
