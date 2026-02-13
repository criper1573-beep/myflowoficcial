# -*- coding: utf-8 -*-
"""Копирование block1-4 из Cursor assets в publish/001. Запуск из корня: python -m blocks.autopost_zen.copy_blocks_to_publish_001"""
import shutil
from pathlib import Path

BLOCK_DIR = Path(__file__).resolve().parent
ASSETS = Path(r"C:\Users\bbru7\.cursor\projects\c-Users-bbru7-Desktop\assets")
DEST_DIR = BLOCK_DIR / "publish" / "001"
FILES = [
    "trends_office_2026_block1.png",
    "trends_office_2026_block2.png",
    "trends_office_2026_block3.png",
    "trends_office_2026_block4.png",
]

DEST_DIR.mkdir(parents=True, exist_ok=True)
for name in FILES:
    src = ASSETS / name
    if src.exists():
        shutil.copy2(src, DEST_DIR / name)
        print("OK:", name)
    else:
        print("Skip (not found):", name)
