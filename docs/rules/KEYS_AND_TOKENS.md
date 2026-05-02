# Ключи и токены проекта

Этот документ описывает все ключи и токены, используемые в проекте, и как их безопасно хранить.

---

## ⚠️ ВАЖНО: Безопасность

**НИКОГДА не коммитьте реальные ключи в Git!**

- ✅ Используйте `.env` файл для хранения ключей
- ✅ `.env` файл добавлен в `.gitignore`
- ✅ Коммитьте только `.env.example` с примерами
- ✅ Документируйте назначение каждого ключа

---

## 📁 Где хранить ключи

### Основной файл: `.env`

**Расположение:** Корень проекта (`ContentZavod/.env`)

**Создание:**
```bash
# Скопируйте пример
copy .env.example .env

# Или создайте вручную
notepad .env
```

**Формат:**
```env
# Комментарий
КЛЮЧ=значение
```

---

## Репозиторий проекта (для деплоя)

**Назначение:** Клонирование и обновление проекта на сервере (`git clone`, `git pull`).

| Способ | URL |
|--------|-----|
| HTTPS | `https://github.com/criper1573-beep/myflowoficcial.git` |
| SSH | `git@github.com:criper1573-beep/myflowoficcial.git` |

**Где используется:** сервер (85.198.66.62), путь `/root/contentzavod` — при первом развёртывании `git clone`, при обновлениях `git pull`. В .env не хранится.

---

### GitHub Webhook Secret (для деплоя по вебхуку)

**Назначение:** Подпись запросов от GitHub при настройке webhook (автодеплой после push). Задаётся в systemd-юните `github-webhook` и в настройках Webhooks репозитория на GitHub.

**Где задать:** На сервере в юните: `Environment=GITHUB_WEBHOOK_SECRET=твой-секрет`. В GitHub: Repo → Settings → Webhooks → у соответствующего webhook в поле Secret — тот же токен. В .env не хранится (только в конфиге сервиса на VPS).

**Где используется:** `webhook_server.py` — проверка заголовка `X-Hub-Signature-256`. См. **docs/guides/DEPLOY_WEBHOOK.md**.

---

## 🔑 Список всех ключей и токенов

### 1. GRS AI API (для AI генерации)

**Назначение:** Генерация контента через GRS AI API

```env
GRS_AI_API_KEY=your_grs_ai_api_key_here
GRS_AI_API_URL=https://grsaiapi.com
```

**Где получить:**
- Регистрация: https://grsai.com/
- Dashboard: https://grsai.com/dashboard
- Раздел: API Keys

**Используется в:**
- `blocks/ai_integrations/grs_ai_client.py`
- Генерация заголовков, текстов, хештегов

---

### 2. Telegram Bot (для NewsBot/Spambot)

