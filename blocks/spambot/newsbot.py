"""
NewsBot - RSS-бот для автоматической публикации новостей в Telegram канал

Основные возможности:
- Чтение RSS-лент с фильтрацией по ключевым словам
- Автоматический перевод на русский язык
- Публикация только статей с изображениями
- Случайные хештеги для каждого поста
- Защита от дублирования постов
- Fallback на запасные ленты
- Graceful shutdown

Использование:
    from blocks.spambot import NewsBot
    
    bot = NewsBot(
        bot_token="your_token",
        channel_id="@your_channel"
    )
    bot.run()
"""

import asyncio
import calendar
import html
import json
import logging
import os
import re
import signal
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field

import feedparser
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import RetryAfter, TimedOut, NetworkError


logger = logging.getLogger(__name__)


@dataclass
class NewsBotConfig:
    """Конфигурация NewsBot"""
    
    # Telegram настройки
    bot_token: str
    channel_id: str
    
    # Интервалы и лимиты
    send_interval: int = 120  # секунд между постами
    max_caption_length: int = 1024  # лимит Telegram для caption
    repost_after_seconds: int = 7200  # не публиковать дубли в течение 2 часов
    last_posted_max: int = 5000  # хранить N ссылок в файле истории
    history_file: str = "blocks/spambot/newsbot_posted.json"  # файл истории (внутри блока)
    sleep_when_no_post: int = 60  # пауза если нет постов
    
    # Retry настройки
    max_retries: int = 3
    retry_base_delay: int = 15
    
    # CTA (Call To Action)
    cta_text: str = "\n\nПланируешь ремонт в офисе? Начни работать в новом кабинете уже через 10 дней\n"
    cta_link: str = "https://flowcabinet.ru"
    
    # Хештеги
    hashtag_options: List[str] = field(default_factory=lambda: [
        "#ремонт", "#ремонтквартиры", "#евроремонт", "#интерьер", "#дизайнинтерьера",
        "#офис", "#кабинет", "#отделка", "#строительство", "#перепланировка",
        "#мебель", "#освещение", "#санузел", "#кухня", "#гостиная", "#спальня",
        "#современныйинтерьер", "#отделочныеработы", "#ремонтподключ",
        "#квартира", "#дом", "#дизайн", "#интерьердома", "#ремонтофиса",
        "#офисныйремонт", "#рабочеепространство", "#переговорная",
    ])
    hashtags_per_post: int = 3
    
    # Приоритетные слова для фильтрации
    priority_words: List[str] = field(default_factory=lambda: [
        "ремонт", "офис", "интерьер", "кабинет",
        "рабочее пространство", "переговорная"
    ])
    
    # User-Agent для RSS запросов
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Максимальный возраст поста для публикации (секунды)
    max_post_age_seconds: int = 48 * 3600  # 48 часов
    
    # RSS ленты (основные; проблемные/не отвечающие удалены)
    rss_feeds: List[str] = field(default_factory=lambda: [
        "https://www.dezeen.com/interiors/feed/",
        "https://www.dezeen.com/design/feed/",
        "https://www.dezeen.com/architecture/feed/",
        # Reddit
        "https://www.reddit.com/r/InteriorDesign/.rss",
        "https://www.reddit.com/r/Workspaces/.rss",
        "https://www.reddit.com/r/OfficeDesign/.rss",
        "https://www.reddit.com/r/roomdetective/.rss",
        # Строительство и ремонт
        "https://rdstroy.ru/news/rss.xml",
        "https://www.design-milk.com/feed/",
        # Habr
        "https://habr.com/ru/rss/articles/",
        "https://habr.com/ru/rss/articles/top/daily/",
    ])
    
    # RSS ленты (запасные)
    rss_feeds_fallback: List[str] = field(default_factory=lambda: [
        "https://www.reddit.com/r/selfimprovement/.rss",
        "https://www.reddit.com/r/business/.rss",
        "https://www.reddit.com/r/Entrepreneur/.rss",
        "https://www.reddit.com/r/productivity/.rss",
        "https://www.reddit.com/r/GetMotivated/.rss",
        "https://www.reddit.com/r/Leadership/.rss",
        "https://www.reddit.com/r/careerguidance/.rss",
        "https://www.reddit.com/r/startups/.rss",
        "https://habr.com/ru/rss/articles/top/weekly/",
        "https://www.inc.com/rss/home",
    ])


