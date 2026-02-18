# Запуск setup_staging_all.sh на сервере по SSH.
# Требуется: SSH-ключ для root@85.198.66.62 (или измени IP ниже).
# Запуск: pwsh -File docs/scripts/deploy_beget/run_setup_staging_ssh.ps1

$host = "85.198.66.62"
$cmd = "cd /root/contentzavod && git pull origin main && sudo bash docs/scripts/deploy_beget/setup_staging_all.sh"
Write-Host "Подключение к root@$host и запуск setup..."
ssh -o StrictHostKeyChecking=accept-new "root@$host" $cmd
