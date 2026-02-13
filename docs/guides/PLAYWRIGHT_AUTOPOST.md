# Автопостинг через Playwright

Единая документация по реализации автопостинга в соцсетях через **Playwright** (браузерная автоматизация). Используйте при добавлении новой площадки (vc.ru, Дзен, ВК, Pinterest).

**Референс:** `UNIVERSAL_AUTOPOST_PROMPT.md` (на рабочем столе или в репозитории) — подробная инструкция по настройке, исследованию площадки, шаблону кода клиента, видео, отладке.

---

## 1. Подход

- **Только Playwright** — работа через веб-интерфейс. API не использовать, если нет стабильного публичного API.
- **ОС:** Windows 10/11, PowerShell/CMD. **Python:** 3.11+.
- **Конфиги:** `.env` в корне через `python-dotenv`. Переменные — в `docs/rules/KEYS_AND_TOKENS.md`.
- **UTF-8:** в начале скрипта `sys.stdout.reconfigure(encoding='utf-8')`, иначе кириллица в логах → `????`.

---

## 2. Исследование веб-интерфейса

Перед написанием кода обязательно исследовать площадку (вручную или через MCP browser — [MCP_BROWSER.md](MCP_BROWSER.md)).

### 2.1. Страница входа

```
ВОПРОСЫ:
1. Какой URL страницы входа/регистрации?
2. Какие поля на форме? (email, пароль, телефон)
3. Есть ли 2FA? CAPTCHA?
4. Какие cookies устанавливаются после входа?
```

### 2.2. Страница создания поста

```
ВОПРОСЫ:
1. Какой URL создания поста/статьи?
2. Какие поля? (заголовок, текст, теги, изображения, видео)
3. Какой редактор? (Quill, TinyMCE, ProseMirror, Draft.js, contenteditable)
4. Есть ли скрытые поля (hidden inputs)?
5. Как сохраняется контент? (автосохранение, кнопка, AJAX)
6. Есть ли sidebar с настройками?
7. Как загружаются изображения/видео?
```

### 2.3. Сеть

- Какие запросы уходят при публикации?
- Есть ли API публикации? Можно ли вызывать через `context.request`, а не `fetch` (CORS)?

**MCP tools:** `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill`, `browser_network`.

---

## 3. Стек и зависимости

**Фиксированный стек:**
```
playwright>=1.48.0
python-dotenv>=1.0.0
requests>=2.32.0  # или httpx
pillow>=10.4.0
beautifulsoup4>=4.12.3
```

**Не использовать:** Selenium, Puppeteer, aiohttp вместо Playwright.

```bash
pip install -r blocks/autopost_<площадка>/requirements.txt
playwright install chromium
```

---

## 4. Структура блока

```
blocks/autopost_<площадка>/
├── __init__.py
├── __main__.py          # точка входа: python -m blocks.autopost_<площадка>
├── main.py              # CLI: --file, --publish, --headless, --keep-open
├── <площадка>_client.py # Playwright-клиент
├── zen_http_server.py   # (Дзен) HTTP API — обход serialize binary в Cursor
├── zen_api_client.py    # (Дзен) клиент, запускает сервер, шлёт POST
├── config.py
├── config.example.env   # пример переменных
├── requirements.txt
├── README.md
├── articles/
│   ├── article_to_publish.json  # рабочий файл для правок перед публикацией
│   └── template.json
└── .gitignore
```

**Runtime (в .gitignore):** `*_storage_state.json`, `autopost_debug.log`, `.zen_last_post.json`, `*.png`.

---

## 5. Обход serialize binary (Cursor)

При работе через Cursor: `[internal] serialize binary: invalid int 32` — бинарные данные (скриншоты) попадают в ответ агента.

**Решение:** HTTP API. Клиент поднимает локальный сервер, Playwright выполняется изолированно, возвращается только JSON.

```
zen_api_client.py → POST /zen/publish → zen_http_server → zen_client (Playwright)
```

**Запуск:**
```bash
npm run zen:publish    # публикует из article_to_publish.json
npm run zen:draft
npm run zen:delete
```

Прямой запуск: `python -m blocks.autopost_zen --file ... --publish`.

---

## 6. Рабочий файл статьи

Перед публикацией статья оформляется в `blocks/autopost_zen/articles/article_to_publish.json`. Промпты и пошаговые инструкции по генерации (ключи, заголовок, текст, обложка и т.д.) — в [BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md](BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md).

**Порядок:**
1. Сгенерировать статью по гайду выше → записать в `article_to_publish.json`
2. Пользователь вносит правки
3. Запуск: `npm run zen:publish`

Не публиковать напрямую из чата. Всегда через файл.

