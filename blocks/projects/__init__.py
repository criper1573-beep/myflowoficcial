# -*- coding: utf-8 -*-
"""
Блок «Проекты» — конфигурация по каждому бизнес-проекту.

Один ContentZavod обслуживает несколько проектов. У каждого проекта свои
аккаунты (Telegram, VK, Дзен и т.д.), общий API ИИ задаётся в .env.
"""

from blocks.projects.loader import (
    list_projects,
    load_project_config,
    get_telegram_config,
    get_spambot_overrides,
    get_project_name,
)

__all__ = [
    "list_projects",
    "load_project_config",
    "get_telegram_config",
    "get_spambot_overrides",
    "get_project_name",
]
