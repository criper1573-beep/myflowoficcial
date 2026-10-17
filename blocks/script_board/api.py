# -*- coding: utf-8 -*-
"""HTTP API доски скриптов.

Автор правки берётся из заголовка X-Remote-User (nginx: proxy_set_header
X-Remote-User $remote_user) или из Basic Authorization. Если заголовков нет —
author = "unknown".
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from blocks.script_board.store import BoardStore, StoreError, _check_id

BLOCK_DIR = Path(__file__).resolve().parent
DIST_DIR = BLOCK_DIR / "frontend" / "dist"


def author_from_request(request: Request) -> str:
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


def create_app(storage_dir: str | os.PathLike | None = None) -> FastAPI:
    store = BoardStore(storage_dir)
    app = FastAPI(
        title="Script Board",
        version="2.0.0",
        description="Доска скриптов переписки. Гранулярные правки, ревизии и история.",
    )
    app.state.store = store

    @app.exception_handler(StoreError)
    async def _store_error(_request: Request, exc: StoreError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail()})

    def author(request: Request) -> str:
        return author_from_request(request)

    @app.get("/api/projects")
    def list_projects(include_archived: bool = Query(False)):
        return store.list_projects(include_archived=include_archived)

    @app.post("/api/projects")
    async def create_project(request: Request):
        body = await _json_object(request)
        created = store.create_project(
            name=body.get("name"),
            script_description=body.get("scriptDescription") or "",
            nodes=body.get("nodes") or [],
            edges=body.get("edges") or [],
            comments=body.get("comments") or [],
            author=author(request),
        )
        return created

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str, include_archived: bool = Query(False)):
        _check_id(project_id, "project id")
        return store.get_project(project_id, include_archived=include_archived)

    @app.put("/api/projects/{project_id}")
    async def replace_project(project_id: str, request: Request):
        body = await _json_object(request)
        return store.replace_project(project_id, body, author(request))

    @app.patch("/api/projects/{project_id}")
    async def update_project(project_id: str, request: Request):
        body = await _json_object(request)
        return store.update_project_meta(
            project_id,
            revision=body.get("revision"),
            author=author(request),
            name=body.get("name") if "name" in body else None,
            script_description=body.get("scriptDescription") if "scriptDescription" in body else None,
        )

    @app.delete("/api/projects/{project_id}")
    def archive_project(project_id: str, request: Request, revision: int = Query(...)):
        return store.archive_project(project_id, revision, author(request))

    @app.post("/api/projects/{project_id}/restore")
    async def restore_project(project_id: str, request: Request):
        body = await _json_object(request)
        return store.restore_project(project_id, body.get("revision"), author(request))

    @app.post("/api/projects/{project_id}/cards")
    async def create_card(project_id: str, request: Request):
        body = await _json_object(request)
        return store.create_card(project_id, body, author(request))

    @app.patch("/api/projects/{project_id}/cards/{card_id}")
    async def update_card(project_id: str, card_id: str, request: Request):
        body = await _json_object(request)
        return store.update_card(project_id, card_id, body, author(request))

    @app.delete("/api/projects/{project_id}/cards/{card_id}")
    def delete_card(project_id: str, card_id: str, request: Request, revision: int = Query(...)):
        return store.delete_card(project_id, card_id, revision, author(request))

    @app.post("/api/projects/{project_id}/edges")
    async def create_edge(project_id: str, request: Request):
        body = await _json_object(request)
        return store.create_edge(project_id, body, author(request))

    @app.delete("/api/projects/{project_id}/edges/{edge_id}")
    def delete_edge(
        project_id: str,
        edge_id: str,
        request: Request,
        project_revision: int = Query(..., alias="projectRevision"),
    ):
        return store.delete_edge(project_id, edge_id, project_revision, author(request))

    @app.post("/api/projects/{project_id}/comments")
    async def create_comment(project_id: str, request: Request):
        body = await _json_object(request)
        return store.create_comment(project_id, body, author(request))

    @app.patch("/api/projects/{project_id}/comments/{comment_id}")
    async def update_comment(project_id: str, comment_id: str, request: Request):
        body = await _json_object(request)
        return store.update_comment(project_id, comment_id, body, author(request))

    @app.delete("/api/projects/{project_id}/comments/{comment_id}")
    def delete_comment(
        project_id: str,
        comment_id: str,
        request: Request,
        project_revision: int = Query(..., alias="projectRevision"),
    ):
        return store.delete_comment(project_id, comment_id, project_revision, author(request))

    @app.get("/api/projects/{project_id}/history")
    def project_history(
        project_id: str,
        since: str | None = Query(None),
        author_filter: str | None = Query(None, alias="author"),
        exclude_author: str | None = Query(None, alias="exclude_author"),
    ):
        return store.get_history(
            project_id,
            since=since,
            author=author_filter,
            exclude_author=exclude_author,
        )

    _mount_frontend(app)
    return app


async def _json_object(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception as exc:
        raise StoreError("bad_request", "Нужен JSON-объект") from exc
    if not isinstance(body, dict):
        raise StoreError("bad_request", "Тело должно быть JSON-объектом")
    return body


def _mount_frontend(app: FastAPI) -> None:
    """Статика собранного фронта. Маршруты /api не перехватываются."""
    if not DIST_DIR.is_dir():
        return
    assets = DIST_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="script-board-assets")

    index = DIST_DIR / "index.html"

    @app.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(index)

    @app.middleware("http")
    async def spa_fallback(request: Request, call_next):
        response = await call_next(request)
        if request.method != "GET" or response.status_code != 404:
            return response
        path = request.url.path
        if path.startswith(("/api", "/docs", "/openapi", "/redoc")):
            return response
        relative = path.lstrip("/")
        root = DIST_DIR.resolve()
        if relative:
            candidate = (DIST_DIR / relative).resolve()
            if str(candidate).startswith(str(root)) and candidate.is_file():
                return FileResponse(candidate)
            if "." in Path(relative).name:
                return response
        if index.is_file():
            return FileResponse(index)
        return response


app = create_app()
