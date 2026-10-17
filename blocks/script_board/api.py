# -*- coding: utf-8 -*-
"""FastAPI: веб-сервис доски скриптов диалогов (аналог Miro)."""
import json
import logging
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import BLOCK_DIR, STATIC_DIR, STORAGE_DIR, PROJECTS_FILE

logger = logging.getLogger(__name__)

# Допустимый id проекта (без path traversal)
PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

def _load_env():
    """Загрузить .env из корня проекта (и из текущей директории как fallback)."""
    try:
        from dotenv import load_dotenv
        root_env = BLOCK_DIR.parent.parent / ".env"
        if root_env.exists():
            load_dotenv(root_env)
        else:
            load_dotenv()  # cwd
    except ImportError:
        pass


_load_env()

app = FastAPI(
    title="Script Board",
    description="Доска скриптов диалогов с клиентами",
    version="1.0.0",
)


class ChatMessage(BaseModel):
    role: str = Field(..., description="user или assistant")
    content: str = Field("", description="Текст сообщения")


class GenerateRequest(BaseModel):
    script_description: str | None = Field(None, description="Описание проекта/скрипта для контекста")
    messages: list[ChatMessage] = Field(..., description="Диалог: user/assistant")


class ImproveTextRequest(BaseModel):
    text: str = Field("", description="Текст для улучшения")
    script_description: str | None = Field(None, description="Контекст скрипта")


# --- Хранилище проектов на сервере ---

def _ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not PROJECTS_FILE.exists():
        PROJECTS_FILE.write_text("{}", encoding="utf-8")


def _read_projects() -> dict:
    _ensure_storage()
    try:
        data = PROJECTS_FILE.read_text(encoding="utf-8")
        return json.loads(data) if data.strip() else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Read projects failed: %s", e)
        return {}


def _write_projects(projects: dict) -> None:
    _ensure_storage()
    PROJECTS_FILE.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/projects")
def api_list_projects():
    """Список проектов: { id, name }."""
    projects = _read_projects()
    return [
        {"id": pid, "name": (p.get("name") or "Без названия")}
        for pid, p in projects.items()
        if isinstance(p, dict)
    ]


@app.get("/api/projects/{project_id}")
def api_get_project(project_id: str):
    """Получить проект по id."""
    if not PROJECT_ID_RE.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project id")
    projects = _read_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects[project_id]


@app.put("/api/projects/{project_id}")
def api_save_project(project_id: str, body: dict):
    """Сохранить проект (body: name, nodes, edges, scriptDescription, comments)."""
    if not PROJECT_ID_RE.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project id")
    projects = _read_projects()
    projects[project_id] = {
        "name": body.get("name") or "Без названия",
        "nodes": body.get("nodes", []),
        "edges": body.get("edges", []),
        "scriptDescription": body.get("scriptDescription", body.get("script_description", "")),
        "comments": body.get("comments", []),
    }
    _write_projects(projects)
    return {"success": True}


@app.post("/api/projects")
def api_create_project(body: dict):
    """Создать проект (body: name), вернуть id."""
    import time
    project_id = f"project-{int(time.time() * 1000)}"
    projects = _read_projects()
    projects[project_id] = {
        "name": (body.get("name") or "").strip() or "Новый проект",
        "nodes": body.get("nodes", []),
        "edges": body.get("edges", []),
        "scriptDescription": body.get("scriptDescription", body.get("script_description", "")),
        "comments": body.get("comments", []),
    }
    _write_projects(projects)
    return {"id": project_id}


def _get_grs_client():
    import os
    from blocks.ai_integrations.grs_ai_client import GRSAIClient
    key = (os.getenv("GRS_AI_API_KEY") or "").strip()
    if not key:
        _load_env()
        key = (os.getenv("GRS_AI_API_KEY") or "").strip()
    if not key:
        raise ValueError(
            "GRS_AI_API_KEY не задан. Добавьте в файл .env в корне проекта строку: GRS_AI_API_KEY=ваш_ключ"
        )
    return GRSAIClient()


@app.post("/api/generate")
def api_generate(body: GenerateRequest):
    """
    Сгенерировать ответ по контексту диалога (GRS AI).
    script_description добавляется как system-сообщение при наличии.
    """
    messages = []
    if body.script_description and body.script_description.strip():
        messages.append({"role": "system", "content": "Контекст скрипта:\n" + body.script_description.strip()})
    for m in body.messages:
        if m.role not in ("user", "assistant"):
            continue
        messages.append({"role": m.role, "content": m.content or ""})
    if not messages or all(m.get("role") == "system" for m in messages):
        return {"success": False, "error": "Нужен хотя бы один user или assistant message"}
    try:
        client = _get_grs_client()
        text = client.chat(messages=messages)
        return {"success": True, "text": text}
    except Exception as e:
        logger.exception("Generate failed: %s", e)
        return {"success": False, "error": str(e)}


@app.post("/api/improve-text")
def api_improve_text(body: ImproveTextRequest):
    """
    Улучшить/доработать текст карточки через GRS AI.
    Возвращает только улучшенный текст.
    """
    system = (
        "Ты редактор скриптов диалогов с клиентами. "
        "Улучши и доработай следующий текст: сделай его яснее, вежливее и уместнее для диалога. "
        "Сохрани смысл и тон. Верни только улучшенный текст, без пояснений и кавычек."
    )
    if body.script_description and body.script_description.strip():
        system += "\n\nКонтекст скрипта:\n" + body.script_description.strip()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": body.text.strip() or "(пустой текст — предложи короткий вариант реплики для скрипта)"},
    ]
    try:
        client = _get_grs_client()
        text = client.chat(messages=messages)
        return {"success": True, "text": text.strip()}
    except Exception as e:
        logger.exception("Improve text failed: %s", e)
        return {"success": False, "error": str(e)}


@app.get("/api/check-grs")
def api_check_grs():
    """
    Проверить, задан ли GRS_AI_API_KEY (для отладки).
    Возвращает configured: true/false, без показа ключа.
    """
    import os
    key = (os.getenv("GRS_AI_API_KEY") or "").strip()
    if not key:
        _load_env()
        key = (os.getenv("GRS_AI_API_KEY") or "").strip()
    return {
        "configured": bool(key),
        "hint": "Задайте GRS_AI_API_KEY в файле .env в корне проекта" if not key else None,
    }


@app.get("/api/models")
def api_models():
    """Список доступных моделей GRS AI для выбора на фронте."""
    try:
        from blocks.ai_integrations.grs_ai_client import GRSAIClient
        models = GRSAIClient.get_available_models()
        return {"success": True, "models": models}
    except Exception as e:
        return {"success": False, "error": str(e), "models": {}}


# Статика SPA
if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/favicon.svg")
def favicon():
    """Фавикон доски скриптов."""
    path = STATIC_DIR / "favicon.svg"
    if path.is_file():
        return FileResponse(path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/")
def index():
    """Главная страница — SPA index.html."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"service": "Script Board", "docs": "/docs", "hint": "Run npm run build in frontend first"}


@app.get("/{path:path}")
def spa_fallback(path: str):
    """SPA: все неизвестные пути отдаём index.html."""
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not found")
