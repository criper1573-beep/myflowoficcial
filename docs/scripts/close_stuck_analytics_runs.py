# -*- coding: utf-8 -*-
"""
Закрытие «зависших» запусков в БД аналитики: помечает runs и steps как failed с записью ошибки,
чтобы статистика дашборда не портилась (зависшие запуски учитываются как неуспешные).

Источник данных дашборда: storage/analytics.db, таблицы runs и steps (см. docs/guides/ANALYTICS_DASHBOARD_DATA.md).

Запуск из корня проекта:
  python docs/scripts/close_stuck_analytics_runs.py 34 35 36 37   # закрыть указанные run_id
  python docs/scripts/close_stuck_analytics_runs.py --all         # закрыть все с status='running'
  python docs/scripts/close_stuck_analytics_runs.py --all --project flow

На сервере:
  cd /root/contentzavod && python docs/scripts/close_stuck_analytics_runs.py --all
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blocks.analytics import db

STUCK_ERROR_MSG = "Остановлено вручную (зависший запуск). Процесс оркестратора был остановлен или завершился до finish_run()."


def _now() -> str:
    return datetime.now().isoformat()


def close_stuck_runs(conn, run_ids: list[int], error_message: str = STUCK_ERROR_MSG) -> int:
    """Помечает указанные запуски и их незавершённые шаги как failed. Возвращает количество обновлённых runs."""
    updated = 0
    now = _now()
    for run_id in run_ids:
        cur = conn.execute(
            "SELECT id FROM steps WHERE run_id = ? AND status IN ('running', 'pending')",
            (run_id,),
        )
        step_ids = [row[0] for row in cur.fetchall()]
        for step_id in step_ids:
            db.update_step_finished(
                conn, step_id, now, "failed", error_message=error_message
            )
        db.update_run_finished(conn, run_id, finished_at=now, status="failed")
        updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Пометить зависшие запуски аналитики как failed с записью ошибки."
    )
    parser.add_argument(
        "run_ids",
        nargs="*",
        type=int,
        help="ID запусков для закрытия (например 34 35 36 37).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Закрыть все запуски со статусом running.",
    )
    parser.add_argument(
        "--project",
        default="flow",
        choices=db.PROJECTS,
        help="Проект (БД): flow или fulfilment.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать, какие run_id будут закрыты, не менять БД.",
    )
    args = parser.parse_args()

    if not args.all and not args.run_ids:
        parser.error("Укажите run_id или --all")

    conn = db.get_connection(project=args.project)

    if args.all:
        cur = conn.execute("SELECT id FROM runs WHERE status = 'running' ORDER BY id")
        run_ids = [row[0] for row in cur.fetchall()]
        if not run_ids:
            print("Нет запусков со статусом 'running'.")
            conn.close()
            return 0
        print("Найдены зависшие запуски (status='running'):", run_ids)
    else:
        run_ids = args.run_ids
        # проверить существование
        existing = set()
        for rid in run_ids:
            cur = conn.execute("SELECT id, status FROM runs WHERE id = ?", (rid,))
            row = cur.fetchone()
            if row:
                existing.add(rid)
                if row[1] != "running":
                    print("Предупреждение: run_id=%s имеет status=%s (не running)." % (rid, row[1]))
        run_ids = [r for r in run_ids if r in existing]
        if not run_ids:
            print("Нет указанных run_id в БД.")
            conn.close()
            return 1

    if args.dry_run:
        print("Dry-run: были бы закрыты run_id:", run_ids)
        conn.close()
        return 0

    n = close_stuck_runs(conn, run_ids)
    conn.close()
    print("Закрыто запусков: %d (run_id: %s)." % (n, run_ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
