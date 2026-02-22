# Снятие приостановки оркестратора на сервере: удаляет storage/orchestrator_kz_paused и перезапускает сервис.
# Запуск: .\docs\scripts\deploy_beget\resume_orchestrator_on_server.ps1
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
    Write-Host "Не задан SERVER_SSH_PASSWORD или DEPLOY_SSH_PASSWORD в .env."
    exit 1
}

Write-Host "Удаляю файл приостановки на сервере..."
& $plink -ssh "${user}@${hostAddr}" -pw $pw -batch "cd $projectDir && ./venv/bin/python -m blocks.autopost_zen --resume-orchestrator"
Write-Host "Перезапускаю orchestrator-kz..."
& $plink -ssh "${user}@${hostAddr}" -pw $pw -batch "sudo systemctl restart orchestrator-kz"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Готово. Оркестратор снова работает по расписанию."
