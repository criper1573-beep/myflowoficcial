# -*- coding: utf-8 -*-
"""FastAPI: веб-сервис доски скриптов диалогов (аналог Miro)."""
import base64
import logging
import re

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR, get_storage_dir
from .store import BoardStore, StoreError

logger = logging.getLogger(__name__)

PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _load_env():
    """Загрузить .env из корня проекта (и из текущей директории как fallback)."""
    try:
        from dotenv import load_dotenv
        from .config import BLOCK_DIR

        root_env = BLOCK_DIR.parent.parent / ".env"
        if root_env.exists():
            load_dotenv(root_env)
        else:
            load_dotenv()
    except ImportError:
        pass


_load_env()

app = FastAPI(
    title="Script Board",
    description="Доска скриптов диалогов с клиентами",
    version="2.0.0",
)


def get_store() -> BoardStore:
    return BoardStore(get_storage_dir())


def author_from_request(request: Request) -> str:
    """Автор правки: X-Remote-User от nginx, иначе логин Basic, иначе unknown."""
    remote = (request.headers.get("x-remote-user") or "").replace("\r", "").replace("\n", "").strip()
    if remote:
        return remote[:200]
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("basic "):
        encoded = header.split(" ", 1)[1].strip()
        try:
            decoded = base64.b64decode(encoded, validate=False).decode("utf-8", errors="replace")
        except Exception:
            decoded = ""
        user = decoded.split(":", 1)[0].replace("\r", "").replace("\n", "").strip()
        if user:
            return user[:200]
    return "unknown"


@app.exception_handler(StoreError)
async def _store_error(_request: Request, exc: StoreError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.detail()})


def _check_project_id(project_id: str) -> None:
    if not PROJECT_ID_RE.match(project_id):
        raise HTTPException(status_code=400, detail="Invalid project id")


async def _json_object(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception as exc:
        raise StoreError("bad_request", "Нужен JSON-объект") from exc
    if not isinstance(body, dict):
        raise StoreError("bad_request", "Тело должно быть JSON-объектом")
    return body


@app.get("/api/projects")
def api_list_projects(include_archived: bool = Query(False)):
    """Список проектов: { id, name, revision }."""
    return get_store().list_projects(include_archived=include_archived)


@app.get("/api/projects/{project_id}")
def api_get_project(project_id: str, include_archived: bool = Query(False)):
    """Получить проект по id."""
    _check_project_id(project_id)
    return get_store().get_project(project_id, include_archived=include_archived)


@app.put("/api/projects/{project_id}")
async def api_save_project(project_id: str, request: Request):
    """Сохранить проект целиком. Для существующего нужна актуальная revision."""
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().replace_project(project_id, body, author_from_request(request))


@app.post("/api/projects")
async def api_create_project(request: Request):
    """Создать проект, вернуть id и revision."""
    body = await _json_object(request)
    description = body.get("scriptDescription", body.get("script_description", ""))
    goals = body.get("goals") or []
    if not isinstance(goals, list):
        raise StoreError("bad_request", "goals должен быть массивом")
    return get_store().create_project(
        name=body.get("name") or "",
        script_description=description if isinstance(description, str) else "",
        nodes=body.get("nodes") or [],
        edges=body.get("edges") or [],
        comments=body.get("comments") or [],
        goals=goals,
        author=author_from_request(request),
    )


@app.patch("/api/projects/{project_id}")
async def api_update_project(project_id: str, request: Request):
    """Переименовать проект или обновить scriptDescription."""
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().update_meta(
        project_id,
        revision=body.get("revision"),
        author=author_from_request(request),
        name=body.get("name") if "name" in body else None,
        script_description=body.get("scriptDescription") if "scriptDescription" in body else None,
    )


@app.delete("/api/projects/{project_id}")
def api_archive_project(project_id: str, request: Request, revision: int = Query(...)):
    """Мягкое удаление: проект уходит в архив и пропадает из списка."""
    _check_project_id(project_id)
    return get_store().archive_project(project_id, revision, author_from_request(request))


@app.post("/api/projects/{project_id}/restore")
async def api_restore_project(project_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().restore_project(project_id, body.get("revision"), author_from_request(request))


@app.post("/api/projects/{project_id}/cards")
async def api_create_card(project_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().create_card(project_id, body, author_from_request(request))


@app.patch("/api/projects/{project_id}/cards/{card_id}")
async def api_update_card(project_id: str, card_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().update_card(project_id, card_id, body, author_from_request(request))


@app.delete("/api/projects/{project_id}/cards/{card_id}")
def api_delete_card(project_id: str, card_id: str, request: Request, revision: int = Query(...)):
    _check_project_id(project_id)
    return get_store().delete_card(project_id, card_id, revision, author_from_request(request))


@app.post("/api/projects/{project_id}/edges")
async def api_create_edge(project_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().create_edge(project_id, body, author_from_request(request))


@app.delete("/api/projects/{project_id}/edges/{edge_id}")
def api_delete_edge(
    project_id: str,
    edge_id: str,
    request: Request,
    project_revision: int = Query(..., alias="projectRevision"),
):
    _check_project_id(project_id)
    return get_store().delete_edge(project_id, edge_id, project_revision, author_from_request(request))


@app.post("/api/projects/{project_id}/comments")
async def api_create_comment(project_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().create_comment(project_id, body, author_from_request(request))


@app.patch("/api/projects/{project_id}/comments/{comment_id}")
async def api_update_comment(project_id: str, comment_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().update_comment(project_id, comment_id, body, author_from_request(request))


@app.delete("/api/projects/{project_id}/comments/{comment_id}")
def api_delete_comment(
    project_id: str,
    comment_id: str,
    request: Request,
    project_revision: int = Query(..., alias="projectRevision"),
):
    _check_project_id(project_id)
    return get_store().delete_comment(project_id, comment_id, project_revision, author_from_request(request))


@app.post("/api/projects/{project_id}/goals")
async def api_create_goal(project_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().create_goal(project_id, body, author_from_request(request))


@app.patch("/api/projects/{project_id}/goals/{goal_id}")
async def api_update_goal(project_id: str, goal_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().update_goal(project_id, goal_id, body, author_from_request(request))


@app.delete("/api/projects/{project_id}/goals/{goal_id}")
def api_delete_goal(project_id: str, goal_id: str, request: Request, revision: int = Query(...)):
    _check_project_id(project_id)
    return get_store().delete_goal(project_id, goal_id, revision, author_from_request(request))


@app.post("/api/projects/{project_id}/goals/reorder")
async def api_reorder_goals(project_id: str, request: Request):
    _check_project_id(project_id)
    body = await _json_object(request)
    return get_store().reorder_goals(project_id, body, author_from_request(request))


@app.get("/api/projects/{project_id}/history")
def api_project_history(
    project_id: str,
    since: str | None = Query(None),
    author: str | None = Query(None),
    exclude_author: str | None = Query(None),
):
    """История правок. exclude_author=sonya&since=... — что изменилось после визита Сони."""
    _check_project_id(project_id)
    return get_store().get_history(project_id, since=since, author=author, exclude_author=exclude_author)


@app.api_route(
    "/api/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
def api_unknown(full_path: str):
    """Снятые и неизвестные методы API, без перехвата SPA."""
    raise HTTPException(status_code=404, detail="Not found")


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
