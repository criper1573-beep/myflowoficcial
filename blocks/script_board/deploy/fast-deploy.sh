#!/usr/bin/env bash
# Быстрая выкладка доски скриптов из GitHub Release.
# Сборку на сервере не делает. Данные storage и .env не затирает.
set -euo pipefail
umask 077

APP_DIR=${SCRIPT_BOARD_APP_DIR:-/root/contentzavod/blocks/script_board}
REPO_ROOT=${SCRIPT_BOARD_REPO_ROOT:-/root/contentzavod}
PREV_DIR=${SCRIPT_BOARD_PREV_DIR:-${APP_DIR}.previous}
BACKUP_ROOT=${SCRIPT_BOARD_BACKUP_ROOT:-/root/backups/script-board}
TOKEN_FILE=${SCRIPT_BOARD_GH_TOKEN_FILE:-/root/.config/flow/gh-token}
LOG=${SCRIPT_BOARD_DEPLOY_LOG:-/var/log/script-board-deploy.log}
SERVICE=${SCRIPT_BOARD_SERVICE:-script-board}
ASSETS_DIR=${SCRIPT_BOARD_ASSETS_DIR:-/var/www/script-flowcabinet/assets}
REPO=${SCRIPT_BOARD_REPO:-criper1573-beep/myflowoficcial}
VENV_PIP=${SCRIPT_BOARD_VENV_PIP:-/root/contentzavod/venv/bin/pip}
API_BASE=${GITHUB_API_URL:-https://api.github.com}
LOCK_FILE=${SCRIPT_BOARD_DEPLOY_LOCK:-/var/lock/script-board-deploy.lock}

PHASE=idle
STOPPED=0
TMP_ROOT=""
NETRC=""
STORAGE_EXTERNAL=0
STORAGE_DIR="${APP_DIR}/storage"
APP_PORT=8780

usage() {
  cat <<'EOF'
Использование:
  fast-deploy.sh                      последний релиз script-board-<sha7>
  fast-deploy.sh <tag|sha7>           конкретный тег или 7 символов коммита
  fast-deploy.sh --rollback           вернуть предыдущую папку кода

Данные доски и .env не перезаписываются. Лог: /var/log/script-board-deploy.log
EOF
}

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
}

on_exit() {
  if [[ "${PHASE}" == "swapped-away" && ! -d "$APP_DIR" && -d "$PREV_DIR" ]]; then
    mv "$PREV_DIR" "$APP_DIR" || true
    PHASE=idle
  fi
  if [[ -d "${APP_DIR}.incoming" ]]; then
    rm -rf "${APP_DIR}.incoming" || true
  fi
  if [[ "$STOPPED" == 1 && "${PHASE}" != "swapped-away" ]]; then
    systemctl restart "$SERVICE" || true
    STOPPED=0
  fi
  if [[ -n "$NETRC" && -f "$NETRC" ]]; then
    rm -f "$NETRC" || true
  fi
  if [[ -n "$TMP_ROOT" && -d "$TMP_ROOT" ]]; then
    rm -rf "$TMP_ROOT" || true
  fi
}

