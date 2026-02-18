# Staging: деплой dev на поддомен

Push в ветку `dev` → автоматический деплой на **dev.flowimage.ru** (или другой поддомен). Production (flowimage.ru) остаётся на ветке `main` и не затрагивается.

---

## Схема

| Ветка | Домен | Директория | Сервис |
|-------|-------|------------|--------|
| main | flowimage.ru | /root/contentzavod | grs-image-web (порт 8765) |
| dev | dev.flowimage.ru | /root/contentzavod-staging | grs-image-web-staging (порт 8766) |

---

## Настройка (один раз)

### 1. Поддомен

В панели DNS хостинга добавь A-запись: **dev.flowimage.ru** → IP сервера (тот же, что у flowimage.ru).

### 2. Клонирование проекта для staging

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

### 3. Systemd-сервис для staging

```bash
# Копируем пример
sudo cp /root/contentzavod-staging/docs/scripts/deploy_beget/grs-image-web-staging.service.example /etc/systemd/system/grs-image-web-staging.service

# Подставляем путь
sudo sed -i 's|__PROJECT_DIR_STAGING__|/root/contentzavod-staging|g' /etc/systemd/system/grs-image-web-staging.service

# Запускаем
sudo systemctl daemon-reload
sudo systemctl enable grs-image-web-staging
sudo systemctl start grs-image-web-staging
```

### 4. Nginx для поддомена

```bash
# Копируем конфиг
sudo cp /root/contentzavod/docs/scripts/deploy_beget/nginx-flowimage-dev.conf.example /etc/nginx/sites-available/flowimage-dev
sudo ln -s /etc/nginx/sites-available/flowimage-dev /etc/nginx/sites-enabled/

# Проверяем и перезагружаем
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
u123 ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart grs-image-web-staging
```

(Подставь пользователя, от которого крутится webhook, если не root.)

### 7. GitHub: webhook на все push

В настройках webhook в GitHub оставь **Just the push event** — webhook будет получать и push в main, и push в dev. Сервер сам различает по `ref`.

---

## Проверка

- **Staging:** открой https://dev.flowimage.ru (или http до настройки SSL)
- **Деплой dev:** сделай изменение, `git push origin dev` → через несколько секунд обнови dev.flowimage.ru
- **Production:** flowimage.ru не меняется при push в dev

---

## См. также

- [GIT_BRANCHING.md](GIT_BRANCHING.md) — workflow веток
- [DEPLOY_WEBHOOK.md](DEPLOY_WEBHOOK.md) — общая настройка вебхука
