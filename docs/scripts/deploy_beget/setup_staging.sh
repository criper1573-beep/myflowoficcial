#!/bin/bash
# Первоначальная настройка staging (ветка dev) на поддомен
# Запускать на VPS. Подставить PROJECT_DIR_STAGING и репозиторий.

set -e

# Подставь свои значения
REPO_URL="https://github.com/YOUR_ORG/YOUR_REPO.git"
PROJECT_DIR_STAGING="/root/contentzavod-staging"

echo "=== Настройка Staging (dev) ==="

if [ -d "$PROJECT_DIR_STAGING" ]; then
    echo "Директория $PROJECT_DIR_STAGING уже существует. Обновляем..."
    cd "$PROJECT_DIR_STAGING"
    git fetch origin dev
    git checkout dev
    git pull origin dev
else
    echo "Клонируем репозиторий..."
    git clone "$REPO_URL" "$PROJECT_DIR_STAGING"
    cd "$PROJECT_DIR_STAGING"
    git checkout dev
fi

echo "Создаём venv и ставим зависимости..."
python3 -m venv venv
./venv/bin/pip install -q -r docs/config/requirements.txt
[ -f blocks/grs_image_web/requirements.txt ] && ./venv/bin/pip install -q -r blocks/grs_image_web/requirements.txt
[ -f blocks/analytics/requirements.txt ] && ./venv/bin/pip install -q -r blocks/analytics/requirements.txt

echo "✅ Staging готов: $PROJECT_DIR_STAGING"
echo ""
echo "Следующие шаги:"
echo "1. Скопировать .env из production (если нужно)"
echo "2. Установить systemd unit: grs-image-web-staging.service"
echo "3. Настроить Nginx для dev.flowimage.ru"
echo "4. В webhook: Environment=PROJECT_DIR_STAGING=$PROJECT_DIR_STAGING"
echo "См. docs/guides/DEPLOY_STAGING.md"
