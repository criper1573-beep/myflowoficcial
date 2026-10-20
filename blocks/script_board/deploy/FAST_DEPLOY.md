# Быстрый деплой доски скриптов

Сайт: https://script.flowcabinet.ru. Сервер: `85.198.66.62`. Код: `/root/contentzavod/blocks/script_board`. Сервис: systemd-юнит `script-board`. Процесс: `/root/contentzavod/venv/bin/python -m blocks.script_board`, порт по умолчанию `8780`.

Данные — файлы, не база. Проекты лежат в `blocks/script_board/storage/projects.json`, история — в `storage/history/<id>.jsonl`. Если в окружении задан `SCRIPT_BOARD_STORAGE`, живые данные берутся оттуда. Корневой `.env` проекта — `/root/contentzavod/.env`. Отдельный `.env` внутри папки блока, если он есть, тоже сохраняется.

Push в git сервер не обновляет. Сначала GitHub Actions публикует готовый архив, потом на VPS вручную запускается скрипт рядом с этим файлом.

## Что делает GitHub Actions

Файл: `.github/workflows/script-board-release.yml`.

Запускается сам при push в `script-board/live-baseline` или `live-baseline`, если изменились файлы в `blocks/script_board/**`. Второе имя нужно, если ветку когда-нибудь переименуют в `live-baseline`: сейчас живая ветка называется `script-board/live-baseline`. Ещё запускается вручную: Actions → Script Board release → Run workflow.

На раннере ставятся зависимости Python, гоняются тесты `blocks/script_board/tests`, собирается фронт (`npm ci`, `npm run build`). Готовый каталог пакуется в `script-board-<sha7>.tar.gz`, рядом кладётся файл sha256. Оба файла прикрепляются к GitHub Release с тегом `script-board-<sha7>`.

В архиве исходники блока и собранный `dist/`. Туда не входят `node_modules`, `projects.json`, история и `.env`. На сервере Node не нужен: Windows-`node_modules` в папке блока больше не мешают, потому что папка кода заменяется целиком, а зависимости фронта в архив не кладутся.

SSH, рестарт сервиса и запись на VPS из workflow нет.

## Один раз настроить руками

1. В GitHub у репозитория: Settings → Actions → General → Workflow permissions → Read and write. Иначе `GITHUB_TOKEN` не сможет создать Release. Содержимое других веток это право не выкладывает на сервер.
2. Создать fine-grained PAT только на чтение содержимого этого репозитория (Contents: Read-only). Положить одну строкой в `/root/.config/flow/gh-token` и выполнить `chmod 600`. Значение в git не коммитить. Описание: `docs/rules/KEYS_AND_TOKENS.md`.
3. Положить `fast-deploy.sh` на сервер и сделать `chmod +x`. После мержа файл есть в репозитории по пути `blocks/script_board/deploy/fast-deploy.sh`. Если живая папка блока не из git, скопировать скрипт в неё отдельно. Дальше скрипт обновляется вместе с папкой, но уже запущенный процесс читает старый файл до конца.
4. На сервере уже должны быть юнит `script-board`, виртуальное окружение `/root/contentzavod/venv` и каталог nginx `/var/www/script-flowcabinet/assets`. Скрипт дописывает туда новые файлы из `dist/assets` без удаления старых хэшей: nginx отдаёт `/assets/` из этого каталога, а `index.html` читает FastAPI из `dist`.

## Запуск

От root на сервере:

```bash
/root/contentzavod/blocks/script_board/deploy/fast-deploy.sh
/root/contentzavod/blocks/script_board/deploy/fast-deploy.sh script-board-abc1234
/root/contentzavod/blocks/script_board/deploy/fast-deploy.sh abc1234
/root/contentzavod/blocks/script_board/deploy/fast-deploy.sh --rollback
```

Без аргумента берётся самый новый релиз с тегом `script-board-` и семью шестнадцатеричными символами среди ста последних релизов репозитория.

## Что делает скрипт

`set -euo pipefail`. Лог пишется в `/var/log/script-board-deploy.log`. Повторный запуск, пока первый не закончился, сразу выходит.

1. Читает токен из `/root/.config/flow/gh-token`. В лог и в список процессов токен не попадает: curl ходит через временный netrc.
2. Скачивает архив и sha256. Проверяет сумму до остановки сервиса. Если сумма не сошлась, папка приложения не трогается.
3. Останавливает `script-board`.
4. Копирует данные и `.env` в `/root/backups/script-board/<ГГГГММДД-ЧЧММСС>-before-<tag>/`: каталог `storage`, `repo.env` (корневой `.env`) и `block.env`, если он был.
5. Текущую папку переименовывает в `/root/contentzavod/blocks/script_board.previous`. На её место ставит новую поставку. Из поставки выкидываются `storage`, `.env` и `node_modules`, затем в неё копируются живые данные и блоковый `.env`. Корневой `.env` только бэкапится и не перезаписывается.
6. Ставит Python-зависимости в уже существующий venv: `pip install -r requirements.txt`.
7. Копирует `dist/assets` в `/var/www/script-flowcabinet/assets` через `rsync -a` без `--delete`.
8. Запускает `script-board` и несколько раз вызывает `curl` на `http://127.0.0.1:<порт>/`. Порт берётся из окружения юнита или из `.env`, иначе `8780`. Ответ `200` или `401` — успех.
9. Если проверка не прошла, скрипт сам возвращает предыдущую папку кода, снова кладёт текущие данные и `.env`, копирует старые ассеты и повторяет проверку. Код выхода при этом ненулевой.

`--rollback` меняет текущую папку и `script_board.previous` местами. Данные и `.env` не откатываются к снимку: после отката в восстановленный код кладутся те данные, которые были живыми в момент отката. Снимок до выкладки остаётся в каталоге бэкапа, его можно вернуть отдельно, если понадобится именно старый `projects.json`.

## Сколько занимает

Обычно меньше минуты. Архив около одного мегабайта, сервис стоит только на время подмены папки, `pip` и перезапуска. Если venv ещё без пакетов и pip качает их заново, запас до полутора минут.
