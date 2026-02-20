# -*- coding: utf-8 -*-
"""FastAPI: REST API для дашборда + раздача static/."""
import json
import logging
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import URLError, HTTPError

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .models import Run, Step

logger = logging.getLogger(__name__)
BLOCK_DIR = Path(__file__).resolve().parent
STATIC_DIR = BLOCK_DIR / "static"
# Соседний блок grs_image_web (генерации и загрузки ссылок). Пути можно переопределить через env.
_GRS_BASE = Path(os.getenv("GRS_IMAGE_WEB_DIR")).resolve() if os.getenv("GRS_IMAGE_WEB_DIR") else (BLOCK_DIR.parent / "grs_image_web")
GRIS_IMAGE_WEB_DIR = _GRS_BASE
GENERATED_DIR = Path(os.getenv("GRS_IMAGE_WEB_GENERATED_DIR")).resolve() if os.getenv("GRS_IMAGE_WEB_GENERATED_DIR") else (_GRS_BASE / "generated")
UPLOADED_DIR = Path(os.getenv("GRS_IMAGE_WEB_UPLOADED_DIR")).resolve() if os.getenv("GRS_IMAGE_WEB_UPLOADED_DIR") else (_GRS_BASE / "uploaded")
GRIS_IMAGE_WEB_PUBLIC_URL = os.getenv("GRS_IMAGE_WEB_PUBLIC_URL", "https://flowimage.ru").rstrip("/")
GRS_IMAGE_WEB_INTERNAL_URL = (os.getenv("GRS_IMAGE_WEB_INTERNAL_URL") or "http://127.0.0.1:8765").strip().rstrip("/")
ALLOWED_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp")
USERS_JSON = _GRS_BASE / "users.json"


def _ensure_generation_user_names(telegram_ids: set) -> None:
    """Подтянуть имена для telegram_id без имени через API grs_image_web (getChat → users.json)."""
    for tid in telegram_ids:
        if tid == "0":
            continue
        try:
            url = f"{GRS_IMAGE_WEB_INTERNAL_URL}/api/user/ensure_name/{tid}"
            req = UrlRequest(url, method="GET")
            urlopen(req, timeout=3)
        except Exception:
            pass


def _load_generation_user_names() -> dict:
    """Загрузить { telegram_id: display_name } из grs_image_web."""
    if not USERS_JSON.is_file():
        return {}
    try:
        with open(USERS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {str(k): str(v) for k, v in (data or {}).items()}
    except Exception:
        return {}


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w.\-]", "_", name)[:80] or "image"

app = FastAPI(title="Pipeline Analytics", version="1.0.0")


def _row_to_tuple(row) -> tuple:
    """sqlite3.Row -> tuple для совместимости с from_row."""
    return tuple(row) if row is not None else None


def _normalize_project(project: str | None) -> str:
    """Допустимые значения: flow, fulfilment (или fulfillment); иначе — default."""
    if not project or not isinstance(project, str):
        return db.DEFAULT_PROJECT
    key = project.strip().lower()
    if key == "flow":
        return "flow"
    if key in ("fulfilment", "fulfillment"):
        return "fulfilment"
    if key in db.PROJECTS:
        return key
    return db.DEFAULT_PROJECT


def _get_conn(project: str | None = None):
    """Соединение с БД проекта; при ошибке логируем и пробрасываем HTTPException."""
    try:
        return db.get_connection(project=_normalize_project(project))
    except Exception as e:
        logger.exception("Ошибка подключения к БД аналитики: %s", e)
        raise HTTPException(status_code=503, detail=f"База аналитики недоступна: {e!s}")


@app.get("/api/projects")
def api_projects():
    """Список проектов для переключателя дашборда (id и отображаемое имя)."""
    return {
        "projects": [
            {"id": "flow", "label": "FLOW"},
            {"id": "fulfilment", "label": "Фулфилмент"},
        ],
        "default": db.DEFAULT_PROJECT,
    }


