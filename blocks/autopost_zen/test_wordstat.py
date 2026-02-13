# -*- coding: utf-8 -*-
"""Тест Вордстата: подбор ключевых фраз по запросу."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from blocks.autopost_zen.wordstat_client import fetch_top_phrases, get_wordstat_token

def main():
    query = "ремонт офисов"
    print("Запрос:", query)
    if not get_wordstat_token():
        print("Ошибка: YANDEX_WORDSTAT_TOKEN не задан в .env")
        return 1
    print("Запрашиваю топ-фразы в Вордстате (может занять 1–2 мин)...")
    phrases = fetch_top_phrases([query])
    if not phrases:
        print("Фраз не получено (API недоступен или пустой отчёт).")
        return 0
    print("Получено фраз:", len(phrases))
    for i, p in enumerate(phrases[:30], 1):
        print(f"  {i}. {p}")
    if len(phrases) > 30:
        print("  ... и ещё", len(phrases) - 30)
    return 0

if __name__ == "__main__":
    sys.exit(main())
