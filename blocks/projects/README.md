# Блок «Проекты»

Хранение конфигурации по каждому бизнес-проекту. Один ContentZavod обслуживает несколько проектов: у каждого свои аккаунты (Telegram, VK, Дзен и т.д.), общий API ИИ задаётся в `.env`.

---

## Структура

```
blocks/projects/
├── __init__.py
├── loader.py          # load config by project_id
├── data/              # project YAML files
│   ├── project.example.yaml
│   ├── flowcabinet.yaml
│   └── другой_проект.yaml
└── README.md
```

---

## Добавление проекта

1. Скопируйте `data/project.example.yaml` в `data/<project_id>.yaml`.
2. Заполните `project_id`, `name`, `telegram.bot_token`, `telegram.channel_id`.
3. При необходимости укажите переопределения для спамбота в секции `spambot`.

Пример минимального конфига:

```yaml
project_id: my_business
name: Мой бизнес

telegram:
  bot_token: "1234567890:ABC..."
  channel_id: "@mychannel"
```

---

## Запуск бота для проекта

**Из папки блока (рекомендуется):**
```bat
blocks\spambot\start.bat flowcabinet
```

**Через полный скрипт:**
```bat
docs\scripts\scripts\run_spambot.bat flowcabinet
```

**Через Python:**
```bash
python -m blocks.spambot --project flowcabinet
```

**Проект по умолчанию:** задайте в `.env`:
```env
PROJECT_ID=flowcabinet
```
Тогда можно запускать без аргумента: `blocks\spambot\start.bat` или `python -m blocks.spambot`.

**Список проектов:**
```bash
python -m blocks.spambot --list-projects
```

---

## Схема конфига проекта (YAML)

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `project_id` | да | Идентификатор (совпадает с именем файла без .yaml) |
| `name` | нет | Название для отображения |
| `telegram.bot_token` | да* | Токен бота Telegram |
| `telegram.channel_id` | да* | ID канала (@channel или -100...) |
| `spambot.cta_text` | нет | Текст CTA для поста |
| `spambot.cta_link` | нет | Ссылка CTA |
| `spambot.hashtag_options` | нет | Список хештегов |
| `spambot.priority_words` | нет | Ключевые слова для фильтрации RSS |
| `spambot.rss_feeds` | нет | Основные RSS-ленты |
| `spambot.rss_feeds_fallback` | нет | Запасные RSS-ленты |

\* Для спамбота обязательны `telegram.bot_token` и `telegram.channel_id` (в файле проекта или в .env).

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
ids = list_projects()  # ['flowcabinet', ...]

# Конфиг целиком
config = load_project_config("flowcabinet")

# Только Telegram (для спамбота)
tg = get_telegram_config("flowcabinet")  # {'bot_token': '...', 'channel_id': '@...'}

# Переопределения для NewsBotConfig
overrides = get_spambot_overrides("flowcabinet")
# Передать в NewsBot: NewsBot(config=NewsBotConfig(bot_token=..., channel_id=..., **overrides))
```

---

## Общее и проектное

| Где | Что |
|-----|-----|
| **.env** | GRS_AI_API_KEY, GRS_AI_API_URL, PROJECT_ID, опционально TELEGRAM_* |
| **blocks/projects/data/<id>.yaml** | telegram, spambot, в будущем vk, zen и т.д. |

API ИИ один на весь завод; аккаунты соцсетей и настройки ботов — по проектам.
