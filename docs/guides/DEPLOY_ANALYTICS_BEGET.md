# Деплой дашборда аналитики на Beget

Пошаговая инструкция: что сделать у себя на компе и что — в панели/по SSH на Beget.

---

## Краткий чеклист (что делать по шагам)

| № | Где | Действие |
|---|-----|----------|
| 1 | У себя | Проверить: `python -m blocks.analytics` → открыть http://localhost:8050 |
| 2 | У себя | Собрать архив: папки `blocks`, файл `.env` (или создать .env на сервере потом) |
| 3 | Beget | В панели: домен/поддомен для дашборда (например analytics.ваш-домен.ru), узнать папку сайта и SSH-доступ |
| 4 | SSH | Подключиться: `ssh логин@хост.beget.tech` |
| 5 | SSH | Загрузить проект в папку сайта (распаковать архив или git clone) |
| 6 | SSH | `python3 -m venv venv` → `source venv/bin/activate` → `pip install -r blocks/analytics/requirements.txt` и `pip install python-dotenv` |
| 7 | SSH | Создать `storage`, при необходимости создать/отредактировать `.env` |
| 8 | SSH | Проверка: `PYTHONPATH=. uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050` → в браузере открыть по адресу сервера:8050 |
| 9 | SSH (VPS) | Настроить systemd-сервис (см. шаг 6 ниже) и Nginx + SSL (шаг 7) |
| 10 | У себя | В .env указать `DASHBOARD_PUBLIC_URL=https://analytics.ваш-домен.ru`, запустить `python -m blocks.analytics.telegram_bot` |

Дальше — подробное описание каждого шага.

---

## Что нужно на Beget

- **Либо VPS** (тариф с root/SSH) — так проще всего запустить FastAPI и держать его постоянно.
- **Либо виртуальный хостинг** с SSH (тарифы Start, Noble и т.д.) — тогда способ запуска может отличаться (см. раздел про виртуальный хостинг внизу).

Дальше описано в первую очередь для **VPS**. Если у вас только виртуальный хостинг — делайте шаги 1–2, затем смотрите раздел «Вариант: виртуальный хостинг Beget».

---

## Шаг 1. Подготовить проект на своём компе

1. **Убедиться, что дашборд локально работает:**
   ```bash
   python -m blocks.analytics
   ```
   Откройте в браузере http://localhost:8050 — должна открыться страница со сводкой и списком запусков.

2. **Собрать архив для загрузки на сервер** (из корня проекта КонтентЗавод):
   - Нужны папки: `blocks/` (целиком), `docs/` (можно не брать, если не нужна документация на сервере).
   - Нужен файл в корне: `.env` (или скопировать из `.env.example` и заполнить только то, что нужно для дашборда).
   - На сервере дашборд будет писать БД в `storage/analytics.db` — папку `storage/` можно не класть в архив, она создастся при первом запуске.

   Удобный вариант — залить на Beget через Git (если есть репозиторий) или упаковать в zip:
   ```bash
   # В PowerShell (из корня КонтентЗавод), например:
   Compress-Archive -Path blocks, .env -DestinationPath analytics-deploy.zip
   ```
   Если `.env` не хотите класть в архив (секреты), создадите его на сервере вручную (шаг 4).

---

## Шаг 2. Домен и папка на Beget

1. Зайти в **панель Beget** → раздел **«Сайты»** / **«Домены»**.
2. Либо выбрать существующий домен, либо создать поддомен для дашборда (например `analytics.ваш-домен.ru`).
3. Запомнить **корневую папку сайта** для этого домена (например `analytics.ваш-домен.ru` → папка `analytics.ваш-домен.ru` или `~/analytics.ваш-домен.ru`).

---

## Шаг 3. Подключиться по SSH

1. В панели Beget найти данные для **SSH** (логин, хост вида `u12345678.beget.tech` или IP для VPS).
2. Подключиться, например:
   ```bash
   ssh u12345678@u12345678.beget.tech
   ```
   (логин и хост подставьте свои из панели.)

---

## Шаг 4. Загрузить проект и поставить зависимости

На сервере по SSH выполнить (пути замените на свои):

```bash
# Перейти в папку сайта (пример для виртуального хостинга)
cd ~/analytics.ваш-домен.ru

# Или для VPS, например:
# cd /var/www/analytics

# Вариант А: загрузка архива
# (архив analytics-deploy.zip предварительно залить в эту папку через SFTP/файловый менеджер)
unzip analytics-deploy.zip

# Вариант Б: клонирование репозитория (если проект в Git)
# git clone https://ваш-репо.git .
# или скопировать только нужное

# Создать виртуальное окружение Python
python3 -m venv venv
source venv/bin/activate   # на Windows Beget: venv\Scripts\activate

# Установить зависимости дашборда
pip install -r blocks/analytics/requirements.txt
# Если есть общий requirements.txt в корне — можно: pip install -r docs/config/requirements.txt
pip install python-dotenv
```

