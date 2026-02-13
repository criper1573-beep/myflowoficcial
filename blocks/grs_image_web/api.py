# -*- coding: utf-8 -*-
"""FastAPI: генерация изображений GRS AI, авторизация Telegram, история по пользователю."""
import base64
import json
import logging
import os
import re
import time
import uuid
from pathlib import Path

# Подгрузка .env из корня проекта (при запуске uvicorn ... api:app иначе не подхватывается)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

import mimetypes
import requests
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import auth

logger = logging.getLogger(__name__)
BLOCK_DIR = Path(__file__).resolve().parent
STATIC_DIR = BLOCK_DIR / "static"
GENERATED_DIR = BLOCK_DIR / "generated"
UPLOADED_DIR = BLOCK_DIR / "uploaded"
COOKIE_NAME = "grs_image_web_session"
LINK_UPLOAD_MAX_MB = 15
ALLOWED_LINK_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 дней
# Локальный режим: без авторизации, все генерации в generated/0/
REQUIRE_AUTH = os.getenv("GRS_IMAGE_WEB_REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes")

app = FastAPI(title="GRS Image Web", version="1.0.0")


@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    """Любая необработанная ошибка → JSON, чтобы клиент не получал HTML."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."},
    )


# ID «локального» пользователя, когда авторизация отключена
LOCAL_USER_ID = 0


def get_telegram_id(request: Request) -> int | None:
    """Текущий пользователь из cookie (или LOCAL_USER_ID, если авторизация отключена)."""
    if not REQUIRE_AUTH:
        return LOCAL_USER_ID
    token = request.cookies.get(COOKIE_NAME)
    return auth.verify_session_token(token) if token else None


def require_auth(request: Request) -> int:
    """Зависимость: вернуть telegram_id или 401."""
    tid = get_telegram_id(request)
    if tid is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram")
    return tid


# --- Pydantic models ---
class TelegramAuthBody(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int = 0
    hash: str = ""


class GenerateBody(BaseModel):
    prompt: str = Field(..., min_length=1)
    refs: list[str] = Field(default_factory=list, max_length=5)  # data URLs (base64)
    format: str = Field(default="1024x1024", description="Размер/формат: 1024x1024, 1024x768 и т.д.")


class ImprovePromptBody(BaseModel):
    prompt: str = Field(..., min_length=1)


# --- Auth ---
@app.post("/api/auth/telegram")
def api_auth_telegram(body: TelegramAuthBody, response: Response):
    """Проверка данных от Telegram Login Widget и установка сессионной cookie."""
    data = body.model_dump()
    user = auth.verify_telegram_login(data)
    if not user or user.get("id") is None:
        raise HTTPException(status_code=400, detail="Не удалось войти через Telegram. Обновите страницу и попробуйте снова.")
    _save_user_display_name(user["id"], user.get("first_name") or user.get("username") or "User")
    token = auth.make_session_token(user["id"])
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"success": True, "user": {"id": user["id"], "first_name": user.get("first_name"), "username": user.get("username")}}


@app.get("/api/config")
def api_config():
    """Публичная конфигурация для фронта (авторизация и имя бота для виджета)."""
    bot = (os.getenv("GRS_IMAGE_WEB_BOT_USERNAME") or os.getenv("TELEGRAM_BOT_USERNAME") or "").strip().replace("@", "")
    return {"require_auth": REQUIRE_AUTH, "bot_username": bot or None}


@app.get("/api/me")
def api_me(request: Request):
    """Текущий пользователь (если авторизован)."""
    tid = get_telegram_id(request)
    if tid is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": {"id": tid}}


@app.post("/api/logout")
def api_logout(response: Response):
    """Выход: удаление cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"success": True}


# --- Improve prompt (GRS AI text) ---
IMPROVE_PROMPT_SYSTEM = (
    "Ты помогаешь улучшать текстовые промпты для генерации изображений нейросетью. "
    "На вход даётся промпт пользователя. Верни один улучшенный промпт: более конкретный, "
    "с деталями по композиции, освещению, стилю, качеству (если уместно). Сохрани язык оригинала. "
    "Ответь только текстом улучшенного промпта, без пояснений и кавычек."
)


