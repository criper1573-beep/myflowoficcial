#!/usr/bin/env python3
"""Добавить client_max_body_size 25M для flowimage.ru (референсы в base64)."""
p = "/etc/nginx/sites-enabled/flowimage.ru"
with open(p) as f:
    content = f.read()
if "client_max_body_size" in content:
    print("already patched")
    exit(0)
needle = "server_name flowimage.ru www.flowimage.ru;\n"
addition = "    client_max_body_size 25M;\n"
if needle not in content:
    print("needle not found")
    exit(1)
content = content.replace(needle, needle + addition, 1)
with open(p, "w") as f:
    f.write(content)
print("patched")
