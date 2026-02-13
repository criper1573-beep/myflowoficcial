#!/bin/bash
# Запустить на сервере ПОСЛЕ того, как flowimage.store в DNS указывает на IP сервера (85.198.66.62).
# Запуск: sudo bash docs/scripts/deploy_beget/get-ssl-flowimage-store.sh

set -e
certbot --nginx -d flowimage.store -d www.flowimage.store --non-interactive --agree-tos --register-unsafely-without-email
echo "SSL установлен. Дашборд: https://flowimage.store"
