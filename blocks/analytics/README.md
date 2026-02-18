# Аналитика пайплайна КонтентЗавод

Дашборд по запускам публикаций (сводка, график, лента с шагами и ошибками). Доступ с телефона — через Telegram Mini App.

---

## Как открыть дашборд в Telegram

### Шаг 1. Дашборд должен быть доступен по HTTPS

Telegram открывает Mini App только по **HTTPS**. Варианты:

- **Вариант A.** Развернули дашборд на сервере (VPS, Railway, Render и т.п.) — у вас уже есть URL вида `https://your-app.example.com`.
- **Вариант B.** Дашборд крутится у вас на компе (`python -m blocks.analytics` → http://localhost:8050). Тогда нужен **туннель**, чтобы с интернета до него достучаться по HTTPS, например:
  - [ngrok](https://ngrok.com): `ngrok http 8050` → выдаст URL вида `https://abc123.ngrok.io`
  - [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps): `cloudflared tunnel --url http://localhost:8050` → свой HTTPS-URL

Скопируйте этот **HTTPS-URL** (например `https://abc123.ngrok.io` или ваш домен).

### Шаг 2. Прописать URL в .env

В корне проекта в файле `.env` добавьте (или измените):

```env
DASHBOARD_PUBLIC_URL=https://ваш-https-url-сюда
```

То есть подставьте тот самый HTTPS-адрес дашборда из шага 1.

### Шаг 3. Запустить бота аналитики

В терминале из корня проекта:

```bash
python -m blocks.analytics.telegram_bot
```

Бот должен работать постоянно (не закрывать окно). Он использует тот же токен, что и остальной проект — `TELEGRAM_BOT_TOKEN` из `.env`.

### Шаг 4. Открыть дашборд в Telegram

1. Откройте Telegram (на телефоне или на компе).
2. Найдите **вашего бота** (тот, чей токен указан в `TELEGRAM_BOT_TOKEN`).
3. Откройте чат с ботом.
4. Сделайте одно из двух:
   - **Кнопка меню:** рядом с полем ввода (или внизу слева) нажмите кнопку меню — там должна быть кнопка **«Дашборд»**. Нажмите её → откроется дашборд во встроенном окне (Mini App).
   - **Команды:** отправьте боту команду `/stats` или `/analytics`. Бот пришлёт сообщение с кнопкой **«Открыть дашборд»**. Нажмите её → откроется тот же дашборд.

После этого дашборд откроется прямо в Telegram (сводка, график, список запусков, клик по красным шагам — описание ошибки).

---

## Откуда дашборд берёт данные

- **Проекты:** в шапке дашборда справа можно выбрать проект — **FLOW** или **Фулфилмент**. У каждого проекта своя БД: `storage/analytics_flow.db` и `storage/analytics_fulfilment.db`. Вся аналитика (сводка, график, запуски) подгружается из выбранного проекта.
- **Legacy одна база:** если не использовать переключатель, по умолчанию используется `storage/analytics.db` (или путь из `ANALYTICS_DB_PATH` в `.env`).
- **Когда появляются записи:**
  - **Режим `--auto`** — полный цикл (тема из Google Sheets → генерация → публикация). Каждый шаг пишется в трекер.
  - **Режим `--file --publish`** — публикация готовой статьи из JSON; в дашборд записывается один запуск с шагом «Публикация в Дзен».

**Как писать в нужный проект из пайплайна:** задайте переменную окружения `ANALYTICS_PROJECT=flow` или `ANALYTICS_PROJECT=fulfilment` перед запуском автопостинга (или в systemd/cron). Тогда RunTracker будет писать в соответствующую БД. По умолчанию — `flow`.

**Важно: сервер и локальный комп — разные БД.**

- Если дашборд запущен **на сервере** (VPS, Beget и т.п.), он читает **базу на сервере**. Запуски, которые вы делаете **локально** (на своём компе), пишутся в **локальную** `storage/analytics.db` и **не попадают** на серверный дашборд.
- Чтобы видеть **локальные** публикации — запускайте дашборд **локально**: `python -m blocks.analytics` и откройте http://localhost:8050.
- Чтобы в дашборде на сервере были видны запуски — автопостинг должен выполняться **на том же сервере** (cron, systemd и т.д.), тогда и дашборд, и скрипты используют одну и ту же БД.

**Раздел Generation (картинки и ссылки с flowimage.ru):** данные берутся с локальной ФС — папки `blocks/grs_image_web/generated` и `blocks/grs_image_web/uploaded`. Если дашборд и grs_image_web на одном сервере в одном репо — пути по умолчанию подходят. Если дашборд развёрнут из другого каталога/репо — задай в `.env` абсолютные пути:
- `GRS_IMAGE_WEB_DIR` — корень блока grs_image_web (например `/root/contentzavod/blocks/grs_image_web`);
- или по отдельности: `GRS_IMAGE_WEB_GENERATED_DIR`, `GRS_IMAGE_WEB_UPLOADED_DIR`. Подробнее: `docs/guides/DEPLOY_DASHBOARD_FLOWIMAGE_STORE.md`.

---

## Только дашборд на компе (без Telegram)

Если нужен только локальный просмотр:

```bash
python -m blocks.analytics
```

Откройте в браузере: http://localhost:8050

Тестовые данные (чтобы не было пусто):

```bash
python -m blocks.analytics.seed_test_data
```

---

## Почему Telegram-бот дашборда не работает

Если сервис «Telegram-бот дашборда» на дашборде показывается красным или постоянно перезапускается, проверь по шагам.

### 1. Переменные в `.env` на сервере

В каталоге проекта на сервере (например `/root/contentzavod`) в файле `.env` должны быть:

| Переменная | Назначение |
|------------|------------|
| **TELEGRAM_BOT_TOKEN** | Токен бота от @BotFather. Без него бот сразу завершается с ошибкой. |
| **DASHBOARD_PUBLIC_URL** | HTTPS-адрес дашборда, например `https://flowimage.store`. Нужен для кнопки «Дашборд» и команды /stats. |

Проверка: на сервере `grep -E 'TELEGRAM_BOT_TOKEN|DASHBOARD_PUBLIC_URL' /root/contentzavod/.env` — обе строки должны быть заданы (без решётки в начале).

### 2. Юнит systemd

Должен существовать файл `/etc/systemd/system/analytics-telegram-bot.service`. Пример — в репозитории: `docs/scripts/deploy_beget/analytics-telegram-bot.service.example`. В нём подставь пользователя и путь к проекту (как в юните дашборда), затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable analytics-telegram-bot
sudo systemctl start analytics-telegram-bot
```

### 3. Зависимости в venv

Бот использует библиотеку `python-telegram-bot`. На сервере в виртуальном окружении проекта:

```bash
cd /root/contentzavod
./venv/bin/pip install python-telegram-bot>=21.0
```

(Если ставишь зависимости из `docs/config/requirements.txt`, эта библиотека там уже есть.)

### 4. Логи сервиса

Чтобы увидеть причину падения или ошибку при старте:

```bash
sudo journalctl -u analytics-telegram-bot -n 50 --no-pager
```

Типичные сообщения:

- **«TELEGRAM_BOT_TOKEN не задан в .env»** — добавь в `.env` на сервере строку `TELEGRAM_BOT_TOKEN=...` (токен от @BotFather).
- **«Дашборд недоступен»** (в ответ на /stats в Telegram) — задай в `.env` на сервере `DASHBOARD_PUBLIC_URL=https://flowimage.store` (или твой URL дашборда) и перезапусти сервис: `sudo systemctl restart analytics-telegram-bot`.
