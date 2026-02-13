#!/usr/bin/env python3
"""Print Telegram bot username from TELEGRAM_BOT_TOKEN in .env."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
try:
    from dotenv import load_dotenv
    load_dotenv(root / ".env")
except ImportError:
    pass

token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
if not token:
    sys.exit(1)
try:
    import urllib.request
    import json
    req = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    data = json.loads(req.read())
    print((data.get("result") or {}).get("username", ""))
except Exception:
    sys.exit(2)
