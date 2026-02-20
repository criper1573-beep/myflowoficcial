# -*- coding: utf-8 -*-
"""
MCP-сервер проекта ContentZavod.
Экспортирует инструменты для автопостинга в Дзен, GRS AI и других задач.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Корень проекта — на уровень выше blocks
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Загрузка .env для GRS_AI_API_KEY
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "ContentZavod",
    json_response=True,
)


@mcp.tool()
def zen_publish(
    file: str = "blocks/autopost_zen/articles/commercial_remont.json",
    publish: bool = True,
) -> dict:
    """Опубликовать или сохранить в черновик статью в Яндекс.Дзен.
    Путь к JSON-файлу статьи относительно корня проекта."""
    p = Path(file)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    if not p.exists():
        return {"success": False, "error": f"Файл не найден: {p}"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}
    from blocks.autopost_zen.zen_client import run_post_flow
    exit_code, msg = asyncio.run(run_post_flow(data, publish=publish, headless=False, keep_open=False))
    return {"success": exit_code == 0, "exit_code": exit_code, "message": msg}


@mcp.tool()
def zen_draft(file: str = "blocks/autopost_zen/articles/commercial_remont.json") -> dict:
    """Сохранить статью в черновик в Яндекс.Дзен."""
    return zen_publish(file=file, publish=False)


@mcp.tool()
def zen_list_articles() -> dict:
    """Список доступных статей в blocks/autopost_zen/articles/."""
    articles_dir = PROJECT_ROOT / "blocks" / "autopost_zen" / "articles"
    if not articles_dir.exists():
        return {"articles": [], "error": "Папка не найдена"}
    files = [f.name for f in articles_dir.glob("*.json")]
    return {"articles": sorted(files), "path": str(articles_dir)}


# --- GRS AI ---

def _get_grs_client():
    from blocks.ai_integrations.grs_ai_client import GRSAIClient
    if not os.getenv("GRS_AI_API_KEY"):
        raise ValueError("GRS_AI_API_KEY не задан в .env")
    return GRSAIClient()


@mcp.tool()
def grs_chat(
    question: str,
    system_prompt: str | None = None,
    model: str = "gpt-4o-mini",
) -> dict:
    """Генерация текста через GRS AI. question — запрос, system_prompt — системная роль (опционально)."""
    try:
        client = _get_grs_client()
        text = client.simple_ask(question=question, system_prompt=system_prompt, model=model)
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def grs_chat_messages(
    messages: str,
    model: str = "gpt-4o-mini",
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Генерация текста через GRS AI с полным диалогом. messages — JSON-строка: [{\"role\":\"user\",\"content\":\"...\"}]."""
    try:
        msgs = json.loads(messages) if isinstance(messages, str) else messages
        client = _get_grs_client()
        text = client.chat(messages=msgs, model=model, temperature=temperature, max_tokens=max_tokens)
        return {"success": True, "text": text}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Неверный JSON messages: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def grs_models() -> dict:
    """Список доступных моделей GRS AI (текст и изображения)."""
    from blocks.ai_integrations.grs_ai_client import GRSAIClient
    text_models = GRSAIClient.get_available_models()
    return {
        "success": True,
        "text": text_models,
        "image": GRSAIClient.IMAGE_MODELS,
    }


@mcp.tool()
def grs_image(
    prompt: str,
    model: str = "gpt-image-1",
    size: str = "1024x1024",
) -> dict:
    """Генерация изображения через GRS AI. Возвращает url или b64_json."""
    try:
        client = _get_grs_client()
        result = client.generate_image(prompt=prompt, model=model, size=size)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Telegram Chat Reader (Telethon) ---


@mcp.tool()
def telegram_chat_history(
    entity: str = "zakazyff",
    limit: int = 100,
) -> dict:
    """Выгрузить историю сообщений из Telegram-чата/канала.
    entity — username (zakazyff), @username или t.me/zakazyff.
    Требует TELEGRAM_API_ID, TELEGRAM_API_HASH и авторизацию:
    python -m blocks.telegram_chat_reader login
    """
    try:
        entity_clean = entity.strip()
        if entity_clean.startswith("https://t.me/"):
            entity_clean = entity_clean.replace("https://t.me/", "").strip("/")
        if entity_clean.startswith("t.me/"):
            entity_clean = entity_clean.replace("t.me/", "").strip("/")
        if entity_clean.startswith("@"):
            entity_clean = entity_clean[1:]
        from blocks.telegram_chat_reader.client import fetch_chat_history
        messages, error = asyncio.run(fetch_chat_history(entity_clean, limit=limit))
        if error:
            return {"success": False, "error": error, "messages": []}
        return {
            "success": True,
            "entity": entity_clean,
            "count": len(messages),
            "messages": messages,
        }
    except ValueError as e:
        return {"success": False, "error": str(e), "messages": []}
    except Exception as e:
        return {"success": False, "error": str(e), "messages": []}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