---

## 7. Формат статьи (JSON)

### 7.1. Базовый

```json
{
  "title": "Заголовок",
  "content": "HTML или текст",
  "tags": ["тег1", "тег2"],
  "cover_image": "путь или имя файла",
  "cover_image_url": "https://...",
  "publish": true
}
```

### 7.2. Content blocks (Дзен — Draft.js)

Редактор Дзена — Draft.js. Контент вставляется блоками: HTML + картинки по очереди.

```json
{
  "title": "Заголовок",
  "content_blocks": [
    {"type": "image", "path": "cover.png", "caption": "Обложка"},
    {"type": "html", "content": "<p>Вступление</p>"},
    {"type": "html", "content": "<h3>1. Подтема</h3>"},
    {"type": "image", "path": "block1.png", "caption": "Подпись"},
    {"type": "html", "content": "<p>Абзац</p>"},
    {"type": "html", "content": "<ul><li>...</li></ul>"}
  ],
  "cover_image": "cover.png",
  "tags": [],
  "publish": true
}
```

**Порядок:** обложка → вступление → (H3 → картинка → абзац → список) × N → заключение.

**HTML:** только `<p>`, `<h3>`, `<ul>`, `<li>`. Без `<div>`, `<span>`, inline-стилей.

**Картинки:** имя файла (`cover.png`). Ищутся в `assets/`, `blocks/autopost_zen/articles/`.

### 7.3. Markdown-like (для площадок с другим редактором)

- `## Заголовок` → H2, `### Заголовок` → H3
- `• пункт` / `- пункт` → список
- `> цитата` → blockquote
- Inline-ссылка: **не через Ctrl+K** — ломает фокус. Использовать `page.evaluate()` + `execCommand('createLink')`.

---

## 8. Конфигурация (.env)

Для Дзен (блок `autopost_zen`):

```env
# Опционально: для входа по паролю (если нет storage_state)
# ZEN_EMAIL=...
# ZEN_PASSWORD=...

ZEN_STORAGE_STATE=zen_storage_state.json
ZEN_EDITOR_URL=https://dzen.ru/profile/editor/flowcabinet

ZEN_HEADLESS=false
ZEN_BROWSER_TIMEOUT=60000
ZEN_KEEP_OPEN=false
```

Пример: `blocks/autopost_zen/config.example.env`. Добавить переменные в `docs/rules/KEYS_AND_TOKENS.md`.

**Cookies:** сохранить один раз через `docs/scripts/scripts/capture_cookies.py`:
```bash
python docs/scripts/scripts/capture_cookies.py --url https://dzen.ru --output zen_storage_state.json
```

---

## 9. Клиент: ключевые методы

| Метод | Описание |
|-------|----------|
| `start()` | Браузер, контекст, viewport 1920×1080, `storage_state` |
| `login()` | Проверка cookies → форма входа при необходимости → `save_cookies()` |
| `create_post()` | Редактор, заголовок, content_blocks (или content), теги, обложка, публикация |
| `_paste_html()` | Clipboard + Ctrl+V (Draft.js) |
| `_add_image_in_article()` | Enter (выход из списка), side button, file chooser |
| `_click_publish()` | Кнопка «Опубликовать», модалка с обложкой |
| `screenshot()` | При ошибках и на ключевых шагах |

**Launch:** `args=['--disable-blink-features=AutomationControlled', '--start-maximized']`.

**Паузы:** `random.uniform(0.5, 2)` между действиями — имитация человека.

---

## 10. Дзен: критичные особенности

### 10.1. Модалка «Яндекс станет основным поиском»

После `page.goto()` на dzen.ru вызывать `dismiss_yandex_default_search_modal(page)` из `docs/scripts/scripts/playwright_helpers.py`.

### 10.2. Draft.js: вставка HTML

- **Не** `innerHTML` — теряется форматирование.
- **Clipboard:** `navigator.clipboard.write` с `text/html` + `text/plain`, затем `Ctrl+V`.
- Обёртка: `<html><body>${html}</body></html>`.

### 10.3. Картинки в статье

Кнопка добавления блока (side button) видна только у **параграфов**, не у списков. Порядок: H3 → картинка → абзац → список. Загрузка: `page.expect_file_chooser()` → `set_input_files(path)`.

### 10.4. Заголовки H3

Перед вставкой блока с `<h3>`: **Control+End**, затем 2× **Enter**. Ввод «### » + текст — Draft.js конвертирует в header-three.

### 10.5. Удаление предыдущего автопоста

Перед созданием новой статьи удалять сегодняшний пост по заголовку из `.zen_last_post.json`. Хранить `title` и `date` последнего созданного поста.

### 10.6. Капча

