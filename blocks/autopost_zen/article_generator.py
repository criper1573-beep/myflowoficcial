# -*- coding: utf-8 -*-
"""
Генератор статей для Дзен: тема из Google Sheets → GRS AI текст → GRS AI картинки → article.json.
Промпты из docs/guides/BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md, адаптированы под flowcabinet.ru.
"""
import base64
import json
import logging
import os
import re
import shutil
import sys
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
PUBLISH_DIR = BLOCK_DIR / "publish"
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Google Sheets (переиспользуем credentials из post_flow)
# ──────────────────────────────────────────────
_CREDS_DEFAULT = str(Path(__file__).resolve().parent.parent / "post_flow" / "credentials.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1gxYpX1FGm5VwtyUoZNKdd8EVYduvkmULpXL5TuOv5z4")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", _CREDS_DEFAULT)
if not os.path.isabs(GOOGLE_CREDENTIALS_PATH):
    GOOGLE_CREDENTIALS_PATH = str(PROJECT_ROOT / GOOGLE_CREDENTIALS_PATH)
ZEN_TOPICS_SHEET_NAME = os.getenv("ZEN_TOPICS_SHEET_NAME", "Лист2")

# ──────────────────────────────────────────────
# GRS AI модели
# ──────────────────────────────────────────────
ZEN_ARTICLE_MODEL = os.getenv("ZEN_ARTICLE_MODEL", "gemini-2.5-pro")
ZEN_HEADLINE_MODEL = os.getenv("ZEN_HEADLINE_MODEL", "gpt-4o-mini")
ZEN_IMAGE_MODEL = os.getenv("ZEN_IMAGE_MODEL", "gpt-image-1")

# ──────────────────────────────────────────────
# Обложка: референсные фото из blueprint
# ──────────────────────────────────────────────
COVER_REF_FACE = os.getenv(
    "ZEN_COVER_REF_FACE",
    "https://i.postimg.cc/jdwFhwpV/photo_2026_02_05_10_46_02.jpg",
)
COVER_REF_EXTRA = [
    "https://mayai.ru/wp-content/uploads/2025/11/06bd46d4-89a4-4ad3-bf87-a84adbf8d952.jpg",
    "https://mayai.ru/wp-content/uploads/2025/11/c410cce6a3fa9f9d28915004e46e1c57.jpg",
    "https://mayai.ru/wp-content/uploads/2025/11/3557247553f3360809d41bb5c4ae311c.jpg",
]

# Ссылки только на наши ресурсы (запрет сторонних в статьях)
# Баннер: файл в blocks/autopost_zen/articles/, при сборке копируется в папку статьи — вставка как обложка (по пути)
BANNER_IMAGE_FILENAME = "reklamnyj-banner.png"
TELEGRAM_CHANNEL_URL = "https://t.me/myflowofficial"
SITE_URL = "https://flowcabinet.ru"


def _get_sheets_client():
    """Создаёт клиент gspread с сервисным аккаунтом (переиспользуем credentials из post_flow)."""
    import gspread
    from google.oauth2.service_account import Credentials

    path = GOOGLE_CREDENTIALS_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Файл ключей Google не найден: {path}\n"
            "Ожидается blocks/post_flow/credentials.json или путь в GOOGLE_CREDENTIALS_PATH."
        )
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(path, scopes=scopes)
    return gspread.authorize(creds)


def _get_grs_client():
    """Создаёт GRS AI клиент."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from blocks.ai_integrations.grs_ai_client import GRSAIClient
    return GRSAIClient()


# =====================================================================
#  ПРОМПТЫ (адаптированы под flowcabinet.ru из BLUEPRINT + новая структура)
# =====================================================================

PROMPT_SEEDS = """Ты — эксперт по семантике и подбору ключевых запросов под Яндекс.Вордстат.

ЗАДАЧА: по теме статьи выдели РОВНО 3 коротких поисковых запроса («сида») для SEO.

ВХОД
ТЕМА: {topic}

