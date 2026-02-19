# -*- coding: utf-8 -*-
"""
Планировщик регулярных публикаций в Дзен: 5 слотов в день в заданных временных окнах.
Запуск: python -m blocks.autopost_zen --schedule

Окна (локальное время):
  1) 10:00–10:30
  2) 11:30–12:00
  3) 13:00–13:30
  4) 14:00–14:30
  5) 15:20–16:40

В каждом окне — одна публикация в случайное время. При ошибке генерации или
публикации в Дзен — 3 попытки (сразу, через 1 мин, через 3 мин), затем пропуск
слота с записью ошибки в дашборд аналитики.
"""
import asyncio
import json
import logging
import random
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from . import config
from .zen_client import run_post_flow, PUBLISH_DIR

LOG = logging.getLogger("autopost_zen.scheduler")

# Окна: (час_начала, минута_начала, час_конца, минута_конца)
SCHEDULE_WINDOWS = [
    (10, 0, 10, 30),   # 10:00–10:30
    (11, 30, 12, 0),   # 11:30–12:00
    (13, 0, 13, 30),   # 13:00–13:30
    (14, 0, 14, 30),   # 14:00–14:30
    (15, 20, 16, 40),  # 15:20–16:40
]

RETRY_DELAYS_SEC = [0, 60, 180]  # сразу, через 1 мин, через 3 мин


