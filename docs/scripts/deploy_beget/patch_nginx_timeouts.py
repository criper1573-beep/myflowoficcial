#!/usr/bin/env python3
"""Добавить proxy_*_timeout в location / для flowimage.ru."""
p = "/etc/nginx/sites-enabled/flowimage.ru"
with open(p) as f:
    content = f.read()
if "proxy_read_timeout" in content:
    print("already patched")
    exit(0)
needle = "proxy_set_header X-Forwarded-Proto $scheme;\n"
addition = """        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
"""
if needle not in content:
    print("needle not found")
    exit(1)
content = content.replace(needle, needle + addition, 1)
with open(p, "w") as f:
    f.write(content)
print("patched")