@app.post("/api/improve-prompt")
def api_improve_prompt(body: ImprovePromptBody, request: Request, telegram_id: int = Depends(require_auth)):
    """Улучшение промпта через GRS AI (текст)."""
    try:
        try:
            from dotenv import load_dotenv
            for path in (_PROJECT_ROOT / ".env", Path(os.getcwd()) / ".env"):
                if path.exists() and load_dotenv(path):
                    break
        except ImportError:
            pass
        from blocks.ai_integrations.grs_ai_client import GRSAIClient
        client = GRSAIClient()
        reply = client.simple_ask(
            question=body.prompt,
            system_prompt=IMPROVE_PROMPT_SYSTEM,
            model="gpt-4o-mini",
        )
        improved = (reply or "").strip().strip('"\'')
        return {"success": True, "improved": improved or body.prompt}
    except Exception as e:
        logger.exception("Improve prompt: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# --- Generate ---
PRIMARY_IMAGE_MODEL = "nano-banana-pro"
FALLBACK_IMAGE_MODELS = ["nano-banana", "gpt-image-1.5", "sora-image"]
MAX_GENERATE_CYCLES = 3


def _call_grs_generate(prompt: str, image_urls: list[str], size: str = "1024x1024") -> dict:
    """
    Вызов GRS AI с резервными моделями.
    Порядок попыток в каждом цикле: основная → nano-banana → gpt-image-1.5 → sora-image.
    До 3 циклов, затем ошибка.
    """
    try:
        try:
            from dotenv import load_dotenv
            for path in (_PROJECT_ROOT / ".env", Path(os.getcwd()) / ".env"):
                if path.exists() and load_dotenv(path):
                    break
        except ImportError:
            pass
        from blocks.ai_integrations.grs_ai_client import GRSAIClient
        client = GRSAIClient()
        models_per_cycle = [PRIMARY_IMAGE_MODEL] + FALLBACK_IMAGE_MODELS
        last_error = None
        for cycle in range(MAX_GENERATE_CYCLES):
            for model in models_per_cycle:
                try:
                    result = client.generate_image(
                        prompt=prompt,
                        model=model,
                        size=size,
                        image_urls=image_urls if image_urls else None,
                    )
                    if result.get("success"):
                        logger.info("Image generated with model %s (cycle %s)", model, cycle + 1)
                        return result
                    last_error = result.get("error") or result.get("failure_reason") or "No image in response"
                    logger.warning("Model %s failed (cycle %s): %s", model, cycle + 1, last_error)
                except Exception as e:
                    last_error = str(e)
                    logger.warning("Model %s exception (cycle %s): %s", model, cycle + 1, e)
        return {"success": False, "error": last_error or "Все модели недоступны после 3 циклов"}
    except Exception as e:
        logger.exception("GRS generate_image: %s", e)
        return {"success": False, "error": str(e)}


def _save_image_from_result(result: dict, out_path: Path) -> bool:
    """Скачать по url или декодировать b64 и сохранить в out_path."""
    try:
        if result.get("url"):
            r = requests.get(result["url"], timeout=60)
            r.raise_for_status()
            out_path.write_bytes(r.content)
            return True
        b64 = result.get("b64_json")
        if b64:
            out_path.write_bytes(base64.b64decode(b64))
            return True
        return False
    except Exception as e:
        logger.exception("Save image: %s", e)
        return False


def _safe_filename(name: str) -> str:
    """Только буквы, цифры, точка, дефис, подчёркивание."""
    return re.sub(r"[^\w.\-]", "_", name)[:80] or "image"

USERS_JSON = BLOCK_DIR / "users.json"


def _load_users_display_names() -> dict:
    """Загрузить { telegram_id: display_name } для дашборда."""
    if not USERS_JSON.is_file():
        return {}
    try:
        with open(USERS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {str(k): str(v) for k, v in (data or {}).items()}
    except Exception:
        return {}


def _save_user_display_name(telegram_id: int, name: str) -> None:
    """Сохранить отображаемое имя пользователя (при логине)."""
    try:
        data = _load_users_display_names()
        data[str(telegram_id)] = (name or "User").strip() or str(telegram_id)
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning("Save user display name: %s", e)


def _load_prompts_metadata(user_dir: Path) -> dict:
    """Загрузить metadata.json: { filename: prompt }."""
    path = user_dir / "metadata.json"
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_prompt_metadata(user_dir: Path, filename: str, prompt: str) -> None:
    """Добавить промпт для файла в metadata.json."""
    meta = _load_prompts_metadata(user_dir)
    meta[filename] = prompt
    path = user_dir / "metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


# Текст формата для добавления в промпт (чтобы модель учитывала пропорции)
FORMAT_PROMPT_SUFFIX = {
    "1024x1024": " [Формат: соотношение сторон 1:1, квадрат.]",
    "1024x768": " [Формат: соотношение сторон 4:3, горизонтальный.]",
    "768x1024": " [Формат: соотношение сторон 3:4, вертикальный.]",
    "1024x576": " [Формат: соотношение сторон 16:9, широкий.]",
    "576x1024": " [Формат: соотношение сторон 9:16, высокий.]",
}


@app.post("/api/generate")
def api_generate(body: GenerateBody, request: Request, telegram_id: int = Depends(require_auth)):
    """Генерация изображения: референсы + промпт + формат → GRS AI → сохранение в папку пользователя."""
    user_dir = auth.get_generated_dir(BLOCK_DIR, telegram_id)
    size = (body.format or "1024x1024").strip() or "1024x1024"
    prompt_suffix = FORMAT_PROMPT_SUFFIX.get(size) or f" [Формат: {size}.]"
    full_prompt = (body.prompt.strip() + prompt_suffix).strip()
    grs_result = _call_grs_generate(full_prompt, body.refs, size=size)
    if not grs_result.get("success"):
        raise HTTPException(status_code=502, detail=grs_result.get("error", "Ошибка генерации"))
    filename = f"{uuid.uuid4().hex}_{int(time.time())}.png"
    out_path = user_dir / filename
    if not _save_image_from_result(grs_result, out_path):
        raise HTTPException(status_code=502, detail="Не удалось сохранить изображение")
    _save_prompt_metadata(user_dir, filename, body.prompt.strip())
    # URL для скачивания/просмотра (доступ только для своего telegram_id проверяется в эндпоинте)
    image_url = f"/generated/{telegram_id}/{filename}"
    return {"success": True, "imageUrl": image_url, "id": filename}


@app.get("/api/history")
def api_history(request: Request, telegram_id: int = Depends(require_auth)):
    """Последние 20 генераций текущего пользователя (с промптом из metadata.json)."""
    user_dir = auth.get_generated_dir(BLOCK_DIR, telegram_id)
    prompts = _load_prompts_metadata(user_dir)
    files = sorted(user_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    return {
        "items": [
            {
                "id": f.name,
                "url": f"/generated/{telegram_id}/{f.name}",
                "name": f.name,
                "prompt": prompts.get(f.name, ""),
            }
            for f in files
        ]
    }


@app.get("/generated/{telegram_id}/{filename}")
def serve_generated(telegram_id: int, filename: str, request: Request):
    """Раздача файла только владельцу (проверка сессии; в режиме без авторизации — любой доступ к local)."""
    current = get_telegram_id(request)
    if current is None or current != telegram_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    safe = _safe_filename(filename)
    path = BLOCK_DIR / "generated" / str(telegram_id) / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(str(path), media_type="image/png")


# --- Links: загрузка фото → прямая ссылка (привязано к Telegram) ---
@app.post("/api/links/upload")
def api_links_upload(
    request: Request,
    file: UploadFile = File(...),
    telegram_id: int = Depends(require_auth),
):
    """Загрузить фото, получить прямую ссылку. Публичный доступ по ссылке."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_LINK_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Разрешены только: {', '.join(ALLOWED_LINK_EXTENSIONS)}",
        )
    max_bytes = LINK_UPLOAD_MAX_MB * 1024 * 1024
    content = file.file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Размер файла не более {LINK_UPLOAD_MAX_MB} МБ",
        )
    user_dir = auth.get_uploaded_dir(BLOCK_DIR, telegram_id)
    filename = f"{uuid.uuid4().hex}{ext}"
    out_path = user_dir / filename
    out_path.write_bytes(content)
    path_url = f"/uploaded/{telegram_id}/{filename}"
    base = str(request.base_url).rstrip("/")
    full_url = f"{base}{path_url}"
    return {"success": True, "url": path_url, "fullUrl": full_url, "id": filename}


@app.get("/api/links")
def api_links_list(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    telegram_id: int = Depends(require_auth),
):
    """Список загруженных фото пользователя (для прямых ссылок)."""
    user_dir = auth.get_uploaded_dir(BLOCK_DIR, telegram_id)
    if not user_dir.exists():
        return {"items": [], "total": 0}
    files = sorted(
        [f for f in user_dir.iterdir() if f.is_file() and f.suffix.lower() in ALLOWED_LINK_EXTENSIONS],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    total = len(files)
    page = files[offset : offset + limit]
    base = str(request.base_url).rstrip("/")
    items = [
        {
            "id": f.name,
            "url": f"/uploaded/{telegram_id}/{f.name}",
            "fullUrl": f"{base}/uploaded/{telegram_id}/{f.name}",
            "name": f.name,
        }
        for f in page
    ]
    return {"items": items, "total": total}


@app.delete("/api/links/{filename}")
def api_links_delete(
    filename: str,
    telegram_id: int = Depends(require_auth),
):
    """Удалить загруженное фото с сервера."""
    safe = _safe_filename(filename)
    path = auth.get_uploaded_dir(BLOCK_DIR, telegram_id) / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    path.unlink()
    return {"success": True}


@app.get("/uploaded/{telegram_id}/{filename}")
def serve_uploaded(telegram_id: int, filename: str):
    """Публичная раздача загруженного фото (прямая ссылка для вставки куда угодно)."""
    safe = _safe_filename(filename)
    path = BLOCK_DIR / "uploaded" / str(telegram_id) / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    media_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return FileResponse(str(path), media_type=media_type)


# --- Static & index ---
@app.get("/")
def index():
    """Главная: index.html."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Static not found")
    return FileResponse(index_path)


@app.get("/links")
def links_page():
    """Страница «Ссылки»: загрузка фото и список с прямыми ссылками."""
    links_path = STATIC_DIR / "links.html"
    if not links_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(links_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
