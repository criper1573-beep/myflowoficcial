# Lifehacks to Spambot

Отдельный скрипт цепочки: после генерации статьи для Дзен и обложки — отправить в Telegram-канал **обложку + краткое саммари** статьи. Саммари генерируется в процессе сборки статьи (поле `telegram_summary` в article.json). Не влияет на основной спамбот (RSS).

При запуске `python -m blocks.autopost_zen --auto --publish` публикация в Telegram запускается **автоматически** сразу после сохранения статьи (после генерации обложки и саммари), затем идёт публикация в Дзен. Тема удаляется из таблицы только после успешной публикации **во всех каналах** (Telegram и Дзен). В дашборде аналитики в плашке запуска отображается шаг «Публикация в Telegram» (успех/ошибка).

## Название (латиница)

`lifehacks_to_spambot` — «Лайфхаки в спам-бот».

## Запуск

Из корня проекта:

```bash
# Последняя папка в publish/ (по номеру)
python -m blocks.lifehacks_to_spambot

# Конкретная папка или файл статьи
python -m blocks.lifehacks_to_spambot blocks/autopost_zen/publish/006
python -m blocks.lifehacks_to_spambot blocks/autopost_zen/publish/006/article.json

# Проект для Telegram (токен и канал из blocks/projects/data/<id>.yaml)
python -m blocks.lifehacks_to_spambot blocks/autopost_zen/publish/006 --project flowcabinet

# Только показать, что будет отправлено (не постить)
python -m blocks.lifehacks_to_spambot blocks/autopost_zen/publish/006 --dry-run
```

## Что делает

1. Читает `article.json` (из указанной папки или последней в `blocks/autopost_zen/publish/`).
2. Берёт **обложку** по полю `cover_image` (ищет файл в папке статьи и в `blocks/autopost_zen/articles/`).
3. Собирает **подпись**: заголовок + **краткое саммари** (`telegram_summary` из article.json — генерируется при сборке статьи; иначе `meta_description`). Обрезка по лимиту Telegram (1024 символа).
4. Отправляет в канал **одним постом**: фото обложки + подпись (HTML).

## Конфигурация

- **Telegram:** тот же бот и канал, что у основного спамбота:
  - через проект: `--project flowcabinet` (из `blocks/projects/data/flowcabinet.yaml`);
  - или переменные окружения: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID` (в т.ч. из `.env`).

Отдельный файл истории для этого скрипта не используется: повторный запуск по той же статье создаст повторный пост. При необходимости можно добавить свой `lifehacks_posted.json`.

## Зависимости

- `python-telegram-bot`
- при использовании `--project`: конфиг проекта (YAML) и при необходимости PyYAML.

Установка из корня: `pip install python-telegram-bot` (если ещё не стоит в проекте).
