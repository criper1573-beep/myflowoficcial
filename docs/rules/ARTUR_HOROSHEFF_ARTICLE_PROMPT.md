# Статьи для Дзен (flowcabinet.ru и др.)

**Все промпты и пошаговые инструкции по генерации статей берём из единого гайда:**

→ **[docs/guides/BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md](../guides/BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md)** — подбор ключей, SEO-заголовок, поиск информации, написание статьи (SEO/GEO), мета-описание, обложка, метаданные изображений.

В этом файле — только **тематика flowcabinet.ru**, **формат content_blocks под Дзен** и **рабочий файл публикации**.

---

**Референс:** структура канала [Артур Хорошев](https://dzen.ru/artur_horosheff) (H3 + картинка + абзац + список)

**Площадка:** flowcabinet.ru — кабинеты под ключ, офисы, рабочие зоны

**Автопостинг:** см. `docs/guides/PLAYWRIGHT_AUTOPOST.md`

---

## Тематика flowcabinet.ru

- Кабинеты под ключ (готовые офисные решения)
- Организация рабочей зоны в офисе
- Обустройство офисных помещений
- Эргономика рабочего места
- Освещение, мебель, планировка
- Ремонт и отделка коммерческих помещений

---

## Структура статьи и content_blocks (Дзен)

Общая структура и порядок блоков описаны в [ZEN_ARTICLE_STRUCTURE.md](../guides/ZEN_ARTICLE_STRUCTURE.md). Кратко для flowcabinet:

- **Заголовок** — по правилам из гайда (SEO-заголовок для Дзена, 50–80 символов).
- **Обложка** — первым блоком в `content_blocks`, затем вступление.
- **Основная часть** — 4–5 блоков: **H3 → картинка → абзац → список (ul)**.
- **Заключение** — 1–2 абзаца.
- **Полезные источники** — «Может пригодиться» + 3–4 ссылки.
- **CTA** — «Планируешь ремонт в офисе?» + ссылка на https://flowcabinet.ru

**Пример порядка content_blocks:**

| Порядок | Тип | Описание |
|--------|-----|----------|
| 1 | image | cover.png — обложка |
| 2 | html | Вступление `<p>...</p>` |
| 3 | html | `<h3>1. ...</h3>` |
| 4 | image | block1.png |
| 5 | html | Абзац + `<ul>` |
| … | … | Аналогично блоки 2, 3, … |
| — | html | Заключение, источники, CTA |

**HTML-теги:** `<p>`, `<h3>`, `<ul>`, `<li>`, `<a href="URL">текст</a>`. Без `<div>`, `<span>`, inline-стилей.

---

## Полная схема content_blocks (JSON)

Порядок: обложка → вступление → (H3 → картинка → абзац → список) × N → заключение → источники → CTA.

```json
[
  {"type": "image", "path": "cover.png", "caption": "Обложка статьи"},
  {"type": "html", "content": "<p>Вступление...</p>"},
  {"type": "html", "content": "<h3>1. Первый блок</h3>"},
  {"type": "image", "path": "block1.png", "caption": "Подпись к картинке 1"},
  {"type": "html", "content": "<p>Абзац...</p>"},
  {"type": "html", "content": "<ul><li>...</li></ul>"},
  {"type": "html", "content": "<h3>2. Второй блок</h3>"},
  {"type": "image", "path": "block2.png", "caption": "Подпись к картинке 2"},
  {"type": "html", "content": "<p>Абзац...</p>"},
  {"type": "html", "content": "<ul><li>...</li></ul>"},
  {"type": "html", "content": "<h3>3. Третий блок</h3>"},
  {"type": "image", "path": "block3.png", "caption": "Подпись к картинке 3"},
  {"type": "html", "content": "<p>Абзац...</p>"},
  {"type": "html", "content": "<ul><li>...</li></ul>"},
  {"type": "html", "content": "<p>Заключение...</p>"},
  {"type": "html", "content": "<p>Может пригодиться</p><p>1. Название 1 — <a href=\"URL1\">читать тут</a></p>..."},
  {"type": "html", "content": "<p>Планируешь ремонт в офисе? ...</p><p><a href=\"https://flowcabinet.ru\">Узнать подробнее</a></p>"}
]
```

---

## Требования к тексту (flowcabinet.ru)

| Параметр | Значение |
|----------|----------|
| Объём | 7000–9000 знаков |
| Стиль | По гайду: живой, экспертный, без воды (см. BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md) |
| SEO | Ключевые слова по гайду (подбор ключей → SEO-заголовок → написание статьи) |

---

## Рабочий файл и порядок действий

**Файл для правок перед публикацией:** `blocks/autopost_zen/articles/article_to_publish.json`

**Порядок:**
1. Сгенерировать статью по инструкциям из [BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md](../guides/BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md) (ключи → заголовок → фактура → текст → мета-описание, обложка и картинки блоков).
2. Оформить результат в `article_to_publish.json` (формат см. выше и в [ZEN_ARTICLE_STRUCTURE.md](../guides/ZEN_ARTICLE_STRUCTURE.md)).
3. При необходимости внести правки в файл.
4. Запуск публикации: `npm run zen:publish` (читает этот же файл).

Картинки искать в папке `assets` или `blocks/autopost_zen/articles/` — в JSON указывать по имени файла (например `cover.png`, `block1.png`).

---

## Быстрый запуск публикации

```bash
npm run zen:publish    # публикует из article_to_publish.json
npm run zen:draft      # сохраняет черновик из article_to_publish.json
npm run zen:publish:flowcabinet   # flowcabinet_office.json
npm run zen:publish:commercial   # commercial_remont.json
```

---

## Референс: шаблон статьи

Файл: `blocks/autopost_zen/articles/article_to_publish.json` — рабочий файл с примером структуры. Заполняй его при генерации новой статьи.
