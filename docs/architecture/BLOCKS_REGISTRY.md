# Реестр блоков «ContentZavod»

Каждый блок регистрируется здесь. Статус: `planned` | `in_progress` | `ready`.

---

## A. Контент-блоки

| ID | Название | Описание | Статус |
|----|----------|----------|--------|
| A1 | titles | Генерация заголовков | planned |
| A2 | article_text | Генерация текста статьи | planned |
| A3 | images | Генерация/подбор картинок | planned |
| A4 | seo_optimization | SEO-оптимизация (ключевые слова) | planned |
| A5 | hashtags | Генерация хештегов | planned |
| A6 | moderation | Модерация и валидация контента | planned |

---

## B. Интеграционные блоки

| ID | Название | Описание | Статус |
|----|----------|----------|--------|
| B1 | grs_ai_client | GRS AI API клиент (универсальный) | ready |
| B2 | openai_adapter | OpenAI (GPT, DALL-E) | planned |
| B3 | yandex_adapter | YandexGPT | planned |

---

## C. Адаптеры под площадки

| ID | Название | Площадка | Статус |
|----|----------|----------|--------|
| C1 | vk_adapter | ВКонтакте | planned |
| C2 | zen_adapter | Яндекс.Дзен | planned |
| C3 | pinterest_adapter | Pinterest | planned |
| C4 | vcru_adapter | vc.ru | planned |
| C5 | telegram_adapter | Telegram | planned |

---

## D. Автопостинг

| ID | Название | Площадка | Статус |
|----|----------|----------|--------|
| D0 | spambot_newsbot | Telegram (RSS бот) | ready |
| D0b | **post_flow** | Telegram (посты из Google Таблицы + GRS AI) | **ready** |
| D1 | autopost_vk | ВКонтакте | planned |
| D2 | autopost_zen | Яндекс.Дзен | ready |
| D3 | autopost_pinterest | Pinterest | planned |
| D4 | autopost_vcru | vc.ru | planned |
| D5 | autopost_telegram | Telegram | planned |

---

## E. Инфраструктурные блоки

| ID | Название | Описание | Статус |
|----|----------|----------|--------|
| E1 | scheduler | Планировщик очереди постов | planned |
| E2 | storage | Хранилище контента | planned |
| E3 | logging_monitor | Логирование и мониторинг | planned |
| E4 | config | Конфигурация и секреты | planned |
| E5 | web_api | Веб-интерфейс / API управления | planned |
| E6 | **проекты** | Конфигурация по каждому проекту (мультипроектность) | **ready** |

---

## Зависимости между блоками

```
Content Creation (A1–A5)  →  AI Integrations (B1–B3)
        ↓
SEO + Hashtags (A4, A5)
        ↓
Platform Adapters (C1–C5)  →  ContentItem.variants
        ↓
Scheduler (E1)
        ↓
Autoposting (D1–D5)
        ↓
Storage (E2) + Logging (E3)
```

---

## Порядок разработки блоков

1. **Ядро:** ContentItem, Pipeline, Block Registry  
2. **E4, E3:** Config, Logging (база для отладки)  
3. **B1–B3:** AI-интеграции  
4. **A1–A5:** Content Creation  
5. **C1–C5:** Адаптеры  
6. **D1–D5:** Автопостинг  
7. **E1, E2:** Scheduler, Storage  
8. **E5:** Web API  
