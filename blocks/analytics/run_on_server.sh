#!/bin/bash
# Запуск дашборда на сервере (Beget/VPS). Запускать из КОРНЯ проекта (где лежит папка blocks/).
# Использование: ./blocks/analytics/run_on_server.sh
# Или: bash blocks/analytics/run_on_server.sh

set -e
cd "$(dirname "$0")/../.."
export PYTHONPATH=.
exec uvicorn blocks.analytics.api:app --host 127.0.0.1 --port 8050
