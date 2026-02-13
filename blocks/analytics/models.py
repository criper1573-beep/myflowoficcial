# -*- coding: utf-8 -*-
"""Модели для трекера: Run и Step (dataclasses, без ORM)."""
from dataclasses import dataclass
from typing import Optional, List, Any
from datetime import datetime


@dataclass
class Step:
    """Один шаг пайплайна в рамках запуска."""
    id: int
    run_id: int
    name: str
    label: str
    status: str  # pending | running | completed | failed | skipped
    started_at: Optional[str]
    finished_at: Optional[str]
    error_message: Optional[str]
    metadata: Optional[str]  # JSON
    sort_order: int

    @classmethod
    def from_row(cls, row: tuple) -> "Step":
        return cls(
            id=row[0],
            run_id=row[1],
            name=row[2],
            label=row[3],
            status=row[4],
            started_at=row[5],
            finished_at=row[6],
            error_message=row[7],
            metadata=row[8],
            sort_order=row[9],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "name": self.name,
            "label": self.label,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "sort_order": self.sort_order,
        }


@dataclass
class Run:
    """Один запуск пайплайна."""
    id: int
    started_at: str
    finished_at: Optional[str]
    status: str  # running | completed | failed
    topic: Optional[str]
    headline: Optional[str]
    source: str
    publish_dir: Optional[str]
    channel: Optional[str] = None  # zen, telegram, site, vk, vc_ru
    steps: Optional[List[Step]] = None

    @classmethod
    def from_row(cls, row: tuple, steps: Optional[List[Step]] = None) -> "Run":
        channel = row[8] if len(row) > 8 else None
        return cls(
            id=row[0],
            started_at=row[1],
            finished_at=row[2],
            status=row[3],
            topic=row[4],
            headline=row[5],
            source=row[6],
            publish_dir=row[7],
            channel=channel,
            steps=steps,
        )

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "topic": self.topic,
            "headline": self.headline,
            "source": self.source,
            "publish_dir": self.publish_dir,
            "channel": self.channel,
        }
        if self.steps is not None:
            d["steps"] = [s.to_dict() for s in self.steps]
        return d