class NewsBot:
    """
    RSS-бот для автоматической публикации новостей в Telegram
    
    Пример использования:
        bot = NewsBot(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            channel_id=os.getenv("TELEGRAM_CHANNEL_ID")
        )
        bot.run()
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        channel_id: Optional[str] = None,
        config: Optional[NewsBotConfig] = None
    ):
        """
        Инициализация бота
        
        Args:
            bot_token: Токен Telegram бота (или из переменной окружения TELEGRAM_BOT_TOKEN)
            channel_id: ID канала (или из переменной окружения TELEGRAM_CHANNEL_ID)
            config: Объект конфигурации (опционально)
        """
        # Создаем конфигурацию (config может содержать bot_token и channel_id)
        if config:
            self.config = config
            bot_token = bot_token or config.bot_token
            channel_id = channel_id or config.channel_id
        else:
            bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
            channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")
            if not bot_token:
                raise ValueError("Bot token must be provided or set in TELEGRAM_BOT_TOKEN environment variable")
            if not channel_id:
                raise ValueError("Channel ID must be provided or set in TELEGRAM_CHANNEL_ID environment variable")
            self.config = NewsBotConfig(
                bot_token=bot_token,
                channel_id=channel_id
            )
        
        # Инициализация
        self.bot: Optional[Bot] = None
        self._translator = None  # lazy: googletrans или deep_translator
        self.last_posted_at: Dict[str, float] = self._load_posted_history()
        self._shutdown = False
        self.current_feed_index = 0
        
        # Настройка логирования
        self._setup_logging()
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, self._request_shutdown)
        signal.signal(signal.SIGTERM, self._request_shutdown)
    
    def _setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.INFO
        )
    
    def _request_shutdown(self, *args, **kwargs):
        """Обработчик сигналов для graceful shutdown"""
        self._shutdown = True
        logger.info("Получен сигнал остановки. Завершение после текущей итерации...")

    def _history_path(self) -> Path:
        """Путь к файлу истории (в текущей рабочей директории)."""
        return Path(self.config.history_file)

    def _load_posted_history(self) -> Dict[str, float]:
        """Загрузка истории опубликованных постов из файла."""
        path = self._history_path()
        if not path.is_file():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            # только ссылки с числовым timestamp
            out = {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
            # удаляем устаревшие (старше repost_after_seconds)
            now = time.time()
            out = {k: t for k, t in out.items() if (now - t) < self.config.repost_after_seconds}
            # обрезаем до last_posted_max
            if len(out) > self.config.last_posted_max:
                sorted_items = sorted(out.items(), key=lambda x: x[1], reverse=True)
                out = dict(sorted_items[: self.config.last_posted_max])
            if out:
                logger.info("Загружено %s записей из истории постов", len(out))
            return out
        except Exception as e:
            logger.warning("Не удалось загрузить историю постов из %s: %s", path, e)
            return {}

    def _save_posted_history(self) -> None:
        """Сохранение истории опубликованных постов в файл."""
        path = self._history_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.last_posted_at, f, ensure_ascii=False, indent=0)
        except Exception as e:
            logger.warning("Не удалось сохранить историю постов в %s: %s", path, e)

    @staticmethod
    def clean_html(text: str) -> str:
        """Удаление HTML тегов, декодирование сущностей и очистка Reddit-подвала из текста"""
        if not text:
            return ""
        # Декодируем HTML-сущности (&#32; → пробел и т.д.)
        text = html.unescape(text)
        # Исправляем сломанные сущности типа "and#32;" (когда &amp; потерялся)
        text = re.sub(r"and#\d+;", " ", text)
        # Удаляем HTML-теги
        text = re.sub(r"<[^>]+>", "", text)
        # Убираем Reddit-подвал: всё от "представлено" / "submitted by" до конца
        text = re.sub(
            r"\s*(?:представлено|submitted by).*$",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # Убираем отдельные метки [ссылка], [комментарии], [link], [comments]
        text = re.sub(r"\s*\[(?:ссылка|link|комментарии|comments)\]\s*", " ", text, flags=re.IGNORECASE)
        # Убираем упоминания пользователя Reddit /u/...
        text = re.sub(r"\s*/u/[^\s\]\)]+", "", text)
        # Схлопываем пробелы и переносы
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    def _get_translator(self):
        """Ленивая инициализация переводчика: deep_translator или googletrans (deep_translator без конфликта httpx)."""
        if self._translator is not None:
            return self._translator
        try:
            from deep_translator import GoogleTranslator
            self._translator = ("deep_translator", GoogleTranslator(source="auto", target="ru"))
            return self._translator
        except Exception:
            pass
        try:
            from googletrans import Translator
            self._translator = ("googletrans", Translator())
            return self._translator
        except Exception as e:
            logger.warning("Нет переводчика (deep_translator/googletrans): %s", e)
            self._translator = ("none", None)
            return self._translator

    def translate_to_russian(self, text: str) -> str:
        """
        Перевод текста на русский язык
        
        Args:
            text: Текст для перевода
        
        Returns:
            Переведенный текст или исходный при ошибке
        """
        if not text or not text.strip():
            return text
        kind, trans = self._get_translator()
        try:
            if kind == "googletrans":
                result = trans.translate(text, dest="ru")
                return result.text if result else text
            if kind == "deep_translator":
                return trans.translate(text) or text
        except Exception as e:
            logger.warning("Ошибка перевода: %s", e)
        return text
    
    async def translate_to_russian_async(self, text: str) -> str:
        """Асинхронный перевод текста"""
        return await asyncio.to_thread(self.translate_to_russian, text)
    
    @staticmethod
    def extract_image(entry) -> Optional[str]:
        """
        Извлечение URL изображения из RSS записи
        
        Args:
            entry: RSS запись из feedparser
        
        Returns:
            URL изображения или None
        """
        # Media RSS
        if "media_content" in entry and entry.media_content:
            url = entry.media_content[0].get("url")
            if url:
                return url
        
        # Media thumbnail
        if "media_thumbnail" in entry and entry.media_thumbnail:
            url = entry.media_thumbnail[0].get("url")
            if url:
                return url
        
        # Links
        if "links" in entry:
            for link in entry.links:
                if link.get("type", "").startswith("image"):
                    return link.get("href")
        
        # Enclosures
        if "enclosures" in entry:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image"):
                    return enc.get("href")
        
        return None
    
    def truncate_caption(self, text: str) -> str:
        """Обрезка текста до максимальной длины caption"""
        max_len = self.config.max_caption_length
        if len(text) <= max_len:
            return text
        return text[: max_len - 3].rstrip() + "..."
    
    def pick_hashtags(self) -> str:
        """Случайный выбор хештегов для поста"""
        k = min(self.config.hashtags_per_post, len(self.config.hashtag_options))
        chosen = random.sample(self.config.hashtag_options, k)
        return " ".join(chosen)
    
    def can_repost_link(self, link: str) -> bool:
        """
        Проверка, можно ли публиковать ссылку
        
        Args:
            link: URL статьи
        
        Returns:
            True если можно публиковать
        """
        if link not in self.last_posted_at:
            return True
        return (time.time() - self.last_posted_at[link]) >= self.config.repost_after_seconds
    
    def prune_last_posted(self):
        """Очистка старых записей из кэша опубликованных ссылок."""
        if len(self.last_posted_at) <= self.config.last_posted_max:
            return
        # Оставляем только последние записи
        sorted_items = sorted(self.last_posted_at.items(), key=lambda x: x[1], reverse=True)
        self.last_posted_at = dict(sorted_items[: self.config.last_posted_max])
    
    async def send_post(self, title: str, summary: str, link: str, image_url: str) -> bool:
        """
        Отправка поста в Telegram канал
        
        Args:
            title: Заголовок статьи
            summary: Краткое описание
            link: Ссылка на статью
            image_url: URL изображения
        
        Returns:
            True если пост отправлен успешно
        """
        if self.bot is None:
            self.bot = Bot(token=self.config.bot_token)
        
        # Формируем текст поста
        read_more = f'<a href="{html.escape(link)}">Читать далее</a>'
        cta_link = f'<a href="{self.config.cta_link}">flowcabinet.ru</a>'
        hashtags = self.pick_hashtags()
        
        text = (
            f"{html.escape(title)}\n\n"
            f"{html.escape(summary)}\n\n"
            f"{read_more}{self.config.cta_text}{cta_link}\n\n"
            f"{hashtags.strip()}"
        )
        text = self.truncate_caption(text)
        
        # Отправка с retry
        for attempt in range(1, self.config.max_retries + 1):
            try:
                await self.bot.send_photo(
                    chat_id=self.config.channel_id,
                    photo=image_url,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                )
                logger.info("Пост отправлен: %s", title[:50])
                return True
            
            except RetryAfter as e:
                wait = e.retry_after
                logger.warning("Telegram просит подождать %s сек.", wait)
                await asyncio.sleep(wait)
            
            except (TimedOut, NetworkError) as e:
                delay = self.config.retry_base_delay * attempt
                logger.warning(
                    "Сетевая ошибка (попытка %s/%s): %s. Повтор через %s сек.",
                    attempt, self.config.max_retries, e, delay
                )
                await asyncio.sleep(delay)
            
            except Exception as e:
                logger.exception("Ошибка отправки поста: %s", e)
                return False
        
        return False
    
    def _entry_within_max_age(self, entry) -> bool:
        """True, если дата публикации записи не старше max_post_age_seconds (48 ч)."""
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if not parsed:
            return False
        try:
            # feedparser часто отдаёт UTC
            ts = calendar.timegm(parsed)
        except (TypeError, ValueError):
            return False
        return (time.time() - ts) <= self.config.max_post_age_seconds
    
    async def fetch_feed(self, url: str):
        """Асинхронная загрузка RSS ленты"""
        return await asyncio.to_thread(
            feedparser.parse,
            url,
            request_headers={"User-Agent": self.config.user_agent},
            response_headers=None,
        )
    
    async def process_feed(self, feed_url: str, max_entries: int = 10) -> Tuple[bool, Optional[Tuple]]:
        """
        Обработка одной RSS ленты
        
        Args:
            feed_url: URL ленты
            max_entries: Максимальное количество статей для проверки
        
        Returns:
            (article_sent, chosen_entry) - был ли отправлен пост и выбранная запись
        """
        logger.info("Проверяем ленту: %s", feed_url)
        
        try:
            feed = await self.fetch_feed(feed_url)
        except Exception as e:
            logger.warning("Ошибка загрузки ленты %s: %s", feed_url, e)
            return False, None
        
        entries = getattr(feed, "entries", [])[:max_entries]
        logger.info("Найдено статей: %s", len(entries))
        
        priority_entry = None
        fallback_entry = None
        
        for entry in entries:
            link = entry.get("link")
            
            # Только актуальные: не старше 48 часов
            if not self._entry_within_max_age(entry):
                continue
            
            # Проверка на дубликат
            if not self.can_repost_link(link):
                continue
            
            # Только статьи с изображениями
            image_url = self.extract_image(entry)
            if not image_url:
                continue
            
            # Получаем заголовок и описание
            title = entry.get("title", "")
            summary = entry.get("summary") or entry.get("description") or ""
            if not summary and entry.get("content"):
                summary = entry.content[0].get("value", "")
            
            if not title or not summary:
                continue
            
            title_clean = self.clean_html(title)
            summary_clean = self.clean_html(summary)
            title_lower = title_clean.lower()
            
            # Проверка приоритетных слов
            if any(word in title_lower for word in self.config.priority_words):
                priority_entry = (entry, title_clean, summary_clean, image_url)
                break
            
            if fallback_entry is None:
                fallback_entry = (entry, title_clean, summary_clean, image_url)
        
        chosen = priority_entry or fallback_entry
        
        if chosen:
            entry, title, summary, image_url = chosen
            link = entry.link
            
            # Перевод на русский
            title_ru = await self.translate_to_russian_async(title)
            summary_ru = await self.translate_to_russian_async(summary)
            
            # Отправка поста
            if await self.send_post(title_ru, summary_ru, link, image_url):
                self.last_posted_at[link] = time.time()
                self.prune_last_posted()
                self._save_posted_history()
                return True, chosen
        
        return False, None
    
    async def run(self):
        """Основной цикл работы бота"""
        logger.info(
            "RSS бот запущен. Канал: %s, интервал: %s сек.",
            self.config.channel_id,
            self.config.send_interval
        )
        
        while not self._shutdown:
            article_sent = False
            
            # Проход по основным лентам
            for _ in range(len(self.config.rss_feeds)):
                if self._shutdown:
                    break
                
                feed_url = self.config.rss_feeds[self.current_feed_index]
                sent, _ = await self.process_feed(feed_url)
                
                if sent:
                    article_sent = True
                    break
                
                self.current_feed_index = (self.current_feed_index + 1) % len(self.config.rss_feeds)
            
            # Если не нашли - пробуем запасные ленты
            if not article_sent and not self._shutdown:
                logger.info("По основным лентам постов нет. Проверяем запасные ленты...")
                
                for feed_url in self.config.rss_feeds_fallback:
                    if self._shutdown or article_sent:
                        break
                    
                    sent, _ = await self.process_feed(feed_url, max_entries=15)
                    
                    if sent:
                        article_sent = True
                        logger.info("Пост из запасной ленты: %s", feed_url)
                        break
                    
                    await asyncio.sleep(1)
            
            # Пауза перед следующей итерацией
            if article_sent:
                await asyncio.sleep(self.config.send_interval)
            else:
                logger.info("Новых постов нет. Пауза %s сек.", self.config.sleep_when_no_post)
                await asyncio.sleep(self.config.sleep_when_no_post)
        
        logger.info("Бот остановлен.")
    
    def start(self):
        """Запуск бота (синхронная обертка)"""
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")


# Пример использования
if __name__ == "__main__":
    # Создание бота
    bot = NewsBot(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        channel_id=os.getenv("TELEGRAM_CHANNEL_ID")
    )
    
    # Запуск
    bot.start()
