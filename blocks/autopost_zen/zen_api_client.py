# -*- coding: utf-8 -*-
"""
Клиент Zen HTTP API. Запускает сервер при необходимости, делает запрос, возвращает JSON.
Один вызов = одна операция. Без бинарных данных в выводе.
"""
import json
import sys
import time
from pathlib import Path
from threading import Thread

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PORT = 3847
BASE = f"http://127.0.0.1:{PORT}"


def _start_server():
    from blocks.autopost_zen.zen_http_server import run_server
    server_thread = Thread(target=run_server, args=(PORT,), daemon=True)
    server_thread.start()
    return server_thread


def _wait_health(timeout=10):
    try:
        import urllib.request
        for _ in range(timeout):
            try:
                with urllib.request.urlopen(f"{BASE}/zen/health", timeout=2) as r:
                    if r.status == 200:
                        return True
            except Exception:
                time.sleep(1)
        return False
    except ImportError:
        return False


def _post(path: str, data: dict) -> dict:
    try:
        import urllib.request
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: zen_api_client.py publish|draft|delete [--file path] [--count N] [--no-publish]"}))
        sys.exit(1)
    cmd = sys.argv[1].lower()
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--file" and i + 1 < len(sys.argv):
            args["file"] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--count" and i + 1 < len(sys.argv):
            args["count"] = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--title" and i + 1 < len(sys.argv):
            args["title"] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--no-publish":
            args["publish"] = False
            i += 1
        else:
            i += 1

    server_thread = _start_server()
    if not _wait_health():
        result = {"success": False, "error": "Server failed to start"}
    elif cmd in ("publish", "draft"):
        args.setdefault("file", "blocks/autopost_zen/articles/office_remont_expanded.json")
        args.setdefault("publish", cmd == "publish")
        result = _post("/zen/publish", args)
    elif cmd == "delete":
        result = _post("/zen/delete", args)
    else:
        result = {"error": f"Unknown command: {cmd}"}

    out = json.dumps(result, ensure_ascii=False)
    print(out)
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
