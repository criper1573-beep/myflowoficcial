# -*- coding: utf-8 -*-
"""
Загрузчик конфигурации проектов.

Reads YAML files from data/ and returns config by project_id.
Общие ключи (например GRS_AI) берутся из .env, проектные — из YAML проекта.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

# Папка с конфигами проектов (рядом с этим файлом)
_DATA = Path(__file__).resolve().parent / "data"


def _data_path() -> Path:
    """Path to project YAML folder."""
    return _DATA


def list_projects() -> List[str]:
    """
    Список идентификаторов проектов (имена YAML без расширения, кроме *.example).
    
    Returns:
        Список project_id, например ['flowcabinet', 'other_project'].
    """
    data_dir = _data_path()
    if not data_dir.is_dir():
        return []
    result = []
    for f in data_dir.glob("*.yaml"):
        if f.suffix.lower() == ".yaml" and ".example" not in f.name.lower():
            result.append(f.stem)
    for f in data_dir.glob("*.yml"):
        if f.suffix.lower() == ".yml" and ".example" not in f.name.lower():
            result.append(f.stem)
    return sorted(result)


def load_project_config(project_id: str) -> Dict[str, Any]:
    """
    Загрузить конфигурацию проекта по его ID.
    
    Args:
        project_id: Идентификатор проекта (имя файла без расширения).
        
    Returns:
        Словарь конфигурации (содержимое YAML). Верхний уровень: project_id, name, telegram, spambot, ...
        
    Raises:
        FileNotFoundError: Если файл проекта не найден.
        ValueError: Если YAML не установлен.
    """
    if yaml is None:
        raise ValueError("Установите PyYAML: pip install pyyaml")
    
    data_dir = _data_path()
    for ext in (".yaml", ".yml"):
        path = data_dir / f"{project_id}{ext}"
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                data = {}
            data.setdefault("project_id", project_id)
            return data
    
    raise FileNotFoundError(f"Проект не найден: {project_id}. Файл: {data_dir / (project_id + '.yaml')}")


def get_telegram_config(project_id: str) -> Dict[str, str]:
    """
    Получить только Telegram-настройки проекта (bot_token, channel_id).
    
    Returns:
        {'bot_token': '...', 'channel_id': '...'}
    """
    config = load_project_config(project_id)
    telegram = config.get("telegram") or {}
    bot_token = telegram.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = telegram.get("channel_id") or os.getenv("TELEGRAM_CHANNEL_ID")
    return {"bot_token": bot_token or "", "channel_id": channel_id or ""}


def get_spambot_overrides(project_id: str) -> Dict[str, Any]:
    """
    Получить переопределения для NewsBot из конфига проекта.
    
    Возвращает только те ключи, которые есть в конфиге проекта (spambot.*).
    Подходит для передачи в NewsBotConfig после bot_token и channel_id.
    
    Returns:
        Словарь полей для NewsBotConfig: cta_text, cta_link, hashtag_options, priority_words, rss_feeds, ...
    """
    config = load_project_config(project_id)
    spambot = config.get("spambot")
    if not spambot or not isinstance(spambot, dict):
        return {}
    
    # Allowed NewsBotConfig fields (see blocks.spambot.newsbot.NewsBotConfig)
    allowed = {
        "cta_text", "cta_link", "hashtag_options", "hashtags_per_post",
        "priority_words", "rss_feeds", "rss_feeds_fallback",
        "send_interval", "max_caption_length", "repost_after_seconds",
        "last_posted_max", "history_file", "max_post_age_seconds", "sleep_when_no_post",
        "max_retries", "retry_base_delay", "user_agent",
    }
    return {k: v for k, v in spambot.items() if k in allowed}


def get_project_name(project_id: str) -> str:
    """Название проекта для отображения."""
    try:
        config = load_project_config(project_id)
        return config.get("name") or project_id
    except Exception:
        return project_id
