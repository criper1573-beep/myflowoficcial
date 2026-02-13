# GRS AI Client - Краткий справочник

## Импорт

```python
from Блоки.интеграции_ии import GRSAIClient
```

## Инициализация

```python
# Автоматически берет API ключ из переменной окружения GRS_AI_API_KEY
client = GRSAIClient()

# Или явно указать ключ
client = GRSAIClient(api_key="your_key")
```

## Основные методы

### simple_ask() - Простой запрос

```python
# Минимальный вариант
response = client.simple_ask("Привет!")

# С системным промптом
response = client.simple_ask(
    question="Напиши заголовок",
    system_prompt="Ты копирайтер"
)

# С выбором модели
response = client.simple_ask(
    question="Напиши статью",
    model="gemini-2.5-pro"
)
```

### chat() - Полноценный диалог

```python
# Простой запрос
response = client.chat(
    messages=[
        {"role": "user", "content": "Привет!"}
    ]
)

# С контекстом
response = client.chat(
    messages=[
        {"role": "system", "content": "Ты помощник"},
        {"role": "user", "content": "Вопрос 1"},
        {"role": "assistant", "content": "Ответ 1"},
        {"role": "user", "content": "Вопрос 2"}
    ],
    model="gpt-4o-mini"
)

# С параметрами
response = client.chat(
    messages=[...],
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000,
    use_fallback=True  # Автоматический fallback на другие модели
)
```

### chat_stream() - Потоковый режим

```python
for chunk in client.chat_stream(
    messages=[{"role": "user", "content": "Напиши историю"}]
):
    print(chunk, end="", flush=True)
```

## Модели

### Быстрые (для простых задач)
- `gpt-4o-mini` ⭐ рекомендуется
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`

### Мощные (для сложных задач)
- `gemini-2.5-pro` ⭐ для длинных текстов
- `gemini-3-pro`
- `gpt-4o-all`

### Простые
- `nano-banana-fast`
- `nano-banana`

## Типичные сценарии

### Генерация заголовков

```python
response = client.simple_ask(
    question=f"Сгенерируй 5 заголовков для статьи про {topic}",
    system_prompt="Ты профессиональный копирайтер",
    model="gpt-4o-mini"
)
```

### Генерация статьи

```python
article = ""
for chunk in client.chat_stream(
    messages=[
        {"role": "system", "content": "Ты автор статей"},
        {"role": "user", "content": f"Напиши статью про {topic}"}
    ],
    model="gemini-2.5-pro"
):
    article += chunk
```

### Генерация хештегов

```python
response = client.simple_ask(
    question=f"Сгенерируй 10 хештегов для: {text[:500]}",
    system_prompt="Ты SMM-специалист",
    model="gpt-4o-mini"
)
```

### SEO-оптимизация

```python
response = client.simple_ask(
    question=f"Создай meta description и keywords для: {text[:1000]}",
    system_prompt="Ты SEO-специалист",
    model="gpt-4o-mini"
)
```

### Модерация контента

```python
response = client.simple_ask(
    question=f"Проверь текст на ошибки и проблемы: {text}",
    system_prompt="Ты модератор и редактор",
    model="gpt-4o-mini"
)
```

## Обработка ошибок

```python
try:
    response = client.chat(
        messages=[...],
        use_fallback=True  # Автоматически пробует другие модели
    )
except Exception as e:
    print(f"Ошибка: {e}")
```

## Конфигурация

```python
from Блоки.интеграции_ии.grs_ai_client import GRSAIConfig

config = GRSAIConfig(
    api_key="your_key",
    base_url="https://grsaiapi.com",
    default_model="gpt-4o-mini",
    timeout=90,
    fallback_models=["gpt-4o-mini", "gemini-2.5-flash"]
)

client = GRSAIClient(config=config)
```

## Переменные окружения

```env
# .env файл
GRS_AI_API_KEY=your_api_key
GRS_AI_API_URL=https://grsaiapi.com
```

## Логирование

```python
import logging

# Включить логи
logging.basicConfig(level=logging.INFO)

# Или только для GRS AI
logger = logging.getLogger('Блоки.интеграции_ии.grs_ai_client')
logger.setLevel(logging.DEBUG)
```

## Полезные функции

### Получить список моделей

```python
models = GRSAIClient.get_available_models()
# {'fast': [...], 'powerful': [...], 'simple': [...]}
```

## Шпаргалка по выбору модели

| Задача | Модель | Причина |
|--------|--------|---------|
| Заголовки | `gpt-4o-mini` | Быстро и качественно |
| Хештеги | `gpt-4o-mini` | Простая задача |
| SEO | `gpt-4o-mini` | Не требует креативности |
| Короткий текст (до 500 слов) | `gpt-4o-mini` | Быстро |
| Длинная статья (1000+ слов) | `gemini-2.5-pro` | Лучше с длинным контекстом |
| Креативный текст | `gemini-2.5-pro` | Более креативная |
| Модерация | `gpt-4o-mini` | Достаточно для проверки |
| Анализ | `gemini-2.5-pro` | Глубокое понимание |

## Примеры промптов

### Хороший промпт
```python
prompt = """
КОНТЕКСТ: Статья для блога про технологии
ЗАДАЧА: Сгенерируй 5 заголовков
ТРЕБОВАНИЯ:
- Длина до 60 символов
- Используй цифры и факты
- Избегай clickbait
ФОРМАТ: Нумерованный список
"""
```

### Плохой промпт
```python
prompt = "Придумай заголовки"  # Слишком расплывчато
```

## Тестирование

```bash
# Запустить тесты
python scripts/test_grs_ai.py
```

## Документация

- [README.md](README.md) - Полная документация
- [USAGE_IN_BLOCKS.md](USAGE_IN_BLOCKS.md) - Примеры использования в блоках
- [../../GRS_AI_API_INTEGRATION.md](../../GRS_AI_API_INTEGRATION.md) - Документация API

## Поддержка

При проблемах проверьте:
1. ✅ API ключ установлен в `.env`
2. ✅ Установлены зависимости: `pip install -r requirements.txt`
3. ✅ Используете только поддерживаемые поля в запросе
4. ✅ Timeout достаточно большой (60+ секунд)
