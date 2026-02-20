# Откуда дашборд аналитики берёт данные

## Источник данных

- **БД:** SQLite, файл `storage/analytics.db` (проект flow) или `storage/analytics_{project}.db`.
- **Путь к БД:** задаётся в `blocks/analytics/db.py` (`get_db_path(project)`), по умолчанию `PROJECT_ROOT/storage/analytics.db`.
- **Таблицы:**
  - **runs** — запуски: `id`, `started_at`, `finished_at`, `status` (running | completed | failed), `topic`, `headline`, `source`, `publish_dir`, `channel`.
  - **steps** — шаги цепочки: `id`, `run_id`, `name`, `label`, `status` (pending | running | completed | failed), `started_at`, `finished_at`, `error_message`, `metadata`, `sort_order`.

## API дашборда

- **Модуль:** `blocks/analytics/api.py` (FastAPI).
- **Эндпоинты:**
  - `GET /api/runs` — список запусков (из `db.get_runs()`), для каждого подгружаются шаги (`db.get_steps_for_run()`).
  - `GET /api/runs/{run_id}` — один запуск и его шаги.
  - Статистика и графики строятся по тем же таблицам (успешные/неуспешные по `runs.status`).

Запись в БД выполняет **RunTracker** в `blocks/analytics/tracker.py`: оркестратор и пайплайны вызывают `start_run()`, `step()`, `finish_run()`. Если процесс убит до `finish_run()`, запуск остаётся в статусе `running`, шаги — `running`/`pending`, и статистика «портится» (зависшие запуски не считаются ни успехом, ни ошибкой).

## Закрытие зависших запусков

Чтобы такие запуски не искажали статистику, их нужно вручную пометить как завершённые с ошибкой:

1. **Скрипт (рекомендуется):**  
   `python docs/scripts/close_stuck_analytics_runs.py [--all | run_id1 run_id2 ...]`  
   Помечает указанные (или все с `status='running'`) запуски как `failed`, проставляет `finished_at` и для всех шагов в статусе `running`/`pending` — `failed` с записью ошибки (например: «Остановлено вручную (зависший запуск)»). Подробности — в docstring скрипта.

2. **Вручную (SQL):**  
   Подключиться к `storage/analytics.db` и:
   - для нужных `runs` с `status='running'` выставить `finished_at = datetime('now')`, `status = 'failed'`;
   - для их `steps` с `status IN ('running','pending')` выставить `finished_at = datetime('now')`, `status = 'failed'`, `error_message = 'Остановлено вручную (зависший запуск)'`.

После этого дашборд и отчёты по успешным/неуспешным запускам будут учитывать эти записи корректно.
