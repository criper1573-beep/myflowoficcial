# -*- coding: utf-8 -*-
"""SQLite: подключение, миграция, создание таблиц runs и steps."""
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

STORAGE_DIR = PROJECT_ROOT / "storage"
# Проекты: у каждого своя БД (разные аккаунты/источники аналитики)
PROJECTS = ["flow", "fulfilment"]  # id для API и путей
DEFAULT_PROJECT = "flow"

# Одна БД по умолчанию (для обратной совместимости и env)
_LEGACY_DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", str(STORAGE_DIR / "analytics.db")))
if not os.path.isabs(_LEGACY_DB_PATH):
    _LEGACY_DB_PATH = PROJECT_ROOT / _LEGACY_DB_PATH


def get_db_path(project: Optional[str] = None) -> Path:
    """Путь к файлу БД для проекта. flow → legacy analytics.db; fulfilment → отдельная БД."""
    if project and project != DEFAULT_PROJECT and project in PROJECTS:
        return STORAGE_DIR / f"analytics_{project}.db"
    # flow и None → legacy БД (analytics.db), где лежат все данные
    return _LEGACY_DB_PATH


def get_connection(project: Optional[str] = None) -> sqlite3.Connection:
    """Возвращает соединение с БД проекта; создаёт директорию и таблицы при первом запуске.
    project: 'flow' | 'fulfilment'; None — одна общая БД (legacy)."""
    path = get_db_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Создаёт таблицы runs и steps, если их ещё нет."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL DEFAULT 'running',
            topic TEXT,
            headline TEXT,
            source TEXT NOT NULL DEFAULT 'google_sheets',
            publish_dir TEXT,
            channel TEXT
        );
    """)
    # Миграция: добавить channel если таблица уже была
    try:
        conn.execute("ALTER TABLE runs ADD COLUMN channel TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # колонка уже есть
    # Бэкфилл: старые запуски без channel считаем Дзен (автопостинг был только в Дзен)
    conn.execute("UPDATE runs SET channel = 'zen' WHERE channel IS NULL")
    conn.commit()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            label TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            started_at TEXT,
            finished_at TEXT,
            error_message TEXT,
            metadata TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_steps_run_id ON steps(run_id);
        CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
        CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
    """)
    conn.commit()


def insert_run(
    conn: sqlite3.Connection,
    started_at: str,
    topic: Optional[str] = None,
    headline: Optional[str] = None,
    source: str = "google_sheets",
    publish_dir: Optional[str] = None,
    channel: Optional[str] = None,
) -> int:
    """Вставляет запись запуска, возвращает run_id."""
    cur = conn.execute(
        "INSERT INTO runs (started_at, status, topic, headline, source, publish_dir, channel) VALUES (?, 'running', ?, ?, ?, ?, ?)",
        (started_at, topic, headline, source, publish_dir, channel),
    )
    conn.commit()
    return cur.lastrowid


def update_run_topic(conn: sqlite3.Connection, run_id: int, topic: str) -> None:
    conn.execute("UPDATE runs SET topic = ? WHERE id = ?", (topic, run_id))
    conn.commit()


def update_run_channel(conn: sqlite3.Connection, run_id: int, channel: Optional[str]) -> None:
    """Устанавливает канал(ы) запуска: одна строка или через запятую (zen, telegram)."""
    conn.execute("UPDATE runs SET channel = ? WHERE id = ?", (channel or None, run_id))
    conn.commit()


def update_run_finished(
    conn: sqlite3.Connection,
    run_id: int,
    finished_at: str,
    status: str,
) -> None:
    """Обновляет время окончания и статус запуска."""
    conn.execute(
        "UPDATE runs SET finished_at = ?, status = ? WHERE id = ?",
        (finished_at, status, run_id),
    )
    conn.commit()


def insert_step(
    conn: sqlite3.Connection,
    run_id: int,
    name: str,
    label: str,
    sort_order: int,
    status: str = "pending",
) -> int:
    """Вставляет запись шага, возвращает step_id."""
    cur = conn.execute(
        """INSERT INTO steps (run_id, name, label, status, sort_order)
           VALUES (?, ?, ?, ?, ?)""",
        (run_id, name, label, status, sort_order),
    )
    conn.commit()
    return cur.lastrowid


def update_step_started(conn: sqlite3.Connection, step_id: int, started_at: str) -> None:
    conn.execute("UPDATE steps SET status = 'running', started_at = ? WHERE id = ?", (started_at, step_id))
    conn.commit()