**Назначение:** Автопостинг в Telegram канал

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel_name
TELEGRAM_BOT_TOKEN_2=...   # второй бот, на будущее (опционально)
```

**Где получить:**
- Создать бота: https://t.me/BotFather
- Команда: `/newbot`
- Токен: BotFather выдаст после создания
- Channel ID: Имя канала с @ (например, @flowcabinetnews)

**Если токен попал в Git (secret scanning):** отзови старый токен в BotFather (`/revoke`), создай новый, пропиши его только в `.env`. В коде и документации — только плейсхолдеры.

**Используется в:**
- Оркестратор, Post FLOW, блок **lifehacks_to_spambot** (ручная отправка статей в Telegram), другие блоки с публикацией в Telegram

**Дополнительно:**
- Бот должен быть администратором канала
- Права: Публикация сообщений

**Оркестратор на сервере (orchestrator-kz):** на VPS в `.env` должны быть те же `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHANNEL_ID`, что на рабочем компе (или `PROJECT_ID` и конфиг в `blocks/projects/data/`). Без них публикация в Telegram при каждом слоте падает с «Не заданы TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID». Скопируйте из локального `.env` в `/root/contentzavod/.env` (или куда развёрнут проект).

---

### 3. Проект по умолчанию (мультипроектность)

**Назначение:** Какой проект использовать по умолчанию в CLI-блоках, если не передан `--project`.

```env
PROJECT_ID=flowcabinet
```

**Используется в:**
- `blocks/projects/` — конфиг: `blocks/projects/data/<PROJECT_ID>.yaml`
- Блоки, которые принимают `--project` (автопостинг, утилиты)

---

### 4. Post FLOW (блок blocks/post_flow)

**Назначение:** Посты из Google Таблицы в канал FLOW (генерация через GRS AI + публикация в Telegram).

```env
GOOGLE_SHEET_ID=1gxYpX1FGm5VwtyUoZNKdd8EVYduvkmULpXL5TuOv5z4
GOOGLE_CREDENTIALS_PATH=credentials.json
TOPICS_SHEET_NAME=Лист1
TELEGRAM_CHANNEL=@myflowofficial
MODEL_GENERATION=gemini-3-pro
MODEL_FALLBACK=gpt-4o-mini
IMAGE_MODEL=nano-banana
```

**Где получить:**
- Google Sheet ID — из URL таблицы (docs.google.com/spreadsheets/d/**SHEET_ID**/edit)
- Сервисный аккаунт (JSON) — [Google Cloud Console](https://console.cloud.google.com/apis/credentials), сохранить как `blocks/post_flow/credentials.json`
- TELEGRAM_CHANNEL — канал FLOW (отдельно от TELEGRAM_CHANNEL_ID для NewsBot)

**Используется в:**
- `blocks/post_flow/config.py`, `sheets_client.py`, `telegram_client.py`, `content.py`

**Примечание:** `TELEGRAM_BOT_TOKEN` общий с NewsBot; для канала FLOW используется `TELEGRAM_CHANNEL` (по умолчанию @myflowofficial).

---

### 5. OpenAI API (опционально)

**Назначение:** Альтернативный AI провайдер

```env
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...
```

**Где получить:**
- Регистрация: https://platform.openai.com/
- API Keys: https://platform.openai.com/api-keys

**Используется в:**
- Планируется в блоке `blocks/ai_integrations/openai_adapter.py`

---

### 6. Yandex GPT (опционально)

**Назначение:** Российский AI провайдер

```env
YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_folder_id
```

**Где получить:**
- Yandex Cloud: https://cloud.yandex.ru/
- Раздел: API ключи

**Используется в:**
- Планируется в блоке `blocks/ai_integrations/yandex_adapter.py`

---

### 7. VK API (для автопостинга ВКонтакте)

**Назначение:** Публикация в группу ВКонтакте

```env
VK_ACCESS_TOKEN=your_vk_access_token
VK_GROUP_ID=123456789
VK_API_VERSION=5.131
```

**Где получить:**
- Создать приложение: https://vk.com/apps?act=manage
- Получить токен: https://vk.com/dev/access_token
- Group ID: ID группы (цифры)

**Используется в:**
- Планируется в блоке `blocks/autopost_vk/`

---

### 8. Яндекс.Дзен API (опционально)

**Назначение:** Публикация статей в Дзен (API)

```env
YANDEX_ZEN_TOKEN=your_zen_token
YANDEX_ZEN_CHANNEL_ID=your_channel_id
```

**Где получить:**
- Дзен для авторов: https://zen.yandex.ru/
- Студия Дзена: https://dzen.ru/profile/editor/flowcabinet
- Настройки → API

**Используется в:**
- Планируется в блоке `blocks/autopost_zen/`

---

### 8a. Дзен автопостинг (Playwright)

**Назначение:** Публикация статей в Дзен через браузерную автоматизацию

```env
# Опционально: для входа по паролю (если нет storage_state)
# ZEN_EMAIL=your_email@example.com
# ZEN_PASSWORD=your_password

ZEN_STORAGE_STATE=zen_storage_state.json
ZEN_EDITOR_URL=https://dzen.ru/profile/editor/flowcabinet

ZEN_HEADLESS=false
ZEN_BROWSER_TIMEOUT=60000
ZEN_KEEP_OPEN=false
```

**Где получить:**
- Cookies сохранить: `python docs/scripts/scripts/capture_cookies.py --url https://dzen.ru --output zen_storage_state.json`
- Студия Дзена: https://dzen.ru/profile/editor/flowcabinet

**Используется в:**
- `blocks/autopost_zen/` — zen_client.py, zen_http_server.py

---

### 8b. Дзен автогенерация статей (--auto)

**Назначение:** Генерация статей из темы в Google Sheets и публикация в Дзен

