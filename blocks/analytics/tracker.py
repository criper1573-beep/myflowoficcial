# -*- coding: utf-8 -*-
"""
RunTracker: чекпоинты пайплайна.
start_run() -> run_id; with tracker.step(run_id, name, label): ...; finish_run(run_id).
Какой проект писать в БД: RunTracker(project='flow'|'fulfilment') или env ANALYTICS_PROJECT.
"""
import os
import traceback
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Generator, Any

from . import db
from .models import Step


def _now() -> str:
    return datetime.now().isoformat()


class RunTracker:
    """Трекер запусков: запись шагов в SQLite с автоматической фиксацией ошибок.
    project: 'flow' | 'fulfilment' — в какую БД писать; по умолчанию из env ANALYTICS_PROJECT или 'flow'.
    """

    def __init__(self, project: Optional[str] = None):
        self._project = (project or os.getenv("ANALYTICS_PROJECT") or db.DEFAULT_PROJECT).strip()
        if self._project not in db.PROJECTS:
            self._project = db.DEFAULT_PROJECT
        self._conn = db.get_connection(project=self._project)
        self._step_counter: dict[int, int] = {}  # run_id -> sort_order

    def start_run(
        self,
        topic: Optional[str] = None,
        headline: Optional[str] = None,
        source: str = "google_sheets",
        publish_dir: Optional[str] = None,
    ) -> int:
        """Начинает новый запуск. Возвращает run_id."""
        run_id = db.insert_run(
            self._conn,
            started_at=_now(),
            topic=topic,
            headline=headline,
            source=source,
            publish_dir=publish_dir,
        )
        self._step_counter[run_id] = 0
        return run_id

    def update_run_topic(self, run_id: int, topic: str) -> None:
        """Обновляет тему запуска (после fetch_topic)."""
        db.update_run_topic(self._conn, run_id, topic)

    def update_run_headline(self, run_id: int, headline: str) -> None:
        """Обновляет заголовок запуска (после генерации)."""
        self._conn.execute("UPDATE runs SET headline = ? WHERE id = ?", (headline, run_id))
        self._conn.commit()

    def update_run_publish_dir(self, run_id: int, publish_dir: str) -> None:
        """Обновляет путь к папке публикации."""
        self._conn.execute("UPDATE runs SET publish_dir = ? WHERE id = ?", (publish_dir, run_id))
        self._conn.commit()

    def update_run_channel(self, run_id: int, channel: Optional[str]) -> None:
        """Устанавливает канал(ы) запуска после публикации. Одна строка или через запятую: 'zen', 'telegram', 'zen,telegram'."""
        db.update_run_channel(self._conn, run_id, channel)

    @contextmanager
    def step(
        self,
        run_id: int,
        name: str,
        label: str,
        metadata: Optional[dict] = None,
    ) -> Generator[None, None, None]:
        """
        Контекстный менеджер шага. При выходе: completed или failed (с error_message).
        """
        sort_order = self._step_counter.get(run_id, 0)
        self._step_counter[run_id] = sort_order + 1

        step_id = db.insert_step(
            self._conn,
            run_id=run_id,
            name=name,
            label=label,
            sort_order=sort_order,
            status="running",
        )
        db.update_step_started(self._conn, step_id, _now())

        error_message: Optional[str] = None
        status = "completed"
        try:
            yield
        except Exception as e:
            status = "failed"
            error_message = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            raise
        finally:
            import json
            meta_str = json.dumps(metadata, ensure_ascii=False) if metadata else None
            db.update_step_finished(
                self._conn,
                step_id,
                finished_at=_now(),
                status=status,
                error_message=error_message,
                metadata=meta_str,
            )

    def finish_run(self, run_id: int) -> None:
        """Завершает запуск: статус completed, если есть хотя бы один failed шаг — failed."""
        cur = self._conn.execute(
            "SELECT status FROM steps WHERE run_id = ? AND status = 'failed' LIMIT 1",
            (run_id,),
        )
        has_failed = cur.fetchone() is not None
        status = "failed" if has_failed else "completed"
        db.update_run_finished(self._conn, run_id, _now(), status)
        self._step_counter.pop(run_id, None)
