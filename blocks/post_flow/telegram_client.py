# -*- coding: utf-8 -*-
"""Публикация поста в Telegram-канал."""
import io
import requests

from blocks.post_flow import config as config_module

config = config_module


def publish_post(image_bytes: bytes, caption: str) -> bool:
    """
    Публикует пост в канал: фото + подпись.
    caption = заголовок + текст (можно объединить через \\n\\n).
    Возвращает True при успехе.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env")
    channel = config.TELEGRAM_CHANNEL.strip()
    if not channel.startswith("@"):
        channel = "@" + channel
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
    if len(caption) > 1024:
        raise ValueError(f"Caption too long ({len(caption)} chars). Build caption must stay under 1024.")
    files = {"photo": ("image.png", io.BytesIO(image_bytes), "image/png")}
    data = {"chat_id": channel, "caption": caption, "parse_mode": "HTML"}
    resp = requests.post(url, files=files, data=data, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Telegram API error: {resp.status_code} {resp.text}")
    return True
