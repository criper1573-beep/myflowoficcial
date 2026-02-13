# -*- coding: utf-8 -*-
"""
Watchdog: проверка systemd-сервисов раз в CHECK_INTERVAL сек.
Если сервис не active — отправка уведомления в Telegram и попытка перезапуска.

Требуется в .env:
  TELEGRAM_BOT_TOKEN — токен бота
  TELEGRAM_ALERT_CHAT_ID — id чата (или канала) для алертов

Запуск: python -m blocks.analytics.watchdog_services
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

CHECK_INTERVAL = int(os.getenv("WATCHDOG_INTERVAL", "90"))
# Те же сервисы, что на дашборде (кроме самого watchdog).
SERVICES = [
    ("analytics-dashboard", "Дашборд аналитики"),
    ("analytics-telegram-bot", "Telegram-бот дашборда"),
    ("grs-image-web", "Генерация картинок и ссылок"),
    ("spambot", "Спамбот (NewsBot)"),
]
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID")


def is_active(unit: str) -> bool:
    try:
        out = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() == "active"
    except Exception:
        return False


def restart_service(unit: str) -> bool:
    try:
        subprocess.run(
            ["systemctl", "restart", unit],
            capture_output=True,
            timeout=15,
        )
        return True
    except Exception:
        return False


def send_telegram(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": "true"}).encode()
        req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    if sys.platform != "linux":
        print("Watchdog только для Linux (systemctl). Выход.")
        sys.exit(0)
    if not BOT_TOKEN or not CHAT_ID:
        print("Задайте TELEGRAM_BOT_TOKEN и TELEGRAM_ALERT_CHAT_ID в .env для уведомлений.")
    while True:
        for unit, label in SERVICES:
            if not is_active(unit):
                msg = f"⚠️ Сервис упал: {label} ({unit})"
                send_telegram(msg)
                if restart_service(unit):
                    send_telegram(f"🔄 Перезапущен: {label} ({unit})")
                else:
                    send_telegram(f"❌ Не удалось перезапустить: {label} ({unit})")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
