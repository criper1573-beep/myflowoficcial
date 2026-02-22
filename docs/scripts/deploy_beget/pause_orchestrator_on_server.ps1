# Приостановка оркестратора на сервере: создаёт storage/orchestrator_kz_paused и перезапускает сервис.
# После перезапуска оркестратор при старте увидит файл и сразу выйдет (без генерации и расписания).
# Запуск: .\docs\scripts\deploy_beget\pause_orchestrator_on_server.ps1
# Требуется: на сервере уже должен быть подтянут код с --pause-orchestrator (git pull). В .env: SERVER_HOST, SERVER_USER, SERVER_SSH_PASSWORD (или DEPLOY_SSH_PASSWORD).
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..\..\..")).Path
$envPath = Join-Path $projectRoot ".env"
if (Test-Path $envPath) {
    Get-Content $envPath -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z0-9_]+)\s*=\s*(.*)$' -and $matches[1] -notmatch '^#') {
            $v = $matches[2].Trim()
            if ($v -match '^["''](.+)["'']\s*$') { $v = $matches[1] }
            [Environment]::SetEnvironmentVariable($matches[1], $v, 'Process')
        }
    }
}
$hostAddr = if ($env:SERVER_HOST) { $env:SERVER_HOST } else { "85.198.66.62" }
$user = if ($env:SERVER_USER) { $env:SERVER_USER } else { "root" }
$pw = $env:SERVER_SSH_PASSWORD; if (-not $pw) { $pw = $env:DEPLOY_SSH_PASSWORD }
$projectDir = if ($env:SERVER_PROJECT_PATH) { $env:SERVER_PROJECT_PATH } else { "/root/contentzavod" }
$plink = "plink"; if (-not (Get-Command plink -ErrorAction SilentlyContinue)) { $plink = "C:\Program Files\PuTTY\plink.exe" }

if (-not $pw) {
    Write-Host "Не задан SERVER_SSH_PASSWORD или DEPLOY_SSH_PASSWORD в .env. Заполни .env и запусти снова."
    exit 1
}

Write-Host "Подтягиваю код на сервере (git pull)..."
& $plink -ssh "${user}@${hostAddr}" -pw $pw -batch "cd $projectDir && git pull origin main"
if ($LASTEXITCODE -ne 0) { Write-Host "git pull завершился с кодом $LASTEXITCODE"; exit $LASTEXITCODE }

Write-Host "Создаю файл приостановки на сервере (--pause-orchestrator)..."
& $plink -ssh "${user}@${hostAddr}" -pw $pw -batch "cd $projectDir && ./venv/bin/python -m blocks.autopost_zen --pause-orchestrator"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка. Убедись, что новый код (с --pause-orchestrator) запушен и на сервере выполнен git pull."
    exit $LASTEXITCODE
}

Write-Host "Перезапускаю orchestrator-kz..."
& $plink -ssh "${user}@${hostAddr}" -pw $pw -batch "sudo systemctl restart orchestrator-kz"
if ($LASTEXITCODE -ne 0) { Write-Host "systemctl restart завершился с кодом $LASTEXITCODE"; exit $LASTEXITCODE }

Write-Host "Готово. Оркестратор на сервере приостановлен: при каждом старте будет сразу выходить без генерации статей."
Write-Host "Чтобы снова включить: запусти resume_orchestrator_on_server.ps1 или на сервере удали storage/orchestrator_kz_paused и выполни sudo systemctl start orchestrator-kz."
