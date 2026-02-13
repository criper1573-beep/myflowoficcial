# Развёртывание всего проекта КонтентЗавод на Beget VPS

Максимально подробная инструкция: что сделать у себя, что на сервере, какие данные понадобятся. Всё, что можно автоматизировать, уже сделано скриптами — тебе нужно выполнять команды по шагам и присылать данные, когда попросят.

---

## Часть 0. Какие данные мне от тебя нужны

Чтобы подставить в скрипты и команды твои значения, нужны такие данные (можно присылать по мере готовности):

| № | Что нужно | Пример | Где взять |
|---|-----------|--------|-----------|
| 1 | **IP-адрес или хост VPS** | `123.45.67.89` или `u12345.beget.tech` | Панель Beget → VPS → данные для доступа |
| 2 | **SSH-логин** | `root` или `u12345` | Там же |
| 3 | **Пароль от SSH или приложенный файл ключа** | — | Там же (или «Ключи SSH») |
| 4 | **Домен или поддомен для дашборда** | `analytics.flowcabinet.ru` | Твой домен, привязанный к VPS в панели Beget |
| 5 | **Путь к проекту на сервере** | `/root/contentzavod` или `/home/u12345/contentzavod` | Решишь на шаге 2; обычно это каталог, куда клонируешь репозиторий |

Когда пришлёшь пункты 1–4 (и путь из 5, если уже решил), можно будет выдать тебе готовые команды с подставленными значениями.

---

## Часть 1. Подготовка у себя на компе

### 1.1. Проверить, что проект в Git

Если проект уже в Git (GitHub / GitLab / другой репозиторий):

- Запомни URL репозитория. В этом проекте: `https://github.com/criper1573-beep/myflowoficcial.git` или SSH: `git@github.com:criper1573-beep/myflowoficcial.git` (см. также `docs/rules/KEYS_AND_TOKENS.md`).
- Он понадобится на сервере для `git clone` и для обновлений через `git pull`.

Если проекта в Git ещё нет:

1. Создай репозиторий на GitHub/GitLab.
2. В корне проекта (папка КонтентЗавод) выполни:
   ```bash
   git init
   git add .
   git commit -m "Initial"
   git remote add origin URL_ТВОЕГО_РЕПОЗИТОРИЯ
   git push -u origin main
   ```
   (URL и ветку `main`/`master` подставь свои.)

### 1.2. Файл .env на сервер не пушится

В репозитории нет файла `.env` (он в `.gitignore`). На сервере `.env` нужно будет создать вручную или скопировать со своего компа (см. шаг 3.5).

---

## Часть 2. Первое подключение к VPS

### 2.0. Проверить, что порт 22 (SSH) открыт

Если позже при подключении PuTTY показывает пустой экран или соединение «висит», или в PowerShell `ssh` не подключается — проверь доступность порта 22.

**В PowerShell выполни:**

```powershell
Test-NetConnection -ComputerName 85.198.66.62 -Port 22
```

(IP подставь свой — из панели Beget.)

- **TcpTestSucceeded : True** — порт открыт, можно подключаться по SSH (см. шаг 2.1).
- **TcpTestSucceeded : False** (при этом **PingSucceeded : True**) — сервер пингуется, но **SSH снаружи недоступен**. Это настраивается на стороне Beget:
  1. Зайди в панель Beget (cp.beget.com) → раздел VPS/Облако → твой сервер.
  2. Посмотри разделы **«Сеть»**, **«Фаервол»**, **«Доступ»** — есть ли возможность открыть входящий порт 22 или «включить SSH-доступ».
  3. Если в панели такого нет — напиши в поддержку Beget (support@beget.com): «Не могу подключиться по SSH к VPS 85.198.66.62, порт 22 недоступен снаружи. Прошу открыть входящий SSH или подсказать, как включить.»

После того как порт 22 станет доступен, повтори проверку `Test-NetConnection` и переходи к шагу 2.1.

### 2.1. Подключиться по SSH

