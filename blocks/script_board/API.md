# Доска скриптов — HTTP API для бота Сони

База: `https://script.flowcabinet.ru`  
Авторизация: HTTP Basic на nginx. Пользователи: `alexey`, `sonya`.  
Пароль в команды и в этот файл не подставлять — только переменная окружения.

```bash
export SONYA_USER=sonya
export SONYA_PASS="$SONYA_PASS"   # значение уже в окружении агента, не печатать
export SB="${SCRIPT_BOARD_URL:-https://script.flowcabinet.ru}"
export AUTH="$SONYA_USER:$SONYA_PASS"

curl -s -u "$AUTH" "$SB/api/projects"
```

Swagger: `$SB/docs`. Текст карточек пишет Соня запросами ниже, Алексей правит их в интерфейсе.

## Автор правки

На каждую запись API подставляет автора:

1. заголовок `X-Remote-User` (его выставляет nginx);
2. иначе имя из `Authorization: Basic ...`;
3. иначе `unknown`.

Пример для серверного nginx (конфиг на сервере этим репозиторием не меняется):

```nginx
proxy_set_header X-Remote-User $remote_user;
```

Полный образец: [docs/guides/nginx-script-board.conf.example](../../docs/guides/nginx-script-board.conf.example).

Локально без nginx автор задаётся так:

```bash
curl -s -u "$AUTH" -H "X-Remote-User: sonya" ...
```

Если присланы оба заголовка, побеждает `X-Remote-User`. Сравнение автора в фильтрах истории без учёта регистра.

## Хранилище

- Проекты: `blocks/script_board/storage/projects.json` (объект `{ "<projectId>": Project }`).
- История: `blocks/script_board/storage/history/<projectId>.jsonl`, одна строка — одно событие.
- Запись проекта атомарная: временный файл в том же каталоге и `rename`.
- На время чтения и записи берётся файловая блокировка `storage/.store.lock`.
- Старый `projects.json` без поля `revision` мигрирует при первом чтении: проекты, карточки, связи и комментарии сохраняются, у проекта и карточек появляется `revision: 0`. Имена «Проект 1» и «Вариант Леши» не переименовываются.

Каталог можно переопределить переменной `SCRIPT_BOARD_STORAGE`.

## Модель

```jsonc
Project = {
  "id": "project-…",              // есть в ответах GET; в файле ключ объекта
  "name": "Авито — потолки",
  "scriptDescription": "…",       // контекст проекта для Сони, не system-prompt модели
  "revision": 3,                  // версия проекта, растёт на каждое изменение
  "archived": false,
  "nodes": [Card],
  "edges": [Edge],
  "comments": [Comment]
}
Card = {
  "id": "node-a1",
  "type": "client" | "our_response",
  "position": { "x": 0, "y": 0 },
  "data": { "title": "Вопрос о цене", "text": "Сколько стоит потолок?" },
  "revision": 1                   // своя ревизия карточки
}
Edge = { "id": "e-node-a1-node-a2", "source": "node-a1", "target": "node-a2" }
Comment = { "id": "comment-1", "x": 0, "y": 0, "text": "…" }
```

`client` — реплика клиента, `our_response` — наш ответ. Несколько исходящих связей от одной карточки — развилка. Служебные поля React Flow (`width`, `height`, `measured`) можно не присылать; если они уже есть, API их сохраняет.

Id проекта, карточки, связи и комментария: `[A-Za-z0-9_-]+`. Иначе `400`.

## Ревизии и 409

- У проекта и у каждой карточки свой счётчик `revision`.
- Создание и удаление карточки, связи и комментария, переименование, смена `scriptDescription`, архив и полная перезапись проверяют **ревизию проекта** (`projectRevision` или `revision` в теле PUT/PATCH).
- `PATCH` и `DELETE` одной карточки проверяют **ревизию этой карточки**, а не проекта. Правка карточки A не мешает параллельной правке карточки B.
- Чужая или пропущенная ревизия → `409`:

```json
{"detail": {"code": "revision_conflict", "message": "Устаревшая ревизия карточки", "revision": 4, "cardRevision": 2}}
```

`revision` в теле 409 — текущая ревизия проекта. `cardRevision` есть только у конфликта карточки. Данные на диске не меняются. Дальше: `GET` проект и повтор с актуальными номерами.

