# -*- coding: utf-8 -*-
"""Проверка наличия ключей и работоспособности GRS AI для grs_image_web. Не выводит значения ключей."""
import os
import sys
from pathlib import Path

# Корень проекта
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def main():
    errors = []
    # 1) Ключ GRS AI
    key = (os.getenv("GRS_AI_API_KEY") or "").strip()
    if not key:
        errors.append("GRS_AI_API_KEY не задан в .env")
        print("FAIL: GRS_AI_API_KEY не задан. Добавьте в .env в корне проекта.")
        sys.exit(1)
    print("OK: GRS_AI_API_KEY задан")

    # 2) Создание клиента
    try:
        from blocks.ai_integrations.grs_ai_client import GRSAIClient
        client = GRSAIClient()
    except ValueError as e:
        errors.append(str(e))
        print("FAIL: GRS AI клиент:", e)
        sys.exit(1)
    print("OK: GRS AI клиент создан")

    # 3) Лёгкий запрос к API (проверка, что ключ принимается)
    try:
        reply = client.simple_ask("Ответь одним словом: ок", model="gpt-4o-mini")
        if not reply or not isinstance(reply, str):
            errors.append("Пустой или неверный ответ API")
            print("WARN: API вернул пустой ответ")
        else:
            print("OK: API отвечает, ключ действителен")
    except Exception as e:
        errors.append("Ошибка запроса к GRS AI: " + str(e))
        print("FAIL: Запрос к GRS AI:", e)
        sys.exit(1)

    # 4) Модели для изображений
    if "nano-banana-pro" in (GRSAIClient.IMAGE_MODELS or []):
        print("OK: Модель nano-banana-pro доступна для генерации")
    else:
        print("INFO: IMAGE_MODELS:", getattr(GRSAIClient, "IMAGE_MODELS", []))

    print("\nВсе проверки пройдены. Генерация изображений должна работать.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
