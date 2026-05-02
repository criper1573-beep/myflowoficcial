# Мультипроектность ContentZavod

Один завод — несколько проектов (бизнесов). У каждого проекта свои аккаунты в соцсетях и настройки; API ИИ общий.

---

## Идея

- **Один код** — один ContentZavod, обновления и правки в одном месте.
- **Несколько проектов** — каждый проект = свой бизнес, свои Telegram/VK/Дзен и т.д.
- **Общий AI** — ключ GRS AI (и др.) в `.env`, один на все проекты.
- **Выбор проекта** — в блоках через аргумент `--project <id>` или переменную `PROJECT_ID` в `.env`.

---

## Структура

| Где | Что хранится |
|-----|----------------|
| **.env** (корень) | GRS_AI_API_KEY, GRS_AI_API_URL, PROJECT_ID (по умолчанию). Опционально TELEGRAM_* и др. |
| **blocks/projects/data/<id>.yaml** | telegram (bot_token, channel_id), в будущем vk, zen и т.д. |

Секция `spambot` в старых YAML больше не используется кодом и может быть удалена из файлов.

---

## Добавление проекта

1. Скопируйте пример:
   ```text
   copy blocks\projects\data\project.example.yaml blocks\projects\data\my_project.yaml
   ```
2. Откройте `blocks/projects/data/мой_проект.yaml` и заполните `project_id`, `name`, `telegram`.

Полный пример и поля — в **blocks/projects/data/project.example.yaml** и **blocks/projects/README.md**.

---

## Использование в коде

```python
from blocks.projects import (
    list_projects,
    load_project_config,
    get_telegram_config,
    get_project_name,
)

list_projects()
config = load_project_config("flowcabinet")
tg = get_telegram_config("flowcabinet")
```

---

## Безопасность

- Файлы проектов в `blocks/projects/data/*.yaml` могут содержать токены. При необходимости добавьте в `.gitignore`:
  ```gitignore
  blocks/projects/data/*.yaml
  !blocks/projects/data/project.example.yaml
  ```

---

## Кратко

| Действие | Как |
|----------|-----|
| Проект по умолчанию | В `.env`: `PROJECT_ID=flowcabinet` |
| Добавить проект | Новый файл в `blocks/projects/data/<id>.yaml` |

Подробнее: **blocks/projects/README.md**.
