# Staging: деплой dev на поддомен

Push в ветку `dev` → автоматический деплой на **dev.flowimage.ru** (или другой поддомен). Production (flowimage.ru) остаётся на ветке `main` и не затрагивается.

---

## Схема

| Ветка | Домен | Директория | Сервис |
|-------|-------|------------|--------|
| main | flowimage.ru | /root/contentzavod | grs-image-web (8765) |
| main | flowimage.store | /root/contentzavod | analytics-dashboard (8050) |
| dev | dev.flowimage.ru | /root/contentzavod-staging | grs-image-web-staging (8766) |
| dev | dev.flowimage.store | /root/contentzavod-staging | analytics-dashboard-staging (8051) |
| dev | dev.quickpack.space | — | Quickpack (порт 8086, настраивается отдельно) |

---

## Настройка (один раз)

### 1. Поддомены (DNS уже созданы)

A-записи: **dev.flowimage.ru**, **dev.flowimage.store**, **dev.quickpack.space** → IP сервера.

### Вариант А: единый скрипт (рекомендуется)

```bash
cd /root/contentzavod
git pull origin main
sudo bash docs/scripts/deploy_beget/setup_staging_all.sh
```

Скрипт: клонирует staging, venv, systemd units, nginx configs, webhook, sudoers.

### Вариант Б: по шагам

#### 2. Клонирование

Вариант А — скрипт (подставь REPO_URL и PROJECT_DIR_STAGING):

```bash
# Редактируй docs/scripts/deploy_beget/setup_staging.sh
bash docs/scripts/deploy_beget/setup_staging.sh
```

Вариант Б — вручную:

```bash
sudo git clone https://github.com/ВАШ_ОРГ/ВАШ_РЕПО.git /root/contentzavod-staging
cd /root/contentzavod-staging
sudo git checkout dev
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r docs/config/requirements.txt
sudo ./venv/bin/pip install -r blocks/grs_image_web/requirements.txt
```

#### 3. Systemd (grs-image-web-staging, analytics-dashboard-staging)

```bash
for u in grs-image-web-staging analytics-dashboard-staging; do
  sed "s|__PROJECT_DIR_STAGING__|/root/contentzavod-staging|g" \
    /root/contentzavod-staging/docs/scripts/deploy_beget/${u}.service.example | sudo tee /etc/systemd/system/${u}.service
done
sudo systemctl daemon-reload && sudo systemctl enable --now grs-image-web-staging analytics-dashboard-staging
```

#### 4. Nginx (все три поддомена)

```bash
for cfg in flowimage-dev flowimage-store-dev quickpack-dev; do
  sudo cp /root/contentzavod-staging/docs/scripts/deploy_beget/nginx-${cfg}.conf.example /etc/nginx/sites-available/${cfg}
  sudo ln -sf /etc/nginx/sites-available/${cfg} /etc/nginx/sites-enabled/
done
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Webhook: переменная PROJECT_DIR_STAGING

```bash
sudo systemctl edit github-webhook
```

Добавь в секцию `[Service]`:

```ini
[Service]
Environment=PROJECT_DIR_STAGING=/root/contentzavod-staging
```

Сохрани, затем:

```bash
sudo systemctl daemon-reload
sudo systemctl restart github-webhook
```

### 6. Sudoers: перезапуск staging-сервиса

```bash
sudo visudo
```

Добавь (или объедини с существующей строкой для webhook):

```
root ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart grs-image-web-staging, /usr/bin/systemctl restart analytics-dashboard-staging
```

(Если webhook под root — `root`; иначе подставь своего пользователя.)

### 7. GitHub: webhook на все push

В настройках webhook в GitHub оставь **Just the push event** — webhook будет получать и push в main, и push в dev. Сервер сам различает по `ref`.

---

## Проверка

- **dev.flowimage.ru** — GRS Image Web (staging)
- **dev.flowimage.store** — дашборд аналитики (staging)
- **dev.quickpack.space** — Quickpack (настрой порт 8086 в nginx если другой)
- **Деплой dev:** `git push origin dev` → вебхук обновит staging
- **Production:** flowimage.ru и flowimage.store не меняются при push в dev

**SSL:** `sudo certbot --nginx -d dev.flowimage.ru -d dev.flowimage.store -d dev.quickpack.space --non-interactive --agree-tos`

---

## См. также

- [GIT_BRANCHING.md](GIT_BRANCHING.md) — workflow веток
- [DEPLOY_WEBHOOK.md](DEPLOY_WEBHOOK.md) — общая настройка вебхука
