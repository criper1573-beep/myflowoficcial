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

Пример минимального конфига:

```yaml
project_id: my_business
name: Мой бизнес

telegram:
  bot_token: "1234567890:ABC..."
  channel_id: "@mychannel"
```

Устаревшая секция `spambot` в YAML (если осталась от старых конфигов) игнорируется кодом.

---

## Схема конфига проекта (YAML)

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `project_id` | да | Идентификатор (совпадает с именем файла без .yaml) |
| `name` | нет | Название для отображения |
| `telegram.bot_token` | да* | Токен бота Telegram |
| `telegram.channel_id` | да* | ID канала (@channel или -100...) |

\* Для блоков, которым нужен Telegram, задайте в файле проекта или в `.env`.

---

## Использование в коде

```python
from blocks.projects import (
    list_projects,
    load_project_config,
    get_telegram_config,
    get_project_name,
)

ids = list_projects()
config = load_project_config("flowcabinet")
tg = get_telegram_config("flowcabinet")
```

---

## Общее и проектное

| Где | Что |
|-----|-----|
| **.env** | GRS_AI_API_KEY, GRS_AI_API_URL, PROJECT_ID, опционально TELEGRAM_* |
| **blocks/projects/data/<id>.yaml** | telegram, в будущем vk, zen и т.д. |

API ИИ один на весь завод; аккаунты соцсетей — по проектам.
