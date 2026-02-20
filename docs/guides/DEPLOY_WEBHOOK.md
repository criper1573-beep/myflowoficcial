# Деплой по вебхуку (GitHub → сервер)

После настройки **один push в GitHub** приводит к автоматическому обновлению на сервере: `git pull`, обновление зависимостей в venv, перезапуск сервисов (analytics-dashboard, grs-image-web). Не нужно заходить по SSH и запускать `update.sh` вручную.

---

## Как это улучшает работу

- **Один шаг вместо двух:** сделали изменения → `git push` → сервер сам подтягивает код и перезапускает сервисы. Не нужно отдельно подключаться к VPS и выполнять `./update.sh`.
- **Удобнее с Cursor/AI:** после правок в коде достаточно отправить коммит в репозиторий; напоминания вроде «теперь зайди на сервер и выполни update.sh» не нужны.
- **Быстрее цикл:** правка → push → через несколько секунд на сервере уже новая версия.

---

## Что уже есть в проекте

- **webhook_server.py** (в корне) — HTTP-сервер (порт по умолчанию 3000, задаётся через `WEBHOOK_PORT`), endpoint `/webhook`, проверка подписи GitHub, при событии `push`: `git pull` (ветка из `DEPLOY_BRANCH`, по умолчанию `main`), `pip install` в venv по `docs/config/requirements.txt` и requirements блоков analytics/grs_image_web, перезапуск systemd-сервисов (analytics-dashboard, grs-image-web, orchestrator-kz).
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
   `u123 ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart analytics-dashboard, /usr/bin/systemctl restart grs-image-web, /usr/bin/systemctl restart orchestrator-kz`  
   Иначе вебхук сделает только `git pull` и `pip install`, а перезапуск systemd не выполнится (в логах будет предупреждение).

   **Кнопки «Запустить»/«Остановить» в дашборде:** чтобы они работали, пользователь, от которого запущен дашборд (analytics-dashboard), должен иметь право без пароля выполнять `systemctl start` и `systemctl stop` для тех же юнитов. Пример (подставь пользователя и полный список юнитов):  
   `u123 ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart analytics-dashboard, /usr/bin/systemctl restart grs-image-web, /usr/bin/systemctl restart orchestrator-kz, /usr/bin/systemctl start analytics-dashboard, /usr/bin/systemctl stop analytics-dashboard, /usr/bin/systemctl start grs-image-web, /usr/bin/systemctl stop grs-image-web, /usr/bin/systemctl start orchestrator-kz, /usr/bin/systemctl stop orchestrator-kz, ...`  
   (аналогично для остальных сервисов из списка на дашборде).

   **Оркестратор контент завода (orchestrator-kz):** при первом деплое сервис нужно один раз установить на VPS: скопировать `docs/scripts/deploy_beget/orchestrator-kz.service.example` в `/etc/systemd/system/orchestrator-kz.service`, подставить пользователя и путь к проекту. В `.env` на сервере **обязательно** задать переменные автопостинга: ZEN_STORAGE_STATE, GOOGLE_CREDENTIALS_PATH, GRS_AI_*, **TELEGRAM_BOT_TOKEN**, **TELEGRAM_CHANNEL_ID** (скопировать из рабочего .env с компа — без них публикация в Telegram падает при каждом запуске). Затем выполнить `playwright install chromium` (и при необходимости `playwright install-deps chromium`) в venv, `sudo systemctl daemon-reload && sudo systemctl enable orchestrator-kz && sudo systemctl start orchestrator-kz`. После этого вебхук при каждом push будет перезапускать orchestrator-kz. При старте оркестратор один раз выполняет пробный запуск цепочки (если не было запуска за последние 2 часа), затем работает по расписанию (5 слотов в день).

   **Дашборд и статистика:** оркестратор пишет каждый запуск (успешный и с ошибками) в ту же БД аналитики, что и дашборд (`storage/analytics.db` или проект из `ANALYTICS_PROJECT`). На сервере дашборд и orchestrator-kz должны работать из одного каталога проекта и одного .env — тогда в дашборде отображаются сводка, график и лента запусков (источник `schedule`). Проверка: после старта оркестратора или первого слота открыть дашборд и убедиться, что появился новый запуск с шагами (Генерация статьи, Публикация в Telegram, Публикация в Дзен) и каналом zen/telegram.

   **Переход с zen-schedule:** если на сервере уже был установлен старый юнит `zen-schedule`, после обновления кода: скопировать `orchestrator-kz.service.example` в `/etc/systemd/system/orchestrator-kz.service`, подставить User и пути, выполнить `sudo systemctl daemon-reload && sudo systemctl enable orchestrator-kz`, затем `sudo systemctl stop zen-schedule && sudo systemctl start orchestrator-kz`. В sudoers заменить `zen-schedule` на `orchestrator-kz`. Файл состояния переименован: `storage/zen_schedule_state.json` → `storage/orchestrator_kz_state.json` (при первом запуске оркестратора создастся новый).

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