def _project_from_request(request: Request, project: str | None = None) -> str:
    """Проект из query param или заголовка X-Requested-Project."""
    if project and str(project).strip():
        return _normalize_project(project)
    header = request.headers.get("X-Requested-Project") if request else None
    if header and str(header).strip():
        return _normalize_project(header)
    return db.DEFAULT_PROJECT


@app.get("/api/stats")
def api_stats(
    request: Request,
    channel: str | None = Query(None),
    project: str | None = Query(None, description="flow | fulfilment"),
):
    """Сводная статистика: всего запусков, успешных, ошибок, сегодня, success_rate. channel: zen, telegram, site, vk, vc_ru."""
    proj = _project_from_request(request, project)
    conn = _get_conn(proj)
    try:
        return db.get_stats(conn, channel=channel)
    except Exception as e:
        logger.exception("Ошибка api/stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/api/stats/timeline")
def api_timeline(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    channel: str | None = Query(None),
    project: str | None = Query(None, description="flow | fulfilment"),
):
    """Публикации по дням для графика. channel: фильтр по каналу."""
    proj = _project_from_request(request, project)
    conn = _get_conn(proj)
    try:
        return db.get_timeline(conn, days=days, channel=channel)
    except Exception as e:
        logger.exception("Ошибка api/stats/timeline: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/api/stats/funnel")
def api_funnel(
    request: Request,
    channel: str | None = Query(None, description="zen, telegram, site, vk, vc_ru"),
    project: str | None = Query(None, description="flow | fulfilment"),
):
    """Воронка по каналу (просмотры и т.д.). Пока заглушка — данные зависят от канала."""
    # TODO: собирать метрики по каналам (просмотры, клики и т.д.)
    return {"channel": channel or "", "stages": [], "note": "Данные воронки пока не собираются"}


@app.get("/api/runs")
def api_runs(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    channel: str | None = Query(None),
    project: str | None = Query(None, description="flow | fulfilment"),
):
    """Список запусков (новые первые), с шагами для отображения цепочки. channel: фильтр по каналу."""
    proj = _project_from_request(request, project)
    conn = _get_conn(proj)
    try:
        rows = db.get_runs(conn, limit=limit, offset=offset, status=status, channel=channel)
        result = []
        for r in rows:
            t = _row_to_tuple(r)
            run_id = t[0]
            steps_rows = db.get_steps_for_run(conn, run_id)
            steps = [Step.from_row(_row_to_tuple(s)) for s in steps_rows]
            run = Run.from_row(t, steps=steps)
            result.append(run.to_dict())
        return result
    except Exception as e:
        logger.exception("Ошибка api/runs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/api/runs/{run_id:int}")
