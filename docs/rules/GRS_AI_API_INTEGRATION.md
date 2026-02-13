# GRS AI API Integration Guide

## Базовая информация

- **Документация**: https://grsai.com/dashboard/documents/chat
- **Base URL**: `https://grsaiapi.com`
- **Endpoint**: `https://grsaiapi.com/v1/chat/completions`

> **Совместимость с OpenAI**: Если ранее использовали OpenAI API, просто замените `https://api.openai.com/v1/chat/completions` на `https://grsaiapi.com/v1/chat/completions`

---

## Аутентификация

### Заголовки запроса

```http
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

API ключ получается в личном кабинете GRS AI.

### Переменные окружения

Рекомендуется хранить настройки в `.env`:

```env
GRS_AI_API_URL=https://grsaiapi.com
GRS_AI_API_KEY=ваш_ключ_api
```

---

## Формат запроса

**ВАЖНО**: Используйте только указанные поля. GRS AI может не понимать дополнительные параметры.

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "Ты помощник."},
    {"role": "user", "content": "Привет!"}
  ],
  "stream": false
}
```

### Параметры

- `model` — название модели (см. список ниже)
- `messages` — массив сообщений с ролями (`system`, `user`, `assistant`)
- `stream` — `true` для потокового ответа, `false` для полного ответа

---

## Доступные модели

### Быстрые модели
- `gpt-4o-mini`
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`

### Мощные модели
- `gemini-2.5-pro`
- `gemini-3-pro`
- `gpt-4o-all`

### Простые модели
- `nano-banana-fast`
- `nano-banana`

**Рекомендация**: Для большинства задач используйте `gpt-4o-mini` или `gemini-2.5-flash`.

---

## Парсинг ответа

GRS AI может возвращать ответ в разных форматах. Проверяйте поля в следующем порядке:

```python
# Порядок проверки полей в ответе
response_text = (
    response.get("choices", [{}])[0].get("message", {}).get("content") or
    response.get("data", {}).get("output", {}).get("text") or
    response.get("output", {}).get("text") or
    response.get("response") or
    response.get("content") or
    response.get("text") or
    ""
)
```

---

## Обработка кодировки (КРИТИЧНО!)

### Проблема

Кириллица иногда приходит в UTF-8, но читается как Latin-1, что приводит к абракадабре (символы типа Ð, Ñ, Â).

### Решение

1. **Явно задать кодировку при получении ответа:**

```python
response.encoding = "utf-8"
```

2. **Если текст уже искажён:**

```python
# Если видите символы Ð, Ñ, Â вместо кириллицы
fixed_text = broken_text.encode("latin-1").decode("utf-8")
```

---

## Обработка ошибок

### Типы ошибок

1. **API ошибка** — `code != 0` в JSON
   - Проверяйте поле `msg` для описания ошибки

2. **Пустой content** — модель не вернула ответ
   - Часто происходит при длинном контексте
   - Решение: повторить запрос с другой моделью

### Стратегия fallback

```python
# Рекомендуемый порядок fallback моделей
fallback_models = ["gpt-4o-mini", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
```

### Пример обработки

```python
if response.get("code") != 0:
    error_msg = response.get("msg", "Unknown error")
    raise Exception(f"GRS AI API Error: {error_msg}")

if not response_text:
    # Попробовать другую модель или вернуть ошибку
    raise Exception("Empty response from model")
```

---

## Пример использования (Python)

### С библиотекой requests

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://grsaiapi.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('GRS_AI_API_KEY')}",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "Ты полезный ассистент."},
        {"role": "user", "content": "Привет! Как дела?"}
    ],
    "stream": False
}

try:
    response = requests.post(url, json=data, headers=headers, timeout=60)
    response.encoding = "utf-8"  # ВАЖНО для кириллицы
    result = response.json()
    
    # Парсинг ответа
    text = (
        result.get("choices", [{}])[0].get("message", {}).get("content") or
        result.get("data", {}).get("output", {}).get("text") or
        result.get("response", "")
    )
    
    if not text:
        raise Exception("Empty response from API")
    
    print(text)
    
except requests.exceptions.Timeout:
    print("Request timeout - try again or use different model")
except Exception as e:
    print(f"Error: {e}")
```

### С потоковым ответом (stream=true)

```python
data = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Расскажи историю"}],
    "stream": True
}

response = requests.post(url, json=data, headers=headers, stream=True, timeout=60)
response.encoding = "utf-8"

for line in response.iter_lines():
    if line:
        # Обработка SSE формата
        if line.startswith(b"data: "):
            chunk = line[6:].decode("utf-8")
            if chunk != "[DONE]":
                try:
                    data = json.loads(chunk)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        print(delta, end="", flush=True)
                except json.JSONDecodeError:
                    continue
```

---

## Чеклист интеграции

- [ ] Получить API ключ в личном кабинете GRS AI
- [ ] Добавить `GRS_AI_API_KEY` в `.env`
- [ ] Использовать только поддерживаемые поля в запросе
- [ ] Установить `response.encoding = "utf-8"`
- [ ] Реализовать парсинг ответа с проверкой всех возможных полей
- [ ] Добавить обработку ошибок и fallback модели
- [ ] Установить разумный timeout (60+ секунд)
- [ ] Протестировать с кириллицей

---

## Troubleshooting

### Проблема: Абракадабра вместо кириллицы
**Решение**: Установите `response.encoding = "utf-8"` перед `response.json()`

### Проблема: Пустой ответ
**Решение**: Попробуйте другую модель из списка fallback

### Проблема: Timeout
**Решение**: Увеличьте timeout до 90-120 секунд или используйте более быструю модель

### Проблема: Ошибка "Invalid parameters"
**Решение**: Убедитесь, что используете только поля `model`, `messages`, `stream`
