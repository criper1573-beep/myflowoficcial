# Tech Context

Технологический стек и окружение КонтентЗавод.

---

## Стек

- **Язык:** Python 3.x
- **Зависимости:** docs/config/requirements.txt; установка: `pip install -r docs/config/requirements.txt`
- **Окружение:** .env в корне (см. docs/config/.env.example)

## Ключевые технологии

- **Telegram:** боты через API (Post FLOW, оркестратор, уведомления).
- **Google Sheets/Таблицы:** источник тем для постов (Post FLOW).
- **GRS AI:** API для генерации текста и изображений.
- **Дзен:** публикация статей (в т.ч. через MCP, Playwright при необходимости).
- **Playwright:** автоматизация браузера (автопостинг, тесты).
- **MCP:** сервер content-factory в blocks/mcp_server/; конфиг Cursor/MCP для zen_*, grs_*.

## Платформа

- Разработка: Windows (PowerShell); скрипты и сервисы деплоя учитывают Linux (Beget, docs/scripts/deploy_beget/).
- Пути в правилах и скриптах при необходимости учитывают OS (path separators).

## Точки входа

- Примеры: `python -m blocks.post_flow.bot`, оркестратор и др. — **docs/guides/** и **blocks/<block>/**.
