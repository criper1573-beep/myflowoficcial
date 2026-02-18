# Дашборд аналитики на домене flowimage.store

Краткая инструкция: как вывести дашборд (порт 8050) на домен **flowimage.store** с HTTPS.

**Предполагается:** VPS уже настроен (проект в `/root/contentzavod`, сервис `analytics-dashboard` запущен), дашборд открывается по IP `http://85.198.66.62`.

**Важно:** Код на сервере должен быть из репозитория **https://github.com/criper1573-beep/myflowoficcial** (ветка `main`). Если после `git push` с компа на flowimage.store не появляются изменения (фавикон, зелёные сервисы и т.д.) — на сервере, скорее всего, другой remote или старый клон. Выполни один раз на сервере:
```bash
cd /root/contentzavod
bash docs/scripts/deploy_beget/fix_server_repo_and_pull.sh
```
Скрипт привяжет `origin` к myflowoficcial, сделает `git pull` и перезапустит дашборд.

**Если на сервере проект был развёрнут из zip (нет .git)** — один раз выполни по SSH:
```bash
cd /root/contentzavod
cp .env .env.bak
git init
git remote add origin https://github.com/criper1573-beep/myflowoficcial.git
git fetch origin main
git reset --hard FETCH_HEAD
git branch -M main
sudo systemctl restart analytics-dashboard
sudo systemctl restart grs-image-web
```
После этого код в каталоге будет из GitHub; дальнейшие обновления — через `git pull` и перезапуск сервисов.

---

## 1. DNS

В панели регистратора домена (где куплен flowimage.store) создай **A-запись**:

| Тип | Имя  | Значение      | TTL (опционально) |
|-----|------|---------------|-------------------|
| A   | @    | 85.198.66.62  | 300               |
| A   | www  | 85.198.66.62  | 300               |

Должна быть **только одна** A-запись на этот IP (без лишних записей на другие IP, иначе Let's Encrypt может выдать ошибку). Подожди 5–15 минут после сохранения.

---

## 2. Nginx на сервере

По SSH на сервер:

```bash
cd /root/contentzavod
sudo cp docs/scripts/deploy_beget/nginx-flowimage-store.conf /etc/nginx/sites-available/flowimage-store
sudo ln -sf /etc/nginx/sites-available/flowimage-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Проверка: в браузере открой `http://flowimage.store` — должна открыться страница дашборда (пока без HTTPS).

---

## 3. SSL (HTTPS)

На сервере:

```bash
cd /root/contentzavod
sudo bash docs/scripts/deploy_beget/get-ssl-flowimage-store.sh
```

Или вручную:

```bash
sudo certbot --nginx -d flowimage.store -d www.flowimage.store
```

После этого дашборд будет доступен по **https://flowimage.store**.

---

## 4. Переменные окружения

В **`.env` на сервере** (в `/root/contentzavod`) добавь или измени:

```env
DASHBOARD_PUBLIC_URL=https://flowimage.store
```

Перезапусти дашборд (если бот и кнопка «Дашборд» должны открывать этот URL):

```bash
sudo systemctl restart analytics-dashboard
```

### Если на дашборде пустой раздел Generation (картинки/ссылки с flowimage.ru)

Дашборд читает данные из папок блока `grs_image_web` (generated, uploaded) на той же машине. Если дашборд и flowimage.ru развёрнуты из разных каталогов или репозиториев, укажи путь к блоку grs_image_web в `.env`:

```env
# Корень блока grs_image_web (здесь лежат generated/, uploaded/, users.json)
GRS_IMAGE_WEB_DIR=/root/contentzavod/blocks/grs_image_web
```

Либо задай папки по отдельности:

```env
GRS_IMAGE_WEB_GENERATED_DIR=/root/contentzavod/blocks/grs_image_web/generated
GRS_IMAGE_WEB_UPLOADED_DIR=/root/contentzavod/blocks/grs_image_web/uploaded
```

После изменения переменных: `sudo systemctl restart analytics-dashboard`.

**Проверка на сервере (если Generation пустой):** выполни по SSH и сверь пути:

```bash
# Из какого каталога запущен дашборд (WorkingDirectory)
sudo systemctl show analytics-dashboard -p WorkingDirectory --no-pager
# Есть ли данные в путях grs_image_web (подставь свой корень проекта)
ls -la /root/contentzavod/blocks/grs_image_web/generated 2>/dev/null || echo "Папка generated не найдена"
ls -la /root/contentzavod/blocks/grs_image_web/uploaded  2>/dev/null || echo "Папка uploaded не найдена"
# Откуда запущен grs-image-web
sudo systemctl show grs-image-web -p WorkingDirectory --no-pager
```

Если дашборд из другого каталога — задай `GRS_IMAGE_WEB_DIR` (или оба `*_DIR`) в `.env` дашборда и перезапусти `analytics-dashboard`.

---

## 5. Итог

| Что              | URL                    |
|------------------|------------------------|
| Дашборд          | https://flowimage.store |
| Конфиг Nginx     | `/etc/nginx/sites-available/flowimage-store` |
| Сервис           | `analytics-dashboard` (порт 8050) |

Продление SSL: certbot настраивает таймер сам (`certbot.timer`).
