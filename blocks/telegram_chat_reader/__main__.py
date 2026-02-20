# -*- coding: utf-8 -*-
"""CLI: авторизация и выгрузка истории чата."""
import argparse
import asyncio
import os
import sys
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


def main():
    parser = argparse.ArgumentParser(
        description="Чтение истории Telegram-чатов (Telethon). Чат: @username или t.me/username"
    )
    sub = parser.add_subparsers(dest="cmd", help="Команда")

    login_p = sub.add_parser("login", help="Авторизация по номеру телефона (однократно)")
    login_p.set_defaults(cmd="login")

    fetch_p = sub.add_parser("fetch", help="Выгрузить историю в JSON")
    fetch_p.add_argument("entity", help="Чат: zakazyff, @zakazyff или t.me/zakazyff")
    fetch_p.add_argument("-n", "--limit", type=int, default=100, help="Макс. сообщений (по умолч. 100)")
    fetch_p.add_argument("-o", "--output", help="Файл для сохранения JSON")
    fetch_p.set_defaults(cmd="fetch")

    monitor_p = sub.add_parser("monitor", help="Мониторинг: ловить новые сообщения, анализировать, слать уведомления")
    monitor_p.set_defaults(cmd="monitor")

    args = parser.parse_args()

    if args.cmd == "login":
        from blocks.telegram_chat_reader.client import login_interactive
        asyncio.run(login_interactive())
        return

    if args.cmd == "fetch":
        from blocks.telegram_chat_reader.client import run_fetch
        entity = args.entity.strip()
        if entity.startswith("https://t.me/"):
            entity = entity.replace("https://t.me/", "").strip("/")
        if entity.startswith("t.me/"):
            entity = entity.replace("t.me/", "").strip("/")
        if entity.startswith("@"):
            entity = entity[1:]
        try:
            msgs = run_fetch(entity, limit=args.limit, output=args.output)
            print(f"Получено {len(msgs)} сообщений из {entity}")
            if not args.output:
                for m in msgs[:5]:
                    print(f"  [{m.get('date')}] {m.get('text', '')[:80]}...")
                if len(msgs) > 5:
                    print(f"  ... и ещё {len(msgs) - 5}")
        except (ValueError, RuntimeError) as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.cmd == "monitor":
        from blocks.telegram_chat_reader.channel_monitor import main as monitor_main
        monitor_main()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
