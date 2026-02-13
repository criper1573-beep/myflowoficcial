# -*- coding: utf-8 -*-
"""Вставка одного тестового запуска для проверки дашборда. Запуск: python -m blocks.analytics.seed_test_data"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Корень проекта в path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from blocks.analytics import db


def _now(offset_days: int = 0) -> str:
    t = datetime.now() + timedelta(days=offset_days)
    return t.isoformat()


def main():
    conn = db.get_connection()
    run_id = db.insert_run(
        conn,
        started_at=_now(-1),
        topic="Каркас FlowCabinet: система Knauf и конструктивная жёсткость",
        headline="Каркас FlowCabinet: особенности системы Knauf и конструктивная жёсткость",
        source="google_sheets",
        publish_dir="publish/001",
    )
    steps = [
        ("fetch_topic", "Получение темы из таблицы", "completed", None),
        ("generate_headline", "Генерация заголовка", "completed", None),
        ("generate_article", "Генерация текста статьи", "completed", None),
        ("build_article", "Генерация обложки и картинок, сборка статьи", "completed", None),
        ("save_article", "Сохранение статьи", "completed", None),
        ("publish_zen", "Публикация в Дзен", "completed", None),
        ("delete_topic", "Удаление темы из таблицы", "completed", None),
    ]
    for i, (name, label, status, err) in enumerate(steps):
        step_id = db.insert_step(conn, run_id, name, label, i, status="pending")
        db.update_step_started(conn, step_id, _now(-1))
        db.update_step_finished(conn, step_id, _now(-1), status, err, None)
    db.update_run_finished(conn, run_id, _now(-1), "completed")

    # Второй запуск — с одной ошибкой
    run_id2 = db.insert_run(
        conn,
        started_at=_now(0),
        topic="Ремонт офиса под ключ",
        headline="Ремонт офиса под ключ: этапы и сроки",
        source="google_sheets",
        publish_dir="publish/002",
    )
    steps2 = [
        ("fetch_topic", "Получение темы из таблицы", "completed", None),
        ("generate_headline", "Генерация заголовка", "completed", None),
        ("generate_article", "Генерация текста статьи", "failed", "ConnectionResetError: [WinError 10054] Удаленный хост принудительно разорвал существующее подключение.\n  ..."),
        ("build_article", "Генерация обложки и картинок", "skipped", None),
        ("save_article", "Сохранение статьи", "skipped", None),
        ("publish_zen", "Публикация в Дзен", "skipped", None),
    ]
    for i, (name, label, status, err) in enumerate(steps2):
        step_id = db.insert_step(conn, run_id2, name, label, i, status="pending")
        db.update_step_started(conn, step_id, _now(0))
        db.update_step_finished(conn, step_id, _now(0), status, err, None)
    db.update_run_finished(conn, run_id2, _now(0), "failed")

    conn.close()
    print("Тестовые данные добавлены: 2 запуска (1 успешный, 1 с ошибкой). Откройте http://localhost:8050")


if __name__ == "__main__":
    main()
