# Деплой Script Board

Сервис: `script-board`. Сайт: https://script.flowcabinet.ru.  
Код блока: `blocks/script_board`. Этот документ не деплоит и не меняет живой nginx.

Быстрый путь: GitHub Actions собирает фронт и публикует архив в релиз `script-board-<sha7>`. На VPS его ставит `blocks/script_board/deploy/fast-deploy.sh`. Push сам сервер не обновляет. Подробности: [blocks/script_board/deploy/FAST_DEPLOY.md](../../blocks/script_board/deploy/FAST_DEPLOY.md).

Пароли и логины basic auth здесь не хранятся.

## Что важно на сервере

- Каталог доски на сервере может быть неотслеживаемым git. Перед обновлением его нужно убрать в сторону, а не затирать `git clean`.
- Процесс запускается из `/root/contentzavod/venv`, не из случайного системного Python.
- nginx отдаёт `/assets/` из `/var/www/script-flowcabinet/assets`. Сборка Vite пишет ассеты в `blocks/script_board/dist/assets`. Их копируют туда отдельно, без `--delete`, чтобы не снести чужие файлы каталога.
- `index.html` читает FastAPI из `blocks/script_board/dist`.

## Обновление

Из каталога репозитория на сервере, после ревью нужной ветки:

```bash
cd /root/contentzavod
cp -a blocks/script_board/storage "/root/script-board-storage-backup-$(date +%Y%m%d%H%M)"

# Если blocks/script_board не в git, сохранить его и вернуть storage после pull.
if ! git ls-files --error-unmatch blocks/script_board/api.py >/dev/null 2>&1; then
  mv blocks/script_board "/root/script-board-untracked-$(date +%Y%m%d%H%M)"
fi

git pull
mkdir -p blocks/script_board/storage
# вернуть storage из бэкапа, если pull пришёл без живого projects.json
if [ ! -f blocks/script_board/storage/projects.json ]; then
  cp -a "/root/script-board-storage-backup-"*"/." blocks/script_board/storage/
fi

/root/contentzavod/venv/bin/pip install -r blocks/script_board/requirements.txt
cd blocks/script_board/frontend
npm ci
npm run build
cd /root/contentzavod
rsync -a blocks/script_board/dist/assets/ /var/www/script-flowcabinet/assets/
sudo systemctl restart script-board
```

`rsync` намеренно без `--delete`. Старые хэши в `/var/www/script-flowcabinet/assets` можно убрать отдельно, когда убедились, что новый `index.html` на них не ссылается.

Живой `projects.json` в git не коммитится. Миграция при первом чтении дописывает ревизии и не удаляет карточки, связи и комментарии. Каталог `storage/history/` появится сам.

## Автор в истории

Один раз в `location`, который проксирует доску, добавить заголовок и перезагрузить nginx. Конфиг сервера этим репозиторием не переписывается:

```nginx
proxy_set_header X-Remote-User $remote_user;
```

Пример целиком: `docs/guides/nginx-script-board.conf.example`.

Без этого заголовка автор берётся из логина basic auth, иначе записывается `unknown`.

## Переменные

- `SCRIPT_BOARD_HOST` — по умолчанию `127.0.0.1` (снаружи слушает nginx).
- `SCRIPT_BOARD_PORT` — по умолчанию `8780`.
- `SCRIPT_BOARD_STORAGE` — необязательный каталог вместо `blocks/script_board/storage`.

Ключи GRS AI доске больше не нужны. Общий клиент GRS других блоков не трогать.
