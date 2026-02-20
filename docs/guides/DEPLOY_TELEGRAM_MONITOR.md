# Деплой мониторинга Telegram-канала на VPS

Мониторинг канала (например zakazyff): ловит новые сообщения с нужным заголовком и шлёт уведомления ботом в другой чат.

## Кратко

1. Проект уже на VPS (git clone или загрузка)
2. Заполнить `.env`
3. Один раз: `python -m blocks.telegram_chat_reader login` (интерактивно)
4. Запустить скрипт деплоя

## Шаг 1. Подключиться к VPS

```bash
ssh root@твой-сервер
```

С телефона: Termius, JuiceSSH и т.п.

## Шаг 2. Перейти в проект

```bash
cd /root/contentzavod   # или путь к проекту
```

Если проекта нет — `git clone` или загрузить архив.

## Шаг 3. Создать/отредактировать .env

```bash
nano .env
```

Добавить или проверить:

```env
# Telethon (my.telegram.org/apps)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef...

# Бот для отправки уведомлений
TELEGRAM_BOT_TOKEN=1234567890:ABC...

# Куда слать (chat_id: узнать у @userinfobot)
TELEGRAM_MONITOR_ALERT_CHAT_ID=123456789

# Канал для мониторинга
TELEGRAM_MONITOR_ENTITY=zakazyff

# Заголовок: если он есть в сообщении — отправить уведомление
TELEGRAM_MONITOR_HEADER=ЗАКАЗ
```

`TELEGRAM_MONITOR_HEADER` — подставь свой заголовок, которым помечаются нужные сообщения в чате.

## Шаг 4. Авторизация Telethon (один раз)

```bash
PYTHONPATH=/root/contentzavod /root/contentzavod/venv/bin/python -m blocks.telegram_chat_reader login
```

Ввести номер телефона (с кодом страны) и код из Telegram. Сессия сохранится в `storage/telegram_sessions/`.

## Шаг 5. Запуск скрипта деплоя

```bash
cd /root/contentzavod
PROJECT_DIR=/root/contentzavod SERVICE_USER=root bash docs/scripts/deploy_beget/setup_telegram_monitor.sh
```

Скрипт установит Telethon, настроит systemd и запустит монитор.

## Проверка

```bash
sudo systemctl status telegram-monitor
sudo journalctl -u telegram-monitor -f
```

В логах должно быть: `Мониторинг канала zakazyff, уведомления в ...`

## Ручная установка (без скрипта)

```bash
pip install telethon
sudo cp docs/scripts/deploy_beget/telegram-monitor.service.example /etc/systemd/system/telegram-monitor.service
# Отредактировать: User, WorkingDirectory, ExecStart (путь к проекту)
sudo systemctl daemon-reload && sudo systemctl enable telegram-monitor && sudo systemctl start telegram-monitor
```
