# Memory Bank — Tasks (Source of Truth)

Активные и завершённые задачи. Обновляется командами /van, /plan, /build, /reflect, /archive.

---

## Текущая задача

| Task ID | dev-changelog-004 |
|---------|-------------------|
| Описание | Dev-ветка с деплоем на поддомен + история патчей (версионирование) |
| Сложность | Level 2 |
| Статус | IN PROGRESS |

### Цели
1. **Dev-ветка с поддоменом:** push в `dev` → деплой на staging (поддомен); push в `main` → деплой на production; основной сайт всегда на стабильной версии.
2. **История патчей:** версионирование релизов (v2.0, v2.1…), CHANGELOG с номерами версий и списком изменений.

### Чеклист
- [x] Создать ветку `dev` от `main`
- [x] Модифицировать `webhook_server.py` — поддержка main (prod) и dev (staging)
- [x] Unit systemd и nginx для staging (grs-image-web-staging, dev.flowimage.ru)
- [x] Гайд `docs/guides/GIT_BRANCHING.md`
- [x] Гайд `docs/guides/DEPLOY_STAGING.md`
- [x] Файл `docs/config/VERSION` + формат CHANGELOG с версиями
- [x] Гайд `docs/guides/CHANGELOG_WORKFLOW.md`

---

## История

| Task ID | Описание | Статус | Архив |
|---------|----------|--------|-------|
| grs-image-web-003 | Починка сайта генерации картинок (Ссылки, улучшение промпта, API) | COMPLETE | [archive-grs-image-web-003.md](archive/archive-grs-image-web-003.md) |
| webhook-002 | Деплой по вебхуку (GitHub → сервер) | COMPLETE | [archive-webhook-002.md](archive/archive-webhook-002.md) |
| docker-001 | Реализовать Docker в проекте | COMPLETE | [archive-docker-001.md](archive-docker-001.md) |
