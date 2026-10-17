# -*- coding: utf-8 -*-
"""Запуск доски скриптов: python -m blocks.script_board"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass

import uvicorn

from blocks.script_board.api import app

HOST = os.getenv("SCRIPT_BOARD_HOST", "127.0.0.1")
PORT = int(os.getenv("SCRIPT_BOARD_PORT", "8780"))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
