# Патчи и история изменений

Единый документ: версии релизов и пофайловые описания патчей.  
Текущая версия: **2.1.0** (см. [docs/config/VERSION](../config/VERSION)). Workflow: [CHANGELOG_WORKFLOW.md](CHANGELOG_WORKFLOW.md)

---

## Оглавление

| Версия / Патч | Дата | Описание |
|---------------|------|----------|
| [v2.1.0](#v210---2026-02-18---dev-ветка-и-история-патчей) | 2026-02-18 | Dev-ветка и история патчей |
| [2026-02-01 GRS AI](#2026-02-01---grs-ai-integration) | 2026-02-01 | GRS AI Integration |
| [2026-02-01 Backup](#2026-02-01---backup-system) | 2026-02-01 | Backup System |
| [2026-02-01 Spambot](#2026-02-01---spambot-newsbot) | 2026-02-01 | Spambot (NewsBot) |
| [2026-02-01 Project Rules](#2026-02-01---project-rules) | 2026-02-01 | Project Rules |
| [2026-02-01 Keys](#2026-02-01---keys-and-tokens-management) | 2026-02-01 | Keys and Tokens Management |
| [2026-02-01 Launch](#2026-02-01---spambot-launch-scripts) | 2026-02-01 | Spambot Launch Scripts |
| [zen-autopost-scheduler](#zen-autopost-scheduler) | 2026-02-19 | Планировщик Дзен, дашборд (сервисы списком, Запустить/Остановить) |
| [orchestrator-kz-deploy](#orchestrator-kz-deploy) | 2026-02-20 | Оркестратор контент завода: переименование, обязательный пробный запуск при старте, дашборд, деплой |
| [orchestrator-stability-telegram-recovery](#orchestrator-stability-telegram-recovery) | 2026-02-20 | Стабилизация после инцидентов: лишние генерации, Telegram env на сервере, cleanup аналитики |
| [flowcabinet-visualizer](#flowcabinet-visualizer) | 2026-02-21 | Визуализатор кабинетов FlowCabinet: 1 фото → проверка композиции → 3 варианта, кнопка «Скачать» |
| [flowcabinet-visualizer-admin](#flowcabinet-visualizer-admin) | 2026-02-21 | Админ-панель визуализатора: референсы по размеру/отделке, промпты, защита паролем |
| [flowcabinet-visualizer-admin-ux](#flowcabinet-visualizer-admin-ux) | 2026-02-21 | Админка: один шаблон промпта, RU→EN перевод (Google), drag-drop референсов, фикс авторизации |
| [cabinet-scale-viewer](#cabinet-scale-viewer) | 2026-02-21 | Cabinet Scale Viewer: наложение 3D на фото, пол по красным точкам, перспективный масштаб |
| [cabinet-scale-viewer-calibration](#cabinet-scale-viewer-calibration) | 2026-02-21 | Калибровка камеры: fallback 5pt→4pt, порог 80px, режим в UI, проба инвертированной высоты |
| [run-source-in-logs](#run-source-in-logs) | 2026-02-22 | Источник запуска (run_id, source) в логах; скрипты и доки для просмотра по run_id |
| [orchestrator-pause-resume](#orchestrator-pause-resume) | 2026-02-22 | Приостановка оркестратора по файлу; один раз остановить — не перезапускать и не генерировать; инструкция по новому запуску |
| [orchestrator-single-service-manual-run](#orchestrator-single-service-manual-run) | 2026-02-22 | Единый сервис оркестратора, без автопрогона при старте; отдельная кнопка «Разовый прогон» в дашборде |
| [script-board-project-picker](#script-board-project-picker) | 2026-02-22 | Доска скриптов: выбор/создание проектов, модалка «Выбрать проект», хранение в localStorage |
| [script-board-deploy-grs](#script-board-deploy-grs) | 2026-02-22 | Деплой Script Board: передача GRS_AI ключей из локального .env на сервер для генерации |

---

## Краткая история версий

## [v2.1.0] - 2026-02-18 - Dev-ветка и история патчей

### ✅ Добавлено

- **Dev-ветка с деплоем на поддомен**
  - Ветка `dev` — тестирование на dev.flowimage.ru до merge в main
  - `webhook_server.py`: push в main → production, push в dev → staging (при настроенном PROJECT_DIR_STAGING)
  - Гайд [GIT_BRANCHING.md](GIT_BRANCHING.md) — workflow веток
  - Гайд [DEPLOY_STAGING.md](DEPLOY_STAGING.md) — настройка staging
- **Версионирование и история патчей**
  - `docs/config/VERSION` — текущая версия (2.1.0)
  - [CHANGELOG_WORKFLOW.md](CHANGELOG_WORKFLOW.md) — как нумеровать релизы и вести историю
  - Формат записей с версиями: `[vX.Y.Z] - YYYY-MM-DD`
- **Deploy-скрипты**
  - `grs-image-web-staging.service.example` — systemd unit для staging (порт 8766)
  - `nginx-flowimage-dev.conf.example` — Nginx для dev.flowimage.ru

### 📝 Изменено

- **webhook_server.py** — разбор `ref` в payload: main → prod, dev → staging
- **DEPLOY_WEBHOOK.md** — переменная PROJECT_DIR_STAGING, описание поведения по веткам

---

## [2026-02-01] - GRS AI Integration

### ✅ Добавлено

#### Блок GRS AI Client
- **`blocks/ai_integrations/grs_ai_client.py`** - Универсальный клиент для работы с GRS AI API
  - Поддержка обычного и потокового режима
  - Автоматическая обработка кодировки UTF-8
  - Парсинг различных форматов ответов
  - Fallback на другие модели при ошибках
  - Обработка всех типов ошибок API
  - Поддержка всех доступных моделей (быстрые, мощные, простые)

#### Документация
- **`GRS_AI_API_INTEGRATION.md`** - Полная документация по интеграции с GRS AI API
- **`blocks/ai_integrations/README.md`** - Документация по использованию GRS AI Client
- **`blocks/ai_integrations/USAGE_IN_BLOCKS.md`** - Примеры использования в блоках
- **`blocks/ai_integrations/QUICK_REFERENCE.md`** - Краткий справочник
- **`GETTING_STARTED.md`** - Руководство для быстрого старта

#### Инфраструктура
- **`requirements.txt`** - Список зависимостей проекта
- **`.env.example`** - Пример файла с переменными окружения
- **`scripts/test_grs_ai.py`** - Тестовый скрипт для проверки GRS AI Client

### 📝 Изменено

- **`README.md`** - Обновлен главный README
- **`BLOCKS_REGISTRY.md`** - B1 (grs_ai_client) статус `ready`

---

## [2026-02-01] - Backup System

### ✅ Добавлено

- **`scripts/backup_manager.py`** - Утилита управления бекапами
- **`BACKUP_SYSTEM.md`**, **`BACKUP_QUICK_START.md`** - Документация

### 📝 Изменено

- **`.gitignore`** - Правила для бекапов
- **`README.md`** - Ссылки на документацию по бекапам

---

## [2026-02-01] - Spambot (NewsBot)

### ✅ Добавлено

- **`blocks/spambot/newsbot.py`** - RSS бот для Telegram
- **`scripts/run_newsbot.py`**, **`blocks/spambot/README.md`**

### 📝 Изменено

- **`requirements.txt`**, **`.env.example`** - Зависимости и переменные для Spambot
- **`BLOCKS_REGISTRY.md`** - Блок D0 (spambot_newsbot) `ready`

---

## [2026-02-01] - Project Rules

### ✅ Добавлено

- **`PROJECT_RULES.md`** - Правила проекта
- **`scripts/run_newsbot.bat`** - BAT для NewsBot

### 📝 Изменено

- **`README.md`**, **`blocks/spambot/README.md`**, **`CHEATSHEET.md`**

---

## [2026-02-01] - Keys and Tokens Management

### ✅ Добавлено

- **`KEYS_AND_TOKENS.md`** - Документация ключей и токенов
- Обновлён **`.env.example`**

### 📝 Изменено

- **`PROJECT_RULES.md`**, **`README.md`**

---

## [2026-02-01] - Spambot Launch Scripts

### ✅ Добавлено

- **`scripts/run_spambot.bat`**, **`START_SPAMBOT.bat`**

### 📝 Изменено

- **`blocks/spambot/README.md`**, **`CHEATSHEET.md`**

---

## Формат записей

```markdown
## [vX.Y.Z] - YYYY-MM-DD - Название релиза

### ✅ Добавлено
### 📝 Изменено
### 🐛 Исправлено
### ❌ Удалено
### 🔒 Безопасность
```

Перед релизом обновить `docs/config/VERSION`. Подробнее: [CHANGELOG_WORKFLOW.md](CHANGELOG_WORKFLOW.md)

---

## Подробные описания патчей

Ниже — пофайловые описания выбранных патчей. Новые записи добавляются в этот раздел и в оглавление выше.

---

## flowcabinet-visualizer

**Дата:** 2026-02-21  
**Задача:** Веб-сервис для flowcabinet.ru: клиент загружает одно фото помещения (без размеров комнаты), выбирает размер кабинета (3/15/20/30 м²) и отделку (Standard/Advanced/Elite). Сервис проверяет пригодность фото по композиции; при неудаче — ошибка с конкретными рекомендациями. При успехе — генерация 3 вариантов визуализации «комната + кабинет»; после успешной генерации — кнопка «Скачать» (выбранный или каждый вариант).

### Добавлено

- **Блок `blocks/flowcabinet_visualizer/`**
  - `__init__.py`, `__main__.py` — точка входа, запуск uvicorn (порт 8777 по умолчанию).
  - `config.py` — размеры кабинетов (3, 15, 20, 30 м²), отделки, лимиты загрузки (15 МБ, 256–4096 px).
  - `validation.py` — проверка фото до генерации: разрешение, яркость, дисперсия (не плоская стена/размытие). Возврат `(ok, error, suggestions)` с текстами на русском.
  - `estimate.py` — оценка помещения по композиции, 3 гипотезы размещения кабинета (CabinetPlacement) для будущего inpainting/композитинга.
  - `pipeline.py` — генерация 3 вариантов: вызовы GRS AI (референсное фото + промпт по размеру/отделке) или fallback (исходное фото как результат). Сохранение в `generated/<session_id>/1.png`, `2.png`, `3.png`.
  - `api.py` — FastAPI: `POST /api/visualize` (multipart: photo, cabinet_size_sqm, finishing), сначала валидация, при ошибке — `success: false`, `error`, `suggestions`; при успехе — массив из 3 URL. `GET /api/config`, `GET /generated/<session_id>/<filename>`.
  - `static/index.html` — загрузка одного фото, форма (размер кабинета, отделка), при ошибке — блок с рекомендациями и «Загрузить другое фото»; при успехе — 3 варианта, выбор, кнопки «Скачать» (общая и у каждого варианта).
  - `static/app.js` — отправка формы, отображение ошибки/результатов, скачивание.
  - `static/style.css` — базовая стилизация.
  - `generated/.gitkeep`, `README.md` — описание запуска и API.
- **Документация**
  - `docs/architecture/FLOWCABINET_VISUALIZER.md` — описание сервиса, поток данных, API.
  - `docs/guides/DEPLOY_FLOWCABINET_VISUALIZER.md` — локальный запуск, systemd, Nginx, поддомен, интеграция с flowcabinet.ru (Tilda).

### Изменено

- `docs/config/.env.example` — секция «Визуализатор кабинетов FlowCabinet»: `FLOWCABINET_VIZ_HOST`, `FLOWCABINET_VIZ_PORT`.
- `docs/architecture/BLOCKS_REGISTRY.md` — блок E7 flowcabinet_visualizer, статус `ready`.
- `docs/rules/KEYS_AND_TOKENS.md` — подраздел 9b2 «Визуализатор кабинетов FlowCabinet» (использование GRS_AI_API_KEY/URL, опционально FLOWCABINET_VIZ_*).

---

## flowcabinet-visualizer-admin

**Дата:** 2026-02-21  
**Задача:** Отдельная веб-панель управления в рамках flowcabinet_visualizer: загрузка референсных изображений кабинета для каждой пары (размер × отделка), редактирование промптов генерации; защита паролем из `.env`. Пароль задаётся в переменной `FLOWCABINET_VIZ_ADMIN_PASSWORD` (локально в `.env` — реальное значение не коммитится).

### Добавлено

- **Хранилище и конфиг**
  - `config.py` — `REFERENCES_DIR`, `PROMPTS_JSON`.
  - `admin_storage.py` — чтение/запись промптов (`get_prompts`, `save_prompts`, `get_prompt_for`), референсы (`get_reference_path`, `get_reference_bytes`, `list_references`, `save_reference`), проверка имени файла `safe_reference_filename`. Папка `references/` с `.gitkeep`.
- **Защита админки**
  - `admin_auth.py` — `get_admin_password()`, `make_admin_token()` / `verify_admin_token()` (HMAC), `is_admin_available()`. При отсутствии `FLOWCABINET_VIZ_ADMIN_PASSWORD` маршруты `/admin` отдают 404.
- **API админки**
  - `admin_routes.py` — роутер `/admin`: `POST /admin/api/login`, `POST /admin/api/logout`, `GET /admin/api/references`, `POST /admin/api/references`, `GET /admin/references/{filename}`, `GET /admin/api/prompts`, `PUT /admin/api/prompts`, `GET /admin` (страница). Подключение роутера в `api.py`.
- **Фронтенд админки**
  - `static/admin.html` — форма входа по паролю, сетка комбинаций (размер × отделка): превью референса, загрузка файла, textarea промпта, кнопка «Сохранить все промпты», «Выйти».
  - `static/admin.js` — проверка авторизации, логин/логаут, загрузка референсов, сохранение промптов, отрисовка сетки (`credentials: 'include'`).
- **Пайплайн**
  - `pipeline.py` — `_get_effective_prompt()` (промпт из админки или дефолт); при наличии референса в `REFERENCES_DIR` передача в GRS `image_urls=[room, cabinet_ref]` и дополнение промпта про вставку кабинета из второго изображения.

### Изменено

- `docs/config/.env.example` — переменная `FLOWCABINET_VIZ_ADMIN_PASSWORD` в секции визуализатора.
- `docs/architecture/FLOWCABINET_VISUALIZER.md` — раздел «Админ-панель» (URL, назначение, хранилище).
- `docs/guides/DEPLOY_FLOWCABINET_VISUALIZER.md` — упоминание пароля админки и шаг в деплое.
- `docs/rules/KEYS_AND_TOKENS.md` — в 9b2 добавлен `FLOWCABINET_VIZ_ADMIN_PASSWORD`.
- `blocks/flowcabinet_visualizer/README.md` — раздел «Админ-панель».

**Примечание:** Реальный пароль задаётся только в `.env` (не в репозитории). В патче не хранится.

---

## flowcabinet-visualizer-admin-ux

**Дата:** 2026-02-21  
**Задача:** Улучшение UX админки визуализатора: один шаблон промпта с подстановками, перевод RU→EN через Google Translate (без API-ключа), загрузка референсов перетаскиванием, предзаполненный русский промпт, корректная авторизация (cookie только для `/admin`).

### Изменено

#### 1. Один шаблон промпта с подстановками

- **`admin_storage.py`** — добавлены `get_prompt_template()`, `get_prompt_template_ru()`, `save_prompt_template(template, template_ru)`. В `admin_prompts.json` хранятся `prompt_template` (англ., для генерации) и опционально `prompt_template_ru` (рус., для редактирования). Подстановки при генерации: `{size}`, `{finishing}`, `{size_width}`, `{size_depth}`, `{finishing_description}`.
- **`pipeline.py`** — `_substitute_prompt_template()` подставляет эти поля; `_get_effective_prompt()` берёт шаблон из админки или дефолт из кода.
- **`admin_routes.py`** — `GET/PUT /admin/api/prompts` работают с одним объектом `{ prompt_template, prompt_template_ru }`. Дефолтные шаблоны (рус. и англ.) возвращаются при пустом сохранённом значении.

#### 2. Два поля промпта: русский → кнопка «Перевести» → английский

- **`admin_routes.py`** — дефолтный русский текст в `DEFAULT_PROMPT_RU`; эндпоинт `POST /admin/api/translate-prompt` (body `{ text_ru }`, ответ `{ text_en }`). Перевод через библиотеку **deep-translator** (Google Translate без API-ключа). Плейсхолдеры перед переводом подменяются на токены, после — восстанавливаются. Обработка ошибок (в т.ч. «not found» от Google) с понятным сообщением пользователю.
- **`admin.html`** — первое поле «Промпт (русский)», кнопка «Перевести», второе поле «Промпт (английский) — для генерации»; подсказка про подстановки. Русский шаблон предзаполнен в HTML, при пустом ответе API поле не затирается.
- **`admin.js`** — загрузка/сохранение обоих шаблонов; по «Перевести» запрос на `/admin/api/translate-prompt`, результат вставляется во второе поле; при ошибке показывается `data.detail` от сервера.
- **`requirements.txt`** (flowcabinet_visualizer) — добавлена зависимость `deep-translator>=1.11.0`.

#### 3. Загрузка референсов перетаскиванием

- **`admin.js`** — зоны превью (`.ref-drop-zone`) принимают drag-and-drop изображений; при перетаскивании — подсветка (ring, bg); клик по зоне открывает выбор файла. Общая функция `uploadFile()` для загрузки по выбранному файлу и по drop.
- **`admin.html`** — подпись про перетаскивание или выбор файла.

#### 4. Маршруты и авторизация

- **`api.py`** — явные маршруты `GET /admin` и `GET /admin/` для страницы админки (чтобы не было 404 в части окружений). Роутер админки подключается без дублирования переводного эндпоинта в корне.
- **`admin_routes.py`** — cookie авторизации с **path="/admin"**: отправляется только на запросы к `/admin` и `/admin/*`, чтобы не авторизовывать остальные пути. Все вызовы админки (референсы, промпты, перевод) идут на `/admin/api/...`, запрос перевода — `api("/api/translate-prompt")` → `/admin/api/translate-prompt`, тогда cookie уходит с запросом и не возникает «пропуск входа и 401 при действии».

#### 5. Документация

- **`DEPLOY_FLOWCABINET_VISUALIZER.md`** — уточнено: админка по `http://127.0.0.1:8777/admin`, не подставлять буквально «host» в URL.

### Итог

- Один шаблон промпта (англ.) с подстановками; при генерации подставляются размер и отделка, выбранные клиентом.
- Редактирование на русском, кнопка «Перевести» → английский во второе поле (Google Translate, без ключа).
- Референсы можно загружать перетаскиванием в зону превью.
- Авторизация: вход по паролю, cookie только для `/admin`; все действия админки выполняются с той же сессией.

---

## cabinet-scale-viewer

**Дата:** 2026-02-21  
**Блок:** `blocks/cabinet_scale_viewer`  
**Задача:** Наложение 3D-модели кабинета на фото помещения с учётом плоскости пола и перспективы; исправление чёрного экрана, светлый UI, drag-drop загрузка, привязка модели к полу, масштаб независимый от положения отрезка.

### Добавлено

- **Модель по умолчанию** — загрузка `cabine.glb` из `public/` (файл из корня проекта копируется в `blocks/cabinet_scale_viewer/public/`).
- **Наложение 3D на фото** — после загрузки фото появляется блок «Наложение 3D»: фото как фон, поверх него Canvas с прозрачным фоном и 3D-моделью; масштаб и позиция/поворот общие с настройками ниже.
- **Четыре красные точки (пол)** — пользователь расставляет их по углам пола в кадре; используются для плоскости пола и для расчёта перспективного масштаба.
- **Перспективный масштаб** — гомография по 4 точкам пола; отрезок масштаба (2 синие точки) переводится в плоскость пола, длина в «единицах пола» не зависит от положения отрезка на фото. Масштаб отображается как «м/ед. пола (с учётом перспективы)» при успешной гомографии.
- **Утилиты** — `utils/homography.ts` (гомография 3×3 по 4 точкам, применение, обращение), `utils/perspectiveScale.ts` (вычисление масштаба по полу и отрезку).
- **Привязка модели к полу** — в режиме наложения высота модели по Y считается автоматически по нижней точке bbox с учётом масштаба и поворота; поворот только вокруг вертикали (Y°), чтобы модель не «отлипала» от пола.
- **Error Boundary** — при ошибке загрузки glTF показывается заглушка (куб) вместо чёрного экрана; глобальный AppErrorBoundary для страницы ошибки.

### Изменено

- **Дизайн** — светлая тема (Inter, карточки, акценты #3b82f6), переменные в `index.css`.
- **Блок загрузки** — зона перетаскивания (drag-and-drop) с подсветкой при перетаскивании; кнопка «Выбрать файл» с иконкой; пояснение: красные точки — углы пола, синие — отрезок известной длины **на полу**.
- **Сцена 3D** — отдельная секция «Сцена 3D (glTF)» удалена; остаётся только блок «Наложение 3D» с управлением X, Z и поворот Y° (Y позиции — «авто»).
- **OrbitControls в наложении** — отключён зум (`enableZoom={false}`), чтобы масштаб модели не менялся при прокрутке мыши.
- **ImageScaleState** — добавлено опциональное поле `perspectiveScale` (результат `computePerspectiveScale`); при валидной гомографии масштаб считается по плоскости пола.
- **README** блока — описание использования `cabine.glb` и копирование из корня в `public/`.

### Итог

- Пользователь загружает фото, ставит 4 красные точки по углам пола и 2 синие на отрезок известной длины (на полу), вводит длину в метрах.
- Масштаб не зависит от того, где на фото указан отрезок (учёт перспективы через гомографию пола).
- В блоке «Наложение 3D» модель стоит на плоскости пола (y=0), двигается по X/Z и крутится только по Y°; зум отключён.

---

## zen-autopost-scheduler

**Дата:** 2026-02-19  
**Задача:** Планировщик автопостинга Дзен (5 слотов/день), деплой на сервер, дашборд (источник, последний/следующий запуск, список сервисов с Запустить/Остановить). Дополнительно: блок «Сервисы на сервере» — одна строка на сервис (вертикальный список).

---

### 1. Планировщик (blocks/autopost_zen)

#### 1.1. `blocks/autopost_zen/scheduler.py` — **новый файл**, затем **изменён**

- Цикл планировщика: ожидание до слота, один запуск (генерация + публикация), запись состояния. Окна: 10:00–10:30, 11:30–12:00, 13:00–13:30, 14:00–14:30, 15:20–16:40. Функции: `_random_time_in_window`, `_next_run_times`, `_sleep_until`, `_get_next_slot`, `_read_schedule_state` / `_write_schedule_state`, `_run_one_slot`, `run_scheduler_loop`. State в `storage/zen_schedule_state.json` (last_run_at, next_run_at).
- **Правка:** после `_run_one_slot()` и записи `last_run_at` вызываются `_get_next_slot()` и `_write_schedule_state(next_run_at=...)`, чтобы в дашборде «След.» показывался следующий слот, а не уже прошедшее время.

#### 1.2. `blocks/autopost_zen/main.py` — **изменён**

- Аргумент `--schedule` / `-s`, при нём вызов `run_scheduler_loop()`.

#### 1.3. `blocks/autopost_zen/config.py`

- Используется для PROJECT_ROOT (путь к state-файлу).

#### 1.4. `blocks/autopost_zen/requirements.txt` — **изменён**

- Добавлены зависимости для Google Sheets (article_generator.fetch_topic): `gspread>=6.0.0`, `google-auth>=2.25.0`. Без них на сервере при запуске по расписанию возникал `ModuleNotFoundError: No module named 'gspread'`.

---

### 2. API и дашборд (blocks/analytics)

#### 2.1. `blocks/analytics/api.py` — **изменён**

- SERVER_SERVICES: добавлен zen-schedule. Константы _PROJECT_ROOT, _ZEN_SCHEDULE_STATE_FILE. Функция _get_zen_schedule_state(). В api_server_services() для zen-schedule добавляются last_run_at, next_run_at. ALLOWED_SERVICE_UNITS. POST /api/server-services/{unit}/start и .../stop (Linux, sudo systemctl).

#### 2.2. `blocks/analytics/static/app.js` — **изменён**

- SOURCE_LABELS: schedule → «Автопостинг Дзен». INITIAL_SERVICES_VISIBLE = 3. Рендер сервисов: одна строка на сервис (label, description, статус, последний/следующий запуск, кнопки Запустить/Остановить, Открыть сайт). Обработчики .service-start, .service-stop.

#### 2.3. `blocks/analytics/static/index.html` — **изменён**

- Блок «Сервисы на сервере»: контейнер списка (space-y-2). Параметр версии CSS: `style.css?v=3` (чтобы браузер не кэшировал старый стиль).

#### 2.4. `blocks/analytics/static/style.css` — **изменён**

- **Сервисы: одна строка — один сервис.** Убрана сетка (grid 3 колонки) у `#services-list` и `#services-items`. Заданы `display: flex; flex-direction: column; gap: 0.5rem;` — вертикальный список, каждая плашка в отдельной строке.

#### 2.5. `blocks/analytics/watchdog_services.py` — **изменён**

- В список мониторинга добавлен zen-schedule.

---

### 3. Деплой и сервер

- **webhook_server.py:** zen-schedule в DEPLOY_MAIN_SERVICES, pip install blocks/autopost_zen/requirements.txt.
- **zen-schedule.service.example**, **update.sh**, **DEPLOY_WEBHOOK.md** — настройка zen-schedule, sudoers для кнопок.
- Скрипты SSH: run_install_zen_schedule_ssh.ps1, get_zen_logs.ps1, get_zen_dashboard_errors.ps1 (выгрузка ошибок из БД аналитики дашборда), remote_cmd.ps1.

---

### 4. Прочее

- **.gitignore** — добавлен storage/zen_schedule_state.json.

---

### 5. Сводная таблица файлов (zen-autopost-scheduler)

| Файл | Действие |
|------|----------|
| blocks/autopost_zen/scheduler.py | Создан, затем изменён (next_run_at после слота) |
| blocks/autopost_zen/requirements.txt | Изменён (gspread, google-auth) |
| blocks/autopost_zen/main.py | Изменён |
| blocks/analytics/api.py | Изменён |
| blocks/analytics/static/app.js | Изменён |
| blocks/analytics/static/index.html | Изменён (блок сервисов, style.css?v=3) |
| blocks/analytics/static/style.css | Изменён (сервисы: flex column, 1 строка = 1 сервис) |
| blocks/analytics/watchdog_services.py | Изменён |
| webhook_server.py | Изменён |
| docs/scripts/deploy_beget/zen-schedule.service.example | Создан |
| docs/scripts/deploy_beget/update.sh | Изменён |
| docs/scripts/deploy_beget/run_install_zen_schedule_ssh.ps1 | Создан/изменён |
| docs/scripts/deploy_beget/get_zen_logs.ps1 | Создан |
| docs/scripts/deploy_beget/remote_cmd.ps1 | Создан |
| docs/guides/DEPLOY_WEBHOOK.md | Изменён |
| .gitignore | Изменён |

---

---

## orchestrator-kz-deploy

**Дата:** 2026-02-20  
**Задача:** Переименование планировщика Дзен в «Оркестратор контент завода» (orchestrator-kz), обязательный пробный запуск цепочки при старте сервиса (вне расписания), исправление отображения в дашборде (название и статус), деплой и перезапуск на сервере.

---

### 1. Оркестратор (blocks/autopost_zen)

#### 1.1. `blocks/autopost_zen/scheduler.py` — **изменён**

- **run_scheduler_loop():** в docstring явно указано: при каждом старте сервиса ОБЯЗАТЕЛЬНО выполняется один полный прогон цепочки (генерация → Telegram → Дзен), чтобы убедиться, что всё работает; расписание — отдельно, после прогона.
- Логи: «Оркестратор: обязательный пробный запуск цепочки при старте (вне расписания)…»; после успешного прогона — «Оркестратор: пробный запуск завершён успешно. Переход к работе по расписанию.»
- Пробный запуск выполняется до цикла `while True` по расписанию; при исключении — логирование и продолжение к расписанию.

---

### 2. Дашборд и API (blocks/analytics)

- **api.py** — в коде уже orchestrator-kz в SERVER_SERVICES, _get_orchestrator_kz_state(), _ORCHESTRATOR_KZ_STATE_FILE (storage/orchestrator_kz_state.json). На сервере при отставании кода от репозитория обновление путём загрузки актуального api.py (pscp) и перезапуска analytics-dashboard.
- **watchdog_services.py** — orchestrator-kz в списке мониторинга; на сервере при необходимости обновлён аналогично.

---

### 3. Деплой

- **docs/scripts/deploy_beget/orchestrator-kz.service.deploy** — сгенерированный unit (User=root, WorkingDirectory/пути /root/contentzavod) для загрузки на сервер по pscp при отсутствии orchestrator-kz.service.example в репозитории.
- На сервере: установка unit в /etc/systemd/system/orchestrator-kz.service, daemon-reload, enable, start; при обновлении scheduler.py — загрузка файла и systemctl restart orchestrator-kz.
- DEPLOY_WEBHOOK.md: переход с zen-schedule (stop zen-schedule, установка orchestrator-kz, замена в sudoers); при смене имени сервиса — перезапуск analytics-dashboard для отображения нового имени и статуса.

---

### 4. Сводная таблица файлов (orchestrator-kz-deploy)

| Файл | Действие |
|------|----------|
| blocks/autopost_zen/scheduler.py | Изменён (обязательный пробный запуск: docstring, логи) |
| blocks/analytics/api.py | На сервере обновлён (orchestrator-kz, _get_orchestrator_kz_state) |
| blocks/analytics/watchdog_services.py | На сервере обновлён (orchestrator-kz в списке) |
| docs/scripts/deploy_beget/orchestrator-kz.service.deploy | Создан (unit для деплоя по pscp) |

---

## orchestrator-stability-telegram-recovery

**Дата:** 2026-02-20  
**Задача:** Стабилизировать оркестратор после инцидентов: убрать лишние/параллельные генерации, исправить причину Telegram-падений на сервере, сохранять частично неуспешные публикации для повторного запуска, очистить зависшие `running` в аналитике и провести контролируемый деплой с максимум одним новым запуском.

---

### 1. Оркестратор и пайплайн публикации

#### 1.1. `blocks/autopost_zen/scheduler.py` — **изменён**

- Добавлен lock-файл `storage/orchestrator_kz.lock` (Linux, `fcntl`) для single-instance работы оркестратора.
- Добавлен warning при старте, если не заданы Telegram-переменные (`TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHANNEL_ID` или проектный конфиг).
- Интервал подавления повторного mandatory-прогона при рестартах увеличен: `MIN_INTERVAL_BETWEEN_STARTUP_RUNS_SEC = 7200` (2 часа), чтобы не плодить генерации при частых деплоях.
- Логика обработки каналов скорректирована:
  - тема удаляется из таблицы, если публикация успешна хотя бы в одном канале;
  - при частичной неуспешности запись сохраняется в `storage/failed_publications.jsonl` (канал(ы) ошибки, пути к статье, title, run_id).

#### 1.2. `blocks/autopost_zen/article_generator.py` — **изменён**

- Добавлена защита от неверной позиции баннера: если `<!-- BANNER -->` оказался в начале/слишком рано, баннер вставляется в безопасную позицию внутри контента, а не сразу после обложки.

#### 1.3. `blocks/lifehacks_to_spambot/run.py` — **изменён**

- `post_article_to_telegram_sync()` переведён на возврат `(ok, err_msg)` вместо bool, чтобы пробрасывать точную причину падения Telegram-публикации.

#### 1.4. `blocks/autopost_zen/main.py` — **изменён**

- Адаптирован вызов Telegram-публикации под формат `(ok, err_msg)` с подробной ошибкой в RuntimeError.

#### 1.5. `blocks/autopost_zen/scheduler.py` — **дополнительные фиксы стабильности (2026-02-20)**

- Добавлен жёсткий таймаут на шаг Дзен-публикации: `ZEN_PUBLISH_TIMEOUT_SEC` (по умолчанию 900 сек), чтобы шаг `publish_zen` не зависал бесконечно в `running`.
- Реализован режим **takeover** lock-файла:
  - при старте новый процесс читает PID из `storage/orchestrator_kz.lock`;
  - если это старый `blocks.autopost_zen --schedule`, новый процесс завершает его (`SIGTERM`, затем `SIGKILL` при необходимости);
  - после этого новый процесс забирает lock и продолжает работу.
- Добавлена авто-очистка `stale` запусков при старте (`_close_stale_schedule_runs()`):
  - все старые `runs` со `status='running'` и `source='schedule'` закрываются как `failed`;
  - связанные `steps` (`running/pending`) тоже закрываются как `failed` с `error_message`.
- Цель фикса: в дашборде не должно оставаться «второго синего» запуска на генерации после рестартов/деплоя.

**Поведение «висящих» запусков (82, 85):** `_close_stale_schedule_runs()` вызывается **не при старте процесса**, а **только перед запуском нового слота**. Так старый run помечается failed только когда реально начинается новый (86); если оркестратор перезапустился и новый слот не запускался — старый run не трогаем. **Почему предыдущий процесс не вызвал finish_run():** OOM kill (ядро убило по памяти) или takeover (новый процесс убил старый при занятии lock). В логах при закрытии: `Закрыты stale schedule-запуски как failed: [82, 85]`.

---

### 2. Аналитика и восстановление статистики

#### 2.1. `docs/scripts/close_stuck_analytics_runs.py` — **добавлен**

- Скрипт операционного cleanup для дашборда:
  - закрывает указанные или все `runs.status='running'` как `failed`;
  - закрывает связанные `steps` (`running/pending`) как `failed` с `error_message`;
  - поддержка `--all`, выбор конкретных run_id, `--dry-run`.

#### 2.2. `docs/guides/ANALYTICS_DASHBOARD_DATA.md` — **добавлен**

- Зафиксированы источники данных дашборда (`storage/analytics*.db`, таблицы `runs/steps`, API `/api/runs`).
- Добавлен регламент закрытия stuck-запусков для восстановления корректной статистики.

#### 2.3. `docs/guides/FAILED_PUBLICATIONS.md` — **изменён**

- Дополнен связкой с аналитикой: куда смотреть и чем закрывать stuck-running, чтобы метрики не искажались.

---

### 3. Деплой и конфигурация сервера

#### 3.1. `docs/scripts/deploy_beget/orchestrator-kz.service.example` — **добавлен/обновлён**

- Явно указано обязательное наличие Telegram-переменных на сервере для оркестратора.

#### 3.2. `docs/guides/DEPLOY_WEBHOOK.md` — **изменён**

- Раздел оркестратора обновлён: обязателен серверный `.env` с `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHANNEL_ID`; уточнён startup-поведение (mandatory-прогон только если не было запуска за последние 2 часа).

#### 3.3. `docs/rules/KEYS_AND_TOKENS.md` — **изменён**

- Добавлено явное правило: локальный `.env` и серверный `.env` должны содержать согласованные Telegram-ключи для оркестратора; иначе Telegram-канал будет падать в каждом слоте.

#### 3.4. `docs/scripts/deploy_beget/orchestrator-kz.service.example` — **изменён**

- `Restart=on-failure` вместо `Restart=always`, чтобы избежать бесконечных перезапусков при штатном завершении процесса (например, при lock-конфликте/контролируемом выходе).

---

### 4. Операции на сервере (production handling)

- Остановлены лишние процессы оркестратора.
- Выполнено массовое закрытие зависших `running` запусков в аналитике как `failed`.
- Синхронизированы Telegram-переменные на сервере (`.env`).
- Проведён controlled restart с итогом: не более одного нового `running` запуска после финального старта.
- Дополнительно: зачищены stale run_id (`53, 54, 55`) и удалены orphan-процессы, после чего оставлен один актуальный `running` run.

---

---

## cabinet-scale-viewer-calibration

**Дата:** 2026-02-21  
**Блок:** `blocks/cabinet_scale_viewer`  
**Задача:** Исправить три бага: 1) зелёные точки не влияли на модель (5-точечная калибровка отклонялась, камера оставалась дефолтной); 2) модель была слишком большой и наклонённой вперёд; 3) перемещение правой синей точки двигало модель вместо масштабирования.

**Корневая причина:** Порог принятия калибровки (15 px для 5pt, 12 px для 4pt) был слишком строгим. Если калибровка давала ошибку 20 px, она полностью отвергалась, камера оставалась на [4, 2, 4] с FOV 50° — модель оказывалась в неправильных координатах, с неправильным масштабом и перспективой, и не реагировала ни на зелёные, ни на синие точки. Кроме того, при неудаче 5pt не пробовалась 4pt.

### Исправлено

#### 1. Fallback 5pt → 4pt (`Scene3D.tsx`)

- Ранее: если `use5Point === true` и 5-точечная калибровка возвращала `valid: false`, камера не применялась вообще (ни 5pt, ни 4pt).
- Теперь: сначала пробуется 5pt; при неудаче (ошибка > 80 px) автоматически пробуется 4pt. Применяется лучший из успешных результатов.

#### 2. Порог принятия калибровки (`Scene3D.tsx`)

- Ранее: порог 15 px для 5pt, 12 px для 4pt. Большинство реальных фото давали ошибку 20–50 px — калибровка отклонялась.
- Теперь: `CALIB_ACCEPT_THRESHOLD = 80 px`. Камера применяется даже при «слабой» калибровке. Качество (`valid: true`) по-прежнему требует < 15 px и отображается в UI.

#### 3. `activeMode` вместо `use5Point` (`Scene3D.tsx`)

- Ранее: `floorAnchor`, `modelSegmentLength` и мировая система координат определялись по `use5Point` — **намерению** использовать 5pt, а не по тому, какая калибровка реально сработала.
- Теперь: введён `activeMode: "5pt" | "4pt" | "none"`, определяемый фактическим результатом калибровки. `floorAnchor` использует метровый мир для `5pt` и единичный квадрат для `4pt`; `modelSegmentLength` соответствует активному режиму.

#### 4. Проба инвертированной высоты (`homography.ts`)

- В `calibrateCameraFrom5Points` добавлен второй проход с отрицательной высотой зелёной точки. Если FOV-область с отрицательной высотой даёт значительно лучшую ошибку (< 70 % от положительной), вокруг этого FOV выполняется повторный поиск с положительной высотой. Это помогает при декомпозициях гомографии с инвертированной осью Y.

#### 5. Расширен диапазон FOV (`homography.ts`)

- Ранее: поиск 15°–130° с уточнением ±3° и ±0.5°.
- Теперь: поиск 10°–150°; уточнение ±3° и ±0.5° вынесено в `refineAround()`.

#### 6. Режим калибровки в UI (`App.tsx`)

- Статус калибровки теперь показывает режим: `[5pt]`, `[4pt]` или `[none]` и текстовую оценку (`уверенная` / `слабая` / `нет`).

### Изменённые файлы

| Файл | Что изменено |
|------|--------------|
| `src/components/Scene3D.tsx` | Вынесен `applyCalibToCamera()`; `CalibResult { mode, valid, reprojectionErrorPx }`; fallback 5pt→4pt; `activeMode` для floorAnchor и modelSegmentLength; `CALIB_ACCEPT_THRESHOLD = 80`; экспорт `CameraCalibrationResult` из homography |
| `src/utils/homography.ts` | `calibrateCameraFrom5Points`: два прохода (положительная + отрицательная высота); `refineAround()`; расширен FOV 10°–150° |
| `src/App.tsx` | Тип `calibrationStatus` расширен на `mode: string`; отображение `[5pt]/[4pt]/[none]` |

### Итог

- Зелёные точки теперь влияют на перспективу (через 5pt калибровку с увеличенным порогом).
- При неудаче 5pt автоматически используется 4pt.
- Модель не «взлетает»: камера всегда применяется при ошибке < 80 px.
- Перемещение синей точки преимущественно изменяет масштаб (при корректной калибровке смещение модели минимально).

---

## run-source-in-logs

**Дата:** 2026-02-22  
**Задача:** Упростить получение информации «какой процесс запустил публикацию» (run_id в дашборде): не лезть в БД и не запускать SSH-скрипты — смотреть в логах. Дополнительно: скрипты для запроса источника запуска по id (локально и по SSH).

### Добавлено

- **Логи при старте и завершении запуска** (`blocks/analytics/tracker.py`):
  - При `start_run()` пишется строка: `run_id=N started | source=schedule | Оркестратор (расписание / автозапуск при старте)` (или `google_sheets` / `file` с человекочитаемой меткой).
  - При `finish_run()` пишется: `run_id=N finished | status=completed` (или `failed`).
  - Константа `SOURCE_LABELS` для единообразных подписей в логах и дашборде.
- **Скрипты для просмотра источника по run_id:**
  - `docs/scripts/get_run_source.py` — локально или на сервере: `python get_run_source.py 75 [flow|fulfilment]` выводит id, started_at, status, source и расшифровку (Оркестратор / Таблица / Файл).
  - `docs/scripts/deploy_beget/get_run_source_ssh.ps1` — с Windows по plink (PuTTY): читает .env, подключается к серверу и запрашивает в БД run по id через Python в venv; параметр `-RunId 75`.
- **Документация:** в `blocks/analytics/README.md` добавлен абзац «Как быстро узнать, какой процесс запустил публикацию»: поиск в логах по `run_id=` или `started | source=`, пути к логу локально (`blocks/autopost_zen/autopost_debug.log`) и на сервере (`journalctl -u orchestrator-kz | grep run_id=`).

### Изменено

- **`blocks/analytics/tracker.py`** — импорт `logging`, логгер `logger`, после `insert_run` вызов `logger.info("run_id=... started | source=... | ...")`, в `finish_run` — `logger.info("run_id=... finished | status=...")`.

### Итог

- Чтобы узнать, кто запустил публикацию (например run 75), достаточно открыть лог и найти строку с `run_id=75` или `started | source=`.
- На сервере: `journalctl -u orchestrator-kz | grep run_id=` или `grep run_id= blocks/autopost_zen/autopost_debug.log`.
- При необходимости точного запроса по БД: локально — `python docs/scripts/get_run_source.py 75`, с Windows на сервер — `.\docs\scripts\deploy_beget\get_run_source_ssh.ps1 -RunId 75`.

---

## orchestrator-pause-resume

**Дата:** 2026-02-22  
**Задача:** Сделать так, чтобы оркестратор можно было **один раз остановить** и он не перезапускался и не запускал генерацию статей, пока явно не возобновить. Реализация через файл-флаг приостановки; инструкция по новому запуску.

### Поведение

- **Файл приостановки:** `storage/orchestrator_kz_paused`. Если этот файл существует, оркестратор при **любом** старте (вручную, systemd, после рестарта) сразу выходит с кодом 0 — **ни пробного запуска, ни генерации, ни работы по расписанию**.
- **Один раз остановить:** создать файл (локально или на сервере) и перезапустить сервис — дальше при каждом рестарте процесс будет только стартовать и сразу завершаться.
- **Новый запуск (возобновление):** удалить файл и перезапустить сервис — оркестратор снова выполняет пробный запуск (если прошло ≥2 ч) и работает по расписанию.

### Изменения в коде

#### 1. `blocks/autopost_zen/scheduler.py` — **изменён**

- Константа **`ORCHESTRATOR_PAUSED_FILE`** = `config.PROJECT_ROOT / "storage" / "orchestrator_kz_paused"`.
- В **начале** `run_scheduler_loop()` (до блокировки и любых действий): проверка `if ORCHESTRATOR_PAUSED_FILE.exists()` → лог «Оркестратор приостановлен (найден файл …). Чтобы возобновить: удалите файл и перезапустите сервис (или запустите с --resume-orchestrator).» и **`sys.exit(0)`**.
- Docstring `run_scheduler_loop()` дополнен: «Если существует файл storage/orchestrator_kz_paused — оркестратор сразу выходит (без генерации и расписания).»

#### 2. `blocks/autopost_zen/main.py` — **изменён**

- Новые аргументы CLI:
  - **`--pause-orchestrator`** — создаёт `ORCHESTRATOR_PAUSED_FILE` (директория `storage/` при необходимости), выводит сообщение и выходит с кодом 0.
  - **`--resume-orchestrator`** — удаляет `ORCHESTRATOR_PAUSED_FILE` (если есть), выводит сообщение и выходит с кодом 0.
- Обработка этих флагов выполняется **до** вызова `run_scheduler_loop()`, чтобы пауза/возобновление работали без запуска цикла расписания.

#### 3. `.gitignore` — **изменён**

- Добавлена строка **`storage/orchestrator_kz_paused`**, чтобы флаг приостановки не попадал в репозиторий.

#### 4. Скрипты деплоя (docs/scripts/deploy_beget/) — **добавлены**

- **`pause_orchestrator_on_server.ps1`** — с локальной машины по SSH: загружает код на сервер (`git pull`), выполняет на сервере `python -m blocks.autopost_zen --pause-orchestrator`, затем `sudo systemctl restart orchestrator-kz`. Требует в `.env`: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_PASSWORD` (или `DEPLOY_SSH_PASSWORD`); по желанию `SERVER_PROJECT_PATH` (по умолчанию `/root/contentzavod`). Использует plink (PuTTY).
- **`resume_orchestrator_on_server.ps1`** — по SSH выполняет на сервере `python -m blocks.autopost_zen --resume-orchestrator` и `sudo systemctl restart orchestrator-kz`. Те же переменные окружения.

#### 5. Документация — **добавлена**

- **`docs/guides/ORCHESTRATOR_PAUSE_RESUME.md`** — инструкция: приостановка (три варианта: скрипт с компа, вручную на сервере, только `systemctl stop`); **новый запуск оркестратора** (скрипт с компа, вручную на сервере); проверка по логам; локальный запуск без сервера.

### Сводная таблица файлов (orchestrator-pause-resume)

| Файл | Действие |
|------|----------|
| blocks/autopost_zen/scheduler.py | Изменён (ORCHESTRATOR_PAUSED_FILE, проверка в начале run_scheduler_loop, sys.exit(0)) |
| blocks/autopost_zen/main.py | Изменён (--pause-orchestrator, --resume-orchestrator) |
| .gitignore | Изменён (storage/orchestrator_kz_paused) |
| docs/scripts/deploy_beget/pause_orchestrator_on_server.ps1 | Создан |
| docs/scripts/deploy_beget/resume_orchestrator_on_server.ps1 | Создан |
| docs/guides/ORCHESTRATOR_PAUSE_RESUME.md | Создан (инструкция по приостановке и новому запуску) |

### Итог

- Один раз остановить: выполнить `pause_orchestrator_on_server.ps1` или на сервере `--pause-orchestrator` и перезапуск сервиса. Дальше оркестратор при любом старте сразу выходит, генерации нет.
- Новый запуск: выполнить `resume_orchestrator_on_server.ps1` или на сервере удалить файл/`--resume-orchestrator` и перезапустить сервис. Подробно: **docs/guides/ORCHESTRATOR_PAUSE_RESUME.md**.

---

## orchestrator-single-service-manual-run

**Дата:** 2026-02-22  
**Задача:** Убрать двойной контур запуска (`zen-schedule` + `orchestrator-kz`), оставить только один оркестратор, полностью отключить автоматический пробный запуск при старте процесса и вынести разовый прогон в отдельное ручное действие из дашборда.

### Почему понадобилось

- На сервере одновременно существовали два systemd-юнита с одинаковым `ExecStart` (`python -m blocks.autopost_zen --schedule`): legacy `zen-schedule` и новый `orchestrator-kz`.
- При webhook-deploy/рестартах запускалась цепочка чаще ожидаемого (каждый restart сервиса давал запуск), что выглядело как «сам включается».
- Требовалось разделить:
  - **плановые запуски** — только по расписанию;
  - **разовый запуск** — только по явной кнопке в дашборде.

### Изменено в коде

#### 1. `blocks/autopost_zen/scheduler.py`

- Удалён автоматический пробный запуск из `run_scheduler_loop()`.
- Новый режим работы процесса `--schedule`: **только ожидание слотов и запуск по расписанию**.
- Добавлена функция `run_one_off_now()` — выполняет один полный прогон цепочки вне расписания.
- `_run_one_slot()` принимает `run_source` (по умолчанию `schedule`), чтобы разовый запуск шёл как отдельный источник (`manual_once`) в аналитике.
- Поведение файла паузы `storage/orchestrator_kz_paused` сохранено: при наличии файла оркестратор при старте сразу выходит.

#### 2. `blocks/autopost_zen/main.py`

- Добавлен флаг CLI `--run-once` для ручного одиночного прогона цепочки.
- Обновлено описание `--schedule`: без пробного старта, только расписание.

#### 3. `blocks/analytics/api.py`

- Для карточки `orchestrator-kz` в сервисах описание обновлено на режим «только расписание».
- Добавлен endpoint:
  - `POST /api/server-services/orchestrator-kz/run-once`
  - запускает отдельный процесс `python -m blocks.autopost_zen --run-once` в фоне;
  - не зависит от текущего состояния systemd-сервиса `orchestrator-kz`;
  - не меняет план расписания (`next_run_at` / `last_run_at` в state-файле оркестратора).

#### 4. `blocks/analytics/static/app.js`

- В карточку сервиса `orchestrator-kz` добавлена кнопка **«Разовый прогон»**.
- Кнопка вызывает `POST /api/server-services/orchestrator-kz/run-once`.
- В UI добавлена расшифровка источника запуска `manual_once` как «Разовый прогон (дашборд)».

#### 5. `blocks/analytics/tracker.py`

- Добавлен источник `manual_once` в человекочитаемые метки source.
- В дашборде и логах разовый запуск отделяется от `schedule`.

### Операционные изменения на сервере

- Зафиксирована архитектура «один сервис оркестратора»:
  - `orchestrator-kz` — основной;
  - `zen-schedule` — остановлен, отключён, замаскирован (чтобы не мог случайно перезапуститься).
- Серверные deploy-пути переведены на `orchestrator-kz` вместо `zen-schedule`.
- Скрипты обслуживания (`pause_orchestrator_on_server.ps1`, `resume_orchestrator_on_server.ps1`, `run_install_zen_schedule_ssh.ps1`) усилены защитой от повторного включения legacy `zen-schedule`.

### Архитектурные документы

- Добавлен архитектурный документ: `docs/architecture/ORCHESTRATOR_KZ_ARCHITECTURE.md`.
- Добавлен эксплуатационный runbook: `docs/guides/ORCHESTRATOR_KZ_RUNBOOK.md`.

### Итог

- Автозапуски от restart процесса больше не происходят.
- Плановые публикации идут только по слотам расписания.
- Разовый прогон выполняется только по явному действию пользователя в дашборде (или CLI `--run-once`).
- Для production поддерживается единый источник плановых запусков: `orchestrator-kz`.

---

## script-board-project-picker

**Дата:** 2026-02-22  
**Блок:** `blocks/script_board`  
**Задача:** Добавить возможность выбирать и создавать проекты на доске скриптов; каждый проект хранит свои узлы, рёбра и описание скрипта независимо от других.

### Добавлено

- **Хранилище проектов** (`frontend/src/projectsStorage.ts`):
  - Ключи localStorage: `script_board_projects`, `script_board_current`.
  - Функции: `getCurrentProjectId`, `setCurrentProjectId`, `listProjects`, `loadProject`, `saveProject`, `createProject`, `getProjectName`. Структура проекта: `{ name, nodes, edges, scriptDescription }`.
- **Модалка выбора проекта** (`frontend/src/ProjectPickerModal.tsx`):
  - Список созданных проектов (клик по строке — выбор текущего).
  - Кнопка «Создать проект» переключает на форму с полем «Название проекта» и кнопкой «Создать».
  - Пропсы: `open`, `projects`, `onCreateProject(name)`, `onSelectProject(id)`, `onClose`.
- **Стили** (`frontend/src/App.css`): `.project-list`, `.project-list__item`, `.project-list__empty`, `.modal--projects .modal__body` для списка проектов в модалке.

### Изменено

- **App.tsx**:
  - Единый черновик заменён на проекты: `getInitialProjectState()` загружает текущий проект по `getCurrentProjectId()` или создаёт «Проект 1».
  - Состояние: `currentProjectId`, `projectPickerOpen`.
  - Сохранение через `saveProject(currentProjectId, getProjectName(currentProjectId), nodes, edges, scriptDescription)`.
  - Обработчики `handleSelectProject(id)` и `handleCreateProject(name)`; кнопка «Выбрать проект» в правой панели открывает модалку.
  - В разметку добавлен рендер `<ProjectPickerModal />` с нужными пропсами.

### Итог

- Кнопка «Выбрать проект» открывает окно со списком проектов и кнопкой «Создать проект». Каждый проект изолирован (свои карточки и описание скрипта). Данные хранятся в localStorage.

---

## script-board-deploy-grs

**Дата:** 2026-02-22  
**Блок:** `blocks/script_board`, деплой на script.flowcabinet.ru  
**Задача:** Обеспечить работу генерации через GRS AI на сервере: данные для API (ключ и URL) есть в проекте в корневом `.env` — при деплое передавать их на сервер, чтобы «Сгенерировать» и «Улучшить текст» работали на https://script.flowcabinet.ru.

### Изменено

- **`docs/scripts/deploy_beget/deploy_script_board.ps1`**:
  - В комментарии вверху указано, что скрипт читает из `.env` также `GRS_AI_API_KEY` и `GRS_AI_API_URL`.
  - Шаг 3: блок для дописывания в серверный `.env` расширен — кроме `SCRIPT_BOARD_HOST` и `SCRIPT_BOARD_PORT` в него добавлены `GRS_AI_API_KEY` и `GRS_AI_API_URL`, берущиеся из локального `.env` (если ключ задан). При отсутствии ключа локально выводится предупреждение.
  - Дописывание на сервер выполняется только если в серверном `.env` ещё нет `GRS_AI_API_KEY` (чтобы не перезаписывать уже настроенные ключи). Используется команда: `grep -q 'GRS_AI_API_KEY' .env || (cat .env.script_board_append >> .env)`.

### Итог

- При деплое Script Board ключи GRS AI из корневого `.env` проекта передаются на сервер (в серверный `.env`), если там ещё не задан `GRS_AI_API_KEY`. Генерация ответов и «Улучшить текст» на script.flowcabinet.ru работают через GRS AI без ручной настройки ключей на сервере.

---

*Новые патчи добавляются в раздел «Подробные описания патчей» и в оглавление в начале документа.*
