# -*- coding: utf-8 -*-
"""
Скрипт для сохранения cookies (storage state) после ручного входа на сайт.
Запускает браузер, открывает URL; вы вручную логинитесь, затем нажимаете Enter —
скрипт сохраняет cookies в файл. Этот файл потом можно подставлять в автопостинг
(Playwright load storage_state) и не вводить пароль при каждом запуске.

Использование:
    # Дзен (по умолчанию), Яндекс.Браузер
    python docs/scripts/scripts/capture_cookies.py

    # Chrome или Edge
    python docs/scripts/scripts/capture_cookies.py --browser chrome

    # Свой браузер (путь к exe)
    python docs/scripts/scripts/capture_cookies.py --browser path --executable-path "C:\\path\\to\\browser.exe"

Требования: pip install playwright. Для chromium: python -m playwright install chromium.

Если Касперский каждый раз спрашивает про микрофон: в настройках Касперского добавьте
исключение для «Управление приложениями» — разрешите доступ для python.exe или для
Yandex Browser при запуске из capture_cookies.bat, либо нажмите «Разрешить» и включите
«Запомнить выбор для этой последовательности».
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Установите Playwright: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

# Типичные пути к Яндекс.Браузеру на Windows
YANDEX_BROWSER_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe",
    Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe",
    Path("C:/Program Files (x86)/Yandex/YandexBrowser/Application/browser.exe"),
]


def get_launch_options(browser: str, executable_path: str | None):
    """Параметры launch для выбранного браузера."""
    base = {
        "headless": False,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--window-size=1920,1000",
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--disable-features=GetDisplayMedia",
            "--autoplay-policy=no-user-gesture-required",
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
        print("Яндекс.Браузер не найден. Укажите путь: --executable-path или YANDEX_BROWSER_PATH")
        sys.exit(1)
    if browser == "path" and executable_path:
        return {**base, "executable_path": executable_path}
    if browser == "path":
        print("Для --browser path укажите --executable-path")
        sys.exit(1)
    return base


async def main():
    parser = argparse.ArgumentParser(
        description="Открыть браузер, залогиниться вручную, сохранить cookies в файл."
    )
    parser.add_argument(
        "--browser",
        "-b",
        choices=["chrome", "msedge", "yandex", "chromium", "path"],
        default="chromium",
        help="Браузер: chromium (по умолчанию — без Касперского), chrome, msedge, yandex, path",
    )
    parser.add_argument(
        "--executable-path",
        help="Путь к exe браузера (для --browser yandex или path)",
    )
    parser.add_argument(
        "--url",
        default="https://passport.yandex.ru/auth?retpath=https%3A%2F%2Fzen.yandex.ru",
        help="URL страницы входа (по умолчанию: форма входа Яндекса с возвратом в Дзен)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="zen_storage_state.json",
        help="Путь к файлу, куда сохранить cookies (по умолчанию zen_storage_state.json)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120_000,
        help="Таймаут навигации в мс (по умолчанию 120000)",
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Постоянный профиль — окно не в режиме инкогнито
    profile_dir = output_path.parent / ".browser_profile_capture"
    profile_dir.mkdir(parents=True, exist_ok=True)

    launch_opts = get_launch_options(args.browser, args.executable_path)
    print("Запуск браузера:", args.browser, "(обычный профиль)...")
    print("  Если Касперский спросит про микрофон — нажмите «Разрешить» и отметьте «Запомнить выбор».")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            **launch_opts,
            viewport=None,
            locale="ru-RU",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            device_scale_factor=1,
            accept_downloads=False,
        )
        context.set_default_timeout(args.timeout)
        # Используем уже открытую вкладку (не new_page), чтобы не было двух вкладок и «съехавшей» верстки
        page = context.pages[0] if context.pages else await context.new_page()
        print()
        print("  Окно браузера открыто. Если Касперский спросил про микрофон — нажмите «Разрешить» и «Запомнить».")
        print("  Через 5 секунд откроется страница входа...")
        await asyncio.sleep(5)
        for attempt in range(1, 4):
            try:
                await page.goto(args.url, wait_until="domcontentloaded", timeout=args.timeout)
                break
            except Exception as e:
                print("  Попытка", attempt, "перехода на страницу входа не удалась:", e)
                if attempt < 3:
                    print("  Повтор через 10 секунд (закройте окно Касперского, если мешает)...")
                    await asyncio.sleep(10)
                else:
                    print("  Откройте вручную:", args.url)
        print()
        print("  Браузер открыт. Залогиньтесь в аккаунт в открывшемся окне.")
        print("  Когда закончите (увидите главную / кабинет), вернитесь сюда и нажмите Enter.")
        print()
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: input("  Нажмите Enter после входа в аккаунт >>> "),
        )
        await context.storage_state(path=str(output_path))
        await context.close()

    abs_path = output_path.resolve()
    size = abs_path.stat().st_size if abs_path.exists() else 0
    print()
    print("Сессия сохранена в:", abs_path)
    print("Размер файла:", size, "байт. При проверке используйте этот же путь.")
    print("Используйте этот файл в автопостинге (STORAGE_STATE или --storage-state).")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
