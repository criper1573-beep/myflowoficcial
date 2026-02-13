# -*- coding: utf-8 -*-
"""Лаунчер публикации в Дзен. Запуск: python docs/scripts/scripts/run_zen_publish.py [--publish]"""
import os
import sys

# 4 уровня вверх: scripts -> scripts -> docs -> ContentZavod
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if "--publish" not in sys.argv and "-p" not in sys.argv:
    sys.argv.append("--publish")
if "--file" not in sys.argv and "-f" not in sys.argv:
    sys.argv.extend(["--file", os.path.join(ROOT, "blocks", "autopost_zen", "articles", "office_remont_expanded.json")])

from blocks.autopost_zen.main import main
sys.exit(main())
