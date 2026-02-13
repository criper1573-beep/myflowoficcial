# -*- coding: utf-8 -*-
"""
Telegram-бот для доступа к дашборду аналитики с телефона (Mini App).
Устанавливает кнопку меню «Дашборд» (Web App) и обрабатывает /stats — кнопка «Открыть дашборд».
Требуется DASHBOARD_PUBLIC_URL (HTTPS) в .env.

Запуск: python -m blocks.analytics.telegram_bot
"""
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

# URL дашборда. HTTPS — для кнопки меню и Web App внутри Telegram; HTTP — бот пришлёт ссылку (откроется в браузере).
DASHBOARD_PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL") or os.getenv("ANALYTICS_DASHBOARD_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def set_menu_button(bot) -> None:
    """Установить кнопку меню «Дашборд» (Web App). Только для HTTPS."""
    if not DASHBOARD_PUBLIC_URL or not DASHBOARD_PUBLIC_URL.startswith("https://"):
        logger.info("DASHBOARD_PUBLIC_URL не HTTPS — кнопка меню не ставится; по /stats будет ссылка")
        return
    from telegram import MenuButtonWebApp, WebAppInfo
    await bot.set_chat_menu_button(menu_button=MenuButtonWebApp("Дашборд", WebAppInfo(url=DASHBOARD_PUBLIC_URL)))
    logger.info("Кнопка меню «Дашборд» установлена: %s", DASHBOARD_PUBLIC_URL)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env")
        sys.exit(2)

    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    from telegram.ext import Application, CommandHandler, ContextTypes

    async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not DASHBOARD_PUBLIC_URL:
            await update.effective_message.reply_text(
                "Дашборд недоступен: задайте DASHBOARD_PUBLIC_URL в .env"
            )
            return
        if DASHBOARD_PUBLIC_URL.startswith("https://"):
            keyboard = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton("Открыть дашборд", web_app=WebAppInfo(url=DASHBOARD_PUBLIC_URL))
            )
            await update.effective_message.reply_text(
                "Статистика пайплайна публикаций КонтентЗавод. Нажмите кнопку, чтобы открыть дашборд.",
                reply_markup=keyboard,
            )
        else:
            await update.effective_message.reply_text(
                f"Дашборд аналитики КонтентЗавод.\n\nОткрыть в браузере: {DASHBOARD_PUBLIC_URL}"
            )

    async def post_init(application: Application) -> None:
        await set_menu_button(application.bot)

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("analytics", cmd_stats))
    logger.info("Бот запущен. Команды: /stats, /analytics. Кнопка меню: Дашборд.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()
