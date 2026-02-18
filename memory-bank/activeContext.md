# Active Context

Текущий фокус разработки. Сбрасывается после /archive.

---

**Текущая задача:** flowimage-store-fix — проверка flowimage.store: (1) данные Generation с flowimage.ru не попадают на дашборд; (2) частые Telegram-алерты про quickpack при «работающем» сервисе на главной.

**Ключевые файлы:**
- `blocks/analytics/api.py` — API дашборда, чтение generation из `blocks/grs_image_web/generated` и `uploaded` (локальная ФС).
- `blocks/analytics/watchdog_services.py` — проверка systemd-юнитов, quickpack в списке; интервал 90 сек; QUICKPACK_URL не используется.
- `blocks/grs_image_web/` — пишет генерации в `generated/<telegram_id>/`, ссылки в `uploaded/<telegram_id>/`.
- `docs/guides/DEPLOY_DASHBOARD_FLOWIMAGE_STORE.md` — деплой дашборда; на сервере может быть репо myflowoficcial.

**Последнее обновление:** BUILD 2026-02-18 — реализованы env для путей generation (api.py), HTTP-проверка quickpack в watchdog, обновлена документация. Готово к проверке на сервере и при необходимости /reflect, /archive.
