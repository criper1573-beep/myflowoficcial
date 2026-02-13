# -*- coding: utf-8 -*-
"""
Бот Post FLOW: один запуск — один пост в канал @myflowofficial.
1. Берёт тему из Google Таблицы (Посты для канала FLOW)
2. Генерирует заголовок и текст (контекст FLOW + последние 10 постов)
3. Генерирует картинку (GRS AI)
4. Публикует пост в канал
5. Удаляет тему из таблицы при успешной публикации
"""
import html
import sys

from blocks.post_flow.sheets_client import get_first_topic, delete_topic_row
from blocks.post_flow.content import (
    load_previous_posts,
    save_post_to_history,
    generate_headline_and_text,
    generate_image,
)
from blocks.post_flow.telegram_client import publish_post


def build_caption(headline: str, text: str) -> str:
    """Собирает подпись к посту: жирный заголовок + текст (HTML). Лимит 1024 символа."""
    headline_esc = html.escape(headline or "", quote=False)
    text_esc = html.escape(text or "", quote=False)
    caption = f"<b>{headline_esc}</b>\n\n{text_esc}"
    if len(caption) > 1024:
        prefix = f"<b>{headline_esc}</b>\n\n"
        available = 1024 - len(prefix) - 3
        if available > 0:
            cut = text_esc[:available]
            while cut.endswith("&"):
                cut = cut[:-1]
            text_esc = cut.rstrip() + "..."
        else:
            max_headline = 1024 - 3 - 4 - 3
            headline_esc = headline_esc[:max_headline] + "..."
            text_esc = ""
        caption = f"<b>{headline_esc}</b>\n\n{text_esc}" if text_esc else f"<b>{headline_esc}</b>"
    return caption


def main():
    """Один запуск = одна тема = один пост."""
    print("Загрузка контекста: последние посты...")
    previous_posts = load_previous_posts()

    print("Получение темы из Google Таблицы...")
    topic, extra_context, row_index = get_first_topic()
    if not topic or not row_index:
        print("Нет тем для поста. Завершение.")
        return 0

    print(f"Тема: {topic}")

    headline, text = generate_headline_and_text(topic, previous_posts, extra_context)
    print("Сгенерированы заголовок и текст.")

    image_bytes = generate_image(topic, headline, text)
    print("Картинка сгенерирована.")

    caption = build_caption(headline, text)
    print("Публикация в канал...")
    publish_post(image_bytes, caption)
    print("Пост опубликован в канал.")

    print("Удаление темы из таблицы...")
    delete_topic_row(row_index)
    print("Тема удалена из таблицы.")

    save_post_to_history(headline, text)
    print("Готово.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback
        print("Ошибка:", e, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