На своём компе открой терминал (PowerShell или «Командная строка»).

**Windows:** можно использовать встроенный OpenSSH или программу PuTTY.

Подключение (подставь свои **логин** и **хост**):

```bash
ssh ЛОГИН@IP_ИЛИ_ХОСТ
```

Примеры:
- `ssh root@123.45.67.89`
- `ssh u12345@u12345.beget.tech`

При первом подключении спросят про «authenticity of host» — напиши `yes` и нажми Enter. Дальше введи пароль от SSH (если настроен ключ — пароль может не спросить).

Успех: в конце строки появится что-то вроде `root@server:~#` или `u12345@vps:~$`. Значит, ты на сервере.

### 2.2. Узнать путь, где будет проект

Обычно проект кладут в домашний каталог пользователя, например:

- от `root`: `/root/contentzavod`
- от обычного пользователя: `/home/ЛОГИН/contentzavod`

Запомни этот путь — он понадобится для скриптов и systemd. Ниже везде будем писать его как **ПУТЬ_К_ПРОЕКТУ**.

---

## Часть 3. Установка проекта на сервере

Все команды ниже выполняются **на VPS по SSH** (после `ssh ЛОГИН@ХОСТ`), если не сказано иное.

### 3.1. Установить Git (если ещё нет)

```bash
sudo apt-get update
sudo apt-get install -y git
```

### 3.2. Клонировать репозиторий

Перейди в каталог, где должен лежать проект (например домашний):

```bash
cd ~
```

Клонируй репозиторий (подставь **свой URL** и при необходимости ветку):

```bash
git clone https://github.com/criper1573-beep/myflowoficcial.git contentzavod
```

Если репозиторий приватный, потребуется логин/пароль или SSH-ключ. После клонирования зайди в папку:

```bash
cd contentzavod
```

Проверь, что есть папка `blocks`:

```bash
ls blocks
```

Должны быть папки `analytics`, `autopost_zen` и т.д.

### 3.3. Запустить скрипт установки окружения

В проекте уже есть скрипт, который ставит Python-окружение и зависимости.

Сначала открой скрипт и подставь свои данные:

```bash
nano docs/scripts/deploy_beget/setup_server.sh
```

В начале файла найди блок:

```bash
PROJECT_DIR="/home/u123/contentzavod"
SERVICE_USER="u123"
```

Замени на **свой путь** и **своего пользователя** (тот, под которым зашёл по SSH). Сохрани: `Ctrl+O`, Enter, `Ctrl+X`.

Запусти скрипт (из корня проекта, т.е. из папки `contentzavod`):

```bash
cd ~/contentzavod
bash docs/scripts/deploy_beget/setup_server.sh
```

Скрипт создаст `venv`, поставит зависимости, создаст папку `storage` и при необходимости скопирует пример `.env`. Если что-то упадёт с ошибкой — пришли текст ошибки.

### 3.4. Создать или отредактировать .env на сервере

Файл `.env` в репозиторий не попадает, его нужно создать на сервере.

Вариант А — скопировать свой локальный `.env` на сервер с компа (из PowerShell на твоём компе, замени логин и хост):

```powershell
scp C:\Users\bbru7\Desktop\КонтентЗавод\.env ЛОГИН@IP_ИЛИ_ХОСТ:~/contentzavod/.env
```

Вариант Б — создать на сервере вручную:

```bash
cd ~/contentzavod
nano .env
```

Минимум для дашборда:

```env
ANALYTICS_DB_PATH=storage/analytics.db
```

Остальные переменные (токены Telegram, GRS_AI и т.д.) можно добавить позже, если на сервере будут боты или автопостинг. Сохрани: `Ctrl+O`, Enter, `Ctrl+X`.

### 3.5. Настроить systemd (чтобы дашборд работал постоянно)

Создай файл сервиса (подставь **своего пользователя** и **путь к проекту**):

```bash
sudo nano /etc/systemd/system/analytics-dashboard.service
```