```env
ZEN_TOPICS_SHEET_NAME=Лист2
ZEN_ARTICLE_MODEL=gemini-2.5-pro
ZEN_HEADLINE_MODEL=gpt-4o-mini
ZEN_IMAGE_MODEL=gpt-image-1
ZEN_COVER_REF_FACE=https://i.postimg.cc/jdwFhwpV/photo_2026_02_05_10_46_02.jpg
```

**Где получить:**
- `ZEN_TOPICS_SHEET_NAME` — имя листа в той же Google Таблице (GOOGLE_SHEET_ID). Формат: столбец A = тема, B = доп. контекст (опционально).
- Модели — GRS AI (grsai.com). По умолчанию: `gemini-2.5-pro` (статьи), `gpt-4o-mini` (заголовки/мета), `gpt-image-1` (картинки).
- `ZEN_COVER_REF_FACE` — URL фото автора для обложки (nano-banana-pro).

**Используется в:**
- `blocks/autopost_zen/article_generator.py`
- Запуск: `python -m blocks.autopost_zen --auto --publish`

---

### 9. Яндекс Вордстат API (сбор ключевых слов)

**Назначение:** Получение данных по частотности поисковых запросов из Яндекс Вордстата для SEO-анализа и подбора ключевых слов.

```env
YANDEX_WORDSTAT_TOKEN=y0__your_oauth_token_here
```

**Где получить:**
1. Авторизоваться с Яндекс ID: https://passport.yandex.ru/
2. Создать OAuth-приложение: https://oauth.yandex.ru/ → «Для доступа к API или отладки»
3. В разделе «Доступ к данным» выбрать «Использование API Вордстата»
4. Получить `ClientId` и подать заявку на доступ через поддержку Яндекс Директа

**API:**
- Базовый URL: `https://api.wordstat.yandex.net`
- Метод: **POST** (тело JSON), заголовок `Content-Type: application/json; charset=utf-8`
- Авторизация: `Authorization: Bearer <OAuth-токен>`
- Для топ-фраз по запросу: **POST /v1/topRequests**, тело `{"phrase": "..."}` или `{"phrases": ["...", ...], "numPhrases": 100}`
- Структура API: https://yandex.ru/support2/wordstat/ru/content/api-structure
- Лимиты: по ответу /v1/userInfo (запросов/сек и в сутки)

**Используется в:**
- `blocks/autopost_zen/wordstat_client.py` — подбор ключевых слов для SEO-заголовков и статей
- `blocks/autopost_zen/article_generator.py` — пайплайн генерации (сиды → Wordstat → заголовок → текст)
- Тест: `python blocks/autopost_zen/test_wordstat.py` (запрос по умолчанию: «ремонт офисов»)

---

### 9a. Аналитика пайплайна и Telegram Mini App

**Назначение:** Доступ к дашборду аналитики с телефона через бота (кнопка меню «Дашборд», команды /stats, /analytics). Тот же бот, что в проекте (TELEGRAM_BOT_TOKEN).

```env
DASHBOARD_PUBLIC_URL=https://your-dashboard.example.com
# или ANALYTICS_DASHBOARD_URL=...
```

**Где взять URL:**
- Деплой дашборда на VPS/Railway/Render с HTTPS — подставить этот URL.
- Локально: туннель (ngrok, cloudflared) на `http://localhost:8050` — в боте указать HTTPS-URL туннеля.

**Используется в:**
- `blocks/analytics/telegram_bot.py` — установка кнопки меню и обработка /stats, /analytics.
- Запуск бота: `python -m blocks.analytics.telegram_bot`

**Локальный дашборд — статус сервисов с сервера:**

```env
ANALYTICS_SERVER_SERVICES_URL=http://85.198.66.62
```

**Назначение:** При запуске дашборда не на Linux (например, локально на Windows) блок «Сервисы на сервере» по умолчанию пустой (нет systemctl). Если задать этот URL — дашборд запрашивает `/api/server-services` с указанного сервера и показывает статусы сервисов (дашборд, бот, спамбот, watchdog).

**Quickpack — проверка по HTTP (сайт без systemd-юнита):**

```env
QUICKPACK_URL=https://твой-сайт-quickpack.ru
```

