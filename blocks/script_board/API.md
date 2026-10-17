# Script Board API

Базовый адрес продакшена: `https://script.flowcabinet.ru`.  
Локально сервис слушает `SCRIPT_BOARD_HOST`:`SCRIPT_BOARD_PORT` (по умолчанию `127.0.0.1:8780`).

Доступ снаружи закрыт nginx basic auth. В примерах ниже логин и пароль берутся из окружения и в репозиторий не пишутся:

```bash
SB=https://script.flowcabinet.ru
AUTH="$SONYA_USER:$SONYA_PASS"
```

Автор правки определяется на сервере:

1. заголовок `X-Remote-User` (его выставляет nginx: `proxy_set_header X-Remote-User $remote_user;`);
2. иначе имя пользователя из `Authorization: Basic`;
3. иначе `unknown`.

Если пришли оба заголовка, побеждает `X-Remote-User`.

## Хранилище

Проекты лежат в `blocks/script_board/storage/projects.json` объектом `{ "<id>": { ... } }`.  
Старый файл читается как есть: миграция дописывает `revision: 0` карточкам и проекту и не выкидывает `nodes`, `edges`, `comments` и прочие поля (`width`, `measured`).

История проекта — построчный журнал `storage/history/<projectId>.jsonl`.  
Запись файла атомарная (временный файл + `rename`) под блокировкой `storage/.store.lock`.

`GET /api/projects/{id}` возвращает сам объект проекта, без обёртки с `id`.

## Ревизии

- У проекта есть `revision`. Она растёт на любое реальное изменение.
- У каждой карточки своя `revision`. `PATCH` и `DELETE` карточки сверяют только её, поэтому правка карточки A не конфликтует с правкой карточки B.
- Создание карточки, связи, комментария, переименование, описание, архив и полная запись `PUT` сверяют ревизию проекта.
- Устаревшая или отсутствующая ревизия у существующего проекта даёт `409`:

```json
{"detail": {"code": "revision_conflict", "message": "Устаревшая ревизия карточки", "revision": 4, "cardRevision": 2}}
```

`revision` в этом теле — текущая ревизия проекта, `cardRevision` — текущая ревизия карточки. После 409 нужно перечитать проект и повторить правку.

Одинаковый `PUT` не увеличивает ревизию и не пишет историю. Поле `archived` полной записью не меняется.

## Проекты

| Метод | Путь | Что делает |
| --- | --- | --- |
| `GET` | `/api/projects` | Список `{id, name, revision}`. Архив скрыт. `?include_archived=true` показывает его. |
| `POST` | `/api/projects` | Создать. Тело: `name`, необязательные `scriptDescription`, `nodes`, `edges`, `comments`. Ответ: `{id, revision}`. |
| `GET` | `/api/projects/{id}` | Объект проекта. |
| `PUT` | `/api/projects/{id}` | Полная запись для интерфейса. Для существующего проекта нужна актуальная `revision`. Ответ: `{success, revision, project}`. Новый id создаёт проект. |
| `PATCH` | `/api/projects/{id}` | `name` и/или `scriptDescription` плюс `revision` проекта. |
| `DELETE` | `/api/projects/{id}?revision=` | Мягкое удаление (`archived: true`), проект пропадает из списка. |
| `POST` | `/api/projects/{id}/restore` | Вернуть из архива. Тело: `{revision}`. |

`scriptDescription` — контекст проекта для Сони, не промпт встроенной генерации.

## Карточки, связи, комментарии

Идентификаторы карточек, связей и комментариев не содержат `/`, `\` и `..`. Идентификаторы связей React Flow (`xy-edge__...`) допустимы. Идентификатор проекта — `[A-Za-z0-9_-]+`.

Тип карточки: `client` или `our_response`.

```bash
# карточка
curl -u "$AUTH" -H 'Content-Type: application/json' \
  -d '{"projectRevision":1,"type":"client","position":{"x":10,"y":20},"data":{"title":"Клиент","text":"Здравствуйте"}}' \
  "$SB/api/projects/$ID/cards"

# правка текста своей ревизией карточки
curl -u "$AUTH" -X PATCH -H 'Content-Type: application/json' \
  -d '{"revision":1,"data":{"text":"Новый текст"}}' \
  "$SB/api/projects/$ID/cards/$CARD"

# удалить карточку
curl -u "$AUTH" -X DELETE "$SB/api/projects/$ID/cards/$CARD?revision=2"

# связь
curl -u "$AUTH" -H 'Content-Type: application/json' \
  -d '{"projectRevision":2,"source":"card-a","target":"card-b"}' \
  "$SB/api/projects/$ID/edges"

