# -*- coding: utf-8 -*-
"""
CLI автопостинга в Дзен: --file, --auto, --publish, --headless, --keep-open.
Следует UNIVERSAL_AUTOPOST_PROMPT; логи в консоль и в autopost_debug.log.

Запуск:
  python -m blocks.autopost_zen --file articles/article.json [--publish]
  python -m blocks.autopost_zen --auto --publish   # генерация из Google Sheets + публикация
  python -m blocks.autopost_zen --schedule        # оркестратор контент завода: пробный запуск при старте + 5 слотов в день
"""
import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from . import config
from .zen_client import run_post_flow, prepare_publication, PUBLISH_DIR

LOG = logging.getLogger("autopost_zen")


def setup_logging(log_file: Path | None = None) -> None:
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=fmt,
        handlers=[logging.StreamHandler()],
    )
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(fmt))
        logging.getLogger().addHandler(fh)


def _run_auto(args) -> int:
    """Режим --auto: тема из Google Sheets → генерация → публикация. Каждый шаг — чекпоинт в RunTracker (если доступен)."""
    from .article_generator import ArticleGenerator, PUBLISH_DIR, _get_next_publish_number

    try:
        from blocks.analytics.tracker import RunTracker
        tracker = RunTracker()
        run_id = tracker.start_run(source="google_sheets")
        use_tracker = True
    except Exception as e:
        LOG.warning("Аналитика недоступна, запуск без трекера: %s", e)
        tracker = run_id = None
        use_tracker = False

    LOG.info("=" * 50)
    LOG.info("РЕЖИМ AUTO: генерация статьи из Google Sheets")
    LOG.info("=" * 50)

    generator = ArticleGenerator()
    exit_code = 2

    def step(name, label, fn):
        if use_tracker:
            with tracker.step(run_id, name, label):
                return fn()
        return fn()

    try:
        topic, extra, row_index = step("fetch_topic", "Получение темы из таблицы", lambda: generator.fetch_topic())
        if not topic:
            LOG.error("Нет тем в таблице для генерации")
            print("Нет тем в таблице для генерации")
            return 3
        if extra:
            topic = f"{topic}. {extra}"
        if use_tracker:
            tracker.update_run_topic(run_id, topic)

        headline = step("generate_headline", "Генерация заголовка", lambda: generator.generate_headline(topic))
        if use_tracker:
            tracker.update_run_headline(run_id, headline)

        article_html = step("generate_article", "Генерация текста статьи", lambda: generator.generate_article(headline, topic))

        def do_build():
            num = _get_next_publish_number()
            article_dir = PUBLISH_DIR / f"{num:03d}"
            article_dir.mkdir(parents=True, exist_ok=True)
            return generator.build_article(headline, topic, article_html, article_dir), article_dir
        article_data, article_dir = step("build_article", "Генерация обложки и картинок, сборка статьи", do_build)
        if use_tracker:
            tracker.update_run_publish_dir(run_id, str(article_dir))

        article_path = step("save_article", "Сохранение статьи", lambda: generator.save_article(article_data, article_dir))
        LOG.info("Статья сгенерирована: %s", article_path)

        if args.generate_only:
            print(f"Статья сгенерирована: {article_path}")
            return 0

        # Публикация по каналам: ошибка в одном не останавливает остальные
        telegram_ok = False
        try:
            def do_telegram():
                import os
                from blocks.lifehacks_to_spambot.run import post_article_to_telegram_sync
                ok, err_msg = post_article_to_telegram_sync(article_dir, project_id=os.getenv("PROJECT_ID"))
                if not ok:
                    raise RuntimeError("Публикация в Telegram не удалась" + (f": {err_msg}" if err_msg else ""))
            step("publish_telegram", "Публикация в Telegram", do_telegram)
            telegram_ok = True
        except Exception as e:
            LOG.error("Публикация в Telegram не удалась: %s. Продолжаем в другие каналы.", e)

        zen_ok = False
        try:
            def do_publish():
                data = json.loads(article_path.read_text(encoding="utf-8"))
                publish = args.publish if args.publish else data.get("publish", True)
                code, msg, _ = asyncio.run(
                    run_post_flow(
                        data,
                        publish=publish,
                        headless=args.headless or config.HEADLESS,
                        keep_open=args.keep_open or config.KEEP_BROWSER_OPEN,
                        article_path=article_path,
                    )
                )
                if code != 0:
                    raise RuntimeError(msg or "Публикация не удалась")
            step("publish_zen", "Публикация в Дзен", do_publish)
            zen_ok = True
        except Exception as e:
            LOG.error("Публикация в Дзен не удалась: %s", e)

        # Каналы для аналитики: по каким каналам реально опубликовали
        if use_tracker:
            channels = []
            if zen_ok:
                channels.append("zen")
            if telegram_ok:
                channels.append("telegram")
            if channels:
                tracker.update_run_channel(run_id, ",".join(channels))

        # Удаление темы из таблицы только после успешной публикации во всех каналах
        if telegram_ok and zen_ok:
            step("delete_topic", "Удаление темы из таблицы", lambda: generator.delete_topic(row_index))
            LOG.info("Тема удалена из таблицы (строка %d)", row_index)
            print("Опубликовано во всех каналах. Тема удалена из таблицы.")
            exit_code = 0
        else:
            if not telegram_ok and not zen_ok:
                LOG.error("Ошибки во всех каналах. Тема не удалена из таблицы.")
            else:
                LOG.warning("Один из каналов завершился с ошибкой. Тема не удалена из таблицы.")
            exit_code = 1
    except Exception:
        raise
    finally:
        if use_tracker:
            tracker.finish_run(run_id)

    return exit_code


