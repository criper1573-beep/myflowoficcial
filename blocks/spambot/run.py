# -*- coding: utf-8 -*-
"""
Точка входа NewsBot (спамбот). Запуск: python -m blocks.spambot [--project flowcabinet]

Использование:
    python -m blocks.spambot --project flowcabinet
    python -m blocks.spambot
    python -m blocks.spambot --list-projects
    python -m blocks.spambot --no-project
"""
import os
import sys
import argparse
from pathlib import Path

# Корень проекта (родитель blocks/)
_project_root = Path(__file__).resolve().parent.parent.parent


def _ensure_project_root():
    os.chdir(_project_root)
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    try:
        from dotenv import load_dotenv
        _env = _project_root / ".env"
        if _env.exists():
            load_dotenv(_env)
    except ImportError:
        pass


def _run_with_project(project_id: str) -> int:
    from blocks.projects import get_telegram_config, get_spambot_overrides, get_project_name
    from blocks.spambot import NewsBot
    from blocks.spambot.newsbot import NewsBotConfig

    tg = get_telegram_config(project_id)
    bot_token = tg.get("bot_token") or ""
    channel_id = tg.get("channel_id") or ""

    if not bot_token or not channel_id:
        print(f"\n❌ ОШИБКА: В проекте '{project_id}' не заданы telegram.bot_token или telegram.channel_id.")
        print("   Check file blocks/projects/data/{}.yaml".format(project_id))
        return 1

    overrides = get_spambot_overrides(project_id)
    config_dict = {"bot_token": bot_token, "channel_id": channel_id, **overrides}
    config = NewsBotConfig(**config_dict)
    name = get_project_name(project_id)

    print("=" * 60)
    print("NewsBot - RSS бот для Telegram")
    print("Проект:", name, f"({project_id})")
    print("=" * 60)
    print(f"\n✅ Токен бота: {bot_token[:10]}...")
    print(f"✅ Канал: {channel_id}")
    print("\nЗапуск бота...\n")

    try:
        bot = NewsBot(config=config)
        bot.start()
    except KeyboardInterrupt:
        print("\n\n✅ Бот остановлен пользователем")
        return 0
    except Exception as e:
        print(f"\n\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


def _run_with_env() -> int:
    from blocks.spambot import NewsBot

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    if not bot_token:
        print("\n❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")
        print("   Используйте --project <id> или задайте в .env")
        return 1
    if not channel_id:
        print("\n❌ ОШИБКА: Переменная TELEGRAM_CHANNEL_ID не установлена!")
        print("   Используйте --project <id> или задайте в .env")
        return 1

    print("=" * 60)
    print("NewsBot - RSS бот для Telegram")
    print("=" * 60)
    print(f"\n✅ Токен бота: {bot_token[:10]}...")
    print(f"✅ Канал: {channel_id}")
    print("\nЗапуск бота...\n")

    try:
        bot = NewsBot(bot_token=bot_token, channel_id=channel_id)
        bot.start()
    except KeyboardInterrupt:
        print("\n\n✅ Бот остановлен пользователем")
        return 0
    except Exception as e:
        print(f"\n\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


def main():
    _ensure_project_root()

    parser = argparse.ArgumentParser(description="Run NewsBot for a project or from .env")
    parser.add_argument("--project", "-p", metavar="ID", help="Project ID (file in blocks/projects/data/<id>.yaml)")
    parser.add_argument("--list-projects", "-l", action="store_true", help="List projects and exit")
    parser.add_argument("--no-project", action="store_true", help="Ignore projects, use TELEGRAM_* from .env")
    args = parser.parse_args()

    if args.list_projects:
        try:
            from blocks.projects import list_projects, get_project_name
            ids = list_projects()
            if not ids:
                print("No projects found. Add YAML to blocks/projects/data/")
                return 0
            print("Доступные проекты:")
            for pid in ids:
                print("  ", pid, "-", get_project_name(pid))
            return 0
        except Exception as e:
            print("Ошибка при загрузке проектов:", e)
            return 1

    if args.no_project:
        return _run_with_env()

    project_id = args.project or os.getenv("PROJECT_ID")
    if project_id:
        try:
            return _run_with_project(project_id)
        except FileNotFoundError:
            print("\n❌ ОШИБКА: Проект не найден:", project_id)
            print("   File: blocks/projects/data/{}.yaml".format(project_id))
            print("   Список проектов: python -m blocks.spambot --list-projects")
            return 1
        except Exception as e:
            print("\n❌ ОШИБКА при загрузке проекта:", e)
            import traceback
            traceback.print_exc()
            return 1
    return _run_with_env()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("\n❌ Критическая ошибка:", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
