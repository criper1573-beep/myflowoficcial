# -*- coding: utf-8 -*-
"""Конфигурация блока Script Board."""
import os
from pathlib import Path

BLOCK_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BLOCK_DIR / "frontend"
# После npm run build статика в dist; для разработки можно использовать frontend/dist
STATIC_DIR = BLOCK_DIR / "dist"
if not STATIC_DIR.exists():
    STATIC_DIR = FRONTEND_DIR / "dist"

# Хранилище проектов на сервере (один JSON-файл).
# SCRIPT_BOARD_STORAGE переопределяет каталог (тесты и нестандартный путь).
_DEFAULT_STORAGE_DIR = BLOCK_DIR / "storage"
STORAGE_DIR = _DEFAULT_STORAGE_DIR
PROJECTS_FILE = STORAGE_DIR / "projects.json"


def get_storage_dir() -> Path:
    override = (os.getenv("SCRIPT_BOARD_STORAGE") or "").strip()
    if override:
        return Path(override)
    return _DEFAULT_STORAGE_DIR


def get_projects_file() -> Path:
    return get_storage_dir() / "projects.json"


def get_history_dir() -> Path:
    return get_storage_dir() / "history"
