# -*- coding: utf-8 -*-
"""
Одноразовый скрипт: скопировать credentials.json из папки "Пост FLOW" с рабочего стола
в blocks/post_flow/ (чтобы все пути были внутри ContentZavod).
Запуск из корня проекта: python blocks/post_flow/copy_credentials_here.py
"""
import shutil
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent.parent  # корень ContentZavod
    desktop = root.parent  # Desktop
    source = desktop / "Пост FLOW" / "credentials.json"
    dest = root / "blocks" / "post_flow" / "credentials.json"
    if not source.exists():
        print("Не найден файл:", source)
        print("Скопируйте credentials.json вручную в blocks/post_flow/")
        return 1
    shutil.copy2(source, dest)
    print("Скопировано:", source, "->", dest)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
