# АРХИВ ЗАДАЧИ: docker-001 — Реализовать Docker в проекте

## METADATA

| Поле | Значение |
|------|----------|
| Task ID | docker-001 |
| Название | Реализовать Docker в нашем проекте |
| Уровень сложности | Level 3 (Intermediate Feature) |
| Дата инициализации | 2025-02-18 |
| Дата архивации | 2025-02-18 |
| Статус | COMPLETE |

---

## SUMMARY

Добавлена полная поддержка Docker для проекта КонтентЗавод: один образ `contentzavod` для всех блоков (spambot, post_flow, mcp_server и др.), запуск через переопределение команды. Секреты не в образе: .env и конфиги проектов передаются при запуске (--env-file, volumes). Реализованы: .dockerignore, Dockerfile, docker-compose.yml (spambot, post_flow), docs/guides/DOCKER.md, обновлены README и правила проекта. Образ собирается и успешно запускается; для совместимости зависимостей введён requirements-docker.txt и deep-translator вместо googletrans в образе.

---

## REQUIREMENTS

- Собрать образ приложения и запускать блоки в контейнере.
- Не хранить секреты в образе (.env, конфиги проектов — при запуске).
- Документировать сборку и запуск в docs/guides/.
- Один образ, разный entry point через command.

---

## IMPLEMENTATION

### Созданные/изменённые артефакты

- **.dockerignore** (корень) — исключение .env, venv, storage, .git, memory-bank, .cursor, бекапы, логи.
- **Dockerfile** (корень) — python:3.12-slim, WORKDIR /app, установка из docs/config/requirements-docker.txt, копирование blocks/ и docs/, CMD по умолчанию `python -m blocks.spambot --project flowcabinet`.
- **docker-compose.yml** (корень) — сервисы spambot, post_flow; общий build, env_file: .env, volume для blocks/projects/data.
- **docs/config/requirements-docker.txt** — зависимости для образа без mcp; вместо googletrans — deep-translator (избежание конфликта httpx с python-telegram-bot).
- **docs/guides/DOCKER.md** — сборка, запуск контейнера и compose, путь к .env, установка Docker (в т.ч. код 3), виртуализация/WSL, ограничение Playwright, типичные проблемы.
- **README.md** — секция «Docker» со ссылкой на DOCKER.md.
- **.cursor/rules/project-structure.mdc** — исключения в корне: Dockerfile, .dockerignore, docker-compose.yml.
- **blocks/spambot/newsbot.py** — порядок инициализации переводчика: сначала deep_translator, затем googletrans (для работы в контейнере с deep-translator без потери совместимости на хосте).

### Ключевые решения

- Один образ для всего проекта (мультипроектность сохранена).
- MCP не в образе (обычно на хосте для Cursor).
- В образе deep-translator вместо googletrans из-за конфликта httpx; на хосте оба варианта по-прежнему поддерживаются.

---

## TESTING

- `docker build -t contentzavod .` — успешная сборка.
- `docker run --rm --env-file .env contentzavod python -m blocks.spambot --list-projects` — вывод списка проектов (flowcabinet и др.) при запуске из корня проекта.
- Проверка пути к .env: при запуске не из корня — явное указание в гайде (полный путь или cd в корень).

---

## LESSONS LEARNED

- При добавлении Docker проверять совместимость зависимостей (pip/образ) заранее; отдельный requirements-docker.txt удобен при конфликтах версий.
- Для Windows: установка Docker (winget/ручной установщик при коде 3), включение виртуализации/WSL, запуск из корня проекта и путь к .env — включать в гайд сразу.
- Рефлексия с фиксацией обхода проблем (установка, виртуализация, зависимости, .env) полезна для архива и повторного использования.

---

## REFERENCES

- Рефлексия: `memory-bank/reflection/reflection-docker-001.md`
- План и чеклист (на момент архива): `memory-bank/tasks.md` (секция задачи docker-001)
- Документация: `docs/guides/DOCKER.md`
