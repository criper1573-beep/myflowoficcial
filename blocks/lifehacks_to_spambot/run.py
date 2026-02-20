# -*- coding: utf-8 -*-
"""
Скрипт «Лайфхаки в спам-бот»: обложка + краткое саммари статьи (из процесса генерации) → Telegram.

Саммари берётся из поля telegram_summary в article.json (генерируется при сборке статьи).
Можно вызывать вручную или из пайплайна autopost_zen после генерации.

Запуск:
  python -m blocks.lifehacks_to_spambot blocks/autopost_zen/publish/006
  python -m blocks.lifehacks_to_spambot blocks/autopost_zen/publish/006/article.json --project flowcabinet
  python -m blocks.lifehacks_to_spambot  (последняя папка в publish/)
"""
import argparse
import asyncio
import html
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Лимит подписи Telegram
MAX_CAPTION_LENGTH = 1024


def load_article(path: Path) -> Tuple[dict, Path]:
    """
    Загружает article.json. path — путь к файлу или к папке (ищем article.json внутри).
    Возвращает (data, article_dir).
    """
    if path.is_file():
        article_dir = path.parent
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), article_dir
    article_json = path / "article.json"
    if article_json.is_file():
        with open(article_json, "r", encoding="utf-8") as f:
            return json.load(f), path
    raise FileNotFoundError(f"Не найден article.json: {path} или {article_json}")


def build_caption(title: str, summary: str, max_len: int = MAX_CAPTION_LENGTH) -> str:
    """
    Собирает подпись для поста: заголовок + саммари + ссылки (Telegram-канал и сайт).
    Для Telegram используем HTML; обрезаем по max_len.
    """
    summary = (summary or "").strip()
    parts = [f"<b>{html.escape(title)}</b>"]
    if summary:
        parts.append(html.escape(summary))
    # Ссылки на канал и сайт
    parts.append('<a href="https://t.me/myflowofficial">Подписаться на канал</a> | <a href="https://flowcabinet.ru">flowcabinet.ru</a>')
    text = "\n\n".join(parts)
    if len(text) > max_len:
        # Обрезаем саммари, но сохраняем заголовок и ссылки
        footer = '\n\n<a href="https://t.me/myflowofficial">Подписаться на канал</a> | <a href="https://flowcabinet.ru">flowcabinet.ru</a>'
        header = f"<b>{html.escape(title)}</b>"
        available = max_len - len(header) - len(footer) - 6  # 6 для \n\n x2 + "..."
        if available > 50 and summary:
            text = header + "\n\n" + html.escape(summary)[:available].rstrip() + "..." + footer
        else:
            text = header + footer
    return text


def get_cover_path(article_data: dict, article_dir: Path) -> Optional[Path]:
    """Возвращает путь к файлу обложки или None."""
    cover = article_data.get("cover_image") or article_data.get("cover_image_url")
    if not cover or cover.startswith("http"):
        return None
    # Путь может быть относительным к статье или от корня
    for base in (article_dir, PROJECT_ROOT, BLOCK_DIR.parent / "autopost_zen" / "articles"):
        p = (base / cover).resolve()
        if p.is_file():
            return p
    p = (article_dir / cover).resolve()
    return p if p.is_file() else None


