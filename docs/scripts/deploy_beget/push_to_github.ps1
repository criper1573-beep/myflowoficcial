# Быстрый пуш изменений в GitHub (ContentZavod / myflowoficcial).
# Запуск из корня проекта: .\docs\scripts\deploy_beget\push_to_github.ps1
# Или из корня: powershell -File docs\scripts\deploy_beget\push_to_github.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path (Split-Path $PSScriptRoot))
Set-Location $root

$msg = $args -join " "
if (-not $msg) { $msg = "Update" }

git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "Нет изменений для коммита."
    exit 0
}
git commit -m "$msg"
git push origin main
Write-Host "Пуш в origin/main выполнен."
