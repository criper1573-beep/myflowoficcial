# -*- coding: utf-8 -*-
"""
Клиент API Яндекс.Вордстат (https://api.wordstat.yandex.net).
Документация: https://yandex.ru/support2/wordstat/ru/content/api-structure

Метод /v1/topRequests — популярные запросы по фразе. POST, JSON, Bearer-токен.
Переменная: YANDEX_WORDSTAT_TOKEN (OAuth, см. docs/rules/KEYS_AND_TOKENS.md).
"""
import json
import logging
import os
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

# Официальный API Вордстата (POST, JSON, Authorization: Bearer)
WORDSTAT_BASE_URL = os.getenv(
    "YANDEX_WORDSTAT_API_URL", "https://api.wordstat.yandex.net"
).rstrip("/")
TOP_REQUESTS_URL = f"{WORDSTAT_BASE_URL}/v1/topRequests"

# Сколько фраз возвращать по каждому запросу (макс. 2000)
NUM_PHRASES_DEFAULT = 100


def get_wordstat_token() -> Optional[str]:
    """Токен из .env (OAuth, Bearer)."""
    return os.getenv("YANDEX_WORDSTAT_TOKEN", "").strip() or None


def _post_top_requests(body: dict) -> Optional[dict]:
    """
    POST /v1/topRequests.
    Тело: {phrase: "..."} или {phrases: ["...", ...], numPhrases?: N, regions?: [], devices?: []}.
    """
    token = get_wordstat_token()
    if not token:
        return None
    try:
        r = requests.post(
            TOP_REQUESTS_URL,
            json=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        err_body = e.response.text if e.response is not None else ""
        logger.warning("Wordstat API HTTP %s: %s", e.response.status_code if e.response else "", err_body[:200])
        return None
    except Exception as e:
        logger.warning("Wordstat request failed: %s", e)
        return None


def _collect_phrases_from_item(item: dict) -> List[str]:
    """Из одного элемента ответа (requestPhrase + topRequests + associations) собирает список фраз."""
    result = []
    for key in ("topRequests", "associations"):
        for obj in (item.get(key) or []):
            phrase = (obj.get("phrase") or "").strip()
            if phrase:
                result.append(phrase)
    return result


def fetch_top_phrases(
    phrases: List[str],
    regions: Optional[List[int]] = None,
    num_phrases: int = NUM_PHRASES_DEFAULT,
) -> List[str]:
    """
    По списку запросов (сидов) возвращает топ-фразы из Вордстата.

    Используется метод /v1/topRequests: для одной фразы — один запрос с параметром
    `phrase`; для нескольких — один запрос с параметром `phrases` (макс. 128 фраз).

    Ответ: topRequests (популярные запросы, содержащие фразу) + associations (похожие).
    Результат объединяется, дубликаты убираются, возвращается до 50 фраз.

    Параметры:
        phrases: список фраз (сидов), например ["ремонт офисов"].
        regions: опционально список ID регионов (из /v1/getRegionsTree).
        num_phrases: сколько фраз в ответе по каждому запросу (по умолчанию 100, макс. 2000).
    """
    if not phrases:
        return []
    token = get_wordstat_token()
    if not token:
        logger.info("YANDEX_WORDSTAT_TOKEN не задан — ключевые слова только из сидов")
        return []

    phrases = [p.strip() for p in phrases if p.strip()]
    if not phrases:
        return []

    # Один запрос: одна фраза или массив фраз (до 128)
    if len(phrases) == 1:
        body = {"phrase": phrases[0], "numPhrases": min(num_phrases, 2000)}
    else:
        body = {
            "phrases": phrases[:128],
            "numPhrases": min(num_phrases, 2000),
        }
    if regions:
        body["regions"] = regions

    data = _post_top_requests(body)
    if not data:
        return []

    result: List[str] = []
    seen = set()

    # Одна фраза — ответ один объект: requestPhrase, topRequests, associations
    if len(phrases) == 1:
        if "error" in data:
            logger.warning("Wordstat error for phrase %s: %s", phrases[0], data.get("error"))
            return []
        for phrase in _collect_phrases_from_item(data):
            if phrase not in seen:
                seen.add(phrase)
                result.append(phrase)
    else:
        # Несколько фраз — ответ массив объектов (или с полем error в элементе)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("error"):
                continue
            for phrase in _collect_phrases_from_item(item):
                if phrase not in seen:
                    seen.add(phrase)
                    result.append(phrase)

    logger.info("Wordstat: получено %d фраз по %d запросам", len(result), len(phrases))
    return result[:50]


def user_info() -> Optional[dict]:
    """
    GET/POST к /v1/userInfo — лимиты и остаток квоты.
    В документации не указан метод для userInfo; если есть — можно вызвать отдельно.
    """
    # В структуре API указано только описание ответа userInfo, без явного curl. Пока не реализуем.
    return None