# удалить связь
curl -u "$AUTH" -X DELETE "$SB/api/projects/$ID/edges/$EDGE?projectRevision=3"

# комментарий
curl -u "$AUTH" -H 'Content-Type: application/json' \
  -d '{"projectRevision":3,"x":12,"y":40,"text":"заметка"}' \
  "$SB/api/projects/$ID/comments"
```

Ответ точечных методов: `{node|edge|comment|goal, projectRevision}` или `{success, projectRevision}`.

## Цели

`goals` — список того, что нужно узнать у клиента, чтобы скрипт можно было закрыть: адрес объекта, площадь, сроки, бюджет, план и другие пункты. У каждого проекта свой список. Старый `projects.json` без поля получает `goals: []`.

Пункт: `{id, text, note?, order, revision}`. `order` — позиция с нуля. `note` можно не передавать.

Как у карточек: правка и удаление сверяют ревизию самой цели. Создание и смена порядка сверяют ревизию проекта. Устаревшая ревизия — `409`, в теле есть `goalRevision`.

```bash
# добавить пункт
curl -u "$AUTH" -H 'Content-Type: application/json' \
  -d '{"projectRevision":1,"text":"Адрес объекта","note":"город, улица, дом"}' \
  "$SB/api/projects/$ID/goals"

# поправить текст своей ревизией цели
curl -u "$AUTH" -X PATCH -H 'Content-Type: application/json' \
  -d '{"revision":1,"text":"Адрес объекта","note":"уточнить подъезд"}' \
  "$SB/api/projects/$ID/goals/$GOAL"

# удалить
curl -u "$AUTH" -X DELETE "$SB/api/projects/$ID/goals/$GOAL?revision=2"

# порядок: ids — все цели проекта, каждая один раз
curl -u "$AUTH" -H 'Content-Type: application/json' \
  -d '{"projectRevision":4,"ids":["goal-b","goal-a"]}' \
  "$SB/api/projects/$ID/goals/reorder"
```

События истории: `goal.create`, `goal.update`, `goal.delete`, `goal.reorder`. В `before`/`after` видно текст и заметку, у перестановки — порядок `{id, order}`. Автор берётся так же, как у карточек.

Полный `PUT` без поля `goals` список не стирает. Соня может вести цели точечно и параллельно с доской.

Соня сначала заводит цели, потом строит ветки скрипта так, чтобы каждый пункт был задан клиенту или закрыт ответом. Перед следующей сессией смотрит `GET /history?exclude_author=sonya&since=...`: если цель изменил человек, скрипт нужно поправить под новый текст.

`PATCH /comments/{id}` требует `projectRevision` и может менять `text`, `x`, `y`.  
`DELETE /comments/{id}?projectRevision=` удаляет комментарий.

## История

```bash
curl -u "$AUTH" \
  "$SB/api/projects/$ID/history?exclude_author=sonya&since=$SINCE"
```

Параметры:

- `since` — ISO-время, epoch в миллисекундах или id события (`evt-...`). Возвращаются события строго после этой точки. Курсор по id ищется в полном журнале до фильтра автора, поэтому `exclude_author=sonya&since=<событие Сони>` показывает чужие правки после этого события.
- `author` — только этот автор, без учёта регистра.
- `exclude_author` — все, кроме этого автора, без учёта регистра.

Событие: `id`, `ts`, `author`, `type`, `cardId`, `edgeId`, `commentId`, `goalId`, `before`, `after`, `revision`.  
Типы: `project.create|rename|description|archive|restore`, `card.create|update|delete`, `edge.create|update|delete`, `comment.create|update|delete`, `goal.create|update|delete|reorder`.

## Порядок для бота Сони

1. `POST /api/projects` и сохранить `revision`.
2. `POST /goals` по пунктам, которые скрипт должен закрыть. Дальше использовать `projectRevision` из ответа.
3. `POST /cards` и `POST /edges` с актуальной ревизией проекта: ветки спрашивают клиента о целях и фиксируют ответ.
4. Перед следующей сессией: `GET /history?exclude_author=sonya&since=<id последнего своего события>`.
5. Правку чужой карточки или цели делать `PATCH` с её собственной `revision`. На `409` перечитать `GET /api/projects/{id}` и повторить.

Полный `PUT` остаётся для автосохранения интерфейса. Бот может им не пользоваться.

## Снятые методы

`POST /api/generate`, `POST /api/improve-text`, `GET /api/check-grs`, `GET /api/models` больше не существуют и отвечают `404`. Встроенной генерации в доске нет.
