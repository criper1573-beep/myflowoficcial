# -*- coding: utf-8 -*-
"""Локально: коммит + пуш. Затем по SSH: pull + restart analytics-dashboard."""
import os
import subprocess
import sys

def find_project_root():
    base = os.path.join(os.path.expanduser("~"), "Desktop")
    for name in os.listdir(base):
        full = os.path.join(base, name)
        if not os.path.isdir(full):
            continue
        git_dir = os.path.join(full, ".git")
        if os.path.isdir(git_dir) and os.path.isfile(os.path.join(full, "blocks", "analytics", "api.py")):
            return full
    return None

def main():
    root = find_project_root()
    if not root:
        print("Проект не найден на рабочем столе.")
        sys.exit(1)
    os.chdir(root)
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Deploy: favicon, green border for active services"
    # Git add, commit, push
    subprocess.run(["git", "add", "-A"], check=True, cwd=root)
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=root)
    if not status.stdout.strip():
        print("Нет изменений для коммита.")
    else:
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=root)
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=root)
        print("Пуш в origin/main выполнен.")
    # SSH: pull + restart
    print("Деплой на сервер...")
    cmd = "cd /root/contentzavod && git pull origin main && sudo systemctl restart analytics-dashboard"
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=accept-new", "root@85.198.66.62", cmd], cwd=root)
    if r.returncode != 0:
        print("SSH-команда завершилась с кодом", r.returncode, "- выполни на сервере: cd /root/contentzavod && git pull && sudo systemctl restart analytics-dashboard")
        sys.exit(r.returncode)
    print("Готово.")

if __name__ == "__main__":
    main()
