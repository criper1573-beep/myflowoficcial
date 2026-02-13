# -*- coding: utf-8 -*-
"""Работа с Google Таблицей: получение и удаление тем."""
import os

import gspread
from google.oauth2.service_account import Credentials

from blocks.post_flow import config as config_module

config = config_module


def get_sheets_client():
    """Создаёт клиент gspread с сервисным аккаунтом."""
    path = config.GOOGLE_CREDENTIALS_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Файл ключей Google не найден: {path}\n"
            "Создайте сервисный аккаунт в Google Cloud Console (APIs & Services -> Credentials),\n"
            "скачайте JSON и сохраните как blocks/post_flow/credentials.json\n"
            "или укажите путь в .env: GOOGLE_CREDENTIALS_PATH=путь/к/файлу.json"
        )
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(path, scopes=scopes)
    return gspread.authorize(creds)


def get_first_topic():
    """
    Берёт ровно одну (первую) тему из листа — первая непустая ячейка в колонке A.
    Дополнительный контекст — из колонки B (та же строка).
    Returns: (topic: str, extra_context: str, row_index: int) или (None, None, None) если тем нет.
    """
    if not config.GOOGLE_SHEET_ID:
        raise ValueError("GOOGLE_SHEET_ID не задан в .env")
    client = get_sheets_client()
    sheet = client.open_by_key(config.GOOGLE_SHEET_ID).worksheet(config.TOPICS_SHEET_NAME)
    col_a = sheet.col_values(1)
    col_b = sheet.col_values(2)
    for i, cell in enumerate(col_a, start=1):
        val = (cell or "").strip()
        if val:
            extra = (col_b[i - 1] if i <= len(col_b) else "").strip()
            return val, extra, i
    return None, None, None


def delete_topic_row(row_index: int):
    """Удаляет строку с темой (по индексу строки, 1-based)."""
    client = get_sheets_client()
    sheet = client.open_by_key(config.GOOGLE_SHEET_ID).worksheet(config.TOPICS_SHEET_NAME)
    sheet.delete_rows(row_index)
