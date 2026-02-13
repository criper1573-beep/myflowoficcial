# -*- coding: utf-8 -*-
"""Конфигурация блока автопостинга Дзен из .env корня проекта."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Сессия Дзена (куки) — по умолчанию в корне проекта
_STORAGE = os.getenv("ZEN_STORAGE_STATE", "zen_storage_state.json")
STORAGE_STATE_PATH = (PROJECT_ROOT / _STORAGE).resolve() if not os.path.isabs(_STORAGE) else Path(_STORAGE)

# URL студии Дзена (редактор статей)
EDITOR_URL = os.getenv("ZEN_EDITOR_URL", "https://dzen.ru/profile/editor/flowcabinet")

# Браузер
HEADLESS = os.getenv("ZEN_HEADLESS", "false").lower() in ("1", "true", "yes")
BROWSER_TIMEOUT_MS = int(os.getenv("ZEN_BROWSER_TIMEOUT", "60000"))
KEEP_BROWSER_OPEN = os.getenv("ZEN_KEEP_OPEN", "false").lower() in ("1", "true", "yes")
