# Product Context

Продуктовый контекст и требования по проекту КонтентЗавод.

---

## Продукты/направления

- **NewsBot (Spambot)** — автоматическая публикация из RSS в Telegram по проектам.
- **Post FLOW** — генерация постов из Google Таблицы (тема → GRS AI) и публикация в канал FLOW.
- **Дзен** — статьи, черновики, публикация (в т.ч. через MCP content-factory).
- **GRS AI** — генерация текста и изображений (общий API для всех блоков).
- **Мультипроектность** — один репозиторий, несколько проектов с разными аккаунтами и конфигами.

## Деплой

- Актуальный способ: **деплой по вебхуку**. Push в `main` → GitHub шлёт webhook на VPS → `git pull`, pip, перезапуск сервисов (grs-image-web и др.). Гайды: docs/guides/DEPLOY_WEBHOOK.md, DEPLOY_WEBHOOK_VERIFICATION.md.

## Ограничения и соглашения

- Конфигурация проектов: blocks/projects/data/<project_id>.yaml.
- Точка входа Spambot: `python -m blocks.spambot` или blocks\spambot\start.bat.
- Лаунчеры и новые скрипты — в blocks/ или docs/scripts/, не в корне.

Дополняйте по мере появления новых продуктов и требований.
