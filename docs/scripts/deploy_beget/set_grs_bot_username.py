# -*- coding: utf-8 -*-
"""Один раз на сервере: прочитать TELEGRAM_BOT_TOKEN из .env, получить username через getMe, записать GRS_IMAGE_WEB_BOT_USERNAME."""
import json
import os
import re
import urllib.request

def main():
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    env_path = os.path.abspath(env_path)
    if not os.path.isfile(env_path):
        env_path = "/root/contentzavod/.env"
    if not os.path.isfile(env_path):
        print("No .env found")
        return
    token = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*TELEGRAM_BOT_TOKEN\s*=\s*(.+)\s*$", line)
            if m:
                token = m.group(1).strip().strip('"\'')
                break
    if not token:
        print("TELEGRAM_BOT_TOKEN not in .env")
        return
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=10) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print("getMe failed:", e)
        return
    if not data.get("ok"):
        print("getMe not ok:", data)
        return
    username = (data.get("result") or {}).get("username", "").strip()
    if not username:
        print("No username in result")
        return
    print("Bot username:", username)
    lines = []
    found = False
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if re.match(r"^\s*GRS_IMAGE_WEB_BOT_USERNAME\s*=", line):
                lines.append(f"GRS_IMAGE_WEB_BOT_USERNAME={username}\n")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"\nGRS_IMAGE_WEB_BOT_USERNAME={username}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Written GRS_IMAGE_WEB_BOT_USERNAME to .env")

if __name__ == "__main__":
    main()
