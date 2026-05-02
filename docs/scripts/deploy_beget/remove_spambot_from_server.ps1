# One-time cleanup: stop processes, remove systemd units, delete blocks/spambot on VPS, patch watchdog, restart watchdog.
# Run: powershell -File docs/scripts/deploy_beget/remove_spambot_from_server.ps1
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
$plink = "plink"; if (-not (Get-Command plink -ErrorAction SilentlyContinue)) { $plink = "C:\Program Files\PuTTY\plink.exe" }

if (-not $pw) {
    Write-Host "Missing SERVER_SSH_PASSWORD or DEPLOY_SSH_PASSWORD in .env"
    exit 1
}

# Decode and run on server (plink -batch breaks on multiline remote command).
$bashScript = @'
pkill -f "blocks.spambot" 2>/dev/null || true
sleep 1
systemctl stop spambot newsbot 2>/dev/null || true
systemctl disable spambot newsbot 2>/dev/null || true
systemctl unmask spambot newsbot 2>/dev/null || true
rm -f /etc/systemd/system/spambot.service /etc/systemd/system/newsbot.service
rm -f /etc/systemd/system/multi-user.target.wants/spambot.service /etc/systemd/system/multi-user.target.wants/newsbot.service
rm -f /lib/systemd/system/spambot.service /lib/systemd/system/newsbot.service 2>/dev/null || true
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true
rm -rf /root/contentzavod/blocks/spambot /root/contentzavod-staging/blocks/spambot 2>/dev/null || true
echo "removed repo dirs blocks/spambot (prod/staging) if present"
for f in /root/contentzavod/blocks/analytics/watchdog_services.py /root/contentzavod-staging/blocks/analytics/watchdog_services.py; do
  if [ -f "$f" ]; then
    sed -i '/("spambot",/d' "$f"
    echo "patched: $f"
  fi
done
systemctl restart contentzavod-watchdog 2>/dev/null || true
echo "==== spambot status (expect not-found) ===="
systemctl status spambot 2>&1 | head -5 || true
echo "==== spambot processes ===="
pgrep -af spambot || echo "no spambot"
echo "==== watchdog ===="
systemctl is-active contentzavod-watchdog
echo done
'@
$bashScript = $bashScript.Replace("`r`n", "`n").Replace("`r", "`n")
$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($bashScript))
$remote = "echo $b64 | base64 -d | bash"

Write-Host "SSH ${user}@${hostAddr}: purge spambot (units, dirs, watchdog line)..."
& $plink -ssh "${user}@${hostAddr}" -pw $pw -batch $remote
exit $LASTEXITCODE
