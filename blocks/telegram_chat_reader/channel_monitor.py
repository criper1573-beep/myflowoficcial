# -*- coding: utf-8 -*-
"""
Мониторинг канала/чата через Telethon: ловит новые сообщения,
проверяет по заголовку (или через GRS AI) и при совпадении
отправляет уведомление ботом в другой чат.

Запуск: python -m blocks.telegram_chat_reader monitor

Требуется в .env:
  TELEGRAM_API_ID, TELEGRAM_API_HASH — Telethon
  TELEGRAM_BOT_TOKEN — бот для отправки уведомлений
  TELEGRAM_MONITOR_ALERT_CHAT_ID — куда слать (или TELEGRAM_ALERT_CHAT_ID)
  TELEGRAM_MONITOR_HEADER — заголовок, по которому отбирать (если есть в сообщении — подходит)
  (опционально GRS_AI_API_KEY + TELEGRAM_MONITOR_CATEGORY_PROMPT — если заголовок не задан)
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from telethon import TelegramClient, events
from telethon.tl.types import Message

from blocks.telegram_chat_reader.client import get_client

logger = logging.getLogger(__name__)

# Конфиг из .env
ENTITY = (os.getenv("TELEGRAM_MONITOR_ENTITY") or "zakazyff").strip().lower()
ENTITY = ENTITY.lstrip("@").replace("https://t.me/", "").strip("/")
ALERT_CHAT_ID = os.getenv("TELEGRAM_MONITOR_ALERT_CHAT_ID") or os.getenv("TELEGRAM_ALERT_CHAT_ID")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Проверка по заголовку (простой режим — без AI)
HEADER = (os.getenv("TELEGRAM_MONITOR_HEADER") or "").strip()
# Опционально: AI для анализа (если заголовок не задан)
CATEGORY_PROMPT = os.getenv("TELEGRAM_MONITOR_CATEGORY_PROMPT", "")
MATCH_WORDS = (os.getenv("TELEGRAM_MONITOR_MATCH_RESPONSE") or "ДА").strip().upper()
MODEL = os.getenv("TELEGRAM_MONITOR_MODEL") or "gpt-4o-mini"


def _send_via_bot(text: str) -> bool:
    """Отправить сообщение через Bot API в чат алертов."""
    if not BOT_TOKEN or not ALERT_CHAT_ID:
        logger.warning("TELEGRAM_BOT_TOKEN или TELEGRAM_MONITOR_ALERT_CHAT_ID не заданы — уведомление не отправлено")
        return False
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        # Экранируем длинные сообщения (лимит 4096)
        text = text[:4000] + "…" if len(text) > 4000 else text
        data = urllib.parse.urlencode({
            "chat_id": ALERT_CHAT_ID,
            "text": text,
            "disable_web_page_preview": "true",
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        logger.exception("Ошибка отправки в Telegram: %s", e)
        return False


def _message_matches(text: str) -> bool:
    """Проверить: подходит ли сообщение. По заголовку (если задан) или через GRS AI."""
    if not text or not text.strip():
        return False
    # Режим по заголовку — без AI
    if HEADER:
        return HEADER.lower() in text.lower()
    # Режим через AI (если CATEGORY_PROMPT задан)
    if not CATEGORY_PROMPT:
        logger.warning("Задайте TELEGRAM_MONITOR_HEADER или TELEGRAM_MONITOR_CATEGORY_PROMPT")
        return False
    try:
        from blocks.ai_integrations.grs_ai_client import GRSAIClient
        client = GRSAIClient()
        answer = client.simple_ask(
            question=f"Сообщение для проверки:\n\n{text[:2000]}",
            system_prompt=CATEGORY_PROMPT,
            model=MODEL,
        )
        answer = (answer or "").strip().upper()
        return MATCH_WORDS in answer or "ДА" in answer or "YES" in answer
    except Exception as e:
        logger.exception("Ошибка GRS AI: %s", e)
        return False


async def _on_new_message(event: events.NewMessage.Event):
    msg = event.message
    if not isinstance(msg, Message):
        return
    text = (msg.text or "").strip()
    if not text:
        return  # пропускаем пустые и только медиа

    logger.debug("Новое сообщение [%s]: %s", msg.id, text[:80])
    if not _message_matches(text):
        return

    # Подходит — отправляем уведомление
    date_str = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
    alert_text = (
        f"📬 <b>Канал {ENTITY}</b>\n"
        f"<i>{date_str}</i>\n\n"
        f"{text}"
    )
    if _send_via_bot(alert_text):
        logger.info("Уведомление отправлено: msg_id=%s", msg.id)
    else:
        logger.warning("Не удалось отправить уведомление для msg_id=%s", msg.id)


async def run_monitor():
    if not ALERT_CHAT_ID or not BOT_TOKEN:
        raise ValueError(
            "Задайте TELEGRAM_BOT_TOKEN и TELEGRAM_MONITOR_ALERT_CHAT_ID (или TELEGRAM_ALERT_CHAT_ID) в .env"
        )

    client = get_client(session_name="chat_reader")
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError("Не авторизован. Выполните: python -m blocks.telegram_chat_reader login")

    chat_entity = await client.get_entity(ENTITY)
    logger.info("Мониторинг канала %s, уведомления в %s", ENTITY, ALERT_CHAT_ID)
    client.add_event_handler(_on_new_message, events.NewMessage(chats=[chat_entity]))
    await client.run_until_disconnected()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        asyncio.run(run_monitor())
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    except (ValueError, RuntimeError) as e:
        logger.error("%s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
