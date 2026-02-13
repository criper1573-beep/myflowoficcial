#!/bin/bash
# Привязать /root/contentzavod к репозиторию myflowoficcial и подтянуть последний код.
# Запуск на сервере: sudo bash /root/contentzavod/docs/scripts/deploy_beget/fix_server_repo_and_pull.sh
# Или: cd /root/contentzavod && bash docs/scripts/deploy_beget/fix_server_repo_and_pull.sh

set -e
REPO_URL="https://github.com/criper1573-beep/myflowoficcial.git"
DIR="${1:-/root/contentzavod}"

cd "$DIR"
echo "Каталог: $(pwd)"

if [ ! -d .git ]; then
  echo "В каталоге нет .git (развёрнуто из zip). Инициализирую репозиторий и подтягиваю код..."
  cp .env .env.bak 2>/dev/null || true
  git init
  git remote add origin "$REPO_URL"
  git fetch origin main
  git reset --hard FETCH_HEAD
  git branch -M main
  git branch -u origin/main main 2>/dev/null || true
  echo "Код обновлён. Перезапуск сервисов..."
  systemctl restart analytics-dashboard 2>/dev/null || sudo systemctl restart analytics-dashboard
  systemctl restart grs-image-web 2>/dev/null || sudo systemctl restart grs-image-web
  echo "Готово. Проверь: https://flowimage.store"
  exit 0
fi

echo "Текущий remote:"
git remote -v
echo "Текущий коммит:"
git log -1 --oneline 2>/dev/null || echo "(ещё не было коммитов)"

CURRENT_URL="$(git remote get-url origin 2>/dev/null)" || true
if [ "$CURRENT_URL" != "$REPO_URL" ]; then
  echo "Привязываю origin к $REPO_URL"
  git remote remove origin 2>/dev/null || true
  git remote add origin "$REPO_URL"
fi

echo "Подтягиваю main..."
git fetch origin main
git branch -M main 2>/dev/null || true
git reset --hard origin/main 2>/dev/null || git pull origin main

echo "После pull коммит:"
git log -1 --oneline
echo "Перезапуск analytics-dashboard..."
systemctl restart analytics-dashboard 2>/dev/null || sudo systemctl restart analytics-dashboard
echo "Готово. Проверь: https://flowimage.store"