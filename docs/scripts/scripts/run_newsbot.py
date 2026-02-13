# -*- coding: utf-8 -*-
"""
Точка входа NewsBot — перенаправление в блок спамбота.
Запуск: python docs/scripts/scripts/run_newsbot.py [--project flowcabinet]
(из корня проекта). Или используйте: python -m blocks.spambot
"""
import sys
import os
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
os.chdir(_root)
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blocks.spambot.run import main

if __name__ == "__main__":
    sys.exit(main())
