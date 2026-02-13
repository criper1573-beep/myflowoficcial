# -*- coding: utf-8 -*-
"""Одноразовый запуск публикации article_trends_office_2026.json."""
import os
import sys
import json
import asyncio

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from blocks.autopost_zen.zen_client import run_post_flow

article_path = os.path.join(ROOT, "blocks", "autopost_zen", "articles", "article_trends_office_2026.json")
with open(article_path, encoding="utf-8") as f:
    data = json.load(f)
data["publish"] = True

exit_code, msg = asyncio.run(run_post_flow(data, publish=True, headless=False, keep_open=False))
print(msg)
sys.exit(exit_code)
