# ContentZavod

Система автоматизированного создания и распространения контента. Папка проекта должна называться **ContentZavod** (латиница) — см. docs/guides/GETTING_STARTED.md.

---

## Структура проекта

- **blocks/** — код всех блоков (AI, Spambot и др.)
- **docs/** — вся документация, конфигурация, скрипты, бекапы

Подробнее: **docs/guides/README.md**

---

## Быстрый старт

### Запуск Spambot (RSS → Telegram)

**Для проекта (рекомендуется):**
```
blocks\spambot\start.bat flowcabinet
```
(или другой project_id из `blocks/projects/data/`)

**Без указания проекта** (используется PROJECT_ID из .env или токены из .env):
```
blocks\spambot\start.bat
```

**Список проектов:** из корня проекта: `python -m blocks.spambot --list-projects`

### Первая настройка

1. Создайте `.env` в корне:
   ```
   copy docs\config\.env.example .env
   ```
2. В `.env` задайте `GRS_AI_API_KEY` (общий для всех проектов) и при необходимости `PROJECT_ID=flowcabinet`.
3. Добавьте проект: скопируйте `blocks/projects/data/project.example.yaml` в `blocks/projects/data/<id>.yaml` и заполните telegram и при необходимости spambot.
4. Установите зависимости:
   ```
   pip install -r docs\config\requirements.txt
   ```

**Мультипроектность:** один завод — несколько проектов; у каждого свои аккаунты, API ИИ общий. Подробнее: **docs/guides/MULTIPROJECT.md**

### Docker

Сборка и запуск блоков в контейнере: **docs/guides/DOCKER.md**. Кратко: `docker build -t contentzavod .` и `docker run --env-file .env contentzavod python -m blocks.spambot --project flowcabinet`.

---

## Документация

| Раздел | Путь |
|--------|------|
| Руководства (старт, справка) | docs/guides/ |
| Правила и ключи | docs/rules/ |
| Архитектура | docs/architecture/ |
| Конфигурация | docs/config/ |
| Скрипты | docs/scripts/scripts/ |

Главный README: **docs/guides/README.md**

---

## Блоки

- **blocks/ai_integrations/** — GRS AI клиент (общий для всех проектов)
- **blocks/spambot/** — NewsBot (RSS → Telegram)
- **blocks/post_flow/** — Post FLOW: посты из Google Таблицы (тема → GRS AI → канал FLOW)
- **blocks/projects/** — конфигурация по каждому проекту (мультипроектность)

---

Версия: 2.0
