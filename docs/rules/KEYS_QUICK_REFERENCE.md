# Ключи и токены - Краткая справка

Быстрый справочник по всем ключам проекта.

Полная версия: [KEYS_AND_TOKENS.md](KEYS_AND_TOKENS.md)

---

## 🔑 Активные ключи (обязательные)

### 1. GRS AI API
```env
GRS_AI_API_KEY=your_key
GRS_AI_API_URL=https://grsaiapi.com
```
**Где:** https://grsai.com/dashboard  
**Для:** Генерация контента через AI

### 2. Telegram Bot
```env
TELEGRAM_BOT_TOKEN=1234567890:ABC...
TELEGRAM_CHANNEL_ID=@channel_name
```
**Где:** https://t.me/BotFather  
**Для:** NewsBot автопостинг

---

## 🔑 Опциональные ключи

### OpenAI
```env
OPENAI_API_KEY=sk-...
```
**Где:** https://platform.openai.com/api-keys

### Yandex GPT
```env
YANDEX_API_KEY=your_key
YANDEX_FOLDER_ID=folder_id
```
**Где:** https://cloud.yandex.ru/

### VK API
```env
VK_ACCESS_TOKEN=token
VK_GROUP_ID=123456789
```
**Где:** https://vk.com/apps?act=manage

---

## 📁 Где хранить

**Файл:** `.env` (в корне проекта)

**Создать:**
```bash
copy .env.example .env
```

**Проверить:**
```bash
# .env должен быть в .gitignore
cat .gitignore | grep .env
```

---

## 💻 Использование в коде

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GRS_AI_API_KEY")
if not API_KEY:
    raise ValueError("GRS_AI_API_KEY not found in .env")
```

---

## ⚠️ Безопасность

### ✅ МОЖНО:
- Хранить в `.env`
- Коммитить `.env.example`
- Документировать назначение

### ❌ НЕЛЬЗЯ:
- Коммитить `.env`
- Хардкодить в коде
- Отправлять в мессенджерах

---

## 🆘 При утечке ключа

1. ✅ Отозвать ключ в сервисе
2. ✅ Создать новый ключ
3. ✅ Обновить `.env`
4. ✅ Перезапустить боты
5. ✅ Удалить из Git истории

---

## 📖 Полная документация

[KEYS_AND_TOKENS.md](KEYS_AND_TOKENS.md) - подробная документация всех ключей
