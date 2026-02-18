#!/usr/bin/env python3
"""Insert webhook location blocks into nginx default_server (after 'server_name _;')."""
import sys

config_path = "/etc/nginx/sites-available/dashboard-by-ip"
snippet = """    location = /webhook {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }
    location = /health {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }

"""

with open(config_path) as f:
    content = f.read()

marker = "    server_name _;\n"
if marker not in content:
    print("Marker not found", file=sys.stderr)
    sys.exit(1)
if "location = /webhook" in content:
    print("Already patched")
    sys.exit(0)

content = content.replace(marker, marker + snippet, 1)
with open(config_path, "w") as f:
    f.write(content)
print("Patched OK")
