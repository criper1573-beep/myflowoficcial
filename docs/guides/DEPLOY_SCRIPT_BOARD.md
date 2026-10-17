# Деплой доски скриптов

Сервис: systemd-юнит `script-board`. Каталог на сервере: `/root/contentzavod`. Порт приложения: `8780` (только localhost). Сайт: https://script.flowcabinet.ru.

Этот документ — порядок обновления. Сам деплой из репозитория не запускается.

## Обновление

На сервере, из `/root/contentzavod`:

```bash
# 1. Бэкап хранилища (проекты и история правок)
stamp=$(date +%F-%H%M)
mkdir -p /root/backups
cp -a blocks/script_board/storage "/root/backups/script-board-storage-$stamp"

# 2. Код
git pull

# 3. Зависимости API, если менялся requirements
# ./venv/bin/pip install -r blocks/script_board/requirements.txt

# 4. Сборка фронта
cd blocks/script_board/frontend
npm ci
npm run build
cd /root/contentzavod

# 5. Рестарт сервиса
sudo systemctl restart script-board
sudo systemctl status script-board --no-pager
```

Проверка без браузера: `curl -s -u "$AUTH" http://127.0.0.1:8780/api/projects` на самом сервере. Пароль брать из локального хранилища паролей, не из git.

Файл `blocks/script_board/storage/projects.json` и каталог `storage/history/` в git не входят. `git pull` их не затирает. Если каталога `storage` на сервере ещё нет, его создаст процесс при первой записи; перед обновлением поверх уже работающего сервера бэкап обязателен.

До этого изменения кода доски в git не было: на сервере каталог `blocks/script_board` может лежать как неотслеживаемые файлы. Тогда `git pull` остановится с сообщением, что неотслеживаемые файлы будут перезаписаны. Каталог `storage` уже должен быть в бэкапе. Старый код можно убрать в сторону (`mv blocks/script_board /root/backups/script-board-code-$stamp`) и повторить `git pull`. Каталог `storage` после pull нужно вернуть из бэкапа, если он уехал вместе со старым кодом.

## Автор правки

Один раз в конфиге nginx (не в этом репозитории) нужно прокинуть логин basic auth:

```nginx
proxy_set_header X-Remote-User $remote_user;
```

Полный пример: [nginx-script-board.conf.example](nginx-script-board.conf.example). Пока заголовка нет, API берёт имя из `Authorization`, если nginx его не вырезает, иначе автор будет `unknown`.

## Контракт для бота

[blocks/script_board/API.md](../../blocks/script_board/API.md)
