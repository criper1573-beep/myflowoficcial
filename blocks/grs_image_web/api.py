# -*- coding: utf-8 -*-
"""FastAPI: веб-страница генерации изображений через GRS AI (nano-banana)."""
import base64
import logging
import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Корень блока и папка сохранения генераций
BLOCK_DIR = Path(__file__).resolve().parent
STATIC_DIR = BLOCK_DIR / "static"
GENERATED_DIR = BLOCK_DIR / "generated"

# Загрузка .env из корня проекта (если есть)
try:
    from dotenv import load_dotenv
    root_env = BLOCK_DIR.parent.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)
except ImportError:
    pass

app = FastAPI(title="GRS Image Generator", version="1.0.0")

# Авторизация через Telegram (cookie-сессии)
from .auth import (
    verify_telegram_login,
    make_session_token,
    verify_session_token,
    get_generated_dir,
)

COOKIE_NAME = "grs_image_web_session"
COOKIE_MAX_AGE = 30 * 24 * 3600


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    refs: list[str] = Field(default_factory=list, max_length=5)


def _get_grs_client():
    from blocks.ai_integrations.grs_ai_client import GRSAIClient
    return GRSAIClient()


def _ensure_generated_dir():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Оставляем только безопасные символы для имени файла."""
    return re.sub(r"[^\w\-.]", "_", name)[:80]


def _save_image_from_result(result: dict) -> tuple[str, Path] | None:
    """Сохраняет изображение из ответа GRS (url или b64_json). Возвращает (filename, path) или None."""
    _ensure_generated_dir()
    ts = int(time.time() * 1000)
    ext = "png"

    if result.get("url"):
        try:
            import urllib.request
            with urllib.request.urlopen(result["url"], timeout=30) as r:
                data = r.read()
        except Exception as e:
            logger.warning("Не удалось скачать по url: %s", e)
            return None
    elif result.get("b64_json"):
        data = base64.b64decode(result["b64_json"])
    else:
        return None

    filename = f"gen_{ts}.{ext}"
    path = GENERATED_DIR / filename
    path.write_bytes(data)
    return filename, path


REQUIRE_AUTH = os.getenv("GRS_IMAGE_WEB_REQUIRE_AUTH", "true").strip().lower() in ("true", "1", "yes")
BOT_USERNAME = (os.getenv("GRS_IMAGE_WEB_BOT_USERNAME") or "").strip() or None


@app.get("/api/config")
def api_config():
    """Конфиг для фронта: нужна ли авторизация и имя бота для виджета «Войти через Telegram»."""
    return {"require_auth": REQUIRE_AUTH, "bot_username": BOT_USERNAME}


@app.post("/api/auth/telegram")
async def api_auth_telegram(request: Request, response: Response):
    """Обработка данных от Telegram Login Widget: проверка подписи и установка cookie-сессии."""
    if not REQUIRE_AUTH:
        raise HTTPException(status_code=400, detail="Authorization is disabled")
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")
    user = verify_telegram_login(data)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Invalid Telegram login")
    try:
        tid = int(user.get("id"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Telegram id")
    token = make_session_token(tid)
    # Создаём папку для пользователя
    try:
        get_generated_dir(BLOCK_DIR, tid)
    except Exception:
        logger.exception("Failed to create generated dir for user %s", tid)
    response.set_cookie(COOKIE_NAME, token, httponly=True, max_age=COOKIE_MAX_AGE, path="/")
    return {"authenticated": True}


@app.get("/api/me")
def api_me(request: Request):
    """Проверка cookie-сессии и возврат информации о текущем пользователе."""
    token = request.cookies.get(COOKIE_NAME)
    tid = verify_session_token(token) if token else None
    if not tid:
        return {"authenticated": False}
    return {"authenticated": True, "user": {"id": tid}}


@app.post("/api/logout")
def api_logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
@app.post("/api/improve-prompt")
def api_improve_prompt(body: dict):
    """
    Улучшение промта через GRS AI.
    """
    if not os.getenv("GRS_AI_API_KEY"):
        raise HTTPException(status_code=503, detail="GRS_AI_API_KEY не настроен")
    
    prompt = body.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Промпт не может быть пустым")
    
    try:
        client = _get_grs_client()
        # Используем текстовую модель для улучшения промта
        improved_prompt = f"Улучши этот промпт для генерации изображения, сделай его более детальным и описательным. Оставь смысл, но добавь художественные детали. Верни только улучшенный промпт без JSON и других форматирований. Промпт: {prompt}"
        
        response = client.chat(
            messages=[
                {"role": "system", "content": "Ты эксперт по созданию промптов для генерации изображений. Улучшай промпты, делая их более детальными и художественными. Возвращай только текст улучшенного промпта, без JSON и других форматирований."},
                {"role": "user", "content": improved_prompt}
            ],
            model="gpt-4o-mini",
            max_tokens=500,
            temperature=0.7
        )
        
        improved = response.strip() if response else prompt
        
        # Если ответ похож на JSON, попробуем извлечь промпт
        if improved.startswith('{') and '"prompt"' in improved:
            try:
                import json
                parsed = json.loads(improved)
                improved = parsed.get('prompt', prompt)
            except:
                pass  # оставляем как есть
        
        if not improved:
            improved = prompt  # fallback к оригиналу
            
        return {"improved": improved}
        
    except Exception as e:
        logger.exception("GRS improve_prompt: %s", e)
        # В случае ошибки возвращаем оригинальный промпт
        return {"improved": prompt}


@app.post("/api/generate")
def api_generate(body: GenerateRequest):
    """
    Генерация изображения: промпт + до 5 референсов (data URL base64).
    Модель: nano-banana-pro. Результат сохраняется в папку generated/.
    """
    if not os.getenv("GRS_AI_API_KEY"):
        raise HTTPException(status_code=503, detail="GRS_AI_API_KEY не настроен")
    refs = [r for r in (body.refs or []) if r and str(r).strip().startswith("data:")]
    if len(refs) > 5:
        refs = refs[:5]
    try:
        client = _get_grs_client()
        result = client.generate_image(
            prompt=body.prompt.strip(),
            model="nano-banana-pro",
            size="1024x1024",
            image_urls=refs if refs else None,
        )
    except Exception as e:
        logger.exception("GRS generate_image: %s", e)
        raise HTTPException(status_code=502, detail=str(e))

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error", "Генерация не вернула изображение"),
        )

    saved = _save_image_from_result(result)
    if not saved:
        raise HTTPException(status_code=502, detail="Не удалось сохранить изображение")
    filename, _ = saved
    return {
        "success": True,
        "imageUrl": f"/generated/{filename}",
        "id": filename,
    }


@app.get("/api/history")
def api_history():
    """Последние 20 сгенерированных изображений (для попапа «История»)."""
    _ensure_generated_dir()
    files = []
    for p in sorted(GENERATED_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            files.append({"id": p.name, "url": f"/generated/{p.name}"})
        if len(files) >= 20:
            break
    return {"items": files}


@app.get("/generated/{filename:path}")
def serve_generated(filename: str):
    """Раздача файла из папки generated (только существующие файлы в этой папке)."""
    path = (GENERATED_DIR / filename).resolve()
    if not path.is_file() or GENERATED_DIR not in path.parents and path != GENERATED_DIR:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


@app.get("/")
def index():
    """Главная страница — генератор изображений."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Static files not found")
    return FileResponse(index_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