def update_step_finished(
    conn: sqlite3.Connection,
    step_id: int,
    finished_at: str,
    status: str,
    error_message: Optional[str] = None,
    metadata: Optional[str] = None,
) -> None:
    conn.execute(
        "UPDATE steps SET finished_at = ?, status = ?, error_message = ?, metadata = ? WHERE id = ?",
        (finished_at, status, error_message, metadata, step_id),
    )
    conn.commit()


def get_run(conn: sqlite3.Connection, run_id: int) -> Optional[Tuple]:
    """Возвращает одну строку runs по id или None."""
    cur = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    return cur.fetchone()


def get_steps_for_run(conn: sqlite3.Connection, run_id: int) -> List[Tuple]:
    """Возвращает список строк steps для run_id, отсортированный по sort_order."""
    cur = conn.execute(
        "SELECT * FROM steps WHERE run_id = ? ORDER BY sort_order, id",
        (run_id,),
    )
    return cur.fetchall()


def get_runs(
    conn: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    channel: Optional[str] = None,
) -> List[Tuple]:
    """Список запусков (новые первые). channel: фильтр по каналу (zen, telegram, …); None — все. channel в БД может быть через запятую (zen,telegram)."""
    if channel:
        # Совпадение по одному из каналов в списке: ,zen, в ,zen,telegram,
        ch_like = "%," + channel + ",%"
        ch_start = channel + ",%"
        ch_end = "%," + channel
        ch_exact = channel
        if status:
            cur = conn.execute(
                """SELECT * FROM runs WHERE status = ?
                   AND (channel = ? OR channel LIKE ? OR channel LIKE ? OR channel LIKE ?)
                   ORDER BY id DESC LIMIT ? OFFSET ?""",
                (status, ch_exact, ch_like, ch_start, ch_end, limit, offset),
            )
        else:
            cur = conn.execute(
                """SELECT * FROM runs WHERE (channel = ? OR channel LIKE ? OR channel LIKE ? OR channel LIKE ?)
                   ORDER BY id DESC LIMIT ? OFFSET ?""",
                (ch_exact, ch_like, ch_start, ch_end, limit, offset),
            )
    else:
        if status:
            cur = conn.execute(
                "SELECT * FROM runs WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
    return cur.fetchall()


def get_stats(conn: sqlite3.Connection, channel: Optional[str] = None) -> dict:
    """Сводная статистика: всего запусков, успешных, с ошибками, сегодня. channel=None — все каналы."""
    if channel:
        like = " (channel = ? OR channel LIKE ? OR channel LIKE ? OR channel LIKE ?) "
        args = (channel, "%," + channel + ",%", channel + ",%", "%," + channel)
        base = "SELECT COUNT(*) FROM runs WHERE" + like
        cur = conn.execute(base, args)
        total = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM runs WHERE" + like + "AND status = 'completed'", args)
        completed = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM runs WHERE" + like + "AND status = 'failed'", args)
        failed = cur.fetchone()[0]
        cur = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE" + like + "AND date(started_at) = date('now', 'localtime')",
            args,
        )
        today = cur.fetchone()[0]
    else:
        cur = conn.execute("SELECT COUNT(*) FROM runs")
        total = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'completed'")
        completed = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'failed'")
        failed = cur.fetchone()[0]
        cur = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE date(started_at) = date('now', 'localtime')"
        )
        today = cur.fetchone()[0]
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "today": today,
        "success_rate": round(100 * completed / total, 1) if total else 0,
    }


def get_timeline(
    conn: sqlite3.Connection, days: int = 30, channel: Optional[str] = None
) -> List[dict]:
    """Публикации по дням для графика. channel=None — все каналы."""
    if channel:
        cur = conn.execute("""
            SELECT date(started_at) AS day, COUNT(*) AS count
            FROM runs
            WHERE (channel = ? OR channel LIKE ? OR channel LIKE ? OR channel LIKE ?)
              AND started_at >= date('now', 'localtime', ?)
            GROUP BY date(started_at)
            ORDER BY day
        """, (channel, "%," + channel + ",%", channel + ",%", "%," + channel, f"-{days} days"))
    else:
        cur = conn.execute("""
            SELECT date(started_at) AS day, COUNT(*) AS count
            FROM runs
            WHERE started_at >= date('now', 'localtime', ?)
            GROUP BY date(started_at)
            ORDER BY day
        """, (f"-{days} days",))
    return [{"day": row[0], "count": row[1]} for row in cur.fetchall()]
