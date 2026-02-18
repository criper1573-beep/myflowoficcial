# System Patterns

Паттерны и архитектурные решения проекта КонтентЗавод.

---

## Общее

- **Модульность по блокам** — каждый блок в blocks/<name>/ со своей логикой и при необходимости конфигом.
- **Документация в docs/** — архитектура, гайды, конфиг, правила, скрипты разделены по подпапкам.
- **Секреты** — только в .env; имена переменных и примеры в docs/config/.env.example и docs/rules/KEYS_AND_TOKENS.md.

## Интеграции

- **GRS AI** — общий клиент в blocks/ai_integrations/; ключ в .env (GRS_AI_API_KEY).
- **MCP content-factory** — инструменты Zen (publish, draft, delete, list) и GRS (chat, image, models); предпочтительно использовать MCP для Дзен и генерации.
- **Проекты** — YAML в blocks/projects/data/; проект выбирается по PROJECT_ID или аргументу запуска.

## Memory Bank

- Задачи и контекст хранятся в memory-bank/; команды /van, /plan, /creative, /build, /reflect, /archive читают и обновляют эти файлы.
- Правила Cursor в .cursor/rules/ (в т.ч. isolation_rules от cursor-memory-bank) работают вместе с правилами проекта (structure, no-manual-steps, keys, MCP, model-AI).

Дополняйте при принятии новых архитектурных решений.