## Если после push код на сервере не обновился

Вебхук вызывается GitHub при каждом push в выбранную ветку. Если на сайте ничего не изменилось:

1. **Проверить доставку в GitHub:**  
   Repo → Settings → Webhooks → ваш webhook → **Recent Deliveries**. Найти запрос с нужным коммитом. Если статус не 200 или доставка не было — GitHub мог не отправить запрос или сервер не ответил (сеть, сервис упал). Можно нажать **Redeliver** для повторной отправки.

2. **Проверить логи на сервере:**  
   `journalctl -u github-webhook -n 100` или файл `storage/webhook.log` в корне проекта. Искать строки «Начинаем деплой», «git pull успешен», «Деплой завершен успешно». Если после вашего push таких записей нет — запрос до вебхука не дошёл или не обработан.

3. **Ручной деплой (fallback):**  
   Подключиться по SSH и выполнить из корня проекта:
   ```bash
   git pull origin main
   sudo systemctl restart analytics-dashboard grs-image-web orchestrator-kz
   ```
   Или с Windows через скрипт проекта (нужен .env с SERVER_HOST, SERVER_USER, SERVER_SSH_PASSWORD или DEPLOY_SSH_PASSWORD):
   ```powershell
   .\docs\scripts\deploy_beget\remote_cmd.ps1 -Command "cd /root/contentzavod && git pull origin main && sudo systemctl restart analytics-dashboard grs-image-web orchestrator-kz"
   ```
   Подставь свой путь к проекту на сервере вместо `/root/contentzavod`, если он другой.

**Важно:** падение GitHub Actions (например, workflow «Setup Staging») не отменяет и не заменяет вебхук: вебхук — это отдельный HTTP-запрос от GitHub на ваш сервер. Если не уверен, обновился ли код — на сервере выполни `git log -1 --oneline` в каталоге проекта и сверь с коммитом в GitHub.

---

## Оркестратор: OOM и таймауты

Если оркестратор (orchestrator-kz) падает с **OOM (Out of Memory)** или в логах виден «killed by OOM killer»:

- **Swap:** на сервере с малым объёмом RAM добавь swap: `sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile` (и при необходимости добавь в fstab для сохранения после перезагрузки).
- Браузер Chromium закрывается сразу после публикации; при нехватке памяти можно дополнительно ограничить процессы на сервере или увеличить RAM.

Если при публикации в Дзен возникает **таймаут загрузки страницы** (Page.goto timeout):

- В `.env` на сервере можно увеличить таймаут браузера: `ZEN_BROWSER_TIMEOUT=90000` (мс; по умолчанию 60000). Логи: `journalctl -u orchestrator-kz -n 100`.

Если при генерации обложки возникает **таймаут GRS/Gemini** (например «google gemini timeout»):

- В `.env` можно задать больший таймаут для запросов к GRS Draw API: `GRS_IMAGE_TIMEOUT=180` (секунды; по умолчанию 120). Генератор обложки при ошибке делает одну повторную попытку и при неудаче может использовать fallback-обложку из репозитория (если файл есть в `blocks/autopost_zen/articles/`).

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
