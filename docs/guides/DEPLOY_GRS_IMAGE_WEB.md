# Деплой GRS Image Web на сервер и домен flowimage.ru

Краткая инструкция по выкладке блока **blocks/grs_image_web** (генерация изображений GRS AI) на VPS и настройке домена flowimage.ru.

---

## Что нужно заранее

| Данные | Где взять |
|--------|-----------|
| **IP или хост VPS** | В проекте используется `85.198.66.62` (см. `docs/rules/KEYS_AND_TOKENS.md`) |
| **SSH-логин** | Обычно `root` |
| **Пароль SSH** | Хранить в `.env`: `SERVER_SSH_PASSWORD=...` или для скриптов `DEPLOY_SSH_PASSWORD=...` (не коммитить) |
| **Путь к проекту на сервере** | Например `/root/contentzavod` |

---

## 1. Быстрая загрузка на сервер (с Windows)

### 1.1. Через скрипт (архив + SCP)

1. Установи [PuTTY](https://www.putty.org/) (нужны `pscp.exe` и `plink.exe`, обычно в `C:\Program Files\PuTTY\`).

2. Задай пароль SSH в переменной (в том же сеансе PowerShell выполни загрузку):
   ```powershell
   $env:DEPLOY_SSH_PASSWORD = "твой_пароль_ssh"
   ```

3. Из корня проекта выполни:
   ```powershell
   .\docs\scripts\deploy_beget\make_zip_and_upload.ps1
   ```
   Скрипт соберёт архив (без `.env` и без `venv`) и загрузит его на сервер как `/root/contentzavod.zip`.

### 1.2. Распаковка и первый запуск на сервере (по SSH)

Подключись к серверу:
```bash
ssh root@85.198.66.62
```

Выполни (путь к проекту — `/root/contentzavod`):

```bash
cd /root
# Если папка проекта уже есть — бэкап и очистка для распаковки поверх
mkdir -p contentzavod
cd contentzavod
unzip -o /root/contentzavod.zip
# Или если архив кладёт файлы в корень архива: unzip -o /root/contentzavod.zip
# Тогда после распаковки в /root появятся blocks, docs и т.д. — перенеси в contentzavod при необходимости.

# Виртуальное окружение (один раз)
python3 -m venv venv
source venv/bin/activate
pip install -r docs/config/requirements.txt
pip install uvicorn
deactivate

# .env на сервере создать вручную (скопировать с компа или задать переменные)
# Минимум для GRS Image Web:
# GRS_AI_API_KEY=...
# GRS_IMAGE_WEB_HOST=0.0.0.0
# GRS_IMAGE_WEB_PORT=8765
# GRS_IMAGE_WEB_REQUIRE_AUTH=false   # или true, если нужен Telegram Login
# При авторизации: TELEGRAM_BOT_TOKEN=..., GRS_IMAGE_WEB_BOT_USERNAME=...

# Проверка запуска (вручную)
cd /root/contentzavod
PYTHONPATH=/root/contentzavod ./venv/bin/uvicorn blocks.grs_image_web.api:app --host 0.0.0.0 --port 8765
# Открой в браузере: http://85.198.66.62:8765
# Остановка: Ctrl+C
```

Дальше — запуск через systemd (см. ниже).

---

## 2. Сервис systemd (постоянный запуск)

На сервере создай юнит (подставь свой путь и пользователя):

```bash
sudo nano /etc/systemd/system/grs-image-web.service
```

Содержимое (пример для пути `/root/contentzavod`):

```ini
[Unit]
Description=КонтентЗавод — GRS Image Web (генерация изображений)
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/contentzavod
Environment="PYTHONPATH=/root/contentzavod"
ExecStart=/root/contentzavod/venv/bin/uvicorn blocks.grs_image_web.api:app --host 127.0.0.1 --port 8765
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Включение и запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable grs-image-web
sudo systemctl start grs-image-web
sudo systemctl status grs-image-web
```

Логи:
```bash
sudo journalctl -u grs-image-web -f -n 100
```

Готовый пример юнита в репозитории: `docs/scripts/deploy_beget/grs-image-web.service.example`.

---

## 3. Домен flowimage.ru (Nginx + SSL)

Когда DNS для flowimage.ru указывает **только** на IP сервера (`85.198.66.62`):

- **Важно:** В DNS не должно быть второй A-записи (например на `87.236.16.23`). Должна быть только одна A-запись: `85.198.66.62`. Иначе Let's Encrypt будет проверять домен на другом IP и выдаст ошибку 500.

1. На сервере установи Nginx (если ещё не стоит) и certbot:
   ```bash
   apt update && apt install -y nginx certbot python3-certbot-nginx
   ```

2. Создай конфиг Nginx для flowimage.ru (пример в репозитории: `docs/scripts/deploy_beget/nginx-flowimage.ru.conf.example`):
   ```bash
   sudo nano /etc/nginx/sites-available/flowimage.ru
   ```
   Укажи в нём `server_name flowimage.ru www.flowimage.ru;` и `proxy_pass http://127.0.0.1:8765;`.

3. Включи сайт и получи сертификат:
   ```bash
   sudo ln -sf /etc/nginx/sites-available/flowimage.ru /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d flowimage.ru -d www.flowimage.ru
   ```

4. Если certbot выдал ошибку «87.236.16.23: Invalid response... 500» — в панели DNS удали лишнюю A-запись (оставь только `85.198.66.62`), подожди 5–10 минут и на сервере выполни:
   ```bash
   sudo bash /root/contentzavod/docs/scripts/deploy_beget/get-ssl-flowimage.sh
   ```
   Или вручную: `sudo certbot --nginx -d flowimage.ru -d www.flowimage.ru --non-interactive --agree-tos --register-unsafely-without-email`

5. В BotFather для бота, указанного в `GRS_IMAGE_WEB_BOT_USERNAME`, выполни `/setdomain` и укажи домен `flowimage.ru` (или тот, с которого открывается страница входа).

После этого приложение будет доступно по https://flowimage.ru. Продление сертификата настроено через systemd-таймер `certbot.timer`.

---

## 4. Обновление после изменений в коде

Если на сервере используется Git:
```bash
cd /root/contentzavod
git pull
source venv/bin/activate
pip install -r docs/config/requirements.txt
deactivate
sudo systemctl restart grs-image-web
```

Либо используй общий скрипт обновления (если добавлен сервис grs-image-web):
```bash
bash docs/scripts/deploy_beget/update.sh
```

Если проект заливаешь архивом — снова выполни шаг 1.1, затем на сервере распакуй архив в каталог проекта и перезапусти сервис:
```bash
cd /root/contentzavod && unzip -o /root/contentzavod.zip
sudo systemctl restart grs-image-web
```

---

## 5. Переменные окружения на сервере

В `.env` в корне проекта на сервере (см. также `docs/rules/KEYS_AND_TOKENS.md` и `docs/config/.env.example`):

| Переменная | Описание |
|------------|----------|
| `GRS_AI_API_KEY` | Ключ GRS AI (обязательно для генерации) |
| `GRS_IMAGE_WEB_HOST` | На сервере за Nginx: `127.0.0.1`; без Nginx: `0.0.0.0` |
| `GRS_IMAGE_WEB_PORT` | Порт приложения (по умолчанию `8765`) |
| `GRS_IMAGE_WEB_REQUIRE_AUTH` | `true` — вход через Telegram; `false` — локальный режим без входа |
| `TELEGRAM_BOT_TOKEN` | Нужен при `REQUIRE_AUTH=true` для проверки Telegram Login |
| `GRS_IMAGE_WEB_BOT_USERNAME` | Имя бота без @ (для виджета и `/setdomain` под flowimage.ru) |

Генерации сохраняются в `blocks/grs_image_web/generated/<telegram_id>/` (при отключённой авторизации — в `generated/0/`).