def api_run_detail(
    request: Request,
    run_id: int,
    project: str | None = Query(None, description="flow | fulfilment"),
):
    """Детали запуска со всеми шагами."""
    proj = _project_from_request(request, project)
    conn = _get_conn(proj)
    try:
        row = db.get_run(conn, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Run not found")
        steps_rows = db.get_steps_for_run(conn, run_id)
        steps = [Step.from_row(_row_to_tuple(s)) for s in steps_rows]
        run = Run.from_row(_row_to_tuple(row), steps=steps)
        return run.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ошибка api/runs/%s: %s", run_id, e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Список systemd-сервисов для страницы «Сервисы» (только Linux): (unit, label, description).
SERVER_SERVICES = [
    ("analytics-dashboard", "Дашборд аналитики", "Веб-интерфейс: сводка запусков, графики и статус сервисов"),
    ("analytics-telegram-bot", "Telegram-бот дашборда", "Уведомления в Telegram о запусках и ошибках пайплайна"),
    ("grs-image-web", "Генерация картинок и ссылок", "Веб-интерфейс генерации изображений и загрузки ссылок (flowimage.ru)"),
    ("orchestrator-kz", "Оркестратор контент завода", "Оркестратор: генерация и публикация (Дзен, Telegram) по расписанию; при старте — один пробный запуск"),
    ("spambot", "Спамбот (NewsBot)", "Публикации в каналы: Дзен, соцсети и др."),
    ("contentzavod-watchdog", "Watchdog", "Следит за сервисами и сообщает при сбоях"),
    ("quickpack", "Quickpack", "Сайт Quickpack на сервере"),
]


# Корень проекта (для чтения storage/orchestrator_kz_state.json)
_PROJECT_ROOT = BLOCK_DIR.parent.parent
_ORCHESTRATOR_KZ_STATE_FILE = _PROJECT_ROOT / "storage" / "orchestrator_kz_state.json"


def _get_orchestrator_kz_state() -> dict:
    """Прочитать last_run_at и next_run_at для карточки Оркестратор контент завода."""
    if not _ORCHESTRATOR_KZ_STATE_FILE.exists():
        return {}
    try:
        data = json.loads(_ORCHESTRATOR_KZ_STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {k: data[k] for k in ("last_run_at", "next_run_at") if data.get(k)}
    except Exception:
        return {}


def _service_public_url(unit: str) -> str | None:
    """Публичный URL сервиса (для кнопки «Открыть сайт» в плашке)."""
    u = (unit or "").strip()
    if u == "analytics-dashboard":
        return (os.getenv("DASHBOARD_PUBLIC_URL") or "").strip() or None
    if u == "grs-image-web":
        return (os.getenv("GRS_IMAGE_WEB_PUBLIC_URL") or "https://flowimage.ru").strip() or None
    if u == "quickpack":
        return (os.getenv("QUICKPACK_URL") or "").strip() or None
    return None


def _fetch_remote_server_services() -> dict | None:
    """Запросить статус сервисов с удалённого сервера (для локального дашборда)."""
    url = os.environ.get("ANALYTICS_SERVER_SERVICES_URL", "").strip()
    if not url:
        return None
    base = url.rstrip("/")
    try:
        req = UrlRequest(base + "/api/server-services", headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except (URLError, HTTPError, ValueError, OSError) as e:
        logger.warning("Не удалось загрузить сервисы с %s: %s", base, e)
        return None


@app.get("/api/server-services")
def api_server_services():
    """
    Статус systemd-сервисов (active/failed/inactive).
    На Linux — через systemctl; на других ОС — пустой список или данные с удалённого
    сервера, если задан ANALYTICS_SERVER_SERVICES_URL.
    """
    if sys.platform != "linux":
        remote = _fetch_remote_server_services()
        if remote and remote.get("services"):
            return {"services": remote["services"], "note": "Данные с сервера"}
        # Локальный режим: те же карточки сервисов с пометкой, чтобы блок не пустой и можно тестировать вёрстку
        result_local = []
        for item in SERVER_SERVICES:
            unit, label = item[0], item[1]
            description = item[2] if len(item) > 2 else ""
            s = {
                "unit": unit,
                "label": label,
                "description": description,
                "active_state": "n/a",
                "sub_state": "Локальный режим — статус только на сервере",
                "pid": None,
                "url": _service_public_url(unit),
            }
            if unit == "orchestrator-kz":
                s.update(_get_orchestrator_kz_state())
            result_local.append(s)
        return {"services": result_local, "note": "Статус сервисов отображается только при запуске на Linux-сервере."}
    result = []
    for item in SERVER_SERVICES:
        unit, label = item[0], item[1]
        description = item[2] if len(item) > 2 else ""
        # Quickpack: если задан QUICKPACK_URL — проверяем сайт по HTTP (сайт может быть без systemd-юнита)
        health_url = os.getenv("QUICKPACK_URL", "").strip() if unit == "quickpack" else None
        if health_url:
            try:
                req = UrlRequest(health_url, headers={"User-Agent": "ContentZavod-HealthCheck/1.0"})
                with urlopen(req, timeout=8) as r:
                    code = r.getcode()
                result.append({
                    "unit": unit,
                    "label": label,
                    "description": description,
                    "active_state": "active" if code == 200 else "inactive",
                    "sub_state": f"HTTP {code}" if code != 200 else "работает",
                    "pid": None,
                    "url": _service_public_url(unit),
                })
            except (URLError, HTTPError, OSError) as e:
                logger.debug("Quickpack health check %s: %s", health_url, e)
                result.append({
                    "unit": unit,
                    "label": label,
                    "description": description,
                    "active_state": "inactive",
                    "sub_state": str(e)[:80] if e else "нет ответа",
                    "pid": None,
                    "url": _service_public_url(unit),
                })
            continue
        try:
            # Без --value, чтобы парсить по ключу (порядок вывода systemctl может отличаться)
            out = subprocess.run(
                ["systemctl", "show", unit, "-p", "ActiveState", "-p", "SubState", "-p", "MainPID", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode != 0:
                # Юнит не найден или ошибка — проверяем, есть ли файл юнита на сервере
                check = subprocess.run(
                    ["systemctl", "list-unit-files", unit + ".service", "--no-pager", "--no-legend"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                unit_exists = check.returncode == 0
                sub_state = "не установлен" if not unit_exists else "ошибка"
                result.append({
                    "unit": unit,
                    "label": label,
                    "description": description,
                    "active_state": "inactive",
                    "sub_state": sub_state,
                    "pid": None,
                    "url": _service_public_url(unit),
                })
                continue
            # Парсим KEY=VALUE (порядок строк не фиксирован на разных системах)
            props = {}
            for line in (out.stdout or "").strip().split("\n"):
                line = (line or "").strip()
                if "=" in line:
                    k, _, v = line.partition("=")
                    props[k.strip()] = (v or "").strip()
            raw_active = (props.get("ActiveState") or "unknown").lower()
            sub_state = props.get("SubState") or ""
            pid = (props.get("MainPID") or "").strip() or None
            if pid == "0":
                pid = None
            # Зелёная подсветка: active, reloading или sub_state=running
            is_running = raw_active in ("active", "reloading") or (props.get("SubState") or "").lower() == "running"
            active_state = "active" if is_running else raw_active
            result.append({
                "unit": unit,
                "label": label,
                "description": description,
                "active_state": active_state,
                "sub_state": sub_state,
                "pid": pid,
                "url": _service_public_url(unit),
            })
        except Exception as e:
            logger.warning("systemctl show %s: %s", unit, e)
            result.append({"unit": unit, "label": label, "description": description, "active_state": "error", "sub_state": str(e), "pid": None, "url": _service_public_url(unit)})
    # Для orchestrator-kz добавить last_run_at и next_run_at из state-файла оркестратора
    for s in result:
        if s.get("unit") == "orchestrator-kz":
            s.update(_get_orchestrator_kz_state())
            break
    return {"services": result}


ALLOWED_SERVICE_UNITS = {u[0] for u in SERVER_SERVICES}


@app.post("/api/server-services/{unit}/start")
def api_server_service_start(unit: str):
    """Запустить systemd-сервис (только на Linux, unit из разрешённого списка)."""
    if sys.platform != "linux":
        raise HTTPException(status_code=501, detail="Управление сервисами только на Linux-сервере")
    if unit not in ALLOWED_SERVICE_UNITS:
        raise HTTPException(status_code=400, detail="Сервис не в списке")
    try:
        out = subprocess.run(
            ["sudo", "-n", "systemctl", "start", unit],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode != 0:
            raise HTTPException(status_code=502, detail=out.stderr or out.stdout or "Ошибка systemctl start")
        return {"ok": True, "unit": unit}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Таймаут")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="systemctl/sudo недоступен")


@app.post("/api/server-services/{unit}/stop")
def api_server_service_stop(unit: str):
    """Остановить systemd-сервис (только на Linux, unit из разрешённого списка)."""
    if sys.platform != "linux":
        raise HTTPException(status_code=501, detail="Управление сервисами только на Linux-сервере")
    if unit not in ALLOWED_SERVICE_UNITS:
        raise HTTPException(status_code=400, detail="Сервис не в списке")
    try:
        out = subprocess.run(
            ["sudo", "-n", "systemctl", "stop", unit],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode != 0:
            raise HTTPException(status_code=502, detail=out.stderr or out.stdout or "Ошибка systemctl stop")
        return {"ok": True, "unit": unit}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Таймаут")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="systemctl/sudo недоступен")


# --- Generation: статистика по картинкам и ссылкам (grs_image_web) ---

def _load_prompts_metadata(user_dir: Path) -> dict:
    path = user_dir / "metadata.json"
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _generation_images_summary():
    """Сводка по сгенерированным картинкам: total, byDay, users (tid -> count)."""
    if not GENERATED_DIR.exists():
        return {"total": 0, "byDay": [], "users": []}
    by_day = defaultdict(int)
    user_counts = defaultdict(int)
    # Подпапки по telegram_id (generated/123/*.png)
    for user_dir in GENERATED_DIR.iterdir():
        if not user_dir.is_dir() or not user_dir.name.isdigit():
            continue
        tid = user_dir.name
        for f in user_dir.glob("*.png"):
            user_counts[tid] += 1
            try:
                mtime = f.stat().st_mtime
                day = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
                by_day[day] += 1
            except OSError:
                pass
    # Файлы в корне generated/*.png (grs_image_web сохраняет сюда при генерации)
    for f in GENERATED_DIR.glob("*.png"):
        if f.is_file():
            user_counts["0"] = user_counts.get("0", 0) + 1
            try:
                mtime = f.stat().st_mtime
                day = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
                by_day[day] += 1
            except OSError:
                pass
    days_sorted = sorted(by_day.keys(), reverse=True)[:90]
    by_day_list = [{"day": d, "count": by_day[d]} for d in days_sorted]
    names = _load_generation_user_names()
    missing = {tid for tid in user_counts if tid != "0" and (not names.get(tid) or names.get(tid) == tid)}
    if missing:
        _ensure_generation_user_names(missing)
        names = _load_generation_user_names()
    users_list = [
        {"telegramId": tid, "count": c, "name": names.get(tid) or tid}
        for tid, c in sorted(user_counts.items(), key=lambda x: -x[1])
    ]
    return {"total": sum(user_counts.values()), "byDay": by_day_list, "users": users_list}


def _generation_links_summary():
    """Сводка по загруженным ссылкам: total, byDay, users."""
    if not UPLOADED_DIR.exists():
        return {"total": 0, "byDay": [], "users": []}
    by_day = defaultdict(int)
    user_counts = defaultdict(int)
    for user_dir in UPLOADED_DIR.iterdir():
        if not user_dir.is_dir() or not user_dir.name.isdigit():
            continue
        tid = user_dir.name
        for f in user_dir.iterdir():
            if f.is_file() and f.suffix.lower() in ALLOWED_IMAGE_EXT:
                user_counts[tid] += 1
                try:
                    mtime = f.stat().st_mtime
                    day = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
                    by_day[day] += 1
                except OSError:
                    pass
    days_sorted = sorted(by_day.keys(), reverse=True)[:90]
    by_day_list = [{"day": d, "count": by_day[d]} for d in days_sorted]
    names = _load_generation_user_names()
    missing = {tid for tid in user_counts if tid != "0" and (not names.get(tid) or names.get(tid) == tid)}
    if missing:
        _ensure_generation_user_names(missing)
        names = _load_generation_user_names()
    users_list = [
        {"telegramId": tid, "count": c, "name": names.get(tid) or tid}
        for tid, c in sorted(user_counts.items(), key=lambda x: -x[1])
    ]
    return {"total": sum(user_counts.values()), "byDay": by_day_list, "users": users_list}


@app.get("/api/generation/images/summary")
def api_generation_images_summary():
    """Статистика по сгенерированным картинкам: всего, по дням, по пользователям."""
    try:
        return _generation_images_summary()
    except Exception as e:
        logger.exception("generation images summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generation/links/summary")
def api_generation_links_summary():
    """Статистика по загруженным ссылкам: всего, по дням, по пользователям."""
    try:
        return _generation_links_summary()
    except Exception as e:
        logger.exception("generation links summary: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generation/images/user/{telegram_id}")
def api_generation_images_user(telegram_id: str):
    """Список генераций пользователя: id, prompt, date, imageProxyUrl, downloadUrl."""
    tid = _safe_filename(telegram_id).strip("_") or "0"
    items = []
    # Подпапка generated/<tid>/
    user_dir = GENERATED_DIR / tid
    if user_dir.is_dir():
        prompts = _load_prompts_metadata(user_dir)
        for f in sorted(user_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                mtime = f.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            except OSError:
                date_str = ""
            items.append({
                "id": f.name,
                "prompt": prompts.get(f.name, ""),
                "date": date_str,
                "imageProxyUrl": f"/api/generation/image-proxy/{tid}/{f.name}",
                "downloadUrl": f"{GRIS_IMAGE_WEB_PUBLIC_URL}/generated/{tid}/{f.name}",
            })
    # Для tid "0" добавляем файлы из корня generated/*.png (куда пишет grs_image_web)
    if tid == "0":
        root_prompts = _load_prompts_metadata(GENERATED_DIR) if GENERATED_DIR.is_dir() else {}
        for f in sorted(GENERATED_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not f.is_file():
                continue
            try:
                mtime = f.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            except OSError:
                date_str = ""
            items.append({
                "id": f.name,
                "prompt": root_prompts.get(f.name, ""),
                "date": date_str,
                "imageProxyUrl": f"/api/generation/image-proxy/0/{f.name}",
                "downloadUrl": f"{GRIS_IMAGE_WEB_PUBLIC_URL}/generated/{f.name}",
            })
    items.sort(key=lambda x: x.get("date") or "", reverse=True)
    return {"items": items}


@app.get("/api/generation/links/user/{telegram_id}")
def api_generation_links_user(telegram_id: str):
    """Список загруженных ссылок пользователя: id, fullUrl, date."""
    tid = _safe_filename(telegram_id).strip("_") or "0"
    user_dir = UPLOADED_DIR / tid
    if not user_dir.is_dir():
        return {"items": []}
    files = sorted(
        [f for f in user_dir.iterdir() if f.is_file() and f.suffix.lower() in ALLOWED_IMAGE_EXT],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    items = []
    for f in files:
        try:
            mtime = f.stat().st_mtime
            date_str = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        except OSError:
            date_str = ""
        full_url = f"{GRIS_IMAGE_WEB_PUBLIC_URL}/uploaded/{tid}/{f.name}"
        items.append({"id": f.name, "fullUrl": full_url, "date": date_str})
    return {"items": items}


@app.get("/api/generation/image-proxy/{telegram_id}/{filename}")
def api_generation_image_proxy(telegram_id: str, filename: str):
    """Прокси картинки из generated/ (для превью в дашборде)."""
    tid = _safe_filename(telegram_id).strip("_") or "0"
    fname = _safe_filename(filename)
    path = GENERATED_DIR / tid / fname
    if not path.is_file() and tid == "0":
        path = GENERATED_DIR / fname  # файлы в корне generated/
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path), media_type="image/png")


@app.get("/")
def index():
    """SPA: отдаём index.html."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Static files not found")
    return FileResponse(index_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
