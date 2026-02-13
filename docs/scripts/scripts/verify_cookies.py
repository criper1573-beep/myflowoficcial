# -*- coding: utf-8 -*-
"""
Проверка входа по сохранённым cookies: открывает браузер с storage_state,
переходит на Дзен — вы должны увидеть себя залогиненным.

Загружает сессию из файла через storage_state (куки + localStorage), чтобы вход
восстанавливался корректно. Размер окна 1920x1000 (экран 1080p: запас под панель задач, низ не обрезает).

Запуск: python docs/scripts/scripts/verify_cookies.py [--browser chrome|msedge|yandex|chromium]
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from playwright_helpers import dismiss_yandex_default_search_modal

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Установите Playwright: python -m pip install playwright && python -m playwright install chromium")
    sys.exit(1)

# Путь к zen_storage_state.json (корень проекта = на 3 уровня выше)
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DEFAULT_STORAGE = PROJECT_ROOT / "zen_storage_state.json"

YANDEX_BROWSER_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe",
    Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe",
    Path("C:/Program Files (x86)/Yandex/YandexBrowser/Application/browser.exe"),
]


def get_launch_options(browser: str, executable_path: str | None):
    """Опции запуска. Окно 1920x1000 — влезает в экран 1080p с учётом панели задач, низ не обрезает."""
    base = {
        "headless": False,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--window-size=1920,1000",
        ],
    }
    if browser == "chrome":
        return {**base, "channel": "chrome"}
    if browser == "msedge":
        return {**base, "channel": "msedge"}
    if browser == "yandex":
        path = executable_path or os.environ.get("YANDEX_BROWSER_PATH")
        if path and Path(path).exists():
            return {**base, "executable_path": path}
        for p in YANDEX_BROWSER_PATHS:
            if p.exists():
                return {**base, "executable_path": str(p)}
        print("Яндекс.Браузер не найден. Укажите --executable-path или YANDEX_BROWSER_PATH")
        sys.exit(1)
    if browser == "path" and executable_path:
        return {**base, "executable_path": executable_path}
    if browser == "path":
        print("Для --browser path укажите --executable-path")
        sys.exit(1)
    return base


async def main():
    parser = argparse.ArgumentParser(description="Проверка входа по сохранённым cookies.")
    parser.add_argument(
        "--browser", "-b",
        choices=["chrome", "msedge", "yandex", "chromium", "path"],
        default="chrome",
        help="Браузер: chrome, msedge, yandex, chromium, path",
    )
    parser.add_argument("--executable-path", help="Путь к exe (для yandex/path)")
    parser.add_argument(
        "--storage", "-s",
        default=None,
        help="Путь к zen_storage_state.json (по умолчанию: корень проекта)",
    )
    parser.add_argument(
        "--url", "-u",
        default="https://zen.yandex.ru",
        help="URL для открытия (по умолчанию: главная Дзена; студия: https://dzen.ru/profile/editor/flowcabinet)",
    )
    args = parser.parse_args()

    storage_path = (Path(args.storage).resolve() if args.storage else DEFAULT_STORAGE.resolve())
    if not storage_path.exists():
        print("Файл сессии не найден:", storage_path)
        print("Сначала запустите capture_cookies.bat, залогиньтесь и сохраните. Путь будет в выводе.")
        return 1

    size = storage_path.stat().st_size
    print("Загружаю сессию из:", storage_path)
    print("Размер файла:", size, "байт")
    launch_opts = get_launch_options(args.browser, args.executable_path)
    print("Запуск браузера", args.browser, "...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_opts)
        context = await browser.new_context(
            storage_state=str(storage_path.resolve()),
            viewport=None,
            locale="ru-RU",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto(args.url, wait_until="domcontentloaded")
        await asyncio.sleep(1)
        if "zen.yandex.ru" in args.url or "dzen.ru" in args.url:
            if await dismiss_yandex_default_search_modal(page):
                print("Модалка «Яндекс станет основным поиском» закрыта.")
        await asyncio.sleep(0.5)
        print("Открыт:", args.url)
        print("Проверьте: вы должны быть залогинены.")
        print("Браузер закроется через 45 секунд...")
        await asyncio.sleep(45)
        await browser.close()

    print("Готово.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
