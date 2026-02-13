# Блок Post FLOW

Генерация и публикация постов в канал FLOW из тем в Google Таблице. Один запуск — один пост.

## Что делает

1. Берёт **первую тему** из Google Таблицы (колонка A, контекст в B).
2. Генерирует **заголовок и текст** через GRS AI (с учётом контекста FLOW и последних 10 постов).
3. Генерирует **картинку** через GRS AI (nano-banana / draw API).
4. Публикует пост в **Telegram-канал** (@myflowofficial по умолчанию).
5. Удаляет тему из таблицы и сохраняет пост в историю.

## Запуск

**Из папки блока (рекомендуется):** дважды нажмите `blocks\post_flow\start.bat` — скрипт перейдёт в корень ContentZavod и запустит бота.

**Из корня проекта:**
```bash
python -m blocks.post_flow.bot
```

## Настройки

- **.env** в **корне КонтентЗавод** (общий с другими блоками):
  - `GRS_AI_API_KEY` — ключ GRS AI (обязательно).
  - `TELEGRAM_BOT_TOKEN` — токен бота (обязательно).
  - `TELEGRAM_CHANNEL` — канал (по умолчанию `@myflowofficial`).
  - `GOOGLE_SHEET_ID` — ID таблицы (по умолчанию таблица «Посты для канала FLOW»).
  - `GOOGLE_CREDENTIALS_PATH` — имя файла ключа (по умолчанию `credentials.json` в папке блока).

- **Google:** создайте сервисный аккаунт в [Google Cloud Console](https://console.cloud.google.com/apis/credentials), скачайте JSON и сохраните как `blocks/post_flow/credentials.json`. Если ключ ещё в папке «Пост FLOW» на рабочем столе — из корня проекта выполните один раз: `python blocks/post_flow/copy_credentials_here.py`. Откройте доступ к таблице для `client_email` из JSON.

- Бот должен быть **администратором** канала.

## Зависимости

Дополнительно к общему `requirements.txt` ContentZavod нужны:
- `gspread>=6.0.0`
- `google-auth>=2.25.0`

Установка: из корня проекта `pip install -r docs/config/requirements.txt` (если зависимости блока добавлены туда) или `pip install gspread google-auth`.

## Структура

- `config.py` — конфиг из .env (корень проекта).
- `context.py` — контекст FLOW для промптов.
- `content.py` — генерация заголовка, текста и картинки (GRS AI).
- `sheets_client.py` — чтение/удаление тем из Google Таблицы.
- `telegram_client.py` — публикация в канал.
- `bot.py` — точка входа (один пост за запуск).
- `posts_history.json` — последние 10 постов (создаётся автоматически, в .gitignore).
