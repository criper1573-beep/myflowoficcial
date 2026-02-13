# -*- coding: utf-8 -*-
"""Однократное копирование обложки из Cursor assets в publish/001. Запуск из корня: python -m blocks.autopost_zen.copy_cover_001"""
import shutil
from pathlib import Path

BLOCK_DIR = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\bbru7\.cursor\projects\c-Users-bbru7-Desktop\assets\trends_office_2026_cover.png")
DEST = BLOCK_DIR / "publish" / "001" / "trends_office_2026_cover.png"

if SRC.exists():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DEST)
    print("OK:", DEST)
else:
    print("Source not found:", SRC)
