# -*- coding: utf-8 -*-
"""Конфигурация блока Post FLOW из переменных окружения и .env корня проекта."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта ContentZavod (родитель папки blocks)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Google Sheets (таблица: Посты для канала FLOW)
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1gxYpX1FGm5VwtyUoZNKdd8EVYduvkmULpXL5TuOv5z4")
_creds = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_CREDENTIALS_PATH = str(BLOCK_DIR / _creds) if not os.path.isabs(_creds) else _creds
TOPICS_SHEET_NAME = os.getenv("TOPICS_SHEET_NAME", "Лист1")

# GRS AI (общий с ContentZavod)
GRS_AI_API_KEY = (os.getenv("GRS_AI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
MODEL_GENERATION = os.getenv("MODEL_GENERATION", "gemini-3-pro")
MODEL_FALLBACK = os.getenv("MODEL_FALLBACK", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "nano-banana")

# Telegram (канал FLOW)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@myflowofficial")
