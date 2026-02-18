#!/usr/bin/env python3
"""Добавить location /bootstrap в nginx (рядом с /webhook)."""
import glob
import os
import sys

snippet = """
    location = /bootstrap {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
"""

for path in glob.glob("/etc/nginx/sites-enabled/*") + glob.glob("/etc/nginx/conf.d/*.conf"):
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        content = f.read()
    if "location = /webhook" not in content:
        continue
    if "location = /bootstrap" in content:
        print("Already has /bootstrap")
        sys.exit(0)
    # Добавляем после блока /health
    marker = "location = /health {"
    if marker not in content:
        marker = "location = /webhook {"
    insert_after = content.find("}", content.find(marker)) + 1
    new_content = content[:insert_after] + snippet + content[insert_after:]
    with open(path, "w") as f:
        f.write(new_content)
    print(f"Patched {path}")
    sys.exit(0)

print("No nginx config with /webhook found")
sys.exit(1)
