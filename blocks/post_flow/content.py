# -*- coding: utf-8 -*-
"""Генерация заголовка, текста и картинки поста через GRS AI (OpenAI-совместимый API)."""
import html
import json
import re
from pathlib import Path

import requests

from blocks.post_flow import config
from blocks.post_flow.context import TECHNOLOGY_CONTEXT, CABINET_IMAGE_CONTEXT

CHAT_URL = "https://grsaiapi.com/v1/chat/completions"


def _grs_chat(model: str, messages: list, temperature: float = 0.7) -> str:
    api_key = (getattr(config, "GRS_AI_API_KEY", None) or getattr(config, "OPENAI_API_KEY", None) or "").strip()
    if not api_key:
        raise ValueError("GRS_AI_API_KEY не задан в .env")
    if not api_key.startswith("sk-"):
        api_key = "sk-" + api_key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    r = requests.post(CHAT_URL, json=data, headers=headers, timeout=60)
    r.encoding = "utf-8"
    if not r.ok:
        raise RuntimeError(f"GRS AI HTTP {r.status_code}: {r.text[:500]}")
    try:
        j = r.json()
    except json.JSONDecodeError as e:
        if "Extra data" in str(e):
            j, _ = json.JSONDecoder().raw_decode(r.text)
        else:
            raise
    if j.get("code") not in (None, 0):
        raise RuntimeError(f"GRS AI ошибка: {j.get('msg', j)}")
    content = (j.get("choices") or [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                content = part.get("text", "")
                break
        else:
            content = ""
    text = content or (j.get("data") or {}).get("output", {}).get("text") or (j.get("output") or {}).get("text") or j.get("response") or j.get("content") or j.get("text") or ""
    if not text:
        raise RuntimeError(
            "API вернул ответ без текста. Ответ: " + json.dumps(j, ensure_ascii=False)[:500]
        )
    return _fix_encoding(str(text))


def _grs_chat_with_retry(model: str, messages: list, temperature: float = 0.7, fallback_model: str | None = None) -> str:
    fallback = fallback_model or getattr(config, "MODEL_FALLBACK", "gpt-4o-mini")
    last_err = None
    for attempt in range(2):
        try:
            return _grs_chat(model, messages, temperature)
        except (RuntimeError, json.JSONDecodeError) as e:
            last_err = e
            if isinstance(e, json.JSONDecodeError) or "без текста" in str(e):
                continue
            raise
    try:
        return _grs_chat(fallback, messages, temperature)
    except RuntimeError as e:
        raise last_err from e


def _strip_markdown(text: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"_([^_]+)_", r"\1", s)
    return s


def _strip_thinking(text: str) -> str:
    s = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    if "HEADLINE:" in s:
        s = s[s.find("HEADLINE:"):]
    return s


def _fix_encoding(text: str) -> str:
    if not text:
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def _history_path() -> Path:
    return Path(__file__).resolve().parent / "posts_history.json"


def load_previous_posts():
    """Загружает последние 10 постов из локального файла (заголовок + текст)."""
    path = _history_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("posts", [])[-10:]
    except Exception:
        return []


def save_post_to_history(headline: str, text: str):
    """Добавляет пост в историю (храним последние 10)."""
    path = _history_path()
    posts = load_previous_posts()
    posts.append({"headline": headline, "text": text})
    posts = posts[-10:]
    path.write_text(
        json.dumps({"posts": posts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _format_previous_posts(posts: list, max_posts: int = 5, snippet_len: int = 80) -> str:
    if not posts:
        return "Предыдущих постов пока нет."
    lines = []
    for i, p in enumerate(posts[-max_posts:], 1):
        t = (p.get("text") or "")[:snippet_len]
        if len((p.get("text") or "")) > snippet_len:
            t += "..."
        lines.append(f"{i}. {p.get('headline', '')} — {t}")
    return "\n".join(lines)


def generate_headline_and_text(topic: str, previous_posts: list, extra_context: str = "") -> tuple[str, str]:
    """Генерирует заголовок и текст поста через GRS AI."""
    previous = _format_previous_posts(previous_posts)
    ctx_block = f"\nДополнительный контекст (из таблицы): {extra_context}\n" if extra_context else ""
    prompt = f"""Канал FLOW: готовые офисные кабинеты и переговорные под ключ.

{TECHNOLOGY_CONTEXT}

Последние посты (не повторяй темы): {previous}

Тема: {topic}{ctx_block}

Напиши заголовок и текст поста (2–3 абзаца) от лица владельца компании — как будто он сам пишет пост руками. От первого лица (я, мы). Личный тон, свои наблюдения, прямой разговор с читателем. Не корпоративный голос, а живой человек, который знает продукт изнутри и делится этим.

Лимит длины (строго): заголовок — до 50 символов, текст — до 630 символов. Весь пост не более 700 символов (запас под лимит Telegram 1024). Пиши лаконично, без воды.

Требования к качеству:
- Конкретика: называй материалы, технологии, преимущества. Избегай общих фраз вроде «качество» и «надёжность» без пояснения.
- Польза для читателя: каждый абзац — одна мысль с выгодой или сутью.
- Используй контекст про материалы и технологии, где это усиливает сообщение.
- Заголовок — цепляющий, без клише. Текст — живой, без воды.

ВАЖНО: Только русский язык. Без разметки (**, Markdown, HTML). Без рассуждений и блоков </think> — сразу заголовок и текст.

Формат ответа:
HEADLINE:
<заголовок>
BODY:
<текст>
"""
    messages = [
        {"role": "system", "content": "Пишешь посты для Telegram от лица владельца компании FLOW. Заголовок до 50 символов, текст до 630. От первого лица. Личный тон. Только русский. Без разметки. Без рассуждений — сразу HEADLINE: и BODY:."},
        {"role": "user", "content": prompt},
    ]
    raw = _strip_thinking(_grs_chat_with_retry(
        config.MODEL_GENERATION,
        messages,
        temperature=0.7,
        fallback_model=config.MODEL_FALLBACK,
    )).strip()
    headline, body = "", ""
    if "HEADLINE:" in raw and "BODY:" in raw:
        parts = raw.split("BODY:", 1)
        headline = parts[0].replace("HEADLINE:", "").strip()
        body = parts[1].strip()
    else:
        lines = raw.split("\n")
        headline = lines[0] if lines else ""
        body = "\n".join(lines[1:]).strip()
    headline = _strip_markdown(headline)
    body = _strip_markdown(body)
    headline, body = _fit_to_caption_limit(headline, body)
    return headline, body


def _fit_to_caption_limit(headline: str, body: str, limit: int = 1024) -> tuple[str, str]:
    prefix = f"<b>{html.escape(headline or '', quote=False)}</b>\n\n"
    max_body = int((limit - len(prefix) - 3) * 0.7)
    if max_body <= 0 or len(body) <= max_body:
        return headline, body
    cut = body[: max_body + 1]
    last_space = cut.rfind(" ")
    if last_space > max_body * 0.7:
        body = body[:last_space].rstrip()
    else:
        body = body[:max_body].rstrip()
    return headline, body


def generate_image(topic: str, headline: str, body: str) -> bytes:
    """Генерирует картинку по теме и контенту поста. Возвращает PNG bytes."""
    prompt = f"""Professional B2B image for Telegram post. {CABINET_IMAGE_CONTEXT}

Topic: {topic}
Post headline: {headline}

Generate image following the cabinet description. All described features (lighting, materials, ventilation etc.) must appear ONLY inside the cabinet. Main office = open space with people. Strictly NO text, labels, logos or any inscriptions on the image. Photorealistic or quality 3D render."""
    return generate_image_by_prompt(prompt)


def _grs_draw(prompt: str) -> bytes:
    api_key = (getattr(config, "GRS_AI_API_KEY", None) or getattr(config, "OPENAI_API_KEY", None) or "").strip()
    if not api_key:
        raise ValueError("GRS_AI_API_KEY не задан в .env")
    if not api_key.startswith("sk-"):
        api_key = "sk-" + api_key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    base = "https://grsaiapi.com"
    model = getattr(config, "IMAGE_MODEL", "nano-banana")

    if model.startswith("nano-banana"):
        url = f"{base}/v1/draw/nano-banana"
        payload = {
            "model": model,
            "prompt": prompt,
            "urls": [],
            "shutProgress": True,
        }
    else:
        url = f"{base}/v1/draw/completions"
        payload = {
            "model": model if model in ("sora-image", "gpt-image", "gpt-image-1.5") else "sora-image",
            "prompt": prompt,
            "urls": [],
            "shutProgress": True,
        }

    r = requests.post(url, json=payload, headers=headers, timeout=120)
    r.encoding = "utf-8"
    if not r.ok:
        raise RuntimeError(f"GRS draw HTTP {r.status_code}: {r.text[:500]}")
    text = r.text.strip()
    if text.startswith("data: "):
        text = text[6:].split("\n")[0].strip()
    j = json.loads(text)
    if j.get("code") not in (None, 0):
        raise RuntimeError(f"GRS draw ошибка: {j.get('msg', j)}")

    image_url = None
    if isinstance(j.get("results"), list) and j["results"]:
        image_url = j["results"][0].get("url")
    if not image_url and isinstance(j.get("url"), str):
        image_url = j["url"]
    if not image_url:
        raise RuntimeError(f"GRS draw не вернул URL. Ответ: {json.dumps(j, ensure_ascii=False)[:300]}")

    img_r = requests.get(image_url, timeout=60)
    img_r.raise_for_status()
    return img_r.content


def generate_image_by_prompt(prompt: str) -> bytes:
    """Генерирует картинку по текстовому промпту. Возвращает PNG bytes."""
    return _grs_draw(prompt)
