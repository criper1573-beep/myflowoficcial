# -*- coding: utf-8 -*-
"""FastAPI: веб-страница генерации изображений через GRS AI (nano-banana)."""
import base64
import json
import logging
import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Корень блока и папка сохранения генераций
BLOCK_DIR = Path(__file__).resolve().parent
STATIC_DIR = BLOCK_DIR / "static"
GENERATED_DIR = BLOCK_DIR / "generated"
USERS_JSON = BLOCK_DIR / "users.json"

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
    get_uploaded_dir,
)

COOKIE_NAME = "grs_image_web_session"
COOKIE_MAX_AGE = 30 * 24 * 3600


def _display_name_from_telegram_user(user: dict) -> str:
    """Имя для отображения: first_name + last_name или username или ID."""
    first = (user.get("first_name") or "").strip()
    last = (user.get("last_name") or "").strip()
    username = (user.get("username") or "").strip()
    if first or last:
        return f"{first} {last}".strip() or first or last
    if username:
        return f"@{username}"
    return str(user.get("id") or "")


def _save_user_display_name(telegram_id: int, display_name: str) -> None:
    """Добавить/обновить имя пользователя в users.json для дашборда аналитики."""
    try:
        data = {}
        if USERS_JSON.is_file():
            with open(USERS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        data[str(telegram_id)] = display_name
        with open(USERS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0)
    except Exception as e:
        logger.warning("Не удалось сохранить users.json: %s", e)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    refs: list[str] = Field(default_factory=list, max_length=5)


class ImprovePromptRequest(BaseModel):
    prompt: str = Field("", min_length=0)


def _get_grs_client():
    from blocks.ai_integrations.grs_ai_client import GRSAIClient
    return GRSAIClient()


def _ensure_generated_dir():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Оставляем только безопасные символы для имени файла."""
    return re.sub(r"[^\w\-.]", "_", name)[:80]


def _save_image_from_result(result: dict, save_dir: Path) -> tuple[str, Path] | None:
    """Сохраняет изображение из ответа GRS в save_dir (папка пользователя). Возвращает (filename, path) или None."""
    save_dir.mkdir(parents=True, exist_ok=True)
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
    path = save_dir / filename
    path.write_bytes(data)
    return filename, path


REQUIRE_AUTH = os.getenv("GRS_IMAGE_WEB_REQUIRE_AUTH", "true").strip().lower() in ("true", "1", "yes")
BOT_USERNAME = (os.getenv("GRS_IMAGE_WEB_BOT_USERNAME") or "").strip() or None

# Максимальный размер загружаемого файла для ссылок (15 МБ)
LINKS_UPLOAD_MAX_BYTES = 15 * 1024 * 1024


def _get_tid_from_request(request: Request) -> int | None:
    """Вернуть telegram_id из cookie или None."""
    token = request.cookies.get(COOKIE_NAME)
    return verify_session_token(token) if token else None


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
    # Сохраняем имя для дашборда аналитики (Generation)
    _save_user_display_name(tid, _display_name_from_telegram_user(user))
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
def api_improve_prompt(body: ImprovePromptRequest):
    """
    Улучшение промта через GRS AI.
    """
    if not os.getenv("GRS_AI_API_KEY"):
        raise HTTPException(status_code=503, detail="GRS_AI_API_KEY не настроен")
    
    prompt = (body.prompt or "").strip()
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
def api_generate(request: Request, body: GenerateRequest):
    """
    Генерация изображения: промпт + до 5 референсов (data URL base64).
    Модель: nano-banana-pro. Результат сохраняется в папку generated/<telegram_id>/.
    """
    if not os.getenv("GRS_AI_API_KEY"):
        raise HTTPException(status_code=503, detail="GRS_AI_API_KEY не настроен")
    tid = _get_tid_from_request(request)
    if tid is None and not REQUIRE_AUTH:
        tid = 0
    if tid is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram")
    save_dir = get_generated_dir(BLOCK_DIR, tid)

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

    saved = _save_image_from_result(result, save_dir)
    if not saved:
        raise HTTPException(status_code=502, detail="Не удалось сохранить изображение")
    filename, _ = saved
    return {
        "success": True,
        "imageUrl": f"/generated/{tid}/{filename}",
        "id": filename,
    }


@app.get("/api/history")
def api_history(request: Request):
    """Последние 20 сгенерированных изображений текущего пользователя (для попапа «История»)."""
    tid = _get_tid_from_request(request)
    if tid is None and not REQUIRE_AUTH:
        tid = 0
    if tid is None:
        return {"items": []}
    user_dir = get_generated_dir(BLOCK_DIR, tid)
    if not user_dir.exists():
        return {"items": []}
    exts = (".png", ".jpg", ".jpeg", ".webp")
    all_files = [p for p in user_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
    files = []
    for p in sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
        files.append({"id": p.name, "url": f"/generated/{tid}/{p.name}"})
    return {"items": files}


@app.get("/generated/{filename:path}")
def serve_generated(filename: str):
    """Раздача файла из папки generated (только существующие файлы в этой папке)."""
    path = (GENERATED_DIR / filename).resolve()
    if not path.is_file() or (GENERATED_DIR.resolve() not in path.parents and path != GENERATED_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


def _links_tid(request: Request) -> int | None:
    """Telegram ID для раздела «Ссылки»: из cookie или 0 при отключённой авторизации."""
    tid = _get_tid_from_request(request)
    if tid is not None:
        return tid
    if not REQUIRE_AUTH:
        return 0
    return None


@app.get("/api/links")
def api_links_list(request: Request, limit: int = 10, offset: int = 0):
    """Список загруженных фото пользователя (прямые ссылки)."""
    tid = _links_tid(request)
    if tid is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram")
    limit = max(1, min(100, limit))
    offset = max(0, offset)
    user_dir = get_uploaded_dir(BLOCK_DIR, tid)
    if not user_dir.exists():
        return {"items": [], "total": 0}
    all_files = [
        p for p in user_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp")
    ]
    total = len(all_files)
    sorted_files = sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)
    page = sorted_files[offset:offset + limit]
    base = str(request.base_url).rstrip("/")
    items = []
    for p in page:
        name = p.name
        url = f"/uploaded/{name}"
        full_url = f"{base}{url}"
        items.append({"id": name, "url": url, "fullUrl": full_url})
    return {"items": items, "total": total}


@app.post("/api/links/upload")
async def api_links_upload(request: Request, file: UploadFile = File(...)):
    """Загрузка фото для получения прямой ссылки. До 15 МБ."""
    tid = _links_tid(request)
    if tid is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Разрешены только изображения (PNG, JPG, GIF, WebP)")
    content = await file.read()
    if len(content) > LINKS_UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Файл слишком большой. До 15 МБ.")
    user_dir = get_uploaded_dir(BLOCK_DIR, tid)
    ext = (file.filename or "").split(".")[-1].lower() if "." in (file.filename or "") else "png"
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        ext = "png"
    ts = int(time.time() * 1000)
    safe_name = _safe_filename(file.filename or "image")[:50]
    filename = f"link_{ts}_{safe_name}.{ext}" if safe_name else f"link_{ts}.{ext}"
    file_path = user_dir / filename
    file_path.write_bytes(content)
    base = str(request.base_url).rstrip("/")
    url = f"/uploaded/{filename}"
    return {"id": filename, "url": url, "fullUrl": f"{base}{url}"}


@app.delete("/api/links/{file_id:path}")
def api_links_delete(request: Request, file_id: str):
    """Удаление загруженного фото (только своё)."""
    tid = _links_tid(request)
    if tid is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram")
    if not file_id or ".." in file_id or "/" in file_id or "\\" in file_id:
        raise HTTPException(status_code=400, detail="Недопустимый идентификатор")
    user_dir = get_uploaded_dir(BLOCK_DIR, tid).resolve()
    path = (user_dir / file_id).resolve()
    if not path.is_file() or user_dir not in path.parents:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        path.unlink()
    except OSError as e:
        logger.warning("Не удалось удалить файл %s: %s", path, e)
        raise HTTPException(status_code=500, detail="Не удалось удалить файл")
    return {"ok": True}


@app.get("/uploaded/{filename:path}")
def serve_uploaded(request: Request, filename: str):
    """Раздача загруженного файла (только из папки текущего пользователя)."""
    tid = _links_tid(request)
    if tid is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация через Telegram")
    if ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Недопустимый путь")
    user_dir = get_uploaded_dir(BLOCK_DIR, tid).resolve()
    path = (user_dir / filename).resolve()
    if not path.is_file() or user_dir not in path.parents:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


@app.get("/links")
def links_page():
    """Страница «Прямые ссылки на изображения»."""
    links_path = STATIC_DIR / "links.html"
    if not links_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(links_path)


@app.get("/")
def index():
    """Главная страница — генератор изображений."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Static files not found")
    return FileResponse(index_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
