#!/usr/bin/env python3
"""
Генерация обложки для статьи Дзен через GRS AI.
Как в Make.com blueprint «RU SEO/GEO СТАТЬИ ДЛЯ БЛОГА 2026»: модуль 5 (nano-banana-pro),
3 референсных фото по URL, первый URL — твоё лицо (подставляется через --ref или --ref-url).

Использование: из корня проекта
  python docs/scripts/scripts/generate_zen_cover.py "Тема статьи" --ref-url "https://..."
  python docs/scripts/scripts/generate_zen_cover.py "Тема" --ref photo.jpg
"""
import os
import sys
import base64
import argparse
import requests

# корень проекта
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# загрузка .env из корня
_env_path = os.path.join(ROOT, ".env")
if os.path.isfile(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                os.environ[k.strip()] = v


# Три референсных фото из blueprint (id 5). Первый заменяется на твоё фото (--ref / --ref-url).
BLUEPRINT_REFERENCE_URLS = [
    "https://mayai.ru/wp-content/uploads/2025/11/06bd46d4-89a4-4ad3-bf87-a84adbf8d952.jpg",
    "https://mayai.ru/wp-content/uploads/2025/11/c410cce6a3fa9f9d28915004e46e1c57.jpg",
    "https://mayai.ru/wp-content/uploads/2025/11/3557247553f3360809d41bb5c4ae311c.jpg",
]

# Промпт из blueprint (id 5, mapper.prompt). Плейсхолдер {{40.content}} → тема статьи.
BLUEPRINT_COVER_PROMPT = r"""Main Objective: Create a HYPER-REALISTIC ACTION SELFIE photo cover for an article.
Theme: {{40.content}}

STRICT VISUAL STYLE:
A photorealistic wide-angle selfie shot of the main hero (from reference), blending seamlessly with historical events/personalities based on the theme.
Captured with a 24mm wide-angle lens (simulating high-end smartphone or wide POV camera) to capture both the hero's face and the dynamic historical background.
The image must look like a real, candid moment captured in time, NOT an illustration.

SUBJECT & COMPOSITION:
CRITICAL — FACE: The first reference image is the author. You MUST preserve this EXACT face: same facial structure, features, skin tone, hair. The person in the result must be unmistakably the same as in reference 1. Do not alter, replace or stylize the face.
The main hero (from first reference image), making a funny/cool expression reacting to the historical event behind him.
- Clothing: Era-accurate costume blended with modern stylish elements (e.g., historical uniform with modern touches).
- Face: Ultra-sharp focus on the hero's face. Visible skin pores, individual stubble hairs, realistic eye reflections.
- NO cap, NO hood.

ENVIRONMENT & CONTEXT (Auto-generated from Theme):
The background depicts a vivid, chaotic, or humorous historical scene relevant to: {{40.content}}.
- Action: Dynamic movement, historical figures reacting to the hero or the event.
- Visual Gag: Witty physical comedy happening in the background.
- Props/Vehicles: 100% era-accurate details (materials, wear and tear, dust).

LIGHTING & ATMOSPHERE:

- Color Palette: Realistic, rich colors (Fujifilm Velvia simulation), NO vintage yellow filters, NO sepia.

TYPOGRAPHY & BRANDING:
СОКРАТИ ЗАГОЛОВОК НА ОБЛОЖКЕ !!!! ( НЕ БЕРИ ВЕСЬ ТЕКСТ )
- Headline: Short title from theme "{{40.content}}". May wrap to 2–3 lines; break only between words.
- CRITICAL — spelling: Write every word EXACTLY as in Russian. No letter swaps, no gibberish (e.g. "пространств" not "проснтарнть"). Copy words from the theme if needed.
- Language: All visible text MUST be in Russian Cyrillic.
- Footer: Subtle Telegram logo and handle @myflowofficial at the very bottom (small, neutral). БЕРИ ИЗ ПРИМЕРОВ КОТОРЫЕ Я ТЕБЕ ДАЛ - КРАСИВЫЙ ЗАГОЛОВОК С ПЛАШКОЙ !

TECHNICAL QUALITY TARGETS:
- 8k resolution, raw photo quality.
- ISO 100 grain texture (subtle).
- Depth of Field: Sharp face, slightly softer background but clearly legible details.
- Imperfections: Chromatic aberration on edges, motion blur on fast-moving background elements to enhance realism.

NEGATIVE PROMPT:
Drawing, painting, illustration, 3d render, cartoon, anime, sketch, plastic skin, smooth skin, doll-like, blurry face, bad eyes, distorted hands, watermark, latin letters, english text.

Эпоха/фон: подбери под тему статьи (Theme выше) — одна сцена или эпоха, релевантная теме. Связь фона и темы должна быть очевидной.
"""


def _local_file_to_data_url(path: str) -> str:
    """Читает локальный файл и возвращает data URL (base64)."""
    path = os.path.normpath(path if os.path.isabs(path) else os.path.join(ROOT, path))
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as f:
        raw = f.read()
    ext = os.path.splitext(path)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "image/webp"
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def main():
    import json as _json
    parser = argparse.ArgumentParser(description="Генерация обложки как в Make blueprint: 3 референса, первый — твоё фото, модель nano-banana-pro. Обложка всегда горизонтальная 16:9 (1792x1024).")
    parser.add_argument("topic", nargs="?", default=None, help="Тема статьи (подставляется в промпт как Theme). Если задан --article, берётся title из статьи.")
    parser.add_argument("--article", "-a", default=None, metavar="ARTICLE_JSON", help="Путь к article.json — тема и имя обложки берутся из статьи, вывод в ту же папку")
    parser.add_argument("--output", "-o", default=None, help="Путь к выходному файлу")
    parser.add_argument("--ref", "-r", default=None, metavar="FILE", help="Локальный путь к референсному фото (твоё лицо) — подставляется первым из 3")
    parser.add_argument("--ref-url", default="https://i.postimg.cc/jdwFhwpV/photo_2026_02_05_10_46_02.jpg", metavar="URL", help="URL референсного фото (твоё лицо) — подставляется первым из 3")
    parser.add_argument("--prompt-override", "-p", default=None, help="Полностью свой промпт (иначе используется промпт из blueprint)")
    parser.add_argument("--model", default="nano-banana-pro", help="Модель GRS (nano-banana-pro как в Make)")
    parser.add_argument("--size", default="1792x1024", help="Размер: горизонтальная ориентация 16:9 (1792x1024)")
    args = parser.parse_args()

    topic = args.topic
    out_path = args.output
    if args.article:
        article_path = os.path.normpath(os.path.join(ROOT, args.article) if not os.path.isabs(args.article) else args.article)
        if not os.path.isfile(article_path):
            print("Ошибка: файл статьи не найден:", article_path)
            return 1
        with open(article_path, "r", encoding="utf-8") as f:
            article = _json.load(f)
        topic = topic or (article.get("title") or "").strip() or "Тренды офисных пространств 2026"
        article_dir = os.path.dirname(article_path)
        cover_name = article.get("cover_image") or "trends_office_2026_cover.png"
        if not os.path.splitext(cover_name)[1]:
            cover_name += ".png"
        out_path = out_path or os.path.join(article_dir, cover_name)
        print("Статья:", article_path, "| тема:", topic[:50] + "..." if len(topic) > 50 else topic, "| обложка:", cover_name)

    topic = topic or "Тренды офисных пространств 2026"

    from blocks.ai_integrations.grs_ai_client import GRSAIClient

    # Как в blueprint: 3 референса; первый = твоё лицо (--ref приоритетнее, иначе --ref-url, по умолчанию задан в parser)
    first_ref = None
    if args.ref:
        first_ref = _local_file_to_data_url(args.ref)
        print("Референс 1 (твоё фото): локальный файл", args.ref)
    elif args.ref_url:
        first_ref = args.ref_url
        print("Референс 1 (твоё фото): URL", args.ref_url[:60] + "..." if len(args.ref_url) > 60 else args.ref_url)
    if not first_ref:
        first_ref = "https://i.postimg.cc/jdwFhwpV/photo_2026_02_05_10_46_02.jpg"
        print("Референс 1 (твоё фото): URL по умолчанию")
    image_urls = [first_ref] + BLUEPRINT_REFERENCE_URLS[1:]
    print("Всего референсов: 3 (первый — твоё фото, 2–3 — из blueprint)")

    prompt = args.prompt_override or BLUEPRINT_COVER_PROMPT.replace("{{40.content}}", topic)

    if not out_path:
        out_path = os.path.join(ROOT, "blocks", "autopost_zen", "articles", "trends_office_2026_cover.png")
    out_path = os.path.normpath(os.path.join(ROOT, out_path) if not os.path.isabs(out_path) else out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    print("Промпт (фрагмент):", prompt[:180] + "..." if len(prompt) > 180 else prompt)
    print("Модель:", args.model, "Размер:", args.size)
    print("Выход:", out_path)

    client = GRSAIClient()
    result = client.generate_image(prompt=prompt, model=args.model, size=args.size, image_urls=image_urls if image_urls else None)

    if not result.get("success"):
        print("Ошибка:", result.get("error", result))
        return 1

    raw: bytes
    if "url" in result:
        r = requests.get(result["url"], timeout=60)
        r.raise_for_status()
        raw = r.content
    elif "b64_json" in result:
        raw = base64.b64decode(result["b64_json"])
    else:
        print("Нет url и b64_json в ответе:", result.keys())
        return 1

    with open(out_path, "wb") as f:
        f.write(raw)
    print("Сохранено:", out_path, len(raw), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
