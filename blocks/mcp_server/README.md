# MCP-сервер ContentZavod

Единая точка доступа к инструментам проекта через Model Context Protocol.

## Установка

```bash
pip install -r blocks/mcp_server/requirements.txt
# или из корня проекта
pip install "mcp[cli]"
```

## Инструменты

### Zen (Дзен)
| Инструмент     | Описание                                              |
|----------------|--------------------------------------------------------|
| `zen_publish`  | Опубликовать статью в Дзен                            |
| `zen_draft`    | Сохранить статью в черновик                           |
| `zen_list_articles` | Список статей в `blocks/autopost_zen/articles/` |

### GRS AI
| Инструмент     | Описание                                              |
|----------------|--------------------------------------------------------|
| `grs_chat`     | Генерация текста (question, system_prompt, model)     |
| `grs_chat_messages` | Генерация с полным диалогом (messages JSON)      |
| `grs_models`   | Список моделей (текст + изображения)                  |
| `grs_image`    | Генерация изображения (prompt, model, size)           |

## Подключение в Cursor

1. Откройте **Cursor Settings** → **MCP** → **Add New MCP Server**
2. Добавьте:

**Имя:** `content-factory` (или `ContentZavod`)

**Команда:**
```text
python
```

**Аргументы:**
```text
-m
blocks.mcp_server
```

Либо укажите полный путь к Python и проекту, например:
```text
C:\Users\<user>\AppData\Local\Programs\Python\Python3xx\python.exe
```
```text
-m
blocks.mcp_server
```

**Рабочая директория:** корень проекта (где лежит `blocks/`).

### Пример mcp.json

В `%USERPROFILE%\.cursor\mcp.json` или через UI:

```json
{
  "mcpServers": {
    "content-factory": {
      "command": "python",
      "args": ["-m", "blocks.mcp_server"],
      "cwd": "C:\\Users\\bbru7\\Desktop\\ContentZavod"
    }
  }
}
```

**Важно:** при использовании Cyrillic в пути возможны проблемы. Альтернатива — разместить проект в пути без кириллицы.

## Запуск вручную (тест)

```bash
python -m blocks.mcp_server
# или
cd C:\Users\bbru7\Desktop\ContentZavod
python -m blocks.mcp_server
```

Сервер запустится в режиме stdio — Cursor подключается к нему автоматически.