Создать папку для БД (если её ещё нет):

```bash
mkdir -p storage
```

Создать или отредактировать `.env` в **корне проекта** (рядом с папкой `blocks/`):

```bash
nano .env
```

Минимум для дашборда можно оставить пусто или задать (по желанию):

```env
ANALYTICS_DB_PATH=storage/analytics.db
```

Сохранить (в nano: Ctrl+O, Enter, Ctrl+X).

---

## Шаг 5. Проверка запуска

Из корня проекта на сервере (с активированным `venv`):

```bash
cd ~/analytics.ваш-домен.ru   # или ваш путь
source venv/bin/activate
export PYTHONPATH=.
uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050
```

Либо из корня проекта (где лежит папка `blocks/`):

```bash
source venv/bin/activate
bash blocks/analytics/run_on_server.sh
```

В браузере открыть: `http://ваш-ip-или-временный-адрес:8050`. Если дашборд открылся — приложение работает. Остановить: Ctrl+C.

---

## Шаг 6. Запуск через systemd (VPS)

Чтобы дашборд работал постоянно и поднимался после перезагрузки:

1. Создать файл сервиса (подставьте свои пути и пользователя):

```bash
sudo nano /etc/systemd/system/analytics-dashboard.service
```

Содержимое (замените `u12345678` и путь на свои):

```ini
[Unit]
Description=Analytics Dashboard (КонтентЗавод)
After=network.target

[Service]
Type=simple
User=u12345678
Group=u12345678
WorkingDirectory=/home/u12345678/analytics.ваш-домен.ru
Environment="PYTHONPATH=/home/u12345678/analytics.ваш-домен.ru"
ExecStart=/home/u12345678/analytics.ваш-домен.ru/venv/bin/uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

2. Включить и запустить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable analytics-dashboard
sudo systemctl start analytics-dashboard
sudo systemctl status analytics-dashboard
```

Если в статусе `active (running)` — сервис работает.

---

## Шаг 7. Nginx и HTTPS (VPS)

Чтобы открывать дашборд по домену с HTTPS (обязательно для Telegram Mini App):

1. Установить Nginx (если ещё не стоит):
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. Создать конфиг сайта (замените домен на свой):

```bash
sudo nano /etc/nginx/sites-available/analytics
```

Вставить (подставьте свой домен):

```nginx
server {
    listen 80;
    server_name analytics.ваш-домен.ru;
    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Включить сайт и перезагрузить Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

4. Включить SSL в панели Beget (раздел «SSL» для домена) или через certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d analytics.ваш-домен.ru
   ```

После этого дашборд будет доступен по `https://analytics.ваш-домен.ru`.

---

## Шаг 8. Указать URL для Telegram

На своём компе (или там, где крутится бот) в `.env` указать публичный HTTPS-адрес дашборда:

```env
DASHBOARD_PUBLIC_URL=https://analytics.ваш-домен.ru
```

Запустить бота: `python -m blocks.analytics.telegram_bot`. В Telegram кнопка «Дашборд» и команды `/stats`, `/analytics` откроют дашборд на Beget.

---

## Вариант: виртуальный хостинг Beget (без VPS)

На виртуальном хостинге обычно нет systemd и своего Nginx. Часто доступны:

- **SSH** в свою папку сайта;
- **Python** (версия уточняется в панели или по `python3 --version`).

Что можно сделать:

1. Загрузить проект в папку сайта (как в шагах 1–4), поднять окружение и установить зависимости.
2. Запустить вручную:
   ```bash
   cd ~/analytics.ваш-домен.ru
   source venv/bin/activate
   export PYTHONPATH=.
   uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050
   ```
   После отключения SSH процесс остановится.

3. Чтобы держать процесс постоянно, в панели Beget использовать **Cron**: задача раз в минуту проверять, запущен ли процесс, и при необходимости запускать его (скрипт-«watchdog»). Либо уточнить в поддержке Beget, как они рекомендуют держать запущенным Python-приложение (долгоживущий процесс).

4. Для HTTPS и домена — использовать настройки **«Сайты»** и **SSL** в панели Beget. Если панель умеет проксировать поддомен на порт 8050 — настроить прокси туда; иначе поддержка подскажет схему для их хостинга.

Итог: **надёжный вариант для дашборда — VPS на Beget** (шаги 1–8). На виртуальном хостинге возможен, но потребует согласования способа запуска и прокси с документацией/поддержкой Beget.
