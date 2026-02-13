# -*- coding: utf-8 -*-
"""Запуск дашборда: python -m blocks.analytics -> http://localhost:8050"""
import sys
from pathlib import Path

# Корень проекта в path для импорта blocks
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from blocks.analytics.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="info")
