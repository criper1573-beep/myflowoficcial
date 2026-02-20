#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook сервер для GitHub деплоя.
Поддержка main (production) и dev (staging): push в main → prod, push в dev → staging.
Порт: WEBHOOK_PORT (по умолчанию 3000). Endpoints: GET /health, POST /webhook.
"""
import json
import logging
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
import hmac
import hashlib

# Настройки
PORT = int(os.getenv('WEBHOOK_PORT', '3000'))
SECRET_TOKEN = os.getenv('GITHUB_WEBHOOK_SECRET', '')  # Секрет из GitHub webhook
PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_DIR_STAGING = os.getenv('PROJECT_DIR_STAGING', '')  # Путь к staging (dev), пусто = отключено
LOG_FILE = PROJECT_DIR / 'storage' / 'webhook.log'

# Ветки и окружения: ref -> (project_dir, services)
DEPLOY_MAIN_DIR = PROJECT_DIR
DEPLOY_MAIN_SERVICES = ['analytics-dashboard', 'grs-image-web', 'zen-schedule', 'telegram-monitor']
DEPLOY_STAGING_SERVICES = ['analytics-dashboard-staging', 'grs-image-web-staging']

# Директория для логов должна существовать до настройки FileHandler
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WebhookHandler(BaseHTTPRequestHandler):
    def _send_response(self, status: int, message: str):
        """Отправить JSON ответ."""
        response = json.dumps({"message": message}, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """Проверить HMAC signature от GitHub."""
        if not SECRET_TOKEN:
            logger.warning("GITHUB_WEBHOOK_SECRET не установлен, пропускаем проверку")
            return True
        
        expected_signature = f"sha256={hmac.new(
            SECRET_TOKEN.encode('utf-8'), 
            payload, 
            hashlib.sha256
        ).hexdigest()}"
        
        return hmac.compare_digest(signature, expected_signature)

    def do_GET(self):
        """Health check и bootstrap."""
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            self._send_response(200, "Webhook server is running")
        elif parsed.path == '/bootstrap':
            from urllib.parse import parse_qs
            qs = parse_qs(parsed.query)
            secret = (qs.get('secret') or [''])[0]
            if SECRET_TOKEN and not hmac.compare_digest(secret, SECRET_TOKEN):
                self._send_response(403, "Invalid secret")
                return
            self._send_response(200, "Bootstrap started")
            self._run_bootstrap()
        else:
            self._send_response(404, "Not found")

    def do_POST(self):
        """Обработка webhook от GitHub."""
        parsed = urlparse(self.path)
        
        if parsed.path != '/webhook':
            self._send_response(404, "Not found")
            return

        # Получаем заголовки
        content_type = self.headers.get('Content-Type', '')
        signature = self.headers.get('X-Hub-Signature-256', '')
        event_type = self.headers.get('X-GitHub-Event', '')

        # Проверяем Content-Type
        if 'application/json' not in content_type:
            logger.error(f"Неверный Content-Type: {content_type}")
            self._send_response(400, "Invalid Content-Type")
            return

        # Читаем тело запроса
        try:
            content_length = int(self.headers.get('Content-Length') or 0)
        except (TypeError, ValueError):
            content_length = 0
        if content_length <= 0:
            logger.error("Пустое тело запроса")
            self._send_response(400, "Empty request body")
            return

        payload = self.rfile.read(content_length)

        # Проверяем подпись
        if not self._verify_signature(payload, signature):
            logger.error(f"Неверная подпись: {signature}")
            self._send_response(403, "Invalid signature")
            return

        # Парсим JSON
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self._send_response(400, "Invalid JSON")
            return

        logger.info(f"Получен webhook: {event_type} от {data.get('repository', {}).get('full_name', 'unknown')}")

        # Обрабатываем только push события
        if event_type != 'push':
            logger.info(f"Пропускаем событие: {event_type}")
            self._send_response(200, f"Event {event_type} ignored")
            return

        # Определяем ветку и окружение
        ref = data.get('ref', '')
        if ref == 'refs/heads/main':
            project_dir = Path(DEPLOY_MAIN_DIR)
            branch = 'main'
            services = DEPLOY_MAIN_SERVICES
            env_name = 'production'
        elif ref == 'refs/heads/dev' and PROJECT_DIR_STAGING:
            project_dir = Path(PROJECT_DIR_STAGING)
            branch = 'dev'
            services = DEPLOY_STAGING_SERVICES
            env_name = 'staging'
        else:
            logger.info(f"Пропускаем ветку: {ref} (не main и не dev или staging не настроен)")
            self._send_response(200, f"Branch {ref} ignored")
            return

        # Выполняем деплой
        try:
            self._deploy(project_dir, branch, services, env_name)
            self._send_response(200, f"Deployment {env_name} successful")
            # После успешного main: автобутстрап staging (если не настроен)
            if ref == 'refs/heads/main':
                self._bootstrap_staging_if_needed()
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            self._send_response(500, f"Deployment failed: {str(e)}")

    def _deploy(self, project_dir: Path, branch: str, services: list, env_name: str):
        """Выполнить деплой: git pull и перезапуск сервисов."""
        logger.info("Начинаем деплой [%s] в %s (ветка %s)...", env_name, project_dir, branch)
        
        if not project_dir.exists():
            raise Exception(f"Директория не существует: {project_dir}")
        
        # Выполняем git pull
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', branch],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(project_dir)
            )
            
            if result.returncode != 0:
                logger.error(f"git pull failed: {result.stderr}")
                raise Exception(f"git pull failed: {result.stderr}")
            
            logger.info(f"git pull успешен: {result.stdout}")
            
        except subprocess.TimeoutExpired:
            logger.error("git pull timeout")
            raise Exception("git pull timeout")
        except FileNotFoundError:
            logger.error("git не найден")
            raise Exception("git not found")

        # Обновляем зависимости в venv
        venv_python = project_dir / 'venv' / 'bin' / 'python'
        if not venv_python.exists():
            venv_python = project_dir / 'venv' / 'Scripts' / 'python.exe'
        if venv_python.exists():
            try:
                subprocess.run(
                    [str(venv_python), '-m', 'pip', 'install', '-q', '-r', 'docs/config/requirements.txt'],
                    cwd=str(project_dir), timeout=120, check=False, capture_output=True
                )
                for req_name in ('blocks/analytics/requirements.txt', 'blocks/grs_image_web/requirements.txt', 'blocks/autopost_zen/requirements.txt', 'blocks/telegram_chat_reader/requirements.txt'):
                    req_path = project_dir / req_name
                    if req_path.exists():
                        subprocess.run(
                            [str(venv_python), '-m', 'pip', 'install', '-q', '-r', str(req_path)],
                            cwd=str(project_dir), timeout=60, check=False, capture_output=True
                        )
                logger.info("Зависимости обновлены")
            except Exception as e:
                logger.warning(f"pip install: {e}")

        # Перезапуск systemd-сервисов (требуется passwordless sudo для user, см. docs)
        for unit in services:
            try:
                subprocess.run(
                    ['sudo', '-n', 'systemctl', 'restart', unit],
                    cwd=str(project_dir), timeout=10, capture_output=True
                )
                logger.info(f"Сервис {unit} перезапущен")
            except Exception:
                pass  # сервис может быть не установлен

        # Перезапуск webhook (чтобы подхватить обновлённый код)
        if env_name == 'production':
            try:
                subprocess.Popen(
                    ['sh', '-c', 'sleep 3 && sudo -n systemctl restart github-webhook'],
                    cwd=str(project_dir), start_new_session=True
                )
                logger.info("Запланирован перезапуск github-webhook через 3 сек")
            except Exception:
                pass

        logger.info("Деплой [%s] завершен успешно", env_name)

    def _bootstrap_staging_if_needed(self):
        """Если staging не настроен — запустить setup (один раз)."""
        staging_dir = Path(PROJECT_DIR_STAGING or '/root/contentzavod-staging')
        if staging_dir.exists():
            return
        self._run_bootstrap()

    def _run_bootstrap(self):
        """Запустить setup_staging_all.sh."""
        staging_dir = Path(PROJECT_DIR_STAGING or '/root/contentzavod-staging')
        setup_script = PROJECT_DIR / 'docs' / 'scripts' / 'deploy_beget' / 'setup_staging_all.sh'
        if not setup_script.exists():
            logger.info("Staging setup script не найден")
            return
        logger.info("Запуск bootstrap: %s", setup_script)
        try:
            result = subprocess.run(
                ['sudo', 'bash', str(setup_script), str(PROJECT_DIR), str(staging_dir)],
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info("Staging bootstrap успешен")
            else:
                logger.warning("Staging bootstrap: %s", result.stderr or result.stdout)
        except Exception as e:
            logger.warning("Staging bootstrap error: %s", e)

    def log_message(self, format, *args):
        """Переопределяем логирование для использования нашего logger."""
        logger.info("%s", args[0] if args else format)


def run_server():
    """Запустить webhook сервер."""
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    logger.info(f"Webhook сервер запущен на http://0.0.0.0:{PORT}")
    logger.info(f"Endpoint: http://0.0.0.0:{PORT}/webhook")
    logger.info(f"Health check: http://0.0.0.0:{PORT}/health")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")
    finally:
        server.server_close()


if __name__ == '__main__':
    run_server()
