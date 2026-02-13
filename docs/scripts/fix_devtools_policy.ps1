# Сброс политики "Режим разработчика отключён" для Chrome и Яндекс.Браузера
# Причина: Windows (или ПО) прописывает в реестр DeveloperToolsDisabled.
# Edge не затронут — у него свои ключи политик.

$ErrorActionPreference = 'Stop'

function Set-PolicyValue {
    param([string]$Root, [string]$SubKey, [string]$Name, [int]$Value)
    $path = "$Root\$SubKey"
    if (-not (Test-Path "Registry::$path")) {
        New-Item -Path "Registry::$path" -Force | Out-Null
    }
    Set-ItemProperty -Path "Registry::$path" -Name $Name -Value $Value -Type DWord -Force
    Write-Host "OK: $path -> $Name = $Value"
}

function Remove-PolicyValue {
    param([string]$Root, [string]$SubKey, [string]$Name)
    $path = "$Root\$SubKey"
    if (Test-Path "Registry::$path") {
        Remove-ItemProperty -Path "Registry::$path" -Name $Name -ErrorAction SilentlyContinue
        Write-Host "OK: удалён параметр $Name в $path"
    }
}

# Текущий пользователь (не требует прав администратора)
$roots = @('HKCU:\SOFTWARE\Policies')
# Системные политики (требуют прав администратора)
$rootsLM = @('HKLM:\SOFTWARE\Policies')

$chromeKey = 'Google\Chrome'
$yandexKey = 'YandexBrowser'

Write-Host "=== Сброс политики DevTools (Chrome и Яндекс.Браузер) ===" -ForegroundColor Cyan

foreach ($r in $roots) {
    if (Test-Path "Registry::$r\$chromeKey") {
        Set-PolicyValue -Root $r -SubKey $chromeKey -Name 'DeveloperToolsDisabled' -Value 0
    }
    if (Test-Path "Registry::$r\$yandexKey") {
        Set-PolicyValue -Root $r -SubKey $yandexKey -Name 'DeveloperToolsDisabled' -Value 0
    }
}

# HKLM — только если скрипт запущен с правами администратора
foreach ($r in $rootsLM) {
    if (-not (Test-Path "Registry::$r")) { continue }
    if (Test-Path "Registry::$r\$chromeKey") {
        try {
            Set-PolicyValue -Root $r -SubKey $chromeKey -Name 'DeveloperToolsDisabled' -Value 0
        } catch {
            Write-Host "HKLM Chrome: нужны права администратора. Запустите скрипт от имени администратора." -ForegroundColor Yellow
        }
    }
    if (Test-Path "Registry::$r\$yandexKey") {
        try {
            Set-PolicyValue -Root $r -SubKey $yandexKey -Name 'DeveloperToolsDisabled' -Value 0
        } catch {
            Write-Host "HKLM Yandex: нужны права администратора." -ForegroundColor Yellow
        }
    }
}

Write-Host "`nГотово. Закройте Chrome и Яндекс.Браузер и откройте снова. Режим разработчика (F12) должен заработать." -ForegroundColor Green
Write-Host "Если нет — откройте chrome://policy (или browser://policy в Яндексе) и проверьте, откуда применяется политика." -ForegroundColor Gray