Одинаковый повторный `PATCH` карточки без изменения текста ревизию не увеличивает.

## История

Каждое изменение дописывает событие:

```json
{
  "id": "evt-…",
  "ts": "2026-10-17T08:16:00.123Z",
  "author": "alexey",
  "type": "card.update",
  "cardId": "node-a1",
  "edgeId": null,
  "commentId": null,
  "before": {},
  "after": {},
  "revision": 4
}
```

Типы: `project.create`, `project.rename`, `project.description`, `project.archive`, `project.restore`, `card.create`, `card.update`, `card.delete`, `edge.create`, `edge.update`, `edge.delete`, `comment.create`, `comment.update`, `comment.delete`.

`GET /api/projects/{id}/history`

| Параметр | Смысл |
|---|---|
| `since` | ISO-время, epoch milliseconds или `id` события. Вернутся только события **строго после** этой точки. Для id точка ищется во всей ленте, потом применяется фильтр автора. |
| `author` | оставить одного автора |
| `exclude_author` | убрать автора. Что изменил Алексей после визита Сони: `exclude_author=sonya&since=<id последнего события Сони>` |

Ответ: `{ "projectId", "revision", "events" }`. История архивного проекта тоже читается. Неизвестный `since`-id → `400`.

## Эндпоинты

| Метод | Путь | Тело / query | Ответ |
|---|---|---|---|
| GET | `/api/projects` | `?include_archived=true` | `[{id, name, revision, archived?}]` |
| POST | `/api/projects` | `{name, scriptDescription?, nodes?, edges?, comments?}` | `{id, revision}` |
| GET | `/api/projects/{id}` | `?include_archived=true` | `Project`. Архив без флага — `404` |
| PUT | `/api/projects/{id}` | полный `Project` с `revision` | `{success, revision, project}`. Новый id создаёт проект и `revision` не требует |
| PATCH | `/api/projects/{id}` | `{revision, name?, scriptDescription?}` | `{success, revision, project}` |
| DELETE | `/api/projects/{id}?revision=` | — | мягкий архив `{success, revision, archived: true}` |
| POST | `/api/projects/{id}/restore` | `{revision}` | `{success, revision, project}` |
| POST | `/api/projects/{id}/cards` | `{projectRevision, id?, type, position, data?}` | `{node, projectRevision}` |
| PATCH | `/api/projects/{id}/cards/{cardId}` | `{revision, type?, position?, data?}` | `{node, projectRevision}`. `data` сливается, а не заменяет карточку целиком |
| DELETE | `/api/projects/{id}/cards/{cardId}?revision=` | ревизия карточки | `{success, projectRevision}`. Связи этой карточки удаляются вместе с ней |
| POST | `/api/projects/{id}/edges` | `{projectRevision, id?, source, target}` | `{edge, projectRevision}` |
| DELETE | `/api/projects/{id}/edges/{edgeId}?projectRevision=` | — | `{success, projectRevision}` |
| POST | `/api/projects/{id}/comments` | `{projectRevision, id?, x, y, text}` | `{comment, projectRevision}` |
| PATCH | `/api/projects/{id}/comments/{commentId}` | `{projectRevision, text?, x?, y?}` | `{comment, projectRevision}` |
| DELETE | `/api/projects/{id}/comments/{commentId}?projectRevision=` | — | `{success, projectRevision}` |
| GET | `/api/projects/{id}/history` | `since`, `author`, `exclude_author` | `{projectId, revision, events}` |

`PUT` оставлен для автосохранения интерфейса. Это полная замена `nodes`, `edges` и `comments`: карточка, которую не прислали, будет удалена. Для бота лучше гранулярные методы. `PUT` существующего проекта без верного `revision` отвечает `409` и ничего не пишет. Если тело совпало с тем, что уже сохранено, ревизия не растёт.

Удаление проекта из списка — архив, не стирание файла. Вернуть: `POST .../restore`.

## Как Соне собрать скрипт

Идти последовательно и подставлять `projectRevision` из последнего ответа. Карточки, которые не зависят друг от друга, можно править параллельно: у каждой свой `revision`.