Вставь (замени `ТВОЙ_ПОЛЬЗОВАТЕЛЬ` и `/путь/к/проекту` на свои, например `root` и `/root/contentzavod`):

```ini
[Unit]
Description=КонтентЗавод — дашборд аналитики
After=network.target

[Service]
Type=simple
User=ТВОЙ_ПОЛЬЗОВАТЕЛЬ
Group=ТВОЙ_ПОЛЬЗОВАТЕЛЬ
WorkingDirectory=/путь/к/проекту
Environment="PYTHONPATH=/путь/к/проекту"
ExecStart=/путь/к/проекту/venv/bin/uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Сохрани: `Ctrl+O`, Enter, `Ctrl+X`.

Включи и запусти сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable analytics-dashboard
sudo systemctl start analytics-dashboard
sudo systemctl status analytics-dashboard
```

В конце должно быть `active (running)`. Если есть ошибка — пришли вывод `status` и строку из логов:  
`sudo journalctl -u analytics-dashboard -n 30`.

### 3.6. Проверить, что дашборд отвечает

На сервере:

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8050/
```

Должно вывести `200`. Тогда дашборд работает локально на VPS. Дальше — вывести его в интернет по домену с HTTPS.

---

## Часть 4. Домен и HTTPS (Nginx + SSL)

Чтобы открывать дашборд по адресу вида `https://analytics.твой-домен.ru`, на VPS нужны Nginx и сертификат.

### 4.1. Установить Nginx

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

### 4.2. Домен для дашборда: свой домен или доступ по IP

**Технический домен Beget** (например `*.beget.tech`, `criper4f.beget.tech`) **нельзя направить на VPS** — у него нельзя изменить A-запись, он предназначен только для виртуального хостинга.

**Варианты:**

- **Свой домен** (рекомендуется): если есть свой домен (не `*.beget.tech`), в панели Beget (раздел домены/DNS) создай A-запись для поддомена (например `analitics.твой-домен.ru`) → IP твоего VPS. Дальше настраиваешь Nginx и SSL по шагам ниже.
- **Доступ по IP**: дашборд можно открывать по адресу `http://IP_ТВОЕГО_VPS` (например `http://85.198.66.62`). В репозитории есть пример конфига: `docs/scripts/deploy_beget/nginx-dashboard-by-ip.conf`. На сервере: положить его в `/etc/nginx/sites-available/dashboard-by-ip`, включить (`ln -sf ... sites-enabled/`), отключить `default` и `analitics` (если были), перезагрузить Nginx. HTTPS по IP оформить нельзя — только HTTP.

В `.env` на сервере укажи `DASHBOARD_PUBLIC_URL` соответственно: `https://твой-домен` или `http://IP_VPS`.

### 4.3. Создать конфиг Nginx для дашборда

```bash
sudo nano /etc/nginx/sites-available/analytics
```

Вставь (замени `analytics.ТВОЙ-ДОМЕН.ru` на свой домен):

```nginx
server {
    listen 80;
    server_name analytics.ТВОЙ-ДОМЕН.ru;

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Сохрани. Включи сайт и проверь конфиг:

```bash
sudo ln -sf /etc/nginx/sites-available/analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

После этого дашборд должен открываться по `http://analytics.твой-домен.ru` (пока без HTTPS).

### 4.4. Включить HTTPS (Let's Encrypt)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d analytics.ТВОЙ-ДОМЕН.ru
```

Следуй подсказкам (email, согласие с правилами). Certbot сам настроит Nginx на HTTPS. В конце дашборд будет доступен по `https://analytics.твой-домен.ru`.

### 4.5. Указать этот URL для Telegram

У себя на компе в `.env` добавь (или измени):

```env
DASHBOARD_PUBLIC_URL=https://analytics.твой-домен.ru
```

После этого кнопка «Дашборд» и команды `/stats`, `/analytics` в боте будут открывать дашборд на Beget.

---

## Часть 5. Как обновлять проект на сервере (апдейты)

