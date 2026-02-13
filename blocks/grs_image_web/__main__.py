# -*- coding: utf-8 -*-
"""Запуск веб-сервера генерации изображений (локально или на сервере)."""
import os
import sys

# Корень проекта для загрузки .env и импорта blocks
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass

import uvicorn
from blocks.grs_image_web.api import app

HOST = os.getenv("GRS_IMAGE_WEB_HOST", "127.0.0.1")
PORT = int(os.getenv("GRS_IMAGE_WEB_PORT", "8765"))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
