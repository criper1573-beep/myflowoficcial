# GRS AI Integration Block

Универсальный блок для работы с GRS AI API.

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install requests python-dotenv
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
GRS_AI_API_KEY=ваш_ключ_api
GRS_AI_API_URL=https://grsaiapi.com
```

### 3. Базовое использование

```python
from Блоки.интеграции_ии import GRSAIClient

# Создание клиента (API ключ берется из .env)
client = GRSAIClient()

# Простой запрос
response = client.simple_ask("Привет! Как дела?")
print(response)
```

## Примеры использования

### Простой запрос с системным промптом

```python
response = client.simple_ask(
    question="Напиши заголовок для статьи про искусственный интеллект",
    system_prompt="Ты профессиональный копирайтер, который пишет цепляющие заголовки"
)
print(response)
```

### Диалог с несколькими сообщениями

```python
messages = [
    {"role": "system", "content": "Ты помощник по написанию контента"},
    {"role": "user", "content": "Мне нужна статья про Python"},
    {"role": "assistant", "content": "О каком аспекте Python вы хотите написать?"},
    {"role": "user", "content": "Про асинхронное программирование"}
]

response = client.chat(messages=messages, model="gpt-4o-mini")
print(response)
```

### Потоковый режим (streaming)

```python
print("Генерация текста:")
for chunk in client.chat_stream(
    messages=[{"role": "user", "content": "Напиши короткую историю"}]
):
    print(chunk, end="", flush=True)
print()
```

### Выбор модели

```python
# Быстрая модель для простых задач
response = client.chat(
    messages=[{"role": "user", "content": "Привет!"}],
    model="gpt-4o-mini"
)

# Мощная модель для сложных задач
response = client.chat(
    messages=[{"role": "user", "content": "Напиши развернутый анализ..."}],
    model="gemini-2.5-pro"
)
```

### Использование с параметрами

```python
response = client.chat(
    messages=[{"role": "user", "content": "Напиши креативный текст"}],
    model="gpt-4o-mini",
    temperature=0.9,  # Больше креативности
    max_tokens=500    # Ограничение длины
)
```

### Обработка ошибок с fallback

```python
try:
    # Автоматический fallback на другие модели при ошибке
    response = client.chat(
        messages=[{"role": "user", "content": "Привет!"}],
        model="gemini-3-pro",
        use_fallback=True  # По умолчанию True
    )
except Exception as e:
    print(f"Все модели не сработали: {e}")
```

### Кастомная конфигурация

```python
from Блоки.интеграции_ии.grs_ai_client import GRSAIConfig

config = GRSAIConfig(
    api_key="your_key",
    base_url="https://grsaiapi.com",
    default_model="gemini-2.5-flash",
    timeout=90,
    fallback_models=["gemini-2.5-flash", "gpt-4o-mini"]
)

client = GRSAIClient(config=config)
```

## Интеграция в пайплайн

### Пример блока для генерации заголовков

```python
from Блоки.интеграции_ии import GRSAIClient

class TitlesBlock:
    def __init__(self):
        self.ai_client = GRSAIClient()
    
    def execute(self, content_item):
        """Генерация заголовков для контента"""
        
        prompt = f"""
        Тема: {content_item.topic}
        Целевая аудитория: {content_item.target_audience}
        
        Сгенерируй 5 цепляющих заголовков для статьи.
        """
        
        response = self.ai_client.simple_ask(
            question=prompt,
            system_prompt="Ты профессиональный копирайтер",
            model="gpt-4o-mini"
        )
        
        # Парсинг заголовков из ответа
        titles = [line.strip() for line in response.split('\n') if line.strip()]
        
        content_item.metadata['generated_titles'] = titles
        return content_item
