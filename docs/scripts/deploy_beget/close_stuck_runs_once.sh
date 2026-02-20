#!/bin/bash
# Разовое закрытие зависших запусков 34–37 в БД аналитики (чтобы не портилась статистика).
# Запуск на сервере: cd /root/contentzavod && bash docs/scripts/deploy_beget/close_stuck_runs_once.sh
set -e
cd "$(dirname "$0")/../.."
DB="storage/analytics.db"
if [ ! -f "$DB" ]; then
  echo "DB not found: $DB"
  exit 1
fi
sqlite3 "$DB" "
UPDATE steps SET finished_at = datetime('now'), status = 'failed', error_message = 'Остановлено вручную (зависший запуск)' WHERE run_id IN (34,35,36,37) AND status IN ('running','pending');
UPDATE runs SET finished_at = datetime('now'), status = 'failed' WHERE id IN (34,35,36,37) AND status = 'running';
"
echo "Done. Stuck runs 34–37 marked as failed."
