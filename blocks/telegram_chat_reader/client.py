# -*- coding: utf-8 -*-
"""
Клиент Telethon для чтения истории сообщений из чатов/каналов Telegram.
Требует API_ID и API_HASH с my.telegram.org и авторизацию по номеру телефона.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    FloodWaitError,
    InviteHashExpiredError,
)
from telethon.tl.types import Message

logger = logging.getLogger(__name__)

# Папка для сессии (не коммитить)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_DIR = PROJECT_ROOT / "storage" / "telegram_sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)


def get_client(session_name: str = "chat_reader") -> TelegramClient:
    """Создать клиент Telethon. API_ID и API_HASH — из .env или my.telegram.org."""
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise ValueError(
            "Задайте TELEGRAM_API_ID и TELEGRAM_API_HASH в .env. "
            "Получить: https://my.telegram.org/apps"
        )
    session_path = SESSION_DIR / session_name
    return TelegramClient(
        str(session_path),
        int(api_id),
        api_hash.strip(),
    )


def _message_to_dict(msg: Message) -> dict[str, Any]:
    """Преобразовать сообщение в словарь для JSON."""
    data = {
        "id": msg.id,
        "date": msg.date.isoformat() if msg.date else None,
        "text": msg.text or "",
        "sender_id": getattr(msg.sender_id, "user_id", None) or str(msg.sender_id) if msg.sender_id else None,
        "reply_to_msg_id": msg.reply_to_msg_id,
        "views": getattr(msg, "views", None),
        "forwards": getattr(msg, "forwards", None),
    }
    if msg.media:
        data["media_type"] = type(msg.media).__name__
        data["has_media"] = True
    else:
        data["has_media"] = False
    return data


async def fetch_chat_history(
    entity: str,
    limit: int = 100,
    offset_id: int | None = None,
    min_id: int | None = None,
) -> tuple[list[dict], str | None]:
    """
    Получить историю сообщений из чата/канала.

    Args:
        entity: username (zakazyff), @username, или invite link
        limit: макс. кол-во сообщений (до 100 за запрос)
        offset_id: ID сообщения, после которого грузить (для пагинации)
        min_id: грузить только сообщения с id > min_id

    Returns:
        (список сообщений, ошибка или None)
    """
    client = get_client()
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        return [], "Не авторизован. Запустите: python -m blocks.telegram_chat_reader --login"

    messages: list[dict] = []
    error: str | None = None
    try:
        async for msg in client.iter_messages(
            entity,
            limit=limit,
            offset_id=offset_id,
            min_id=min_id,
            reverse=False,  # от старых к новым при reverse=True
        ):
            if isinstance(msg, Message):
                messages.append(_message_to_dict(msg))
    except ChannelPrivateError:
        error = "Канал/чат приватный или вы не участник. Присоединитесь к чату через t.me/..."
    except InviteHashExpiredError:
        error = "Ссылка-приглашение истекла"
    except FloodWaitError as e:
        error = f"Telegram rate limit: подождите {e.seconds} сек"
    except Exception as e:
        logger.exception("Ошибка получения сообщений")
        error = str(e)
    finally:
        await client.disconnect()

    return messages, error


async def login_interactive() -> bool:
    """Интерактивная авторизация по номеру телефона и коду."""
    client = get_client()
    await client.connect()
    if await client.is_user_authorized():
        print("Уже авторизован.")
        await client.disconnect()
        return True
    await client.start(
        phone=lambda: input("Введите номер телефона (с кодом страны): "),
        code_callback=lambda: input("Введите код из Telegram: "),
        password=lambda: input("Введите 2FA пароль (если включён): "),
    )
    await client.disconnect()
    print("Авторизация успешна. Сессия сохранена.")
    return True


def run_fetch(entity: str, limit: int = 100, output: str | None = None) -> list[dict]:
    """Синхронная обёртка: получить историю и опционально сохранить в JSON."""
    messages, error = asyncio.run(fetch_chat_history(entity, limit=limit))
    if error:
        raise RuntimeError(error)
    if output:
        out_path = Path(output)
        if not out_path.is_absolute():
            out_path = PROJECT_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {"entity": entity, "count": len(messages), "messages": messages},
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"Сохранил {len(messages)} сообщений в {out_path}")
    return messages
