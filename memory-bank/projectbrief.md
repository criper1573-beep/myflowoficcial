# Project Brief — КонтентЗавод (ContentZavod)

## Что это

Система автоматизированного создания и распространения контента. Один «завод» — несколько проектов; у каждого свои аккаунты (Telegram, Дзен, Google Таблицы и т.д.), API ИИ общий.

## Структура проекта

- **blocks/** — код блоков: AI (GRS), Spambot (RSS → Telegram), Post FLOW, проекты и др.
- **docs/** — документация, конфигурация, скрипты, гайды, правила, ключи.
- **memory-bank/** — контекст и задачи для Cursor Memory Bank (этот workflow).

В корне только README.md, .gitignore и папки. Новый код и скрипты — в blocks/ или docs/.

## Ключевые блоки

- **blocks/ai_integrations/** — клиент GRS AI (общий для всех проектов).
- **blocks/spambot/** — NewsBot: RSS → Telegram.
- **blocks/post_flow/** — Post FLOW: тема из Google Таблицы → GRS AI → канал FLOW.
- **blocks/projects/** — конфигурация по каждому проекту (мультипроектность).
- **blocks/mcp_server/** — MCP content-factory (Zen, GRS chat/image).

## Правила работы (Cursor)

- Не создавать файлы в корне — только в blocks/ или docs/ (исключение: memory-bank/).
- Не предлагать ручные шаги — выполнять всё самому через инструменты.
- Ключи и токены — в docs/rules/KEYS_AND_TOKENS.md и docs/config/.env.example; реальные значения только в .env.
- Перед новой задачей проверять MCP (content-factory, реестр); для Дзен/публикаций использовать MCP, а не только терминал.
- Выбор модели по задаче: код/автоматизация → Opus; контент/идеи → GPT; документация → Sonnet (см. .cursor/rules/model-AI.mdc).

## Деплой

- **По вебхуку:** push в `main` → production (flowimage.ru); push в `dev` → staging (dev.flowimage.ru, при настройке). Подробно: **docs/guides/DEPLOY_WEBHOOK.md**, staging — **docs/guides/DEPLOY_STAGING.md**. Секрет вебхука — в systemd-юните на сервере (см. docs/rules/KEYS_AND_TOKENS.md).

## Документация

- Старт и справка: docs/guides/
- Правила и ключи: docs/rules/
- Архитектура: docs/architecture/
- Конфигурация: docs/config/

Версия проекта: 2.1 (docs/config/VERSION).
