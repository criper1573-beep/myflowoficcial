# -*- coding: utf-8 -*-
"""
Блок Post FLOW — генерация и публикация постов в канал FLOW из тем в Google Таблице.

Один запуск = один пост: тема из таблицы → GRS AI (заголовок + текст + картинка) → Telegram.
"""
from blocks.post_flow.bot import main as run_one_post

__all__ = ["run_one_post"]