При SmartCaptcha — пауза на ручной ввод (30–90 сек). Не открывать редактор слишком часто с одного IP.

---

## 11. Реализация клиента (общее)

### 11.1. Запуск и контекст

- `chromium.launch(headless=..., args=['--disable-blink-features=AutomationControlled'])`
- `browser.new_context`: viewport 1920×1080, user_agent Chrome, `storage_state` при наличии
- `page.on("console")`, `page.on("pageerror")` — логировать

### 11.2. Авторизация

- Проверка «залогинен» по header/кнопке, не по аватаркам в ленте
- Форма входа: заполнить email/пароль, нажать кнопку в модалке/форме
- После входа: `storage_state` в файл

### 11.3. Создание поста (порядок)

1. Перейти на URL редактора
2. Закрыть модалки (dismiss_yandex_default_search_modal для Дзен)
3. Удалить предыдущий автопост (если требуется)
4. Заполнить заголовок
5. Вставить content_blocks (или content): HTML через clipboard, картинки через file chooser
6. Теги, обложка
7. Публикация или черновик
8. Скриншоты на ключевых шагах

### 11.4. Публикация

- **Не** `fetch()` со страницы — CORS. Использовать `context.request.post()` (Playwright API).
- Fallback на UI: кнопка «Опубликовать», `page.on("dialog")` при confirm.
- Подтверждение успеха: открыть публичную страницу поста, проверить заголовок.

---

## 12. CLI и коды выхода

- Аргументы: `--file`, `--publish`, `--headless`, `--keep-open`
- Режим: `--publish` > `article.publish` > по умолчанию False
- Exit codes: `0` — успех; `1` — не авторизовались; `2` — ошибка создания; `3` — ошибка файла/валидации
- Логи: консоль + `autopost_debug.log` (UTF-8)

---

## 13. Типичные проблемы и отладка

| Проблема | Решение |
|----------|---------|
| Модалка перекрывает Дзен | `dismiss_yandex_default_search_modal(page)` |
| serialize binary в Cursor | HTTP API (zen_api_client → zen_http_server) |
| H3 слипается, не применяется стиль | Control+End, 2× Enter, ввод «### » + текст |
| Картинка не вставляется после списка | Картинка после абзаца, до списка; несколько Enter для выхода из списка |
| Элемент не найден | `wait_for_selector`, несколько селекторов |
| Контент не сохраняется | Триггерить `input`, `change`, `blur` на contenteditable |
| Капча | Пауза на ручной ввод (30–90 сек) |
| SPA не загрузился | Ждать конкретный элемент (`.editor-ready`, `[data-loaded]`) |
| Видео таймаут | Таймаут ∝ размеру файла (10–15 сек на 1 MB) |
| Селекторы «плывут» | Стабильные атрибуты (data-*, роль); fallback на текст кнопки |

---

## 14. Видео (опционально)

При поддержке площадкой:

- Таймаут: `max(60, file_size_mb * 15)` секунд, макс 600
- `page.expect_file_chooser()` или drag-n-drop через JS
- Ожидание прогресс-бара / статуса «готово»
- Конвертация: ffmpeg в MP4 (H.264, AAC) при нужном формате

---

## 15. Чек-лист перед сдачей блока

- [ ] Авторизация, сохранение/загрузка cookies
- [ ] Заголовок, контент с H3, списками
- [ ] Обложка (file chooser или URL → temp file)
- [ ] Картинки в статье (content_blocks, side button)
- [ ] H3 в отдельных блоках (Enter перед вставкой, «### » + текст)
- [ ] Удаление предыдущего автопоста (если требуется)
- [ ] Модалки (dismiss_yandex_default_search_modal)
- [ ] HTTP API для Cursor (zen_http_server + zen_api_client)
- [ ] article_to_publish.json — рабочий файл
- [ ] Публикация или черновик
- [ ] Exit codes, логи в UTF-8, скриншоты при ошибках
- [ ] README блока, переменные в KEYS_AND_TOKENS.md

---

## 16. Ссылки

- **UNIVERSAL_AUTOPOST_PROMPT** — подробная инструкция по настройке (референс)
- **Промпты и инструкции по генерации статей для Дзен:** `docs/guides/BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md`
- **Структура статей и примеры (flowcabinet):** `docs/rules/ARTUR_HOROSHEFF_ARTICLE_PROMPT.md`, `docs/guides/ZEN_ARTICLE_STRUCTURE.md`
- **Ключи:** `docs/rules/KEYS_AND_TOKENS.md`
- **Блок Дзен:** `blocks/autopost_zen/`
- **Реестр блоков:** `docs/architecture/BLOCKS_REGISTRY.md`
