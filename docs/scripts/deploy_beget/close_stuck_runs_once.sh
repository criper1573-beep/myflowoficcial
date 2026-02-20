#!/bin/bash
# Разовое закрытие зависших запусков 34–37 в БД аналитики (чтобы не портилась статистика).
# Запуск на сервере: cd /root/contentzavod && bash docs/scripts/deploy_beget/close_stuck_runs_once.sh
set -e
# Перейти в корень репо: из docs/scripts/deploy_beget вверх на 3 уровня
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$ROOT"
# Путь к БД как в blocks/analytics/db.py (по умолчанию storage/analytics.db или из .env)
if [ -n "$ANALYTICS_DB_PATH" ]; then
  DB="$ANALYTICS_DB_PATH"
else
  DB="$ROOT/storage/analytics.db"
fi
if [ ! -f "$DB" ]; then
  # попробовать analytics_flow.db
  DB="$ROOT/storage/analytics_flow.db"
fi
if [ ! -f "$DB" ]; then
  echo "DB not found: $ROOT/storage/analytics.db nor analytics_flow.db"
  exit 1
fi
sqlite3 "$DB" "
UPDATE steps SET finished_at = datetime('now'), status = 'failed', error_message = 'Остановлено вручную (зависший запуск)' WHERE run_id IN (34,35,36,37) AND status IN ('running','pending');
UPDATE runs SET finished_at = datetime('now'), status = 'failed' WHERE id IN (34,35,36,37) AND status = 'running';
"
echo "Done. Stuck runs 34–37 marked as failed."
