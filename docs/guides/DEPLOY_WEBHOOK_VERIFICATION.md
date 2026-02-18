# План полной проверки деплоя по вебхуку

Чеклист для проверки всей цепочки: GitHub push → webhook-сервер на VPS → git pull, pip, перезапуск сервисов. Выполняется с предоставленными доступами (SSH и при необходимости данные вебхука).

---

## Что нужно от тебя (доступы)

| Что | Зачем |
|-----|--------|
| **SSH на VPS** | Хост (IP или домен), пользователь, ключ или пароль. Нужен доступ под пользователем, от которого крутится/будет крутиться сервис webhook (например `u123`), и возможность при необходимости выполнить команды с `sudo` (или ты выполнишь один раз настройку sudoers по гайду). |
| **Путь проекта на VPS** | Например `/home/u123/contentzavod` — корень репозитория. |
| **Подтверждение вебхука в GitHub** | Либо: URL вебхука и что Secret уже задан (проверим только сервер). Либо: доступ к репо (токен с правами на Webhooks) — тогда можно проверить/создать вебхук через API. |
| **GITHUB_WEBHOOK_SECRET** | Нужен только если будем слать тестовый POST с подписью (опционально). Для проверки «push → логи» достаточно SSH. |

Минимум для полной проверки: **SSH + путь проекта**. Остальное — по ситуации.

---

## Шаг 0. Подготовка на VPS (если ещё не сделано)

- [ ] Проект склонирован в `PROJECT_DIR`, есть ветка `main` (или та, что в `DEPLOY_BRANCH`).
- [ ] Создан venv: `python3 -m venv venv`, установлены зависимости из `docs/config/requirements.txt`.
- [ ] В корне есть `webhook_server.py`, `github-webhook.service`, `docs/scripts/deploy_beget/setup_webhook.sh`.
- [ ] В `setup_webhook.sh` и при необходимости в `github-webhook.service` подставлены актуальные `PROJECT_DIR` и `SERVICE_USER`.

---

## Шаг 1. Установка и запуск сервиса webhook

- [ ] Выполнен (или уже был выполнен) на VPS из корня проекта:  
  `bash docs/scripts/deploy_beget/setup_webhook.sh`
- [ ] Сервис установлен: `systemctl status github-webhook` — активен (active/running).
- [ ] Секрет задан: `sudo systemctl edit github-webhook` уже делался, в override есть  
  `Environment=GITHUB_WEBHOOK_SECRET=...`  
  Проверка (без раскрытия секрета): `systemctl show github-webhook --property=Environment` — переменная есть.
- [ ] После правок юнита выполнялись: `sudo systemctl daemon-reload`, `sudo systemctl restart github-webhook`.

---

## Шаг 2. Health endpoint

- [ ] С сервера:  
  `curl -s http://127.0.0.1:3000/health`  
  Ожидается ответ с сообщением вроде "Webhook server is running" (или JSON с полем `message`).
- [ ] Снаружи (если порт 3000 открыт):  
  `curl -s http://IP_СЕРВЕРА:3000/health`  
  Тот же результат. Если порт закрыт файрволом — достаточно проверки с localhost.

---

## Шаг 3. Конфигурация вебхука в GitHub

- [ ] В репозитории: Settings → Webhooks — есть webhook с:
  - **Payload URL:** `http://IP_ИЛИ_ДОМЕН:3000/webhook` (или https, если настроен прокси).
  - **Content type:** application/json.
  - **Secret:** тот же, что в `GITHUB_WEBHOOK_SECRET` на сервере.
  - **Events:** только push (или включён push).
- [ ] При необходимости — создан или исправлен вебхук (вручную или через API, если есть токен).

---

## Шаг 4. Sudoers (перезапуск сервисов без пароля)

- [ ] Для пользователя, от которого запущен `github-webhook`, настроен NOPASSWD для перезапуска:  
  `sudo -n systemctl restart analytics-dashboard`  
  `sudo -n systemctl restart grs-image-web`  
  Выполняются без запроса пароля. Если сервисы не установлены — допустимо получить «unit not found»; важно, что sudo не просит пароль.
- [ ] При необходимости правки по гайду: `sudo visudo` или файл в `/etc/sudoers.d/`.

---

## Шаг 5. End-to-end: push → деплой

- [ ] На сервере запущен просмотр логов:  
  `journalctl -u github-webhook -f`  
  (или в отдельной сессии оставлен вывод последних строк: `journalctl -u github-webhook -n 50`).
- [ ] Выполнен push в нужную ветку (например `main`):  
  `git push origin main`  
  (из локальной копии репо или через коммит в веб-интерфейсе).
- [ ] В логах `github-webhook` видно:
  - приём webhook (событие push);
  - успешный `git pull`;
  - обновление зависимостей (pip);
  - перезапуск сервисов (если они есть и настроен sudo).
- [ ] На сервере в `PROJECT_DIR`: `git log -1` — последний коммит совпадает с только что запушенным.
- [ ] При наличии сервисов: время перезапуска обновилось, например:  
  `systemctl show analytics-dashboard --property=ActiveEnterTimestamp`  
  (опционально).

---

## Шаг 6. Граничные проверки (по желанию)

- [ ] GET на `/webhook`:  
  `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/webhook`  
  Ожидается 404 (или 405).
- [ ] POST без подписи / с неверной подписью при заданном секрете: ожидается 403.
- [ ] POST с неверным Content-Type: ожидается 400.

---

## Итог

- Все пункты отмечены — деплой по вебхуку считается полностью проверенным.
- Результаты (что выполнено, что не удалось, вывод ключевых команд) можно зафиксировать в рефлексии задачи (например `memory-bank/reflection/reflection-webhook-002.md`).

---

## Для VPS с root и путём /root/contentzavod

Используется unit **docs/scripts/deploy_beget/github-webhook-root.service** (User=root, WorkingDirectory=/root/contentzavod). Секрет в unit не коммитится — подставляется на сервере при установке (или через `systemctl edit github-webhook`).
