# -*- coding: utf-8 -*-
"""
Оркестратор контент завода: регулярные публикации (Дзен, Telegram) — 5 слотов в день.
Запуск: python -m blocks.autopost_zen --schedule

При старте выполняется один пробный запуск цепочки, затем работа по расписанию.

Окна (локальное время):
  1) 10:00–10:30
  2) 11:30–12:00
  3) 13:00–13:30
  4) 14:00–14:30
  5) 15:20–16:40

В каждом окне — одна публикация в случайное время. При ошибке генерации или
публикации — 3 попытки (сразу, через 1 мин, через 3 мин), затем пропуск
слота с записью ошибки в дашборд аналитики.
"""
import asyncio
import json
import logging
import random
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from . import config

ORCHESTRATOR_KZ_STATE_FILE = config.PROJECT_ROOT / "storage" / "orchestrator_kz_state.json"
ORCHESTRATOR_LOCK_FILE = config.PROJECT_ROOT / "storage" / "orchestrator_kz.lock"
FAILED_PUBLICATIONS_FILE = config.PROJECT_ROOT / "storage" / "failed_publications.jsonl"
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
# Не делать повторный пробный запуск при старте, если уже был запуск недавно (защита от лишних генераций при рестартах/деплоях)
MIN_INTERVAL_BETWEEN_STARTUP_RUNS_SEC = 7200  # 2 часа


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


