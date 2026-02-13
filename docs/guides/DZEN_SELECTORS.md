# Селекторы Яндекс.Дзен для Playwright

Используются **только** эти селекторы в `blocks/autopost_zen/zen_client.py` (словарь `DZEN`). Дубли и старые селекторы удалены.

## Закрытие попапов

- **Попап донатов:** `[data-testid="donations-promo-banner-popup"]`, внутри кнопка `[data-testid="close-button"]`
- **Универсально закрыть:** `[data-testid="close-button"]`

## Главная → редактор статьи

- **Кнопка «Добавить публикацию» (плюс):** `[data-testid="add-publication-button"]`
- **«Написать статью»:** `[aria-label="Написать статью"]`

## Поля редактора

- **Заголовок:** `div.article-editor-desktop--editor__titleInput-2D`
- **Основной текст:** `div.article-editor-desktop--zen-draft-editor__zenEditor-13`

## Форматирование (только getByRole)

- **H2:** `page.get_by_role('button', { name: 'Heading 2' })`
- **H3:** `page.get_by_role('button', { name: 'Heading 3' })`
- **Жирный:** `page.get_by_role('button', { name: 'Bold' })`
- **Курсив:** `page.get_by_role('button', { name: 'Italic' })`
- **Зачёркивание:** `page.get_by_role('button', { name: 'Strike' })`
- **Цитата:** `page.get_by_role('button', { name: 'Blockquote' })`
- **Список UL:** `page.get_by_role('button', { name: 'ul' })`
- **Список OL:** `page.get_by_role('button', { name: 'ol' })`

## Картинки

- **Вставить изображение:** `button[data-tip='Вставить изображение']`

## Кнопки

- **Опубликовать:** `[data-testid='article-publish-btn']`
- **Закрыть донат-попап:** `[data-testid='close-button']`

## Панели

- **Панель инструментов:** `div.article-editor-desktop--editor-toolbar__editorToolbar-15`
- **Ссылка:** `div.article-editor-desktop--editor-toolbar__linkTools-9h`

## Правила (реализовано в zen_client)

1. **Не использовать Markdown `#` / `##`** для заголовков — редактор Дзена не парсит их как H2/H3. Заголовки только через меню: getByRole(button, "Heading 2") / "Heading 3".
2. **Не использовать Ctrl+A** в теле статьи. Выделение строки: `Ctrl+Right` → `Shift+Ctrl+Left` (`_select_current_line_keyboard`).
3. **ENTER x2** между блоками и перед/после картинок.
4. **Ждать появление панели** перед выбором типа блока: `DZEN["toolbar"]` с `wait_for(state="visible")`.