ТРЕБОВАНИЯ:
- Коротко: 1–2 слова (макс. 3), без кликбейта.
- Сохраняй тему и намерение (инфо/коммерция).
- Нормализация: разговорная форма, ед. число, именительный падеж.
- 1-й — самый широкий «ядровой», 2-й — уточнённый, 3-й — по намерению (как/ремонт/цена и т.п.).
- Язык: русский, строчные.

ВЫВОД: только JSON с полями k1, k2, k3 (строки). Без пояснений.
Пример: {{"k1": "ремонт офиса", "k2": "офис под ключ", "k3": "дизайн офиса"}}"""

PROMPT_HEADLINE = """# SEO-заголовок для Дзена

РОЛЬ
Ты — SEO-редактор заголовков. Получаешь тему и ключевые слова. Цель: CTR без кликбейта, раннее вхождение ключа.

ВХОД
ТЕМА = "{topic}"
КЛЮЧЕВЫЕ СЛОВА (из Вордстата/сидов): {keywords}

ПРАВИЛА
- Длина: 50–65 символов (макс. 80).
- Ключевая фраза — в начале или до «:», в первых ~35 символах.
- Одно точное вхождение основного ключа, при необходимости один вторичный ключ — естественно.
- Дзен-safe: без «шок», «вы не поверите», капслока, «!!!».
- Язык: русский. Тематика: офис, ремонт, дизайн, flowcabinet.ru.

ВЫВОД
Верни ТОЛЬКО один финальный заголовок. Без кавычек, комментариев — ровно одна строка."""

PROMPT_ARTICLE = """Ты — эксперт по офисным пространствам и ремонту. Пишешь живо, экспертно, с лёгкой иронией. Без «нейро»-оборотов, без воды.

ЗАДАЧА: написать статью для Яндекс.Дзен по СТРОГОЙ структуре ниже.

ЗАГОЛОВОК (держи в уме, НЕ выводи в текст): {headline}
ТЕМА: {topic}
КЛЮЧЕВЫЕ СЛОВА (вплетай органично для SEO): {keywords}

СТРУКТУРА СТАТЬИ (строго по порядку):

1. Введение — 2–3 абзаца <p>. Контекст темы, зачем читать, что получит читатель. Без заголовка.

2. Основной блок по теме — 3–4 секции, каждая:
   - <h3> подзаголовок (только текст, без нумерации)
   - <p> абзац (длина разная: то 2–3 предложения, то 4–5 — не шаблонно)
   - Список: чередуй формат — то <ul> (маркированный), то <ol> (нумерованный); где уместно — 3 пункта, где детальнее — 5–6. Выделяй ключевые мысли в <strong> внутри <li> или <p>, чтобы текст выглядел живым и «очеловеченным».

3. Пошаговый блок — полезный совет по теме. Заголовок h3 по смыслу (например «Как выбрать потолок» или «Подготовка стен»), без обязательного слова «Инструкция».
   - <h3>[название блока по теме]</h3>
   - <p>Краткое введение к шагам.</p>
   - Шаги пиши НЕ нумерованным списком <ol>, а отдельными абзацами <p>. Каждый шаг: сначала жирным «ШАГ N.» (например <p><strong>ШАГ 1.</strong> Текст первого шага.</p>), 5–7 шагов. После третьего шага выведи ровно одну строку маркера: <!-- BANNER -->, затем продолжай <p><strong>ШАГ 4.</strong> Текст.</p> и т.д.
   Пример: <p><strong>ШАГ 1.</strong> Текст первого шага.</p><p><strong>ШАГ 2.</strong> Текст второго шага.</p><p><strong>ШАГ 3.</strong> Текст.</p><!-- BANNER --><p><strong>ШАГ 4.</strong> Текст.</p>

4. Тренды по теме на 2026 — <h3>Тренды 2026</h3>, затем 1–2 абзаца <p> и/или <ul>. Без ссылок на внешние источники.

