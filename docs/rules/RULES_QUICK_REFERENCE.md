# Правила проекта - Краткая справка

Быстрая шпаргалка по основным правилам проекта ContentZavod.

Полная версия: [PROJECT_RULES.md](PROJECT_RULES.md)

---

## 🤖 Боты

### ✅ Правило 1: BAT-файлы для ботов

**Для каждого бота создавать BAT-файл**

```
scripts/run_<bot_name>.bat
```

**Минимальный шаблон:**
```bat
@echo off
chcp 65001 > nul
echo Запуск [Название Бота]
python scripts\run_<bot_name>.py
if errorlevel 1 pause
```

---

## 📁 Структура

### ✅ Правило 2: Структура блоков

```
blocks/block_name/
├── __init__.py          # Экспорт
├── block_name.py        # Код
├── README.md            # Документация
└── QUICK_START.md       # Опционально
```

---

## 💾 Бекапы

### ✅ Правило 3: Когда создавать бекапы

| Когда | Команда | Теги |
|-------|---------|------|
| Блок работает | `create ... "Первая рабочая версия"` | `working,v0.1` |
| Перед изменениями | `create ... "Перед рефакторингом"` | `before-refactor` |
| Стабильная версия | `create ... "Стабильная версия"` | `stable,v1.0` |
| Перед коммитом | `create ... "Версия для коммита"` | `production,v1.0` |

---

## 📝 Документация

### ✅ Правило 4: Обязательная документация

**Каждый блок должен иметь:**
- ✅ README.md с примерами
- ✅ Docstrings в коде
- ✅ Примеры использования

---

## 🔧 Конфигурация

### ✅ Правило 5: Переменные окружения

**Секреты ТОЛЬКО через .env**

```python
# ✅ Правильно
API_KEY = os.getenv("API_KEY")

# ❌ Неправильно
API_KEY = "hardcoded_key"
```

---

## 🎯 Именование

### ✅ Правило 7: Соглашения

| Что | Формат | Пример |
|-----|--------|--------|
| blocks | Latin | `ai_integrations`, `autopost_zen` |
| Классы | `PascalCase` | `NewsBot` |
| Функции | `snake_case` | `send_post` |
| Константы | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Переменные окружения | `UPPER_SNAKE_CASE` | `TELEGRAM_BOT_TOKEN` |

---

## 📋 Коммиты

### ✅ Правило 8: Формат коммитов

```
<тип>: <описание>
```

**Типы:**
- `feat:` - новая функциональность
- `fix:` - исправление бага
- `docs:` - документация
- `refactor:` - рефакторинг
- `test:` - тесты
- `chore:` - рутина

---

## 🔒 Безопасность

### ✅ Правило 9: Что НЕ коммитить

❌ `.env` файлы  
❌ Токены и API ключи  
❌ Пароли  
❌ Приватные ключи  

✅ `.env.example` с примерами  
✅ Документацию  
✅ Конфигурацию без секретов  

---

## 📊 Логирование

### ✅ Правило 10: Использовать logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Информация")
logger.warning("Предупреждение")
logger.error("Ошибка")
```

**НЕ использовать `print()` для логов!**

---

## 🔄 Обновления

### ✅ Правило 11: Обновлять документацию

**При изменении кода обновить:**
- ✅ README блока
- ✅ PATCHES.md
- ✅ PROJECT_STATUS.md
- ✅ Docstrings
- ✅ Примеры

---

## 📦 Зависимости

### ✅ Правило 12: requirements.txt

```txt
# Core dependencies
requests>=2.31.0

# Spambot dependencies
python-telegram-bot>=21.0
feedparser>=6.0
googletrans==4.0.0-rc1  # Специфичная версия
```

**Группировать по назначению + комментарии**

---

## 🎨 Код

### ✅ Правило 13: Стиль кода

- ✅ Type hints для параметров
- ✅ Максимум 100 символов в строке
- ✅ f-strings для форматирования
- ✅ Избегать глобальных переменных

```python
def process_data(
    items: List[str],
    config: Optional[Dict[str, any]] = None
) -> bool:
    """Docstring с описанием"""
    pass
```

---

## 🚀 Быстрые команды

### Создать бекап
```bash
python scripts/backup_manager.py create blocks/path/file.py "Описание" --tags stable,v1.0
```

### Запуск Post FLOW (Windows)
```bash
python -m blocks.post_flow.bot
```

### Проверить правила
```bash
# Проверить .env в .gitignore
cat .gitignore | grep .env

# Проверить секреты в staged
git diff --cached | grep -i "token\|key\|password"
```

---

## 📖 Полная документация

[PROJECT_RULES.md](PROJECT_RULES.md) - полная версия всех правил с примерами и объяснениями

---

**Версия:** 1.0  
**Дата:** 2026-02-01
