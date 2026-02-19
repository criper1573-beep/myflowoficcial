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

## zen-autopost-scheduler

**Дата:** 2026-02-19  
**Задача:** Планировщик автопостинга Дзен (5 слотов/день), деплой на сервер, дашборд (источник, последний/следующий запуск, список сервисов с Запустить/Остановить). Дополнительно: блок «Сервисы на сервере» — одна строка на сервис (вертикальный список).

---

### 1. Планировщик (blocks/autopost_zen)

#### 1.1. `blocks/autopost_zen/scheduler.py` — **новый файл**

- Цикл планировщика: ожидание до слота, один запуск (генерация + публикация), запись состояния. Окна: 10:00–10:30, 11:30–12:00, 13:00–13:30, 14:00–14:30, 15:20–16:40. Функции: `_random_time_in_window`, `_next_run_times`, `_sleep_until`, `_get_next_slot`, `_read_schedule_state` / `_write_schedule_state`, `_run_one_slot`, `run_scheduler_loop`. State в `storage/zen_schedule_state.json` (last_run_at, next_run_at).

#### 1.2. `blocks/autopost_zen/main.py` — **изменён**

- Аргумент `--schedule` / `-s`, при нём вызов `run_scheduler_loop()`.

#### 1.3. `blocks/autopost_zen/config.py`

- Используется для PROJECT_ROOT (путь к state-файлу).

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
- Скрипты SSH: run_install_zen_schedule_ssh.ps1, get_zen_logs.ps1, remote_cmd.ps1.

---

### 4. Прочее

- **.gitignore** — добавлен storage/zen_schedule_state.json.

---

### 5. Сводная таблица файлов (zen-autopost-scheduler)

| Файл | Действие |
|------|----------|
| blocks/autopost_zen/scheduler.py | Создан |
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

*Новые патчи добавляются в раздел «Подробные описания патчей» и в оглавление в начале документа.*
