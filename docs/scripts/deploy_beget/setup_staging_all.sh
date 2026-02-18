#!/bin/bash
# Полная настройка staging для dev.flowimage.ru, dev.flowimage.store, dev.quickpack.space
# Запускать на VPS из КОРНЯ production-проекта: cd /root/contentzavod && sudo bash docs/scripts/deploy_beget/setup_staging_all.sh

set -e

PROJECT_DIR="${1:-/root/contentzavod}"
PROJECT_DIR_STAGING="${2:-/root/contentzavod-staging}"
REPO_URL="https://github.com/criper1573-beep/myflowoficcial.git"

echo "=== Настройка Staging (все поддомены) ==="
echo "Production: $PROJECT_DIR"
echo "Staging:    $PROJECT_DIR_STAGING"
echo ""

# 1. Клонирование / обновление staging
if [ -d "$PROJECT_DIR_STAGING" ]; then
    echo "[1/6] Обновляем staging..."
    cd "$PROJECT_DIR_STAGING"
    git fetch origin dev 2>/dev/null || true
    git checkout dev
    git pull origin dev || true
else
    echo "[1/6] Клонируем репозиторий в staging..."
    git clone "$REPO_URL" "$PROJECT_DIR_STAGING"
    cd "$PROJECT_DIR_STAGING"
    git checkout dev
fi

# 2. venv и зависимости
echo "[2/6] venv и зависимости..."
cd "$PROJECT_DIR_STAGING"
[ ! -d venv ] && python3 -m venv venv
./venv/bin/pip install -q -r docs/config/requirements.txt
[ -f blocks/grs_image_web/requirements.txt ] && ./venv/bin/pip install -q -r blocks/grs_image_web/requirements.txt
[ -f blocks/analytics/requirements.txt ] && ./venv/bin/pip install -q -r blocks/analytics/requirements.txt

# Копируем .env из prod (если есть)
[ -f "$PROJECT_DIR/.env" ] && [ ! -f "$PROJECT_DIR_STAGING/.env" ] && cp "$PROJECT_DIR/.env" "$PROJECT_DIR_STAGING/.env" && echo "  .env скопирован из prod"

# 3. Systemd units
echo "[3/6] Systemd units..."
for unit in grs-image-web-staging analytics-dashboard-staging; do
    ex="docs/scripts/deploy_beget/${unit}.service.example"
    dst="/etc/systemd/system/${unit}.service"
    if [ -f "$ex" ]; then
        sed "s|__PROJECT_DIR_STAGING__|$PROJECT_DIR_STAGING|g" "$ex" | sudo tee "$dst" > /dev/null
        echo "  $unit установлен"
    fi
done
sudo systemctl daemon-reload
sudo systemctl enable grs-image-web-staging analytics-dashboard-staging 2>/dev/null || true
sudo systemctl start grs-image-web-staging analytics-dashboard-staging 2>/dev/null || true

# 4a. Nginx: /bootstrap для webhook
echo "[4/6] Nginx configs..."
if [ -f "$PROJECT_DIR/docs/scripts/deploy_beget/patch_nginx_bootstrap.py" ]; then
    sudo python3 "$PROJECT_DIR/docs/scripts/deploy_beget/patch_nginx_bootstrap.py" 2>/dev/null && sudo nginx -t && sudo systemctl reload nginx || true
fi

# 4b. Nginx: staging поддомены
cd "$PROJECT_DIR_STAGING"
for pair in "flowimage-dev:nginx-flowimage-dev.conf.example" "flowimage-store-dev:nginx-flowimage-store-dev.conf.example" "quickpack-dev:nginx-quickpack-dev.conf.example"; do
    cfg="${pair%%:*}"
    src="docs/scripts/deploy_beget/${pair##*:}"
    if [ -f "$src" ]; then
        sudo cp "$src" "/etc/nginx/sites-available/$cfg" 2>/dev/null || sudo mkdir -p /etc/nginx/sites-available && sudo cp "$src" "/etc/nginx/sites-available/$cfg"
        [ -d /etc/nginx/sites-enabled ] && sudo ln -sf "/etc/nginx/sites-available/$cfg" "/etc/nginx/sites-enabled/$cfg"
        echo "  $cfg"
    fi
done
sudo nginx -t 2>/dev/null && sudo systemctl reload nginx || echo "  nginx -t: проверь конфиг вручную"

# 5. Webhook: PROJECT_DIR_STAGING
echo "[5/6] Webhook..."
if systemctl is-active --quiet github-webhook 2>/dev/null; then
    override_dir="/etc/systemd/system/github-webhook.service.d"
    sudo mkdir -p "$override_dir"
    echo -e "[Service]\nEnvironment=PROJECT_DIR_STAGING=$PROJECT_DIR_STAGING" | sudo tee "$override_dir/override.conf" > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl restart github-webhook
    echo "  PROJECT_DIR_STAGING=$PROJECT_DIR_STAGING"
else
    echo "  Webhook не запущен — задай PROJECT_DIR_STAGING вручную в systemctl edit github-webhook"
fi

# 6. Sudoers
echo "[6/6] Sudoers..."
sudoers_line="root ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart grs-image-web-staging, /usr/bin/systemctl restart analytics-dashboard-staging"
if ! sudo grep -q "grs-image-web-staging" /etc/sudoers 2>/dev/null; then
    echo "$sudoers_line" | sudo tee /etc/sudoers.d/webhook-staging > /dev/null
    sudo chmod 440 /etc/sudoers.d/webhook-staging
    echo "  Sudoers добавлен"
else
    echo "  Sudoers уже настроен"
fi

echo ""
echo "✅ Staging настроен."
echo ""
echo "Поддомены (DNS уже созданы):"
echo "  - dev.flowimage.ru     → GRS Image Web (порт 8766)"
echo "  - dev.flowimage.store  → Дашборд аналитики (порт 8051)"
echo "  - dev.quickpack.space  → Quickpack (порт 8086, настрой вручную если другой)"
echo ""
echo "SSL (запусти после проверки DNS):"
echo "  sudo certbot --nginx -d dev.flowimage.ru -d dev.flowimage.store -d dev.quickpack.space --non-interactive --agree-tos"
echo ""
echo "Проверка: curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8766/ && echo ' grs' && curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8051/ && echo ' dashboard'"
