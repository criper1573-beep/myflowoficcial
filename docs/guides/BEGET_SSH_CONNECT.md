# Подключение к VPS Beget по SSH

Инструкция для Mac и Windows. Сохрани этот файл у себя на компьютере.

---

## Твои серверы

| Сервер | IP | Логин | Для чего |
|--------|-----|-------|----------|
| **Латвия** (основной сейчас) | `194.113.209.152` | `root` | kit20.ru, сайты жены, ERP |
| **РФ** | `85.198.66.62` | `root` | КонтентЗавод `/root/contentzavod` |

Пароли **разные** у каждого VPS. Не путай.

---

## Где взять или сбросить пароль

1. Зайди в [cp.beget.com](https://cp.beget.com)
2. Раздел **Облако** / **VPS** / **Серверы**
3. Выбери нужный сервер (по IP)
4. **Доступ** → **Смена root-пароля** / **Сброс пароля**
5. Beget покажет **новый пароль** — скопируй сразу (потом посмотреть нельзя)

Альтернатива: **VNC-консоль** в панели Beget — терминал в браузере, вход как `root` с паролем root.

Пароль от входа в панель Beget ≠ пароль `root` на VPS.

---

## Mac — быстрое подключение

1. Открой **Терминал** (Программы → Утилиты → Терминал)
2. Введи:

```bash
ssh root@194.113.209.152
```

(для РФ-сервера: `ssh root@85.198.66.62`)

3. При первом подключении напиши `yes` и Enter
4. Введи пароль root (символы не отображаются — это нормально)
5. Успех: строка вида `root@qabulrwxgs:~#`

---

## Mac — удобный алиас (один раз настроить)

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Ключ (если ещё нет)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_beget_lv -N "" -C "beget-latvia"

# Запись в config
cat >> ~/.ssh/config << 'EOF'

# Beget Latvia (kit20.ru)
Host beget-lv
    HostName 194.113.209.152
    User root
    IdentityFile ~/.ssh/id_ed25519_beget_lv
    IdentitiesOnly yes

# Beget RF (КонтентЗавод)
Host beget-rf
    HostName 85.198.66.62
    User root
    IdentityFile ~/.ssh/id_ed25519_beget_lv
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
```

Дальше подключение одной командой:

```bash
ssh beget-lv    # Латвия
ssh beget-rf    # РФ
```

Если вход только по паролю (без ключа на сервере):

```bash
ssh root@194.113.209.152
```

### Добавить ключ на сервер (чтобы не вводить пароль)

Скопируй публичный ключ:

```bash
cat ~/.ssh/id_ed25519_beget_lv.pub
```

На сервере (через пароль или VNC в панели Beget):

```bash
mkdir -p ~/.ssh
echo 'ВСТАВЬ_СЮДА_СТРОКУ_ИЗ_.pub' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## Windows

### Вариант А — PowerShell / Windows Terminal

```powershell
ssh root@194.113.209.152
```

(нужен OpenSSH: Параметры → Приложения → Дополнительные компоненты → OpenSSH Client)

### Вариант Б — PuTTY

1. Скачай [PuTTY](https://www.putty.org/)
2. Host: `194.113.209.152`, Port: `22`, Type: SSH
3. Open → логин `root`, пароль root

Для скриптов деплоя КонтентЗавода используется **plink** (идёт с PuTTY).

---

## Полезные пути после входа

### Латвия (`194.113.209.152`)

| Что | Путь |
|-----|------|
| Сайт kit20.ru | `/var/www/kit20` |
| Правила деплоя kit20 | `/var/www/kit20/DEPLOY_RULES.md` |
| Перезапуск сайта | `sudo systemctl restart kit20` |
| Логи сайта | `journalctl -u kit20 -n 50 --no-pager` |

### РФ (`85.198.66.62`)

| Что | Путь |
|-----|------|
| КонтентЗавод | `/root/contentzavod` |
| Перезапуск оркестратора | `sudo systemctl restart orchestrator-kz` |
| Дашборд аналитики | `sudo systemctl restart analytics-dashboard` |

---

## Проверка, что сервер доступен

**Mac / Linux:**

```bash
nc -zv 194.113.209.152 22
```

`succeeded` — порт открыт, можно подключаться.

---

## Если не подключается

| Симптом | Что сделать |
|---------|-------------|
| `Permission denied` | Неверный пароль → сбросить в панели Beget |
| Таймаут / висит | Проверить IP, файрвол Beget, раздел «Сеть» / «Доступ» |
| `Connection reset` | Подождать 5–10 мин (fail2ban после неудачных попыток) |
| Забыл пароль | Панель Beget → VPS → сброс root-пароля |

Поддержка Beget: support@beget.com

---

## Где хранить пароли у себя

| Где | Что |
|-----|-----|
| `.env` в корне КонтентЗавода | `SERVER_LV_HOST`, `SERVER_LV_SSH_PASSWORD`, `SERVER_RF_HOST`… |
| `kit20-oauth.env` в репо kit20 | пароль для деплоя kit20 |
| Менеджер паролей / заметки | резервная копия |

**Не отправляй пароли в чат и не коммить в git.**

---

## Ссылки в проекте

- Полный деплой КонтентЗавод: `docs/guides/DEPLOY_FULL_PROJECT_BEGET.md`
- Деплой kit20 (на сервере): `/var/www/kit20/DEPLOY_RULES.md`
- Ключи и переменные: `docs/rules/KEYS_AND_TOKENS.md`
- Пример `.env`: `docs/config/.env.example`

---

*Обновлено: 2026-07-13*