```

### Пример блока для генерации текста статьи

```python
class ArticleTextBlock:
    def __init__(self):
        self.ai_client = GRSAIClient()
    
    def execute(self, content_item):
        """Генерация текста статьи"""
        
        title = content_item.metadata.get('selected_title', content_item.topic)
        
        prompt = f"""
        Заголовок: {title}
        Тема: {content_item.topic}
        Целевая аудитория: {content_item.target_audience}
        Желаемая длина: 1500-2000 слов
        
        Напиши полноценную статью с введением, основной частью и заключением.
        """
        
        # Используем потоковый режим для длинного текста
        article_text = ""
        for chunk in self.ai_client.chat_stream(
            messages=[
                {"role": "system", "content": "Ты профессиональный автор статей"},
                {"role": "user", "content": prompt}
            ],
            model="gemini-2.5-pro"  # Мощная модель для длинного текста
        ):
            article_text += chunk
        
        content_item.content['text'] = article_text
        return content_item
```

## Доступные модели

### Быстрые модели (для простых задач)
- `gpt-4o-mini` — рекомендуется для большинства задач
- `gemini-2.5-flash` — очень быстрая
- `gemini-2.5-flash-lite` — самая быстрая

### Мощные модели (для сложных задач)
- `gemini-2.5-pro` — лучшее качество
- `gemini-3-pro` — новейшая версия
- `gpt-4o-all` — универсальная мощная модель

### Простые модели
- `nano-banana-fast` — для очень простых задач
- `nano-banana` — базовая модель

## API Reference

### GRSAIClient

#### `__init__(api_key=None, config=None)`
Создание клиента. API ключ берется из параметра или переменной окружения `GRS_AI_API_KEY`.

#### `chat(messages, model=None, stream=False, temperature=None, max_tokens=None, use_fallback=True)`
Отправка запроса к API.

**Параметры:**
- `messages` (List[Dict]) — список сообщений в формате `[{"role": "user", "content": "текст"}]`
- `model` (str) — название модели
- `stream` (bool) — потоковый режим (используйте `chat_stream()` вместо этого)
- `temperature` (float) — температура генерации (0.0-2.0)
- `max_tokens` (int) — максимальное количество токенов
- `use_fallback` (bool) — использовать fallback модели при ошибке

**Возвращает:** строку с ответом

#### `chat_stream(messages, model=None, temperature=None, max_tokens=None)`
Потоковый режим генерации.

**Возвращает:** генератор, который выдает части текста

#### `simple_ask(question, system_prompt=None, model=None)`
Упрощенный метод для быстрых запросов.

**Параметры:**
- `question` (str) — вопрос пользователя
- `system_prompt` (str) — системный промпт (опционально)
- `model` (str) — модель для использования

**Возвращает:** строку с ответом

#### `get_available_models()` (classmethod)
Получить список доступных моделей.

**Возвращает:** словарь с категориями моделей

## Troubleshooting

### Проблема: Абракадабра вместо кириллицы
**Решение:** Клиент автоматически устанавливает `response.encoding = "utf-8"` и исправляет искаженную кодировку.

### Проблема: Пустой ответ
**Решение:** Клиент автоматически пробует fallback модели. Убедитесь, что `use_fallback=True`.

### Проблема: Timeout
**Решение:** Увеличьте timeout в конфигурации:
```python
config = GRSAIConfig(api_key="key", timeout=120)
client = GRSAIClient(config=config)
```

### Проблема: API ключ не найден
**Решение:** Убедитесь, что переменная окружения `GRS_AI_API_KEY` установлена или передайте ключ явно:
```python
client = GRSAIClient(api_key="your_key")
```

## Логирование

Клиент использует стандартный модуль `logging`:

```python
import logging

# Включить подробное логирование
logging.basicConfig(level=logging.INFO)

# Или только для GRS AI клиента
logger = logging.getLogger('Блоки.интеграции_ии.grs_ai_client')
logger.setLevel(logging.DEBUG)
```

## См. также

- [GRS_AI_API_INTEGRATION.md](../../GRS_AI_API_INTEGRATION.md) — полная документация по API
- [BLOCKS_REGISTRY.md](../../BLOCKS_REGISTRY.md) — реестр всех блоков
