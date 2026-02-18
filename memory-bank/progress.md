# Progress

Статус реализации, выполненные шаги, команды, наблюдения. Обновляется в фазе /build.

---

## webhook-002 (Деплой по вебхуку) — 2025-02-18

### Выполнено
1. **webhook_server.py** — исправления: создание `storage/` до настройки логирования (избежание падения при старте); ветка из `DEPLOY_BRANCH` (по умолчанию `main`); безопасный разбор `Content-Length`; порт из `WEBHOOK_PORT`; установка зависимостей для `blocks/grs_image_web/requirements.txt` при деплое.
2. **docs/guides/DEPLOY_WEBHOOK.md** — добавлены переменные окружения (GITHUB_WEBHOOK_SECRET, DEPLOY_BRANCH, WEBHOOK_PORT), шаг `daemon-reload` после `systemctl edit`, описание текущего поведения.
3. **memory-bank** — tasks.md, activeContext.md обновлены под задачу webhook-002.

### Проверка
- Локальный запуск на Windows не выполнялся (фоновый запуск упирался в кодировку пути). На VPS после `setup_webhook.sh` и настройки секрета: `curl http://IP:3000/health` и push в репозиторий с просмотром `journalctl -u github-webhook -f`.

### Полная проверка на VPS (2025-02-18)
- **VPS:** 85.198.66.62, проект `/root/contentzavod`, репо `criper1573-beep/myflowoficcial`, ветка main.
- **webhook_server.py** на сервере не было — загружен через pscp. Развёрнут unit для root: **docs/scripts/deploy_beget/github-webhook-root.service** (секрет на сервере, не в репо).
- **Health:** `curl http://85.198.66.62:3000/health` → `{"message": "Webhook server is running"}`.
- **Тестовый POST** с подписью (secret contentzavod-webhook-secret): первый раз git pull не прошёл из-за локальных изменений в `blocks/grs_image_web/api.py`; выполнен `git stash` на сервере; повторный POST → 200, «Deployment successful», в логах: git pull, pip, перезапуск analytics-dashboard и grs-image-web.
- **GitHub webhook:** настроен URL `http://85.198.66.62/webhook` (порт 80 через Nginx), ответ 200. Push в main триггерит деплой на VPS.

### Архив
- Задача закрыта 2025-02-18. Архив: `memory-bank/archive/archive-webhook-002.md`.

---

## docker-001 (Реализовать Docker) — 2025-02-18

### Выполнено
1. **.dockerignore** — создан в корне; исключены .env, venv, storage, .git, memory-bank, .cursor, бекапы, IDE, логи и др.
2. **Dockerfile** — python:3.12-slim, WORKDIR /app, установка из docs/config/requirements.txt, копирование blocks/ и docs/, CMD по умолчанию `python -m blocks.spambot --project flowcabinet`.
3. **docker-compose.yml** — сервисы spambot и post_flow с общим образом, env_file: .env, volumes для blocks/projects/data.
4. **docs/guides/DOCKER.md** — сборка, запуск одного контейнера (spambot, post_flow, mcp_server), compose, секреты, ограничение Playwright, Windows/volumes, типичные проблемы.
5. **README.md** — добавлена секция «Docker» со ссылкой на docs/guides/DOCKER.md.
6. **.cursor/rules/project-structure.mdc** — в исключения корня добавлены Dockerfile, .dockerignore, docker-compose.yml.

### Команды для проверки (после появления .env)
- `docker build -t contentzavod .`
- `docker run --rm -it --env-file .env contentzavod python -m blocks.spambot --list-projects`
- `docker compose up -d spambot` / `docker compose down`

### Наблюдения
- Playwright-блоки (autopost_zen) в базовом образе не поддерживаются; в DOCKER.md указано, что нужен отдельный образ или хост.

### Архив
- Задача закрыта 2025-02-18. Архив: `memory-bank/archive/archive-docker-001.md`.

---

## grs-image-web-003 (Починка сайта генерации картинок) — 2025-02-18

### Выполнено
1. **blocks/grs_image_web/api.py** — GET /links, ImprovePromptRequest и исправленный /api/improve-prompt, GET/POST/DELETE /api/links, GET /uploaded/{filename}, проверка path для /generated/.
2. **memory-bank/projectbrief.md**, **productContext.md** — секция «Деплой» (деплой по вебхуку).
3. Деплой: коммит, push в main → вебхук на VPS.

### Архив
- Задача закрыта 2025-02-18. Архив: `memory-bank/archive/archive-grs-image-web-003.md`.
