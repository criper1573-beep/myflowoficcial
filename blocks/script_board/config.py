# -*- coding: utf-8 -*-
"""Конфигурация блока Script Board."""
from pathlib import Path

BLOCK_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BLOCK_DIR / "frontend"
# После npm run build статика в dist; для разработки можно использовать frontend/dist
STATIC_DIR = BLOCK_DIR / "dist"
if not STATIC_DIR.exists():
    STATIC_DIR = FRONTEND_DIR / "dist"

# Хранилище проектов на сервере (один JSON-файл)
STORAGE_DIR = BLOCK_DIR / "storage"
PROJECTS_FILE = STORAGE_DIR / "projects.json"