Обновления делаются через Git: ты пушишь изменения в репозиторий с компа, на сервере делаешь `git pull` и перезапускаешь сервис.

### 5.1. У себя на компе (как обычно)

- Вносишь изменения в код.
- Коммитишь и пушишь в репозиторий:

```bash
git add .
git commit -m "Описание изменений"
git push
```

  **Быстрый пуш (Windows):** из корня проекта можно запустить скрипт, который сам сделает `add`, `commit` и `push`:
  ```powershell
  .\docs\scripts\deploy_beget\push_to_github.ps1 "Описание изменений"
  ```
  Без аргумента коммит будет с сообщением «Update».

### 5.2. На сервере — подтянуть изменения и перезапустить дашборд

Подключись по SSH к VPS и выполни (путь к проекту подставь свой, если другой):

```bash
cd ~/contentzavod
git pull
sudo systemctl restart analytics-dashboard
```

Проверка:

```bash
sudo systemctl status analytics-dashboard
```

Должно быть `active (running)`. Если после `git pull` были установлены новые зависимости (новые строки в `requirements.txt`), перед перезапуском нужно обновить venv:

```bash
cd ~/contentzavod
source venv/bin/activate
pip install -r docs/config/requirements.txt
pip install -r blocks/analytics/requirements.txt
deactivate
sudo systemctl restart analytics-dashboard
```

### 5.3. Краткая шпаргалка по обновлениям

| Действие | Где | Команды |
|----------|-----|--------|
| Обновил только код (без новых библиотек) | Сервер | `cd ~/contentzavod` → `git pull` → `sudo systemctl restart analytics-dashboard` |
| Добавил новые зависимости в requirements | Сервер | `cd ~/contentzavod` → `git pull` → `source venv/bin/activate` → `pip install -r docs/config/requirements.txt` и `pip install -r blocks/analytics/requirements.txt` → `deactivate` → `sudo systemctl restart analytics-dashboard` |
| Что-то сломалось после обновления | Сервер | `sudo journalctl -u analytics-dashboard -n 50` — пришли вывод, разберёмся |

В репозитории уже есть скрипт обновления. На сервере в корне проекта выполни:

```bash
cd ~/contentzavod
chmod +x docs/scripts/deploy_beget/update.sh
```

Дальше после каждого `git push` с компа заходи на сервер и запускай:

```bash
cd ~/contentzavod
bash docs/scripts/deploy_beget/update.sh
```

Скрипт сделает: `git pull`, обновление зависимостей из requirements, перезапуск сервиса `analytics-dashboard`.

---

## Часть 6. Что прислать, чтобы подставить в команды

Когда будешь готов, пришли (можно частично):

1. **IP или хост VPS** (например `123.45.67.89` или `u12345.beget.tech`).
2. **SSH-логин** (например `root` или `u12345`).
3. **Домен для дашборда** (например `analytics.flowcabinet.ru`).
4. **Путь к проекту на сервере** (после клонирования), например `/root/contentzavod` или `/home/u12345/contentzavod`.

По ним можно будет выдать тебе готовые команды и готовый конфиг systemd/Nginx без замены — только вставить и выполнить.

---

## Если что-то пошло не так

- **Не подключается по SSH** — проверь IP/логин/пароль в панели Beget, убедись, что с компа открыт порт 22 (часто мешают корпоративные файрволы).
- **После git clone нет папки blocks** — проверь, что клонировал именно тот репозиторий и ветку, где лежит проект.
- **Сервис не стартует** — смотри логи: `sudo journalctl -u analytics-dashboard -n 50`; часто причина — неправильный путь в `WorkingDirectory`/`ExecStart` или отсутствие `.env`.
- **Сайт не открывается по домену** — проверь, что домен привязан к этому VPS в панели и что Nginx перезагружен (`sudo systemctl reload nginx`) и конфиг без ошибок (`sudo nginx -t`).

Если пришлёшь текст ошибки или вывод команды — можно точечно подсказать, что поправить.