**Назначение:** На сервере в блоке «Сервисы на сервере» плашка Quickpack определяется по systemd-юниту `quickpack`. Если сайт отдаётся через nginx без отдельного юнита — задай здесь URL главной страницы; дашборд будет считать сервис работающим при ответе HTTP 200. **Watchdog:** если `QUICKPACK_URL` задан в `.env` на сервере, где запущен watchdog (`contentzavod-watchdog`), проверка Quickpack идёт по HTTP (200 = работает); алерты «Сервис упал» по quickpack не шлются из-за отсутствия systemd-юнита.

**Используется в:** `blocks/analytics/api.py` — эндпоинт `/api/server-services`; `blocks/analytics/watchdog_services.py` — проверка Quickpack по URL вместо systemd.

**Watchdog (алерты при падении сервисов на сервере):**

```env
TELEGRAM_ALERT_CHAT_ID=123456789
```

**Где взять chat_id:** написать боту @userinfobot в Telegram — он вернёт твой ID. Либо отправить любое сообщение боту проекта и посмотреть в логах/getUpdates.

**Используется в:**
- `blocks/analytics/watchdog_services.py` — при падении любого из сервисов (дашборд, бот, спамбот) отправляет сообщение в этот чат. Тот же `TELEGRAM_BOT_TOKEN`.

---

### 9b. Генерация изображений — веб (blocks/grs_image_web)

**Назначение:** Авторизация через Telegram на странице генерации изображений GRS AI; история генераций хранится по аккаунту (каждый пользователь видит только свои генерации).

```env
TELEGRAM_BOT_TOKEN=1234567890:ABC...
GRS_IMAGE_WEB_BOT_USERNAME=YourImageBot
# Опционально:
GRS_IMAGE_WEB_SESSION_SECRET=random_secret_for_cookies
GRS_IMAGE_WEB_HOST=127.0.0.1
GRS_IMAGE_WEB_PORT=8765
```