```bash
# 1. Проект и контекст
curl -s -u "$AUTH" -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  "$SB/api/projects" \
  -d '{"name":"Авито — потолки","scriptDescription":"Ремонт квартир, Москва. Цель — договориться о замере."}'
# {"id":"project-…","revision":1}

P=project-…
REV=1

# 2. Реплика клиента
curl -s -u "$AUTH" -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  "$SB/api/projects/$P/cards" \
  -d "{\"projectRevision\":$REV,\"id\":\"node-q\",\"type\":\"client\",\"position\":{\"x\":0,\"y\":0},\"data\":{\"title\":\"Цена\",\"text\":\"Сколько стоит потолок?\"}}"
# revision карточки будет 1, projectRevision в ответе — следующий номер

# 3. Наш ответ. REV взять из projectRevision предыдущего ответа
curl -s -u "$AUTH" -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  "$SB/api/projects/$P/cards" \
  -d "{\"projectRevision\":$REV,\"id\":\"node-a\",\"type\":\"our_response\",\"position\":{\"x\":0,\"y\":220},\"data\":{\"title\":\"Ответ\",\"text\":\"Зависит от площади. Могу записать на замер.\"}}"

# 4. Связь
curl -s -u "$AUTH" -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  "$SB/api/projects/$P/edges" \
  -d "{\"projectRevision\":$REV,\"source\":\"node-q\",\"target\":\"node-a\"}"

# 5. Развилка: ещё один ответ клиента от той же карточки и связь на него
#    снова POST /cards и POST /edges с новым projectRevision

# 6. Что Алексей поменял после последнего события Сони
curl -s -u "$AUTH" \
  "$SB/api/projects/$P/history?exclude_author=sonya&since=evt-ПОСЛЕДНЕЕ-СОБЫТИЕ-СОНИ"

# 7. Подтянуть его текст в свою карточку. revision — поле карточки из GET, не проекта
curl -s -u "$AUTH" "$SB/api/projects/$P"
curl -s -u "$AUTH" -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  -X PATCH "$SB/api/projects/$P/cards/node-a" \
  -d '{"revision":2,"data":{"text":"Новая формулировка"}}'
```

На `409` не повторять тот же номер. Прочитать проект и отправить текущие `revision` / `cardRevision`.

Полная перезапись по-прежнему работает, если прислать актуальную ревизию:

```bash
curl -s -u "$AUTH" "$SB/api/projects/$P" > /tmp/p.json
# править /tmp/p.json целиком, поле revision не увеличивать самим
curl -s -u "$AUTH" -X PUT -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  "$SB/api/projects/$P" --data-binary @/tmp/p.json
```

Переименовать или сменить только контекст:

```bash
curl -s -u "$AUTH" -H 'Content-Type: application/json' -H 'X-Remote-User: sonya' \
  -X PATCH "$SB/api/projects/$P" \
  -d "{\"revision\":$REV,\"scriptDescription\":\"Новый контекст для Сони\"}"
```

Архив:

```bash
curl -s -u "$AUTH" -H 'X-Remote-User: alexey' -X DELETE "$SB/api/projects/$P?revision=$REV"
```

## Интерфейс

Автосохранение шлёт `PUT` с текущей ревизией. Ответ `409` перечитывает проект и показывает уведомление. Пока локальных несохранённых правок нет, вкладка раз в 12 секунд и при фокусе забирает проект, если выросла ревизия.

Типы событий, клиент и хук для панели истории:

- `blocks/script_board/frontend/src/types.ts`
- `blocks/script_board/frontend/src/api.ts` — объект `api`
- `blocks/script_board/frontend/src/useHistory.ts` — `useHistory(projectId, query?)`
- реэкспорт: `blocks/script_board/frontend/src/index.ts`

```ts
const history = useHistory(projectId, {
  excludeAuthor: "sonya",
  since: lastSeenEventId,
  pollMs: 12000,
});
// history.events[].author, history.events[].before, history.events[].after
```

## Деплой

Коротко: бэкап `blocks/script_board/storage`, `git pull`, `npm ci && npm run build` в `frontend/`, `systemctl restart script-board`. Пошагово: [docs/guides/DEPLOY_SCRIPT_BOARD.md](../../docs/guides/DEPLOY_SCRIPT_BOARD.md).