env_value() {
  local file="$1"
  local key="$2"
  local line=""
  [[ -f "$file" ]] || return 1
  line=$(grep -E "^[[:space:]]*${key}=" "$file" | tail -n 1 || true)
  [[ -n "$line" ]] || return 1
  line=${line#*=}
  line=${line%%#*}
  line=${line//$'\r'/}
  line=$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
  line=${line#\"}
  line=${line%\"}
  line=${line#\'}
  line=${line%\'}
  [[ -n "$line" ]] || return 1
  printf '%s' "$line"
}

read_runtime_var() {
  local key="$1"
  local raw=""
  local files=""
  local found=""
  local part=""
  local path=""
  local value=""
  raw=$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)
  if [[ "$raw" =~ (^|[[:space:]])${key}=([^[:space:]]+) ]]; then
    value="${BASH_REMATCH[2]}"
    value=${value#\"}
    value=${value%\"}
    value=${value#\'}
    value=${value%\'}
    printf '%s' "$value"
    return 0
  fi
  files=$(systemctl show "$SERVICE" -p EnvironmentFiles --value 2>/dev/null || true)
  local -a parts=()
  if [[ -n "$files" ]]; then
    # Пути без пробелов: systemd печатает их через пробел, хвост в скобках отбрасываем.
    read -r -a parts <<< "$files"
    for part in "${parts[@]}"; do
      [[ "$part" == "("* ]] && continue
      path="$part"
      if value=$(env_value "$path" "$key"); then
        found="$value"
      fi
    done
  fi
  if [[ -n "$found" ]]; then
    printf '%s' "$found"
    return 0
  fi
  if value=$(env_value "$REPO_ROOT/.env" "$key"); then
    printf '%s' "$value"
    return 0
  fi
  return 1
}

resolve_runtime() {
  local value=""
  APP_PORT=8780
  if value=$(read_runtime_var SCRIPT_BOARD_PORT); then
    APP_PORT=$value
  fi
  if [[ ! "$APP_PORT" =~ ^[0-9]+$ ]]; then
    log "некорректный SCRIPT_BOARD_PORT, оставляю 8780"
    APP_PORT=8780
  fi
  STORAGE_DIR="${APP_DIR}/storage"
  STORAGE_EXTERNAL=0
  if value=$(read_runtime_var SCRIPT_BOARD_STORAGE); then
    if [[ -n "$value" && "$value" != "${APP_DIR}/storage" ]]; then
      STORAGE_DIR=$value
      STORAGE_EXTERNAL=1
    fi
  fi
}

require_unit() {
  if ! systemctl cat "$SERVICE" >/dev/null 2>&1; then
    log "нет systemd-юнита ${SERVICE}"
    exit 1
  fi
}

require_pip() {
  if [[ ! -x "$VENV_PIP" ]]; then
    log "нет интерпретатора зависимостей: ${VENV_PIP}"
    exit 1
  fi
}

load_token() {
  local token=""
  local mode=""
  if [[ -n "$NETRC" && -f "$NETRC" ]]; then
    return 0
  fi
  if [[ ! -f "$TOKEN_FILE" ]]; then
    log "нет файла токена ${TOKEN_FILE}"
    exit 1
  fi
  token=$(tr -d '[:space:]' < "$TOKEN_FILE")
  token=${token#\"}
  token=${token%\"}
  if [[ -z "$token" ]]; then
    log "файл токена пустой"
    exit 1
  fi
  mode=$(stat -c '%a' "$TOKEN_FILE" 2>/dev/null || echo "")
  if [[ -n "$mode" && "$mode" != "600" && "$mode" != "400" ]]; then
    log "предупреждение: права ${TOKEN_FILE} сейчас ${mode}, нужны 600"
  fi
  local host="${API_BASE#https://}"
  host="${host#http://}"
  host="${host%%/*}"
  host="${host%%:*}"
  NETRC=$(mktemp)
  chmod 600 "$NETRC"
  printf 'machine %s login x-access-token password %s\n' "$host" "$token" > "$NETRC"
}

api_get() {
  local url="$1"
  local body=""
  if ! body=$(curl -fsSL --retry 3 --retry-delay 2 --connect-timeout 15 --max-time 120 \
    --netrc-file "$NETRC" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$url"); then
    log "GitHub API не ответил: ${url}"
    return 1
  fi
  printf '%s' "$body"
}

latest_tag() {
  local body=""
  body=$(api_get "${API_BASE}/repos/${REPO}/releases?per_page=100") || return 1
  printf '%s' "$body" | python3 -c '
import json, re, sys
pattern = re.compile(r"^script-board-[0-9a-f]{7}$")
releases = json.load(sys.stdin)
if not isinstance(releases, list):
    sys.exit(1)
for rel in releases:
    if not isinstance(rel, dict) or rel.get("draft"):
        continue
    tag = rel.get("tag_name") or ""
    if pattern.match(tag):
        print(tag)
        sys.exit(0)
sys.exit(1)
'
}

download_asset() {
  local url="$1"
  local dest="$2"
  local hdr=""
  local code=""
  local loc=""
  hdr=$(mktemp)
  code=$(curl -sS --connect-timeout 15 --max-time 180 \
    -D "$hdr" -o /dev/null -w '%{http_code}' \
    --netrc-file "$NETRC" \
    -H "Accept: application/octet-stream" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$url" || true)
  if [[ "$code" == "200" ]]; then
    rm -f "$hdr"
    curl -fsSL --retry 3 --retry-delay 2 --connect-timeout 15 --max-time 180 \
      --netrc-file "$NETRC" \
      -H "Accept: application/octet-stream" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      -o "$dest" \
      "$url" || return 1
    return 0
  fi
  loc=$(awk 'tolower($1) ~ /^location:/ { print $2 }' "$hdr" | tr -d '\r' | tail -n 1)
  rm -f "$hdr"
  if [[ "$code" != "301" && "$code" != "302" && "$code" != "307" && "$code" != "308" ]]; then
    log "не скачался файл, HTTP ${code}"
    return 1
  fi
  if [[ "$loc" != http://* && "$loc" != https://* ]]; then
    log "не скачался файл, нет адреса перенаправления"
    return 1
  fi
  curl -fsSL --retry 3 --retry-delay 2 --connect-timeout 15 --max-time 180 -o "$dest" "$loc" || return 1
}

fetch_release() {
  local tag="$1"
  local dest="$2"
  local meta=""
  local archive_name="${tag}.tar.gz"
  local checksum_name="${tag}.tar.gz.sha256"
  meta=$(api_get "${API_BASE}/repos/${REPO}/releases/tags/${tag}") || return 1
  local urls=""
  if ! urls=$(printf '%s' "$meta" | python3 -c '
import json, sys
rel = json.load(sys.stdin)
need = sys.argv[1:]
by = {}
for asset in rel.get("assets") or []:
    name = asset.get("name")
    url = asset.get("url")
    if name and url:
        by[name] = url
missing = [name for name in need if name not in by]
if missing:
    sys.stderr.write("в релизе нет: " + ", ".join(missing) + "\n")
    sys.exit(1)
for name in need:
    print(by[name])
' "$archive_name" "$checksum_name"); then
    log "в релизе ${tag} нет архива или sha256"
    return 1
  fi
  local archive_url=""
  local checksum_url=""
  archive_url=$(printf '%s\n' "$urls" | sed -n '1p')
  checksum_url=$(printf '%s\n' "$urls" | sed -n '2p')
  download_asset "$checksum_url" "${dest}/${checksum_name}" || return 1
  download_asset "$archive_url" "${dest}/${archive_name}" || return 1
  if ! (cd "$dest" && sha256sum -c "$checksum_name"); then
    log "sha256 не совпал, каталог приложения не тронут"
    return 1
  fi
  log "sha256 совпал: ${archive_name}"
  python3 - "$dest/$archive_name" "$dest" <<'PY' || return 1
import sys
import tarfile

archive, dest = sys.argv[1], sys.argv[2]
with tarfile.open(archive, "r:gz") as tar:
    members = tar.getmembers()
    for member in members:
        parts = [part for part in member.name.split("/") if part not in ("", ".")]
        if (
            member.name.startswith("/")
            or member.name.startswith("\\")
            or ".." in parts
            or not parts
            or parts[0] != "script_board"
            or member.issym()
            or member.islnk()
        ):
            raise SystemExit("отклонён небезопасный архив")
    if sys.version_info >= (3, 12):
        tar.extractall(dest, members=members, filter="data")
    else:
        tar.extractall(dest, members=members)
PY
  if [[ ! -d "${dest}/script_board" ]]; then
    log "в архиве нет каталога script_board"
    return 1
  fi
}

sanitize_stage() {
  local stage="$1"
  rm -rf "${stage}/storage" "${stage}/.env" "${stage}/frontend/node_modules" "${stage}/__pycache__" || return 1
  find "$stage" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
  if [[ ! -f "${stage}/api.py" || ! -f "${stage}/dist/index.html" || ! -d "${stage}/dist/assets" ]]; then
    log "в поставке нет api.py или собранного dist"
    return 1
  fi
  if [[ ! -f "${stage}/requirements.txt" ]]; then
    log "в поставке нет requirements.txt"
    return 1
  fi
}

stop_service() {
  systemctl stop "$SERVICE" || return 1
  STOPPED=1
  local attempt=0
  while [[ "$attempt" -lt 15 ]]; do
    attempt=$((attempt + 1))
    if ! systemctl is-active --quiet "$SERVICE"; then
      log "сервис ${SERVICE} остановлен"
      return 0
    fi
    sleep 1
  done
  log "сервис ${SERVICE} не остановился"
  return 1
}

backup_data() {
  local tag="$1"
  local stamp=""
  local backup=""
  stamp=$(date '+%Y%m%d-%H%M%S')
  backup="${BACKUP_ROOT}/${stamp}-before-${tag}"
  mkdir -p "$backup" || return 1
  chmod 700 "$BACKUP_ROOT" "$backup" || true
  if [[ -d "$STORAGE_DIR" ]]; then
    cp -a "$STORAGE_DIR" "${backup}/storage" || return 1
    log "бэкап данных: ${backup}/storage"
  else
    log "каталог данных ещё не создан: ${STORAGE_DIR}"
  fi
  if [[ -f "${REPO_ROOT}/.env" ]]; then
    cp -a "${REPO_ROOT}/.env" "${backup}/repo.env" || return 1
    chmod 600 "${backup}/repo.env" || true
  fi
  if [[ -f "${APP_DIR}/.env" ]]; then
    cp -a "${APP_DIR}/.env" "${backup}/block.env" || return 1
    chmod 600 "${backup}/block.env" || true
  fi
  log "бэкап: ${backup}"
}

attach_live_data() {
  local incoming="$1"
  rm -rf "${incoming}/storage" || return 1
  rm -f "${incoming}/.env" || return 1
  if [[ "$STORAGE_EXTERNAL" == 1 ]]; then
    mkdir -p "${incoming}/storage" || return 1
    log "данные остаются во внешнем каталоге ${STORAGE_DIR}"
  elif [[ -d "${APP_DIR}/storage" ]]; then
    cp -a "${APP_DIR}/storage" "${incoming}/storage" || return 1
  else
    mkdir -p "${incoming}/storage" || return 1
  fi
  if [[ -f "${APP_DIR}/.env" ]]; then
    cp -a "${APP_DIR}/.env" "${incoming}/.env" || return 1
  fi
}

replace_with_stage() {
  local stage="$1"
  local incoming="${APP_DIR}.incoming"
  rm -rf "$incoming" || return 1
  cp -a "$stage" "$incoming" || return 1
  attach_live_data "$incoming" || return 1
  rm -rf "$PREV_DIR" || return 1
  if [[ -d "$APP_DIR" ]]; then
    mv "$APP_DIR" "$PREV_DIR" || return 1
    PHASE=swapped-away
  fi
  mv "$incoming" "$APP_DIR" || return 1
  PHASE=live
  log "папка обновлена, предыдущая: ${PREV_DIR}"
}

sync_assets() {
  local src="${APP_DIR}/dist/assets"
  if [[ ! -d "$src" ]]; then
    log "нет каталога ассетов ${src}"
    return 1
  fi
  mkdir -p "$ASSETS_DIR" || return 1
  if command -v rsync >/dev/null 2>&1; then
    rsync -a "${src}/" "${ASSETS_DIR}/" || return 1
  else
    cp -a "${src}/." "${ASSETS_DIR}/" || return 1
  fi
  log "ассеты дописаны в ${ASSETS_DIR}"
}

install_python_deps() {
  "$VENV_PIP" install --disable-pip-version-check --no-input -r "${APP_DIR}/requirements.txt"
}

wait_health() {
  local code="000"
  local attempt=0
  while [[ "$attempt" -lt 15 ]]; do
    attempt=$((attempt + 1))
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${APP_PORT}/" || true)
    if [[ "$code" == "200" || "$code" == "401" ]]; then
      log "проверка http://127.0.0.1:${APP_PORT}/ -> ${code}"
      return 0
    fi
    sleep 1
  done
  log "проверка не прошла, последний код ${code}"
  journalctl -u "$SERVICE" -n 40 --no-pager || true
  return 1
}

start_service() {
  systemctl restart "$SERVICE" || return 1
  STOPPED=0
}

revert_failed_install() {
  local hold=""
  local failed=""
  if [[ ! -d "$PREV_DIR" ]]; then
    log "откат невозможен: нет ${PREV_DIR}"
    return 1
  fi
  hold=$(mktemp -d) || return 1
  if [[ "$STORAGE_EXTERNAL" != 1 && -d "${APP_DIR}/storage" ]]; then
    cp -a "${APP_DIR}/storage" "${hold}/storage" || return 1
  fi
  if [[ -f "${APP_DIR}/.env" ]]; then
    cp -a "${APP_DIR}/.env" "${hold}/block.env" || return 1
  fi
  failed="${APP_DIR}.failed"
  rm -rf "$failed" || return 1
  mv "$APP_DIR" "$failed" || return 1
  PHASE=swapped-away
  mv "$PREV_DIR" "$APP_DIR" || return 1
  PHASE=live
  if [[ "$STORAGE_EXTERNAL" != 1 ]]; then
    rm -rf "${APP_DIR}/storage" || return 1
    if [[ -d "${hold}/storage" ]]; then
      cp -a "${hold}/storage" "${APP_DIR}/storage" || return 1
    else
      mkdir -p "${APP_DIR}/storage" || return 1
    fi
  fi
  rm -f "${APP_DIR}/.env" || return 1
  if [[ -f "${hold}/block.env" ]]; then
    cp -a "${hold}/block.env" "${APP_DIR}/.env" || return 1
  fi
  rm -rf "$hold" "$failed" || return 1
  log "код возвращён из предыдущей папки, данные оставлены текущие"
}

rollback_failed_release() {
  systemctl stop "$SERVICE" || true
  STOPPED=1
  if ! revert_failed_install; then
    return 1
  fi
  sync_assets || true
  start_service
  if wait_health; then
    log "после отката сервис отвечает"
    return 0
  fi
  log "после отката сервис не ответил"
  return 1
}

activate_stage() {
  local stage="$1"
  replace_with_stage "$stage" || exit 1
  if ! install_python_deps; then
    log "зависимости не установились, откат"
    rollback_failed_release || true
    exit 1
  fi
  if ! sync_assets; then
    log "ассеты не скопировались, откат"
    rollback_failed_release || true
    exit 1
  fi
  if ! start_service; then
    log "сервис не запустился, откат"
    rollback_failed_release || true
    exit 1
  fi
  if ! wait_health; then
    log "проверка не прошла, откат"
    rollback_failed_release || true
    exit 1
  fi
  log "выкладка успешна: ${APP_DIR}"
}

do_rollback() {
  local tag="rollback"
  local stage=""
  if [[ ! -d "$PREV_DIR" ]]; then
    log "предыдущей версии нет: ${PREV_DIR}"
    exit 1
  fi
  if [[ -f "${PREV_DIR}/RELEASE" ]]; then
    tag="rollback"
  fi
  require_unit
  require_pip
  resolve_runtime
  if [[ -z "${TMP_ROOT}" || ! -d "${TMP_ROOT}" ]]; then
    TMP_ROOT=$(mktemp -d)
  fi
  stop_service || exit 1
  backup_data "$tag" || exit 1
  stage="${TMP_ROOT}/rollback-stage"
  cp -a "$PREV_DIR" "$stage" || exit 1
  sanitize_stage "$stage" || exit 1
  activate_stage "$stage"
  log "откат выполнен"
}

do_deploy() {
  local tag="$1"
  local stage=""
  require_unit
  require_pip
  resolve_runtime
  load_token
  if [[ -z "${TMP_ROOT}" || ! -d "${TMP_ROOT}" ]]; then
    TMP_ROOT=$(mktemp -d)
  fi
  log "скачиваю ${tag}"
  fetch_release "$tag" "$TMP_ROOT" || exit 1
  stage="${TMP_ROOT}/script_board"
  sanitize_stage "$stage" || exit 1
  stop_service || exit 1
  backup_data "$tag" || exit 1
  activate_stage "$stage"
  log "релиз ${tag} установлен"
}

main() {
  local mode="latest"
  local tag=""
  case "${1:-}" in
    -h|--help)
      usage
      exit 0
      ;;
    "")
      mode="latest"
      ;;
    --rollback)
      mode="rollback"
      ;;
    --*)
      usage >&2
      exit 2
      ;;
    *)
      if [[ $# -ne 1 ]]; then
        usage >&2
        exit 2
      fi
      mode="tag"
      tag="$1"
      if [[ "$tag" =~ ^[0-9a-f]{7}$ ]]; then
        tag="script-board-${tag}"
      elif [[ ! "$tag" =~ ^script-board-[0-9a-f]{7}$ ]]; then
        log "тег должен быть script-board-<sha7> или 7 шестнадцатеричных символов"
        exit 2
      fi
      ;;
  esac
  if [[ $# -gt 1 ]]; then
    usage >&2
    exit 2
  fi

  mkdir -p "$(dirname "$LOG")" "$(dirname "$LOCK_FILE")" "$BACKUP_ROOT"
  touch "$LOG"
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log "уже идёт другая выкладка"
    exit 1
  fi
  exec > >(tee -a "$LOG") 2>&1
  trap on_exit EXIT

  log "старт ($mode${tag:+ $tag})"
  if [[ "$mode" == "rollback" ]]; then
    do_rollback
    exit 0
  fi
  if [[ "$mode" == "latest" ]]; then
    load_token
    tag=$(latest_tag) || {
      log "не нашёл релиз с тегом script-board-<sha7>"
      exit 1
    }
    log "последний релиз: ${tag}"
  fi
  do_deploy "$tag"
}

main "$@"
