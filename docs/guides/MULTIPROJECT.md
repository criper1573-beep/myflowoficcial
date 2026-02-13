# Мультипроектность ContentZavod

Один завод — несколько проектов (бизнесов). У каждого проекта свои аккаунты в соцсетях и настройки; API ИИ общий.

---

## Идея

- **Один код** — один ContentZavod, обновления и правки в одном месте.
- **Несколько проектов** — каждый проект = свой бизнес, свои Telegram/VK/Дзен, свои CTA, хештеги, RSS.
- **Общий AI** — ключ GRS AI (и др.) в `.env`, один на все проекты.
- **Выбор проекта при запуске** — `start.bat flowcabinet` или `python -m blocks.spambot --project flowcabinet`.

---

## Структура

| Где | Что хранится |
|-----|----------------|
| **.env** (корень) | GRS_AI_API_KEY, GRS_AI_API_URL, PROJECT_ID (проект по умолчанию). Опционально TELEGRAM_* для запуска без проектов. |
| **blocks/projects/data/<id>.yaml** | telegram (bot_token, channel_id), spambot (CTA, хештеги, RSS), в будущем vk, zen и т.д. |

---

## Добавление проекта

1. Скопируйте пример:
   ```text
   copy blocks\projects\data\project.example.yaml blocks\projects\data\my_project.yaml
   ```
2. Откройте `blocks/projects/data/мой_проект.yaml` и заполните:
   - `project_id`, `name`
   - `telegram.bot_token`, `telegram.channel_id`
   - при необходимости — секцию `spambot` (cta_text, cta_link, hashtag_options, priority_words, rss_feeds).
3. Запуск:
   ```bat
   blocks\spambot\start.bat мой_проект
   ```

---

## Запуск бота по проекту

**С указанием проекта (рекомендуется):**
```bat
blocks\spambot\start.bat flowcabinet
docs\scripts\scripts\run_spambot.bat flowcabinet
```
```bash
python docs/scripts/scripts/python -m blocks.spambot --project flowcabinet
```

**Проект по умолчанию:** в `.env` задайте `PROJECT_ID=flowcabinet`. Тогда можно вызывать без аргумента:
```bat
blocks\spambot\start.bat
```

**Список проектов:**
```bash
python -m blocks.spambot --list-projects
```

**Без проектов (как раньше):** токены только из `.env`:
```bash
python -m blocks.spambot --no-project
```
В `.env` должны быть заданы `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHANNEL_ID`.

---

## Пример конфига проекта (YAML)

```yaml
project_id: flowcabinet
name: Flow Cabinet

telegram:
  bot_token: "8468363310:AAG..."
  channel_id: "@flowcabinetnews"

spambot:
  cta_text: "\n\nПланируешь ремонт в офисе?...\n"
  cta_link: "https://flowcabinet.ru"
  hashtag_options: ["#ремонт", "#офис", ...]
  priority_words: ["ремонт", "офис", "интерьер"]
```

Полный пример и все поля — в **blocks/projects/data/project.example.yaml** и **blocks/projects/README.md**.

---

## Использование в коде

```python
from blocks.projects import (
    list_projects,
    load_project_config,
    get_telegram_config,
    get_spambot_overrides,
    get_project_name,
)

# Список проектов
list_projects()  # ['flowcabinet', ...]

# Конфиг проекта
config = load_project_config("flowcabinet")

# Только Telegram (для спамбота)
tg = get_telegram_config("flowcabinet")

# Переопределения для NewsBotConfig
overrides = get_spambot_overrides("flowcabinet")
```

---

## Безопасность

- Файлы проектов в `blocks/projects/data/*.yaml` могут содержать токены. Добавьте в `.gitignore` при необходимости, например:
  ```gitignore
  blocks/projects/data/*.yaml
  !blocks/projects/data/project.example.yaml
  ```
- Альтернатива: в YAML указывать только `project_id` и `name`, а токены подставлять из переменных окружения (например `TELEGRAM_BOT_TOKEN_flowcabinet`) — при желании можно расширить загрузчик.

---

## Кратко

| Действие | Команда |
|----------|--------|
| Запуск для проекта | `blocks\spambot\start.bat flowcabinet` |
| Список проектов | `python ... python -m blocks.spambot --list-projects` |
| Проект по умолчанию | В `.env`: `PROJECT_ID=flowcabinet` |
| Добавить проект | Новый файл в `blocks/projects/data/<id>.yaml` |

Подробнее по блоку: **blocks/projects/README.md**.
