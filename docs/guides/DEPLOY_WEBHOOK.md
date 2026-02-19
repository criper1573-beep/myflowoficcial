# Деплой по вебхуку (GitHub → сервер)

После настройки **один push в GitHub** приводит к автоматическому обновлению на сервере: `git pull`, обновление зависимостей в venv, перезапуск сервисов (analytics-dashboard, grs-image-web). Не нужно заходить по SSH и запускать `update.sh` вручную.

---

## Как это улучшает работу

- **Один шаг вместо двух:** сделали изменения → `git push` → сервер сам подтягивает код и перезапускает сервисы. Не нужно отдельно подключаться к VPS и выполнять `./update.sh`.
- **Удобнее с Cursor/AI:** после правок в коде достаточно отправить коммит в репозиторий; напоминания вроде «теперь зайди на сервер и выполни update.sh» не нужны.
- **Быстрее цикл:** правка → push → через несколько секунд на сервере уже новая версия.

---

## Что уже есть в проекте

- **webhook_server.py** (в корне) — HTTP-сервер (порт по умолчанию 3000, задаётся через `WEBHOOK_PORT`), endpoint `/webhook`, проверка подписи GitHub, при событии `push`: `git pull` (ветка из `DEPLOY_BRANCH`, по умолчанию `main`), `pip install` в venv по `docs/config/requirements.txt` и requirements блоков analytics/grs_image_web, перезапуск systemd-сервисов (analytics-dashboard, grs-image-web, zen-schedule).
- **github-webhook.service** — пример юнита systemd для запуска вебхука.
- **docs/scripts/deploy_beget/setup_webhook.sh** — скрипт установки вебхука на VPS (пути и пользователь подставить свои).

---

## Настройка на сервере

1. **Убедиться, что на VPS есть проект и venv:**  
   `git clone`, `python3 -m venv venv`, `pip install -r docs/config/requirements.txt` и т.д. (как в DEPLOY_FULL_PROJECT_BEGET.md).

2. **Скопировать и подставить пути:**  
   В `github-webhook.service` и `setup_webhook.sh` заменить `/home/u123/contentzavod` и `u123` на свой путь и пользователя.

3. **Запустить установку вебхука:**  
   На VPS из корня проекта:  
   `bash docs/scripts/deploy_beget/setup_webhook.sh`

4. **Задать секрет (и при необходимости ветку/порт):**  
   `sudo systemctl edit github-webhook` → в секции `[Service]` добавить:  
   `Environment=GITHUB_WEBHOOK_SECRET=твой-секретный-токен`  
   При другой ветке по умолчанию: `Environment=DEPLOY_BRANCH=master`  
   Сохранить, затем: `sudo systemctl daemon-reload` и `sudo systemctl restart github-webhook`.

5. **Разрешить перезапуск сервисов без пароля (для пользователя, от которого крутится вебхук):**  
   `sudo visudo` (или файл в `/etc/sudoers.d/`), добавить строку (подставь своего пользователя):  
   `u123 ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart analytics-dashboard, /usr/bin/systemctl restart grs-image-web, /usr/bin/systemctl restart zen-schedule`  
   Иначе вебхук сделает только `git pull` и `pip install`, а перезапуск systemd не выполнится (в логах будет предупреждение).

   **Планировщик Дзен (zen-schedule):** при первом деплое сервис нужно один раз установить на VPS: скопировать `docs/scripts/deploy_beget/zen-schedule.service.example` в `/etc/systemd/system/zen-schedule.service`, подставить пользователя и путь к проекту, в .env задать переменные автопостинга (ZEN_STORAGE_STATE, GOOGLE_CREDENTIALS_PATH, GRS_AI_* и т.д.), выполнить `playwright install chromium` в venv, затем `sudo systemctl daemon-reload && sudo systemctl enable zen-schedule && sudo systemctl start zen-schedule`. После этого вебхук при каждом push будет перезапускать zen-schedule вместе с остальными сервисами. Запуски публикаций пишутся в ту же БД аналитики, что и дашборд — статистика отображается в дашборде.

6. **Настроить вебхук в GitHub:**  
   Repo → Settings → Webhooks → Add webhook:  
   - **Payload URL:** `http://IP_СЕРВЕРА:3000/webhook` (для продакшена лучше проксировать через Nginx и HTTPS).  
   - **Content type:** application/json.  
   - **Secret:** тот же токен, что в `GITHUB_WEBHOOK_SECRET`.  
   - **Events:** Just the push event.

7. **Проверка:**  
   `curl http://IP_СЕРВЕРА:3000/health` → ответ "Webhook server is running".  
   После push в репозиторий смотреть логи: `journalctl -u github-webhook -f`.

---

## Переменные окружения (systemd)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `GITHUB_WEBHOOK_SECRET` | — | Секрет вебхука (обязателен в продакшене). |
| `PROJECT_DIR_STAGING` | — | Путь к staging (ветка dev). Если задан, push в `dev` деплоит туда. См. [DEPLOY_STAGING.md](DEPLOY_STAGING.md). |
| `WEBHOOK_PORT` | `3000` | Порт, на котором слушает webhook-сервер. |

**Поведение по веткам:**
- Push в `main` → деплой в корневую директорию проекта (production).
- Push в `dev` → деплой в `PROJECT_DIR_STAGING` (если задана).

---

## Безопасность

- Обязательно задать **GITHUB_WEBHOOK_SECRET** и указать тот же Secret в настройках вебхука в GitHub — иначе любой может слать запросы на `/webhook`.
- В продакшене лучше не открывать порт 3000 наружу, а повесить перед вебхуком Nginx с HTTPS и (при желании) базовой проверкой (например, по заголовку или по отдельному пути).

---

## Ссылки

- Полный деплой на Beget: **docs/guides/DEPLOY_FULL_PROJECT_BEGET.md**
- Ручное обновление без вебхука: **docs/scripts/deploy_beget/update.sh**
