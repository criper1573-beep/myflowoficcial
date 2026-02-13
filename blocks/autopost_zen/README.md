# Автопостинг в Яндекс.Дзен

Публикация статей в Дзен через Playwright. Реализация по **UNIVERSAL_AUTOPOST_PROMPT**; см. `docs/guides/PLAYWRIGHT_AUTOPOST.md`. Сессия — из cookies (ZEN_STORAGE_STATE) или ZEN_EMAIL/ZEN_PASSWORD.

## Требования

- Python 3.11+
- `pip install -r blocks/autopost_zen/requirements.txt` → `playwright install chromium`
- Куки: из корня проекта `python docs/scripts/scripts/capture_cookies.py` — сохранит `zen_storage_state.json` в корень

## Запуск

По умолчанию статья **сразу публикуется** (не черновик).

```bash
# Указать файл статьи (JSON). Если файл не в publish/001, 002, … — он и все картинки переносятся в следующую папку publish/N/ и оттуда публикуются. Копии в других местах не хранятся.
python -m blocks.autopost_zen --file blocks/autopost_zen/articles/статья.json

# Публикация из уже подготовленной папки
python -m blocks.autopost_zen --file blocks/autopost_zen/publish/001/article.json

# Оставить браузер открытым
python -m blocks.autopost_zen --file ... --keep-open
```

## Конфигурация

Добавьте переменные в корневой `.env`. Пример: `blocks/autopost_zen/config.example.env`. См. `docs/rules/KEYS_AND_TOKENS.md` §8a.

## Переменные (.env в корне проекта)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `ZEN_STORAGE_STATE` | Путь к файлу сессии (куки) | `zen_storage_state.json` (в корне) |
| `ZEN_EDITOR_URL` | URL студии Дзена | `https://dzen.ru/profile/editor/flowcabinet` |
| `ZEN_HEADLESS` | Запуск браузера без окна | `false` |
| `ZEN_BROWSER_TIMEOUT` | Таймаут страницы, мс | `60000` |
| `ZEN_KEEP_OPEN` | Не закрывать браузер после заполнения | `false` |

## Папки публикаций и формат статьи

**Папки с порядковым номером:** `blocks/autopost_zen/publish/001/`, `002/`, … В каждой — только один выпуск: `article.json` и все картинки к нему. При запуске с `--file` на статью вне `publish/` скрипт создаёт следующую папку (001, 002, …), **переносит** туда JSON и все картинки из статьи и публикует оттуда. Исходный файл и картинки из старых мест удаляются — копии не хранятся.

**Локально** папки лежат относительно корня проекта (например `C:\...\КонтентЗавод\blocks\autopost_zen\publish\001\`). **На сервере** — там же относительно корня проекта на VPS, например `/root/contentzavod/blocks/autopost_zen/publish/001/`, `002/`, … Все сгенерированные статьи и картинки при запуске `--auto` с сервера сохраняются в эту папку на диске VPS.

**Формат (content_blocks для Дзен):**
- `title` — заголовок
- `content_blocks` — массив: `{"type": "image", "path": "cover.png", "caption": "..."}` и `{"type": "html", "content": "<p>...</p>"}`. Порядок: обложка → вступление → (H3 → картинка → абзац → список) × N → заключение
- `cover_image` — имя файла обложки (в той же папке, что и article.json)
- `tags` — массив тегов
- `publish` — по умолчанию статья публикуется сразу

Картинки при подготовке переносятся в папку публикации и в JSON остаются только имена файлов.

**Промпты и структура:** `docs/guides/BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md`, `docs/rules/ARTUR_HOROSHEFF_ARTICLE_PROMPT.md`, `docs/guides/ZEN_ARTICLE_STRUCTURE.md`. Примеры: `blocks/autopost_zen/articles/template.json`.

## Селекторы редактора

Используются только селекторы из документа (см. `docs/guides/DZEN_SELECTORS.md` и словарь `DZEN` в `zen_client.py`).

## Дубликаты и удаление постов

Если одна и та же статья опубликовалась несколько раз (например, из‑за повторного запуска или таймаута), лишние посты нужно удалить вручную:

1. Откройте [Дзен-студию](https://dzen.ru/profile/editor/flowcabinet) (или ваш канал).
2. Перейдите в раздел **«Публикации»** (или «Статьи»).
3. Найдите дубликаты по заголовку и откройте меню (три точки) у каждой лишней публикации → **«Удалить»**.

В коде добавлена защита от двойного нажатия «Опубликовать»: после подтверждения в модалке скрипт ждёт закрытия диалога и не кликает по кнопкам вне модалки.

## Капча

При открытии студии Дзен может показать SmartCaptcha («Вы не робот?»). Скрипт ждёт 90 секунд на ручное решение; при необходимости увеличьте `CAPTCHA_WAIT_SEC` в `zen_client.py`.
