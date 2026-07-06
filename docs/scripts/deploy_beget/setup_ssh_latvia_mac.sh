#!/usr/bin/env bash
# Настройка SSH к латвийскому VPS с нового Mac (или Linux).
# Запуск: bash docs/scripts/deploy_beget/setup_ssh_latvia_mac.sh

set -euo pipefail

HOST="194.113.209.152"
USER="root"
ALIAS="contentzavod-lv"
KEY="$HOME/.ssh/id_ed25519_contentzavod_lv"
CONFIG="$HOME/.ssh/config"

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY" ]; then
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "contentzavod-latvia-mac"
  echo "Создан ключ: $KEY"
else
  echo "Ключ уже есть: $KEY"
fi

PUB=$(cat "${KEY}.pub")
BLOCK_START="# contentzavod-latvia"
BLOCK_END="# /contentzavod-latvia"

if [ -f "$CONFIG" ] && grep -q "$BLOCK_START" "$CONFIG" 2>/dev/null; then
  echo "Запись $ALIAS уже есть в $CONFIG"
else
  cat >> "$CONFIG" <<EOF

$BLOCK_START
Host $ALIAS
    HostName $HOST
    User $USER
    IdentityFile $KEY
    IdentitiesOnly yes
$BLOCK_END
EOF
  chmod 600 "$CONFIG"
  echo "Добавлен Host $ALIAS в $CONFIG"
fi

echo ""
echo "=== Публичный ключ (добавь на сервер) ==="
echo "$PUB"
echo ""
echo "Если пароль не подходит, на старом Mac вход был по ключу."
echo "Варианты:"
echo "  1) Панель Beget → VPS → VNC/консоль → выполни:"
echo "     mkdir -p /root/.ssh && echo '$PUB' >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys"
echo "  2) Скопировать ~/.ssh/id_ed25519(.pub) со старого Mac и положить в ~/.ssh на новом."
echo ""
echo "Проверка: ssh $ALIAS"
