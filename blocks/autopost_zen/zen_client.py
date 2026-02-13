# -*- coding: utf-8 -*-
"""
Клиент для автоматизации публикации в Яндекс.Дзен.
Использует Playwright для автоматизации браузера.
Следует UNIVERSAL_AUTOPOST_PROMPT; данные из документации ContentZavod (PLAYWRIGHT_AUTOPOST.md).
Поведение имитирует человека, чтобы снизить вероятность капчи.
"""
import asyncio
import json
import random
import re
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
from dotenv import load_dotenv
import logging

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
# Папка публикаций: publish/001, publish/002, ... — в каждой статья article.json и картинки
PUBLISH_DIR = BLOCK_DIR / "publish"
load_dotenv(PROJECT_ROOT / ".env")

# playwright_helpers (модалка Дзена)
SCRIPTS_DIR = PROJECT_ROOT / "docs" / "scripts" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from playwright_helpers import dismiss_yandex_default_search_modal
except ImportError:
    async def dismiss_yandex_default_search_modal(page, timeout_ms=5000):
        return False

logger = logging.getLogger(__name__)

# Селекторы Дзена (официальные data-testid и классы редактора). Правила: не Ctrl+A в теле; ENTER x2 между блоками.
DZEN = {
    "popup_close": '[data-testid="close-button"]',
    "donations_popup": '[data-testid="donations-promo-banner-popup"]',
    "add_publication": '[data-testid="add-publication-button"]',
    "write_article": '[aria-label="Написать статью"]',
    "title_field": "div.article-editor-desktop--editor__titleInput-2D",
    "body_editor": "div.article-editor-desktop--zen-draft-editor__zenEditor-13",
    "publish_btn": '[data-testid="article-publish-btn"]',
    "image_button": "button[data-tip='Вставить изображение']",
    "toolbar": "div.article-editor-desktop--editor-toolbar__editorToolbar-15",
}


def get_next_publish_number() -> int:
    """Следующий порядковый номер для папки публикации (001, 002, ...)."""
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    existing = [d.name for d in PUBLISH_DIR.iterdir() if d.is_dir() and d.name.isdigit()]
    return max([0] + [int(n) for n in existing]) + 1


def _resolve_article_image_path(path_str: str, article_parent: Path) -> Optional[Path]:
    """Найти файл картинки: сначала рядом со статьёй, затем articles/, корень проекта."""
    if not path_str or str(path_str).startswith("http"):
        return None
    p = Path(path_str)
    name = p.name
    for base in (article_parent, BLOCK_DIR / "articles", PROJECT_ROOT):
        candidate = base / name if not p.is_absolute() else base / p
        if candidate.exists():
            return candidate.resolve()
    if not p.is_absolute():
        if (PROJECT_ROOT / path_str).exists():
            return (PROJECT_ROOT / path_str).resolve()
        if (BLOCK_DIR / "articles" / name).exists():
            return (BLOCK_DIR / "articles" / name).resolve()
    return None


def prepare_publication(article_path: Path) -> Path:
    """
    Перенос статьи и всех её картинок в папку с порядковым номером (publish/001, 002, ...).
    Пути в JSON заменяются на имена файлов. Исходный файл и картинки удаляются из старых мест.
    Возвращает путь к article.json в новой папке.
    """
    article_path = article_path.resolve()
    if not article_path.exists():
        raise FileNotFoundError(f"Файл статьи не найден: {article_path}")
    data = json.loads(article_path.read_text(encoding="utf-8"))
    article_parent = article_path.parent
    images_to_move = []  # (src Path, basename)
    # Обложка
    cover = data.get("cover_image")
    if cover and not str(cover).startswith("http"):
        src = _resolve_article_image_path(cover, article_parent)
        if src:
            images_to_move.append((src, Path(cover).name))
            data["cover_image"] = Path(cover).name
    # Картинки в блоках
    for block in data.get("content_blocks", []):
        if block.get("type") != "image" or not block.get("path"):
            continue
        path_str = block["path"]
        src = _resolve_article_image_path(path_str, article_parent)
        if src:
            name = Path(path_str).name
            if (src, name) not in [(s, n) for s, n in images_to_move]:
                images_to_move.append((src, name))
            block["path"] = name
    # Создаём папку публикации
    n = get_next_publish_number()
    pub_dir = PUBLISH_DIR / f"{n:03d}"
    pub_dir.mkdir(parents=True, exist_ok=True)
    # Переносим картинки (без дублей по src)
    seen_src = set()
    for src, name in images_to_move:
        if str(src.resolve()) in seen_src:
            continue
        seen_src.add(str(src.resolve()))
        dest = pub_dir / name
        if src.resolve() != dest.resolve():
            shutil.move(str(src), str(dest))
            logger.info("Перенесено: %s -> %s", src.name, pub_dir)
    # Записываем обновлённый JSON и удаляем исходный файл статьи
    out_json = pub_dir / "article.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    article_path.unlink()
    logger.info("Публикация подготовлена: %s (статья и картинки в %s)", out_json, pub_dir)
    return out_json


async def _human_wait(lo: float = 0.8, hi: float = 2.5):
    """Случайная пауза в секундах, имитирующая человека."""
    await asyncio.sleep(random.uniform(lo, hi))


def _block_label(block: dict) -> str:
    """Краткая подпись блока для чеклиста (h1, h2, ul, image и т.д.)."""
    if block.get("type") == "image":
        return "image"
    content = (block.get("content") or "").strip().lower()
    if content.startswith("<h1"):
        return "h1"
    if content.startswith("<h2"):
        return "h2"
    if content.startswith("<h3"):
        return "h3"
    if content.startswith("<h4"):
        return "h4"
    if content.startswith("<ul"):
        return "ul"
    if content.startswith("<ol"):
        return "ol"
    if content.startswith("<blockquote"):
        return "blockquote"
    if "<a " in content:
        return "a (ссылка)"
    return "p"