**Где получить:**
- `TELEGRAM_BOT_TOKEN` — тот же бот, что в проекте, или отдельный бот. Используется для **проверки подписи** данных от Telegram Login Widget (виджет «Войти через Telegram»).
- `GRS_IMAGE_WEB_BOT_USERNAME` — **имя бота без @** (например, `FlowImageBot`). В [@BotFather](https://t.me/BotFather) выполнить `/setdomain` и указать домен сайта, на котором открыта страница (для локальной разработки можно использовать туннель ngrok/cloudflared и указать его домен).

**Используется в:**
- `blocks/grs_image_web/auth.py` — верификация hash от Telegram, подпись сессионной cookie.
- `blocks/grs_image_web/api.py` — эндпоинты `/api/auth/telegram`, `/api/me`, `/api/generate`, `/api/history`; раздача файлов из `generated/<telegram_id>/`.

**Примечание:** Генерации сохраняются в папке `blocks/grs_image_web/generated/<telegram_id>/`; доступ к файлам только у владельца по сессионной cookie. Для **локального запуска без входа** авторизацию можно отключить: не задавать `GRS_IMAGE_WEB_REQUIRE_AUTH` или задать `GRS_IMAGE_WEB_REQUIRE_AUTH=false` — тогда страница работает без Telegram, все генерации сохраняются в `generated/0/`. На сервере задать `GRS_IMAGE_WEB_REQUIRE_AUTH=true`.

---

### 9b2. Визуализатор кабинетов FlowCabinet (blocks/flowcabinet_visualizer)

**Назначение:** Веб-сервис визуализации кабинета в помещении (1 фото → проверка композиции → 3 варианта). Для генерации используется тот же GRS AI, что и для grs_image_web.

**Ключи:** те же `GRS_AI_API_KEY` и `GRS_AI_API_URL` (см. выше). Опционально: `FLOWCABINET_VIZ_HOST=0.0.0.0`, `FLOWCABINET_VIZ_PORT=8777` для деплоя на сервере; `FLOWCABINET_VIZ_ADMIN_PASSWORD` — пароль для доступа к админ-панели `/admin` (референсы и промпты; если не задан — админка возвращает 404).

**Используется в:** `blocks/flowcabinet_visualizer/api.py`, `blocks/flowcabinet_visualizer/pipeline.py`, `blocks/flowcabinet_visualizer/admin_auth.py`. Деплой: `docs/guides/DEPLOY_FLOWCABINET_VISUALIZER.md`.

---

### 9c2. Zakazy Forwarder (blocks/zakazy_forwarder)

**Назначение:** Чтение чата [t.me/zakazyff](https://t.me/zakazyff) от имени пользователя (Telethon) и пересылка сообщений с фразой «Новый Заказ на упаковку и отгрузку» в отдельный чат.

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
ZAKAZY_SOURCE=zakazyff
ZAKAZY_DESTINATION=@channel_or_chat
ZAKAZY_BOT_TOKEN=123456:ABC...   # токен бота для отправки в канал (получить у @BotFather)
# Опционально:
ZAKAZY_TRIGGER=Новый Заказ на упаковку и отгрузку
ZAKAZY_SESSION_PATH=blocks/zakazy_forwarder/zakazy_forwarder.session
```

**Где получить:**
- **TELEGRAM_API_ID** и **TELEGRAM_API_HASH** — [my.telegram.org](https://my.telegram.org) → API development tools → создать приложение.
- **ZAKAZY_DESTINATION** — @username чата/канала или числовой chat_id (например `-1001234567890`). Ваш аккаунт должен иметь доступ к этому чату.

**Используется в:**
- `blocks/zakazy_forwarder/config.py`, `blocks/zakazy_forwarder/forwarder.py`
- Запуск: `python -m blocks.zakazy_forwarder`

**Примечание:** При первом запуске Telethon запросит номер телефона и код из Telegram (и пароль 2FA при включённой двухфакторной аутентификации). Сессия сохраняется в файл `*.session` (не коммитить; в `.gitignore` добавлено `*.session`).

---

### 9c. Смета — материалы (estimate_materials)

**Назначение:** Веб-сервис расчёта материалов по смете (в папке `estimate_materials/` в корне проекта). Опциональные переменные для порта и пути к БД.

```env
# Опционально (значения по умолчанию указаны ниже):
ESTIMATE_MATERIALS_PORT=8052
ESTIMATE_MATERIALS_DATABASE=путь/к/estimate_materials/data/estimate_materials.db
```

По умолчанию БД создаётся в `estimate_materials/data/estimate_materials.db`; порт 8052. Используется в `estimate_materials/config.py`; .env читается из корня КонтентЗавода.

---

### 10. SSH-доступ к серверу (VPS)

**Назначение:** Удалённый доступ к серверу для деплоя, перезапуска сервисов и мониторинга

```env
SERVER_HOST=85.198.66.62
SERVER_USER=root
SERVER_SSH_PASSWORD=your_ssh_password_here
```

Реальные значения хранить только в `.env` (не коммитить). Для plink/pscp при деплое использовать тот же пароль в переменной сеанса `DEPLOY_SSH_PASSWORD`.

**Для скрипта загрузки архива на сервер** (Windows, `docs/scripts/deploy_beget/make_zip_and_upload.ps1`) задай в том же сеансе:
- `DEPLOY_SSH_PASSWORD` — тот же пароль SSH (скрипт передаёт его в pscp). Не коммитить, не хранить в репозитории.

**Подключение:**
- Через PuTTY/plink: `plink -ssh root@85.198.66.62 -pw "PASSWORD" "command"`
- Через OpenSSH: `ssh root@85.198.66.62`

**Используется для:**
- Деплоя, `docs/scripts/deploy_beget/*.ps1`, диагностики по SSH
- Перезапуск сервисов: `systemctl restart orchestrator-kz`, `systemctl restart nginx` и т.д.
- Просмотр логов: `journalctl -u <unit> --no-pager -n 50`
- Обновление конфигов и кода на VPS
- Блоки: `blocks/analytics/`, `blocks/autopost_zen/`, `blocks/grs_image_web/` и др.
- Деплой GRS Image Web и домен flowimage.ru: см. `docs/guides/DEPLOY_GRS_IMAGE_WEB.md`

---

### 10.1. Amnezia VPN — проверка VPS (опционально)

**Назначение:** IP и пользователь SSH для скрипта проверки готовности VPS к установке Amnezia VPN.

```env
AMNEZIA_VPS_IP=1.2.3.4
AMNEZIA_SSH_USER=root
```

**Где используется:** `docs/scripts/check_amnezia_server.py` — проверка доступности SSH (порт 22) и при наличии OpenSSH проверка Docker на сервере. Пароль SSH в .env не хранится — ввод только в клиенте Amnezia. Гайд: `docs/guides/AMNEZIA_VPN_OWN_SERVER.md`.

---

### 11. Pinterest API (опционально)

**Назначение:** Публикация пинов

```env
PINTEREST_ACCESS_TOKEN=your_pinterest_token
PINTEREST_BOARD_ID=your_board_id
```

**Где получить:**
- Pinterest Developers: https://developers.pinterest.com/
- Создать приложение

**Используется в:**
- Планируется в блоке `blocks/autopost_pinterest/`

---

### 11. vc.ru API (опционально)

**Назначение:** Публикация статей на vc.ru

```env
VCRU_TOKEN=your_vcru_token
VCRU_SUBSECTION_ID=123456
```

**Где получить:**
- vc.ru API: https://vc.ru/api
- Личный кабинет

**Используется в:**
- Планируется в блоке `blocks/autopost_vcru/`

---

### 12. База данных (опционально)

**Назначение:** Хранение контента и истории

```env
DATABASE_URL=sqlite:///storage/content.db
# Или для PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/dbname
```

**Используется в:**
- Планируется в блоке `blocks/storage/`

---

### 13. Логирование и мониторинг

**Назначение:** Настройка логирования

```env
LOG_LEVEL=INFO
LOG_FILE=storage/logs/app.log
```

**Возможные значения LOG_LEVEL:**
- `DEBUG` - детальная отладка
- `INFO` - общая информация
- `WARNING` - предупреждения
- `ERROR` - только ошибки
- `CRITICAL` - критические ошибки

**Используется в:**
- Все блоки проекта

---

## 📋 Полный шаблон .env файла

Скопируйте этот шаблон в `.env` и заполните нужные значения:

```env
# ============================================
# GRS AI API
# ============================================
GRS_AI_API_KEY=your_grs_ai_api_key_here
GRS_AI_API_URL=https://grsaiapi.com

# Проект по умолчанию (NewsBot)
PROJECT_ID=flowcabinet

# ============================================
# Telegram Bot (NewsBot/Spambot)
# ============================================
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel_name

# ============================================
# Post FLOW (blocks/post_flow)
# ============================================
# GOOGLE_SHEET_ID=1gxYpX1FGm5VwtyUoZNKdd8EVYduvkmULpXL5TuOv5z4
# GOOGLE_CREDENTIALS_PATH=credentials.json
# TOPICS_SHEET_NAME=Лист1
# TELEGRAM_CHANNEL=@myflowofficial
# MODEL_GENERATION=gemini-3-pro
# MODEL_FALLBACK=gpt-4o-mini
# IMAGE_MODEL=nano-banana

# ============================================
# OpenAI (опционально)
# ============================================
# OPENAI_API_KEY=sk-...
# OPENAI_ORG_ID=org-...

# ============================================
# Yandex GPT (опционально)
# ============================================
# YANDEX_API_KEY=your_yandex_api_key
# YANDEX_FOLDER_ID=your_folder_id

# ============================================
# VK API (опционально)
# ============================================
# VK_ACCESS_TOKEN=your_vk_access_token
# VK_GROUP_ID=123456789
# VK_API_VERSION=5.131

# ============================================
# Яндекс.Дзен (опционально)
# ============================================
# YANDEX_ZEN_TOKEN=your_zen_token
# YANDEX_ZEN_CHANNEL_ID=your_channel_id

# ============================================
# Яндекс Вордстат API
# ============================================
# YANDEX_WORDSTAT_TOKEN=y0__your_oauth_token_here

# ============================================
# Pinterest (опционально)
# ============================================
# PINTEREST_ACCESS_TOKEN=your_pinterest_token
# PINTEREST_BOARD_ID=your_board_id

# ============================================
# vc.ru (опционально)
# ============================================
# VCRU_TOKEN=your_vcru_token
# VCRU_SUBSECTION_ID=123456

# ============================================
# База данных (опционально)
# ============================================
# DATABASE_URL=sqlite:///storage/content.db
# DATABASE_URL=postgresql://user:password@localhost/dbname

# ============================================
# Логирование
# ============================================
LOG_LEVEL=INFO
LOG_FILE=storage/logs/app.log

# ============================================
# Другие настройки
# ============================================
# ENVIRONMENT=development
# DEBUG=False
```

---

## 🔒 Правила безопасности

### ✅ Что МОЖНО делать:

1. Хранить ключи в `.env` файле
2. Использовать `python-dotenv` для загрузки
3. Коммитить `.env.example` с примерами
4. Документировать назначение ключей
5. Использовать переменные окружения в production

### ❌ Что НЕЛЬЗЯ делать:

1. Коммитить `.env` файл в Git
2. Хардкодить ключи в коде
3. Отправлять ключи в мессенджерах
4. Публиковать ключи в открытом доступе
5. Использовать одни ключи для dev и production

---

## 💻 Использование в коде

### Python (с python-dotenv)

```python
import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Получение значений
API_KEY = os.getenv("GRS_AI_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверка наличия
if not API_KEY:
    raise ValueError("GRS_AI_API_KEY must be set in .env file")
```

### Python (без dotenv)

```python
import os

# Переменные окружения (установлены системой или через export/set)
API_KEY = os.getenv("GRS_AI_API_KEY")
```

### BAT-файл (Windows)

```bat
@echo off

REM Загрузка переменных из .env
for /f "usebackq tokens=1,* delims==" %%a in (.env) do (
    set "%%a=%%b"
)

REM Использование
echo Bot Token: %TELEGRAM_BOT_TOKEN%
```

### Bash (Linux/Mac)

```bash
#!/bin/bash

# Загрузка переменных из .env
export $(cat .env | xargs)

# Использование
echo "Bot Token: $TELEGRAM_BOT_TOKEN"
```

---

## 🔄 Ротация ключей

**Рекомендуется периодически менять ключи для безопасности**

### Когда менять:

1. ✅ Ключ скомпрометирован (утечка)
2. ✅ Раз в 3-6 месяцев (плановая ротация)
3. ✅ При смене команды/доступов
4. ✅ После обнаружения подозрительной активности

### Как менять:

1. Создать новый ключ в сервисе
2. Обновить `.env` файл
3. Перезапустить все боты/сервисы
4. Удалить старый ключ в сервисе
5. Проверить работоспособность

---

## 📊 Проверка безопасности

### Перед коммитом в Git:

```bash
# Проверить, что .env в .gitignore
cat .gitignore | grep .env

# Проверить staged файлы на наличие секретов
git diff --cached | grep -i "token\|key\|password\|secret"

# Проверить историю на наличие секретов
git log -p | grep -i "token\|key\|password"
```

### Если случайно закоммитили ключ:

```bash
# 1. Немедленно смените ключ в сервисе!
# 2. Удалите из истории Git (опасная операция!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Форсированный push (если уже запушили)
git push origin --force --all
```

---

## 🆘 Что делать при утечке ключа

### Немедленные действия:

1. ✅ **Отозвать скомпрометированный ключ** в сервисе
2. ✅ **Создать новый ключ**
3. ✅ **Обновить .env файл**
4. ✅ **Перезапустить все сервисы**
5. ✅ **Проверить логи на подозрительную активность**
6. ✅ **Удалить ключ из Git истории** (если был закоммичен)

### Контакты служб поддержки:

- **GRS AI:** https://grsai.com/support
- **Telegram:** https://t.me/BotSupport
- **OpenAI:** https://help.openai.com/
- **VK:** https://vk.com/support

---

## 📝 Чеклист настройки

### Первоначальная настройка:

- [ ] Скопировать `.env.example` в `.env`
- [ ] Получить все необходимые ключи
- [ ] Заполнить `.env` файл
- [ ] Проверить, что `.env` в `.gitignore`
- [ ] Протестировать работу с ключами
- [ ] Документировать назначение ключей
- [ ] Настроить резервное копирование `.env` (локально!)

### Регулярное обслуживание:

- [ ] Проверять актуальность ключей (раз в месяц)
- [ ] Ротация ключей (раз в 3-6 месяцев)
- [ ] Проверка логов на подозрительную активность
- [ ] Обновление документации при добавлении новых ключей

---

## 🔗 См. также

- [PROJECT_RULES.md](PROJECT_RULES.md) - Правило 5: Переменные окружения
- [PROJECT_RULES.md](PROJECT_RULES.md) - Правило 9: Безопасность
- [.env.example](.env.example) - Пример файла с ключами
- [.gitignore](.gitignore) - Список игнорируемых файлов

---

**Последнее обновление:** 2026-02-01  
**Версия:** 1.0  
**Статус:** 🔒 Конфиденциально - не распространять
