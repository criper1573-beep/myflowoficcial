Скрипты для деплоя КонтентЗавод на Beget VPS.
Подробная инструкция: docs/guides/DEPLOY_FULL_PROJECT_BEGET.md

Файлы:
  setup_server.sh     — запустить на VPS после клонирования проекта (установка venv, зависимости, storage)
  update.sh           — на сервере после каждого git push: git pull, pip install, перезапуск сервиса
  env.server.example  — пример .env для сервера (скопировать в .env и заполнить)
  nginx.conf.example  — пример конфига Nginx (подставить домен и путь)
  analytics-dashboard.service.example — пример юнита systemd (подставить пользователя и путь)
