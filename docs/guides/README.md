# ContentZavod

Система автоматизированного создания и распространения контента в социальных сетях.

## Суть проекта

- **Автопостинг** статей, постов и медиа в различные каналы (ВК, Дзен, Pinterest, vc.ru, Telegram)
- **Модульная архитектура** — работа разбита на независимые блоки
- **Расширяемость** — новый блок можно добавить без изменения существующего кода

## 🚀 Быстрый старт

**Новичок?** Начните с [GETTING_STARTED.md](GETTING_STARTED.md) — пошаговое руководство по установке и первым шагам.

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | 🚀 Быстрый старт для новичков |
| [PROJECT_RULES.md](PROJECT_RULES.md) | 📋 Правила проекта (ОБЯЗАТЕЛЬНО К ПРОЧТЕНИЮ) |
| [KEYS_AND_TOKENS.md](KEYS_AND_TOKENS.md) | 🔑 Ключи и токены (где получить и как хранить) |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | 📊 Текущий статус проекта |
| [PATCHES.md](PATCHES.md) | 📝 Патчи и история изменений (единый документ) |
| [CHANGELOG.md](CHANGELOG.md) | 📝 Ссылка на PATCHES.md |
| [CHANGELOG_WORKFLOW.md](CHANGELOG_WORKFLOW.md) | 📝 Версии и workflow релизов |
| [GIT_BRANCHING.md](GIT_BRANCHING.md) | 🌿 Ветки main, dev, feature |
| [DEPLOY_WEBHOOK.md](DEPLOY_WEBHOOK.md) | 🚀 Деплой по вебхуку |
| [DEPLOY_STAGING.md](DEPLOY_STAGING.md) | 🧪 Staging (dev на поддомене) |
| [BACKUP_QUICK_START.md](BACKUP_QUICK_START.md) | 💾 Быстрый старт с системой бекапов |
| [BACKUP_SYSTEM.md](BACKUP_SYSTEM.md) | 💾 Полная документация системы бекапов |
| [МУЛЬТИПРОЕКТНОСТЬ.md](МУЛЬТИПРОЕКТНОСТЬ.md) | 📁 Один завод — несколько проектов |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Полная архитектура системы |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Структура каталогов и файлов |
| [BLOCKS_REGISTRY.md](BLOCKS_REGISTRY.md) | Реестр блоков и их статус |
| [CONTENT_ITEM_SCHEMA.md](CONTENT_ITEM_SCHEMA.md) | Схема контент-элемента |
| [GRS_AI_API_INTEGRATION.md](GRS_AI_API_INTEGRATION.md) | Интеграция с GRS AI API |
| [PLAYWRIGHT_AUTOPOST.md](PLAYWRIGHT_AUTOPOST.md) | Автопостинг через Playwright (vc.ru, Дзен, ВК и др.) |
| [BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md](BLUEPRINT_ARTICLE_GENERATION_PROMPTS.md) | **Промпты и инструкции по генерации статей для Дзен/блога** (ключи, заголовок, текст, мета-описание, обложка) |
| [ZEN_ARTICLE_STRUCTURE.md](ZEN_ARTICLE_STRUCTURE.md) | Структура JSON-статьи для Дзен (content_blocks, поля) |
| [MCP_BROWSER.md](MCP_BROWSER.md) | MCP и браузерные инструменты — зачем и как настроить |
| [CURSOR_PLUGIN_AI_OFFICE_SETUP.md](CURSOR_PLUGIN_AI_OFFICE_SETUP.md) | 🧠 Подробная настройка Cursor-плагина «AI Office» (директор + субагенты + MCP) |
| blocks/ai_integrations/README.md | Документация GRS AI Client |
| blocks/ai_integrations/QUICK_REFERENCE.md | Краткий справочник по AI Client |
| blocks/projects/README.md | Конфигурация проектов (мультипроектность) |
| blocks/post_flow/README.md | Post FLOW: посты из Google Таблицы в канал FLOW |

## Блоки

### Создание контента
- Генерация заголовков, текста, картинок
- SEO-оптимизация и хештеги

### Интеграции
- **GRS AI API** ✅ (готов к использованию)
- OpenAI, YandexGPT (в планах)

### Автопостинг
- **NewsBot (Spambot)** ✅ (RSS бот для Telegram)
- **Post FLOW** ✅ (посты из Google Таблицы → GRS AI → канал FLOW)
- ВКонтакте, Дзен, Pinterest, vc.ru (в планах)

### Инфраструктура
- **Проекты** ✅ (конфигурация по каждому проекту — мультипроектность)
- Планировщик, хранилище, логирование, конфигурация

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка

Скопируйте `docs/config/.env.example` в `.env` в корне проекта и добавьте ваш API ключ:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
GRS_AI_API_KEY=ваш_ключ_api
```

### 3. Тестирование GRS AI клиента

```bash
python docs/scripts/scripts/test_grs_ai.py
```

### 4. Использование в коде

```python
from blocks.ai_integrations import GRSAIClient

client = GRSAIClient()
response = client.simple_ask("Привет! Как дела?")
print(response)
```

Подробнее: blocks/ai_integrations/README.md

## Статус

**Готовые блоки:**
- ✅ GRS AI Client — универсальный клиент для работы с AI
- ✅ NewsBot (Spambot) — RSS бот для автопостинга в Telegram

**В разработке:**
- Генерация контента (заголовки, тексты, изображения)
- Адаптеры под площадки
- Автопостинг на другие площадки

## Лицензия

Частный проект.
