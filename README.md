# ContentZavod

Система автоматизированного создания и распространения контента. Папка проекта должна называться **ContentZavod** (латиница) — см. docs/guides/GETTING_STARTED.md.

---

## Структура проекта

- **blocks/** — код всех блоков (AI, автопостинг, аналитика и др.)
- **docs/** — вся документация, конфигурация, скрипты, бекапы

Подробнее: **docs/guides/README.md**

---

## Быстрый старт

### Post FLOW (посты из Google Таблицы в Telegram)

Из корня проекта (после `pip install -r docs\config\requirements.txt` и настройки `.env` / credentials):

```bash
python -m blocks.post_flow.bot
```

Подробнее: **docs/guides/** и блок **blocks/post_flow/**.

### Первая настройка

1. Создайте `.env` в корне:
   ```
   copy docs\config\.env.example .env
   ```
2. В `.env` задайте `GRS_AI_API_KEY` (общий для всех проектов) и при необходимости `PROJECT_ID=flowcabinet`.
3. Добавьте проект: скопируйте `blocks/projects/data/project.example.yaml` в `blocks/projects/data/<id>.yaml` и заполните `telegram`.
4. Установите зависимости:
   ```
   pip install -r docs\config\requirements.txt
   ```

**Мультипроектность:** один завод — несколько проектов; у каждого свои аккаунты, API ИИ общий. Подробнее: **docs/guides/MULTIPROJECT.md**

### Docker

Сборка и запуск блоков в контейнере: **docs/guides/DOCKER.md**. Кратко: `docker build -t contentzavod .` и `docker run --env-file .env contentzavod` (по умолчанию запускается Post FLOW; команду можно переопределить).

---

## Документация

| Раздел | Путь |
|--------|------|
| Руководства (старт, справка) | docs/guides/ |
| Правила и ключи | docs/rules/ |
| Архитектура | docs/architecture/ |
| Конфигурация | docs/config/ |
| Скрипты | docs/scripts/scripts/ |

Главный README: **docs/guides/README.md**

---

## Блоки

- **blocks/ai_integrations/** — GRS AI клиент (общий для всех проектов)
- **blocks/post_flow/** — Post FLOW: посты из Google Таблицы (тема → GRS AI → канал FLOW)
- **blocks/projects/** — конфигурация по каждому проекту (мультипроектность)
- **blocks/autopost_zen/** — автопостинг в Дзен (генерация из таблицы + публикация); оркестратор — по расписанию

---

## Оркестратор (автопостинг Дзен на сервере)

Оркестратор контент завода (`orchestrator-kz`) — сервис, который по расписанию генерирует статью из Google Таблицы и публикует в Telegram и Дзен. На сервере он запускается через **systemd**.

### Как он запускается

- **При каждом старте** (в том числе после перезапуска systemd) оркестратор делает **один пробный запуск** цепочки (генерация → Telegram → Дзен), если с последнего запуска прошло не меньше 2 часов. Затем работает по расписанию (5 слотов в день).
- В юните указано **`Restart=on-failure`** и **`RestartSec=30`**: если процесс **упал или был убит** (kill), systemd через 30 секунд **запускает его снова**. Так сервис сам восстанавливается после сбоев.

### Остановка и включение

- **Приостановить (один раз остановить — не генерировать и не перезапускаться по расписанию):** создать файл приостановки и перезапустить сервис. С компа: **`.\docs\scripts\deploy_beget\pause_orchestrator_on_server.ps1`**. На сервере: `./venv/bin/python -m blocks.autopost_zen --pause-orchestrator` и `sudo systemctl restart orchestrator-kz`. После этого при каждом старте оркестратор сразу выходит без генерации.
- **Новый запуск (возобновить оркестратор):** с компа **`.\docs\scripts\deploy_beget\resume_orchestrator_on_server.ps1`** или на сервере: `./venv/bin/python -m blocks.autopost_zen --resume-orchestrator` и `sudo systemctl restart orchestrator-kz`.
- **Просто остановить systemd** (при следующем `start` снова будет работать): **`sudo systemctl stop orchestrator-kz`**. **Включить снова:** **`sudo systemctl start orchestrator-kz`**.

Подробная инструкция: **docs/guides/ORCHESTRATOR_PAUSE_RESUME.md**. Юнит: **docs/scripts/deploy_beget/orchestrator-kz.service.example**, гайды по деплою в **docs/guides/**.

---

Версия: 2.0
