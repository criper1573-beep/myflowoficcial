# Run from project root: .\docs\scripts\deploy_beget\make_zip_and_upload.ps1
# Creates zip and uploads to VPS. Requires: plink, pscp, host key accepted.
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$zipPath = Join-Path $env:USERPROFILE "Desktop\contentzavod.zip"
$tempDir = Join-Path $env:USERPROFILE "Desktop\contentzavod_temp"

# Clean
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy needed dirs (exclude heavy/unnecessary)
$exclude = @(".git", "venv", ".cursor", "__pycache__", ".browser_profile_verify", ".browser_profile_capture")
Get-ChildItem -LiteralPath $projectRoot -Directory | Where-Object { $_.Name -notin $exclude } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $tempDir $_.Name) -Recurse -Force
}
Get-ChildItem -LiteralPath $projectRoot -File | Where-Object { $_.Name -ne ".env" } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $tempDir $_.Name) -Force
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
Remove-Item $tempDir -Recurse -Force
Write-Host "Zip created: $zipPath"

# Upload (set these or pass as params)
$hostKey = "SHA256:xG6ieATkmchxohmu4h6+YtrJFdGEx+Xw5kmN35mQ030"
$server = "root@85.198.66.62"
$pw = $env:DEPLOY_SSH_PASSWORD
if (-not $pw) { Write-Host "Set DEPLOY_SSH_PASSWORD and run pscp manually, or pass password."; exit 0 }
& "C:\Program Files\PuTTY\pscp.exe" -pw $pw -hostkey $hostKey $zipPath "${server}:/root/contentzavod.zip"
Write-Host "Upload done."
