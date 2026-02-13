# Дашборд аналитики на домене flowimage.store

Краткая инструкция: как вывести дашборд (порт 8050) на домен **flowimage.store** с HTTPS.

**Предполагается:** VPS уже настроен (проект в `/root/contentzavod`, сервис `analytics-dashboard` запущен), дашборд открывается по IP `http://85.198.66.62`.

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

---

## 5. Итог

| Что              | URL                    |
|------------------|------------------------|
| Дашборд          | https://flowimage.store |
| Конфиг Nginx     | `/etc/nginx/sites-available/flowimage-store` |
| Сервис           | `analytics-dashboard` (порт 8050) |

Продление SSL: certbot настраивает таймер сам (`certbot.timer`).
