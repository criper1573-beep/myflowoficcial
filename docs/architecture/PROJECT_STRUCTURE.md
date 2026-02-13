# Структура проекта «ContentZavod»

## Дерево каталогов

```
ContentZavod/
│
├── ARCHITECTURE.md          # Полная архитектура (этот документ)
├── PROJECT_STRUCTURE.md     # Структура проекта
├── BLOCKS_REGISTRY.md       # Реестр блоков
├── README.md                # Описание проекта
│
├── config/                  # Конфигурация
│   ├── main.yaml            # Основные настройки
│   ├── pipelines.yaml       # Определение пайплайнов
│   └── .env.example         # Пример переменных окружения
│
├── core/                    # Ядро системы
│   ├── __init__.py
│   ├── content_item.py      # Модель ContentItem
│   ├── pipeline.py          # Оркестратор пайплайна
│   ├── block_registry.py    # Реестр блоков
│   ├── block_interface.py   # Интерфейс/протокол блока
│   └── context.py           # BlockContext, общие типы
│
├── blocks/                  # Блоки (модули)
│   │
│   ├── content_creation/    # [A] Создание контента
│   │   ├── __init__.py
│   │   ├── titles.py
│   │   ├── article_text.py
│   │   ├── images.py
│   │   ├── seo_optimization.py
│   │   └── hashtags.py
│   │
│   ├── ai_integrations/     # [B] Интеграции с ИИ
│   │   ├── __init__.py
│   │   ├── provider.py      # Абстракция над API
│   │   ├── openai_adapter.py
│   │   └── yandex_adapter.py
│   │
│   ├── platform_adapters/   # [C] Адаптеры под площадки
│   │   ├── __init__.py
│   │   ├── vk_adapter.py
│   │   ├── zen_adapter.py
│   │   ├── pinterest_adapter.py
│   │   ├── vcru_adapter.py
│   │   └── telegram_adapter.py
│   │
│   ├── autopost_vk/         # [D] Автопостинг ВК
│   │   ├── __init__.py
│   │   ├── block.py
│   │   └── rules.md
│   │
│   ├── autopost_zen/        # [D] Автопостинг Дзен
│   │   ├── __init__.py
│   │   ├── block.py
│   │   └── rules.md
│   │
│   ├── autopost_pinterest/  # [D] Автопостинг Pinterest
│   │   ├── __init__.py
│   │   ├── block.py
│   │   └── rules.md
│   │
│   ├── autopost_vcru/       # [D] Автопостинг vc.ru
│   │   ├── __init__.py
│   │   ├── block.py
│   │   └── rules.md
│   │
│   ├── autopost_telegram/   # [D] Автопостинг Telegram
│   │   ├── __init__.py
│   │   ├── block.py
│   │   └── rules.md
│   │
│   ├── scheduler/           # [E] Планировщик
│   │   ├── __init__.py
│   │   └── block.py
│   │
│   ├── storage/             # [E] Хранилище контента
│   │   ├── __init__.py
│   │   └── block.py
│   │
│   ├── moderation/          # [A] Модерация
│   │   ├── __init__.py
│   │   └── block.py
│   │
│   └── logging_monitor/     # [E] Логирование
│       ├── __init__.py
│       └── block.py
│
├── pipelines/               # Определения пайплайнов (если YAML недостаточно)
│   └── default.py
│
├── storage/                 # Физическое хранилище (создаётся при запуске)
│   ├── content/             # Сохранённый контент
│   ├── images/              # Кэш изображений
│   └── logs/                # Логи
│
├── scripts/                 # Вспомогательные скрипты
│   ├── run_pipeline.py      # Запуск пайплайна
│   └── register_blocks.py   # Регистрация блоков
│
├── tests/                   # Тесты
│   ├── core/
│   └── blocks/
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Принципы структуры

1. **core/** — только ядро, без бизнес-логики площадок.
2. **blocks/** — каждый блок в своей папке, изолирован от других.
3. **rules.md** в каждом публикационном блоке — правила площадки.
4. **config/** — вся конфигурация в одном месте.
5. **storage/** — данные приложения, не коммитятся в git.

---

## Добавление нового блока

1. Создать папку `blocks/new_block_name/`
2. Реализовать интерфейс `Block`
3. Добавить в `BLOCKS_REGISTRY.md`
4. Зарегистрировать в `block_registry.py` или через конфиг
5. Добавить блок в нужный пайплайн в `config/pipelines.yaml`

Существующий код менять не нужно.
