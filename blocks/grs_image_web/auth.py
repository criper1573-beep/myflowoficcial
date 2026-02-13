# -*- coding: utf-8 -*-
"""Верификация Telegram Login Widget и сессии по cookie."""
import hashlib
import hmac
import json
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)

# Папка для хранения сессий (telegram_id -> актуальность) при желании можно заменить на Redis
SESSION_SECRET = os.getenv("GRS_IMAGE_WEB_SESSION_SECRET") or os.getenv("TELEGRAM_BOT_TOKEN") or "dev-secret-change-in-production"
BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()


def verify_telegram_login(data: dict) -> dict | None:
    """
    Проверка данных от Telegram Login Widget.
    data: dict с полями id, first_name, last_name, username, photo_url, auth_date, hash.
    Возвращает данные пользователя (id, first_name, username и т.д.) или None при неверном hash.
    """
    if not BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не задан, авторизация через Telegram недоступна")
        return None
    received_hash = (data.get("hash") or "").strip()
    if not received_hash:
        return None
    # data-check-string: все полученные поля кроме hash, алфавитный порядок; пустые не включаем (как у Telegram)
    data_check_parts = []
    for key in sorted(data.keys()):
        if key == "hash":
            continue
        val = data[key]
        if val is None or (isinstance(val, str) and val == ""):
            continue
        data_check_parts.append(f"{key}={val}")
    data_check_string = "\n".join(data_check_parts)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        return None
    # Опционально: проверка auth_date (не старше 24 ч)
    try:
        auth_date = int(data.get("auth_date", 0))
        if auth_date and auth_date < (__import__("time").time() - 86400):
            logger.warning("Telegram auth_date устарел")
            return None
    except (ValueError, TypeError):
        pass
    return {
        "id": data.get("id"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "username": data.get("username"),
        "photo_url": data.get("photo_url"),
    }


def make_session_token(telegram_id: int) -> str:
    """Создать подписанный токен сессии (telegram_id + подпись)."""
    payload = f"{telegram_id}"
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{telegram_id}.{sig}"


def verify_session_token(token: str) -> int | None:
    """Проверить токен и вернуть telegram_id или None."""
    if not token or "." not in token:
        return None
    part, sig = token.rsplit(".", 1)
    try:
        telegram_id = int(part)
    except ValueError:
        return None
    expected = hmac.new(SESSION_SECRET.encode(), part.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(sig, expected):
        return None
    return telegram_id


def get_generated_dir(block_dir: Path, telegram_id: int) -> Path:
    """Папка для сгенерированных изображений пользователя."""
    d = block_dir / "generated" / str(telegram_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_uploaded_dir(block_dir: Path, telegram_id: int) -> Path:
    """Папка для загруженных фото (прямые ссылки)."""
    d = block_dir / "uploaded" / str(telegram_id)
    d.mkdir(parents=True, exist_ok=True)
    return d
