# Memory Bank — Tasks (Source of Truth)

Активные и завершённые задачи. Обновляется командами /van, /plan, /build, /reflect, /archive.

---

## Текущая задача

**ID:** flowimage-store-fix  
**Описание:** Проверить проект https://flowimage.store/: (1) почему на дашборд Generation не тянется информация о сгенерированном в flowimage.ru; (2) почему каждые 1–2 минуты приходят уведомления в Telegram о нерабочем quickpack, хотя на главной он отображается как работающий.

**Сложность:** 3 (расследование + правки в нескольких местах: дашборд, источник данных, watchdog).

**Ограничение:** Не приступать к build до акцепта плана пользователем.

---

### Гипотезы (по результатам VAN)

**1. Generation не тянется на flowimage.store**
- Дашборд (blocks/analytics) берёт данные **только с локальной ФС**: `blocks/grs_image_web/generated` и `blocks/grs_image_web/uploaded` (см. `blocks/analytics/api.py`: `GENERATED_DIR`, `UPLOADED_DIR`).
- Если flowimage.store и flowimage.ru на одном сервере и одном репозитории (`/root/contentzavod`) — данные должны быть видны. Возможные причины: разный рабочий каталог/репозиторий на сервере (в гайде указан репо myflowoficcial для дашборда), права доступа к папкам, или ошибка API/фронта (500, CORS, неверный base URL).

**2. Уведомления про quickpack каждые 1–2 минуты**
- Watchdog (`blocks/analytics/watchdog_services.py`) проверяет сервисы **только через systemd** (`systemctl is-active`), интервал по умолчанию 90 сек (`WATCHDOG_INTERVAL`).
- Для quickpack **не используется** `QUICKPACK_URL`. На дашборде при заданном `QUICKPACK_URL` статус Quickpack определяется по HTTP (главная отдаёт 200 → «работает»).
- Итог: если quickpack **не** запущен как systemd-юнит (например, отдаётся только через nginx), watchdog всегда видит `inactive` → каждые ~90 сек шлёт «Сервис упал» и «Перезапущен»/«Не удалось перезапустить».

---

## План реализации (PLAN)

### Цель 1: Данные Generation на flowimage.store

| Шаг | Действие | Файлы / место |
|-----|----------|----------------|
| 1.1 | **Диагностика (на сервере).** Проверить: из какого каталога запущен `analytics-dashboard` (WorkingDirectory в systemd), есть ли по пути `blocks/grs_image_web/generated` и `blocks/grs_image_web/uploaded` данные; откуда запущен `grs-image-web` и куда он пишет. При необходимости — скрипт или команды в гайде. | Сервер, при необходимости `docs/scripts/` или `docs/guides/` |
| 1.2 | **Гибкие пути в дашборде.** Добавить в API дашборда поддержку переопределения путей через env (например `GRS_IMAGE_WEB_GENERATED_DIR`, `GRS_IMAGE_WEB_UPLOADED_DIR` — абсолютные пути). Если переменные заданы — использовать их вместо путей относительно `BLOCK_DIR.parent / "grs_image_web"`. | `blocks/analytics/api.py` |
| 1.3 | **Документация.** Описать в `docs/guides/DEPLOY_DASHBOARD_FLOWIMAGE_STORE.md` или `blocks/analytics/README.md`: когда задавать эти переменные (разные репо/рабочие каталоги), пример для сервера. | `docs/guides/`, `blocks/analytics/README.md` |

**Зависимости:** 1.2 и 1.3 не зависят от 1.1; 1.1 можно оформить как чеклист в гайде или отдельный скрипт проверки.

---

### Цель 2: Убрать ложные алерты Quickpack в Telegram

| Шаг | Действие | Файлы / место |
|-----|----------|----------------|
| 2.1 | **Проверка Quickpack по HTTP в watchdog.** В `watchdog_services.py`: для юнита `quickpack` при заданном `QUICKPACK_URL` считать сервис работающим по результату HTTP GET (200 = active). Не вызывать `restart_service` для quickpack при проверке по URL (нет systemd-юнита для перезапуска). | `blocks/analytics/watchdog_services.py` |
| 2.2 | **Поведение.** Если `QUICKPACK_URL` задан — только HTTP-проверка, алерты только при недоступности сайта. Если не задан — оставить текущую логику (systemd). | Тот же файл |
| 2.3 | **Документация.** В `docs/rules/KEYS_AND_TOKENS.md` (или README watchdog) указать: для отключения алертов по quickpack при работе сайта через nginx задать `QUICKPACK_URL` в `.env` на сервере, где крутится watchdog. | `docs/rules/KEYS_AND_TOKENS.md`, при необходимости `blocks/analytics/README.md` |

**Зависимости:** 2.1 и 2.2 выполняются вместе в одном изменении; 2.3 — после.

---

### Компоненты и риски

- **Компоненты:** analytics API (пути к generation), watchdog (логика quickpack), документация деплоя и ключей.
- **Риски:** На сервере дашборд может быть из репо myflowoficcial — тогда переменные окружения для путей позволят указать общую папку с grs_image_web без смены репозитория.
- **Креативная фаза не требуется** — решения однозначны (env для путей, HTTP для quickpack в watchdog).

---

### Чеклист перед build

- [x] Реализовать переопределение `GENERATED_DIR` / `UPLOADED_DIR` в `blocks/analytics/api.py` через env.
- [x] Обновить гайд/README по дашборду (когда задавать эти env).
- [x] В `watchdog_services.py`: для quickpack при `QUICKPACK_URL` проверять HTTP, не слать алерты и не перезапускать systemd.
- [x] Документировать использование `QUICKPACK_URL` для watchdog в KEYS_AND_TOKENS или README.

### Build выполнено (2026-02-18)

- **api.py:** добавлены `GRS_IMAGE_WEB_DIR`, `GRS_IMAGE_WEB_GENERATED_DIR`, `GRS_IMAGE_WEB_UPLOADED_DIR`; пути к generation считаются из env при задании.
- **watchdog_services.py:** для юнита quickpack при заданном `QUICKPACK_URL` — проверка по HTTP (200 = ок), алерты только при недоступности URL; перезапуск systemd не вызывается.
- **Документация:** DEPLOY_DASHBOARD_FLOWIMAGE_STORE.md (переменные для Generation, чеклист проверки на сервере), blocks/analytics/README.md (раздел Generation и env), KEYS_AND_TOKENS.md (QUICKPACK_URL и watchdog).

---

## История

| Task ID | Описание | Статус | Архив |
|---------|----------|--------|-------|
| dev-changelog-004 | Dev-ветка с деплоем на поддомен + история патчей | COMPLETE | [archive-dev-changelog-004.md](archive/archive-dev-changelog-004.md) |
| grs-image-web-003 | Починка сайта генерации картинок (Ссылки, улучшение промпта, API) | COMPLETE | [archive-grs-image-web-003.md](archive-grs-image-web-003.md) |
| webhook-002 | Деплой по вебхуку (GitHub → сервер) | COMPLETE | [archive-webhook-002.md](archive-webhook-002.md) |
| docker-001 | Реализовать Docker в проекте | COMPLETE | [archive-docker-001.md](archive-docker-001.md) |