5. Ссылки на наши каналы (только наши, никаких сторонних):
   - <p>Подпишись на наш <a href="https://t.me/myflowofficial">Telegram-канал</a></p>
   - <p>Планируешь ремонт в офисе? Начни работать в новом кабинете уже через 10 дней. <a href="https://flowcabinet.ru">Узнать подробнее</a></p>

6. FAQ — <h3>Частые вопросы</h3>, затем 4–6 пар: каждый вопрос обязательно в <p><strong>Текст вопроса?</strong></p> (без слова «Вопрос», только сам вопрос жирным), ответ — в <p>Обычный текст ответа...</p>. Вопросы по теме статьи.

ТРЕБОВАНИЯ:
- Объём: 5000–7500 символов.
- По всему тексту выделяй ключевые смысловые слова и термины жирным (<strong>): важные понятия, цифры, названия, советы — чтобы читатель мог сканировать текст глазами.
- Очеловеченный стиль: блоки должны различаться — не все списки одинаковые (чередуй ul/ol, разное число пунктов), абзацы разной длины, используй <strong> для акцентов. Как у живого автора: выделения, ритм, без ощущения «шаблона».
- HTML: только <p>, <h3>, <ul>, <ol>, <li>, <a href="...">, <strong>. Без <div>, <span>, inline-стилей, <h1>, <h2>.
- SEO/GEO: органично вплетай ключевые слова; прямой ответ в первом абзаце (Zero-Click).
- ЗАПРЕЩЕНО: эмодзи, штампы («в современном мире», «давайте разберемся», «подводя итог»), упоминание ИИ, ссылки на сторонние сайты — только https://t.me/myflowofficial и https://flowcabinet.ru
- Каждый тег верхнего уровня (<p>, <h3>, <ul>, <ol>) — отдельный фрагмент на своей строке.

