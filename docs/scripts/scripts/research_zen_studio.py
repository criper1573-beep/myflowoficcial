# -*- coding: utf-8 -*-
"""
Исследование страницы студии Дзена и редактора статей (с cookies).
Запуск: python docs/scripts/scripts/research_zen_studio.py [--editor]

--editor: дополнительно перейти в «Публикации» → «Новая статья» и сохранить снапшот редактора.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# docs/scripts/scripts/ -> project root (4 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "docs" / "scripts" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Установите: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

try:
    from playwright_helpers import dismiss_yandex_default_search_modal
except ImportError:
    async def dismiss_yandex_default_search_modal(page, timeout_ms=5000):
        return False

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

STORAGE = os.getenv("ZEN_STORAGE_STATE", "zen_storage_state.json")
STORAGE_PATH = (PROJECT_ROOT / STORAGE).resolve() if not os.path.isabs(STORAGE) else Path(STORAGE)
EDITOR_URL = os.getenv("ZEN_EDITOR_URL", "https://dzen.ru/profile/editor/flowcabinet")
OUTPUT_DIR = PROJECT_ROOT / "docs" / "guides"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def _get_snapshot(page, html_fallback=True):
    """Получить accessibility snapshot или HTML."""
    if hasattr(page, "accessibility"):
        try:
            return await page.accessibility.snapshot()
        except Exception:
            pass
    if html_fallback:
        content = await page.content()
        return {"html_preview": content[:30000]}
    return {}


async def _dismiss_donation_modal(page):
    """Закрыть модалку «У нас появились донаты!» и другие overlay."""
    for _ in range(3):
        try:
            close = page.get_by_role("button", name="Закрыть")
            if await close.count() > 0:
                await close.first.click(timeout=2000)
                await page.wait_for_timeout(500)
                continue
        except Exception:
            pass
        try:
            close = page.locator("[aria-label='Закрыть']").first
            if await close.count() > 0:
                await close.click(timeout=2000)
                await page.wait_for_timeout(500)
                continue
        except Exception:
            pass
        try:
            # Крестик в модалке донатов
            x_btn = page.locator("[data-testid='modal-overlay'] ~ * button, .modal button[aria-label], [class*='modal'] button").first
            if await x_btn.count() > 0:
                await x_btn.click(force=True, timeout=2000)
                await page.wait_for_timeout(500)
                continue
        except Exception:
            pass
        try:
            # Эскейп или клик вне модалки
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
        except Exception:
            pass
        break
    return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--editor", action="store_true", help="Перейти в редактор новой статьи")
    parser.add_argument("--image", action="store_true", help="Заполнить редактор, добавить пустую строку и сбросить элементы для вставки картинки")
    parser.add_argument("--cover", action="store_true", help="Нажать Опубликовать и сбросить DOM модалки обложки")
    args = parser.parse_args()

    if not STORAGE_PATH.exists():
        print(f"Файл куки не найден: {STORAGE_PATH}")
        print("Запустите: python docs/scripts/scripts/capture_cookies.py")
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--window-size=1920,1000"],
        )
        context = await browser.new_context(
            storage_state=str(STORAGE_PATH),
            viewport={"width": 1920, "height": 1000},
            locale="ru-RU",
        )
        context.set_default_timeout(30000)
        page = await context.new_page()

        print(f"Переход на {EDITOR_URL} (с cookies)...")
        await page.goto(EDITOR_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await dismiss_yandex_default_search_modal(page, 5000)
        await page.wait_for_timeout(1000)
        for _ in range(5):
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
        await _dismiss_donation_modal(page)
        await page.wait_for_timeout(1500)

        snapshot = await _get_snapshot(page)
        if not isinstance(snapshot, dict):
            snapshot = {}
        snapshot_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
        (OUTPUT_DIR / "zen_studio_snapshot.json").write_text(snapshot_json, encoding="utf-8")
        await page.screenshot(path=str(OUTPUT_DIR / "zen_studio_screenshot.png"))
        print(f"Студия: zen_studio_snapshot.json, zen_studio_screenshot.png")

        if args.editor or args.image or args.cover:
            print("Переход в Публикации → Новая статья...")
            await page.goto("https://dzen.ru/profile/editor/flowcabinet/publications", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            plus_btn = page.locator('[data-testid*="add"]').first
            if await plus_btn.count() > 0:
                await plus_btn.click(timeout=5000)
                await page.wait_for_timeout(2000)
            new_article = page.get_by_text("Написать статью", exact=False)
            if await new_article.count() == 0:
                new_article = page.get_by_role("button", name="Новая статья")
            if await new_article.count() == 0:
                new_article = page.get_by_role("link", name="Новая статья")
            if await new_article.count() > 0:
                await new_article.first.click()
                await page.wait_for_timeout(5000)
            else:
                print("Кнопка «Новая статья» не найдена, пробуем по тексту...")
                btn = page.locator("text=Новая статья").first
                if await btn.count() > 0:
                    await btn.click()
                    await page.wait_for_timeout(5000)

            editor_url = page.url
            print(f"URL редактора: {editor_url}")

            editor_snapshot = await _get_snapshot(page)
            if not isinstance(editor_snapshot, dict):
                editor_snapshot = {}
            editor_snapshot["_meta"] = {"url": editor_url, "title": await page.title()}
            html = await page.content()

            elem_info = await page.evaluate("""() => {
                const inputs = [...document.querySelectorAll('input[type="file"]')].map(el => ({
                    accept: el.accept, name: el.name, id: el.id, className: el.className,
                    parentTag: el.parentElement?.tagName, parentClass: el.parentElement?.className?.slice(0,80),
                    visible: el.offsetParent !== null
                }));
                const imgs = [...document.querySelectorAll('[class*="image" i], [class*="photo" i], [class*="cover" i], [class*="обложк" i], [class*="фото" i], [class*="картинк" i]')].slice(0, 20).map(el => ({
                    tag: el.tagName, className: el.className?.slice(0,100), text: el.textContent?.slice(0,50),
                    role: el.getAttribute('role'), ariaLabel: el.getAttribute('aria-label')
                }));
                const plusBtns = [...document.querySelectorAll('button, [role="button"], a')].filter(el =>
                    /^\\+$/.test((el.textContent||'').trim()) || /добавить|создать|фото|картинк|изображен|обложк/i.test(el.textContent||'') || /добавить|фото|image|photo|cover/i.test(el.getAttribute('aria-label')||'')
                ).slice(0, 15).map(el => ({ tag: el.tagName, text: (el.textContent||'').slice(0,60), ariaLabel: el.getAttribute('aria-label'), className: el.className?.slice(0,80) }));
                return { fileInputs: inputs, imageRelated: imgs, addButtons: plusBtns };
            }""")
            if elem_info:
                (OUTPUT_DIR / "zen_editor_elements.json").write_text(
                    json.dumps(elem_info, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print("Элементы редактора: zen_editor_elements.json")
            if "ProseMirror" in html:
                editor_snapshot["_meta"]["editor"] = "ProseMirror"
            elif "ql-editor" in html or "quill" in html.lower():
                editor_snapshot["_meta"]["editor"] = "Quill"
            elif "TinyMCE" in html or "mce-" in html:
                editor_snapshot["_meta"]["editor"] = "TinyMCE"
            elif "contenteditable" in html:
                editor_snapshot["_meta"]["editor"] = "contenteditable"
            (OUTPUT_DIR / "zen_editor_snapshot.json").write_text(
                json.dumps(editor_snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            await page.screenshot(path=str(OUTPUT_DIR / "zen_editor_screenshot.png"))
            print(f"Редактор: zen_editor_snapshot.json, zen_editor_screenshot.png")

            if args.image:
                print("Заполняю редактор и ищу элементы для картинки...")
                editors = page.locator('.public-DraftEditor-content[contenteditable="true"]')
                if await editors.count() >= 2:
                    await editors.nth(0).click(force=True)
                    await page.keyboard.type("Тест заголовок", delay=30)
                    await page.wait_for_timeout(300)
                    await editors.nth(1).click(force=True)
                    await page.keyboard.type("Тестовый абзац для проверки.", delay=30)
                    await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2500)
                side_btn = page.locator('button[class*="side-button"], button[class*="sideButton"]').first
                if await side_btn.count() > 0:
                    await side_btn.click(force=True)
                    await page.wait_for_timeout(1500)
                blocks = await page.evaluate("""() => {
                    const clickables = [];
                    document.querySelectorAll('button, [role="button"], [class*="block"], [class*="add"], [class*="insert"], a[href="#"], [data-block], [role="menuitem"]').forEach((el, i) => {
                        if (el.offsetParent && el.getBoundingClientRect().width > 0) {
                            const rect = el.getBoundingClientRect();
                            if (rect.top >= 150 && rect.top <= 900) {
                                clickables.push({
                                    i, tag: el.tagName, text: (el.textContent||'').trim().slice(0,50),
                                    class: (el.className||'').slice(0,120), role: el.getAttribute('role'),
                                    ariaLabel: el.getAttribute('aria-label')
                                });
                            }
                        }
                    });
                    return clickables;
                }""")
                (OUTPUT_DIR / "zen_image_block_candidates.json").write_text(
                    json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                await page.screenshot(path=str(OUTPUT_DIR / "zen_after_enter_screenshot.png"))
                print("zen_image_block_candidates.json, zen_after_enter_screenshot.png")

            if args.cover:
                print("Закрываю help-попап, заполняю минимум, нажимаю Опубликовать...")
                for _ in range(5):
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(300)
                close_help = page.get_by_role("button", name="Понятно")
                if await close_help.count() > 0:
                    await close_help.first.click()
                    await page.wait_for_timeout(500)
                editors = page.locator('.public-DraftEditor-content[contenteditable="true"]')
                if await editors.count() >= 2:
                    await editors.nth(0).click(force=True)
                    await page.keyboard.type("Заголовок", delay=30)
                    await editors.nth(1).click(force=True)
                    await page.keyboard.type("Текст статьи.", delay=30)
                    await page.wait_for_timeout(500)
                pub = page.locator('button:has-text("Опубликовать"), [data-testid="article-publish-btn"]').first
                if await pub.count() > 0:
                    await pub.click()
                    await page.wait_for_timeout(5000)
                    modal_info = await page.evaluate("""() => {
                        const inputs = [...document.querySelectorAll('input[type="file"]')].map(el => ({
                            accept: el.accept, name: el.name, id: el.id, visible: el.offsetParent !== null,
                            parent: el.closest('[class*="cover"], [class*="card"], [class*="modal"]')?.className?.slice(0,80)
                        }));
                        const allInputs = document.querySelectorAll('input');
                        const allInputsInfo = [...allInputs].slice(0, 20).map(el => ({ type: el.type, name: el.name, id: el.id, accept: el.accept }));
                        const btns = [...document.querySelectorAll('button, [role="button"], a')].filter(el =>
                            /обложк|добавить|загрузить|выбрать|cover|upload|файл/i.test(el.textContent||'') || /обложк|cover|upload/i.test(el.getAttribute('aria-label')||'')
                        ).slice(0, 20).map(el => ({ tag: el.tagName, text: (el.textContent||'').trim().slice(0,60), ariaLabel: el.getAttribute('aria-label'), class: (el.className||'').slice(0,100) }));
                        const coverArea = document.querySelector('[class*="cover"], [class*="card-preview"]');
                        const overlay = document.querySelector('[class*="overlay"]');
                        return { fileInputs: inputs, allInputs: allInputsInfo, coverButtons: btns, hasCoverArea: !!coverArea, hasOverlay: !!overlay };
                    }""")
                    (OUTPUT_DIR / "zen_cover_modal_elements.json").write_text(
                        json.dumps(modal_info, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    await page.screenshot(path=str(OUTPUT_DIR / "zen_publish_modal_screenshot.png"))
                    print("zen_cover_modal_elements.json, zen_publish_modal_screenshot.png")

        print("\nБраузер открыт 15 сек. Закройте при необходимости.")
        await page.wait_for_timeout(15000)
        await browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
