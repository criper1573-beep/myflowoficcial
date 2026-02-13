# -*- coding: utf-8 -*-
"""
HTTP-сервер для автопостинга Дзен.
Запускает Playwright в отдельном процессе, возвращает только JSON — без бинарных данных.
Обход ошибки Cursor: serialize binary: invalid int 32.
"""
import asyncio
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BLOCK_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("zen_http")


def _run_async(coro):
    return asyncio.run(coro)


class ZenAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def log_message(self, format, *args):
        logger.info("%s", args[0] if args else format)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/zen/health":
            self._send_json(200, {"ok": True, "message": "Zen API ready"})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        body = self._read_body()

        if parsed.path == "/zen/publish":
            self._handle_publish(body)
        elif parsed.path == "/zen/delete":
            self._handle_delete(body)
        else:
            self._send_json(404, {"error": "Not found"})

    def _handle_publish(self, body: dict):
        try:
            file_path = body.get("file", "blocks/autopost_zen/articles/office_remont_expanded.json")
            publish = body.get("publish", True)
            p = Path(file_path)
            if not p.is_absolute():
                p = PROJECT_ROOT / p
            if not p.exists():
                self._send_json(400, {"success": False, "error": f"File not found: {p}"})
                return
            data = json.loads(p.read_text(encoding="utf-8"))
            from blocks.autopost_zen.zen_client import run_post_flow
            exit_code, msg = _run_async(run_post_flow(data, publish=publish, headless=False, keep_open=False))
            success = exit_code == 0
            self._send_json(200, {"success": success, "exit_code": exit_code, "message": msg})
        except Exception as e:
            logger.exception("Publish error: %s", e)
            self._send_json(500, {"success": False, "error": str(e)})

    def _handle_delete(self, body: dict):
        self._send_json(410, {"success": False, "error": "Удаление постов отключено"})


def run_server(port: int = 3847):
    server = HTTPServer(("127.0.0.1", port), ZenAPIHandler)
    logger.info("Zen API server on http://127.0.0.1:%s", port)
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3847
    run_server(port)