def _read_schedule_state() -> dict:
    """Прочитать состояние оркестратора (last_run_at, next_run_at в ISO)."""
    if not ORCHESTRATOR_KZ_STATE_FILE.exists():
        return {}
    try:
        data = json.loads(ORCHESTRATOR_KZ_STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_schedule_state(*, next_run_at: datetime | None = None, last_run_at: datetime | None = None) -> None:
    """Обновить состояние оркестратора (для дашборда)."""
    state = _read_schedule_state()
    if next_run_at is not None:
        state["next_run_at"] = next_run_at.isoformat()
    if last_run_at is not None:
        state["last_run_at"] = last_run_at.isoformat()
    ORCHESTRATOR_KZ_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ORCHESTRATOR_KZ_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def _append_failed_publication(
    *,
    article_path: Path,
    article_data: dict,
    failed_channels: list[str],
    succeeded_channels: list[str],
    run_id: Optional[str] = None,
) -> None:
    """
    Добавляет запись в storage/failed_publications.jsonl для последующей ручной публикации
    в каналы, где публикация не прошла. В записи — все ссылки на статью, заголовок, пути.
    """
    try:
        article_dir = article_path.parent
        rel_dir = article_dir
        try:
            rel_dir = article_dir.relative_to(config.PROJECT_ROOT)
        except ValueError:
            pass
        record = {
            "timestamp": datetime.now().isoformat(),
            "title": article_data.get("title") or "",
            "meta_description": article_data.get("meta_description") or "",
            "article_dir": str(article_dir),
            "article_dir_relative": str(rel_dir),
            "article_json": str(article_path),
            "cover_image": article_data.get("cover_image") or "",
            "cover_path": str(article_dir / (article_data.get("cover_image") or "")),
            "failed_channels": failed_channels,
            "succeeded_channels": succeeded_channels,
            "run_id": run_id,
        }
        FAILED_PUBLICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FAILED_PUBLICATIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        LOG.info(
            "Запись о неудачной публикации добавлена в %s (не удалось: %s)",
            FAILED_PUBLICATIONS_FILE.name,
            ", ".join(failed_channels),
        )
    except Exception as e:
        LOG.warning("Не удалось записать в failed_publications.jsonl: %s", e)


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
                ok, err_msg = post_article_to_telegram_sync(article_dir, project_id=os.getenv("PROJECT_ID"))
                if not ok:
                    raise RuntimeError("Публикация в Telegram не удалась" + (f": {err_msg}" if err_msg else ""))
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

        if use_tracker:
            if zen_ok or telegram_ok:
                channels = []
                if zen_ok:
                    channels.append("zen")
                if telegram_ok:
                    channels.append("telegram")
                tracker.update_run_channel(run_id, ",".join(channels))
            tracker.finish_run(run_id)

        # Если хотя бы один канал успешен — удаляем тему из таблицы, чтобы не публиковать её снова
        if zen_ok or telegram_ok:
            try:
                gen = ArticleGenerator()
                gen.delete_topic(row_index)
                LOG.info(
                    "Тема удалена из таблицы (строка %d). Опубликовано: %s.",
                    row_index,
                    ", ".join(c for c in ("zen" if zen_ok else "", "telegram" if telegram_ok else "") if c),
                )
            except Exception as e:
                LOG.warning("Не удалось удалить тему из таблицы: %s", e)
            # Если не во всех каналах — пишем в документ для последующей ручной публикации
            if not (zen_ok and telegram_ok):
                failed = [c for c in ("telegram", "zen") if (c == "telegram" and not telegram_ok) or (c == "zen" and not zen_ok)]
                succeeded = [c for c in ("telegram", "zen") if (c == "telegram" and telegram_ok) or (c == "zen" and zen_ok)]
                _append_failed_publication(
                    article_path=article_path,
                    article_data=data,
                    failed_channels=failed,
                    succeeded_channels=succeeded,
                    run_id=str(run_id) if use_tracker and run_id else None,
                )

    except Exception as e:
        LOG.exception("Ошибка в слоте оркестратора (записана в дашборд по шагу): %s", e)
        if use_tracker:
            tracker.finish_run(run_id)
        raise


def _acquire_orchestrator_lock():
    """
    Эксклюзивная блокировка: только один процесс оркестратора может работать.
    Возвращает открытый файл (держать до конца работы) или None если lock недоступен (Windows).
    При занятом lock выходит из процесса (sys.exit(0)).
    """
    ORCHESTRATOR_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        import fcntl
        f = open(ORCHESTRATOR_LOCK_FILE, "w", encoding="utf-8")
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except BlockingIOError:
        LOG.error("Другой экземпляр оркестратора уже запущен (lock %s). Выход.", ORCHESTRATOR_LOCK_FILE)
        try:
            f.close()
        except Exception:
            pass
        sys.exit(0)
    except (ImportError, OSError) as e:
        LOG.warning("Блокировка оркестратора недоступна (не Linux?): %s. Продолжаем без lock.", e)
        return None


def run_scheduler_loop() -> None:
    """
    Бесконечный цикл оркестратора.
    ОБЯЗАТЕЛЬНО: при каждом старте сервиса сначала выполняется один полный прогон цепочки
    (генерация → Telegram → Дзен), чтобы убедиться, что всё работает. Расписание — отдельно, после прогона.
    Только один экземпляр оркестратора может работать (файловая блокировка на Linux).
    """
    _lock_file = _acquire_orchestrator_lock()  # держим ссылку, чтобы файл не закрылся и lock не снялся

    # Проверка Telegram при старте: если не заданы токены — в логах будет видно (на сервере скопировать .env с компа)
    try:
        import os
        from blocks.lifehacks_to_spambot.run import get_telegram_config
        _tg_token, _tg_channel = get_telegram_config(os.getenv("PROJECT_ID"))
        if not _tg_token or not _tg_channel:
            LOG.warning(
                "TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID (или проект в blocks/projects) не заданы. "
                "Публикация в Telegram будет падать. На сервере добавьте в .env те же переменные, что на компе (см. docs/rules/KEYS_AND_TOKENS.md)."
            )
    except Exception as e:
        LOG.warning("Проверка Telegram при старте: %s", e)

    LOG.info("Оркестратор контент завода: запущен. 5 слотов в день: 10:00–10:30, 11:30–12:00, 13:00–13:30, 14:00–14:30, 15:20–16:40")
    # ОБЯЗАТЕЛЬНЫЙ пробный запуск при старте — пропускаем, если уже был запуск за последние 2 часа (защита от лишних генераций при рестартах)
    state = _read_schedule_state()
    last_run_str = state.get("last_run_at")
    skip_startup_run = False
    if last_run_str:
        try:
            last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
            if last_run.tzinfo:
                last_run = last_run.astimezone().replace(tzinfo=None)
            elapsed = (datetime.now() - last_run).total_seconds()
            if elapsed >= 0 and elapsed < MIN_INTERVAL_BETWEEN_STARTUP_RUNS_SEC:
                skip_startup_run = True
                LOG.info(
                    "Оркестратор: пропуск пробного запуска при старте (последний запуск был %.0f мин назад).",
                    elapsed / 60,
                )
        except (ValueError, TypeError):
            pass
    if not skip_startup_run:
        LOG.info("Оркестратор: обязательный пробный запуск цепочки при старте (вне расписания)…")
        try:
            _run_one_slot()
            _write_schedule_state(last_run_at=datetime.now())
            LOG.info("Оркестратор: пробный запуск завершён успешно. Переход к работе по расписанию.")
        except Exception as e:
            LOG.exception("Ошибка при пробном запуске: %s. Продолжаем по расписанию.", e)
    next_slot = _get_next_slot()
    _write_schedule_state(next_run_at=next_slot)

    while True:
        try:
            _sleep_until(next_slot)
            LOG.info("Запуск слота в %s", next_slot.strftime("%Y-%m-%d %H:%M"))
            _run_one_slot()
            _write_schedule_state(last_run_at=datetime.now())
            # Сразу записать следующий слот, чтобы в дашборде не показывалось прошедшее время
            next_slot = _get_next_slot()
            _write_schedule_state(next_run_at=next_slot)
        except KeyboardInterrupt:
            LOG.info("Оркестратор остановлен по Ctrl+C")
            break
        except Exception as e:
            LOG.exception("Ошибка в оркестраторе: %s. Продолжаем цикл.", e)
