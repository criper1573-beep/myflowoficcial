# NewsBot - Быстрый старт

## 🚀 За 3 шага

### 1. Установите зависимости

```bash
pip install python-telegram-bot feedparser googletrans==4.0.0-rc1
```

### 2. Настройте .env

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel
```

### 3. Запустите бота

**Windows (двойной клик):**
```
START_SPAMBOT.bat
```

**Или через командную строку:**
```bash
# Windows
scripts\run_spambot.bat

# Python напрямую
python -m blocks.spambot
```

Готово! Бот начнет публиковать посты каждые 2 минуты.

---

## 💡 Быстрые примеры

### Базовое использование

```python
from blocks.spambot import NewsBot

bot = NewsBot()
bot.start()
```

### Изменить интервал

```python
from blocks.spambot.newsbot import NewsBotConfig

config = NewsBotConfig(
    bot_token="your_token",
    channel_id="@channel",
    send_interval=300  # 5 минут
)

bot = NewsBot(config=config)
bot.start()
```

### Свои RSS ленты

```python
config = NewsBotConfig(
    bot_token="your_token",
    channel_id="@channel",
    rss_feeds=[
        "https://example.com/feed.xml",
        "https://another.com/rss",
    ]
)

bot = NewsBot(config=config)
bot.start()
```

### Свои хештеги

```python
config = NewsBotConfig(
    bot_token="your_token",
    channel_id="@channel",
    hashtag_options=[
        "#мойхештег1", "#мойхештег2", "#мойхештег3"
    ],
    hashtags_per_post=2
)

bot = NewsBot(config=config)
bot.start()
```

---

## 🛑 Остановка бота

Нажмите `Ctrl+C` - бот корректно завершит текущую итерацию и остановится.

---

## 📖 Полная документация

[README.md](README.md) - подробная документация со всеми параметрами