ФОРМАТ ВЫВОДА:
Чистый HTML без обёрток ```html, без <body>/<html>. Каждый блок на новой строке. Без H1. Обязательно включи маркер <!-- BANNER --> внутри инструкции после 3–4 шага."""

PROMPT_META_DESCRIPTION = """Создай короткое мета-описание для Яндекс.Дзен строго по содержанию фрагмента ниже.
Текст статьи (фрагмент): {text_fragment}

Требования:
- 100–140 символов.
- Описывай только то, о чём реально написано в фрагменте. Без общих фраз про SEO, маркетинг, «узнайте как» — только суть статьи.
- Один предложение, без кавычек."""

PROMPT_TELEGRAM_SUMMARY = """Ты — редактор. Прочитай текст ниже и напиши краткий анонс для Telegram-канала.

Текст:
{text_fragment}

СТРОГИЕ ПРАВИЛА:
- 400–700 символов.
- Пиши ТОЛЬКО о содержании текста выше: о чём статья, какие советы, факты, шаги приведены.
- ЗАПРЕЩЕНО упоминать: SEO, копирайтинг, Дзен, HTML-теги, структуру статьи, чек-листы для контента, процесс написания, ключевые слова. Если в тексте нет этих тем — их не должно быть в анонсе.
- НЕ описывай процесс создания статьи. Описывай то, что читатель узнает из статьи.
- Стиль: по делу, простым языком, как краткий пересказ. Без кавычек в начале и конце.
- Верни ТОЛЬКО текст анонса, без пояснений."""

PROMPT_TAGS = """Из заголовка и темы статьи извлеки 5–7 тегов для Яндекс.Дзен.
Заголовок: {headline}
Тема: {topic}

Требования:
- Короткие (1–3 слова), без # и кавычек.
- Релевантные: офис, ремонт, дизайн, кабинет и т.п.
- Верни JSON-массив строк, например: ["тег1", "тег2", "тег3"]
- ТОЛЬКО JSON, без пояснений."""

PROMPT_IMAGE = """Сгенерируй реалистичное фото для статьи о: {section_title}.
Контекст статьи: {headline}.
Стиль: современное фото высокого качества, офисный интерьер, яркие цвета, профессиональная съёмка.
Никаких текстов, водяных знаков, логотипов на изображении.
Фокус: {section_title}."""

# Промпт обложки из blueprint (generate_zen_cover.py)
PROMPT_COVER = r"""Main Objective: Create a HYPER-REALISTIC ACTION SELFIE photo cover for an article.
Theme: {topic}

STRICT VISUAL STYLE:
A photorealistic wide-angle selfie shot of the main hero (from reference), blending seamlessly with historical events/personalities based on the theme.
Captured with a 24mm wide-angle lens to capture both the hero's face and the dynamic background.
The image must look like a real, candid moment captured in time, NOT an illustration.

SUBJECT & COMPOSITION:
CRITICAL — FACE: The first reference image is the author. You MUST preserve this EXACT face.
The main hero making a funny/cool expression reacting to the event behind him.
- Do NOT show any phone, smartphone, or mobile device in the image. No phones at all.
- Clothing: Era-accurate costume blended with modern stylish elements.
- Face: Ultra-sharp focus. Visible skin pores, realistic eye reflections.
- NO cap, NO hood.

ENVIRONMENT & CONTEXT:
The background depicts a vivid scene relevant to: {topic}.
- Action: Dynamic movement, relevant to the article theme.
- Props: 100% era-accurate details.

TYPOGRAPHY & BRANDING:
- Headline: Short title from theme "{topic}". May wrap to 2–3 lines.
- CRITICAL — spelling: Write every word EXACTLY as in Russian.
- Language: All visible text MUST be in Russian Cyrillic.
- Footer: Subtle Telegram logo at the very bottom.

TECHNICAL:
- HORIZONTAL 16:9 landscape orientation. Width is much greater than height.
- 8k resolution, raw photo quality.
- Sharp face, slightly softer background.

NEGATIVE PROMPT:
Drawing, painting, illustration, 3d render, cartoon, anime, sketch, plastic skin, blurry face, bad eyes, distorted hands, watermark, latin letters, english text."""


# =====================================================================
#  ArticleGenerator
# =====================================================================

class ArticleGenerator:
    """Генератор статей: тема → заголовок → текст → картинки → article.json."""

    def __init__(self):
        self._grs = None

    @property
    def grs(self):
        if self._grs is None:
            self._grs = _get_grs_client()
        return self._grs

    # ── 1. Google Sheets ────────────────────────────────
    def fetch_topic(self, sheet_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Читает первую тему из Лист2. Возвращает (topic, extra_context, row_index) или (None, None, None)."""
        sheet_name = sheet_name or ZEN_TOPICS_SHEET_NAME
        client = _get_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(sheet_name)
        col_a = sheet.col_values(1)
        col_b = sheet.col_values(2) if len(sheet.row_values(1)) > 1 else []
        for i, cell in enumerate(col_a, start=1):
            val = (cell or "").strip()
            if val:
                extra = (col_b[i - 1] if i <= len(col_b) else "").strip()
                logger.info("Тема из таблицы (строка %d): %s", i, val)
                return val, extra, i
        logger.warning("Нет тем в листе '%s'", sheet_name)
        return None, None, None

    def delete_topic(self, row_index: int, sheet_name: Optional[str] = None) -> None:
        """Удаляет строку с темой после публикации."""
        sheet_name = sheet_name or ZEN_TOPICS_SHEET_NAME
        client = _get_sheets_client()
        sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(sheet_name)
        sheet.delete_rows(row_index)
        logger.info("Удалена строка %d из '%s'", row_index, sheet_name)

    # ── 2. Заголовок ────────────────────────────────────
    def generate_headline(self, topic: str, keywords: str = "") -> str:
        """Генерирует SEO-заголовок через GRS AI (с ключевыми словами для SEO)."""
        prompt = PROMPT_HEADLINE.format(topic=topic, keywords=keywords or topic)
        result = self.grs.simple_ask(prompt, model=ZEN_HEADLINE_MODEL)
        headline = result.strip().strip('"').strip("'").strip()
        if len(headline) > 80:
            headline = headline[:77] + "..."
        logger.info("Заголовок: %s", headline)
        return headline

    # ── 2a. Сиды для Wordstat ────────────────────────────
    def generate_seeds(self, topic: str) -> Tuple[str, str, str]:
        """Генерирует 3 поисковых сида (k1, k2, k3) для Wordstat/SEO."""
        prompt = PROMPT_SEEDS.format(topic=topic)
        result = self.grs.simple_ask(prompt, model=ZEN_HEADLINE_MODEL)
        try:
            match = re.search(r'\{[^{}]*"k1"[^{}]*\}', result)
            if match:
                data = json.loads(match.group())
                return (
                    str(data.get("k1", topic)).strip() or topic,
                    str(data.get("k2", "")).strip(),
                    str(data.get("k3", "")).strip(),
                )
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: тема как первый сид
        return (topic, "", "")

    # ── 3. Текст статьи ────────────────────────────────
    def generate_article(self, headline: str, topic: str, keywords: str = "") -> str:
        """Генерирует HTML текст статьи. Возвращает сырой HTML."""
        prompt = PROMPT_ARTICLE.format(
            headline=headline, topic=topic, keywords=keywords or topic
        )
        messages = [
            {"role": "system", "content": "Ты — SEO-копирайтер для Яндекс.Дзен, тематика: офисные пространства и ремонт (flowcabinet.ru). Ссылки только на flowcabinet.ru и t.me/myflowofficial."},
            {"role": "user", "content": prompt},
        ]
        result = self.grs.chat(messages=messages, model=ZEN_ARTICLE_MODEL, temperature=0.7)
        html = result.strip()
        html = re.sub(r"^```html?\s*\n?", "", html)
        html = re.sub(r"\n?```\s*$", "", html)
        logger.info("Текст статьи: %d символов", len(html))
        return html

    def generate_meta_description(self, article_html: str) -> str:
        """Генерирует короткое мета-описание для Дзен строго по содержанию статьи."""
        fragment = re.sub(r"<[^>]+>", " ", article_html)[:800].strip()
        prompt = PROMPT_META_DESCRIPTION.format(text_fragment=fragment)
        result = self.grs.simple_ask(prompt, model=ZEN_HEADLINE_MODEL)
        desc = result.strip().strip('"').strip("'").strip()
        if len(desc) > 160:
            desc = desc[:157] + "..."
        logger.info("Meta description: %s", desc[:60])
        return desc

    def generate_telegram_summary(self, article_html: str) -> str:
        """Генерирует саммари для Telegram (400–700 символов) строго по содержанию статьи.
        Из фрагмента убираются все HTML-теги, чтобы модель не описывала «HTML-структуру»."""
        # Убираем все HTML-теги и лишние пробелы, чтобы модель видела только текст
        clean = re.sub(r"<[^>]+>", " ", article_html)
        clean = re.sub(r"\s{2,}", " ", clean).strip()
        fragment = clean[:3000]
        prompt = PROMPT_TELEGRAM_SUMMARY.format(text_fragment=fragment)
        result = self.grs.simple_ask(prompt, model=ZEN_HEADLINE_MODEL)
        summary = result.strip().strip('"').strip("'").strip()
        if len(summary) > 750:
            summary = summary[:747] + "…"
        logger.info("Telegram summary: %d символов", len(summary))
        return summary

    def generate_tags(self, headline: str, topic: str) -> List[str]:
        """Генерирует теги из заголовка и темы."""
        prompt = PROMPT_TAGS.format(headline=headline, topic=topic)
        result = self.grs.simple_ask(prompt, model=ZEN_HEADLINE_MODEL)
        try:
            # Извлекаем JSON из ответа
            match = re.search(r'\[.*?\]', result, re.DOTALL)
            if match:
                tags = json.loads(match.group())
                if isinstance(tags, list):
                    return [str(t).strip() for t in tags[:7]]
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: разбиваем по запятым
        return [t.strip().strip('"') for t in result.split(",")][:7]

    # ── 4. Парсер HTML → content_blocks ────────────────
    def _parse_html_fragments_to_blocks(self, html: str) -> List[Dict[str, Any]]:
        """Парсит фрагмент HTML в блоки. Картинок в теле нет — только обложка и баннер по URL."""
        blocks: List[Dict[str, Any]] = []
        tag_pattern = re.compile(
            r'(<(?:h[23]|p|ul|ol|blockquote|div|table|details)[^>]*>.*?</(?:h[23]|p|ul|ol|blockquote|div|table|details)>)',
            re.DOTALL | re.IGNORECASE,
        )
        parts = tag_pattern.findall(html)
        if not parts:
            for line in html.strip().split("\n"):
                line = line.strip()
                if line and line.startswith("<"):
                    blocks.append({"type": "html", "content": line})
            return blocks
        for part in parts:
            part = part.strip()
            if part:
                blocks.append({"type": "html", "content": part})
        return blocks

    def parse_html_to_blocks(self, html: str) -> List[Dict[str, Any]]:
        """Парсит HTML в content_blocks. При наличии <!-- BANNER --> вставляет рекламный баннер и ссылку на сайт."""
        banner_marker = "<!-- BANNER -->"
        if banner_marker not in html:
            return self._parse_html_fragments_to_blocks(html)
        parts = html.split(banner_marker, 1)
        before = self._parse_html_fragments_to_blocks(parts[0].strip())
        after = self._parse_html_fragments_to_blocks(parts[1].strip())
        banner_blocks: List[Dict[str, Any]] = [
            {
                "type": "image",
                "path": BANNER_IMAGE_FILENAME,
                "caption": "Планируешь ремонт в офисе? flowcabinet.ru",
            },
        ]
        return before + banner_blocks + after

    # ── 5. Генерация картинок ──────────────────────────
    def generate_cover(self, topic: str, output_path: Path) -> bool:
        """Генерирует обложку (1792x1024) с лицом автора."""
        prompt = PROMPT_COVER.format(topic=topic)
        image_urls = [COVER_REF_FACE] + COVER_REF_EXTRA[:2]
        logger.info("Генерация обложки: %s", topic[:50])
        result = self.grs.generate_image(
            prompt=prompt,
            model="nano-banana-pro",
            size="1792x1024",
            image_urls=image_urls,
        )
        return self._save_image_result(result, output_path)

    def generate_article_image(self, section_title: str, headline: str, output_path: Path) -> bool:
        """Генерирует картинку для секции статьи (1024x1024). Пробует ZEN_IMAGE_MODEL, при ошибке — nano-banana."""
        prompt = PROMPT_IMAGE.format(section_title=section_title, headline=headline)
        logger.info("Генерация картинки: %s", section_title[:50])
        result = self.grs.generate_image(
            prompt=prompt,
            model=ZEN_IMAGE_MODEL,
            size="1024x1024",
        )
        if not result.get("success") and ZEN_IMAGE_MODEL != "nano-banana":
            logger.info("Повтор картинки блока с nano-banana")
            result = self.grs.generate_image(
                prompt=prompt,
                model="nano-banana",
                size="1024x1024",
            )
        return self._save_image_result(result, output_path)

    def _save_image_result(self, result: Dict[str, Any], output_path: Path) -> bool:
        """Скачивает/декодирует результат GRS image и сохраняет."""
        if not result.get("success"):
            logger.warning("Ошибка генерации изображения: %s", result.get("error"))
            return False
        raw: bytes
        if "url" in result:
            try:
                r = requests.get(result["url"], timeout=120)
                r.raise_for_status()
                raw = r.content
            except Exception as e:
                logger.warning("Не удалось скачать изображение: %s", e)
                return False
        elif "b64_json" in result:
            raw = base64.b64decode(result["b64_json"])
        else:
            logger.warning("Нет url/b64 в ответе: %s", list(result.keys()))
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(raw)
        logger.info("Изображение сохранено: %s (%d KB)", output_path.name, len(raw) // 1024)
        return True

    # ── 6. Сборка article.json ─────────────────────────
    def build_article(
        self,
        headline: str,
        topic: str,
        article_html: str,
        article_dir: Path,
    ) -> Dict[str, Any]:
        """Полный пайплайн: HTML → blocks, генерация картинок, сборка JSON."""
        # 1. Парсим HTML в блоки
        content_blocks = self.parse_html_to_blocks(article_html)

        # 2. Баннер и обложка: файлы в папке статьи, вставка в Дзен как обложка (по пути)
        banner_src = BLOCK_DIR / "articles" / BANNER_IMAGE_FILENAME
        if banner_src.exists():
            shutil.copy2(banner_src, article_dir / BANNER_IMAGE_FILENAME)
        cover_name = "cover.png"
        cover_path = article_dir / cover_name
        cover_ok = self.generate_cover(topic, cover_path)
        if cover_ok:
            content_blocks.insert(0, {
                "type": "image",
                "path": cover_name,
                "caption": headline,
            })

        # 4. Meta для Дзен и отдельное саммари для Telegram (длиннее, строго по содержанию статьи)
        meta = self.generate_meta_description(article_html)
        telegram_summary = self.generate_telegram_summary(article_html)

        # 5. Теги
        tags = self.generate_tags(headline, topic)

        # 6. Собираем JSON
        article_data = {
            "title": headline,
            "meta_description": meta,
            "telegram_summary": telegram_summary,
            "content_blocks": content_blocks,
            "tags": tags,
            "cover_image": cover_name if cover_ok else None,
            "publish": True,
        }
        return article_data

    # ── 7. Сохранение ──────────────────────────────────
    def save_article(self, article_data: Dict[str, Any], article_dir: Path) -> Path:
        """Сохраняет article.json в папку publish/NNN/."""
        article_dir.mkdir(parents=True, exist_ok=True)
        path = article_dir / "article.json"
        path.write_text(json.dumps(article_data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Статья сохранена: %s", path)
        return path

    # ── ПОЛНЫЙ ПАЙПЛАЙН ────────────────────────────────
    def run(self, sheet_name: Optional[str] = None) -> Optional[Tuple[Path, int]]:
        """
        Полный пайплайн: тема → сиды → Wordstat (SEO) → заголовок → текст → картинки → article.json.
        Возвращает (путь к article.json, row_index) или None если нет тем.
        """
        # 1. Тема из таблицы
        topic, extra, row_index = self.fetch_topic(sheet_name)
        if not topic:
            logger.warning("Нет тем для генерации")
            return None

        if extra:
            topic = f"{topic}. {extra}"

        # 2. Сиды для Wordstat и топ-фразы (SEO)
        k1, k2, k3 = self.generate_seeds(topic)
        seeds = [s for s in (k1, k2, k3) if s]
        try:
            from blocks.autopost_zen import wordstat_client as wc
            top_phrases = wc.fetch_top_phrases(seeds) if seeds else []
        except Exception as e:
            logger.warning("Wordstat не использован: %s", e)
            top_phrases = []
        keywords = ", ".join(top_phrases) if top_phrases else ", ".join(seeds) if seeds else topic

        # 3. SEO-заголовок с ключевыми словами
        headline = self.generate_headline(topic, keywords)

        # 4. Текст статьи (новая структура: введение, основной блок, инструкция+баннер, тренды, ссылки, FAQ)
        article_html = self.generate_article(headline, topic, keywords)

        # 5. Папка публикации
        num = _get_next_publish_number()
        article_dir = PUBLISH_DIR / f"{num:03d}"
        article_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Папка публикации: %s", article_dir)

        # 6. Сборка (парсинг с вставкой баннера + картинки + meta + теги)
        article_data = self.build_article(headline, topic, article_html, article_dir)

        # 7. Сохранение
        article_path = self.save_article(article_data, article_dir)

        return article_path, row_index


def _get_next_publish_number() -> int:
    """Следующий порядковый номер для папки публикации."""
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    existing = [d.name for d in PUBLISH_DIR.iterdir() if d.is_dir() and d.name.isdigit()]
    return max([0] + [int(n) for n in existing]) + 1
