# Доска скриптов

Редактор скриптов переписки для Авито: карточки `client` и `our_response`, связи, комментарии, контекст `scriptDescription`. Бот Соня собирает скрипт через HTTP API, Алексей правит карточки в интерфейсе. Каждая запись хранит автора и ревизию.

Запуск из корня монорепо:

```bash
pip install -r blocks/script_board/requirements.txt
cd blocks/script_board/frontend && npm ci && npm run build && cd ../../..
python -m blocks.script_board
```

По умолчанию сервис слушает `127.0.0.1:8780` и отдаёт собранный фронт из `frontend/dist`. Переменные: `SCRIPT_BOARD_HOST`, `SCRIPT_BOARD_PORT`, `SCRIPT_BOARD_STORAGE`.

Контракт для бота: [API.md](API.md). Деплой: [docs/guides/DEPLOY_SCRIPT_BOARD.md](../../docs/guides/DEPLOY_SCRIPT_BOARD.md).

Тесты:

```bash
python -m pytest blocks/script_board/tests -q
```

Фронтовые типы, клиент и хук истории: `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/useHistory.ts` (реэкспорт из `frontend/src/index.ts`).
