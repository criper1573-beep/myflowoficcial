#!/bin/bash
# Запустить на сервере ПОСЛЕ того, как у flowimage.ru в DNS только одна A-запись: 85.198.66.62
# (удалить вторую A-запись 87.236.16.23, иначе certbot будет получать 500 с другого сервера)
# Запуск: sudo bash docs/scripts/deploy_beget/get-ssl-flowimage.sh

set -e
certbot --nginx -d flowimage.ru -d www.flowimage.ru --non-interactive --agree-tos --register-unsafely-without-email
echo "SSL установлен. Проверка: https://flowimage.ru"
