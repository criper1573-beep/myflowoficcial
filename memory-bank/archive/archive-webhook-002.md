# АРХИВ ЗАДАЧИ: webhook-002 — Деплой по вебхуку

## METADATA

| Поле | Значение |
|------|----------|
| Task ID | webhook-002 |
| Название | Реализовать/починить деплой по вебхуку (GitHub → сервер) |
| Уровень сложности | Level 2 |
| Дата инициализации | 2025-02-18 |
| Дата архивации | 2025-02-18 |
| Статус | COMPLETE |

---

## SUMMARY

Деплой по вебхуку приведён в рабочее состояние: при push в ветку `main` репозитория `criper1573-beep/myflowoficcial` GitHub отправляет POST на сервер, webhook-сервис выполняет `git pull`, обновление зависимостей в venv и перезапуск systemd-сервисов (analytics-dashboard, grs-image-web). Исправлены баги в `webhook_server.py`, добавлены конфигурируемые переменные окружения, развёрнут сервис на VPS 85.198.66.62, настроено проксирование через Nginx на порт 80 (доступ GitHub), вебхук в GitHub отвечает 200.

---

## REQUIREMENTS

- Проверить существующую цепочку деплоя по вебхуку и исправить неработающее.
- Обеспечить приём webhook от GitHub, проверку подписи, выполнение git pull, pip install, перезапуск сервисов.
- Документировать переменные окружения и шаги настройки.
- Провести полную проверку на VPS при наличии доступов.

---

## IMPLEMENTATION

### Изменённые/созданные артефакты

- **webhook_server.py** (корень) — создание `storage/` до логирования; DEPLOY_BRANCH, WEBHOOK_PORT из env; безопасный разбор Content-Length; установка зависимостей для blocks/analytics и blocks/grs_image_web; удалены неиспользуемые импорты.
- **docs/guides/DEPLOY_WEBHOOK.md** — таблица переменных окружения (GITHUB_WEBHOOK_SECRET, DEPLOY_BRANCH, WEBHOOK_PORT), шаг daemon-reload после systemctl edit.
- **docs/guides/DEPLOY_WEBHOOK_VERIFICATION.md** — план полной проверки: доступы, шаги 0–6, чеклист.
- **docs/scripts/deploy_beget/github-webhook-root.service** — unit для запуска webhook под root, WorkingDirectory=/root/contentzavod (секрет не в репо, подставляется на сервере).
- **docs/scripts/deploy_beget/nginx-webhook-location.conf** — фрагмент location для /webhook и /health (proxy_pass на 127.0.0.1:3000).
- **docs/scripts/deploy_beget/patch_nginx_webhook.py** — скрипт вставки location в Nginx default_server (выполнен на VPS).

### Развёртывание на VPS

- Загрузка webhook_server.py через pscp в /root/contentzavod.
- Установка unit github-webhook (путь root, /root/contentzavod), секрет задан на сервере.
- Патч Nginx: location = /webhook и location = /health в default_server (порт 80) → proxy на 127.0.0.1:3000.
- В GitHub: Payload URL изменён на http://85.198.66.62/webhook (без :3000).

---

## TESTING

- Health: curl http://85.198.66.62/health и http://127.0.0.1:3000/health — ответ «Webhook server is running».
- Тестовый POST с HMAC-подписью (secret contentzavod-webhook-secret) — 200, «Deployment successful»; в логах: git pull, pip, перезапуск analytics-dashboard и grs-image-web.
- Redeliver из GitHub после смены URL на порт 80 — ответ 200, доставка успешна.
- При конфликте git pull (локальные изменения на сервере) — выполнен git stash, повторный деплой прошёл.

---

## LESSONS LEARNED

- На многих VPS снаружи доступны только 80/443/22; сервисы на нестандартных портах нужно проксировать через Nginx на 80/443.
- В гайдах явно указывать итоговый URL вебхука (http://IP/webhook без порта при проксировании).
- Для задач сложности 2+ соблюдать VAN → PLAN → подтверждение → BUILD.
- Секрет вебхука не коммитить; на сервере задавать через systemctl edit или при установке unit.

---

## REFERENCES

- Рефлексия: [memory-bank/reflection/reflection-webhook-002.md](../reflection/reflection-webhook-002.md)
- План проверки: [docs/guides/DEPLOY_WEBHOOK_VERIFICATION.md](../../docs/guides/DEPLOY_WEBHOOK_VERIFICATION.md)
- Гайд по настройке: [docs/guides/DEPLOY_WEBHOOK.md](../../docs/guides/DEPLOY_WEBHOOK.md)