def _random_time_in_window(base_date: date, h1: int, m1: int, h2: int, m2: int) -> datetime:
    """Случайный момент внутри окна в заданную дату (локальное время)."""
    start_mins = h1 * 60 + m1
    end_mins = h2 * 60 + m2
    if end_mins <= start_mins:
        end_mins += 24 * 60  # через полночь
    r = random.uniform(start_mins, end_mins)
    r = r % (24 * 60)
    h = int(r // 60)
    m = int(r % 60)
    return datetime(base_date.year, base_date.month, base_date.day, h, m, 0)


def _next_run_times() -> list[datetime]:
    """Список следующих 5 времён запуска на сегодня (случайные в окнах), отсортированный."""
    today = date.today()
    return sorted(
        _random_time_in_window(today, h1, m1, h2, m2)
        for (h1, m1, h2, m2) in SCHEDULE_WINDOWS
    )


def _sleep_until(target: datetime) -> None:
    """Ожидание до целевого времени (с логированием)."""
    now = datetime.now()
    if target <= now:
        return
    delta = (target - now).total_seconds()
    LOG.info("Ожидание до %s (%.0f сек)", target.strftime("%H:%M"), delta)
    time.sleep(delta)


def _get_next_slot() -> datetime:
    """Возвращает ближайший будущий слот на сегодня или первый слот завтра."""
    times = _next_run_times()
    now = datetime.now()
    for t in times:
        if t > now:
            return t
    # все слоты сегодня уже прошли — первый слот завтра
    tomorrow = date.today() + timedelta(days=1)
    h1, m1, h2, m2 = SCHEDULE_WINDOWS[0]
    return _random_time_in_window(tomorrow, h1, m1, h2, m2)


def _run_one_slot() -> None:
    """Один слот: генерация (3 попытки) → Telegram → Дзен (3 попытки). Ошибки пишутся в аналитику."""
    from .article_generator import ArticleGenerator

    try:
        from blocks.analytics.tracker import RunTracker
        tracker = RunTracker()
        run_id = tracker.start_run(source="schedule")
        use_tracker = True
    except Exception as e:
        LOG.warning("Аналитика недоступна: %s", e)
        tracker = run_id = None
        use_tracker = False

    def _retry_loop(fn):
        """До 3 попыток с задержками 0, 60, 180 сек. Возвращает результат fn() или пробрасывает последнее исключение."""
        last_error = None
        for attempt, delay in enumerate(RETRY_DELAYS_SEC):
            if delay > 0:
                LOG.info("Повтор через %d сек (попытка %d/3)", delay, attempt + 1)
                time.sleep(delay)
            try:
                return fn()
            except Exception as e:
                last_error = e
                LOG.warning("Попытка %d/3: %s", attempt + 1, e)
                if attempt == 2:
                    raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("Не удалось выполнить шаг после 3 попыток")

    def step(name: str, label: str, fn, retries: bool = False):
        if not use_tracker:
            if retries:
                return _retry_loop(fn)
            return fn()
        if not retries:
            with tracker.step(run_id, name, label):
                return fn()
        # С повторами: один шаг в аналитике, внутри — до 3 попыток
        with tracker.step(run_id, name, label):
            return _retry_loop(fn)

    article_path = None
    article_dir = None
    row_index = None

    try:
        # ─── Генерация (3 попытки) ───
        def do_generate():
            gen = ArticleGenerator()
            res = gen.run()
            if not res:
                raise RuntimeError("Нет тем в таблице для генерации")
            return res

        try:
            article_path, row_index = step(
                "generate_article", "Генерация статьи",
                lambda: do_generate(),
                retries=True,
            )
        except Exception as e:
            LOG.error("Генерация не удалась после 3 попыток: %s. Пропуск слота.", e)
            if use_tracker:
                tracker.finish_run(run_id)
            return

        article_dir = article_path.parent
        data = json.loads(article_path.read_text(encoding="utf-8"))
        if use_tracker:
            tracker.update_run_topic(run_id, data.get("title", ""))
            tracker.update_run_headline(run_id, data.get("title", ""))
            tracker.update_run_publish_dir(run_id, str(article_dir))

        # ─── Telegram (3 попытки) ───
        telegram_ok = False
        try:
            def do_telegram():
                import os
                from blocks.lifehacks_to_spambot.run import post_article_to_telegram_sync
                ok = post_article_to_telegram_sync(article_dir, project_id=os.getenv("PROJECT_ID"))
                if not ok:
                    raise RuntimeError("Публикация в Telegram не удалась")
            step("publish_telegram", "Публикация в Telegram", do_telegram, retries=True)
            telegram_ok = True
        except Exception as e:
            LOG.error("Публикация в Telegram не удалась после 3 попыток: %s", e)

        # ─── Дзен (3 попытки) ───
        zen_ok = False
        try:
            def do_zen():
                data = json.loads(article_path.read_text(encoding="utf-8"))
                code, msg, _ = asyncio.run(
                    run_post_flow(
                        data,
                        publish=data.get("publish", True),
                        headless=config.HEADLESS,
                        keep_open=config.KEEP_BROWSER_OPEN,
                        article_path=article_path,
                    )
                )
                if code != 0:
                    raise RuntimeError(msg or "Публикация в Дзен не удалась")
            step("publish_zen", "Публикация в Дзен", do_zen, retries=True)
            zen_ok = True
        except Exception as e:
            LOG.error("Публикация в Дзен не удалась после 3 попыток: %s. Пропуск публикации.", e)
            # Тему всё равно помечаем как использованную (удаляем из таблицы), чтобы не дублировать
            try:
                gen = ArticleGenerator()
                gen.delete_topic(row_index)
                LOG.info("Тема удалена из таблицы (строка %d), следующая публикация — новая тема.", row_index)
            except Exception as del_e:
                LOG.warning("Не удалось удалить тему из таблицы: %s", del_e)

        if use_tracker:
            if zen_ok or telegram_ok:
                channels = []
                if zen_ok:
                    channels.append("zen")
                if telegram_ok:
                    channels.append("telegram")
                tracker.update_run_channel(run_id, ",".join(channels))
            tracker.finish_run(run_id)

        if zen_ok and telegram_ok:
            try:
                gen = ArticleGenerator()
                gen.delete_topic(row_index)
                LOG.info("Опубликовано во всех каналах. Тема удалена из таблицы (строка %d).", row_index)
            except Exception as e:
                LOG.warning("Не удалось удалить тему из таблицы: %s", e)

    except Exception:
        if use_tracker:
            tracker.finish_run(run_id)
        raise


def run_scheduler_loop() -> None:
    """Бесконечный цикл: ожидание следующего слота → один запуск → повтор."""
    LOG.info("Планировщик запущен. 5 слотов в день: 10:00–10:30, 11:30–12:00, 13:00–13:30, 14:00–14:30, 15:20–16:40")
    while True:
        try:
            next_slot = _get_next_slot()
            _sleep_until(next_slot)
            LOG.info("Запуск слота в %s", next_slot.strftime("%Y-%m-%d %H:%M"))
            _run_one_slot()
        except KeyboardInterrupt:
            LOG.info("Планировщик остановлен по Ctrl+C")
            break
        except Exception as e:
            LOG.exception("Ошибка в планировщике: %s. Продолжаем цикл.", e)