class ZenClient:
    """Клиент для работы с Яндекс.Дзен через автоматизацию браузера."""

    BASE_URL = "https://dzen.ru"
    LOGIN_URL = "https://passport.yandex.ru/auth?retpath=https%3A%2F%2Fzen.yandex.ru"
    CREATE_POST_URL = os.getenv("ZEN_EDITOR_URL", "https://dzen.ru/profile/editor/flowcabinet")

    def __init__(self):
        self.email = os.getenv("ZEN_EMAIL", "").strip()
        self.password = os.getenv("ZEN_PASSWORD", "").strip()
        self.headless = os.getenv("ZEN_HEADLESS", "false").lower() in ("1", "true", "yes")
        self.timeout = int(os.getenv("ZEN_BROWSER_TIMEOUT", "60000"))
        _storage = os.getenv("ZEN_STORAGE_STATE", "zen_storage_state.json")
        self.storage_state_path = str((PROJECT_ROOT / _storage).resolve()) if not os.path.isabs(_storage) else _storage
        self.keep_open = os.getenv("ZEN_KEEP_OPEN", "false").lower() in ("1", "true", "yes")

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        if not os.path.exists(self.storage_state_path) and (not self.email or not self.password):
            raise ValueError(
                "Нужен либо файл сессии (ZEN_STORAGE_STATE / zen_storage_state.json), "
                "либо ZEN_EMAIL и ZEN_PASSWORD в .env. Сохраните куки: python docs/scripts/scripts/capture_cookies.py"
            )

    async def start(self):
        """Запуск браузера и создание контекста. Скрывает признаки автоматизации."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        )

        context_kwargs = {
            "viewport": None,
            "locale": "ru-RU",
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        if os.path.exists(self.storage_state_path):
            context_kwargs["storage_state"] = self.storage_state_path
            logger.info("Загружены cookies из %s", self.storage_state_path)

        self.context = await self.browser.new_context(**context_kwargs)
        # Разрешаем clipboard API (иначе navigator.clipboard.write не работает)
        await self.context.grant_permissions(["clipboard-read", "clipboard-write"])
        use_stealth = os.getenv("ZEN_STEALTH", "false").lower() in ("1", "true", "yes")
        if use_stealth and STEALTH_AVAILABLE:
            try:
                stealth = Stealth()
                await stealth.apply_stealth_async(self.context)
                logger.info("Применён playwright-stealth")
            except Exception as e:
                logger.warning("Stealth не применён: %s", e)
        self.context.set_default_timeout(self.timeout)
        self.page = await self.context.new_page()
        self._attach_debug_listeners()
        logger.info("Браузер запущен")

    def _attach_debug_listeners(self):
        if not self.page:
            return

        def _on_console(msg):
            logger.debug("[БРАУЗЕР] %s: %s", msg.type, msg.text)

        def _on_page_error(err):
            logger.error("[ОШИБКА СТРАНИЦЫ] %s", err)

        # Логируем только запросы загрузки файлов в Дзен (не Метрику, не apptracer)
        def _is_upload_request(url: str, method: str) -> bool:
            u = (url or "").lower()
            if method != "POST":
                return False
            if "mc.yandex.ru" in u or "apptracer" in u:
                return False
            return any(x in u for x in ("storage", "avatars", "dzeninfra.ru/s3", "upload", "multipart")) or "image" in u

        def _on_request(request):
            try:
                url = request.url
                method = request.method
                if _is_upload_request(url, method):
                    headers = request.headers
                    ct = headers.get("content-type", "")
                    post_data = request.post_data
                    logger.info(
                        "[UPLOAD REQ] %s %s | Content-Type: %s | post_data len=%s",
                        method, url[:120], ct[:80] if ct else "-", len(post_data) if post_data else 0
                    )
                    if post_data and len(post_data) < 2000:
                        logger.info("[UPLOAD REQ] post_data (snippet): %s", post_data[:1500])
                    elif post_data and ("boundary" in ct or "multipart" in ct):
                        try:
                            raw = post_data if isinstance(post_data, str) else (post_data.decode("utf-8", errors="replace") if isinstance(post_data, bytes) else "")
                            if 'name="' in raw:
                                logger.info("[UPLOAD REQ] multipart snippet: %s", raw[:500].replace("\r", " ").replace("\n", " ")[:400])
                        except Exception:
                            pass
            except Exception as e:
                logger.debug("_on_request: %s", e)

        def _on_response(response):
            try:
                url = response.url
                req = response.request
                if req.method == "POST" and _is_upload_request(url, req.method):
                    status = response.status
                    logger.info("[UPLOAD RESP] %s %s | status=%s", req.method, url[:120], status)
                    if status >= 400:
                        logger.warning("[UPLOAD RESP] ошибка %s — открой Network в DevTools для тела ответа", status)
            except Exception as e:
                logger.debug("_on_response: %s", e)

        self.page.on("console", _on_console)
        self.page.on("pageerror", _on_page_error)
        self.page.on("request", _on_request)
        self.page.on("response", _on_response)

    async def close(self):
        if self.keep_open:
            logger.info("Браузер оставлен открытым (ZEN_KEEP_OPEN=true)")
            return
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Браузер закрыт")

    async def save_cookies(self):
        if self.context and self.storage_state_path:
            await self.context.storage_state(path=self.storage_state_path)
            logger.info("Cookies сохранены в %s", self.storage_state_path)

    async def screenshot(self, name: str = "screenshot", full_page: bool = False):
        """Сохранение скриншота в blocks/autopost_zen/. full_page=True — весь документ (для проверки статьи)."""
        try:
            if not self.page:
                return ""
            filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = BLOCK_DIR / filename
            await self.page.screenshot(path=str(path), full_page=full_page)
            logger.info("Скриншот: %s", filename)
            return str(path)
        except Exception as e:
            if "TargetClosedError" in type(e).__name__ or "closed" in str(e).lower():
                logger.debug("Скриншот пропущен: страница/браузер закрыты")
            else:
                logger.warning("Скриншот не сохранён: %s", e)
            return ""

    async def _wait_captcha_if_present(self):
        try:
            captcha = self.page.get_by_text("Вы не робот", exact=False)
            if await captcha.is_visible():
                logger.warning("Обнаружена капча. Ожидание 90 сек для ручного решения.")
                await self.page.wait_for_timeout(90000)
        except Exception:
            pass

    def _html_to_plain_text(self, html: str) -> str:
        """Конвертация HTML в plain text с сохранением абзацев."""
        if not html or not html.strip():
            return ""
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
        text = re.sub(r"</p>", "\n", text, flags=re.I)
        text = re.sub(r"</h[1-6]>", "\n", text, flags=re.I)
        text = re.sub(r"</li>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _parse_html_block(self, html: str) -> tuple[str, str, Optional[List[str]]]:
        """
        Определить тип блока и извлечь текст (или пункты списка).
        В теле статьи только H2 и H3; H1 используется только в заголовке статьи — в теле трактуем как H2.
        Возвращает (block_kind, text, list_items).
        block_kind: "h2" | "h3" | "p" | "ul" | "ol" | "blockquote" | "p_with_link"
        """
        raw = html.strip().lower()
        plain = self._html_to_plain_text(html)
        list_items = None
        if raw.startswith("<h1"):
            return "h2", plain, None  # H1 только в заголовке статьи; в теле — H2
        if raw.startswith("<h2"):
            return "h2", plain, None
        if raw.startswith("<h3"):
            return "h3", plain, None
        if raw.startswith("<h4"):
            return "h3", plain, None  # в теле только h2/h3; h4 трактуем как h3
        if raw.startswith("<blockquote"):
            return "blockquote", plain, None
        if raw.startswith("<ul"):
            list_items = re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.DOTALL | re.I)
            list_items = [re.sub(r"<[^>]+>", "", x).strip() for x in list_items]
            return "ul", plain, list_items if list_items else None
        if raw.startswith("<ol"):
            list_items = re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.DOTALL | re.I)
            list_items = [re.sub(r"<[^>]+>", "", x).strip() for x in list_items]
            return "ol", plain, list_items if list_items else None
        if "<a " in raw or "<a>" in raw:
            return "p_with_link", plain, None
        return "p", plain, None

    async def _clear_field(self) -> None:
        """Выделить всё в текущем поле (для замены вводом). Используется только для заголовка."""
        await self.page.keyboard.press("Control+a")

    async def _select_current_block_only(self) -> bool:
        """
        Выделить только текущий блок (параграф/строка), не весь документ.
        Ctrl+A в теле статьи выделяет всё — из-за этого ломаются H3 и списки.
        """
        try:
            return await self.page.evaluate(
                """() => {
                    const sel = window.getSelection();
                    if (!sel || sel.rangeCount === 0) return false;
                    const range = sel.getRangeAt(0);
                    let node = range.startContainer;
                    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
                    if (!node || !node.closest) return false;
                    const selectors = [
                        '[class*="DraftEditor-block"]',
                        '[class*="DraftEditor-block" i]',
                        '[data-block-key]',
                        '[data-block-type]',
                        '[class*="paragraph"]',
                        'div[contenteditable="true"] > div'
                    ];
                    let block = null;
                    for (const s of selectors) {
                        try {
                            block = node.closest(s);
                            if (block && block.closest('[contenteditable="true"]')) break;
                        } catch (e) {}
                    }
                    if (!block) return false;
                    try {
                        const r = document.createRange();
                        r.selectNodeContents(block);
                        sel.removeAllRanges();
                        sel.addRange(r);
                        return true;
                    } catch (e) { return false; }
                }"""
            )
        except Exception:
            return False

    async def _select_current_line_keyboard(self) -> None:
        """
        Выделить текущую строку без Ctrl+A: Ctrl+Right (в конец слова/строки), затем Shift+Ctrl+Left.
        Используется в теле статьи, чтобы не ломать вёрстку (правило Дзена: не выделять через Ctrl+A).
        """
        await self.page.keyboard.press("Control+ArrowRight")
        await _human_wait(0.05, 0.15)
        await self.page.keyboard.press("Shift+Control+ArrowLeft")
        await _human_wait(0.1, 0.25)

    async def _click_block_type_in_menu(self, block_kind: str) -> bool:
        """
        Выбор типа блока в панели Дзена. Приоритет: getByRole(button, name) — самый надёжный.
        H2, H3, Blockquote, ul, ol по списку селекторов из документации Дзена.
        """
        await _human_wait(0.5, 1.0)
        try:
            toolbar = self.page.locator(DZEN["toolbar"]).first
            if await toolbar.count() > 0:
                await toolbar.wait_for(state="visible", timeout=3000)
        except Exception:
            pass
        # Сначала getByRole (рекомендовано для Дзена)
        role_names = []
        if block_kind == "h2":
            role_names = ["Heading 2", "Заголовок 2"]
        elif block_kind == "h3":
            role_names = ["Heading 3", "Заголовок 3"]
        elif block_kind == "blockquote":
            role_names = ["Blockquote", "Цитата", "Quote"]
        elif block_kind == "ul":
            role_names = ["ul", "Маркированный список", "Bulleted list"]
        elif block_kind == "ol":
            role_names = ["ol", "Нумерованный список", "Numbered list"]
        elif block_kind == "p":
            role_names = ["Paragraph", "Обычный текст", "текст"]
        for name in role_names:
            btn = self.page.get_by_role("button", name=name)
            if await btn.count() > 0:
                try:
                    await btn.first.scroll_into_view_if_needed(timeout=2000)
                    if await btn.first.is_visible():
                        await btn.first.click(timeout=3000)
                        await _human_wait(0.3, 0.6)
                        return True
                except Exception:
                    pass
        return False

    async def _select_current_line_safe(self) -> None:
        """Выделить текущую строку: Home (начало строки) → Shift+ArrowDown (выделить строку).
        Курсор должен быть на нужной строке (сразу после _paste_text).
        Тулбар Дзена появляется автоматически при выделении."""
        await self.page.keyboard.press("Home")
        await _human_wait(0.05, 0.15)
        await self.page.keyboard.press("Shift+ArrowDown")
        await _human_wait(0.3, 0.6)

    async def _format_current_line(self, block_kind: str) -> bool:
        """Выделить строку (Home → Shift+Down) → кликнуть кнопку формата (aria-label) → снять выделение (ArrowRight).
        Кнопки формата — div с aria-label, НЕ button. Тулбар появляется автоматически при выделении."""
        await self._select_current_line_safe()
        result = False
        # Карта block_kind → aria-label кнопки в тулбаре Дзена
        label_map = {
            "h2": "Heading 2",
            "h3": "Heading 3",
            "blockquote": "Blockquote",
            "ul": "ul",
            "ol": "ol",
        }
        label = label_map.get(block_kind)
        if label:
            btn = self.page.locator(f'[aria-label="{label}"]')
            try:
                if await btn.count() > 0 and await btn.first.is_visible():
                    await btn.first.click(timeout=3000)
                    await _human_wait(0.3, 0.6)
                    logger.info("Формат %s применён (aria-label='%s')", block_kind, label)
                    result = True
                else:
                    logger.warning("Кнопка формата [aria-label='%s'] не найдена или не видна", label)
            except Exception as e:
                logger.warning("Клик по [aria-label='%s'] не удался: %s", label, e)
        if not result:
            logger.warning("Формат %s не применён, текст остался параграфом", block_kind)
        # Снять выделение — ArrowRight перемещает курсор в конец и снимает выделение
        await self.page.keyboard.press("ArrowRight")
        await _human_wait(0.1, 0.2)
        return result

    async def _click_bold_button(self) -> bool:
        """Нажать кнопку жирного в тулбаре (aria-label='Bold')."""
        try:
            btn = self.page.locator('[aria-label="Bold"]')
            if await btn.count() > 0 and await btn.first.is_visible():
                await btn.first.click(timeout=3000)
                await _human_wait(0.2, 0.4)
                logger.info("Жирный применён (aria-label='Bold')")
                return True
        except Exception as e:
            logger.warning("Кнопка Bold не найдена или клик не удался: %s", e)
        return False

    async def _move_cursor_to_block_start(self) -> bool:
        """Перемещает курсор в НАЧАЛО текущего Draft.js-блока через JavaScript.
        Обычный Home перемещает только в начало визуальной строки; если абзац
        переносится на несколько строк — Home попадёт в начало ПОСЛЕДНЕЙ строки,
        а не в начало абзаца. Этот метод решает проблему."""
        try:
            return await self.page.evaluate(
                """() => {
                    const sel = window.getSelection();
                    if (!sel || sel.rangeCount === 0) return false;
                    const range = sel.getRangeAt(0);
                    let node = range.startContainer;
                    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
                    if (!node || !node.closest) return false;
                    const selectors = [
                        '[class*="DraftEditor-block"]',
                        '[class*="DraftEditor-block" i]',
                        '[data-block-key]',
                        '[data-block-type]',
                        '[class*="paragraph"]',
                        'div[contenteditable="true"] > div'
                    ];
                    let block = null;
                    for (const s of selectors) {
                        try {
                            block = node.closest(s);
                            if (block && block.closest('[contenteditable="true"]')) break;
                        } catch (e) {}
                    }
                    if (!block) return false;
                    try {
                        // Найти первый текстовый узел в блоке
                        const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, null, false);
                        const firstText = walker.nextNode();
                        if (!firstText) return false;
                        const r = document.createRange();
                        r.setStart(firstText, 0);
                        r.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(r);
                        return true;
                    } catch (e) { return false; }
                }"""
            )
        except Exception:
            return False

    async def _move_cursor_to_block_end(self) -> bool:
        """Перемещает курсор в КОНЕЦ текущего Draft.js-блока через JavaScript.
        Обычный End перемещает только в конец визуальной строки; если абзац
        переносится на несколько строк — End попадёт в конец ПЕРВОЙ строки,
        а не в конец абзаца. Следующий Enter тогда разрежет абзац."""
        try:
            return await self.page.evaluate(
                """() => {
                    const sel = window.getSelection();
                    if (!sel || sel.rangeCount === 0) return false;
                    const range = sel.getRangeAt(0);
                    let node = range.startContainer;
                    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
                    if (!node || !node.closest) return false;
                    const selectors = [
                        '[class*="DraftEditor-block"]',
                        '[class*="DraftEditor-block" i]',
                        '[data-block-key]',
                        '[data-block-type]',
                        '[class*="paragraph"]',
                        'div[contenteditable="true"] > div'
                    ];
                    let block = null;
                    for (const s of selectors) {
                        try {
                            block = node.closest(s);
                            if (block && block.closest('[contenteditable="true"]')) break;
                        } catch (e) {}
                    }
                    if (!block) return false;
                    try {
                        // Найти ПОСЛЕДНИЙ текстовый узел в блоке
                        const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, null, false);
                        let lastText = null;
                        let n;
                        while ((n = walker.nextNode())) lastText = n;
                        if (!lastText) return false;
                        const r = document.createRange();
                        r.setStart(lastText, lastText.length);
                        r.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(r);
                        return true;
                    } catch (e) { return false; }
                }"""
            )
        except Exception:
            return False

    async def _apply_bold_after_paragraph(self, text: str) -> None:
        """После вставки абзаца: «ШАГ N.» — 5 символов жирным; вопросы FAQ — вся строка жирным.
        ВАЖНО: после любого форматирования курсор ОБЯЗАТЕЛЬНО возвращается в КОНЕЦ БЛОКА
        (не визуальной строки!), иначе следующий Enter в главном цикле разрежет абзац."""
        text = text.strip()
        if not text:
            return
        # ШАГ 1., ШАГ 2. ... — перемещаем курсор в начало БЛОКА (не визуальной строки!)
        # → 5× Shift+Right → Bold → конец БЛОКА (JS).
        if re.match(r"^ШАГ\s*\d+\s*\.", text):
            # JS-перемещение в начало блока; fallback — Home
            moved = await self._move_cursor_to_block_start()
            if not moved:
                await self.page.keyboard.press("Home")
            await _human_wait(0.05, 0.15)
            for _ in range(5):
                await self.page.keyboard.press("Shift+ArrowRight")
                await _human_wait(0.02, 0.06)
            await self._click_bold_button()
            # КРИТИЧНО: вернуть курсор в конец БЛОКА, а не визуальной строки!
            # End перемещает только в конец текущей визуальной строки,
            # что при длинном абзаце разрежет его при следующем Enter.
            moved = await self._move_cursor_to_block_end()
            if not moved:
                await self.page.keyboard.press("End")
            await _human_wait(0.05, 0.12)
            return
        # FAQ: перемещаем в начало блока → Shift+End → Bold → конец БЛОКА (JS).
        # НЕ используем Shift+ArrowDown — он захватывает следующий блок, Bold ломает чужой текст.
        if "\n" not in text and text.endswith("?"):
            moved = await self._move_cursor_to_block_start()
            if not moved:
                await self.page.keyboard.press("Home")
            await _human_wait(0.05, 0.15)
            await self.page.keyboard.press("Shift+End")
            await _human_wait(0.3, 0.6)
            await self._click_bold_button()
            # Конец БЛОКА, а не визуальной строки
            moved = await self._move_cursor_to_block_end()
            if not moved:
                await self.page.keyboard.press("End")
            await _human_wait(0.1, 0.2)

    async def _insert_paragraph_with_links(self, html: str) -> None:
        """Вставить абзац со ссылками: печатаем plain text, затем для каждой <a href> выделяем текст-якорь и добавляем URL через тулбар Дзена (кнопка Link).
        Это надёжнее, чем _paste_html — Draft.js часто игнорирует <a> из буфера."""
        # Парсим ссылки из HTML
        links = re.findall(r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL | re.I)
        plain = self._html_to_plain_text(html)

        # Вставляем plain text
        await self._paste_text(plain)
        await _human_wait(0.3, 0.6)

        if not links:
            return

        # Для каждой ссылки: находим текст-якорь в строке, выделяем его, добавляем URL
        for url, anchor_html in links:
            anchor = re.sub(r"<[^>]+>", "", anchor_html).strip()
            if not anchor or not url:
                continue

            # Ищем позицию якоря в plain text
            pos = plain.find(anchor)
            if pos < 0:
                logger.warning("Якорь '%s' не найден в тексте, пропускаю ссылку", anchor[:30])
                continue

            # Home → pos раз ArrowRight → выделить len(anchor) символов → кнопка Link → вставить URL
            await self.page.keyboard.press("Home")
            await _human_wait(0.05, 0.1)
            for _ in range(pos):
                await self.page.keyboard.press("ArrowRight")
                await _human_wait(0.01, 0.03)
            for _ in range(len(anchor)):
                await self.page.keyboard.press("Shift+ArrowRight")
                await _human_wait(0.01, 0.03)
            await _human_wait(0.3, 0.6)

            # Кликаем кнопку Link в тулбаре
            link_btn = self.page.locator('[aria-label="Link"]')
            try:
                if await link_btn.count() > 0 and await link_btn.first.is_visible():
                    await link_btn.first.click(timeout=3000)
                    await _human_wait(0.5, 1.0)

                    # Ищем поле ввода URL в появившемся popup/input
                    url_input = self.page.locator(
                        'input[type="url"], input[placeholder*="ссылк" i], input[placeholder*="URL" i], '
                        'input[placeholder*="http" i], input[placeholder*="link" i], '
                        '[role="dialog"] input[type="text"], input[data-testid*="link" i]'
                    ).first
                    if await url_input.count() > 0 and await url_input.is_visible():
                        await url_input.fill(url)
                        await _human_wait(0.2, 0.4)
                        await self.page.keyboard.press("Enter")
                        await _human_wait(0.3, 0.6)
                        logger.info("Ссылка вставлена: %s → %s", anchor[:30], url[:50])
                    else:
                        logger.warning("Поле URL не найдено после клика по Link")
                        await self.page.keyboard.press("Escape")
                else:
                    logger.warning("Кнопка Link [aria-label='Link'] не видна в тулбаре")
            except Exception as e:
                logger.warning("Не удалось вставить ссылку '%s': %s", anchor[:30], e)
                await self.page.keyboard.press("Escape")

            # Снять выделение
            await self.page.keyboard.press("End")
            await _human_wait(0.1, 0.2)

    async def _insert_block_via_editor(
        self,
        block_kind: str,
        text: str,
        list_items: Optional[List[str]] = None,
        html_for_paste: Optional[str] = None,
    ) -> None:
        """
        Вставить блок в редактор Дзена.
        Текст вводится → Shift+Ctrl+Up (выделить строку) → клик по aria-label кнопке формата.
        _paste_html НЕ используется — Дзен не парсит HTML из буфера.
        """
        await _human_wait(0.2, 0.5)
        if block_kind == "p_with_link" and html_for_paste:
            # Ссылки: вставляем текст, затем для каждой <a> выделяем якорь и добавляем URL через тулбар
            await self._insert_paragraph_with_links(html_for_paste)
            return
        if block_kind == "p":
            await self._paste_text(text)
            await _human_wait(0.2, 0.4)
            await self._apply_bold_after_paragraph(text)
            return
        # H2, H3, blockquote: ввод текста → Shift+Ctrl+Up (выделить) → aria-label кнопка формата
        if block_kind in ("h2", "h3", "blockquote"):
            await self._paste_text(text)
            await _human_wait(0.2, 0.4)
            await self._format_current_line(block_kind)
            return
        # Списки: первый пункт вводим + формат, остальные через Enter
        if block_kind in ("ul", "ol") and list_items:
            for idx, item in enumerate(list_items):
                if idx > 0:
                    await self.page.keyboard.press("Enter")
                    await _human_wait(0.1, 0.25)
                await self._paste_text(item)
                if idx == 0:
                    await _human_wait(0.2, 0.4)
                    await self._format_current_line(block_kind)
                    await _human_wait(0.2, 0.4)
            await _human_wait(0.2, 0.4)
            return
        await self._paste_text(text)

    async def _paste_html(self, html: str):
        """Вставить HTML через буфер — Draft.js сохраняет h1–h6, blockquote, списки.
        Два способа: 1) clipboard API + Ctrl+V  2) программный paste event (надёжнее для Draft.js)."""
        plain = self._html_to_plain_text(html)
        wrapped = html if html.strip().lower().startswith("<html") else f"<html><body>{html}</body></html>"
        pasted = False

        # Способ 1: clipboard API + Ctrl+V
        try:
            await self.page.evaluate(
                """async (args) => {
                    await navigator.clipboard.write([
                        new ClipboardItem({
                            "text/html": new Blob([args.wrapped], { type: "text/html" }),
                            "text/plain": new Blob([args.plain], { type: "text/plain" })
                        })
                    ]);
                }""",
                {"wrapped": wrapped, "plain": plain},
            )
            await _human_wait(0.15, 0.4)
            await self.page.keyboard.press("Control+v")
            await _human_wait(0.7, 1.5)
            pasted = True
        except Exception as e:
            logger.debug("clipboard.write не сработал: %s, пробую paste event", e)

        # Способ 2: программный paste event (Draft.js слушает onPaste и парсит text/html)
        if not pasted:
            try:
                await self.page.evaluate(
                    """(args) => {
                        const el = document.querySelector('[contenteditable="true"]');
                        if (!el) return;
                        el.focus();
                        const dt = new DataTransfer();
                        dt.setData('text/html', args.wrapped);
                        dt.setData('text/plain', args.plain);
                        const event = new ClipboardEvent('paste', {
                            clipboardData: dt,
                            bubbles: true,
                            cancelable: true
                        });
                        el.dispatchEvent(event);
                    }""",
                    {"wrapped": wrapped, "plain": plain},
                )
                await _human_wait(0.7, 1.5)
                pasted = True
            except Exception as e2:
                logger.warning("paste event тоже не сработал: %s, вставляю plain text", e2)

        if not pasted:
            await self._paste_text(plain)

    async def _paste_text(self, text: str):
        """Вставить plain text через буфер обмена."""
        try:
            await self.page.evaluate(
                """async (t) => {
                await navigator.clipboard.writeText(t);
            }""",
                text,
            )
            await self.page.wait_for_timeout(200)
            await self.page.keyboard.press("Control+v")
            await self.page.wait_for_timeout(500)
        except Exception as e:
            logger.warning("Вставка через буфер не сработала: %s, печатаю...", e)
            await self.page.keyboard.type(text, delay=5)

    async def _dismiss_help_popup(self):
        """Закрыть модалку подсказки/help в редакторе статей."""
        for _ in range(5):
            try:
                for btn_text in ["Понятно", "Закрыть", "Пропустить", "Продолжить", "Ок", "OK"]:
                    btn = self.page.get_by_role("button", name=btn_text)
                    if await btn.count() > 0:
                        await btn.first.click(timeout=2000)
                        await self.page.wait_for_timeout(500)
                        return True
            except Exception:
                pass
            try:
                close_btn = self.page.locator('[class*="help-popup"] button, .ReactModal__Content button').first
                if await close_btn.count() > 0:
                    await close_btn.click(timeout=2000)
                    await self.page.wait_for_timeout(500)
                    return True
            except Exception:
                pass
            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(300)
        return False

    async def _dismiss_donation_modal(self):
        """Закрыть попап донатов. Только селекторы из DZEN: donations_popup + close-button."""
        for _ in range(5):
            try:
                popup = self.page.locator(DZEN["donations_popup"])
                if await popup.count() > 0 and await popup.first.is_visible():
                    close_btn = popup.locator(DZEN["popup_close"]).first
                    if await close_btn.count() > 0:
                        await close_btn.click(timeout=2000)
                        await self.page.wait_for_timeout(500)
                        return True
            except Exception:
                pass
            try:
                close = self.page.locator(DZEN["popup_close"]).first
                if await close.count() > 0 and await close.is_visible():
                    await close.click(timeout=2000)
                    await self.page.wait_for_timeout(500)
                    return True
            except Exception:
                pass
            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(400)
        return False

    async def _open_new_article_editor(self):
        """Перейти в редактор новой статьи: data-testid add-publication-button → Написать статью."""
        title_check = self.page.locator(DZEN["title_field"]).first
        if await title_check.count() > 0 and await title_check.is_visible():
            logger.info("Редактор уже открыт")
            return

        logger.info("Открываю редактор новой статьи...")
        await self.page.goto("https://dzen.ru/profile/editor/flowcabinet/publications", wait_until="domcontentloaded")
        await _human_wait(2.5, 4)
        await self._dismiss_donation_modal()
        await _human_wait(0.6, 1.2)

        # Приоритет: официальные селекторы Дзена
        add_btn = self.page.locator(DZEN["add_publication"]).first
        await add_btn.wait_for(state="visible", timeout=10000)
        await add_btn.hover()
        await _human_wait(0.4, 0.9)
        await add_btn.click(timeout=3000)
        await _human_wait(1.5, 3)

        write_article = self.page.locator(DZEN["write_article"]).first
        await write_article.wait_for(state="visible", timeout=8000)
        await write_article.click(timeout=3000)
        await _human_wait(2, 4)

        await _human_wait(2, 4)
        try:
            await self.page.wait_for_selector(DZEN["title_field"], timeout=20000)
            await _human_wait(2, 3.5)
        except Exception:
            await self.page.wait_for_selector(DZEN["body_editor"], timeout=15000)

        await self._dismiss_help_popup()

    async def login(self) -> bool:
        try:
            logger.info("=" * 50)
            logger.info("НАЧАЛО АВТОРИЗАЦИИ")
            logger.info("=" * 50)

            await self.page.goto(self.CREATE_POST_URL, wait_until="domcontentloaded")
            await _human_wait(2, 4)
            await self._wait_captcha_if_present()
            await _human_wait(0.5, 1.2)
            if await dismiss_yandex_default_search_modal(self.page):
                logger.info("Модалка «Яндекс станет основным поиском» закрыта.")
            await _human_wait(1, 2)

            # Проверка: уже залогинены (профиль, «Новая статья», нет «Войти»)
            logged_in_selectors = [
                '[data-testid="user-menu"]',
                ".user-avatar",
                "a[href*='profile']",
                "button:has-text('Новая статья')",
                "a:has-text('Новая статья')",
            ]
            for selector in logged_in_selectors:
                if await self.page.locator(selector).count() > 0:
                    logger.info("Уже авторизованы (cookies)")
                    return True

            login_btn = self.page.get_by_text("Войти", exact=False)
            if await login_btn.count() > 0:
                pass
            else:
                logger.info("Признаки входа есть, считаем залогиненными.")
                return True

            if not self.email or not self.password:
                await self.screenshot("error_not_logged_in")
                logger.error("Не залогинены и нет ZEN_EMAIL/ZEN_PASSWORD. Сохраните куки: capture_cookies.py")
                return False

            logger.info("Переход на страницу входа: %s", self.LOGIN_URL)
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)

            email_selectors = [
                'input[type="email"]',
                'input[name="login"]',
                'input[placeholder*="mail"]',
                "#passp-field-login",
            ]
            for selector in email_selectors:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    await field.click()
                    await field.fill(self.email)
                    logger.info("Email заполнен")
                    break
            await self.page.wait_for_timeout(500)

            password_selectors = ['input[type="password"]', 'input[name="passwd"]', "#passp-field-passwd"]
            for selector in password_selectors:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    await field.click()
                    await field.fill(self.password)
                    logger.info("Пароль заполнен")
                    break
            await self.page.wait_for_timeout(500)

            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Войти")',
                'button:has-text("Log in")',
                "#passp:sign-in",
            ]
            for selector in submit_selectors:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    break
            await self.page.wait_for_timeout(5000)

            if "passport" in self.page.url.lower() or "auth" in self.page.url.lower():
                await self.screenshot("error_login_failed")
                logger.error("Авторизация не удалась")
                return False

            await self.save_cookies()
            logger.info("АВТОРИЗАЦИЯ УСПЕШНА")
            return True

        except Exception as e:
            logger.exception("Ошибка авторизации: %s", e)
            await self.screenshot("error_login_exception")
            return False

    async def create_post(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        cover_image: Optional[str] = None,
        video: Optional[str] = None,
        excerpt: Optional[str] = None,
        slug: Optional[str] = None,
        publish: bool = True,
        **kwargs,
    ) -> bool:
        try:
            logger.info("=" * 50)
            logger.info("СОЗДАНИЕ ПОСТА: %s...", title[:50])
            logger.info("=" * 50)

            await self.page.goto(self.CREATE_POST_URL, wait_until="domcontentloaded")
            await _human_wait(2.5, 5)
            await self._wait_captcha_if_present()
            await _human_wait(0.5, 1.2)
            if await dismiss_yandex_default_search_modal(self.page):
                logger.info("Модалка закрыта.")
                await _human_wait(0.4, 0.9)
            for _ in range(5):
                await self.page.keyboard.press("Escape")
                await _human_wait(0.25, 0.6)
            await self._dismiss_donation_modal()
            await _human_wait(1, 2)
            logger.info("Открыта страница: %s", self.page.url)

            await self._open_new_article_editor()

            await self._dismiss_help_popup()
            await _human_wait(1.2, 2.5)

            editors = self.page.locator(f'{DZEN["title_field"]}, {DZEN["body_editor"]}')
            try:
                await editors.first.wait_for(state="visible", timeout=8000)
            except Exception:
                pass
            count = await editors.count()
            logger.info("Найдено полей редактора: %s", count)

            if count >= 1:
                title_el = editors.nth(0)
                await title_el.hover()
                await _human_wait(0.2, 0.5)
                await title_el.click(force=True, timeout=5000)
                await _human_wait(0.3, 0.7)
                await self._clear_field()
                await _human_wait(0.1, 0.25)
                await self.page.keyboard.type(title, delay=random.randint(35, 85))
                logger.info("Заголовок введён: %s", title[:50])
            else:
                logger.warning("Поле заголовка не найдено")
            await _human_wait(0.5, 1.2)

            content_blocks = kwargs.get("content_blocks")
            if content_blocks:
                content_el = editors.nth(1) if count >= 2 else editors.nth(0)
                await content_el.click(force=True, timeout=5000)
                await _human_wait(0.4, 0.9)
                # Защиты от поломки вёрстки: только End+Enter между блоками (никогда Control+End);
                # после списка ul/ol перед картинкой — пустой <p>; картинки вставляются по месту в _add_image_in_article.
                block_results = kwargs.get("block_results")  # опционально: список для чеклиста по каждому блоку
                for i, block in enumerate(content_blocks):
                    if self.page.is_closed():
                        logger.error("Страница закрылась, прерываем вставку блоков")
                        break
                    block_label = _block_label(block)
                    next_is_image = i + 1 < len(content_blocks) and content_blocks[i + 1].get("type") == "image"
                    block_kind = None
                    try:
                        # Между блоками: один Enter (без лишних переносов).
                        if i > 0:
                            await self.page.keyboard.press("Enter")
                            await _human_wait(0.15, 0.3)
                        if block.get("type") == "html":
                            html = block.get("content", "")
                            block_kind, text, list_items = self._parse_html_block(html)
                            next_is_image = i + 1 < len(content_blocks) and content_blocks[i + 1].get("type") == "image"
                            await self._insert_block_via_editor(
                                block_kind,
                                text,
                                list_items=list_items,
                                html_for_paste=html if block_kind == "p_with_link" else None,
                            )
                        # Дополнительных Enter после h2/h3/ul/blockquote НЕ нужно:
                        # между блоками уже есть End + Enter + Enter (строки выше)
                        if block.get("type") == "html":
                            logger.info("Блок HTML #%s вставлен (%s)", i + 1, block_kind)
                            if block_results is not None:
                                block_results.append({"i": i + 1, "type": "html", "label": block_label, "success": True, "error": None})
                        if block.get("type") == "image":
                            img_path = block.get("path", "")
                            image_url = block.get("url")
                            ok = False
                            err = None
                            article_dir = kwargs.get("article_dir")
                            # Вставка по URL (рекламный баннер и т.п.) — без локального файла
                            if image_url and str(image_url).strip().startswith("http"):
                                ok = await self._add_image_in_article(
                                    "", block.get("caption"), image_url=image_url.strip()
                                )
                                if ok:
                                    logger.info("Картинка #%s добавлена по URL", i + 1)
                                else:
                                    err = "не вставлена по URL"
                            elif img_path:
                                if article_dir:
                                    p = article_dir / Path(img_path).name
                                else:
                                    p = Path(img_path)
                                    if not p.is_absolute():
                                        p = PROJECT_ROOT / p
                                    if not p.exists():
                                        if (BLOCK_DIR / "articles" / p.name).exists():
                                            p = BLOCK_DIR / "articles" / p.name
                                    if not p.exists() and not p.is_absolute():
                                        p_alt = PROJECT_ROOT / block.get("path", "")
                                        if p_alt.exists():
                                            p = p_alt
                                if p.exists():
                                    ok = await self._add_image_in_article(
                                        str(p), block.get("caption"), image_url=block.get("url")
                                    )
                                    if ok:
                                        logger.info("Картинка #%s добавлена", i + 1)
                                    else:
                                        err = "не вставлена (side button / file chooser)"
                                else:
                                    err = f"файл не найден: {img_path}"
                            else:
                                err = "нет path и нет url"
                            if block_results is not None:
                                block_results.append({"i": i + 1, "type": "image", "label": block_label, "success": ok, "error": err})
                        await _human_wait(1, 2.5)
                    except Exception as e:
                        err_str = str(e)
                        logger.warning("Блок #%s (%s): %s", i + 1, block_label, err_str)
                        if block_results is not None:
                            block_results.append({"i": i + 1, "type": block.get("type", ""), "label": block_label, "success": False, "error": err_str})
                        # Если страница/браузер закрылись — дальше нет смысла
                        if self.page.is_closed():
                            logger.error("Страница закрылась, прерываем вставку блоков")
                            break
                        # Иначе пропускаем упавший блок и продолжаем
                        continue
            else:
                if count >= 2:
                    content_el = editors.nth(1)
                    await content_el.click(force=True, timeout=5000)
                    await self.page.wait_for_timeout(300)
                    await self._paste_html(content)
                    logger.info("Контент вставлен (HTML с заголовками)")
                elif count >= 1:
                    await self.page.keyboard.press("Enter")
                    await self.page.wait_for_timeout(300)
                    await self._paste_html(content)
                    logger.info("Контент вставлен в единственное поле")
                else:
                    await self.screenshot("error_no_content_field")
                    raise Exception("Не найдено поле редактора (Draft.js)")
                await self.page.wait_for_timeout(1000)
                article_image = kwargs.get("article_image") or (cover_image if (cover_image and os.path.exists(cover_image)) else None)
                if article_image:
                    await self._add_image_in_article(article_image, kwargs.get("image_caption"))

            if self.page.is_closed():
                raise Exception("Страница закрылась до публикации")

            if tags:
                await self._set_tags(tags)

            if video and os.path.exists(video):
                await self._upload_video(video)

            await self._click_publish(cover_image=cover_image, cover_image_url=kwargs.get("cover_image_url"))

            await self.page.wait_for_timeout(3500)
            await self.screenshot("post_created")
            await self.screenshot("post_created_full", full_page=True)
            # Дополнительная проверка: скриншоты для верификации заголовков и картинок
            try:
                editor = self.page.locator('[contenteditable="true"]').first
                if await editor.count() > 0:
                    await editor.evaluate("el => el.scrollIntoView({ block: 'start', behavior: 'instant' })")
                    await self.page.wait_for_timeout(800)
                    await self.screenshot("article_verify_top")
                    try:
                        await editor.evaluate("""el => {
                            const c = el.closest('[class*="editor"], [class*="Editor"], [class*="scroll"]') || el.parentElement || el;
                            if (c && c.scrollHeight > c.clientHeight) {
                                c.scrollTop = Math.floor(c.scrollHeight / 2);
                            }
                        }""")
                        await self.page.wait_for_timeout(600)
                        await self.screenshot("article_verify_mid")
                        await editor.evaluate("""el => {
                            const c = el.closest('[class*="editor"], [class*="Editor"], [class*="scroll"]') || el.parentElement || el;
                            if (c) c.scrollTop = c.scrollHeight;
                        }""")
                        await self.page.wait_for_timeout(600)
                        await self.screenshot("article_verify_bottom")
                    except Exception:
                        pass
            except Exception as e:
                logger.debug("Скриншоты верификации редактора: %s", e)
            logger.info("ПОСТ УСПЕШНО СОЗДАН")
            return True

        except Exception as e:
            logger.exception("Ошибка создания поста: %s", e)
            await self.screenshot("error_create_post")
            return False

    async def _fill_caption_and_exit_image_block(self, caption_to_fill: str, wait_img: bool = True) -> None:
        """Заполнить подпись к картинке и выйти из блока. При необходимости дождаться img в DOM."""
        # LAST — берём последний (только что добавленный) input описания, а не первый!
        cap = self.page.locator(
            'input[placeholder*="описан" i], input[placeholder*="подпись" i], textarea[placeholder*="описан" i], [placeholder*="Описание"]'
        ).last
        if await cap.count() > 0:
            await cap.fill(caption_to_fill)
            await _human_wait(0.3, 0.6)
        if wait_img:
            try:
                await self.page.wait_for_selector(
                    'img[src*="yandex"], img[src*="dzen"], [class*="image"] img', timeout=6000
                )
            except Exception:
                pass
        # 1 Escape — выйти из режима редактирования картинки
        await self.page.keyboard.press("Escape")
        await _human_wait(0.3, 0.5)
        # ArrowDown — переместить курсор ниже картинки (в следующий блок)
        await self.page.keyboard.press("ArrowDown")
        await _human_wait(0.2, 0.4)

    async def _add_image_in_article(
        self,
        image_path: str,
        caption: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> bool:
        """
        Вставить картинку в статью. По ссылке (image_url) — Дзен подтягивает сам;
        с диска (image_path) — загрузка файла как есть (PNG/JPG без конвертации).
        """
        caption_to_fill = (caption or "").strip() or "Описание картинки"
        try:
            # Enter уже нажат в главном цикле. Курсор на пустой строке — кнопка вставки должна появиться.
            await _human_wait(0.4, 0.8)

            insert_img_btn = self.page.locator(DZEN["image_button"]).first
            if await insert_img_btn.count() == 0 or not await insert_img_btn.is_visible():
                # Fallback: input без кнопки (тоже buffer+mimeType)
                path_to_upload = self._ensure_jpeg(image_path, "article")
                payload = self._file_payload(path_to_upload)
                if payload:
                    file_inputs = self.page.locator('input[type="file"][accept*="image"]')
                    if await file_inputs.count() > 0:
                        await file_inputs.first.set_input_files(files=payload)
                        await self.page.wait_for_timeout(5000)
                        await self._fill_caption_and_exit_image_block(caption_to_fill, wait_img=True)
                        logger.info("Картинка добавлена (input, buffer+mime)")
                        return True
                await self.screenshot("error_add_image_failed")
                return False

            # Сначала пробуем вставку по ссылке (Дзен подтягивает сам — без ошибки формата)
            if image_url and image_url.strip().startswith("http"):
                await insert_img_btn.click(timeout=5000)
                await self.page.wait_for_timeout(1500)
                url_input = self.page.locator(
                    'input[type="url"], input[placeholder*="ссылк"], input[placeholder*="URL"], '
                    'input[placeholder*="link"], [role="dialog"] input[type="text"]'
                ).first
                if await url_input.count() > 0 and await url_input.is_visible():
                    await url_input.fill(image_url.strip())
                    await _human_wait(0.3, 0.6)
                    add_btn = self.page.locator(
                        '[role="dialog"] button:has-text("Добавить"), '
                        '[role="dialog"] button:has-text("Вставить"), '
                        'button:has-text("Готово")'
                    ).first
                    if await add_btn.count() > 0 and await add_btn.is_visible():
                        await add_btn.click()
                        await _human_wait(5, 10)
                        await self.page.wait_for_timeout(2000)
                        await self._fill_caption_and_exit_image_block(caption_to_fill, wait_img=True)
                        logger.info("Картинка добавлена по ссылке")
                        return True
                await self.page.keyboard.press("Escape")
                await _human_wait(0.5, 1)
                insert_img_btn = self.page.locator(DZEN["image_button"]).first

            # Загрузка с диска: конвертация в JPEG + buffer+mimeType
            path_to_upload = self._ensure_jpeg(image_path, "article")
            payload = self._file_payload(path_to_upload)
            if not payload:
                logger.warning("Не удалось подготовить картинку для статьи: %s", image_path)
                return False

            # Стратегия 1: клик по кнопке → ищем input[type=file] который появился
            # Считаем input[type=file] ДО клика
            inputs_before = await self.page.locator('input[type="file"]').count()
            await insert_img_btn.click(timeout=8000, force=True)
            await _human_wait(1.5, 3.0)

            # Ищем новый или любой input[type=file]
            file_inputs = self.page.locator('input[type="file"]')
            inputs_after = await file_inputs.count()
            if inputs_after > 0:
                # Берём последний (новый) input
                target_input = file_inputs.nth(inputs_after - 1) if inputs_after > inputs_before else file_inputs.first
                await target_input.set_input_files(files=payload)
                await _human_wait(8, 14)
                await self.page.wait_for_timeout(2000)
                await self._fill_caption_and_exit_image_block(caption_to_fill, wait_img=True)
                logger.info("Картинка добавлена (файл, input)")
                return True

            # Стратегия 2: expect_file_chooser (на случай если input не появился)
            logger.info("input[type=file] не найден после клика, пробую file_chooser...")
            try:
                async with self.page.expect_file_chooser(timeout=15000) as fc:
                    await insert_img_btn.click(timeout=5000, force=True)
                await (await fc.value).set_files(files=payload)
                await _human_wait(8, 14)
                await self.page.wait_for_timeout(2000)
                await self._fill_caption_and_exit_image_block(caption_to_fill, wait_img=True)
                logger.info("Картинка добавлена (файл, file_chooser)")
                return True
            except Exception as e2:
                logger.warning("file_chooser тоже не сработал: %s", e2)
        except Exception as e:
            logger.warning("Не удалось добавить картинку: %s", e)
        await self.screenshot("error_add_image_failed")
        return False

    async def _upload_image(self, image_path: str, label: str = "изображение"):
        try:
            path_to_upload = self._ensure_jpeg(image_path, label)
            payload = self._file_payload(path_to_upload)
            if not payload:
                logger.warning("Не удалось подготовить %s: %s", label, image_path)
                return
            file_inputs = self.page.locator('input[type="file"][accept*="image"]')
            if await file_inputs.count() == 0:
                file_inputs = self.page.locator('input[type="file"]')
            if await file_inputs.count() > 0:
                await file_inputs.first.set_input_files(files=payload)
                await self.page.wait_for_timeout(3000)
                logger.info("%s загружена (buffer+mime): %s", label, path_to_upload)
            else:
                logger.warning("Не найден input для загрузки: %s", label)
        except Exception as e:
            logger.error("Ошибка загрузки %s: %s", label, e)

    async def _upload_image_from_url(self, url: str):
        try:
            import requests
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            tmp = BLOCK_DIR / ".tmp_zen_upload"
            tmp.mkdir(parents=True, exist_ok=True)
            path = tmp / f"cover_url_{datetime.now().strftime('%H%M%S')}.jpg"
            path.write_bytes(r.content)
            await self._upload_image(str(path), "обложка")
            path.unlink(missing_ok=True)
        except Exception as e:
            logger.warning("Обложка по URL не загружена: %s", e)

    async def _upload_video(self, video_path: str):
        try:
            file_input = self.page.locator('input[type="file"][accept*="video"]')
            if await file_input.count() == 0:
                file_input = self.page.locator('input[type="file"]')
            if await file_input.count() > 0:
                await file_input.first.set_input_files(video_path)
                size_mb = os.path.getsize(video_path) / 1024 / 1024
                wait_ms = max(10000, int(size_mb * 10000))
                await self.page.wait_for_timeout(wait_ms)
                logger.info("Видео загружено")
            else:
                logger.warning("Не найден input для загрузки видео")
        except Exception as e:
            logger.error("Ошибка загрузки видео: %s", e)

    async def _set_tags(self, tags: List[str]):
        try:
            for selector in ['input[name="tags"]', 'input[placeholder*="тег"]', ".tags-input"]:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    for tag in tags:
                        await field.fill(tag)
                        await self.page.keyboard.press("Enter")
                        await _human_wait(0.3, 0.7)
                    logger.info("Теги установлены: %s", tags)
                    return
            logger.warning("Поле для тегов не найдено")
        except Exception as e:
            logger.error("Ошибка установки тегов: %s", e)

    def _mime_for_path(self, path: str) -> str:
        """MIME-type по расширению файла (Дзен ожидает явный тип при File API)."""
        p = Path(path)
        suf = (p.suffix or "").lower()
        if suf in (".jpg", ".jpeg"):
            return "image/jpeg"
        if suf == ".webp":
            return "image/webp"
        if suf == ".png":
            return "image/png"
        return "image/jpeg"

    def _file_payload(self, path: str) -> Optional[List[Dict[str, Any]]]:
        """Читает файл и возвращает [{name, mimeType, buffer}] для set_input_files/set_files.
        Файл должен быть предварительно сконвертирован в JPEG через _ensure_jpeg()."""
        p = Path(path)
        if not p.exists():
            return None
        try:
            buf = p.read_bytes()
            name = p.name
            mime = self._mime_for_path(path)
            logger.debug("_file_payload: name=%s, mimeType=%s, size=%d bytes", name, mime, len(buf))
            return [{"name": name, "mimeType": mime, "buffer": buf}]
        except Exception as e:
            logger.warning("_file_payload: не удалось прочитать файл %s: %s", path, e)
            return None

    def _ensure_jpeg(self, image_path: str, label: str = "image") -> str:
        """ВСЕГДА конвертирует картинку в JPEG (Дзен проверяет магические байты, а не только MIME).
        Если >3MB — дополнительно ресайзит до 1792x1024. Возвращает путь к .jpg файлу."""
        img_path = Path(image_path)
        if not img_path.exists():
            return image_path
        if not PIL_AVAILABLE:
            logger.warning("PIL не установлен — картинка идёт как есть: %s", image_path)
            return image_path
        # Если уже JPEG и <3MB — не конвертируем
        if img_path.suffix.lower() in (".jpg", ".jpeg"):
            if img_path.stat().st_size <= 3_000_000:
                return image_path
        try:
            size_bytes = img_path.stat().st_size
            img = Image.open(img_path)
            img.load()
            img = img.convert("RGB")
            # Ресайз если файл >3MB
            if size_bytes > 3_000_000:
                logger.info("[%s] Ресайз %.1f MB → 1792x1024 JPEG", label, size_bytes / 1e6)
                img = img.resize((1792, 1024), Image.Resampling.LANCZOS)
            out_dir = BLOCK_DIR / ".tmp_zen_upload"
            out_dir.mkdir(parents=True, exist_ok=True)
            jpeg_name = f"{label}_{img_path.stem}_{datetime.now().strftime('%H%M%S')}.jpg"
            if len(jpeg_name) > 200:
                jpeg_name = f"{label}_{datetime.now().strftime('%H%M%S')}.jpg"
            jpeg_path = out_dir / jpeg_name
            img.save(str(jpeg_path), "JPEG", quality=88, optimize=True)
            logger.info("[%s] Конвертировано в JPEG: %s (%.1f KB)", label, jpeg_path.name, jpeg_path.stat().st_size / 1024)
            return str(jpeg_path)
        except Exception as e:
            logger.warning("[%s] Конвертация в JPEG не удалась, используем исходный: %s", label, e)
            return image_path

    async def upload_cover(self, image_path: str) -> bool:
        """Подготовка обложки (конвертация в JPEG) и загрузка через File API (buffer + mimeType)."""
        img_path = Path(image_path)
        if not img_path.exists():
            return False
        path_to_upload = self._ensure_jpeg(image_path, "cover")
        payload = self._file_payload(path_to_upload)
        if not payload:
            return False
        try:
            file_input = self.page.locator("input[type=file]").first
            if await file_input.count() > 0:
                await file_input.set_input_files(files=payload)
                await _human_wait(6, 10)
                logger.info("Обложка загружена (upload_cover, buffer+mime)")
                return True
        except Exception as e:
            logger.warning("upload_cover: %s", e)
        return False

    async def _click_publish(
        self,
        cover_image: Optional[str] = None,
        cover_image_url: Optional[str] = None,
    ):
        """Нажать Опубликовать, в модалке загрузить обложку при необходимости, подтвердить."""
        # Закрыть блок ошибки, если перекрывает кнопку
        error_block = self.page.locator('[class*="error-block"][class*="visible"]').first
        if await error_block.count() > 0 and await error_block.is_visible():
            try:
                close_btn = error_block.locator('button[aria-label*="закрыть" i], button[aria-label*="close" i], [class*="close"], [class*="dismiss"]').first
                if await close_btn.count() > 0:
                    await close_btn.click(timeout=2000)
                    await _human_wait(0.5, 1)
                else:
                    await self.page.keyboard.press("Escape")
                    await _human_wait(0.3, 0.6)
            except Exception:
                await self.page.keyboard.press("Escape")
                await _human_wait(0.3, 0.6)

        publish_btn_selectors = [
            DZEN["publish_btn"],
            '[data-testid="publish-button"]',
            'button:has-text("Опубликовать")',
            'button:has-text("Publish")',
            'button[type="submit"]',
            ".publish-button",
        ]
        for selector in publish_btn_selectors:
            button = self.page.locator(selector).first
            if await button.count() > 0 and await button.is_visible():
                try:
                    await button.hover(timeout=3000)
                except Exception:
                    pass
                await _human_wait(0.5, 1.2)
                await button.click(force=True)
                await _human_wait(3, 6)
                logger.info("Открыто окно подготовки публикации")
                await self.screenshot("publish_modal")
                break
        else:
            logger.warning("Кнопка публикации не найдена")
            return

        cover_path = None
        if cover_image and os.path.exists(cover_image):
            cover_path = cover_image
        elif cover_image_url:
            try:
                import requests
                r = requests.get(cover_image_url, timeout=30)
                r.raise_for_status()
                tmp = BLOCK_DIR / ".tmp_zen_upload"
                tmp.mkdir(parents=True, exist_ok=True)
                path = tmp / f"cover_url_{datetime.now().strftime('%H%M%S')}.jpg"
                path.write_bytes(r.content)
                cover_path = str(path)
            except Exception as e:
                logger.warning("Не удалось скачать обложку по URL: %s", e)

        if cover_path:
            try:
                await self.page.wait_for_timeout(3000)
                ok = await self.upload_cover(cover_path)
                if not ok:
                    # Fallback: область обложки или input в модалке (с той же подготовленной обложкой)
                    prepared = self._ensure_jpeg(cover_path, "cover_fallback")
                    payload = self._file_payload(prepared)
                    cover_area = self.page.locator(
                        '[class*="card-preview__overlay"], '
                        '[class*="publication-settings-card-preview"], '
                        '[class*="cover"] [class*="upload"], '
                        '[class*="Cover"] input[type="file"], '
                        'label:has-text("Обложка"), label:has-text("обложк"), '
                        '[data-testid*="cover"]'
                    ).first
                    if await cover_area.count() > 0 and payload:
                        async with self.page.expect_file_chooser(timeout=15000) as fc:
                            await cover_area.click(force=True)
                        await (await fc.value).set_files(files=payload)
                        await _human_wait(6, 10)
                        logger.info("Обложка загружена (клик по области, buffer+mime)")
                    elif payload:
                        in_dialog = self.page.locator('[role="dialog"] input[type="file"], [class*="modal"] input[type="file"]').first
                        if await in_dialog.count() > 0:
                            await in_dialog.set_input_files(files=payload)
                            await _human_wait(6, 10)
                            logger.info("Обложка загружена (input в модалке, buffer+mime)")
                        else:
                            logger.warning("Обложку добавьте вручную в окне публикации")
                    else:
                        logger.warning("Не удалось подготовить файл обложки (buffer)")
            except Exception as e:
                logger.warning("Не удалось загрузить обложку: %s", e)

        # Только кнопки внутри модалки — чтобы не нажать главную «Опубликовать» дважды и не создать дубликат
        confirm_selectors = [
            '[role="dialog"] button:has-text("Опубликовать статью")',
            '[role="dialog"] button:has-text("Опубликовать")',
            '[class*="modal"] button:has-text("Опубликовать статью")',
            '[class*="modal"] button:has-text("Опубликовать")',
            '[role="dialog"] button:has-text("Готово")',
            '[role="dialog"] [data-testid*="publish"]',
            '[role="dialog"] [data-testid*="confirm"]',
            '[role="dialog"] button[type="submit"]',
        ]
        for selector in confirm_selectors:
            btn = self.page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await self.page.wait_for_timeout(3000)
                # Дождаться закрытия модалки, чтобы не было повторного клика и дубликата поста
                try:
                    dialog = self.page.locator('[role="dialog"]').first
                    await dialog.wait_for(state="detached", timeout=15000)
                except Exception:
                    pass
                logger.info("Публикация подтверждена")
                return
        logger.warning("Кнопка подтверждения публикации не найдена")

async def run_post_flow(
    article: dict,
    *,
    publish: bool = False,
    headless: bool = False,
    keep_open: bool = False,
    article_path: Optional[Path] = None,
) -> tuple[int, str]:
    """
    Запуск: ZenClient.start → login → create_post → close.
    article: {"title", "content", "tags", "cover_image", "cover_image_url", "publish", ...}
    article_path: путь к article.json (если задан — картинки ищутся в той же папке).
    Возвращает (exit_code, message). 0 — успех, 1 — не авторизован, 2 — ошибка поста, 3 — ошибка конфига.
    """
    title = (article.get("title") or "").strip()
    content = (article.get("content") or "").strip()
    content_blocks = article.get("content_blocks")
    # В Дзене не больше 5 фото в статье — обрезаем лишние по порядку
    if content_blocks:
        img_count = 0
        _max_images = 5
        new_blocks = []
        for b in content_blocks:
            if b.get("type") == "image":
                if img_count >= _max_images:
                    logger.warning("Пропуск картинки (лимит %s): %s", _max_images, b.get("path", ""))
                    continue
                img_count += 1
            new_blocks.append(b)
        content_blocks = new_blocks
    if not title:
        logger.error("В статье обязателен title.")
        return 3, "Нет title", []
    if not content and not content_blocks:
        logger.error("В статье нужны content или content_blocks.")
        return 3, "Нет content", []

    try:
        client = ZenClient()
    except ValueError as e:
        logger.error("%s", e)
        return 3, str(e), []

    client.headless = headless or client.headless
    client.keep_open = keep_open or client.keep_open

    block_results = []  # чеклист по каждому блоку (заполняется в create_post при content_blocks)
    try:
        await client.start()
        if not await client.login():
            await client.screenshot("error_login_failed")
            return 1, "Не удалось авторизоваться", block_results

        publish_flag = publish if publish else article.get("publish", True)
        article_dir = article_path.parent if article_path else None
        cover = article.get("cover_image") or article.get("cover_image_url")
        if isinstance(cover, str) and cover.startswith("http"):
            cover_path = None
            cover_url = cover
        else:
            cover_path = None
            if cover and not str(cover).startswith("http"):
                if article_dir:
                    p = article_dir / Path(cover).name
                else:
                    p = Path(cover)
                    if not p.is_absolute():
                        p = PROJECT_ROOT / p
                    if not p.exists():
                        if (BLOCK_DIR / "articles" / p.name).exists():
                            p = BLOCK_DIR / "articles" / p.name
                if p.exists():
                    cover_path = str(p)
            cover_url = article.get("cover_image_url")

        result = await client.create_post(
            title=title,
            content=content,
            tags=article.get("tags"),
            cover_image=cover_path,
            cover_image_url=cover_url,
            image_caption=article.get("image_caption"),
            content_blocks=content_blocks,
            publish=publish_flag,
            block_results=block_results,
            article_dir=article_dir,
        )
        if result:
            return 0, "Опубликовано", block_results
        return 2, "Ошибка создания поста", block_results
    except Exception as e:
        logger.exception("Ошибка при постинге: %s", e)
        return 2, str(e), block_results
    finally:
        try:
            await client.close()
        except Exception:
            pass
        # Очистка временных файлов
        tmp_dir = BLOCK_DIR / ".tmp_zen_upload"
        if tmp_dir.exists():
            try:
                shutil.rmtree(str(tmp_dir), ignore_errors=True)
            except Exception:
                pass