async def send_lifehack_post(
    bot_token: str,
    channel_id: str,
    photo_path: Path,
    caption: str,
) -> bool:
    """Отправляет пост с фото и подписью в канал (увеличенный таймаут для больших обложек)."""
    from telegram import Bot
    from telegram.constants import ParseMode
    from telegram.request import HTTPXRequest

    # Таймаут 120 с для загрузки крупных фото (обложка может быть 1–2 MB)
    request = HTTPXRequest(read_timeout=120, write_timeout=120)
    bot = Bot(token=bot_token, request=request)
    with open(photo_path, "rb") as f:
        await bot.send_photo(
            chat_id=channel_id,
            photo=f,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    return True


async def send_lifehack_post_text_only(
    bot_token: str,
    channel_id: str,
    text: str,
) -> bool:
    """Отправляет пост только текстом (без фото). Используется при TELEGRAM_ALLOW_NO_COVER и отсутствии обложки."""
    from telegram import Bot
    from telegram.constants import ParseMode
    from telegram.request import HTTPXRequest

    request = HTTPXRequest(read_timeout=60, write_timeout=60)
    bot = Bot(token=bot_token, request=request)
    await bot.send_message(
        chat_id=channel_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )
    return True


def post_article_to_telegram_sync(
    article_dir: Path, project_id: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Публикует обложку и саммари статьи в Telegram. Вызывается из пайплайна autopost_zen.
    Использует telegram_summary из article.json (генерируется при сборке статьи).
    Возвращает (True, None) при успехе, (False, "причина ошибки") при ошибке.
    """
    try:
        article_data, _ = load_article(article_dir)
    except FileNotFoundError:
        logger.exception("article.json не найден в %s", article_dir)
        return False, f"article.json не найден в {article_dir}"
    title = article_data.get("title") or "Статья"
    summary = article_data.get("telegram_summary") or article_data.get("meta_description") or ""
    caption = build_caption(title, summary)
    cover_path = get_cover_path(article_data, article_dir)
    bot_token, channel_id = get_telegram_config(project_id or os.getenv("PROJECT_ID"))
    if not bot_token or not channel_id:
        logger.error("Не заданы TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID или проект")
        return False, "Не заданы TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID или проект"
    if not cover_path:
        allow_no_cover = os.getenv("TELEGRAM_ALLOW_NO_COVER", "").strip().lower() in ("1", "true", "yes")
        if allow_no_cover:
            try:
                asyncio.run(send_lifehack_post_text_only(bot_token, channel_id, caption))
                logger.info("Пост в Telegram отправлен без фото (TELEGRAM_ALLOW_NO_COVER): %s", title[:50])
                return True, None
            except Exception as e:
                logger.exception("Ошибка отправки в Telegram (текст без фото): %s", e)
                return False, str(e)
        logger.error("Обложка не найдена в %s", article_dir)
        return False, f"Обложка не найдена в {article_dir}"
    try:
        asyncio.run(send_lifehack_post(bot_token, channel_id, cover_path, caption))
        logger.info("Пост в Telegram отправлен: %s", title[:50])
        return True, None
    except Exception as e:
        logger.exception("Ошибка отправки в Telegram: %s", e)
        return False, str(e)


def get_telegram_config(project_id: Optional[str]) -> Tuple[str, str]:
    """Берёт bot_token и channel_id из проекта или .env."""
    if project_id:
        try:
            from blocks.projects import get_telegram_config as get_tg
            tg = get_tg(project_id)
            token = tg.get("bot_token") or ""
            channel = tg.get("channel_id") or ""
            if token and channel:
                return token, channel
        except Exception as e:
            logger.warning("Проект не загружен %s: %s", project_id, e)
    token = os.getenv("TELEGRAM_BOT_TOKEN") or ""
    channel = os.getenv("TELEGRAM_CHANNEL_ID") or ""
    return token, channel


def find_latest_publish_dir() -> Optional[Path]:
    """Последняя по номеру папка в blocks/autopost_zen/publish/."""
    publish = PROJECT_ROOT / "blocks" / "autopost_zen" / "publish"
    if not publish.is_dir():
        return None
    dirs = [d for d in publish.iterdir() if d.is_dir() and d.name.isdigit()]
    if not dirs:
        return None
    return max(dirs, key=lambda d: int(d.name))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Публикация обложки и краткого саммари статьи в Telegram-канал (саммари из процесса генерации).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Путь к папке статьи (publish/NNN) или к article.json. Если не указан — последняя папка в publish/.",
    )
    parser.add_argument("--project", "-p", help="ID проекта (blocks/projects/data/<id>.yaml) для Telegram.")
    parser.add_argument("--dry-run", action="store_true", help="Не отправлять, только показать что будет отправлено.")
    args = parser.parse_args()

    if args.path:
        path = Path(args.path)
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
    else:
        path = find_latest_publish_dir()
        if not path:
            logger.error("Не указан path и не найдена папка в blocks/autopost_zen/publish/")
            return 1

    try:
        article_data, article_dir = load_article(path)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1

    title = article_data.get("title") or "Статья"
    summary = article_data.get("telegram_summary") or article_data.get("meta_description") or ""

    caption = build_caption(title, summary)
    cover_path = get_cover_path(article_data, article_dir)

    if not cover_path:
        logger.error("Обложка не найдена (cover_image: %s)", article_data.get("cover_image"))
        return 1

    logger.info("Заголовок: %s", title[:60])
    logger.info("Обложка: %s", cover_path)
    logger.info("Длина подписи: %s символов", len(caption))

    if args.dry_run:
        logger.info("--dry-run: пост не отправлен.")
        return 0

    bot_token, channel_id = get_telegram_config(args.project or os.getenv("PROJECT_ID"))
    if not bot_token or not channel_id:
        logger.error("Задайте TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID или --project <id>")
        return 1

    try:
        asyncio.run(send_lifehack_post(bot_token, channel_id, cover_path, caption))
        logger.info("Пост отправлен в %s", channel_id)
        return 0
    except Exception as e:
        logger.exception("Ошибка отправки: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
