# Active Context

Текущий фокус разработки. Сбрасывается после /archive.

---

**Текущий фокус:** dev-changelog-004 — Dev-ветка с деплоем на поддомен + история патчей.

**Контекст:**
- Production: main → flowimage.ru, директория /root/contentzavod, сервисы grs-image-web, analytics-dashboard
- Staging (новое): dev → dev.flowimage.ru (поддомен), отдельная директория или порт, grs-image-web-staging
- Webhook: один endpoint, проверка ref в payload — main → prod, dev → staging
- CHANGELOG: уже есть docs/guides/CHANGELOG.md; добавить версии (v2.0, v2.1) и workflow

**Последнее обновление:** VAN 2026-02-18 — инициализация задачи dev-changelog-004.
