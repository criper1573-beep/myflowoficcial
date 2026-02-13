# Шпаргалка ContentZavod

Быстрый справочник по основным командам и функциям проекта.

---

## 🤖 GRS AI Client

### Импорт
```python
from blocks.интеграции_ии import GRSAIClient
client = GRSAIClient()
```

### Простой запрос
```python
response = client.simple_ask("Привет!")
```

### С системным промптом
```python
response = client.simple_ask(
    question="Придумай заголовок",
    system_prompt="Ты копирайтер",
    model="gpt-4o-mini"
)
```

### Потоковый режим
```python
for chunk in client.chat_stream(messages=[...]):
    print(chunk, end="", flush=True)
```

### Модели
- **Быстрые:** `gpt-4o-mini`, `gemini-2.5-flash`
- **Мощные:** `gemini-2.5-pro`, `gemini-3-pro`

---

## 💾 Система бекапов

### Создать бекап
```bash
python docs/scripts/scripts/backup_manager.py create blocks/path/to/file.py "Описание" --tags stable,v1.0
```

### Список бекапов
```bash
# Все бекапы
python docs/scripts/scripts/backup_manager.py list

# Бекапы файла
python docs/scripts/scripts/backup_manager.py list blocks/path/to/file.py
```

### Информация о бекапе
```bash
python scripts/backup_manager.py info backup_0001
```

### Восстановить бекап
```bash
python scripts/backup_manager.py restore backup_0001
```

### Сравнить версии
```bash
python scripts/backup_manager.py diff backup_0001
```

### Удалить бекап
```bash
python scripts/backup_manager.py delete backup_0001
```

---

## 🏷️ Теги для бекапов

| Тег | Использование |
|-----|---------------|
| `working` | Рабочая версия |
| `stable` | Стабильная версия |
| `v1.0` | Версия |
| `before-refactor` | Перед изменениями |
| `milestone` | Важный этап |

---

## 🤖 NewsBot (Spambot)

### Запуск бота
```bash
# Windows (самый простой способ)
START_SPAMBOT.bat

# Или через scripts
scripts\run_spambot.bat
scripts\run_newsbot.bat

# Или через Python
python -m blocks.spambot
```

### Использование в коде
```python
from blocks.спамбот import NewsBot

bot = NewsBot()
bot.start()
```

### С конфигурацией
```python
from blocks.спамбот.newsbot import NewsBotConfig

config = NewsBotConfig(
    bot_token="token",
    channel_id="@channel",
    send_interval=180,
    hashtags_per_post=5
)
bot = NewsBot(config=config)
bot.start()
```

---

## 🧪 Тестирование

### Тест GRS AI Client
```bash
python docs/scripts/scripts/test_grs_ai.py
```

---

## 📁 Структура проекта

```
ContentZavod/
├── blocks/                     # Блоки
│   └── интеграции_ии/        # ✅ GRS AI Client
├── backups/                   # Бекапы (локальные)
├── config/                    # Конфигурация
├── docs/scripts/scripts/  # Скрипты
│   ├── test_grs_ai.py        # Тесты AI
│   └── backup_manager.py     # Управление бекапами
└── docs...                    # Документация
```

---

## 📚 Документация

| Документ | Назначение |
|----------|------------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Быстрый старт |
| [BACKUP_QUICK_START.md](BACKUP_QUICK_START.md) | Бекапы - быстрый старт |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Статус проекта |
| blocks/интеграции_ии/QUICK_REFERENCE.md | AI Client справочник |

---

## 🔧 Настройка

### Переменные окружения (.env)
```env
# GRS AI
GRS_AI_API_KEY=your_api_key
GRS_AI_API_URL=https://grsaiapi.com

# Telegram (NewsBot)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel
```

### Установка зависимостей
```bash
pip install -r docs/config/requirements.txt
```

---

## 🎯 Workflow разработки блока

1. **Создать блок** → Написать код
2. **Блок работает** → Создать бекап с тегом `working`
   ```bash
   python docs/scripts/scripts/backup_manager.py create blocks/new_block.py "Работает" --tags working
   ```
3. **Перед изменениями** → Создать бекап с тегом `before-refactor`
   ```bash
   python docs/scripts/scripts/backup_manager.py create blocks/new_block.py "Перед рефакторингом" --tags before-refactor
   ```
4. **Стабильная версия** → Создать бекап с тегом `stable`
   ```bash
   python docs/scripts/scripts/backup_manager.py create blocks/new_block.py "Стабильная" --tags stable,v1.0
   ```
5. **Проблемы** → Восстановить последний рабочий бекап
   ```bash
   python docs/scripts/scripts/backup_manager.py list blocks/new_block.py
   python scripts/backup_manager.py restore backup_0005
   ```

---

## 💡 Полезные команды

### Python REPL с AI Client
```bash
python -c "from blocks.интеграции_ии import GRSAIClient; c=GRSAIClient(); print(c.simple_ask('Привет!'))"
```

### Проверка структуры
```bash
# Windows
tree /F /A

# Linux/Mac
tree
```

---

## 🆘 Troubleshooting

### Проблема: API ключ не найден
**Решение:** Проверьте `.env` файл
```bash
# Создать .env из примера
copy docs\config\.env.example .env
# Отредактировать и добавить ключ
```

### Проблема: Модуль не найден
**Решение:** Установите зависимости
```bash
pip install -r docs/config/requirements.txt
```

### Проблема: Кириллица в ответе AI
**Решение:** Клиент автоматически исправляет кодировку

---

## 🔗 Быстрые ссылки

- **GRS AI Dashboard:** https://grsai.com/dashboard
- **API Endpoint:** https://grsaiapi.com/v1/chat/completions
- **Документация API:** https://grsai.com/dashboard/documents/chat

---

**Версия:** 2026-02-01  
**Статус:** 🟢 Активная разработка
