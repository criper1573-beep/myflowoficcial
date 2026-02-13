# -*- coding: utf-8 -*-
"""
Вспомогательные функции для Playwright-скриптов (Дзен, Яндекс и др.).
Используются в verify_cookies.py и в блоках автопостинга.
"""
from __future__ import annotations


async def dismiss_yandex_default_search_modal(page, timeout_ms: int = 5000) -> bool:
    """
    Закрывает модалку «Яндекс станет основным поиском» на dzen.ru / zen.yandex.ru,
    если она появилась. Иначе кнопки страницы перекрыты и скрипт не видит элементы.

    Возвращает True, если модалка была найдена и закрыта, иначе False.
    Не бросает исключений — при ошибке просто возвращает False.
    """
    try:
        # Кнопка «Закрыть» в углу модалки (текст или aria-label)
        close = page.get_by_role("button", name="Закрыть")
        await close.click(timeout=timeout_ms)
        return True
    except Exception:
        pass
    try:
        close = page.locator("[aria-label='Закрыть']").first
        await close.click(timeout=timeout_ms)
        return True
    except Exception:
        pass
    try:
        # Модалка с заголовком «Яндекс станет основным поиском» — ищем крестик внутри
        modal = page.get_by_text("Яндекс станет основным поиском", exact=False)
        if await modal.is_visible():
            # Крестик часто в кнопке или в элементе с role=button
            x_btn = modal.locator("button").first
            await x_btn.click(timeout=timeout_ms)
            return True
    except Exception:
        pass
    return False