def _run_file(args) -> int:
    """Режим --file: публикация готовой статьи из JSON."""
    if not args.file:
        LOG.error("Нужен --file или --auto")
        return 3

    # Резолвим путь: абсолютный → как есть; относительный → от PROJECT_ROOT
    raw = Path(args.file)
    if raw.is_absolute():
        article_path = raw
    else:
        article_path = (config.PROJECT_ROOT / raw).resolve()
        if not article_path.exists():
            alt = (config.BLOCK_DIR / raw).resolve()
            if alt.exists():
                article_path = alt
    if not article_path.exists():
        LOG.error("Файл не найден: %s", article_path)
        return 3

    # По умолчанию публикуем один раз из указанного пути (без переноса в publish/N)
    if args.prepare_only:
        try:
            article_path = prepare_publication(article_path)
            print("Готово: статья подготовлена к публикации →", article_path)
        except Exception as e:
            LOG.error("Ошибка подготовки: %s", e)
            return 3
        return 0

    try:
        data = json.loads(article_path.read_text(encoding="utf-8"))
    except Exception as e:
        LOG.error("Ошибка чтения JSON: %s", e)
        return 3

    # Трекер: записываем запуск в аналитику (дашборд), чтобы публикации по --file тоже отображались
    try:
        from blocks.analytics.tracker import RunTracker
        tracker = RunTracker()
        headline = data.get("title") or "Статья из файла"
        run_id = tracker.start_run(
            topic=headline,
            headline=headline,
            source="file",
            publish_dir=str(article_path.parent),
        )
        use_tracker = True
    except Exception as e:
        LOG.debug("Аналитика недоступна, публикация без трекера: %s", e)
        tracker = run_id = None
        use_tracker = False

    publish = args.publish if args.publish else data.get("publish", True)

    def do_publish():
        return asyncio.run(
            run_post_flow(
                data,
                publish=publish,
                headless=args.headless or config.HEADLESS,
                keep_open=args.keep_open or config.KEEP_BROWSER_OPEN,
                article_path=article_path,
            )
        )

    if use_tracker:
        with tracker.step(run_id, "publish_zen", "Публикация в Дзен"):
            exit_code, msg, _ = do_publish()
            if exit_code != 0:
                raise RuntimeError(msg or "Публикация не удалась")
        tracker.update_run_channel(run_id, "zen")
        tracker.finish_run(run_id)
    else:
        exit_code, msg, _ = do_publish()

    LOG.info("%s", msg)
    if exit_code == 0:
        print(msg)
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Автопостинг статьи в Яндекс.Дзен")
    parser.add_argument("--file", "-f", help="Путь к JSON статьи")
    parser.add_argument("--auto", "-a", action="store_true",
                        help="Авто-режим: тема из Google Sheets → генерация → публикация")
    parser.add_argument("--generate-only", action="store_true",
                        help="Только сгенерировать статью (без публикации), работает с --auto")
    parser.add_argument("--publish", "-p", action="store_true", help="Опубликовать")
    parser.add_argument("--prepare-only", action="store_true",
                        help="Только подготовить: перенести статью в publish/N/")
    parser.add_argument("--headless", action="store_true", help="Запуск браузера без окна")
    parser.add_argument("--keep-open", action="store_true", help="Не закрывать браузер")
    parser.add_argument("--schedule", "-s", action="store_true",
                        help="Оркестратор контент завода: пробный запуск при старте, затем 5 слотов в день по расписанию")
    args = parser.parse_args()

    log_file = config.BLOCK_DIR / "autopost_debug.log"
    setup_logging(log_file)

    if args.schedule:
        from .scheduler import run_scheduler_loop
        run_scheduler_loop()
        return 0

    if args.auto:
        return _run_auto(args)

    if args.file:
        return _run_file(args)

    LOG.error("Нужен --file или --auto")
    parser.print_help()
    return 3


if __name__ == "__main__":
    sys.exit(main())
